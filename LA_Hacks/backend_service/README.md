# FastAPI Context + ALS Models

This project implements the first two modeling layers for The Living City:

- Model 1: a development-ready context classifier trained on WISDM smartwatch accelerometer data
- Model 2: an ALS regressor trained from prepared physiology features and served through FastAPI

## What it does

- Downloads or reads the WISDM smartwatch accelerometer dataset
- Builds fixed windows and extracts motion features
- Maps raw WISDM activities into four development classes:
  - `stationary`
  - `walking`
  - `running`
  - `transit_like`
- Trains a baseline classifier
- Persists model artifacts for serving
- Exposes prediction endpoints for precomputed motion features

## Dataset

This implementation is built around the UCI WISDM Smartphone and Smartwatch Activity and Biometrics Dataset:

- UCI dataset page: <https://archive.ics.uci.edu/dataset/507/wisdm+smartphone+and+smartwatch+activity+and+biometrics+dataset>
- Default download URL used by the training CLI:
  `https://archive.ics.uci.edu/static/public/507/wisdm+smartphone+and+smartwatch+activity+and+biometrics+dataset.zip`

The service uses smartwatch accelerometer data only for Model 1.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`httpx` is included because FastAPI's `TestClient` depends on it for API tests.

## Train the model

Prepare a feature dataset from WISDM:

```bash
python3 -m training.cli prepare --output-csv data/context_features.csv
```

Train artifacts from a prepared CSV:

```bash
python3 -m training.cli train --prepared-csv data/context_features.csv --artifacts-dir artifacts
```

Or train directly from raw/extracted WISDM files:

```bash
python3 -m training.cli train --artifacts-dir artifacts
```

Evaluate a trained model:

```bash
python3 -m training.cli evaluate --prepared-csv data/context_features.csv --artifacts-dir artifacts
```

## Train the ALS model

Phase 2 assumes feature extraction is handled elsewhere. Prepare a CSV with:

- `subject_id`
- one of `als_target`, `stress_label`, `stress_state`, or `label`
- `hrv_rmssd`
- `hrv_sdnn`
- `hrv_pnn50`
- `hr_mean`
- `hr_variance`
- `skin_temp_delta`
- `ambient_noise_db`
- `accel_intensity_mean`

Train ALS artifacts:

```bash
python3 -m training.cli train-als --prepared-csv data/als_features.csv --artifacts-dir artifacts/als
```

Evaluate ALS artifacts:

```bash
python3 -m training.cli evaluate-als --prepared-csv data/als_features.csv --artifacts-dir artifacts/als
```

If you just need demo-ready ALS artifacts locally, you can bootstrap a synthetic ALS training set and train the artifacts in one step:

```bash
python3 scripts/bootstrap_demo_als_artifacts.py
```

## Run the API

```bash
uvicorn app.main:app --reload
```

If your environment blocks binding a local port during development checks, you can still validate the app through the test suite:

```bash
python3 -m unittest discover -s tests -v
```

To load the repo's synthetic Apple Watch data into the Stage 1 ingestion endpoint:

```bash
python3 scripts/load_mock_watch_events.py --json living_city_mock_data/mock_events.json
```

You can limit the first pass to a few users while iterating:

```bash
python3 scripts/load_mock_watch_events.py --json living_city_mock_data/mock_events.json --limit-users 3
```

To load the same mock data through the privacy-safe prize-track flow:

```bash
python3 scripts/load_mock_privacy_packets.py --json living_city_mock_data/mock_events.json --limit-users 3
```

To export the trained context classifier to ONNX for the ZETIC Melange flow:

```bash
python3 scripts/export_context_model_onnx.py
```

See [docs/prize_track_runbook.md](/Users/jeevikakiran/Documents/PersonalLearning/LAHacks/docs/prize_track_runbook.md) for the remaining ZETIC and Arista device/demo steps.

## API

### `POST /ingest/watch-events`

Use this Stage 1 endpoint to ingest Apple Watch-style event data for a single user. The API expects JSON, not CSV.

Request:

```json
{
  "user_id": "demo_user_01",
  "events": [
    {
      "timestamp": "2026-04-24T10:15:30Z",
      "location": {
        "lat": 34.0689,
        "lng": -118.4452
      },
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
        "resting_energy": 12
      }
    }
  ]
}
```

Notes:
- `running_distance` must be less than or equal to `walking_distance` for the same event.
- `physical_effort` and `walking_steadiness` are normalized `0..1`.
- The current Stage 1 implementation stores accepted events in memory for local development and integration testing.

### `GET /ingest/watch-events/{user_id}`

Returns all accepted watch events currently stored for a user, along with the latest event and event count.

### `POST /ingest/edge-packets`

Use this for the prize-track backend path. These packets contain only the privacy-safe fields that should leave the device.

Request:

```json
{
  "packets": [
    {
      "user_id": "demo_user_01",
      "timestamp": "2026-04-24T10:15:30Z",
      "h3_index": "8929a1d7577ffff",
      "als_score": 0.82,
      "context": "walking",
      "noise_db": 72.0
    }
  ]
}
```

### `GET /map/tiles`

Polling endpoint for the 3D map. Each tile item follows this shape:

```json
{
  "h3_index": "8929a1d7577ffff",
  "avg_als": 0.78,
  "dominant_context": "walking",
  "noise_db": 71.0,
  "status": "red_zone"
}
```

The full response is:

```json
{
  "tiles": [
    {
      "h3_index": "8929a1d7577ffff",
      "avg_als": 0.78,
      "dominant_context": "walking",
      "noise_db": 71.0,
      "status": "red_zone"
    }
  ],
  "tile_count": 1
}
```

### `WS /ws/map/tiles`

WebSocket endpoint for live map updates. It streams the same payload shape as `GET /map/tiles`.

Behavior:
- sends an initial snapshot when the client connects
- sends a fresh snapshot whenever new edge packets are ingested

### `GET /map/tiles/history`

Historical replay endpoint for the frontend. Query params:
- `bucket_minutes`: time bucket size, default `60`
- `limit`: max number of buckets to return, default `24`

Response:

```json
{
  "bucket_minutes": 60,
  "buckets": [
    {
      "bucket_start": "2026-04-24T10:00:00Z",
      "tile_count": 1,
      "tiles": [
        {
          "h3_index": "8929a1d7577ffff",
          "avg_als": 0.78,
          "dominant_context": "walking",
          "noise_db": 71.0,
          "status": "red_zone"
        }
      ]
    }
  ]
}
```

### `GET /map/tiles/{h3_index}`

Hotspot detail endpoint for drill-down cards and side panels.

Response includes:
- tile summary fields
- `packet_count`
- `unique_user_count`
- `latest_timestamp`
- `context_counts`
- `recent_scores`

### `GET /agents/hotspots`

Agent-facing hotspot payload endpoint. Query param:
- `limit`: max hotspots to return, default `10`

Returns ranked hotspot objects with:
- `rank`
- `h3_index`
- `avg_als`
- `dominant_context`
- `noise_db`
- `status`
- `packet_count`
- `unique_user_count`
- `latest_timestamp`
- `context_counts`

### `POST /simulate/intervention`

Simulation backend endpoint for what-if analysis.

Request:

```json
{
  "h3_index": "8929a1d7577ffff",
  "intervention_type": "shade_canopy",
  "intensity": 1.0,
  "budget_usd": 15000
}
```

Supported intervention types:
- `shade_canopy`
- `longer_crossing_time`
- `parklet`
- `pedestrian_bridge`

Response includes:
- `estimated_cost_usd`
- `estimated_als_reduction`
- `estimated_noise_reduction_db`
- `impact_score`
- `before`
- `after`
- `assumptions`

### `GET /agents/diagnosis/red-zone-alerts`

Returns agent-ready red zone alerts shaped for the existing diagnosis layer in `LA_Hacks/`.

### `GET /agents/simulation-request/{h3_index}`

Returns an agent-ready simulation request payload with:
- `diagnosis.failure_modes`
- `diagnosis.root_causes`
- `diagnosis.recommendations`
- `diagnosis.confidence`

### `GET /agents/planning-request/{h3_index}`

Returns an agent-ready planning payload with simulated intervention scenarios shaped for the planner agent.

### `GET /health`

Returns whether model artifacts are loaded and ready.

### `GET /model/info`

Returns model version, classifier type, feature names, class list, and the current feature-validation contract used by the API.

### `GET /als/model/info`

Returns ALS model version, regressor type, feature names, training metrics, and the ALS feature contract.

### `POST /predict/context`

Request:

```json
{
  "window_id": "w_001",
  "features": {
    "accel_x_mean": 0.12,
    "accel_y_mean": -0.04,
    "accel_z_mean": 9.71,
    "accel_mag_std": 0.83,
    "accel_mag_energy": 18.2
  }
}
```

Response:

```json
{
  "window_id": "w_001",
  "context": "walking",
  "probabilities": {
    "running": 0.02,
    "stationary": 0.06,
    "transit_like": 0.01,
    "walking": 0.91
  },
  "model_version": "context-classifier-v1"
}
```

### `POST /predict/context/batch`

Request:

```json
{
  "items": [
    {
      "window_id": "w_001",
      "features": {
        "accel_x_mean": 0.12,
        "accel_y_mean": -0.04,
        "accel_z_mean": 9.71
      }
    }
  ]
}
```

Items may omit features. Missing known features are filled with the default value used by the API. Unknown feature names are rejected.

### `POST /predict/context/sequence`

Use this for ordered windows from the same user/session when you want steadier demo output.

Request:

```json
{
  "items": [
    {
      "window_id": "w_001",
      "features": {
        "accel_x_mean": 0.12,
        "accel_x_std": 0.44
      }
    }
  ],
  "smoothing_window": 3
}
```

Response items include both raw and smoothed outputs:
- `context`
- `smoothed_context`
- `probabilities`
- `smoothed_probabilities`

### `POST /predict/als`

Use this for per-window ALS inference. If you include `session_id`, the API automatically returns rolling smoothed ALS output for live/demo workflows.

Request:

```json
{
  "window_id": "als_001",
  "session_id": "judge-demo-1",
  "smoothing_window": 3,
  "features": {
    "hrv_rmssd": 34.2,
    "hrv_sdnn": 28.5,
    "hrv_pnn50": 12.7,
    "hr_mean": 96.0,
    "hr_variance": 8.1,
    "skin_temp_delta": 0.6,
    "ambient_noise_db": 73.0,
    "accel_intensity_mean": 0.3
  }
}
```

Response:

```json
{
  "window_id": "als_001",
  "session_id": "judge-demo-1",
  "als_score": 0.78,
  "smoothed_als_score": 0.74,
  "stress_band": "high",
  "smoothed_stress_band": "high",
  "model_version": "als-regressor-v1"
}
```

### `POST /predict/als/sequence`

Use this for ordered historical windows when you want raw and smoothed ALS in one response.

### `POST /predict/als/watch/sequence`

Use this when you have Stage 1 Apple Watch-style event payloads instead of precomputed ALS features. The API derives the ALS feature set from watch metrics using a heuristic mapping, then runs the existing ALS regressor.

Request:

```json
{
  "user_id": "demo_user_01",
  "items": [
    {
      "timestamp": "2026-04-24T10:15:30Z",
      "location": {
        "lat": 34.0689,
        "lng": -118.4452
      },
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
        "resting_energy": 12
      }
    }
  ],
  "smoothing_window": 3
}
```

Response items include:
- `als_score`
- `smoothed_als_score`
- `stress_band`
- `smoothed_stress_band`
- `derived_features`

Notes:
- This route is the Stage 2 bridge between raw watch-style events and the trained ALS model.
- HRV-related ALS features are estimated heuristically from the available watch metrics because the current Stage 1 event schema does not include raw HRV inputs yet.

### `POST /predict/als/watch/privacy-packets`

Use this to convert Stage 1 watch-style events into privacy-safe edge packets. It derives ALS, infers a coarse context label, and computes an H3 resolution-9 index from the event location.

Response packet items include:
- `timestamp`
- `h3_index`
- `als_score`
- `context`
- `noise_db`

## Notes

- `transit_like` is a temporary development class derived from stair and similar movement patterns. Replace it with real transit and vehicle classes once you have first-party watch data.
- The original raw watch-event ingestion route is still available for local development, but the prize-track backend path should use privacy-safe packets through `/ingest/edge-packets`.
- If `lightgbm` is not installed, the training pipeline falls back to `RandomForestClassifier`.
- Training now uses a `subject-wise` split based on `subject_id`, so metrics better reflect generalization to unseen users.
- The feature contract is locked for now: the API recognizes 28 feature names, fills missing known features with a default value, rejects unknown features, requires finite values, and checks internal consistency for any summary-stat groups you provide.
- For demo stability, use `/predict/context/sequence` with a smoothing window of `3` or `5` on consecutive windows from the same user.
- ALS v1 is a development regressor for prepared features. It is meant to support demos and pipeline integration before you have enough first-party biometric training data.
- `scripts/run_ingestion_uagent.py` is a minimal Arista-facing bridge that receives discoverable uAgent messages and forwards them into the FastAPI edge ingestion route.

## Smoke test a running API

After starting FastAPI, you can send a real sample from the prepared CSV:

```bash
python3 scripts/send_sample_prediction.py --csv data/context_features.csv
```

By default it calls `http://127.0.0.1:8000/predict/context`. Override with `--url` if needed.

To simulate a live smoothed session across consecutive windows:

```bash
python3 scripts/send_sample_prediction.py --csv data/context_features.csv --row-index 100 --count 3 --session-id demo-1 --smoothing-window 3
```

If you have a prepared ALS CSV, you can smoke-test the ALS endpoint too:

```bash
python3 scripts/send_sample_als_prediction.py --csv data/als_features.csv --row-index 0 --count 3 --session-id als-demo
```

## Run tests

```bash
python3 -m unittest discover -s tests -v
```
