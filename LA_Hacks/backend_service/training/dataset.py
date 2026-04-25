from __future__ import annotations

import csv
import shutil
import tarfile
import zipfile
from pathlib import Path

import pandas as pd
import requests

from training.constants import (
    DEFAULT_DATASET_URL,
    DEFAULT_DATASET_URLS,
    LABEL_COLUMN,
    PROJECT_LABEL_MAP,
    RAW_ACTIVITY_CODE_MAP,
)


def map_raw_activity(raw_value: str) -> str | None:
    cleaned = raw_value.strip().lower()
    if not cleaned:
        return None

    if len(cleaned) == 1 and cleaned.upper() in RAW_ACTIVITY_CODE_MAP:
        cleaned = RAW_ACTIVITY_CODE_MAP[cleaned.upper()]

    aliases = {
        "jogging": "jogging",
        "walking": "walking",
        "stairs": "stairs",
        "upstairs": "upstairs",
        "downstairs": "downstairs",
        "sitting": "sitting",
        "standing": "standing",
        "typing": "typing",
        "brushingteeth": "brushing_teeth",
        "brushing_teeth": "brushing_teeth",
        "eatingsoup": "eating_soup",
        "eating_soup": "eating_soup",
        "eatingchips": "eating_chips",
        "eating_chips": "eating_chips",
        "eatingpasta": "eating_pasta",
        "eating_pasta": "eating_pasta",
        "drinkingfromcup": "drinking_from_cup",
        "drinking_from_cup": "drinking_from_cup",
        "eatingsandwich": "eating_sandwich",
        "eating_sandwich": "eating_sandwich",
        "kicking": "kicking",
        "playingcatch": "playing_catch",
        "playing_catch": "playing_catch",
        "dribbling": "dribbling",
        "writing": "writing",
        "clapping": "clapping",
        "foldingclothes": "folding_clothes",
        "folding_clothes": "folding_clothes",
    }
    canonical = aliases.get(cleaned, cleaned)
    return PROJECT_LABEL_MAP.get(canonical)


def ensure_wisdm_download(
    target_dir: Path,
    dataset_url: str = DEFAULT_DATASET_URL,
) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    extract_dir = target_dir / "wisdm_extracted"

    if extract_dir.exists():
        return extract_dir

    attempted_urls = []
    candidate_urls = [dataset_url, *[url for url in DEFAULT_DATASET_URLS if url != dataset_url]]

    for candidate_url in candidate_urls:
        attempted_urls.append(candidate_url)
        suffix = ".tar.gz" if candidate_url.endswith(".tar.gz") else ".zip"
        archive_path = target_dir / f"wisdm_dataset{suffix}"

        try:
            response = requests.get(candidate_url, stream=True, timeout=60)
            response.raise_for_status()
            with archive_path.open("wb") as handle:
                shutil.copyfileobj(response.raw, handle)

            if suffix == ".zip":
                with zipfile.ZipFile(archive_path, "r") as archive:
                    archive.extractall(extract_dir)
            else:
                with tarfile.open(archive_path, "r:gz") as archive:
                    archive.extractall(extract_dir)

            return extract_dir
        except (requests.RequestException, zipfile.BadZipFile, tarfile.TarError):
            if archive_path.exists():
                archive_path.unlink()

    raise RuntimeError(
        "Unable to download the WISDM dataset from the configured official sources. "
        "Tried: "
        + ", ".join(attempted_urls)
        + ". Download it manually and rerun with --raw-dir."
    )


def find_watch_accel_files(root_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    for path in root_dir.rglob("*"):
        if not path.is_file():
            continue
        lower = path.as_posix().lower()
        if "watch" in lower and "accel" in lower and path.suffix.lower() in {".txt", ".csv"}:
            candidates.append(path)
        elif lower.endswith("wisdm_ar_v1.1_raw.txt"):
            candidates.append(path)
    if not candidates:
        raise FileNotFoundError(
            f"Could not find smartwatch accelerometer files or legacy WISDM raw files under {root_dir}"
        )
    return sorted(candidates)


def _parse_raw_line(row: list[str]) -> dict[str, str | float | int] | None:
    if len(row) < 6:
        return None

    subject_id = row[0].strip()
    raw_activity = row[1].strip()
    timestamp = row[2].strip()
    x_value = row[3].strip()
    y_value = row[4].strip()
    z_value = row[5].strip().rstrip(";")

    label = map_raw_activity(raw_activity)
    if label is None:
        return None

    return {
        "subject_id": str(subject_id),
        "raw_activity": raw_activity,
        "timestamp": int(float(timestamp)),
        "x": float(x_value),
        "y": float(y_value),
        "z": float(z_value),
        LABEL_COLUMN: label,
    }


def _iter_wisdm_records(file_path: Path) -> list[list[str]]:
    if file_path.name.lower() == "wisdm_ar_v1.1_raw.txt":
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        records = []
        for chunk in content.split(";"):
            cleaned = chunk.strip()
            if not cleaned:
                continue
            records.append([part.strip() for part in cleaned.split(",") if part.strip()])
        return records

    records = []
    with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
        reader = csv.reader(handle)
        for row in reader:
            records.append(row)
    return records


def load_watch_accel_samples(root_dir: Path) -> pd.DataFrame:
    records: list[dict[str, str | float | int]] = []
    for file_path in find_watch_accel_files(root_dir):
        for row in _iter_wisdm_records(file_path):
            parsed = _parse_raw_line(row)
            if parsed is not None:
                records.append(parsed)

    frame = pd.DataFrame(records)
    if frame.empty:
        raise ValueError(
            f"No usable smartwatch accelerometer samples were parsed from {root_dir}"
        )
    return frame
