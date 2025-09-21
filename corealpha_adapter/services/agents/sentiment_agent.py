from typing import Optional

from ...models.types import AgentProposalResp
from .base import IAgent


class SentimentAgent(IAgent):
    name = "Sentiment"
    default_weight = 0.22

    def propose(
        self,
        ticker: str,
        sentiment: Optional[float] = None,
        price: Optional[float] = None,
    ) -> AgentProposalResp:
        s = sentiment or 0.0
        vote = "BUY" if s > 0.15 else ("SELL" if s < -0.15 else "HOLD")
        conf = min(1.0, 0.5 + abs(s))
        return AgentProposalResp(
            agent=self.name,
            vote=vote,
            weight=self.default_weight,
            confidence=conf,
            rationale="Nyhetston (stub).",
            features=[f"Ton {s:+.2f}"],
        )
