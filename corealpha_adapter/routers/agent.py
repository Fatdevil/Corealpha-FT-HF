from fastapi import APIRouter, Depends, HTTPException

from ..app import api_key_guard
from ..schemas import AgentProposalRequest, AgentProposalResponse
from ..services.agents.registry import AgentRegistry, get_agent_registry

router = APIRouter(dependencies=[Depends(api_key_guard)])


@router.post("/agent/propose", response_model=AgentProposalResponse)
def agent_propose(req: AgentProposalRequest, reg: AgentRegistry = Depends(get_agent_registry)):
    agent = reg.get(req.agent)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{req.agent}' ej registrerad")
    return agent.propose(
        ticker=req.ticker,
        sentiment=req.sentiment,
        price=req.price,
    )
