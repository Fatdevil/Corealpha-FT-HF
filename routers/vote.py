from fastapi import APIRouter, Depends
from models.types import VoteReq, VoteResp
from services.voting.factory import get_voting_engine
from services.voting.base import VotingEngine
router = APIRouter()
@router.post('/vote', response_model=VoteResp)
def vote(req: VoteReq, engine: VotingEngine = Depends(get_voting_engine)):
    return engine.vote(req)
