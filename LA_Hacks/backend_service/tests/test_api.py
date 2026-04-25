from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import model_loader
from app.session_state import edge_packet_store, watch_event_store
from app.settings import get_settings
from tests.test_training import make_prepared_frame
from training.features import expected_feature_names
from training.modeling import train_classifier


def make_valid_feature_payload() -> dict[str, float]:
    return {
        "accel_x_mean": 1.0,
        "accel_x_std": 0.2,
        "accel_x_min": 0.5,
        "accel_x_max": 1.5,
        "accel_x_median": 1.0,
        "accel_x_energy": 1.1,
        "accel_x_sma": 1.0,
        "accel_y_mean": 2.0,
        "accel_y_std": 0.3,
        "accel_y_min": 1.4,
        "accel_y_max": 2.6,
        "accel_y_median": 2.0,
        "accel_y_energy": 4.2,
        "accel_y_sma": 2.0,
        "accel_z_mean": 9.8,
        "accel_z_std": 0.4,
        "accel_z_min": 9.0,
        "accel_z_max": 10.4,
        "accel_z_median": 9.8,
        "accel_z_energy": 96.2,
        "accel_z_sma": 9.8,
        "accel_mag_mean": 10.1,
        "accel_mag_std": 0.35,
        "accel_mag_min": 9.4,
        "accel_mag_max": 10.8,
        "accel_mag_median": 10.1,
        "accel_mag_energy": 102.5,
        "accel_mag_sma": 10.1,
    }


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.artifacts_dir = Path(self.temp_dir.name) / "artifacts"
        train_classifier(make_prepared_frame(), artifacts_dir=self.artifacts_dir)
        watch_event_store.clear()
        edge_packet_store.clear()

        settings = get_settings()
        settings.artifacts_dir = self.artifacts_dir
        settings.model_path = self.artifacts_dir / "model.joblib"
        settings.metadata_path = self.artifacts_dir / "metadata.json"
        settings.feature_names_path = self.artifacts_dir / "feature_names.json"
        settings.metrics_path = self.artifacts_dir / "metrics.json"
        model_loader.reload_loaded_model()

        from app.main import app

        self.client = TestClient(app)

    def tearDown(self) -> None:
        model_loader.reload_loaded_model()
        self.temp_dir.cleanup()

    def test_health_ready(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ready")
        self.assertTrue(body["model_loaded"])

    def test_predict_context(self) -> None:
        features = make_valid_feature_payload()
        response = self.client.post(
            "/predict/context",
            json={"window_id": "w_001", "features": features},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn(body["context"], {"stationary", "walking", "running", "transit_like"})
        self.assertEqual(body["window_id"], "w_001")
        self.assertEqual(set(body["probabilities"].keys()), {"stationary", "walking", "running", "transit_like"})
        self.assertIsNone(body["smoothed_context"])

    def test_predict_context_missing_feature_is_filled(self) -> None:
        features = make_valid_feature_payload()
        features.pop("accel_x_mean")
        response = self.client.post("/predict/context", json={"features": features})
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json()["context"], {"stationary", "walking", "running", "transit_like"})

    def test_predict_context_with_session_returns_smoothed_output(self) -> None:
        features = make_valid_feature_payload()
        response = self.client.post(
            "/predict/context",
            json={
                "window_id": "w_001",
                "session_id": "demo-session",
                "smoothing_window": 3,
                "features": features,
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["session_id"], "demo-session")
        self.assertIsNotNone(body["smoothed_context"])
        self.assertIsNotNone(body["smoothed_probabilities"])

    def test_batch_empty_returns_422(self) -> None:
        response = self.client.post("/predict/context/batch", json={"items": []})
        self.assertEqual(response.status_code, 422)

    def test_ingest_watch_events(self) -> None:
        payload = {
            "user_id": "demo_user_01",
            "events": [
                {
                    "timestamp": "2026-04-24T10:15:30Z",
                    "location": {"lat": 34.0689, "lng": -118.4452},
                    "metrics": {
                        "heart_rate": 102,
                        "wrist_temperature": 0.6,
                        "environmental_sound_level": 71.4,
                        "exercise_time": 12,
                        "walking_distance": 0.42,
                        "running_distance": 0.0,
                        "physical_effort": 0.68,
                        "respiratory_rate": 19,
                        "blood_oxygen": 97,
                        "sleep": 6.5,
                        "walking_speed": 1.4,
                        "walking_steadiness": 0.82,
                        "step_length": 0.67,
                        "stair_speed": 0.0,
                        "stairs_up": 0,
                        "stairs_down": 0,
                        "stand_minutes": 18,
                        "active_energy": 44,
                        "resting_energy": 12,
                    },
                }
            ],
        }
        response = self.client.post("/ingest/watch-events", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["user_id"], "demo_user_01")
        self.assertEqual(body["accepted_events"], 1)
        self.assertEqual(body["stored_events"], 1)

    def test_get_watch_events(self) -> None:
        payload = {
            "user_id": "demo_user_02",
            "events": [
                {
                    "timestamp": "2026-04-24T10:15:30Z",
                    "location": {"lat": 34.0689, "lng": -118.4452},
                    "metrics": {
                        "heart_rate": 98,
                        "wrist_temperature": 0.4,
                        "environmental_sound_level": 65.0,
                        "exercise_time": 10,
                        "walking_distance": 0.3,
                        "running_distance": 0.0,
                        "physical_effort": 0.52,
                        "respiratory_rate": 17,
                        "blood_oxygen": 98,
                        "sleep": 7.2,
                        "walking_speed": 1.2,
                        "walking_steadiness": 0.88,
                        "step_length": 0.65,
                        "stair_speed": 0.0,
                        "stairs_up": 0,
                        "stairs_down": 0,
                        "stand_minutes": 12,
                        "active_energy": 35,
                        "resting_energy": 11,
                    },
                }
            ],
        }
        self.client.post("/ingest/watch-events", json=payload)
        response = self.client.get("/ingest/watch-events/demo_user_02")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["event_count"], 1)
        self.assertEqual(body["latest_event"]["metrics"]["heart_rate"], 98)

    def test_ingest_watch_events_rejects_invalid_running_distance(self) -> None:
        payload = {
            "user_id": "demo_user_03",
            "events": [
                {
                    "timestamp": "2026-04-24T10:15:30Z",
                    "location": {"lat": 34.0689, "lng": -118.4452},
                    "metrics": {
                        "heart_rate": 98,
                        "wrist_temperature": 0.4,
                        "environmental_sound_level": 65.0,
                        "exercise_time": 10,
                        "walking_distance": 0.3,
                        "running_distance": 0.4,
                        "physical_effort": 0.52,
                        "respiratory_rate": 17,
                        "blood_oxygen": 98,
                        "sleep": 7.2,
                        "walking_speed": 1.2,
                        "walking_steadiness": 0.88,
                        "step_length": 0.65,
                        "stair_speed": 0.0,
                        "stairs_up": 0,
                        "stairs_down": 0,
                        "stand_minutes": 12,
                        "active_energy": 35,
                        "resting_energy": 11,
                    },
                }
            ],
        }
        response = self.client.post("/ingest/watch-events", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_ingest_edge_packets_and_get_map_tiles(self) -> None:
        payload = {
            "packets": [
                {
                    "user_id": "demo_user_01",
                    "timestamp": "2026-04-24T10:15:30Z",
                    "h3_index": "8929a1d7577ffff",
                    "als_score": 0.82,
                    "context": "walking",
                    "noise_db": 72.0,
                },
                {
                    "user_id": "demo_user_02",
                    "timestamp": "2026-04-24T10:16:30Z",
                    "h3_index": "8929a1d7577ffff",
                    "als_score": 0.74,
                    "context": "walking",
                    "noise_db": 70.0,
                },
            ]
        }
        response = self.client.post("/ingest/edge-packets", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["accepted_packets"], 2)

        map_response = self.client.get("/map/tiles")
        self.assertEqual(map_response.status_code, 200)
        map_body = map_response.json()
        self.assertEqual(map_body["tile_count"], 1)
        tile = map_body["tiles"][0]
        self.assertEqual(tile["h3_index"], "8929a1d7577ffff")
        self.assertEqual(tile["dominant_context"], "walking")
        self.assertEqual(tile["status"], "red_zone")

    def test_ingest_edge_packets_rejects_invalid_context(self) -> None:
        payload = {
            "packets": [
                {
                    "user_id": "demo_user_01",
                    "timestamp": "2026-04-24T10:15:30Z",
                    "h3_index": "8929a1d7577ffff",
                    "als_score": 0.5,
                    "context": "running",
                    "noise_db": 72.0,
                }
            ]
        }
        response = self.client.post("/ingest/edge-packets", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_map_tiles_history(self) -> None:
        payload = {
            "packets": [
                {
                    "user_id": "demo_user_01",
                    "timestamp": "2026-04-24T10:15:30Z",
                    "h3_index": "8929a1d7577ffff",
                    "als_score": 0.82,
                    "context": "walking",
                    "noise_db": 72.0,
                },
                {
                    "user_id": "demo_user_02",
                    "timestamp": "2026-04-24T11:16:30Z",
                    "h3_index": "8929a1d7577ffff",
                    "als_score": 0.74,
                    "context": "walking",
                    "noise_db": 70.0,
                },
            ]
        }
        self.client.post("/ingest/edge-packets", json=payload)
        response = self.client.get("/map/tiles/history?bucket_minutes=60&limit=10")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["bucket_minutes"], 60)
        self.assertEqual(len(body["buckets"]), 2)

    def test_hotspot_detail(self) -> None:
        payload = {
            "packets": [
                {
                    "user_id": "demo_user_01",
                    "timestamp": "2026-04-24T10:15:30Z",
                    "h3_index": "8929a1d7577ffff",
                    "als_score": 0.82,
                    "context": "walking",
                    "noise_db": 72.0,
                },
                {
                    "user_id": "demo_user_02",
                    "timestamp": "2026-04-24T10:16:30Z",
                    "h3_index": "8929a1d7577ffff",
                    "als_score": 0.74,
                    "context": "walking",
                    "noise_db": 70.0,
                },
            ]
        }
        self.client.post("/ingest/edge-packets", json=payload)
        response = self.client.get("/map/tiles/8929a1d7577ffff")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["h3_index"], "8929a1d7577ffff")
        self.assertEqual(body["packet_count"], 2)
        self.assertEqual(body["unique_user_count"], 2)
        self.assertIn("recent_scores", body)

    def test_agent_hotspots(self) -> None:
        payload = {
            "packets": [
                {
                    "user_id": "demo_user_01",
                    "timestamp": "2026-04-24T10:15:30Z",
                    "h3_index": "8929a1d7577ffff",
                    "als_score": 0.82,
                    "context": "walking",
                    "noise_db": 72.0,
                },
                {
                    "user_id": "demo_user_02",
                    "timestamp": "2026-04-24T10:16:30Z",
                    "h3_index": "8929a1d7577ffff",
                    "als_score": 0.74,
                    "context": "walking",
                    "noise_db": 70.0,
                },
                {
                    "user_id": "demo_user_03",
                    "timestamp": "2026-04-24T10:17:30Z",
                    "h3_index": "8929a1d7578ffff",
                    "als_score": 0.41,
                    "context": "stationary",
                    "noise_db": 50.0,
                },
            ]
        }
        self.client.post("/ingest/edge-packets", json=payload)
        response = self.client.get("/agents/hotspots?limit=2")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["hotspot_count"], 2)
        self.assertEqual(body["hotspots"][0]["rank"], 1)
        self.assertEqual(body["hotspots"][0]["h3_index"], "8929a1d7577ffff")

    def test_agent_red_zone_alerts(self) -> None:
        payload = {
            "packets": [
                {
                    "user_id": "demo_user_01",
                    "timestamp": "2026-04-24T10:15:30Z",
                    "h3_index": "8929a1d7577ffff",
                    "als_score": 0.82,
                    "context": "walking",
                    "noise_db": 72.0,
                },
                {
                    "user_id": "demo_user_02",
                    "timestamp": "2026-04-24T10:16:30Z",
                    "h3_index": "8929a1d7577ffff",
                    "als_score": 0.74,
                    "context": "walking",
                    "noise_db": 70.0,
                },
            ]
        }
        self.client.post("/ingest/edge-packets", json=payload)
        response = self.client.get("/agents/diagnosis/red-zone-alerts?limit=5")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["alert_count"], 1)
        self.assertEqual(body["alerts"][0]["noise_bucket"], "High")

    def test_agent_simulation_request(self) -> None:
        payload = {
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
        }
        self.client.post("/ingest/edge-packets", json=payload)
        response = self.client.get("/agents/simulation-request/8929a1d7577ffff")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("diagnosis", body)
        self.assertIn("failure_modes", body["diagnosis"])

    def test_agent_planning_request(self) -> None:
        payload = {
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
        }
        self.client.post("/ingest/edge-packets", json=payload)
        response = self.client.get("/agents/planning-request/8929a1d7577ffff")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertGreaterEqual(len(body["scenarios"]), 1)
        self.assertIn("scenario_name", body["scenarios"][0])

    def test_simulate_intervention(self) -> None:
        payload = {
            "packets": [
                {
                    "user_id": "demo_user_01",
                    "timestamp": "2026-04-24T10:15:30Z",
                    "h3_index": "8929a1d7577ffff",
                    "als_score": 0.82,
                    "context": "walking",
                    "noise_db": 72.0,
                },
                {
                    "user_id": "demo_user_02",
                    "timestamp": "2026-04-24T10:16:30Z",
                    "h3_index": "8929a1d7577ffff",
                    "als_score": 0.74,
                    "context": "walking",
                    "noise_db": 70.0,
                },
            ]
        }
        self.client.post("/ingest/edge-packets", json=payload)
        response = self.client.post(
            "/simulate/intervention",
            json={
                "h3_index": "8929a1d7577ffff",
                "intervention_type": "shade_canopy",
                "intensity": 1.0,
                "budget_usd": 15000,
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["intervention_type"], "shade_canopy")
        self.assertLess(body["after"]["avg_als"], body["before"]["avg_als"])
        self.assertGreater(body["estimated_als_reduction"], 0.0)

    def test_simulate_intervention_unknown_tile_returns_404(self) -> None:
        response = self.client.post(
            "/simulate/intervention",
            json={
                "h3_index": "missing-tile",
                "intervention_type": "shade_canopy",
                "intensity": 1.0,
                "budget_usd": 15000,
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_map_tiles_websocket_streams_updates(self) -> None:
        with self.client.websocket_connect("/ws/map/tiles") as websocket:
            initial = websocket.receive_json()
            self.assertEqual(initial["tile_count"], 0)

            ingest_payload = {
                "packets": [
                    {
                        "user_id": "demo_user_01",
                        "timestamp": "2026-04-24T10:15:30Z",
                        "h3_index": "8929a1d7577ffff",
                        "als_score": 0.79,
                        "context": "walking",
                        "noise_db": 73.0,
                    }
                ]
            }
            response = self.client.post("/ingest/edge-packets", json=ingest_payload)
            self.assertEqual(response.status_code, 200)

            update = websocket.receive_json()
            self.assertEqual(update["tile_count"], 1)
            self.assertEqual(update["tiles"][0]["h3_index"], "8929a1d7577ffff")

    def test_non_numeric_feature_returns_422(self) -> None:
        features = make_valid_feature_payload()
        features["accel_x_mean"] = "bad"
        response = self.client.post("/predict/context", json={"features": features})
        self.assertEqual(response.status_code, 422)

    def test_unexpected_feature_returns_422(self) -> None:
        features = make_valid_feature_payload()
        features["unexpected"] = 2.0
        response = self.client.post("/predict/context", json={"features": features})
        self.assertEqual(response.status_code, 422)

    def test_inconsistent_feature_stats_return_422(self) -> None:
        features = make_valid_feature_payload()
        features["accel_x_min"] = 5.0
        features["accel_x_mean"] = 1.0
        features["accel_x_median"] = 1.0
        features["accel_x_max"] = 2.0
        response = self.client.post("/predict/context", json={"features": features})
        self.assertEqual(response.status_code, 422)

    def test_sequence_endpoint_returns_smoothed_predictions(self) -> None:
        base = make_valid_feature_payload()
        items = [
            {"window_id": "w1", "features": base},
            {"window_id": "w2", "features": base},
            {"window_id": "w3", "features": base},
        ]
        response = self.client.post(
            "/predict/context/sequence",
            json={"items": items, "smoothing_window": 3},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["smoothing_window"], 3)
        self.assertEqual(len(body["predictions"]), 3)
        self.assertIn("smoothed_context", body["predictions"][0])
        self.assertIn("smoothed_probabilities", body["predictions"][0])


if __name__ == "__main__":
    unittest.main()
