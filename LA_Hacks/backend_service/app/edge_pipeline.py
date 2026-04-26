from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from app.spatial import H3_RESOLUTION, geo_to_h3

RED_ZONE_THRESHOLD = 0.66


def derive_context_from_watch_metrics(metrics: dict[str, float]) -> str:
    walking_speed = float(metrics["walking_speed"])
    physical_effort = float(metrics["physical_effort"])
    stair_speed = float(metrics["stair_speed"])
    environmental_sound = float(metrics["environmental_sound_level"])

    if walking_speed < 0.25 and physical_effort < 0.2:
        return "stationary"
    if stair_speed > 0.2:
        return "transit_like"
    if walking_speed >= 0.6:
        return "walking"
    if environmental_sound > 72.0 and physical_effort < 0.35:
        return "transit_like"
    return "stationary"


def build_privacy_packet(
    *,
    user_id: str,
    timestamp: str,
    lat: float,
    lng: float,
    als_score: float,
    metrics: dict[str, float],
) -> dict[str, object]:
    return {
        "user_id": user_id,
        "timestamp": timestamp,
        "h3_index": geo_to_h3(lat, lng, H3_RESOLUTION),
        "als_score": float(als_score),
        "context": derive_context_from_watch_metrics(metrics),
        "noise_db": float(metrics["environmental_sound_level"]),
    }


def aggregate_packets_to_tiles(packets: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for packet in packets:
        grouped[str(packet["h3_index"])].append(packet)

    tiles: list[dict[str, object]] = []
    for h3_index, tile_packets in grouped.items():
        avg_als = sum(float(packet["als_score"]) for packet in tile_packets) / len(tile_packets)
        avg_noise = sum(float(packet.get("noise_db", 0.0)) for packet in tile_packets) / len(tile_packets)
        dominant_context = Counter(
            str(packet["context"]) for packet in tile_packets
        ).most_common(1)[0][0]
        tiles.append(
            {
                "h3_index": h3_index,
                "avg_als": round(avg_als, 4),
                "dominant_context": dominant_context,
                "noise_db": round(avg_noise, 2),
                "status": "red_zone" if avg_als >= RED_ZONE_THRESHOLD else "blue_zone",
                # Compatibility fields for UI
                "als_score": round(avg_als, 4),
                "context": dominant_context,
            }
        )

    tiles.sort(key=lambda tile: (-float(tile["avg_als"]), str(tile["h3_index"])))
    return tiles


def _parse_timestamp(raw_timestamp: object) -> datetime:
    if isinstance(raw_timestamp, datetime):
        return raw_timestamp.astimezone(timezone.utc)
    text = str(raw_timestamp)
    if text.endswith("Z"):
        text = text.replace("Z", "+00:00")
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def build_history_buckets(
    packets: list[dict[str, object]],
    bucket_minutes: int,
    limit: int,
) -> list[dict[str, object]]:
    grouped: dict[datetime, list[dict[str, object]]] = defaultdict(list)
    for packet in packets:
        timestamp = _parse_timestamp(packet["timestamp"])
        bucket_start = timestamp.replace(second=0, microsecond=0)
        bucket_start -= timedelta(
            minutes=bucket_start.minute % bucket_minutes,
        )
        grouped[bucket_start].append(packet)

    buckets = [
        {
            "bucket_start": bucket_start,
            "tile_count": len(aggregate_packets_to_tiles(bucket_packets)),
            "tiles": aggregate_packets_to_tiles(bucket_packets),
        }
        for bucket_start, bucket_packets in sorted(grouped.items())
    ]
    if limit > 0:
        return buckets[-limit:]
    return buckets


def build_hotspot_detail(
    packets: list[dict[str, object]],
    h3_index: str,
) -> dict[str, object] | None:
    matching = [packet for packet in packets if str(packet["h3_index"]) == h3_index]
    if not matching:
        return None

    tile = aggregate_packets_to_tiles(matching)[0]
    latest_timestamp = max(_parse_timestamp(packet["timestamp"]) for packet in matching)
    context_counter = Counter(str(packet["context"]) for packet in matching)
    return {
        **tile,
        "packet_count": len(matching),
        "unique_user_count": len({str(packet["user_id"]) for packet in matching}),
        "latest_timestamp": latest_timestamp,
        "context_counts": {
            "stationary": context_counter.get("stationary", 0),
            "walking": context_counter.get("walking", 0),
            "transit_like": context_counter.get("transit_like", 0),
        },
        "recent_scores": [float(packet["als_score"]) for packet in matching[-10:]],
        # Compatibility fields for UI
        "location_label": f"H3:{h3_index[:12]}",
        "als_score": tile["avg_als"],
        "context": tile["dominant_context"],
        "stressors": ["heat", "noise"] if tile["avg_als"] >= 0.7 else ["urban_stress"],
        "severity": "high" if tile["avg_als"] >= 0.7 else "medium" if tile["avg_als"] >= 0.5 else "low",
    }


def build_agent_hotspots(
    packets: list[dict[str, object]],
    limit: int,
) -> list[dict[str, object]]:
    tiles = aggregate_packets_to_tiles(packets)
    hotspots: list[dict[str, object]] = []
    for tile in tiles[:limit]:
        detail = build_hotspot_detail(packets, str(tile["h3_index"]))
        if detail is None:
            continue
        hotspots.append(detail)

    hotspots.sort(key=lambda item: (-float(item["avg_als"]), -int(item["packet_count"])))
    return hotspots
