from fastapi import APIRouter, Depends

from ..app import api_key_guard
from ..schemas import SentimentRequest, SentimentResponse
from ..services.fingpt_service import FinGPTRAGService, get_fingpt_service

router = APIRouter(dependencies=[Depends(api_key_guard)])


@router.post("/sentiment", response_model=SentimentResponse)
def sentiment(req: SentimentRequest, svc: FinGPTRAGService = Depends(get_fingpt_service)):
    return svc.sentiment(req)
