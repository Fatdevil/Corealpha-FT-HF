from ...schemas import VoteExplain, VoteRequest, VoteResponse


class TOPSISEngine:
    def vote(self, req: VoteRequest) -> VoteResponse:
        weights = {proposal.agent: proposal.weight for proposal in req.proposals}
        explain = VoteExplain(
            weights=weights,
            meta={"method": "TOPSIS", "status": "stub"},
        )
        return VoteResponse(
            decision="HOLD",
            explain=explain,
            calibrated_probs={"up_48h": 0.5, "down_48h": 0.5},
        )
