from typing import Optional

from ...schemas import AgentProposalResponse
from .base import IAgent, deterministic_rng


class FundamentalAgent(IAgent):
    name = "Fundamental"
    default_weight = 0.20

    def propose(
        self,
        ticker: str,
        sentiment: Optional[float] = None,
        price: Optional[float] = None,
    ) -> AgentProposalResponse:
        rng = deterministic_rng(ticker, self.name)
        pe = 15 + rng.random() * 30
        gm = 0.40 + rng.random() * 0.30
        vote = "BUY" if (gm > 0.55 and pe < 35) else ("SELL" if (gm < 0.45 and pe > 28) else "HOLD")
        conf = 0.5 + rng.random() * 0.4
        return AgentProposalResponse(
            agent=self.name,
            vote=vote,
            weight=self.default_weight,
            confidence=conf,
            rationale="Värdering vs kvalitet (stub).",
            features=[f"PE fwd {pe:.1f}x", f"GM {int(gm * 100)}%"],
        )
