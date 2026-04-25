"""Generate synthetic Apple Watch event data for The Living City demo.

Emits a JSON array of `{user_id, events: [{timestamp, location, metrics}]}`
matching the 19-field backend ingestion schema. Behaviorally realistic
(circadian patterns, commute peaks, hotspot stress) and reproducible via
--seed.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

METRIC_KEYS: tuple[str, ...] = (
    "heart_rate",
    "wrist_temperature",
    "environmental_sound_level",
    "exercise_time",
    "walking_distance",
    "running_distance",
    "physical_effort",
    "respiratory_rate",
    "blood_oxygen",
    "sleep",
    "walking_speed",
    "walking_steadiness",
    "step_length",
    "stair_speed",
    "stairs_up",
    "stairs_down",
    "stand_minutes",
    "active_energy",
    "resting_energy",
)

LA_BBOX = (33.95, -118.55, 34.20, -118.20)  # (min_lat, min_lng, max_lat, max_lng)

AM_PEAK = range(7 * 60, 9 * 60 + 1)        # 07:00–09:00
PM_PEAK = range(17 * 60, 19 * 60 + 1)      # 17:00–19:00

HOTSPOT_RADIUS_M = 250.0


@dataclass(frozen=True)
class Hotspot:
    name: str
    lat: float
    lng: float
    intensity: float  # 0.0–1.0 multiplier on stress contribution


HOTSPOTS: tuple[Hotspot, ...] = (
    Hotspot("DTLA_3rd_Hill",      lat=34.0488, lng=-118.2518, intensity=1.00),
    Hotspot("I405_Wilshire",      lat=34.0608, lng=-118.4444, intensity=0.95),
    Hotspot("Westwood_Village",   lat=34.0639, lng=-118.4452, intensity=0.85),
    Hotspot("Hollywood_Highland", lat=34.1014, lng=-118.3387, intensity=0.75),
)


@dataclass(frozen=True)
class UserProfile:
    user_id: str
    archetype: str             # "nine_to_five" | "night_shift" | "gym_bro" | "homebody"
    home: tuple[float, float]
    work: tuple[float, float]
    commute_mode: str          # "walk" | "transit" | "drive"
    baseline_hr: int
    baseline_sleep_hours: float
    wake_minute: int
    bed_minute: int
    work_start_minute: int
    work_end_minute: int
    commute_waypoints_to_work: tuple[tuple[float, float], ...]
    stair_event_minutes: tuple[int, ...]  # minutes of day when stair bursts happen


@dataclass(frozen=True)
class TickState:
    """Per-user accumulators that thread through the day."""
    wrist_temp: float
    cum_active_kcal: float
    cum_resting_kcal: float
    cum_exercise_min: float
    cum_stand_min: float
    cum_walking_km: float
    cum_running_km: float
    cum_stairs_up: int
    cum_stairs_down: int
    last_sleep_hours: float


# ---------------------------------------------------------------------------
# Geo helpers
# ---------------------------------------------------------------------------

def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lng1 = a
    lat2, lng2 = b
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def jitter(point: tuple[float, float], rng: random.Random, deg: float = 0.0003) -> tuple[float, float]:
    return (point[0] + rng.uniform(-deg, deg), point[1] + rng.uniform(-deg, deg))


def lerp_point(a: tuple[float, float], b: tuple[float, float], t: float) -> tuple[float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def random_la_point(rng: random.Random) -> tuple[float, float]:
    return (rng.uniform(LA_BBOX[0], LA_BBOX[2]), rng.uniform(LA_BBOX[1], LA_BBOX[3]))


def hotspot_stress(lat: float, lng: float, minute_of_day: int) -> float:
    """0.0–1.0 stress modifier from hotspot proximity, amplified at peak hours."""
    peak = 1.0 if (minute_of_day in AM_PEAK or minute_of_day in PM_PEAK) else 0.4
    best = 0.0
    for h in HOTSPOTS:
        d = haversine_m((lat, lng), (h.lat, h.lng))
        if d > HOTSPOT_RADIUS_M:
            continue
        proximity = 1.0 - (d / HOTSPOT_RADIUS_M)
        contribution = proximity * h.intensity * peak
        if contribution > best:
            best = contribution
    return best


# ---------------------------------------------------------------------------
# Profile + schedule builders
# ---------------------------------------------------------------------------

ARCHETYPE_WEIGHTS = (
    ("nine_to_five", 0.70),
    ("night_shift", 0.10),
    ("gym_bro", 0.10),
    ("homebody", 0.10),
)


def pick_archetype(rng: random.Random) -> str:
    r = rng.random()
    cum = 0.0
    for name, w in ARCHETYPE_WEIGHTS:
        cum += w
        if r <= cum:
            return name
    return ARCHETYPE_WEIGHTS[-1][0]


def near_hotspot(rng: random.Random, jitter_m: float = 600.0) -> tuple[float, float]:
    h = rng.choice(HOTSPOTS)
    deg = jitter_m / 111_000.0
    return (h.lat + rng.uniform(-deg, deg), h.lng + rng.uniform(-deg, deg))


def build_commute_path(
    home: tuple[float, float],
    work: tuple[float, float],
    rng: random.Random,
) -> tuple[tuple[float, float], ...]:
    """Build 1–2 waypoints, biased to pass near a hotspot if one lies within the corridor."""
    candidates = []
    for h in HOTSPOTS:
        midpoint = lerp_point(home, work, 0.5)
        dist_to_corridor = haversine_m((h.lat, h.lng), midpoint)
        if dist_to_corridor < 4_000:
            candidates.append(h)
    if candidates and rng.random() < 0.8:
        h = rng.choice(candidates)
        return ((h.lat + rng.uniform(-0.001, 0.001), h.lng + rng.uniform(-0.001, 0.001)),)
    return ()


def build_user_profile(idx: int, rng: random.Random) -> UserProfile:
    archetype = pick_archetype(rng)
    work_near_hot = rng.random() < 0.6

    home = random_la_point(rng)
    work = near_hotspot(rng) if work_near_hot else random_la_point(rng)

    if archetype == "nine_to_five":
        wake = 7 * 60 + rng.randint(-30, 30)
        work_start = 9 * 60 + rng.randint(-30, 30)
        work_end = 17 * 60 + rng.randint(-30, 60)
        bed = 23 * 60 + rng.randint(-30, 30)
    elif archetype == "night_shift":
        wake = 16 * 60 + rng.randint(-30, 30)
        work_start = 18 * 60
        work_end = (2 * 60) % (24 * 60)  # 02:00 next day — handled as past midnight
        bed = 8 * 60
    elif archetype == "gym_bro":
        wake = 6 * 60
        work_start = 9 * 60
        work_end = 17 * 60
        bed = 22 * 60
    else:  # homebody
        wake = 8 * 60 + rng.randint(-60, 60)
        work_start = wake + 30
        work_end = 17 * 60
        bed = 23 * 60 + rng.randint(-60, 60)
        work = home  # works from home

    commute_mode = rng.choices(
        population=("walk", "transit", "drive"),
        weights=(0.2, 0.4, 0.4),
        k=1,
    )[0]

    waypoints = build_commute_path(home, work, rng) if archetype != "homebody" else ()

    n_stair_events = rng.randint(0, 2) if commute_mode == "transit" else 0
    stair_minutes = tuple(sorted(rng.sample(range(work_start - 30, work_start + 5), n_stair_events))) if n_stair_events else ()

    return UserProfile(
        user_id=f"demo_user_{idx:02d}",
        archetype=archetype,
        home=home,
        work=work,
        commute_mode=commute_mode,
        baseline_hr=rng.randint(55, 70),
        baseline_sleep_hours=round(rng.uniform(6.0, 8.5), 1),
        wake_minute=wake,
        bed_minute=bed,
        work_start_minute=work_start,
        work_end_minute=work_end,
        commute_waypoints_to_work=waypoints,
        stair_event_minutes=stair_minutes,
    )


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

def state_for_minute(profile: UserProfile, minute: int) -> str:
    """Return one of: sleep, sedentary, walking, commuting, running, lunch."""
    if profile.archetype == "gym_bro" and 6 * 60 <= minute < 6 * 60 + 30:
        return "running"

    if profile.archetype == "homebody":
        if minute < profile.wake_minute or minute >= profile.bed_minute:
            return "sleep"
        if (12 * 60) <= minute < (12 * 60 + 30) and minute % 47 < 15:
            return "walking"
        return "sedentary"

    if profile.archetype == "night_shift":
        # Sleep block 08:00–16:00. Work 18:00–02:00.
        if (8 * 60) <= minute < (16 * 60):
            return "sleep"
        if (16 * 60) <= minute < profile.work_start_minute:
            return "sedentary"
        if profile.work_start_minute <= minute or minute < (2 * 60):
            return "sedentary"
        return "sedentary"

    # nine_to_five / gym_bro standard
    if minute < profile.wake_minute or minute >= profile.bed_minute:
        return "sleep"
    if minute < profile.wake_minute + 30:
        return "sedentary"
    commute_to_work_end = profile.work_start_minute
    commute_to_work_start = max(profile.wake_minute + 30, commute_to_work_end - 60)
    if commute_to_work_start <= minute < commute_to_work_end:
        return "commuting"
    if (12 * 60) <= minute < (13 * 60):
        return "lunch"
    if profile.work_start_minute <= minute < profile.work_end_minute:
        return "sedentary"
    commute_home_end = profile.work_end_minute + 60
    if profile.work_end_minute <= minute < commute_home_end:
        return "commuting"
    return "sedentary"


def location_for_minute(
    profile: UserProfile, minute: int, state: str, rng: random.Random
) -> tuple[float, float]:
    if state == "sleep":
        return jitter(profile.home, rng)
    if state == "sedentary":
        # Either home or work depending on time
        anchor = profile.work if profile.work_start_minute <= minute < profile.work_end_minute else profile.home
        return jitter(anchor, rng, deg=0.0002)
    if state == "lunch":
        return jitter(profile.work, rng, deg=0.0008)
    if state == "running":
        # short run loop near home
        loop = (math.sin(minute / 5.0) * 0.002, math.cos(minute / 5.0) * 0.002)
        return (profile.home[0] + loop[0], profile.home[1] + loop[1])
    if state == "commuting":
        going_to_work = minute < (12 * 60)
        commute_start = max(profile.wake_minute + 30, profile.work_start_minute - 60) if going_to_work else profile.work_end_minute
        commute_end = profile.work_start_minute if going_to_work else profile.work_end_minute + 60
        span = max(commute_end - commute_start, 1)
        t = max(0.0, min(1.0, (minute - commute_start) / span))
        path: list[tuple[float, float]] = [profile.home, *profile.commute_waypoints_to_work, profile.work]
        if not going_to_work:
            path = list(reversed(path))
        # interpolate along multi-segment path
        seg_count = len(path) - 1
        segf = t * seg_count
        seg_idx = min(int(segf), seg_count - 1)
        seg_t = segf - seg_idx
        loc = lerp_point(path[seg_idx], path[seg_idx + 1], seg_t)
        return jitter(loc, rng, deg=0.0002)
    # default
    return jitter(profile.home, rng)


# ---------------------------------------------------------------------------
# Metric synthesis
# ---------------------------------------------------------------------------

STATE_BASE_HR_DELTA = {
    "sleep": -8,
    "sedentary": 5,
    "walking": 25,
    "lunch": 18,
    "commuting": 18,
    "running": 70,
}

STATE_SOUND_BASE = {
    "sleep": 30.0,
    "sedentary": 50.0,
    "walking": 60.0,
    "lunch": 58.0,
    "commuting": 65.0,
    "running": 62.0,
}

STATE_EFFORT_BASE = {
    "sleep": 0.05,
    "sedentary": 0.15,
    "walking": 0.45,
    "lunch": 0.40,
    "commuting": 0.35,
    "running": 0.85,
}

STATE_RESP_DELTA = {
    "sleep": -2,
    "sedentary": 0,
    "walking": 4,
    "lunch": 3,
    "commuting": 3,
    "running": 12,
}

STATE_WALK_SPEED = {
    "sleep": 0.0,
    "sedentary": 0.0,
    "walking": 1.30,
    "lunch": 1.20,
    "commuting": 1.10,
    "running": 3.50,
}


def _round(x: float, n: int = 2) -> float:
    return round(x, n)


def synth_tick(
    profile: UserProfile,
    minute: int,
    state: str,
    location: tuple[float, float],
    cadence_s: int,
    prev: TickState,
    rng: random.Random,
) -> tuple[dict, TickState]:
    stress = hotspot_stress(location[0], location[1], minute)

    # Heart rate
    hr = profile.baseline_hr + STATE_BASE_HR_DELTA[state] + stress * 30 + rng.gauss(0, 3)
    hr = max(40, min(180, hr))

    # Wrist temp random walk (only awake)
    drift = rng.uniform(-0.02, 0.02) if state != "sleep" else rng.uniform(-0.005, 0.005)
    new_wrist = max(-1.5, min(2.0, prev.wrist_temp + drift + stress * 0.04 * 0.05))

    # Sound
    sound = STATE_SOUND_BASE[state] + stress * 20 + rng.gauss(0, 3)
    sound = max(25.0, min(95.0, sound))

    # Effort
    effort = max(0.0, min(1.0, STATE_EFFORT_BASE[state] + stress * 0.3 + rng.gauss(0, 0.04)))

    # Respiratory rate
    resp = 12 + STATE_RESP_DELTA[state] + stress * 4 + rng.gauss(0, 1)
    resp = max(10, min(28, resp))

    # Blood oxygen
    spo2 = 99 - (1 if state == "sleep" else 0) + rng.gauss(0, 0.6)
    spo2 = max(94, min(100, spo2))

    # Walking metrics
    walk_speed = STATE_WALK_SPEED[state] + (0.2 if state == "commuting" and profile.commute_mode == "walk" else 0.0)
    walk_speed = max(0.0, walk_speed + rng.gauss(0, 0.08))
    step_len = 0.0 if walk_speed == 0 else max(0.2, 0.4 + walk_speed * 0.15 + rng.gauss(0, 0.02))
    steadiness = max(0.4, min(1.0, 0.85 - stress * 0.15 + rng.gauss(0, 0.03)))

    # Stair burst
    on_stairs = minute in profile.stair_event_minutes
    stair_speed = max(0.0, rng.gauss(0.55, 0.08)) if on_stairs else 0.0
    new_stairs_up = prev.cum_stairs_up + (rng.randint(8, 18) if on_stairs else 0)
    new_stairs_down = prev.cum_stairs_down + (rng.randint(0, 4) if on_stairs else 0)

    # Cumulative deltas
    minute_fraction = cadence_s / 60.0
    is_walking = state in {"walking", "lunch", "commuting"} and walk_speed > 0
    is_running = state == "running"

    walk_delta_km = (walk_speed * cadence_s / 1000.0) if is_walking else 0.0
    run_delta_km = (walk_speed * cadence_s / 1000.0) if is_running else 0.0

    new_walking_km = prev.cum_walking_km + walk_delta_km
    new_running_km = prev.cum_running_km + run_delta_km
    new_exercise_min = prev.cum_exercise_min + (minute_fraction if (is_walking or is_running) else 0.0)
    new_stand_min = prev.cum_stand_min + (minute_fraction if state in {"sedentary", "walking", "lunch", "commuting"} else 0.0)

    # Energy: roughly 1 kcal/min resting baseline + scaled active
    active_kcal_per_min = STATE_EFFORT_BASE[state] * 8.0
    new_active = prev.cum_active_kcal + active_kcal_per_min * minute_fraction
    new_resting = prev.cum_resting_kcal + 1.0 * minute_fraction

    # Sleep — refresh on wake transition
    new_sleep_hours = prev.last_sleep_hours
    if state != "sleep" and minute == profile.wake_minute:
        new_sleep_hours = round(profile.baseline_sleep_hours + rng.gauss(0, 0.3), 2)

    metrics = {
        "heart_rate": int(round(hr)),
        "wrist_temperature": _round(new_wrist, 3),
        "environmental_sound_level": _round(sound, 1),
        "exercise_time": _round(new_exercise_min, 1),
        "walking_distance": _round(new_walking_km, 3),
        "running_distance": _round(new_running_km, 3),
        "physical_effort": _round(effort, 3),
        "respiratory_rate": int(round(resp)),
        "blood_oxygen": int(round(spo2)),
        "sleep": _round(new_sleep_hours, 2),
        "walking_speed": _round(walk_speed, 2),
        "walking_steadiness": _round(steadiness, 3),
        "step_length": _round(step_len, 2),
        "stair_speed": _round(stair_speed, 2),
        "stairs_up": new_stairs_up,
        "stairs_down": new_stairs_down,
        "stand_minutes": _round(new_stand_min, 1),
        "active_energy": int(round(new_active)),
        "resting_energy": int(round(new_resting)),
    }

    next_state = TickState(
        wrist_temp=new_wrist,
        cum_active_kcal=new_active,
        cum_resting_kcal=new_resting,
        cum_exercise_min=new_exercise_min,
        cum_stand_min=new_stand_min,
        cum_walking_km=new_walking_km,
        cum_running_km=new_running_km,
        cum_stairs_up=new_stairs_up,
        cum_stairs_down=new_stairs_down,
        last_sleep_hours=new_sleep_hours,
    )
    return metrics, next_state


# ---------------------------------------------------------------------------
# Per-user event emission
# ---------------------------------------------------------------------------

def emit_user_events(
    profile: UserProfile,
    start_dt: datetime,
    hours: int,
    cadence_s: int,
    rng: random.Random,
) -> list[dict]:
    initial = TickState(
        wrist_temp=rng.uniform(-0.2, 0.2),
        cum_active_kcal=0.0,
        cum_resting_kcal=0.0,
        cum_exercise_min=0.0,
        cum_stand_min=0.0,
        cum_walking_km=0.0,
        cum_running_km=0.0,
        cum_stairs_up=0,
        cum_stairs_down=0,
        last_sleep_hours=profile.baseline_sleep_hours,
    )

    total_ticks = (hours * 3600) // cadence_s
    state = initial
    events: list[dict] = []

    for tick in range(total_ticks):
        ts = start_dt + timedelta(seconds=tick * cadence_s)
        minute_of_day = (ts.hour * 60 + ts.minute) % (24 * 60)
        s = state_for_minute(profile, minute_of_day)
        loc = location_for_minute(profile, minute_of_day, s, rng)
        metrics, state = synth_tick(profile, minute_of_day, s, loc, cadence_s, state, rng)
        events.append({
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "location": {"lat": _round(loc[0], 6), "lng": _round(loc[1], 6)},
            "metrics": metrics,
        })

    return events


# ---------------------------------------------------------------------------
# Top-level
# ---------------------------------------------------------------------------

def generate(
    n_users: int,
    seed: int,
    start_date: str,
    hours: int,
    cadence_s: int,
) -> list[dict]:
    rng = random.Random(seed)
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    profiles = [build_user_profile(i + 1, rng) for i in range(n_users)]
    payload: list[dict] = []
    for profile in profiles:
        user_rng = random.Random(rng.randint(0, 2**31 - 1))
        events = emit_user_events(profile, start_dt, hours, cadence_s, user_rng)
        payload.append({"user_id": profile.user_id, "events": events})
    return payload


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--users", type=int, default=50)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--start-date", default="2026-04-21")
    p.add_argument("--hours", type=int, default=24)
    p.add_argument("--cadence-seconds", type=int, default=60)
    p.add_argument("--output", default="data/mock_events.json")
    p.add_argument("--minify", action="store_true", help="Write compact JSON (smaller file)")
    return p.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> Path:
    args = parse_args(argv)
    payload = generate(
        n_users=args.users,
        seed=args.seed,
        start_date=args.start_date,
        hours=args.hours,
        cadence_s=args.cadence_seconds,
    )
    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        if args.minify:
            json.dump(payload, f, separators=(",", ":"))
        else:
            json.dump(payload, f, indent=2)
    n_events = sum(len(u["events"]) for u in payload)
    print(json.dumps({
        "output": str(out_path),
        "users": len(payload),
        "events": n_events,
        "size_bytes": out_path.stat().st_size,
    }, indent=2))
    return out_path


if __name__ == "__main__":
    main()
