from __future__ import annotations

import asyncio
import importlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def provider_modules(monkeypatch, tmp_path) -> Tuple[object, object, object, object]:
    monkeypatch.setenv("PROVIDERS_CACHE_DIR", str(tmp_path))

    import server.providers.cache as cache_module
    import server.providers.elevation as elevation_module
    import server.providers.wind as wind_module
    import server.routes.providers as routes_module

    for module in (cache_module, elevation_module, wind_module):
        importlib.reload(module)
    importlib.reload(routes_module)

    return cache_module, elevation_module, wind_module, routes_module


def test_elevation_cached_across_memory_and_disk(monkeypatch, provider_modules):
    cache_module, elevation_module, _, _ = provider_modules

    class DummyAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params=None):
            DummyAsyncClient.calls += 1
            data = {"results": [{"elevation": 123.4}]}
            request = httpx.Request("GET", url, params=params)
            return httpx.Response(200, json=data, request=request)

    DummyAsyncClient.calls = 0
    monkeypatch.setattr(elevation_module.httpx, "AsyncClient", DummyAsyncClient)

    cache_module.clear_memory()
    payload = asyncio.run(elevation_module.get_elevation(59.33, 18.06))
    assert payload["elevation_m"] == pytest.approx(123.4)
    assert payload["ttl_s"] == 604800
    assert payload["etag"]

    second = asyncio.run(elevation_module.get_elevation(59.33, 18.06))
    assert second == payload
    assert DummyAsyncClient.calls == 1

    cache_module.clear_memory()
    third = asyncio.run(elevation_module.get_elevation(59.33, 18.06))
    assert third == payload
    assert DummyAsyncClient.calls == 1  # served from disk cache


def test_wind_components_and_etag(monkeypatch, provider_modules):
    cache_module, _, wind_module, _ = provider_modules

    class DummyAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, params=None):
            DummyAsyncClient.calls += 1
            data = {
                "hourly": {
                    "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
                    "wind_speed_10m": [5.0, 7.0],
                    "wind_direction_10m": [45.0, 90.0],
                }
            }
            request = httpx.Request("GET", url, params=params)
            return httpx.Response(200, json=data, request=request)

    DummyAsyncClient.calls = 0
    monkeypatch.setattr(wind_module.httpx, "AsyncClient", DummyAsyncClient)

    when = datetime(2024, 1, 1, 1, 30, tzinfo=timezone.utc)
    cache_module.clear_memory()
    payload = asyncio.run(wind_module.get_wind(1.0, 2.0, when=when, bearing=90))

    assert payload["speed_mps"] == pytest.approx(7.0)
    assert payload["dir_from_deg"] == pytest.approx(90.0)
    assert payload["w_parallel"] == pytest.approx(-7.0, rel=1e-6)
    assert payload["w_perp"] == pytest.approx(0.0, abs=1e-6)
    assert payload["ttl_s"] == 900

    payload_tailwind = asyncio.run(wind_module.get_wind(1.0, 2.0, when=when, bearing=270))
    assert DummyAsyncClient.calls == 1
    assert payload_tailwind["w_parallel"] == pytest.approx(7.0, rel=1e-6)
    assert payload_tailwind["etag"] != payload["etag"]


def test_routes_emit_etag_and_304(monkeypatch, provider_modules):
    _, _, _, routes_module = provider_modules

    async def fake_elevation(lat, lon):
        return {"elevation_m": 12.0, "ttl_s": 604800, "etag": "abc"}

    async def fake_wind(lat, lon, bearing=None):
        body = {"speed_mps": 3.0, "dir_from_deg": 270.0, "ttl_s": 900}
        if bearing is not None:
            body["w_parallel"] = 1.0
            body["w_perp"] = 0.0
        body["etag"] = "wind"
        return body

    monkeypatch.setattr(routes_module, "get_elevation", fake_elevation)
    monkeypatch.setattr(routes_module, "get_wind", fake_wind)

    app = FastAPI()
    app.include_router(routes_module.router)
    client = TestClient(app)

    resp = client.get("/providers/elevation", params={"lat": 1, "lon": 2})
    assert resp.status_code == 200
    assert resp.headers["ETag"] == "abc"
    assert resp.headers["Cache-Control"] == "public, max-age=604800"

    resp_304 = client.get(
        "/providers/elevation",
        params={"lat": 1, "lon": 2},
        headers={"If-None-Match": "abc"},
    )
    assert resp_304.status_code == 304
    assert resp_304.content == b""
    assert resp_304.headers["ETag"] == "abc"

    wind_resp = client.get(
        "/providers/wind",
        params={"lat": 1, "lon": 2, "bearing": 180},
    )
    assert wind_resp.status_code == 200
    assert wind_resp.headers["ETag"] == "wind"
    assert wind_resp.headers["Cache-Control"] == "public, max-age=900"
