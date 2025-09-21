from typing import Protocol

from ...models.types import VoteReq, VoteResp


class VotingEngine(Protocol):
    def vote(self, req: VoteReq) -> VoteResp:
        ...
