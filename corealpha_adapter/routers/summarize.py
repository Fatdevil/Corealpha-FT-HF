from fastapi import APIRouter, Depends

from ..app import api_key_guard
from ..schemas import SummarizeRequest, SummarizeResponse
from ..services.fingpt_service import FinGPTRAGService, get_fingpt_service

router = APIRouter(dependencies=[Depends(api_key_guard)])


@router.post("/summarize", response_model=SummarizeResponse)
def summarize(req: SummarizeRequest, svc: FinGPTRAGService = Depends(get_fingpt_service)):
    return svc.summarize(req)
