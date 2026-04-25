from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from training.constants import LABEL_COLUMN
from training.dataset import map_raw_activity
from training.features import as_feature_dict, expected_feature_names
from training.modeling import train_classifier


def make_prepared_frame(rows_per_class: int = 16) -> pd.DataFrame:
    feature_names = expected_feature_names()
    rows = []
    class_bases = {
        "stationary": 0.2,
        "walking": 1.0,
        "running": 2.0,
        "transit_like": 1.5,
    }
    for label, base in class_bases.items():
        for row_index in range(rows_per_class):
            values = [
                base + ((feature_index + row_index) * 0.01)
                for feature_index in range(len(feature_names))
            ]
            row = as_feature_dict(values)
            row["subject_id"] = f"user_{row_index % 4}"
            row["raw_activity"] = label
            row[LABEL_COLUMN] = label
            rows.append(row)
    return pd.DataFrame(rows)


class TrainingTests(unittest.TestCase):
    def test_label_mapping(self) -> None:
        self.assertEqual(map_raw_activity("A"), "walking")
        self.assertEqual(map_raw_activity("B"), "running")
        self.assertEqual(map_raw_activity("C"), "transit_like")
        self.assertEqual(map_raw_activity("D"), "stationary")
        self.assertEqual(map_raw_activity("E"), "stationary")
        self.assertEqual(map_raw_activity("Q"), "stationary")

    def test_train_classifier_saves_artifacts(self) -> None:
        prepared = make_prepared_frame()
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_dir = Path(temp_dir) / "artifacts"
            metrics = train_classifier(prepared, artifacts_dir=artifacts_dir)

            self.assertIn("accuracy", metrics)
            self.assertEqual(metrics["split_strategy"], "subject_wise_group_shuffle_split")
            self.assertGreater(metrics["train_subject_count"], 0)
            self.assertGreater(metrics["test_subject_count"], 0)
            self.assertTrue(
                set(metrics["train_subject_ids"]).isdisjoint(set(metrics["test_subject_ids"]))
            )
            self.assertTrue((artifacts_dir / "model.joblib").exists())
            self.assertTrue((artifacts_dir / "metadata.json").exists())
            self.assertTrue((artifacts_dir / "feature_names.json").exists())
            self.assertTrue((artifacts_dir / "metrics.json").exists())

    def test_feature_order_helper_is_stable(self) -> None:
        names = expected_feature_names()
        self.assertEqual(names[0], "accel_x_mean")
        self.assertEqual(names[-1], "accel_mag_sma")
        self.assertEqual(len(names), 28)


if __name__ == "__main__":
    unittest.main()
