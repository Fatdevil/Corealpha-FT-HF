from fastapi import APIRouter, Depends, HTTPException, Request

from ..app import api_key_guard, limiter
from ..schemas import SentimentRequest, SentimentResponse
from ..core.config import settings
from ..providers import BaseLLM, ProviderError
from ..services.llm_router import get_provider

router = APIRouter(dependencies=[Depends(api_key_guard)])


PROVIDER_ERROR_RESPONSE = {
    502: {
        "description": "Upstream LLM provider error",
        "content": {
            "application/json": {
                "example": {"error": "provider_error", "message": "Provider unavailable"}
            }
        },
    }
}


@router.post("/sentiment", response_model=SentimentResponse, responses=PROVIDER_ERROR_RESPONSE)
@limiter.limit("30/minute")
async def sentiment(
    req: SentimentRequest,
    request: Request,
    provider: BaseLLM = Depends(get_provider),
):
    try:
        return await provider.sentiment(req)
    except ProviderError as exc:
        detail = {"error": exc.error_code, "message": str(exc)}
        status_code = 502 if settings.ENV.lower() == "prod" else exc.status_code
        raise HTTPException(status_code=status_code, detail=detail)
