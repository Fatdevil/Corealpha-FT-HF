import random
from typing import Optional

from ...models.types import AgentProposalResp
from .base import IAgent


class TechnicalAgent(IAgent):
    name = "Technical"
    default_weight = 0.18

    def propose(
        self,
        ticker: str,
        sentiment: Optional[float] = None,
        price: Optional[float] = None,
    ) -> AgentProposalResp:
        rng = random.Random(hash(ticker + self.name) & 0xFFFFFFFF)
        rsi = 35 + rng.random() * 40
        above = rng.random() > 0.45
        vote = "BUY" if (rsi > 55 and above) else ("SELL" if (rsi < 45 and not above) else "HOLD")
        conf = 0.45 + rng.random() * 0.4
        return AgentProposalResp(
            agent=self.name,
            vote=vote,
            weight=self.default_weight,
            confidence=conf,
            rationale="Pris/volymsignal (stub).",
            features=[f"RSI {int(rsi)}", "MA20>MA50" if above else "MA20<=MA50"],
        )
