"""Factory for selecting the active LLM provider based on environment variables."""

from __future__ import annotations

import os
from typing import Optional

from ..providers.base import BaseLLM

_provider: Optional[BaseLLM] = None
_provider_name: Optional[str] = None


def get_provider() -> BaseLLM:
    """Return a singleton provider instance based on ``LLM_PROVIDER``."""

    global _provider, _provider_name

    provider_name = os.getenv("LLM_PROVIDER", "stub").lower()
    if _provider is not None and provider_name == _provider_name:
        return _provider

    if provider_name == "fingpt":
        from ..providers.fingpt import FinGPTProvider

        _provider = FinGPTProvider()
    else:
        from ..providers.stub import StubProvider

        _provider = StubProvider()

    _provider_name = provider_name
    return _provider


def reset_provider() -> None:
    """Reset the cached provider (useful in tests)."""

    global _provider, _provider_name
    _provider = None
    _provider_name = None
