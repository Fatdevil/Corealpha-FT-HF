from fastapi import APIRouter, Depends, Request

from ..app import api_key_guard, limiter
from ..schemas import VoteRequest, VoteResponse
from ..services.voting.base import VotingEngine
from ..services.voting.factory import get_voting_engine

router = APIRouter(dependencies=[Depends(api_key_guard)])


@router.post("/vote", response_model=VoteResponse)
@limiter.limit("30/minute")
def vote(
    req: VoteRequest,
    request: Request,
    engine: VotingEngine = Depends(get_voting_engine),
):
    return engine.vote(req)
