"""Stub OpenAI provider implementation."""

from __future__ import annotations

from .base import BaseLLM, ProviderConfigurationError


class OpenAIProvider(BaseLLM):
    """Placeholder implementation that signals missing configuration."""

    def __init__(self, *, cache_ttl_seconds: int) -> None:
        super().__init__(cache_ttl_seconds=cache_ttl_seconds)

    async def summarize(self, req):  # type: ignore[override]
        raise ProviderConfigurationError("OpenAI provider is not configured")

    async def sentiment(self, req):  # type: ignore[override]
        raise ProviderConfigurationError("OpenAI provider is not configured")

    async def vote(self, req):  # type: ignore[override]
        raise ProviderConfigurationError("OpenAI provider is not configured")

    async def aclose(self) -> None:
        return
