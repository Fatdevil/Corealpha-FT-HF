"""Provider protocol and exceptions for LLM integrations."""

from typing import Dict, List, Protocol


class BaseLLM(Protocol):
    async def summarize(self, text: str):  # type: ignore[override]
        """Return a summary for the supplied payload."""

    async def sentiment(self, texts: List[str]):  # type: ignore[override]
        """Return sentiment analysis for the supplied payload."""

    async def vote(self, proposals: List[Dict]):  # type: ignore[override]
        """Return an aggregated vote for the supplied proposals."""


class ProviderError(Exception):
    """Base class for provider errors."""


class ProviderConfigurationError(ProviderError):
    """Raised when the provider is misconfigured."""


class ProviderCircuitOpenError(ProviderError):
    """Raised when the provider circuit breaker is open."""
