"""Stub implementation of the FinGPT provider used for local development and CI."""

from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Dict, Iterable, List

from ..schemas import SentimentResponse, Source, SummarizeResponse, VoteRequest, VoteResponse
from ..services.voting.factory import get_voting_engine

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


def _simple_sentiment(texts: List[str]) -> List[Dict[str, float]]:
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


class StubProvider:
    """Pure in-memory provider that mimics the FinGPT contract."""

    async def summarize(self, payload):  # type: ignore[override]
        if isinstance(payload, str):
            body = payload.strip()
            data = {"text": body}
        else:
            data = dict(payload or {})
        text = (data.get("text") or "").strip() if isinstance(data.get("text"), str) else ""
        url = data.get("url") or ""
        ticker = data.get("ticker") or ""

        if text:
            summary = (text[:200] + "...") if len(text) > 200 else text
        elif url:
            summary = f"Sammanfattning av {url}: (stub) – viktiga punkter extraheras här."
        else:
            summary = (
                f"Kort sammanfattning för {ticker or 'okänd'} – (stub) via FinGPT RAG i produktion."
            )

        sources: List[Source] = []
        if url:
            sources.append(
                Source(title="Källa", url=url, time=datetime.utcnow().isoformat())
            )
        if ticker:
            sources.append(
                Source(
                    title=f"{ticker} IR (stub)",
                    url="http://example.com/ir",
                    time=datetime.utcnow().isoformat(),
                )
            )

        resp = SummarizeResponse(
            summary=summary,
            impact="Okänd (stub)",
            sources=sources,
            latency_ms=int(time.perf_counter() * 1000) % 100,
        )
        return resp.model_dump()

    async def sentiment(self, payload):  # type: ignore[override]
        data = dict(payload or {})
        texts = [str(t) for t in data.get("texts", [])]
        vectors = _simple_sentiment(texts)
        if not vectors:
            score = 0.0
        else:
            avg_pos = sum(v["pos"] for v in vectors) / len(vectors)
            avg_neg = sum(v["neg"] for v in vectors) / len(vectors)
            score = max(-0.9, min(0.9, avg_pos - avg_neg))
        rationale = (
            "Lexikon‑baserad stub som räknar positiva/negativa ord och ger "
            "ett poäng i [-1,1]."
        )
        sources = [
            Source(title="Nyhet 1 (stub)", url="http://example.com/news1"),
            Source(title="Nyhet 2 (stub)", url="http://example.com/news2"),
        ]
        resp = SentimentResponse(score=round(score, 3), rationale=rationale, sources=sources)
        result = resp.model_dump()
        result["vectors"] = vectors
        return result

    async def vote(self, payload):  # type: ignore[override]
        data = dict(payload or {})
        proposals = data.get("proposals") or []
        vote_req = VoteRequest.model_validate({"proposals": proposals})
        engine = get_voting_engine()
        vote_resp: VoteResponse = engine.vote(vote_req)
        return vote_resp.model_dump()
