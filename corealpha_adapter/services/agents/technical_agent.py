from typing import Optional

from ...schemas import AgentProposalResponse
from .base import IAgent, deterministic_rng


class TechnicalAgent(IAgent):
    name = "Technical"
    default_weight = 0.18

    def propose(
        self,
        ticker: str,
        sentiment: Optional[float] = None,
        price: Optional[float] = None,
    ) -> AgentProposalResponse:
        rng = deterministic_rng(ticker, self.name)
        rsi = 35 + rng.random() * 40
        above = rng.random() > 0.45
        vote = "BUY" if (rsi > 55 and above) else ("SELL" if (rsi < 45 and not above) else "HOLD")
        conf = 0.45 + rng.random() * 0.4
        return AgentProposalResponse(
            agent=self.name,
            vote=vote,
            weight=self.default_weight,
            confidence=conf,
            rationale="Pris/volymsignal (stub).",
            features=[f"RSI {int(rsi)}", "MA20>MA50" if above else "MA20<=MA50"],
        )
