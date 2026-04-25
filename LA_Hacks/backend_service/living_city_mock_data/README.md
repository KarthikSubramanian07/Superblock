# Synthetic Apple Watch Events — Living City demo data

`mock_events.json` — 50 users × 1,440 events (1-min cadence over a Tuesday in LA, 2026-04-21 UTC). Matches the backend ingestion schema exactly (19 metric fields, no extras).

## Schema

```json
[
  {
    "user_id": "demo_user_01",
    "events": [
      {
        "timestamp": "2026-04-21T07:32:00Z",
        "location": { "lat": 34.0488, "lng": -118.2518 },
        "metrics": {
          "heart_rate": 102, "wrist_temperature": 0.6,
          "environmental_sound_level": 71.4, "exercise_time": 12,
          "walking_distance": 0.42, "running_distance": 0.0,
          "physical_effort": 0.68, "respiratory_rate": 19,
          "blood_oxygen": 97, "sleep": 6.5,
          "walking_speed": 1.4, "walking_steadiness": 0.82,
          "step_length": 0.67, "stair_speed": 0.0,
          "stairs_up": 0, "stairs_down": 0,
          "stand_minutes": 18, "active_energy": 44, "resting_energy": 12
        }
      }
    ]
  }
]
```

## Hotspots planted (visible red zones)

| Name | Lat | Lng | Intensity |
|------|-----|-----|-----------|
| DTLA 3rd & Hill | 34.0488 | -118.2518 | 1.00 |
| 405 / Wilshire on-ramp | 34.0608 | -118.4444 | 0.95 |
| Westwood Village | 34.0639 | -118.4452 | 0.85 |
| Hollywood / Highland | 34.1014 | -118.3387 | 0.75 |

Stress amplified during 07:00–09:00 and 17:00–19:00 commute peaks. Most users' commute paths are biased to cross ≥1 hotspot.

## Field semantics

- **Cumulative since midnight:** `exercise_time` (min), `walking_distance` / `running_distance` (km), `stand_minutes`, `active_energy` / `resting_energy` (kcal), `stairs_up` / `stairs_down` (count).
- **Instantaneous:** `heart_rate`, `wrist_temperature` (Δ°C from baseline), `environmental_sound_level` (dB), `physical_effort` (0–1), `respiratory_rate`, `blood_oxygen` (%), `walking_speed` (m/s), `walking_steadiness` (0–1), `step_length` (m), `stair_speed` (m/s, 0 unless on stairs).
- **Slow-varying:** `sleep` = hours from last completed sleep block; updates only on wake event.

## Regenerate

```bash
python3 scripts/generate_mock_events.py --users 50 --seed 42 --output data/mock_events.json
```

CLI flags: `--users`, `--seed`, `--start-date`, `--hours`, `--cadence-seconds`, `--output`, `--minify`. Stdlib-only (no install).

## Tests

```bash
python3 -m unittest tests.test_mock_generator -v
```

9 cases: schema conformance, type checks, monotone timestamps, no-extras, hotspot HR signal ≥ 5 bpm above background.

## Sanity

- DTLA tile, peak hours: mean HR ≈ 78 bpm vs overall mean ≈ 72 bpm.
- 50-user file: ~58 MB pretty, ~30 MB minified (`--minify`).
