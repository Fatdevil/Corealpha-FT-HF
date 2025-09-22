import time
from typing import Any, Iterable, List

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status

from ..app import api_key_guard, limiter
from ..providers import ProviderCircuitOpenError, ProviderConfigurationError, ProviderError
from ..schemas import Source, SummarizeRequest, SummarizeResponse
from ..services.llm_router import get_provider

router = APIRouter(dependencies=[Depends(api_key_guard)])
provider = get_provider()


def _coerce_sources(raw_sources: Any, fallback: List[Source]) -> List[Source]:
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
    return sources or fallback


@router.post("/summarize", response_model=SummarizeResponse)
@limiter.limit("30/minute")
async def summarize(
    request: Request,
    req: SummarizeRequest = Body(...),
):
    payload = req.model_dump(exclude_none=True)
    start = time.perf_counter()
    try:
        result = await provider.summarize(payload)
    except ProviderConfigurationError as exc:  # missing API key, etc.
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ProviderCircuitOpenError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    latency_ms = int((time.perf_counter() - start) * 1000)
    summary_text = ""
    impact = "Okänd"
    sources_data: Any = None

    if isinstance(result, dict):
        summary_text = str(result.get("summary", ""))
        impact = str(result.get("impact", impact))
        sources_data = result.get("sources")
        latency_ms = int(result.get("latency_ms", latency_ms))
    else:
        summary_text = str(result)

    fallback_sources: List[Source] = []
    if req.url:
        fallback_sources.append(Source(title="Källa", url=req.url))
    if req.ticker:
        fallback_sources.append(Source(title=f"{req.ticker} (stub)", url="http://example.com/ir"))

    sources = _coerce_sources(sources_data, fallback_sources)
    if not summary_text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Provider returned an empty summary",
        )

    return SummarizeResponse(
        summary=summary_text,
        impact=impact,
        sources=sources,
        latency_ms=latency_ms,
    )
