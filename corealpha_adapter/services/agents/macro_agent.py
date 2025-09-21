from typing import Optional

from ...schemas import AgentProposalResponse
from .base import IAgent, deterministic_rng


class MacroAgent(IAgent):
    name = "Macro"
    default_weight = 0.10

    def propose(
        self,
        ticker: str,
        sentiment: Optional[float] = None,
        price: Optional[float] = None,
    ) -> AgentProposalResponse:
        rng = deterministic_rng(ticker, self.name)
        risk_on = rng.random() > 0.5
        vote = "BUY" if risk_on else "HOLD"
        conf = 0.4 + rng.random() * 0.4
        return AgentProposalResponse(
            agent=self.name,
            vote=vote,
            weight=self.default_weight,
            confidence=conf,
            rationale="Makroregim (stub).",
            features=["Risk-on" if risk_on else "Risk-off"],
        )
