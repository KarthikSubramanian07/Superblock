# Prize Track Runbook

This repo now covers the backend-side requirements for the ZETIC and Arista prizes as far as we can complete them inside the Python codebase.

## Completed In Repo

- Context classifier backend is trained and served.
- Context classifier can be exported to ONNX for Melange.
- ALS can be derived from watch-style events.
- Privacy-safe edge packets can be generated from watch-style events.
- H3 resolution-9 indexing is built into the privacy packet path.
- Privacy-safe packets can be ingested and aggregated into map tiles.
- A minimal `uAgent` forwarding bridge exists for the Arista story.

## ZETIC: What You Need To Run

### 1. Export the context model to ONNX

Run:

```bash
python3 scripts/export_context_model_onnx.py
```

This writes:

- `artifacts/context_classifier.onnx`
- `artifacts/context_classifier_sample_input.npy`

### 2. Convert or upload through Melange

Based on ZETIC's docs, Melange currently supports `ONNX` and `.pt2` inputs and provisions hardware-accelerated deployment artifacts through the dashboard or CLI.

What you should use from this repo:

- model: `artifacts/context_classifier.onnx`
- sample input: `artifacts/context_classifier_sample_input.npy`

Then follow the ZETIC flow to:

1. create a model key
2. create or copy a personal key
3. integrate the Melange iOS SDK into the Apple app
4. initialize the model with your keys

### 3. Prove NPU execution during the demo

This cannot be completed in the Python backend alone.

You need to run the Melange-backed model on the Apple device and capture:

- device name
- model name
- processor target
- latency

Minimum demo proof:

- one screenshot or log proving Melange selected Apple Neural Engine
- one latency comparison showing NPU faster than CPU

### 4. Enforce privacy in the app

For the final demo app, do not send raw heart rate, temperature, or noise time series to the backend.

The app should only transmit:

- `als_score`
- `context`
- `h3_index`
- `noise_db`

Important note:

Your requirement list says only `ALS_Score`, `Context`, and `H3_Tile` should leave the device, but the map API contract also asks for `noise_db`. The team needs to make one final decision here.

## Arista: What You Need To Run

### 1. Run the FastAPI backend

```bash
uvicorn app.main:app --reload
```

### 2. Run the uAgent bridge

```bash
python3 scripts/run_ingestion_uagent.py
```

This gives you a discoverable agent process that can forward privacy-safe packets into the backend.

### 3. Feed privacy-safe packets into the backend

For mock data:

```bash
python3 scripts/load_mock_privacy_packets.py --json living_city_mock_data/mock_events.json --limit-users 3
```

### 4. Frontend polling endpoint

Use:

```text
GET /map/tiles
```

Each tile looks like:

```json
{
  "h3_index": "string",
  "avg_als": 0.0,
  "dominant_context": "walking",
  "noise_db": 71.2,
  "status": "red_zone"
}
```

## Suggested Demo Flow

1. Export the context classifier to ONNX before the event.
2. Upload or convert it in Melange.
3. Integrate the Melange-backed context model in the Apple app.
4. Run context inference on-device.
5. Derive `context`, `als_score`, and `h3_index` on-device.
6. Send only privacy-safe packets to `/ingest/edge-packets` or through the uAgent bridge.
7. Point the frontend at `GET /map/tiles`.
8. Show Melange benchmark evidence separately during the pitch.
