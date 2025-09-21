import hashlib
import random
from dataclasses import dataclass
from typing import List, Literal, Optional, Protocol

from ...schemas import AgentProposalResponse


@dataclass
class Proposal:
    agent: str
    vote: Literal["BUY", "HOLD", "SELL"]
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
    ) -> AgentProposalResponse: ...


def deterministic_rng(*parts: str) -> random.Random:
    """Return a reproducible RNG seeded via SHA-256."""
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()
    seed = int(h[:16], 16)
    return random.Random(seed)
