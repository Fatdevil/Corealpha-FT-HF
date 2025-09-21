from dataclasses import dataclass
from typing import List, Literal, Optional, Protocol

from ...models.types import AgentProposalResp

@dataclass
class Proposal:
    agent: str
    vote: Literal['BUY','HOLD','SELL']
    weight: float
    confidence: float
    rationale: str
    features: List[str]

class IAgent(Protocol):
    name: str
    default_weight: float

    def propose(
        self,
        ticker: str,
        sentiment: Optional[float] = None,
        price: Optional[float] = None,
    ) -> AgentProposalResp:
        ...
