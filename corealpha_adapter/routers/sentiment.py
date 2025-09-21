from fastapi import APIRouter, Depends

from ..models.types import SentimentReq, SentimentResp
from ..services.fingpt_service import FinGPTRAGService, get_fingpt_service

router = APIRouter()


@router.post("/sentiment", response_model=SentimentResp)
def sentiment(
    req: SentimentReq, svc: FinGPTRAGService = Depends(get_fingpt_service)
):
    return svc.sentiment(req)
