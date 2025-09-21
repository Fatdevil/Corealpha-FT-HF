from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Source(BaseModel):
    title: str
    url: str
    time: Optional[str] = None


class SummarizeReq(BaseModel):
    ticker: Optional[str] = None
    url: Optional[str] = None
    text: Optional[str] = None


class SummarizeResp(BaseModel):
    summary: str
    impact: str
    sources: List[Source] = Field(default_factory=list)
    latency_ms: int


class SentimentReq(BaseModel):
    ticker: str
    texts: List[str]


class SentimentResp(BaseModel):
    score: float
    rationale: str
    sources: List[Source] = Field(default_factory=list)


class AgentProposalReq(BaseModel):
    ticker: str
    agent: str
    sentiment: Optional[float] = None
    price: Optional[float] = None


class AgentProposalResp(BaseModel):
    agent: str
    vote: Literal["BUY", "HOLD", "SELL"]
    weight: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    rationale: str
    features: List[str]


class VoteItem(BaseModel):
    agent: str
    vote: Literal["BUY", "HOLD", "SELL"]
    weight: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)


class VoteReq(BaseModel):
    proposals: List[VoteItem]


class VoteExplain(BaseModel):
    weights: Dict[str, float]
    meta: Dict[str, str] = Field(default_factory=dict)


class VoteResp(BaseModel):
    decision: Literal["BUY", "HOLD", "SELL"]
    explain: VoteExplain
    calibrated_probs: Dict[str, float]
