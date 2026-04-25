from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from app.agent_integration import (
    build_agent_orchestration_flow,
    build_planning_request_for_agent,
    build_red_zone_alerts_for_agents,
    build_simulation_request_for_agent,
)
from app.als_feature_contract import ALS_DEFAULT_FILL_VALUE, ALS_FEATURE_LIMITS
from app.als_model_loader import (
    MissingAlsArtifactsError,
    get_loaded_als_model,
    predict_als_scores,
    score_to_band,
)
from app.als_pipeline import derive_als_features_from_watch_sequence
from app.edge_pipeline import aggregate_packets_to_tiles, build_privacy_packet
from app.edge_pipeline import build_agent_hotspots, build_history_buckets, build_hotspot_detail
from app.feature_contract import (
    COMPONENT_ABS_LIMIT,
    DEFAULT_FEATURE_FILL_VALUE,
    EXPECTED_FEATURES,
    MAGNITUDE_MAX_LIMIT,
)
from app.model_loader import (
    MissingArtifactsError,
    get_loaded_model,
    predict_classes,
    predict_probabilities,
    probabilities_to_classes,
    smooth_probabilities,
)
from app.live_agent_bridge import run_live_agent_workflow
from app.schemas import (
    ALSModelInfoResponse,
    ALSPredictionRequest,
    ALSPredictionResponse,
    ALSSequencePredictionItemResponse,
    ALSSequencePredictionRequest,
    ALSSequencePredictionResponse,
    BatchContextPredictionRequest,
    BatchContextPredictionResponse,
    ContextPredictionRequest,
    ContextPredictionResponse,
    AgentPlanningRequestResponse,
    AgentRedZoneAlertResponse,
    AgentRedZoneAlertsResponse,
    AgentSimulationRequestResponse,
    AgentLiveWorkflowResponse,
    AgentWorkflowRequest,
    AgentWorkflowResponse,
    EdgeTelemetryIngestionRequest,
    EdgeTelemetryIngestionResponse,
    AgentHotspotResponse,
    AgentHotspotsResponse,
    AppIngestionContractResponse,
    HealthResponse,
    DemoResetResponse,
    DemoStatusResponse,
    HotspotDetailResponse,
    MapTileHistoryResponse,
    MapTilesResponse,
    ModelInfoResponse,
    SequenceBatchContextPredictionResponse,
    SequenceContextPredictionRequest,
    SequenceContextPredictionResponse,
    SimulationRequest,
    SimulationResponse,
    WatchALSSequencePredictionItemResponse,
    WatchALSSequencePredictionRequest,
    WatchALSSequencePredictionResponse,
    WatchEvent,
    WatchEventsIngestionRequest,
    WatchEventsIngestionResponse,
    WatchPrivacyPacketItemResponse,
    WatchPrivacyPacketSequenceResponse,
    WatchUserEventsResponse,
)
from app.session_state import (
    als_scalar_store,
    edge_packet_store,
    session_smoother_store,
    watch_event_store,
)
from app.simulation import simulate_intervention
from app.settings import get_settings
from training.als_constants import ALS_FEATURE_NAMES

app = FastAPI(title="The Living City Context Classifier", version="1.0.0")
logger = logging.getLogger(__name__)

OFFICIAL_INGESTION_PATH = "/ingest/edge-packets"
DEV_ONLY_PATHS = [
    "/ingest/watch-events",
    "/predict/als/watch/sequence",
    "/predict/als/watch/privacy-packets",
]
FRONTEND_ENDPOINTS = [
    "/map/tiles",
    "/ws/map/tiles",
    "/map/tiles/history",
    "/map/tiles/{h3_index}",
]
AGENT_ENDPOINTS = [
    "/agents/hotspots",
    "/agents/diagnosis/red-zone-alerts",
    "/agents/simulation-request/{h3_index}",
    "/agents/planning-request/{h3_index}",
    "/agents/orchestrate",
    "/agents/orchestrate/live",
]


def _build_app_ingestion_contract() -> AppIngestionContractResponse:
    return AppIngestionContractResponse(
        official_ingestion_path=OFFICIAL_INGESTION_PATH,
        method="POST",
        description=(
            "Production app and device builds should send only privacy-safe edge packets "
            "to this endpoint. Raw watch-event routes remain available for development only."
        ),
        packet_fields={
            "user_id": "string",
            "timestamp": "ISO 8601 UTC string",
            "h3_index": "H3 resolution 9 string",
            "als_score": "float in [0.0, 1.0]",
            "context": "stationary | walking | transit_like",
            "noise_db": "float in [0.0, 140.0]",
        },
        dev_only_paths=DEV_ONLY_PATHS,
        frontend_endpoints=FRONTEND_ENDPOINTS,
        agent_endpoints=AGENT_ENDPOINTS,
        example_payload={
            "packets": [
                {
                    "user_id": "demo_user_01",
                    "timestamp": "2026-04-24T10:15:30Z",
                    "h3_index": "8929a1d7577ffff",
                    "als_score": 0.82,
                    "context": "walking",
                    "noise_db": 72.0,
                }
            ]
        },
    )


def _latest_edge_timestamp(packets: list[dict[str, object]]) -> object | None:
    if not packets:
        return None
    return max(packet["timestamp"] for packet in packets)


@app.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    settings = get_settings()
    try:
        loaded = get_loaded_model()
        return HealthResponse(
            status="ready",
            model_loaded=True,
            model_version=loaded.model_version,
        )
    except MissingArtifactsError:
        return HealthResponse(
            status="artifacts_missing",
            model_loaded=False,
            model_version=settings.model_version,
        )


@app.get("/als/health", response_model=HealthResponse)
def als_healthcheck() -> HealthResponse:
    settings = get_settings()
    try:
        loaded = get_loaded_als_model()
        return HealthResponse(
            status="ready",
            model_loaded=True,
            model_version=loaded.model_version,
        )
    except MissingAlsArtifactsError:
        return HealthResponse(
            status="artifacts_missing",
            model_loaded=False,
            model_version=settings.als_model_version,
        )


@app.get("/model/info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    try:
        loaded = get_loaded_model()
    except MissingArtifactsError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ModelInfoResponse(
        model_version=loaded.model_version,
        classifier_name=loaded.classifier_name,
        classes=loaded.classes,
        feature_names=loaded.feature_names,
        training_metrics=loaded.training_metrics,
        feature_validation={
            "known_feature_count": len(EXPECTED_FEATURES),
            "missing_features_allowed": "true",
            "missing_feature_fill_value": DEFAULT_FEATURE_FILL_VALUE,
            "component_abs_limit": COMPONENT_ABS_LIMIT,
            "magnitude_max_limit": MAGNITUDE_MAX_LIMIT,
            "sequence_smoothing_default_window": 3,
        },
    )


@app.get("/als/model/info", response_model=ALSModelInfoResponse)
def als_model_info() -> ALSModelInfoResponse:
    try:
        loaded = get_loaded_als_model()
    except MissingAlsArtifactsError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ALSModelInfoResponse(
        model_version=loaded.model_version,
        regressor_name=loaded.regressor_name,
        feature_names=loaded.feature_names,
        training_metrics=loaded.training_metrics,
        feature_validation={
            "known_feature_count": len(ALS_FEATURE_NAMES),
            "missing_features_allowed": "true",
            "missing_feature_fill_value": ALS_DEFAULT_FILL_VALUE,
            "hr_min_limit": ALS_FEATURE_LIMITS["hr_mean"][0],
            "hr_max_limit": ALS_FEATURE_LIMITS["hr_mean"][1],
            "sequence_smoothing_default_window": 3,
        },
    )


@app.post("/ingest/watch-events", response_model=WatchEventsIngestionResponse)
def ingest_watch_events(
    payload: WatchEventsIngestionRequest,
) -> WatchEventsIngestionResponse:
    serialized_events = [event.model_dump(mode="json") for event in payload.events]
    stored_events = watch_event_store.append_events(payload.user_id, serialized_events)
    latest_timestamp = max(event.timestamp for event in payload.events)

    return WatchEventsIngestionResponse(
        user_id=payload.user_id,
        accepted_events=len(payload.events),
        stored_events=stored_events,
        latest_timestamp=latest_timestamp,
    )


@app.get("/ingest/watch-events/{user_id}", response_model=WatchUserEventsResponse)
def get_watch_events(user_id: str) -> WatchUserEventsResponse:
    stored_events = watch_event_store.get_events(user_id)
    latest_event = watch_event_store.get_latest_event(user_id)

    return WatchUserEventsResponse(
        user_id=user_id,
        event_count=len(stored_events),
        latest_event=WatchEvent.model_validate(latest_event) if latest_event else None,
        events=[WatchEvent.model_validate(event) for event in stored_events],
    )


@app.post("/ingest/edge-packets", response_model=EdgeTelemetryIngestionResponse)
def ingest_edge_packets(
    payload: EdgeTelemetryIngestionRequest,
) -> EdgeTelemetryIngestionResponse:
    serialized_packets = [packet.model_dump(mode="json") for packet in payload.packets]
    stored_packets = edge_packet_store.append_packets(serialized_packets)
    unique_tiles = len({packet.h3_index for packet in payload.packets})
    latest_timestamp = max(packet.timestamp for packet in payload.packets)
    logger.info(
        "Ingested %s edge packets across %s tile(s); latest=%s",
        len(payload.packets),
        unique_tiles,
        latest_timestamp.isoformat(),
    )

    return EdgeTelemetryIngestionResponse(
        accepted_packets=len(payload.packets),
        stored_packets=stored_packets,
        unique_tiles=unique_tiles,
        latest_timestamp=latest_timestamp,
        ingestion_mode="privacy_safe_edge_packets",
        official_contract=OFFICIAL_INGESTION_PATH,
    )


@app.get("/map/tiles", response_model=MapTilesResponse)
def get_map_tiles() -> MapTilesResponse:
    tiles = aggregate_packets_to_tiles(edge_packet_store.get_packets())
    return MapTilesResponse(tiles=tiles, tile_count=len(tiles))


@app.get("/contracts/app-ingestion", response_model=AppIngestionContractResponse)
def get_app_ingestion_contract() -> AppIngestionContractResponse:
    return _build_app_ingestion_contract()


@app.get("/demo/status", response_model=DemoStatusResponse)
def get_demo_status() -> DemoStatusResponse:
    packets = edge_packet_store.get_packets()
    tiles = aggregate_packets_to_tiles(packets)
    hotspots = build_agent_hotspots(packets, limit=50)
    return DemoStatusResponse(
        official_ingestion_path=OFFICIAL_INGESTION_PATH,
        edge_packet_count=edge_packet_store.total_packets(),
        watch_event_count=watch_event_store.total_events(),
        unique_edge_users=len({str(packet["user_id"]) for packet in packets}),
        active_tile_count=len(tiles),
        hotspot_count=len(hotspots),
        latest_edge_timestamp=_latest_edge_timestamp(packets),
        red_zone_count=sum(1 for tile in tiles if tile["status"] == "red_zone"),
        dev_only_paths=DEV_ONLY_PATHS,
        frontend_endpoints=FRONTEND_ENDPOINTS,
        agent_endpoints=AGENT_ENDPOINTS,
    )


@app.post("/demo/reset", response_model=DemoResetResponse)
def reset_demo_state() -> DemoResetResponse:
    cleared_edge_packets = edge_packet_store.total_packets()
    cleared_watch_events = watch_event_store.total_events()
    cleared_context_sessions = session_smoother_store.clear_all()
    cleared_als_sessions = als_scalar_store.clear_all()
    edge_packet_store.clear()
    watch_event_store.clear()
    logger.info(
        "Reset demo state: cleared %s edge packets, %s watch events, %s context sessions, %s als sessions",
        cleared_edge_packets,
        cleared_watch_events,
        cleared_context_sessions,
        cleared_als_sessions,
    )
    return DemoResetResponse(
        status="reset",
        cleared_edge_packets=cleared_edge_packets,
        cleared_watch_events=cleared_watch_events,
        cleared_context_sessions=cleared_context_sessions,
        cleared_als_sessions=cleared_als_sessions,
    )


@app.get("/map/tiles/history", response_model=MapTileHistoryResponse)
def get_map_tiles_history(
    bucket_minutes: int = 60,
    limit: int = 24,
) -> MapTileHistoryResponse:
    buckets = build_history_buckets(
        edge_packet_store.get_packets(),
        bucket_minutes=bucket_minutes,
        limit=limit,
    )
    return MapTileHistoryResponse(
        buckets=buckets,
        bucket_minutes=bucket_minutes,
    )


@app.get("/map/tiles/{h3_index}", response_model=HotspotDetailResponse)
def get_hotspot_detail(h3_index: str) -> HotspotDetailResponse:
    detail = build_hotspot_detail(edge_packet_store.get_packets(), h3_index)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Unknown h3_index: {h3_index}")
    return HotspotDetailResponse(**detail)


@app.get("/agents/hotspots", response_model=AgentHotspotsResponse)
def get_agent_hotspots(limit: int = 10) -> AgentHotspotsResponse:
    hotspots = build_agent_hotspots(edge_packet_store.get_packets(), limit=limit)
    return AgentHotspotsResponse(
        hotspots=[
            AgentHotspotResponse(rank=index, **hotspot)
            for index, hotspot in enumerate(hotspots, start=1)
        ],
        hotspot_count=len(hotspots),
    )


@app.get("/agents/diagnosis/red-zone-alerts", response_model=AgentRedZoneAlertsResponse)
def get_agent_red_zone_alerts(limit: int = 10) -> AgentRedZoneAlertsResponse:
    alerts = build_red_zone_alerts_for_agents(edge_packet_store.get_packets(), limit=limit)
    return AgentRedZoneAlertsResponse(
        alerts=[AgentRedZoneAlertResponse(**alert) for alert in alerts],
        alert_count=len(alerts),
    )


@app.get(
    "/agents/simulation-request/{h3_index}",
    response_model=AgentSimulationRequestResponse,
)
def get_agent_simulation_request(h3_index: str) -> AgentSimulationRequestResponse:
    request_payload = build_simulation_request_for_agent(
        edge_packet_store.get_packets(),
        h3_index=h3_index,
    )
    if request_payload is None:
        raise HTTPException(status_code=404, detail=f"Unknown h3_index: {h3_index}")
    return AgentSimulationRequestResponse(**request_payload)


@app.get(
    "/agents/planning-request/{h3_index}",
    response_model=AgentPlanningRequestResponse,
)
def get_agent_planning_request(h3_index: str) -> AgentPlanningRequestResponse:
    request_payload = build_planning_request_for_agent(
        edge_packet_store.get_packets(),
        h3_index=h3_index,
    )
    if request_payload is None:
        raise HTTPException(status_code=404, detail=f"Unknown h3_index: {h3_index}")
    return AgentPlanningRequestResponse(**request_payload)


@app.post("/agents/orchestrate", response_model=AgentWorkflowResponse)
def orchestrate_agent_flow(payload: AgentWorkflowRequest) -> AgentWorkflowResponse:
    flow = build_agent_orchestration_flow(
        edge_packet_store.get_packets(),
        h3_index=payload.h3_index,
    )
    if flow is None:
        detail = (
            f"Unknown h3_index: {payload.h3_index}"
            if payload.h3_index
            else "No hotspots available to orchestrate."
        )
        raise HTTPException(status_code=404, detail=detail)
    return AgentWorkflowResponse(**flow)


@app.post("/agents/orchestrate/live", response_model=AgentLiveWorkflowResponse)
def orchestrate_live_agent_flow(payload: AgentWorkflowRequest) -> AgentLiveWorkflowResponse:
    flow = run_live_agent_workflow(
        edge_packet_store.get_packets(),
        h3_index=payload.h3_index,
    )
    if flow is None:
        detail = (
            f"Unknown h3_index: {payload.h3_index}"
            if payload.h3_index
            else "No hotspots available to orchestrate."
        )
        raise HTTPException(status_code=404, detail=detail)
    return AgentLiveWorkflowResponse(**flow)


@app.post("/simulate/intervention", response_model=SimulationResponse)
def simulate_intervention_endpoint(
    payload: SimulationRequest,
) -> SimulationResponse:
    result = simulate_intervention(
        edge_packet_store.get_packets(),
        h3_index=payload.h3_index,
        intervention_type=payload.intervention_type,
        intensity=payload.intensity,
        budget_usd=payload.budget_usd,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unknown h3_index: {payload.h3_index}")
    return SimulationResponse(**result)


@app.websocket("/ws/map/tiles")
async def map_tiles_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    last_seen_version = -1

    try:
        while True:
            current_version = edge_packet_store.get_version()
            if current_version != last_seen_version:
                tiles = aggregate_packets_to_tiles(edge_packet_store.get_packets())
                await websocket.send_json(
                    MapTilesResponse(
                        tiles=tiles,
                        tile_count=len(tiles),
                    ).model_dump(mode="json")
                )
                last_seen_version = current_version
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return


@app.post("/predict/context", response_model=ContextPredictionResponse)
def predict_context(payload: ContextPredictionRequest) -> ContextPredictionResponse:
    try:
        probabilities = predict_probabilities([payload.features])[0]
        context = predict_classes([payload.features])[0]
        loaded = get_loaded_model()
    except MissingArtifactsError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    smoothed_context = None
    smoothed_probabilities = None
    if payload.session_id:
        history = session_smoother_store.append(
            payload.session_id,
            probabilities,
            payload.smoothing_window,
        )
        smoothed_probabilities = smooth_probabilities(
            history,
            loaded.classes,
            payload.smoothing_window,
        )[-1]
        smoothed_context = probabilities_to_classes(
            [smoothed_probabilities],
            loaded.classes,
        )[0]

    return ContextPredictionResponse(
        window_id=payload.window_id,
        session_id=payload.session_id,
        context=context,
        smoothed_context=smoothed_context,
        probabilities=probabilities,
        smoothed_probabilities=smoothed_probabilities,
        model_version=loaded.model_version,
    )


@app.post("/predict/als", response_model=ALSPredictionResponse)
def predict_als(payload: ALSPredictionRequest) -> ALSPredictionResponse:
    try:
        score = predict_als_scores([payload.features])[0]
        loaded = get_loaded_als_model()
    except MissingAlsArtifactsError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    smoothed_score = None
    smoothed_band = None
    if payload.session_id:
        history = als_scalar_store.append(payload.session_id, score, payload.smoothing_window)
        smoothed_score = float(sum(history) / len(history))
        smoothed_band = score_to_band(smoothed_score)

    return ALSPredictionResponse(
        window_id=payload.window_id,
        session_id=payload.session_id,
        als_score=score,
        smoothed_als_score=smoothed_score,
        stress_band=score_to_band(score),
        smoothed_stress_band=smoothed_band,
        model_version=loaded.model_version,
    )


@app.post("/predict/context/batch", response_model=BatchContextPredictionResponse)
def predict_context_batch(
    payload: BatchContextPredictionRequest,
) -> BatchContextPredictionResponse:
    try:
        features_list = [item.features for item in payload.items]
        probabilities = predict_probabilities(features_list)
        contexts = predict_classes(features_list)
        loaded = get_loaded_model()
    except MissingArtifactsError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    predictions = [
        ContextPredictionResponse(
            window_id=item.window_id,
            context=context,
            probabilities=probability,
            model_version=loaded.model_version,
        )
        for item, context, probability in zip(
            payload.items, contexts, probabilities, strict=True
        )
    ]

    return BatchContextPredictionResponse(
        predictions=predictions,
        model_version=loaded.model_version,
    )


@app.post(
    "/predict/context/sequence",
    response_model=SequenceBatchContextPredictionResponse,
)
def predict_context_sequence(
    payload: SequenceContextPredictionRequest,
) -> SequenceBatchContextPredictionResponse:
    try:
        features_list = [item.features for item in payload.items]
        raw_probabilities = predict_probabilities(features_list)
        loaded = get_loaded_model()
        smoothed = smooth_probabilities(
            raw_probabilities,
            loaded.classes,
            payload.smoothing_window,
        )
    except MissingArtifactsError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    raw_contexts = probabilities_to_classes(raw_probabilities, loaded.classes)
    smoothed_contexts = probabilities_to_classes(smoothed, loaded.classes)
    predictions = [
        SequenceContextPredictionResponse(
            window_id=item.window_id,
            context=raw_context,
            smoothed_context=smoothed_context,
            probabilities=raw_probability,
            smoothed_probabilities=smoothed_probability,
            model_version=loaded.model_version,
        )
        for item, raw_context, smoothed_context, raw_probability, smoothed_probability in zip(
            payload.items,
            raw_contexts,
            smoothed_contexts,
            raw_probabilities,
            smoothed,
            strict=True,
        )
    ]

    return SequenceBatchContextPredictionResponse(
        predictions=predictions,
        model_version=loaded.model_version,
        smoothing_window=payload.smoothing_window,
    )


@app.post("/predict/als/sequence", response_model=ALSSequencePredictionResponse)
def predict_als_sequence(
    payload: ALSSequencePredictionRequest,
) -> ALSSequencePredictionResponse:
    try:
        scores = predict_als_scores([item.features for item in payload.items])
        loaded = get_loaded_als_model()
    except MissingAlsArtifactsError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    smoothed_scores: list[float] = []
    for index in range(len(scores)):
        start_index = max(0, index - payload.smoothing_window + 1)
        window = scores[start_index : index + 1]
        smoothed_scores.append(float(sum(window) / len(window)))

    predictions = [
        ALSSequencePredictionItemResponse(
            window_id=item.window_id,
            als_score=score,
            smoothed_als_score=smoothed_score,
            stress_band=score_to_band(score),
            smoothed_stress_band=score_to_band(smoothed_score),
            model_version=loaded.model_version,
        )
        for item, score, smoothed_score in zip(
            payload.items,
            scores,
            smoothed_scores,
            strict=True,
        )
    ]

    return ALSSequencePredictionResponse(
        predictions=predictions,
        model_version=loaded.model_version,
        smoothing_window=payload.smoothing_window,
    )


@app.post("/predict/als/watch/sequence", response_model=WatchALSSequencePredictionResponse)
def predict_als_from_watch_sequence(
    payload: WatchALSSequencePredictionRequest,
) -> WatchALSSequencePredictionResponse:
    try:
        derived_features = derive_als_features_from_watch_sequence(
            [item.metrics.model_dump() for item in payload.items]
        )
        scores = predict_als_scores(derived_features)
        loaded = get_loaded_als_model()
    except MissingAlsArtifactsError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    smoothed_scores: list[float] = []
    for index in range(len(scores)):
        start_index = max(0, index - payload.smoothing_window + 1)
        window = scores[start_index : index + 1]
        smoothed_scores.append(float(sum(window) / len(window)))

    predictions = [
        WatchALSSequencePredictionItemResponse(
            timestamp=item.timestamp,
            als_score=score,
            smoothed_als_score=smoothed_score,
            stress_band=score_to_band(score),
            smoothed_stress_band=score_to_band(smoothed_score),
            derived_features=feature_row,
        )
        for item, score, smoothed_score, feature_row in zip(
            payload.items,
            scores,
            smoothed_scores,
            derived_features,
            strict=True,
        )
    ]

    return WatchALSSequencePredictionResponse(
        user_id=payload.user_id,
        predictions=predictions,
        model_version=loaded.model_version,
        smoothing_window=payload.smoothing_window,
        derivation_mode="heuristic_watch_metrics_v1",
    )


@app.post(
    "/predict/als/watch/privacy-packets",
    response_model=WatchPrivacyPacketSequenceResponse,
)
def predict_privacy_packets_from_watch_sequence(
    payload: WatchALSSequencePredictionRequest,
) -> WatchPrivacyPacketSequenceResponse:
    try:
        derived_features = derive_als_features_from_watch_sequence(
            [item.metrics.model_dump() for item in payload.items]
        )
        scores = predict_als_scores(derived_features)
        loaded = get_loaded_als_model()
    except MissingAlsArtifactsError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    packets = [
        WatchPrivacyPacketItemResponse.model_validate(
            build_privacy_packet(
                user_id=payload.user_id,
                timestamp=item.timestamp.isoformat().replace("+00:00", "Z"),
                lat=item.location.lat,
                lng=item.location.lng,
                als_score=score,
                metrics=item.metrics.model_dump(),
            )
        )
        for item, score in zip(payload.items, scores, strict=True)
    ]

    return WatchPrivacyPacketSequenceResponse(
        user_id=payload.user_id,
        packets=packets,
        model_version=loaded.model_version,
        h3_resolution=9,
        derivation_mode="privacy_packet_v1",
    )
