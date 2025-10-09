"""Elevation provider using Open-Meteo with caching and ETag support."""

from __future__ import annotations

import json
from hashlib import sha1
from typing import Dict

import httpx

from . import cache
from .errors import ProviderDataError, ProviderServiceError

ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"
TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days


def _build_key(lat: float, lon: float) -> str:
    return f"elevation:{lat:.6f}:{lon:.6f}"


def _etag_for(payload: Dict[str, object]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha1(body.encode("utf-8"), usedforsecurity=False).hexdigest()


async def get_elevation(lat: float, lon: float) -> Dict[str, object]:
    """Return elevation in meters for the provided coordinates."""

    key = _build_key(lat, lon)
    cached = cache.get(key)
    if cached:
        content = {"elevation_m": float(cached["elevation_m"]), "ttl_s": TTL_SECONDS}
        return {**content, "etag": _etag_for(content)}

    params = {"latitude": lat, "longitude": lon}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(ELEVATION_URL, params=params)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ProviderServiceError("Elevation provider request failed") from exc

    data = response.json()
    elevation_value = _parse_elevation(data)
    payload = {"elevation_m": elevation_value}
    cache.set(key, payload, TTL_SECONDS)
    content = {"elevation_m": elevation_value, "ttl_s": TTL_SECONDS}
    return {**content, "etag": _etag_for(content)}


def _parse_elevation(data: Dict[str, object]) -> float:
    elevation_value = None

    if isinstance(data, dict):
        results = data.get("results")
        if isinstance(results, list) and results:
            first = results[0]
            if isinstance(first, dict) and "elevation" in first:
                try:
                    elevation_value = float(first["elevation"])
                except (TypeError, ValueError):
                    pass
        if elevation_value is None and "elevation" in data:
            elevation_field = data["elevation"]
            if isinstance(elevation_field, (list, tuple)) and elevation_field:
                try:
                    elevation_value = float(elevation_field[0])
                except (TypeError, ValueError):
                    pass
            elif isinstance(elevation_field, (int, float)):
                elevation_value = float(elevation_field)

    if elevation_value is None:
        raise ProviderDataError("Elevation field missing in provider response")

    return float(elevation_value)
