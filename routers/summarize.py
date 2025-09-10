from fastapi import APIRouter, Depends
from models.types import SummarizeReq, SummarizeResp
from services.fingpt_service import FinGPTRAGService, get_fingpt_service
router = APIRouter()
@router.post('/summarize', response_model=SummarizeResp)
def summarize(req: SummarizeReq, svc: FinGPTRAGService = Depends(get_fingpt_service)):
    return svc.summarize(req)
