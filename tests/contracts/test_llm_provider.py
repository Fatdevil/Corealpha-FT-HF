from typing import List

import httpx
import pytest

from corealpha_adapter.providers import (
    FinGPTProvider,
    ProviderCircuitOpenError,
    ProviderNetworkError,
)
from corealpha_adapter.schemas import SummarizeRequest

pytestmark = pytest.mark.asyncio


@pytest.mark.contract
async def test_fingpt_retry_and_normalisation(monkeypatch):
    calls: List[str] = []

    responses = [
        httpx.Response(500, json={"error": "upstream"}),
        httpx.Response(
            200,
            json={
                "summary": "Market rallied strongly",
                "impact": "bullish",
                "sources": [{"title": "Note", "url": "https://example.com/note"}],
            },
        ),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return responses.pop(0)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="https://api.test")
    provider = FinGPTProvider(
        base_url="https://api.test",
        api_key="secret",
        timeout=0.1,
        max_retries=1,
        cache_ttl_seconds=60,
        use_stub_summary=False,
        use_stub_sentiment=False,
        voting_engine=None,
        client=client,
    )

    sleep_calls: List[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr(provider, "_sleep", fake_sleep)

    response = await provider.summarize(SummarizeRequest(text="Hello world"))

    assert calls == ["/rag/summarize", "/rag/summarize"]
    assert sleep_calls  # backoff triggered
    assert response.summary == "Market rallied strongly"
    assert response.impact.lower() == "bullish"
    assert response.sources[0].url == "https://example.com/note"
    assert response.latency_ms >= 0

    await provider.aclose()


@pytest.mark.contract
async def test_fingpt_cache_hits():
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            200,
            json={
                "summary": "Cached response",
                "impact": "neutral",
                "sources": [],
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="https://api.test")
    provider = FinGPTProvider(
        base_url="https://api.test",
        api_key="secret",
        timeout=0.1,
        max_retries=0,
        cache_ttl_seconds=60,
        use_stub_summary=False,
        use_stub_sentiment=False,
        voting_engine=None,
        client=client,
    )

    req = SummarizeRequest(text="Cache me")
    first = await provider.summarize(req)
    second = await provider.summarize(req)

    assert call_count == 1
    assert first.summary == second.summary
    assert first is not second  # cached copy

    await provider.aclose()


@pytest.mark.contract
async def test_circuit_breaker_opens_after_failures():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "bad"})

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="https://api.test")
    provider = FinGPTProvider(
        base_url="https://api.test",
        api_key="secret",
        timeout=0.1,
        max_retries=0,
        cache_ttl_seconds=60,
        use_stub_summary=False,
        use_stub_sentiment=False,
        voting_engine=None,
        client=client,
    )

    req = SummarizeRequest(text="trigger")

    for _ in range(3):
        with pytest.raises(ProviderNetworkError):
            await provider.summarize(req)

    with pytest.raises(ProviderCircuitOpenError) as excinfo:
        await provider.summarize(req)

    assert excinfo.value.status_code == 503

    await provider.aclose()
