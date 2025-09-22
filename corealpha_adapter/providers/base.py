"""Base abstractions and primitives for LLM providers."""

from __future__ import annotations

import copy
import hashlib
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ProviderError(Exception):
    """Base exception for provider errors."""

    status_code: int = 500
    error_code: str = "provider_error"

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code


class ProviderConfigurationError(ProviderError):
    status_code = 500
    error_code = "provider_configuration"


class ProviderNetworkError(ProviderError):
    status_code = 502
    error_code = "provider_network"


class ProviderTimeoutError(ProviderNetworkError):
    error_code = "provider_timeout"


class ProviderResponseError(ProviderError):
    status_code = 502
    error_code = "provider_response"


class ProviderCircuitOpenError(ProviderError):
    status_code = 503
    error_code = "provider_circuit_open"


def _clone(value: T) -> T:
    if isinstance(value, BaseModel):
        return value.model_copy(deep=True)  # type: ignore[return-value]
    return copy.deepcopy(value)


class TTLCache:
    """Simple in-memory TTL cache."""

    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = max(0, int(ttl_seconds))
        self.enabled = self.ttl_seconds > 0
        self._store: Dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any:
        if not self.enabled:
            return None
        entry = self._store.get(key)
        if not entry:
            return None
        expires_at, value = entry
        now = time.monotonic()
        if expires_at <= now:
            self._store.pop(key, None)
            return None
        return _clone(value)

    def set(self, key: str, value: Any) -> None:
        if not self.enabled:
            return
        expires_at = time.monotonic() + self.ttl_seconds
        self._store[key] = (expires_at, _clone(value))

    def clear(self) -> None:
        self._store.clear()


class BaseLLM(ABC):
    """Base class for provider implementations with caching and circuit breaker."""

    circuit_breaker_threshold = 3
    circuit_breaker_timeout_seconds = 30

    def __init__(self, *, cache_ttl_seconds: int) -> None:
        self._cache = TTLCache(cache_ttl_seconds)
        self._failures = 0
        self._circuit_open_until: Optional[float] = None

    # Public API ------------------------------------------------------------
    @abstractmethod
    async def summarize(self, req: "SummarizeRequest") -> "SummarizeResponse":
        ...

    @abstractmethod
    async def sentiment(self, req: "SentimentRequest") -> "SentimentResponse":
        ...

    @abstractmethod
    async def vote(self, req: "VoteRequest") -> "VoteResponse":
        ...

    async def aclose(self) -> None:
        """Optional cleanup for async clients."""

    # Helpers ---------------------------------------------------------------
    def _now(self) -> float:
        return time.monotonic()

    def _generate_cache_key(self, method: str, payload: Dict[str, Any]) -> str:
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(f"{method}:{serialized}".encode("utf-8")).hexdigest()
        return digest

    def _is_circuit_open(self) -> bool:
        if self._circuit_open_until is None:
            return False
        if self._circuit_open_until <= self._now():
            self._circuit_open_until = None
            self._failures = 0
            return False
        return True

    def _register_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.circuit_breaker_threshold:
            self._circuit_open_until = self._now() + self.circuit_breaker_timeout_seconds

    def _register_success(self) -> None:
        self._failures = 0
        self._circuit_open_until = None

    async def _execute(
        self,
        method: str,
        payload: Dict[str, Any],
        call: Callable[[], Awaitable[T]],
        *,
        use_cache: bool = True,
    ) -> T:
        if self._is_circuit_open():
            raise ProviderCircuitOpenError("LLM provider circuit breaker is open")

        cache_key = self._generate_cache_key(method, payload) if use_cache else None
        if use_cache and cache_key:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        try:
            result = await call()
        except ProviderError:
            self._register_failure()
            raise
        except Exception as exc:  # pragma: no cover - defensive
            self._register_failure()
            raise ProviderError("Unexpected provider failure", error_code="provider_unexpected") from exc

        self._register_success()
        if use_cache and cache_key:
            self._cache.set(cache_key, result)
        return result


# Late imports for type checking ------------------------------------------------
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ..schemas import (
        SentimentRequest,
        SentimentResponse,
        SummarizeRequest,
        SummarizeResponse,
        VoteRequest,
        VoteResponse,
    )
