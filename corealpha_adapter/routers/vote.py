from fastapi import APIRouter, Depends

from ..app import api_key_guard
from ..schemas import VoteRequest, VoteResponse
from ..services.voting.base import VotingEngine
from ..services.voting.factory import get_voting_engine

router = APIRouter(dependencies=[Depends(api_key_guard)])


@router.post("/vote", response_model=VoteResponse)
def vote(req: VoteRequest, engine: VotingEngine = Depends(get_voting_engine)):
    return engine.vote(req)
