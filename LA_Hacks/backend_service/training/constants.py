from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = BASE_DIR / "data"
DEFAULT_ARTIFACTS_DIR = BASE_DIR / "artifacts"
DEFAULT_DATASET_URL = (
    "https://archive.ics.uci.edu/static/public/507/"
    "wisdm+smartphone+and+smartwatch+activity+and+biometrics+dataset.zip"
)
DEFAULT_DATASET_URLS = (
    DEFAULT_DATASET_URL,
    "https://archive.ics.uci.edu/static/public/507/wisdm-dataset.zip",
    "https://www.cis.fordham.edu/wisdm/includes/datasets/latest/WISDM_ar_latest.tar.gz",
)

RAW_ACTIVITY_CODE_MAP = {
    "A": "walking",
    "B": "jogging",
    "C": "stairs",
    "D": "sitting",
    "E": "standing",
    "F": "typing",
    "G": "brushing_teeth",
    "H": "eating_soup",
    "I": "eating_chips",
    "J": "eating_pasta",
    "K": "drinking_from_cup",
    "L": "eating_sandwich",
    "M": "kicking",
    "O": "playing_catch",
    "P": "dribbling",
    "Q": "writing",
    "R": "clapping",
    "S": "folding_clothes",
}

PROJECT_LABEL_MAP = {
    "walking": "walking",
    "jogging": "running",
    "stairs": "transit_like",
    "upstairs": "transit_like",
    "downstairs": "transit_like",
    "sitting": "stationary",
    "standing": "stationary",
    "typing": "stationary",
    "brushing_teeth": "stationary",
    "eating_soup": "stationary",
    "eating_chips": "stationary",
    "eating_pasta": "stationary",
    "drinking_from_cup": "stationary",
    "eating_sandwich": "stationary",
    "kicking": "stationary",
    "playing_catch": "stationary",
    "dribbling": "stationary",
    "writing": "stationary",
    "clapping": "stationary",
    "folding_clothes": "stationary",
}

LABEL_COLUMN = "context_label"
