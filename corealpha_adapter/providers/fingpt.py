"""HTTP-backed FinGPT provider with retries, caching and a circuit breaker."""

from __future__ import annotations

import asyncio
import copy
import json
import os
import time
from typing import Any, Dict, Tuple

import httpx

from .base import ProviderCircuitOpenError, ProviderConfigurationError, ProviderError


class FinGPTProvider:
    """Provider that talks to the FinGPT HTTP API."""

    def __init__(self) -> None:
        self._base_url = os.getenv("FINGPT_BASE_URL", "").rstrip("/")
        self._api_key = os.getenv("FINGPT_API_KEY", "")
        self._timeout = int(os.getenv("HTTP_TIMEOUT_SECONDS", "20"))
        self._max_retries = int(os.getenv("HTTP_MAX_RETRIES", "2"))
        self._cache_ttl = float(os.getenv("HTTP_CACHE_SECONDS", "30"))
        self._backoff_base = float(os.getenv("HTTP_BACKOFF_SECONDS", "0.5"))
        self._circuit_threshold = 3
        self._circuit_open_seconds = 30.0
        self._failure_count = 0
        self._circuit_open_until = 0.0
        self._cache: Dict[Tuple[str, str], Tuple[float, Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def summarize(self, payload):  # type: ignore[override]
        request_payload = self._normalize_payload(payload)
        data = await self._request("/summarize", request_payload)
        return data

    async def sentiment(self, payload):  # type: ignore[override]
        request_payload = self._normalize_payload(payload)
        data = await self._request("/sentiment", request_payload)
        return data

    async def vote(self, payload):  # type: ignore[override]
        request_payload = self._normalize_payload(payload)
        data = await self._request("/vote", request_payload)
        return data

    async def _request(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self._base_url:
            raise ProviderConfigurationError("FINGPT_BASE_URL is not configured")
        if not self._api_key:
            raise ProviderConfigurationError("FINGPT_API_KEY is not configured")

        cache_key = (path, json.dumps(payload, sort_keys=True))
        now = time.monotonic()

        cached = await self._get_cached(cache_key, now)
        if cached is not None:
            return cached

        await self._ensure_circuit_closed(now)

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = await self._execute_request(path, payload)
                response.raise_for_status()
                data: Dict[str, Any] = response.json()
                await self._record_success()
                await self._store_cache(cache_key, data, now)
                return data
            except (
                httpx.HTTPStatusError,
                httpx.RequestError,
            ) as exc:  # pragma: no cover - defensive
                last_error = exc
                await self._record_failure(now)
                if attempt >= self._max_retries:
                    break
                await asyncio.sleep(self._backoff_base * (2**attempt))

        if isinstance(last_error, httpx.HTTPStatusError):
            raise ProviderError(
                f"FinGPT request failed with status {last_error.response.status_code}"
            ) from last_error
        if last_error is not None:
            raise ProviderError("FinGPT request failed") from last_error
        raise ProviderError("FinGPT request failed")

    async def _execute_request(self, path: str, payload: Dict[str, Any]) -> httpx.Response:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as client:
            return await client.post(path, json=payload, headers=headers)

    async def _get_cached(self, cache_key: Tuple[str, str], now: float) -> Dict[str, Any] | None:
        async with self._lock:
            item = self._cache.get(cache_key)
            if not item:
                return None
            expires_at, value = item
            if expires_at < now:
                del self._cache[cache_key]
                return None
            return copy.deepcopy(value)

    async def _store_cache(
        self, cache_key: Tuple[str, str], value: Dict[str, Any], now: float
    ) -> None:
        async with self._lock:
            self._cache[cache_key] = (now + self._cache_ttl, copy.deepcopy(value))

    async def _ensure_circuit_closed(self, now: float) -> None:
        async with self._lock:
            if self._circuit_open_until and now < self._circuit_open_until:
                raise ProviderCircuitOpenError("FinGPT circuit breaker is open")
            if self._circuit_open_until and now >= self._circuit_open_until:
                self._failure_count = 0
                self._circuit_open_until = 0.0

    async def _record_success(self) -> None:
        async with self._lock:
            self._failure_count = 0
            self._circuit_open_until = 0.0

    async def _record_failure(self, now: float) -> None:
        async with self._lock:
            self._failure_count += 1
            if self._failure_count >= self._circuit_threshold:
                self._circuit_open_until = now + self._circuit_open_seconds

    @staticmethod
    def _normalize_payload(payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return dict(payload)
        if payload is None:
            return {}
        return {"text": payload}
