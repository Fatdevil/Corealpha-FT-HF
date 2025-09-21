from fastapi import APIRouter, Depends, Request

from ..app import api_key_guard, limiter
from ..schemas import SentimentRequest, SentimentResponse
from ..services.fingpt_service import FinGPTRAGService, get_fingpt_service

router = APIRouter(dependencies=[Depends(api_key_guard)])


@router.post("/sentiment", response_model=SentimentResponse)
@limiter.limit("30/minute")
def sentiment(
    req: SentimentRequest,
    request: Request,
    svc: FinGPTRAGService = Depends(get_fingpt_service),
):
    return svc.sentiment(req)
