from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export the trained context classifier to ONNX for ZETIC Melange.",
    )
    parser.add_argument(
        "--model-path",
        default="artifacts/model.joblib",
        help="Path to the trained sklearn classifier artifact.",
    )
    parser.add_argument(
        "--feature-names-path",
        default="artifacts/feature_names.json",
        help="Path to the JSON file containing ordered feature names.",
    )
    parser.add_argument(
        "--sample-csv",
        default="data/context_features.csv",
        help="Prepared feature CSV used to extract a realistic sample input row.",
    )
    parser.add_argument(
        "--output-onnx",
        default="artifacts/context_classifier.onnx",
        help="Output path for the exported ONNX model.",
    )
    parser.add_argument(
        "--output-sample",
        default="artifacts/context_classifier_sample_input.npy",
        help="Output path for a representative sample input tensor.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    model_path = Path(args.model_path).expanduser().resolve()
    feature_names_path = Path(args.feature_names_path).expanduser().resolve()
    sample_csv = Path(args.sample_csv).expanduser().resolve()
    output_onnx = Path(args.output_onnx).expanduser().resolve()
    output_sample = Path(args.output_sample).expanduser().resolve()

    model = joblib.load(model_path)
    feature_names = json.loads(feature_names_path.read_text())
    frame = pd.read_csv(sample_csv)
    if frame.empty:
        raise ValueError(f"Sample CSV is empty: {sample_csv}")

    sample = frame.iloc[[0]][feature_names].astype(np.float32)
    initial_types = [("float_input", FloatTensorType([1, len(feature_names)]))]
    onnx_model = convert_sklearn(
        model,
        initial_types=initial_types,
        target_opset=17,
    )

    # Apply ONNX Simplification for NPU optimization
    from onnxsim import simplify
    onnx_model, check = simplify(onnx_model)
    if not check:
        print("[WARNING] ONNX Simplification check failed")

    output_onnx.parent.mkdir(parents=True, exist_ok=True)
    output_onnx.write_bytes(onnx_model.SerializeToString())
    np.save(output_sample, sample.to_numpy(dtype=np.float32))

    print(f"Exported ONNX model to {output_onnx}")
    print(f"Saved sample input to {output_sample}")
    print(f"Feature count: {len(feature_names)}")


if __name__ == "__main__":
    main()
