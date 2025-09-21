import math
from typing import List

from ...schemas import VoteExplain, VoteRequest, VoteResponse


def vote_to_signal(v: str) -> float:
    if v == "BUY":
        return 1.0
    if v == "SELL":
        return 0.0
    return 0.5


def wsum_probability(weights: List[float], signals: List[float]) -> float:
    if len(weights) != len(signals) or not weights:
        return 0.5
    s = sum(max(0.0, min(1.0, w)) for w in weights)
    if s == 0:
        return 0.5
    norm_w = [max(0.0, min(1.0, w)) / s for w in weights]
    score = sum(w * x for w, x in zip(norm_w, signals))
    k = 5.0
    p = 1.0 / (1.0 + math.exp(-k * (score - 0.5)))
    return max(0.0, min(1.0, p))


class WSUMEngine:
    def vote(self, req: VoteRequest) -> VoteResponse:
        weights = [proposal.weight for proposal in req.proposals]
        signals = [vote_to_signal(proposal.vote) for proposal in req.proposals]
        prob_up = wsum_probability(weights, signals)
        decision = "BUY" if prob_up > 0.55 else ("SELL" if prob_up < 0.45 else "HOLD")

        s = sum(max(0.0, min(1.0, w)) for w in weights)
        if s == 0:
            normalized = [1.0 / len(weights)] * len(weights)
        else:
            normalized = [max(0.0, min(1.0, w)) / s for w in weights]

        explain = VoteExplain(
            weights={
                proposal.agent: round(norm_w, 4)
                for proposal, norm_w in zip(req.proposals, normalized)
            },
            meta={
                "method": "WSUM",
                "calibration": "logit(k=5.0)",
                "decision_threshold": "0.55/0.45",
            },
        )
        return VoteResponse(
            decision=decision,
            explain=explain,
            calibrated_probs={
                "up_48h": round(prob_up, 3),
                "down_48h": round(1 - prob_up, 3),
            },
        )
