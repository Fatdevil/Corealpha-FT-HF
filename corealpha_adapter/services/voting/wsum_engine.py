import math

from ...models.types import VoteExplain, VoteReq, VoteResp


def vote_to_score(v: str) -> int:
    return 1 if v == "BUY" else (-1 if v == "SELL" else 0)


class WSUMEngine:
    def vote(self, req: VoteReq) -> VoteResp:
        score = 0.0
        weights = {}
        for proposal in req.proposals:
            score += proposal.weight * vote_to_score(proposal.vote)
            weights[proposal.agent] = proposal.weight
        decision = "BUY" if score > 0.05 else ("SELL" if score < -0.05 else "HOLD")
        prob_up = 1.0 / (1.0 + math.exp(-3.0 * score))
        explain = VoteExplain(
            weights=weights,
            meta={"method": "WSUM", "thresholds": "+/-0.05"},
        )
        return VoteResp(
            decision=decision,
            explain=explain,
            calibrated_probs={
                "up_48h": round(prob_up, 3),
                "down_48h": round(1 - prob_up, 3),
            },
        )
