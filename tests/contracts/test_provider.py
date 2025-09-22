from __future__ import annotations

import httpx
import pytest
import respx

from corealpha_adapter.providers import (
    ProviderCircuitOpenError,
    ProviderConfigurationError,
    ProviderError,
)
from corealpha_adapter.providers.fingpt import FinGPTProvider


@pytest.fixture(autouse=True)
def _reset_env(monkeypatch):
    monkeypatch.setenv("FINGPT_BASE_URL", "https://api.fingpt.test")
    monkeypatch.setenv("FINGPT_API_KEY", "secret")
    monkeypatch.setenv("HTTP_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("HTTP_MAX_RETRIES", "2")
    monkeypatch.setenv("HTTP_CACHE_SECONDS", "60")
    monkeypatch.setenv("HTTP_BACKOFF_SECONDS", "0.0")
    yield
    monkeypatch.delenv("FINGPT_BASE_URL", raising=False)
    monkeypatch.delenv("FINGPT_API_KEY", raising=False)
    monkeypatch.delenv("HTTP_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("HTTP_MAX_RETRIES", raising=False)
    monkeypatch.delenv("HTTP_CACHE_SECONDS", raising=False)
    monkeypatch.delenv("HTTP_BACKOFF_SECONDS", raising=False)


@pytest.fixture
def provider():
    return FinGPTProvider()


@pytest.mark.asyncio
async def test_summarize_success_and_cache(provider):
    payload = {"text": "hello world"}
    sample = {
        "summary": "Hello World",  # case-changed to show transformation
        "impact": "Bullish",
        "sources": [{"title": "Doc", "url": "http://example.com"}],
        "latency_ms": 12,
    }
    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.post("https://api.fingpt.test/summarize").mock(
            return_value=httpx.Response(200, json=sample)
        )
        first = await provider.summarize(payload)
        assert first["summary"] == "Hello World"
        second = await provider.summarize(payload)
        assert route.called
        assert route.call_count == 1  # cache hit prevents a second HTTP request
        assert second == first


@pytest.mark.asyncio
async def test_sentiment_retries_then_success(monkeypatch, provider):
    payload = {"texts": ["good up"], "ticker": "NVDA"}
    request = httpx.Request("POST", "https://api.fingpt.test/sentiment")
    responses = [
        httpx.ReadTimeout("boom", request=request),
        httpx.ConnectTimeout("boom", request=request),
        httpx.Response(200, json={"score": 0.42, "rationale": "LLM"}),
    ]

    async def fast_sleep(_):
        return None

    monkeypatch.setattr("corealpha_adapter.providers.fingpt.asyncio.sleep", fast_sleep)

    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.post("https://api.fingpt.test/sentiment")
        route.side_effect = responses
        result = await provider.sentiment(payload)
        assert result["score"] == pytest.approx(0.42)
        assert route.call_count == 3


@pytest.mark.asyncio
async def test_circuit_breaker_opens(monkeypatch, provider):
    payload = {"proposals": [{"agent": "A", "vote": "BUY", "weight": 1.0, "confidence": 1.0}]}
    request = httpx.Request("POST", "https://api.fingpt.test/vote")
    failure = httpx.ConnectError("boom", request=request)

    async def fast_sleep(_):
        return None

    monkeypatch.setattr("corealpha_adapter.providers.fingpt.asyncio.sleep", fast_sleep)

    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.post("https://api.fingpt.test/vote")
        route.side_effect = failure
        with pytest.raises(ProviderError):
            await provider.vote(payload)
        assert route.call_count == 3  # initial try + 2 retries

        with pytest.raises(ProviderCircuitOpenError):
            await provider.vote(payload)
        # circuit breaker should block the second call immediately
        assert route.call_count == 3


@pytest.mark.asyncio
async def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("FINGPT_API_KEY", raising=False)
    provider = FinGPTProvider()
    with pytest.raises(ProviderConfigurationError):
        await provider.summarize({"text": "hello"})
