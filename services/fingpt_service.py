import time
from typing import List
from datetime import datetime
from models.types import SummarizeReq, SummarizeResp, SentimentReq, SentimentResp, Source
from core.config import settings

POS_WORDS = set("strong beat growth surge upgrade raise record breakout resilient positive bullish expand improve accelerate".split())
NEG_WORDS = set("weak miss fall cut downgrade risk recession negative bearish decline contract deteriorate decelerate".split())

class FinGPTRAGService:
    """
    Adapter mot FinGPT‑pipelines för:
      - Sammanfattning (RAG)
      - Sentiment
    I dev-läge används stubbar (settings.USE_STUB_*). Byt till riktiga HTTP-anrop när FINGPT_BASE_URL sätts.
    """
    def summarize(self, req: SummarizeReq) -> SummarizeResp:
        t0 = time.perf_counter()
        if settings.USE_STUB_SUMMARY or not settings.FINGPT_BASE_URL:
            summary = self._stub_summary(req)
            impact = "Okänd (stub)"
            sources = []
            if req.url:
                sources.append(Source(title="Källa", url=req.url, time=datetime.utcnow().isoformat()))
            if req.ticker:
                sources.append(Source(title=f"{req.ticker} IR (stub)", url="http://example.com/ir", time=datetime.utcnow().isoformat()))
            dt = int((time.perf_counter()-t0)*1000)
            return SummarizeResp(summary=summary, impact=impact, sources=sources, latency_ms=dt)
        # TODO: call real FinGPT endpoint here (e.g., POST {base}/rag/summarize)
        raise NotImplementedError("FinGPT integration ej implementerad ännu")

    def sentiment(self, req: SentimentReq) -> SentimentResp:
        if settings.USE_STUB_SENTIMENT or not settings.FINGPT_BASE_URL:
            s = self._stub_sentiment(req.texts)
            rationale = "Lexikon‑baserad stub som räknar positiva/negativa ord och ger ett poäng i [-1,1]."
            sources = [Source(title="Nyhet 1 (stub)", url="http://example.com/news1"),
                       Source(title="Nyhet 2 (stub)", url="http://example.com/news2")]
            return SentimentResp(score=round(s,3), rationale=rationale, sources=sources)
        # TODO: call real FinGPT sentiment endpoint
        raise NotImplementedError("FinGPT integration ej implementerad ännu")

    # --- Stubs ---
    def _stub_summary(self, req: SummarizeReq) -> str:
        if req.text:
            t = req.text.strip()
            return (t[:240]+"...") if len(t)>240 else t
        if req.url:
            return f"Sammanfattning av {req.url}: (stub) – viktiga punkter extraheras här."
        return f"Kort sammanfattning för {req.ticker or 'okänd'} – (stub) via FinGPT RAG i produktion."

    def _stub_sentiment(self, texts: List[str]) -> float:
        pos = sum(sum(1 for w in t.lower().split() if w.strip(".,!?\"'()") in POS_WORDS) for t in texts)
        neg = sum(sum(1 for w in t.lower().split() if w.strip(".,!?\"'()") in NEG_WORDS) for t in texts)
        if pos+neg == 0: return 0.0
        s = (pos - neg) / (pos + neg)
        s = max(-0.9, min(0.9, s))
        return s

_svc = FinGPTRAGService()
def get_fingpt_service() -> FinGPTRAGService:
    return _svc
