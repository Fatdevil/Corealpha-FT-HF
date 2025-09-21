from fastapi import APIRouter, Depends, HTTPException

from ..models.types import AgentProposalReq, AgentProposalResp
from ..services.agents.registry import AgentRegistry, get_agent_registry

router = APIRouter()


@router.post("/agent/propose", response_model=AgentProposalResp)
def agent_propose(
    req: AgentProposalReq, reg: AgentRegistry = Depends(get_agent_registry)
):
    agent = reg.get(req.agent)
    if not agent:
        raise HTTPException(
            status_code=404, detail=f"Agent '{req.agent}' ej registrerad"
        )
    return agent.propose(
        ticker=req.ticker,
        sentiment=req.sentiment,
        price=req.price,
    )
