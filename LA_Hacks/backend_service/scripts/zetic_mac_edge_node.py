import json
import time
import argparse
from datetime import datetime
from pathlib import Path

import h3
import numpy as np
import onnxruntime as ort
import requests

ALS_FEATURE_NAMES = [
    "hrv_rmssd",
    "hrv_sdnn",
    "hrv_pnn50",
    "hr_mean",
    "hr_variance",
    "skin_temp_delta",
    "ambient_noise_db",
    "accel_intensity_mean",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ZETIC Macbook Edge Simulator")
    parser.add_argument(
        "--onnx-model",
        default="artifacts/als/als_model.onnx",
        help="Path to the quantized/ONNX model",
    )
    parser.add_argument(
        "--data",
        default="living_city_mock_data/mock_events.json",
        help="Path to the raw biometric data stream",
    )
    parser.add_argument(
        "--endpoint",
        default="http://localhost:8000/ingest/edge-packets",
        help="FastAPI Backend Endpoint",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=0.1,
        help="Delay between streaming events",
    )
    return parser


def map_metrics_to_features(metrics: dict) -> np.ndarray:
    """Map raw Apple Watch mock metrics to the ALS feature vector expected by the model."""
    feature_dict = {
        "hrv_rmssd": 45.0 + (metrics.get("physical_effort", 0.0) * 10),
        "hrv_sdnn": 50.0,
        "hrv_pnn50": 20.0,
        "hr_mean": float(metrics.get("heart_rate", 70)),
        "hr_variance": 5.0,
        "skin_temp_delta": float(metrics.get("wrist_temperature", 0.1)),
        "ambient_noise_db": float(metrics.get("environmental_sound_level", 40)),
        "accel_intensity_mean": float(metrics.get("physical_effort", 0.0)),
    }
    
    # Ensure exact order as ALS_FEATURE_NAMES
    vector = [feature_dict[name] for name in ALS_FEATURE_NAMES]
    return np.array(vector, dtype=np.float32).reshape(1, -1)


def determine_context(metrics: dict) -> str:
    """Simple heuristic to determine context for the edge packet."""
    speed = metrics.get("walking_speed", 0.0)
    if speed > 0.01:
        return "walking"
    return "stationary"


def main():
    args = build_parser().parse_args()
    
    print("=" * 60)
    print(" ZETIC MACBOOK EDGE SIMULATOR INITIALIZING...")
    print(" Target Hardware: Apple Silicon Neural Engine (Simulated)")
    print("=" * 60)
    
    # 1. Load ONNX model locally
    try:
        session = ort.InferenceSession(args.onnx_model, providers=["CPUExecutionProvider"])
        input_name = session.get_inputs()[0].name
        print(f"[OK] Loaded ONNX model from {args.onnx_model}")
    except Exception as e:
        print(f"[ERROR] Failed to load ONNX model: {e}")
        return

    # 2. Load the "Streaming" Data
    try:
        with open(args.data, "r") as f:
            all_users_data = json.load(f)
        print(f"[OK] Connected to local Apple Watch stream ({len(all_users_data)} users)")
    except Exception as e:
        print(f"[ERROR] Failed to load mock data: {e}")
        return

    # 3. Process stream and send ONLY ALS Score
    print("\n--- STARTING SECURE ZERO-KNOWLEDGE EDGE INFERENCE ---\n")
    
    # Just simulate streaming for the first user to avoid overwhelming the log
    user_data = all_users_data[0]
    user_id = user_data["user_id"]
    
    for event in user_data["events"][:20]:  # Just do 20 events for demo
        metrics = event["metrics"]
        lat = event["location"]["lat"]
        lng = event["location"]["lng"]
        timestamp = event["timestamp"]
        
        # Local Inference (The ZETIC part)
        start_time = time.perf_counter()
        features = map_metrics_to_features(metrics)
        result = session.run(None, {input_name: features})
        als_score = float(np.squeeze(result[0]))
        inference_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Determine H3 and Context locally
        h3_index = getattr(h3, "latlng_to_cell", getattr(h3, "geo_to_h3", None))(lat, lng, 9)
        context = determine_context(metrics)
        
        print(f"[Local NPU] Processed {len(ALS_FEATURE_NAMES)} raw biometrics. Latency: {inference_time_ms:.2f}ms. Generated ALS Score: {als_score:.3f}")
        
        # Construct the Privacy-Safe Packet
        packet = {
            "user_id": user_id,
            "timestamp": timestamp,
            "h3_index": h3_index,
            "als_score": als_score,
            "context": context,
            "noise_db": metrics.get("environmental_sound_level", 0.0)
        }
        
        payload = {"packets": [packet]}
        
        # Send to Backend with custom ZETIC header
        headers = {
            "Content-Type": "application/json",
            "X-Inference-Location": "On-Device-NPU",
            "X-Inference-Engine": "ZETIC_Melange_macOS"
        }
        
        try:
            resp = requests.post(args.endpoint, json=payload, headers=headers)
            if resp.status_code == 200:
                print(f"[Cloud Sync] Sent anonymized packet to backend. Raw biometrics discarded.\n")
            else:
                print(f"[Cloud Sync] Error {resp.status_code}: {resp.text}\n")
        except requests.exceptions.ConnectionError:
            print("[Cloud Sync] Failed to connect to backend. Is FastAPI running?\n")
            
        time.sleep(args.speed)

    print("=" * 60)
    print(" EDGE INFERENCE STREAM COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
