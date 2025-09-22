from typing import Any, Iterable, List

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status

from ..app import api_key_guard, limiter
from ..providers import ProviderCircuitOpenError, ProviderConfigurationError, ProviderError
from ..schemas import SentimentRequest, SentimentResponse, Source
from ..services.llm_router import get_provider

router = APIRouter(dependencies=[Depends(api_key_guard)])
provider = get_provider()


def _coerce_sources(raw_sources: Any) -> List[Source]:
    sources: List[Source] = []
    if isinstance(raw_sources, Iterable):
        for item in raw_sources:
            if isinstance(item, Source):
                sources.append(item)
            elif isinstance(item, dict):
                try:
                    sources.append(Source.model_validate(item))
                except Exception:
                    continue
    return sources


@router.post("/sentiment", response_model=SentimentResponse)
@limiter.limit("30/minute")
async def sentiment(
    request: Request,
    req: SentimentRequest = Body(...),
):
    payload = req.model_dump(exclude_none=True)
    try:
        result = await provider.sentiment(payload)
    except ProviderConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ProviderCircuitOpenError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    default_rationale = "Provider-returned sentiment"
    sources: List[Source] = []
    score = 0.0

    if isinstance(result, dict):
        score = float(result.get("score", 0.0))
        rationale = str(result.get("rationale", default_rationale))
        sources = _coerce_sources(result.get("sources"))
    else:
        vectors = list(result) if isinstance(result, Iterable) else []
        if vectors:
            avg_pos = sum(v.get("pos", 0.0) for v in vectors) / len(vectors)
            avg_neg = sum(v.get("neg", 0.0) for v in vectors) / len(vectors)
            score = max(-0.9, min(0.9, avg_pos - avg_neg))
        rationale = (
            "Lexikon‑baserad stub som räknar positiva/negativa ord och ger ett poäng i [-1,1]."
        )
        sources = [
            Source(title="Nyhet 1 (stub)", url="http://example.com/news1"),
            Source(title="Nyhet 2 (stub)", url="http://example.com/news2"),
        ]

    return SentimentResponse(score=round(score, 3), rationale=rationale, sources=sources)
