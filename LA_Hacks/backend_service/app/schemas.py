from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.feature_contract import validate_feature_payload


class ContextPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    window_id: Optional[str] = None
    session_id: Optional[str] = None
    smoothing_window: int = Field(default=3, ge=1, le=15)
    features: Dict[str, float]

    @field_validator("features")
    @classmethod
    def validate_features(cls, value: Dict[str, float]) -> Dict[str, float]:
        if not value:
            raise ValueError("features must not be empty")
        validate_feature_payload(value)
        return value


class BatchContextPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: List[ContextPredictionRequest] = Field(min_length=1)


class SequenceContextPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: List[ContextPredictionRequest] = Field(min_length=1)
    smoothing_window: int = Field(default=3, ge=1, le=15)


class ContextPredictionResponse(BaseModel):
    window_id: Optional[str] = None
    session_id: Optional[str] = None
    context: str
    smoothed_context: Optional[str] = None
    probabilities: Dict[str, float]
    smoothed_probabilities: Optional[Dict[str, float]] = None
    model_version: str


class SequenceContextPredictionResponse(BaseModel):
    window_id: Optional[str] = None
    context: str
    smoothed_context: str
    probabilities: Dict[str, float]
    smoothed_probabilities: Dict[str, float]
    model_version: str


class BatchContextPredictionResponse(BaseModel):
    predictions: List[ContextPredictionResponse]
    model_version: str


class SequenceBatchContextPredictionResponse(BaseModel):
    predictions: List[SequenceContextPredictionResponse]
    model_version: str
    smoothing_window: int


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str


class ModelInfoResponse(BaseModel):
    model_version: str
    classifier_name: str
    classes: List[str]
    feature_names: List[str]
    training_metrics: Dict[str, Any]
    feature_validation: Dict[str, str | float | int]


class ALSPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    window_id: Optional[str] = None
    session_id: Optional[str] = None
    smoothing_window: int = Field(default=3, ge=1, le=15)
    features: Dict[str, float]

    @field_validator("features")
    @classmethod
    def validate_als_features(cls, value: Dict[str, float]) -> Dict[str, float]:
        if not value:
            raise ValueError("features must not be empty")
        from app.als_feature_contract import validate_als_feature_payload

        validate_als_feature_payload(value)
        return value


class ALSSequencePredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: List[ALSPredictionRequest] = Field(min_length=1)
    smoothing_window: int = Field(default=3, ge=1, le=15)


class ALSPredictionResponse(BaseModel):
    window_id: Optional[str] = None
    session_id: Optional[str] = None
    als_score: float
    smoothed_als_score: Optional[float] = None
    stress_band: str
    smoothed_stress_band: Optional[str] = None
    model_version: str


class ALSSequencePredictionItemResponse(BaseModel):
    window_id: Optional[str] = None
    als_score: float
    smoothed_als_score: float
    stress_band: str
    smoothed_stress_band: str
    model_version: str


class ALSSequencePredictionResponse(BaseModel):
    predictions: List[ALSSequencePredictionItemResponse]
    model_version: str
    smoothing_window: int


class ALSModelInfoResponse(BaseModel):
    model_version: str
    regressor_name: str
    feature_names: List[str]
    training_metrics: Dict[str, Any]
    feature_validation: Dict[str, str | float | int]


class WatchALSSequencePredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1, max_length=128)
    items: List[WatchEvent] = Field(
        min_length=1,
        validation_alias=AliasChoices("items", "events"),
    )
    smoothing_window: int = Field(default=3, ge=1, le=15)


class WatchALSSequencePredictionItemResponse(BaseModel):
    timestamp: datetime
    als_score: float
    smoothed_als_score: float
    stress_band: str
    smoothed_stress_band: str
    derived_features: Dict[str, float]


class WatchALSSequencePredictionResponse(BaseModel):
    user_id: str
    predictions: List[WatchALSSequencePredictionItemResponse]
    model_version: str
    smoothing_window: int
    derivation_mode: str


class WatchLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: float = Field(ge=-90.0, le=90.0)
    lng: float = Field(ge=-180.0, le=180.0)


class WatchMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    heart_rate: float = Field(gt=0.0, le=240.0)
    wrist_temperature: float = Field(ge=-20.0, le=20.0)
    environmental_sound_level: float = Field(ge=0.0, le=140.0)
    exercise_time: float = Field(ge=0.0, le=1440.0)
    walking_distance: float = Field(ge=0.0)
    running_distance: float = Field(ge=0.0)
    physical_effort: float = Field(ge=0.0, le=1.0)
    respiratory_rate: float = Field(ge=0.0, le=80.0)
    blood_oxygen: float = Field(ge=0.0, le=100.0)
    sleep: float = Field(ge=0.0, le=24.0)
    walking_speed: float = Field(ge=0.0, le=12.0)
    walking_steadiness: float = Field(ge=0.0, le=1.0)
    step_length: float = Field(ge=0.0, le=3.0)
    stair_speed: float = Field(ge=0.0, le=10.0)
    stairs_up: int = Field(ge=0)
    stairs_down: int = Field(ge=0)
    stand_minutes: float = Field(ge=0.0, le=1440.0)
    active_energy: float = Field(ge=0.0)
    resting_energy: float = Field(ge=0.0)

    @field_validator("running_distance")
    @classmethod
    def validate_running_distance(cls, value: float, info: Any) -> float:
        walking_distance = info.data.get("walking_distance")
        if walking_distance is not None and value > walking_distance:
            raise ValueError("running_distance must be <= walking_distance for the same event")
        return value


class WatchEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    location: WatchLocation
    metrics: WatchMetrics


class WatchEventsIngestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1, max_length=128)
    events: List[WatchEvent] = Field(min_length=1)


class WatchEventsIngestionResponse(BaseModel):
    user_id: str
    accepted_events: int
    stored_events: int
    latest_timestamp: datetime


class WatchUserEventsResponse(BaseModel):
    user_id: str
    event_count: int
    latest_event: Optional[WatchEvent] = None
    events: List[WatchEvent]


EdgeContext = Literal["stationary", "walking", "transit_like"]
ZoneStatus = Literal["red_zone", "blue_zone"]


class EdgeTelemetryPacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1, max_length=128)
    timestamp: datetime
    h3_index: str = Field(min_length=1)
    als_score: float = Field(ge=0.0, le=1.0)
    context: EdgeContext
    noise_db: float = Field(default=0.0, ge=0.0, le=140.0)


class EdgeTelemetryIngestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    packets: List[EdgeTelemetryPacket] = Field(min_length=1)


class EdgeTelemetryIngestionResponse(BaseModel):
    accepted_packets: int
    stored_packets: int
    unique_tiles: int
    latest_timestamp: datetime


class MapTileResponse(BaseModel):
    h3_index: str
    avg_als: float = Field(ge=0.0, le=1.0)
    dominant_context: EdgeContext
    noise_db: float = Field(ge=0.0, le=140.0)
    status: ZoneStatus


class MapTilesResponse(BaseModel):
    tiles: List[MapTileResponse]
    tile_count: int


class MapTileHistoryBucketResponse(BaseModel):
    bucket_start: datetime
    tile_count: int
    tiles: List[MapTileResponse]


class MapTileHistoryResponse(BaseModel):
    buckets: List[MapTileHistoryBucketResponse]
    bucket_minutes: int


class HotspotDetailResponse(BaseModel):
    h3_index: str
    avg_als: float = Field(ge=0.0, le=1.0)
    dominant_context: EdgeContext
    noise_db: float = Field(ge=0.0, le=140.0)
    status: ZoneStatus
    packet_count: int
    unique_user_count: int
    latest_timestamp: datetime
    context_counts: Dict[EdgeContext, int]
    recent_scores: List[float]


class AgentHotspotResponse(BaseModel):
    rank: int
    h3_index: str
    avg_als: float = Field(ge=0.0, le=1.0)
    dominant_context: EdgeContext
    noise_db: float = Field(ge=0.0, le=140.0)
    status: ZoneStatus
    packet_count: int
    unique_user_count: int
    latest_timestamp: datetime
    context_counts: Dict[EdgeContext, int]


class AgentHotspotsResponse(BaseModel):
    hotspots: List[AgentHotspotResponse]
    hotspot_count: int


class WatchPrivacyPacketItemResponse(BaseModel):
    user_id: str
    timestamp: datetime
    h3_index: str
    als_score: float
    context: EdgeContext
    noise_db: float


class WatchPrivacyPacketSequenceResponse(BaseModel):
    user_id: str
    packets: List[WatchPrivacyPacketItemResponse]
    model_version: str
    h3_resolution: int
    derivation_mode: str
