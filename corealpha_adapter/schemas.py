"""Pydantic schemas with environment-driven limits."""

from __future__ import annotations

import os
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, conlist, constr

MAX_TEXT_LEN = int(os.getenv("MAX_TEXT_LEN", "5000"))
MAX_ITEMS = int(os.getenv("MAX_ITEMS", "200"))

TextStr = constr(strip_whitespace=True, min_length=1, max_length=MAX_TEXT_LEN)
TickerStr = constr(strip_whitespace=True, min_length=1, max_length=16)
AgentNameStr = constr(strip_whitespace=True, min_length=1, max_length=64)


class Source(BaseModel):
    title: str
    url: str
    time: Optional[str] = None


class SummarizeRequest(BaseModel):
    ticker: Optional[TickerStr] = None
    url: Optional[str] = Field(default=None, max_length=2048)
    text: Optional[TextStr] = None


class SummarizeResponse(BaseModel):
    summary: str
    impact: str
    sources: List[Source] = Field(default_factory=list)
    latency_ms: int


class SentimentRequest(BaseModel):
    ticker: Optional[TickerStr] = None
    texts: conlist(TextStr, min_length=1, max_length=MAX_ITEMS)


class SentimentResponse(BaseModel):
    score: float
    rationale: str
    sources: List[Source] = Field(default_factory=list)


class AgentProposalRequest(BaseModel):
    ticker: TickerStr
    agent: AgentNameStr
    sentiment: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    price: Optional[float] = Field(default=None, ge=0.0)


class AgentProposalResponse(BaseModel):
    agent: AgentNameStr
    vote: Literal["BUY", "HOLD", "SELL"]
    weight: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    features: List[str]


class VoteProposal(BaseModel):
    agent: AgentNameStr
    vote: Literal["BUY", "HOLD", "SELL"]
    weight: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)


class VoteRequest(BaseModel):
    proposals: conlist(VoteProposal, min_length=1, max_length=MAX_ITEMS)


class VoteExplain(BaseModel):
    weights: Dict[str, float]
    meta: Dict[str, str] = Field(default_factory=dict)


class VoteResponse(BaseModel):
    decision: Literal["BUY", "HOLD", "SELL"]
    explain: VoteExplain
    calibrated_probs: Dict[str, float]


# Backwards compatible aliases (legacy names)
SummarizeReq = SummarizeRequest
SummarizeResp = SummarizeResponse
SentimentReq = SentimentRequest
SentimentResp = SentimentResponse
AgentProposalReq = AgentProposalRequest
AgentProposalResp = AgentProposalResponse
VoteItem = VoteProposal
VoteReq = VoteRequest
VoteResp = VoteResponse

__all__ = [
    "AgentProposalReq",
    "AgentProposalRequest",
    "AgentProposalResp",
    "AgentProposalResponse",
    "AgentNameStr",
    "MAX_ITEMS",
    "MAX_TEXT_LEN",
    "SentimentReq",
    "SentimentRequest",
    "SentimentResp",
    "SentimentResponse",
    "Source",
    "SummarizeReq",
    "SummarizeRequest",
    "SummarizeResp",
    "SummarizeResponse",
    "TextStr",
    "TickerStr",
    "VoteExplain",
    "VoteItem",
    "VoteProposal",
    "VoteReq",
    "VoteRequest",
    "VoteResp",
    "VoteResponse",
]
