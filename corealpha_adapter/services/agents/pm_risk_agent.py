from typing import Optional

from ...schemas import AgentProposalResponse
from .base import IAgent, deterministic_rng


class PMRiskAgent(IAgent):
    name = "PM / Risk"
    default_weight = 0.12

    def propose(
        self,
        ticker: str,
        sentiment: Optional[float] = None,
        price: Optional[float] = None,
    ) -> AgentProposalResponse:
        rng = deterministic_rng(ticker, self.name)
        dd_ok = rng.random() > 0.3
        vote = "BUY" if dd_ok else "HOLD"
        conf = 0.4 + rng.random() * 0.4
        return AgentProposalResponse(
            agent=self.name,
            vote=vote,
            weight=self.default_weight,
            confidence=conf,
            rationale="Portföljregler (stub).",
            features=["DD-budget ok" if dd_ok else "DD-budget låg"],
        )
