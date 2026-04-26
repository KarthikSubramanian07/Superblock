from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

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
    parser = argparse.ArgumentParser(
        description="Export the trained ALS Regressor to ONNX for ZETIC Melange.",
    )
    parser.add_argument(
        "--model-path",
        default="artifacts/als/model.joblib",
        help="Path to the trained sklearn Regressor artifact.",
    )
    parser.add_argument(
        "--output-onnx",
        default="artifacts/als/als_model.onnx",
        help="Output path for the exported ONNX model.",
    )
    parser.add_argument(
        "--output-sample",
        default="artifacts/als/als_sample_input.npy",
        help="Output path for a representative sample input tensor.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    model_path = Path(args.model_path).expanduser().resolve()
    output_onnx = Path(args.output_onnx).expanduser().resolve()
    output_sample = Path(args.output_sample).expanduser().resolve()

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Run the bootstrap script first.")

    model = joblib.load(model_path)
    feature_count = len(ALS_FEATURE_NAMES)

    import onnx
    
    # Define the input signature with FIXED shape [1, 8]
    # NPU compilers often fail on dynamic [None, 8] shapes.
    initial_types = [("input", FloatTensorType([1, feature_count]))]
    
    onnx_model = convert_sklearn(
        model,
        initial_types=initial_types,
        target_opset=11, # Baseline for mobile NPU support
    )

    # Validate the model before saving
    onnx.checker.check_model(onnx_model)

    output_onnx.parent.mkdir(parents=True, exist_ok=True)
    output_onnx.write_bytes(onnx_model.SerializeToString())

    # Create a dummy sample input
    sample = np.random.rand(1, feature_count).astype(np.float32)
    np.save(output_sample, sample)

    print(f"Exported ALS ONNX model to {output_onnx}")
    print(f"Saved dummy sample input to {output_sample}")
    print(f"Feature count: {feature_count}")
    print(f"Expected Features: {ALS_FEATURE_NAMES}")


if __name__ == "__main__":
    main()
