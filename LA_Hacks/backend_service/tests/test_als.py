from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from app import als_model_loader, model_loader
from app.settings import get_settings
from training.als_constants import ALS_FEATURE_NAMES
from training.als_modeling import train_als_regressor


def make_als_frame(rows_per_subject: int = 12) -> pd.DataFrame:
    rows = []
    subject_targets = {
        "s1": 0.15,
        "s2": 0.25,
        "s3": 0.40,
        "s4": 0.55,
        "s5": 0.70,
        "s6": 0.85,
    }
    for subject_index, (subject_id, target) in enumerate(subject_targets.items(), start=1):
        for row_index in range(rows_per_subject):
            row = {
                "subject_id": subject_id,
                "als_target": target,
                "hrv_rmssd": 50.0 - (target * 20.0) + row_index * 0.05,
                "hrv_sdnn": 45.0 - (target * 15.0) + row_index * 0.03,
                "hrv_pnn50": 35.0 - (target * 10.0) + row_index * 0.02,
                "hr_mean": 70.0 + (target * 40.0) + row_index * 0.1,
                "hr_variance": 4.0 + (target * 10.0),
                "skin_temp_delta": -0.5 + (target * 2.0),
                "ambient_noise_db": 45.0 + (target * 25.0),
                "accel_intensity_mean": 0.2 + (subject_index * 0.1),
            }
            rows.append(row)
    return pd.DataFrame(rows)


def make_valid_als_payload() -> dict[str, float]:
    return {
        "hrv_rmssd": 38.0,
        "hrv_sdnn": 32.0,
        "hrv_pnn50": 18.0,
        "hr_mean": 96.0,
        "hr_variance": 9.0,
        "skin_temp_delta": 0.8,
        "ambient_noise_db": 74.0,
        "accel_intensity_mean": 0.5,
    }


def make_watch_event(timestamp: str, heart_rate: float = 98.0, noise: float = 68.0) -> dict:
    return {
        "timestamp": timestamp,
        "location": {"lat": 34.0689, "lng": -118.4452},
        "metrics": {
            "heart_rate": heart_rate,
            "wrist_temperature": 0.5,
            "environmental_sound_level": noise,
            "exercise_time": 12,
            "walking_distance": 0.42,
            "running_distance": 0.0,
            "physical_effort": 0.62,
            "respiratory_rate": 18,
            "blood_oxygen": 97,
            "sleep": 6.8,
            "walking_speed": 1.35,
            "walking_steadiness": 0.84,
            "step_length": 0.66,
            "stair_speed": 0.0,
            "stairs_up": 0,
            "stairs_down": 0,
            "stand_minutes": 18,
            "active_energy": 44,
            "resting_energy": 12,
        },
    }


class AlsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.als_artifacts_dir = Path(self.temp_dir.name) / "artifacts" / "als"
        train_als_regressor(make_als_frame(), artifacts_dir=self.als_artifacts_dir)

        settings = get_settings()
        settings.als_artifacts_dir = self.als_artifacts_dir
        settings.als_model_path = self.als_artifacts_dir / "model.joblib"
        settings.als_metadata_path = self.als_artifacts_dir / "metadata.json"
        settings.als_feature_names_path = self.als_artifacts_dir / "feature_names.json"
        settings.als_metrics_path = self.als_artifacts_dir / "metrics.json"
        als_model_loader.reload_loaded_als_model()
        model_loader.reload_loaded_model()

        from app.main import app

        self.client = TestClient(app)

    def tearDown(self) -> None:
        als_model_loader.reload_loaded_als_model()
        self.temp_dir.cleanup()

    def test_train_als_regressor_saves_artifacts(self) -> None:
        self.assertTrue((self.als_artifacts_dir / "model.joblib").exists())
        self.assertTrue((self.als_artifacts_dir / "metadata.json").exists())
        self.assertTrue((self.als_artifacts_dir / "feature_names.json").exists())
        self.assertTrue((self.als_artifacts_dir / "metrics.json").exists())

    def test_predict_als(self) -> None:
        response = self.client.post("/predict/als", json={"features": make_valid_als_payload()})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertGreaterEqual(body["als_score"], 0.0)
        self.assertLessEqual(body["als_score"], 1.0)
        self.assertIn(body["stress_band"], {"low", "elevated", "high"})

    def test_predict_als_missing_feature_is_filled(self) -> None:
        payload = make_valid_als_payload()
        payload.pop("ambient_noise_db")
        response = self.client.post("/predict/als", json={"features": payload})
        self.assertEqual(response.status_code, 200)

    def test_predict_als_with_session_returns_smoothed_output(self) -> None:
        response = self.client.post(
            "/predict/als",
            json={
                "window_id": "als_1",
                "session_id": "als-demo",
                "smoothing_window": 3,
                "features": make_valid_als_payload(),
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsNotNone(body["smoothed_als_score"])
        self.assertIsNotNone(body["smoothed_stress_band"])

    def test_predict_als_unknown_feature_returns_422(self) -> None:
        payload = make_valid_als_payload()
        payload["unknown"] = 1.0
        response = self.client.post("/predict/als", json={"features": payload})
        self.assertEqual(response.status_code, 422)

    def test_predict_als_sequence(self) -> None:
        payload = {
            "items": [
                {"window_id": "als_1", "features": make_valid_als_payload()},
                {"window_id": "als_2", "features": make_valid_als_payload()},
            ],
            "smoothing_window": 3,
        }
        response = self.client.post("/predict/als/sequence", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body["predictions"]), 2)

    def test_als_model_info(self) -> None:
        response = self.client.get("/als/model/info")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["feature_names"], ALS_FEATURE_NAMES)

    def test_predict_als_from_watch_sequence(self) -> None:
        payload = {
            "user_id": "demo_user_01",
            "items": [
                make_watch_event("2026-04-24T10:15:30Z", heart_rate=92.0, noise=62.0),
                make_watch_event("2026-04-24T10:16:30Z", heart_rate=104.0, noise=75.0),
            ],
            "smoothing_window": 2,
        }
        response = self.client.post("/predict/als/watch/sequence", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["user_id"], "demo_user_01")
        self.assertEqual(len(body["predictions"]), 2)
        self.assertEqual(body["derivation_mode"], "heuristic_watch_metrics_v1")
        self.assertEqual(
            set(body["predictions"][0]["derived_features"].keys()),
            set(ALS_FEATURE_NAMES),
        )

    def test_predict_als_from_watch_sequence_reacts_to_higher_load(self) -> None:
        payload = {
            "user_id": "demo_user_02",
            "items": [
                make_watch_event("2026-04-24T10:15:30Z", heart_rate=78.0, noise=50.0),
                make_watch_event("2026-04-24T10:16:30Z", heart_rate=118.0, noise=82.0),
            ],
            "smoothing_window": 1,
        }
        response = self.client.post("/predict/als/watch/sequence", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        first = body["predictions"][0]
        second = body["predictions"][1]
        self.assertLess(first["derived_features"]["hr_mean"], second["derived_features"]["hr_mean"])
        self.assertGreaterEqual(second["als_score"], first["als_score"])

    def test_predict_privacy_packets_from_watch_sequence(self) -> None:
        payload = {
            "user_id": "demo_user_03",
            "events": [
                make_watch_event("2026-04-24T10:15:30Z", heart_rate=88.0, noise=55.0),
                make_watch_event("2026-04-24T10:16:30Z", heart_rate=110.0, noise=78.0),
            ],
            "smoothing_window": 2,
        }
        response = self.client.post("/predict/als/watch/privacy-packets", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["user_id"], "demo_user_03")
        self.assertEqual(body["h3_resolution"], 9)
        self.assertEqual(len(body["packets"]), 2)
        packet = body["packets"][0]
        self.assertEqual(packet["user_id"], "demo_user_03")
        self.assertIn(packet["context"], {"stationary", "walking", "transit_like"})
        self.assertIsInstance(packet["h3_index"], str)


if __name__ == "__main__":
    unittest.main()
