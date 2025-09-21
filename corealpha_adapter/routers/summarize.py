from fastapi import APIRouter, Depends, Request

from ..app import api_key_guard, limiter
from ..schemas import SummarizeRequest, SummarizeResponse
from ..services.fingpt_service import FinGPTRAGService, get_fingpt_service

router = APIRouter(dependencies=[Depends(api_key_guard)])


@router.post("/summarize", response_model=SummarizeResponse)
@limiter.limit("30/minute")
def summarize(
    req: SummarizeRequest,
    request: Request,
    svc: FinGPTRAGService = Depends(get_fingpt_service),
):
    return svc.summarize(req)
