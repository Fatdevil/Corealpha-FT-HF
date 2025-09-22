"""FinGPT provider implementation with retries, caching and circuit breaker."""

from __future__ import annotations

import asyncio
import re
import time
from datetime import UTC, datetime
from typing import Dict, Iterable, List, Optional, TYPE_CHECKING

import httpx

from ..schemas import (
    SentimentRequest,
    SentimentResponse,
    Source,
    SummarizeRequest,
    SummarizeResponse,
    VoteRequest,
    VoteResponse,
)
from .base import (
    BaseLLM,
    ProviderConfigurationError,
    ProviderNetworkError,
    ProviderResponseError,
    ProviderTimeoutError,
)

if TYPE_CHECKING:  # pragma: no cover
    from ..services.voting.base import VotingEngine

_POS = {
    "good",
    "great",
    "excellent",
    "bull",
    "up",
    "strong",
    "beat",
    "growth",
    "surge",
    "upgrade",
    "raise",
    "record",
    "breakout",
    "resilient",
    "positive",
    "bullish",
    "expand",
    "improve",
    "accelerate",
}
_NEG = {
    "bad",
    "poor",
    "terrible",
    "bear",
    "down",
    "weak",
    "miss",
    "fall",
    "cut",
    "downgrade",
    "risk",
    "recession",
    "negative",
    "bearish",
    "decline",
    "contract",
    "deteriorate",
    "decelerate",
}
_WORD_RE = re.compile(r"\b[\w'-]+\b", re.IGNORECASE)


def _tokenize(text: str) -> Iterable[str]:
    return (word.lower() for word in _WORD_RE.findall(text))


def _simple_sentiment(texts: Iterable[str]) -> List[Dict[str, float]]:
    out: List[Dict[str, float]] = []
    for text in texts:
        pos = neg = 0
        for word in _tokenize(text):
            if word in _POS:
                pos += 1
            elif word in _NEG:
                neg += 1
        total = max(1, pos + neg)
        out.append({"pos": pos / total, "neg": neg / total})
    return out


class FinGPTProvider(BaseLLM):
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout: float,
        max_retries: int,
        cache_ttl_seconds: int,
        use_stub_summary: bool,
        use_stub_sentiment: bool,
        voting_engine: Optional["VotingEngine"] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        super().__init__(cache_ttl_seconds=cache_ttl_seconds)
        self._base_url = base_url.rstrip("/") if base_url else ""
        self._api_key = api_key
        self._timeout = max(0.1, float(timeout))
        self._max_retries = max(0, int(max_retries))
        self._use_stub_summary = use_stub_summary
        self._use_stub_sentiment = use_stub_sentiment
        self._voting_engine = voting_engine
        self._client = client or (
            httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(self._timeout),
                headers=self._build_headers(),
            )
            if self._base_url
            else None
        )

    async def summarize(self, req: SummarizeRequest) -> SummarizeResponse:  # type: ignore[override]
        payload = req.model_dump(exclude_none=True)

        async def call() -> SummarizeResponse:
            start = time.perf_counter()
            if self._use_stub_summary or self._client is None:
                return self._stub_summary(req, start)
            data = await self._post("/rag/summarize", payload)
            latency_ms = int((time.perf_counter() - start) * 1000)
            return self._normalise_summary(data, latency_ms)

        return await self._execute("summarize", payload or {"_": None}, call)

    async def sentiment(self, req: SentimentRequest) -> SentimentResponse:  # type: ignore[override]
        payload = req.model_dump(exclude_none=True)

        async def call() -> SentimentResponse:
            if self._use_stub_sentiment or self._client is None:
                return self._stub_sentiment(req)
            data = await self._post("/sentiment", payload)
            return self._normalise_sentiment(data)

        return await self._execute("sentiment", payload or {"_": None}, call)

    async def vote(self, req: VoteRequest) -> VoteResponse:  # type: ignore[override]
        payload = req.model_dump()

        async def call() -> VoteResponse:
            if self._voting_engine is None:
                raise ProviderConfigurationError("Voting engine is not configured for FinGPT provider")
            return self._voting_engine.vote(req)

        return await self._execute("vote", payload, call)

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    # --- HTTP helpers --------------------------------------------------
    def _build_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _backoff_seconds(self, attempt: int) -> float:
        return min(2.0, 0.2 * (2**attempt))

    async def _sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)

    async def _post(self, path: str, payload: Dict[str, object]) -> Dict[str, object]:
        if self._client is None:
            raise ProviderConfigurationError("FinGPT base URL is not configured")
        request_path = path if path.startswith("/") else f"/{path}"
        for attempt in range(self._max_retries + 1):
            try:
                response = await self._client.post(request_path, json=payload)
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise ProviderResponseError("FinGPT JSON response must be an object")
            except httpx.TimeoutException as exc:
                if attempt == self._max_retries:
                    raise ProviderTimeoutError("FinGPT request timed out") from exc
                await self._sleep(self._backoff_seconds(attempt))
                continue
            except httpx.HTTPStatusError as exc:
                if attempt == self._max_retries:
                    status_code = exc.response.status_code if exc.response else "unknown"
                    raise ProviderNetworkError(f"FinGPT upstream HTTP {status_code}") from exc
                await self._sleep(self._backoff_seconds(attempt))
                continue
            except httpx.HTTPError as exc:
                if attempt == self._max_retries:
                    raise ProviderNetworkError("FinGPT transport error") from exc
                await self._sleep(self._backoff_seconds(attempt))
                continue
            except ValueError as exc:
                raise ProviderResponseError("FinGPT JSON decode error") from exc
            return data  # type: ignore[return-value]
        raise ProviderNetworkError("FinGPT request failed")

    # --- Normalisers ---------------------------------------------------
    def _normalise_summary(self, data: Dict[str, object], latency_ms: int) -> SummarizeResponse:
        summary = self._extract_text(data, ["summary", "result", "text"]) or ""
        impact = self._extract_text(data, ["impact", "insight", "sentiment"]) or "Okänd"
        sources = self._extract_sources(data.get("sources"))
        return SummarizeResponse(summary=summary, impact=impact, sources=sources, latency_ms=latency_ms)

    def _normalise_sentiment(self, data: Dict[str, object]) -> SentimentResponse:
        score = self._extract_float(data, ["score", "sentiment", "value"], default=0.0)
        rationale = self._extract_text(data, ["rationale", "explanation", "reason"]) or ""
        sources = self._extract_sources(data.get("sources"))
        return SentimentResponse(score=float(score), rationale=rationale, sources=sources)

    def _extract_text(self, data: Dict[str, object], keys: List[str]) -> Optional[str]:
        for key in keys:
            value = data.get(key) if isinstance(data, dict) else None
            if isinstance(value, str):
                return value
            if isinstance(value, dict) and "text" in value and isinstance(value["text"], str):
                return value["text"]
        return None

    def _extract_float(self, data: Dict[str, object], keys: List[str], default: float) -> float:
        for key in keys:
            value = data.get(key) if isinstance(data, dict) else None
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, dict):
                nested = value.get("score") or value.get("value")
                if isinstance(nested, (int, float)):
                    return float(nested)
        return float(default)

    def _extract_sources(self, raw: object) -> List[Source]:
        sources: List[Source] = []
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    title = str(item.get("title") or item.get("name") or "Källa")
                    url = str(item.get("url") or "")
                    time_str = item.get("time") or item.get("timestamp")
                    if url:
                        sources.append(Source(title=title, url=url, time=time_str if isinstance(time_str, str) else None))
        return sources

    # --- Stubs ---------------------------------------------------------
    def _stub_summary(self, req: SummarizeRequest, start: float) -> SummarizeResponse:
        if req.text:
            text = req.text.strip()
            summary = (text[:200] + "...") if len(text) > 200 else text
        elif req.url:
            summary = f"Sammanfattning av {req.url}: (stub) – viktiga punkter extraheras här."
        else:
            summary = (
                f"Kort sammanfattning för {req.ticker or 'okänd'} – (stub) via FinGPT RAG i produktion."
            )
        impact = "Okänd (stub)"
        sources: List[Source] = []
        if req.url:
            sources.append(
                Source(title="Källa", url=req.url, time=datetime.now(UTC).isoformat()),
            )
        if req.ticker:
            sources.append(
                Source(
                    title=f"{req.ticker} IR (stub)",
                    url="http://example.com/ir",
                    time=datetime.now(UTC).isoformat(),
                ),
            )
        latency_ms = int((time.perf_counter() - start) * 1000)
        return SummarizeResponse(summary=summary, impact=impact, sources=sources, latency_ms=latency_ms)

    def _stub_sentiment(self, req: SentimentRequest) -> SentimentResponse:
        texts = list(req.texts)
        vectors = _simple_sentiment(texts)
        if not vectors:
            score = 0.0
        else:
            avg_pos = sum(v["pos"] for v in vectors) / len(vectors)
            avg_neg = sum(v["neg"] for v in vectors) / len(vectors)
            score = max(-0.9, min(0.9, avg_pos - avg_neg))
        rationale = (
            "Lexikon‑baserad stub som räknar positiva/negativa ord och ger ett poäng i [-1,1]."
        )
        sources = [
            Source(title="Nyhet 1 (stub)", url="http://example.com/news1"),
            Source(title="Nyhet 2 (stub)", url="http://example.com/news2"),
        ]
        return SentimentResponse(score=round(score, 3), rationale=rationale, sources=sources)
