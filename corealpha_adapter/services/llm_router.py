"""Factory for resolving the active LLM provider."""

from __future__ import annotations

from typing import Optional

from ..core.config import settings
from ..providers import BaseLLM, FinGPTProvider, OpenAIProvider
from .voting.factory import get_voting_engine

_provider: Optional[BaseLLM] = None


def _build_provider() -> BaseLLM:
    provider_name = (settings.LLM_PROVIDER or "fingpt").strip().lower()
    cache_ttl = int(settings.CACHE_TTL_SECONDS)
    if provider_name == "openai":
        return OpenAIProvider(cache_ttl_seconds=cache_ttl)
    return FinGPTProvider(
        base_url=settings.FINGPT_BASE_URL,
        api_key=settings.FINGPT_API_KEY,
        timeout=float(settings.HTTP_TIMEOUT_SECONDS),
        max_retries=int(settings.HTTP_MAX_RETRIES),
        cache_ttl_seconds=cache_ttl,
        use_stub_summary=settings.USE_STUB_SUMMARY,
        use_stub_sentiment=settings.USE_STUB_SENTIMENT,
        voting_engine=get_voting_engine(),
    )


def get_provider() -> BaseLLM:
    global _provider
    if _provider is None:
        _provider = _build_provider()
    return _provider


def reset_provider() -> None:
    global _provider
    _provider = None


async def close_provider() -> None:
    global _provider
    if _provider is not None:
        await _provider.aclose()
        _provider = None
