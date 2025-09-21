from typing import Protocol

from ...schemas import VoteRequest, VoteResponse


class VotingEngine(Protocol):
    def vote(self, req: VoteRequest) -> VoteResponse: ...
