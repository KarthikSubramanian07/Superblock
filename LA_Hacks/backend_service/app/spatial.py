from __future__ import annotations

from functools import lru_cache

import h3

H3_RESOLUTION = 9


@lru_cache(maxsize=1)
def _has_modern_api() -> bool:
    return hasattr(h3, "latlng_to_cell")


def geo_to_h3(lat: float, lng: float, resolution: int = H3_RESOLUTION) -> str:
    if _has_modern_api():
        return str(h3.latlng_to_cell(lat, lng, resolution))
    return str(h3.geo_to_h3(lat, lng, resolution))
