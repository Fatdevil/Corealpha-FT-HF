"""Provider proxy endpoints with HTTP caching semantics."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse

from server.providers.elevation import get_elevation
from server.providers.errors import ProviderDataError, ProviderServiceError
from server.providers.wind import get_wind

router = APIRouter(prefix="/providers", tags=["providers"])


def _cache_headers(payload: dict) -> dict:
    ttl = max(int(payload.get("ttl_s", 0)), 0)
    etag = str(payload.get("etag", ""))
    return {"Cache-Control": f"public, max-age={ttl}", "ETag": etag}


def _etag_matches(request: Request, etag: str) -> bool:
    if not etag:
        return False
    header = request.headers.get("if-none-match")
    if not header:
        return False
    candidates = [token.strip() for token in header.split(",") if token.strip()]
    quoted = f'"{etag}"'
    return "*" in candidates or etag in candidates or quoted in candidates


@router.get("/elevation")
async def elevation(request: Request, lat: float = Query(...), lon: float = Query(...)):
    try:
        payload = await get_elevation(lat, lon)
    except (ProviderServiceError, ProviderDataError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    if _etag_matches(request, payload.get("etag", "")):
        headers = _cache_headers(payload)
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=headers)

    headers = _cache_headers(payload)
    response = JSONResponse(payload)
    response.headers.update(headers)
    return response


@router.get("/wind")
async def wind(
    request: Request,
    lat: float = Query(...),
    lon: float = Query(...),
    bearing: Optional[float] = Query(default=None),
):
    try:
        payload = await get_wind(lat, lon, bearing=bearing)
    except (ProviderServiceError, ProviderDataError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    if _etag_matches(request, payload.get("etag", "")):
        headers = _cache_headers(payload)
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=headers)

    headers = _cache_headers(payload)
    response = JSONResponse(payload)
    response.headers.update(headers)
    return response
