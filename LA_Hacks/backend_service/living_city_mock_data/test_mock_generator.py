from __future__ import annotations

import unittest
from statistics import mean

from scripts.generate_mock_events import (
    HOTSPOTS,
    HOTSPOT_RADIUS_M,
    METRIC_KEYS,
    generate,
    haversine_m,
)


SMALL_SEED = 7
SMALL_USERS = 5
SMALL_HOURS = 4
CADENCE_S = 60


class TestMockGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = generate(
            n_users=SMALL_USERS,
            seed=SMALL_SEED,
            start_date="2026-04-21",
            hours=SMALL_HOURS,
            cadence_s=CADENCE_S,
        )

    def test_top_level_shape(self) -> None:
        self.assertIsInstance(self.payload, list)
        self.assertEqual(len(self.payload), SMALL_USERS)
        for user in self.payload:
            self.assertEqual(set(user.keys()), {"user_id", "events"})
            self.assertIsInstance(user["user_id"], str)
            self.assertIsInstance(user["events"], list)
            self.assertEqual(len(user["events"]), SMALL_HOURS * 60)

    def test_event_shape(self) -> None:
        first = self.payload[0]["events"][0]
        self.assertEqual(set(first.keys()), {"timestamp", "location", "metrics"})
        self.assertEqual(set(first["location"].keys()), {"lat", "lng"})
        self.assertEqual(set(first["metrics"].keys()), set(METRIC_KEYS))

    def test_no_extra_metric_fields(self) -> None:
        for user in self.payload:
            for ev in user["events"]:
                self.assertEqual(set(ev["metrics"].keys()), set(METRIC_KEYS))

    def test_timestamps_strictly_increasing(self) -> None:
        for user in self.payload:
            ts = [ev["timestamp"] for ev in user["events"]]
            self.assertEqual(ts, sorted(ts))
            self.assertEqual(len(ts), len(set(ts)))

    def test_running_distance_zero_when_not_running(self) -> None:
        # Across the small sample, gym_bro window may not be present.
        # Sanity: any event with walking_speed < 2.0 m/s should have running_distance unchanged from prior.
        for user in self.payload:
            prev_run = 0.0
            for ev in user["events"]:
                run = ev["metrics"]["running_distance"]
                speed = ev["metrics"]["walking_speed"]
                if speed < 2.0:
                    self.assertAlmostEqual(run, prev_run, places=3)
                prev_run = run

    def test_sleep_value_constant_within_day(self) -> None:
        # Sleep is "last sleep block" hours; should not flip every minute.
        for user in self.payload:
            sleep_values = {ev["metrics"]["sleep"] for ev in user["events"]}
            # Allow at most one transition (wake event in window).
            self.assertLessEqual(len(sleep_values), 2)

    def test_metric_value_types(self) -> None:
        ev = self.payload[0]["events"][0]
        m = ev["metrics"]
        # Counts are int, others numeric
        for k in ("heart_rate", "respiratory_rate", "blood_oxygen",
                  "stairs_up", "stairs_down", "active_energy", "resting_energy"):
            self.assertIsInstance(m[k], int, msg=f"{k} should be int")
        for k in ("wrist_temperature", "environmental_sound_level",
                  "physical_effort", "walking_speed", "step_length",
                  "stair_speed", "stand_minutes", "exercise_time",
                  "walking_distance", "running_distance",
                  "walking_steadiness", "sleep"):
            self.assertIsInstance(m[k], (int, float), msg=f"{k} numeric")

    def test_la_coords(self) -> None:
        for user in self.payload:
            for ev in user["events"]:
                self.assertGreater(ev["location"]["lat"], 33.5)
                self.assertLess(ev["location"]["lat"], 34.5)
                self.assertGreater(ev["location"]["lng"], -119.0)
                self.assertLess(ev["location"]["lng"], -117.5)


class TestHotspotSignal(unittest.TestCase):
    """Larger sample to verify hotspot HR signal."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = generate(
            n_users=40,
            seed=11,
            start_date="2026-04-21",
            hours=24,
            cadence_s=60,
        )

    def test_hotspot_hr_above_background(self) -> None:
        hotspot_hrs: list[int] = []
        background_hrs: list[int] = []
        for user in self.payload:
            for ev in user["events"]:
                lat, lng = ev["location"]["lat"], ev["location"]["lng"]
                in_hotspot = any(
                    haversine_m((lat, lng), (h.lat, h.lng)) < HOTSPOT_RADIUS_M
                    for h in HOTSPOTS
                )
                bucket = hotspot_hrs if in_hotspot else background_hrs
                bucket.append(ev["metrics"]["heart_rate"])

        self.assertGreater(len(hotspot_hrs), 50, msg="too few hotspot events to test")
        diff = mean(hotspot_hrs) - mean(background_hrs)
        self.assertGreater(diff, 5.0, msg=f"hotspot HR not materially above background (diff={diff:.1f})")


if __name__ == "__main__":
    unittest.main()
