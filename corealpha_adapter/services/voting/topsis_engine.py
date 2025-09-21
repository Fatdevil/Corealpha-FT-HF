from ...models.types import VoteExplain, VoteReq, VoteResp


class TOPSISEngine:
    def vote(self, req: VoteReq) -> VoteResp:
        weights = {proposal.agent: proposal.weight for proposal in req.proposals}
        explain = VoteExplain(
            weights=weights,
            meta={"method": "TOPSIS", "status": "stub"},
        )
        return VoteResp(
            decision="HOLD",
            explain=explain,
            calibrated_probs={"up_48h": 0.5, "down_48h": 0.5},
        )
