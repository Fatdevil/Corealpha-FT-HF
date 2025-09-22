from fastapi import APIRouter, Body, Depends, HTTPException, Request, status

from ..app import api_key_guard, limiter
from ..providers import ProviderCircuitOpenError, ProviderConfigurationError, ProviderError
from ..schemas import VoteRequest, VoteResponse
from ..services.llm_router import get_provider

router = APIRouter(dependencies=[Depends(api_key_guard)])
provider = get_provider()


@router.post("/vote", response_model=VoteResponse)
@limiter.limit("30/minute")
async def vote(
    request: Request,
    req: VoteRequest = Body(...),
):
    payload = req.model_dump()
    try:
        result = await provider.vote(payload)
    except ProviderConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ProviderCircuitOpenError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    if isinstance(result, VoteResponse):
        return result
    if isinstance(result, dict):
        try:
            return VoteResponse.model_validate(result)
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Provider returned an invalid vote payload",
            ) from exc

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Provider returned an unsupported vote payload",
    )
