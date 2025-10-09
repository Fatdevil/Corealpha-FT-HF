"""Wind provider using Open-Meteo with caching and derived components."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from hashlib import sha1
from typing import Dict, Optional

import httpx

from . import cache
from .errors import ProviderDataError, ProviderServiceError

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TTL_SECONDS = 15 * 60


def _build_key(lat: float, lon: float, hour: datetime) -> str:
    return f"wind:{lat:.6f}:{lon:.6f}:{hour.isoformat()}"


def _etag_for(payload: Dict[str, object]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha1(body.encode("utf-8"), usedforsecurity=False).hexdigest()


def _normalise_time(moment: Optional[datetime]) -> datetime:
    if moment is None:
        moment = datetime.now(timezone.utc)
    elif moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    else:
        moment = moment.astimezone(timezone.utc)
    return moment.replace(minute=0, second=0, microsecond=0)


async def get_wind(
    lat: float,
    lon: float,
    *,
    when: Optional[datetime] = None,
    bearing: Optional[float] = None,
) -> Dict[str, object]:
    """Return wind speed/direction and optional bearing components."""

    target_time = _normalise_time(when)
    key = _build_key(lat, lon, target_time)
    cached = cache.get(key)
    if cached:
        return _build_response(cached, bearing)

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "wind_speed_10m,wind_direction_10m",
        "windspeed_unit": "ms",
        "timezone": "UTC",
        "past_days": 1,
        "forecast_days": 1,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(FORECAST_URL, params=params)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ProviderServiceError("Wind provider request failed") from exc

    data = response.json()
    base_payload = _parse_wind_payload(data, target_time)
    cache.set(key, base_payload, TTL_SECONDS)
    return _build_response(base_payload, bearing)


def _parse_wind_payload(data: Dict[str, object], target_time: datetime) -> Dict[str, float]:
    if not isinstance(data, dict):
        raise ProviderDataError("Unexpected wind payload structure")

    hourly = data.get("hourly")
    if not isinstance(hourly, dict):
        raise ProviderDataError("Wind payload missing hourly data")

    times = hourly.get("time")
    speeds = hourly.get("wind_speed_10m")
    directions = hourly.get("wind_direction_10m")
    if not (isinstance(times, list) and isinstance(speeds, list) and isinstance(directions, list)):
        raise ProviderDataError("Wind payload missing expected arrays")

    index = _closest_index(times, target_time)
    if index is None:
        raise ProviderDataError("Wind payload missing timestamp close to request")

    try:
        speed = float(speeds[index])
        direction = float(directions[index])
    except (TypeError, ValueError, IndexError) as exc:
        raise ProviderDataError("Invalid wind data values") from exc

    return {"speed_mps": speed, "dir_from_deg": direction}


def _closest_index(times: list, target_time: datetime) -> Optional[int]:
    best_idx: Optional[int] = None
    best_delta: Optional[float] = None
    for idx, raw_time in enumerate(times):
        if not isinstance(raw_time, str):
            continue
        try:
            if raw_time.endswith("Z"):
                sample = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
            else:
                sample = datetime.fromisoformat(raw_time)
            if sample.tzinfo is None:
                sample = sample.replace(tzinfo=timezone.utc)
            else:
                sample = sample.astimezone(timezone.utc)
        except ValueError:
            continue
        delta = abs((sample - target_time).total_seconds())
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best_idx = idx
    return best_idx


def _build_response(payload: Dict[str, float], bearing: Optional[float]) -> Dict[str, object]:
    content: Dict[str, object] = {
        "speed_mps": float(payload["speed_mps"]),
        "dir_from_deg": float(payload["dir_from_deg"]),
        "ttl_s": TTL_SECONDS,
    }

    if bearing is not None:
        content.update(_bearing_components(content["speed_mps"], content["dir_from_deg"], bearing))

    return {**content, "etag": _etag_for({k: v for k, v in content.items()})}


def _bearing_components(speed: float, direction_from: float, bearing: float) -> Dict[str, float]:
    bearing_norm = float(bearing) % 360.0
    wind_from = float(direction_from) % 360.0
    delta = math.radians((wind_from - bearing_norm) % 360.0)
    if delta > math.pi:
        delta -= 2 * math.pi
    w_parallel = -speed * math.cos(delta)
    w_perp = speed * math.sin(delta)
    return {"w_parallel": w_parallel, "w_perp": w_perp}
