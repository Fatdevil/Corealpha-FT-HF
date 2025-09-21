import re
import time
from datetime import datetime
from typing import Dict, Iterable, List

from fastapi import HTTPException, status

from ..core.config import settings
from ..schemas import (
    SentimentRequest,
    SentimentResponse,
    Source,
    SummarizeRequest,
    SummarizeResponse,
)

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


class FinGPTRAGService:
    """
    Adapter mot FinGPT‑pipelines för:
      - Sammanfattning (RAG)
      - Sentiment

    I dev-läge används stubbar (settings.USE_STUB_*).
    Byt till riktiga HTTP-anrop när FINGPT_BASE_URL sätts.
    """

    def summarize(self, req: SummarizeRequest) -> SummarizeResponse:
        t0 = time.perf_counter()
        if settings.USE_STUB_SUMMARY or not settings.FINGPT_BASE_URL:
            summary = self._stub_summary(req)
            impact = "Okänd (stub)"
            sources = []
            if req.url:
                sources.append(
                    Source(
                        title="Källa",
                        url=req.url,
                        time=datetime.utcnow().isoformat(),
                    )
                )
            if req.ticker:
                sources.append(
                    Source(
                        title=f"{req.ticker} IR (stub)",
                        url="http://example.com/ir",
                        time=datetime.utcnow().isoformat(),
                    )
                )
            dt = int((time.perf_counter() - t0) * 1000)
            return SummarizeResponse(
                summary=summary,
                impact=impact,
                sources=sources,
                latency_ms=dt,
            )
        # TODO: call real FinGPT endpoint here (e.g., POST {base}/rag/summarize)
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="FinGPT summarize not yet available",
        )

    def sentiment(self, req: SentimentRequest) -> SentimentResponse:
        if settings.USE_STUB_SENTIMENT or not settings.FINGPT_BASE_URL:
            score = self._stub_sentiment(req.texts)
            rationale = (
                "Lexikon‑baserad stub som räknar positiva/negativa ord och ger "
                "ett poäng i [-1,1]."
            )
            sources = [
                Source(title="Nyhet 1 (stub)", url="http://example.com/news1"),
                Source(title="Nyhet 2 (stub)", url="http://example.com/news2"),
            ]
            return SentimentResponse(
                score=round(score, 3),
                rationale=rationale,
                sources=sources,
            )
        # TODO: call real FinGPT sentiment endpoint
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="FinGPT sentiment not yet available",
        )

    # --- Stubs ---
    def _stub_summary(self, req: SummarizeRequest) -> str:
        if req.text:
            text = req.text.strip()
            return (text[:200] + "...") if len(text) > 200 else text
        if req.url:
            return f"Sammanfattning av {req.url}: (stub) – viktiga punkter extraheras här."
        return (
            f"Kort sammanfattning för {req.ticker or 'okänd'} – (stub) via FinGPT RAG i produktion."
        )

    def _stub_sentiment(self, texts: Iterable[str]) -> float:
        vectors = _simple_sentiment(list(texts))
        if not vectors:
            return 0.0
        avg_pos = sum(v["pos"] for v in vectors) / len(vectors)
        avg_neg = sum(v["neg"] for v in vectors) / len(vectors)
        score = avg_pos - avg_neg
        return max(-0.9, min(0.9, score))


_svc = FinGPTRAGService()


def get_fingpt_service() -> FinGPTRAGService:
    return _svc
