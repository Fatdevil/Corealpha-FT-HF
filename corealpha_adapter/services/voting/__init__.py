"""Voting engines used by the CoreAlpha adapter."""

from .base import VotingEngine
from .factory import get_voting_engine
from .topsis_engine import TOPSISEngine
from .wsum_engine import WSUMEngine

__all__ = [
    "TOPSISEngine",
    "VotingEngine",
    "WSUMEngine",
    "get_voting_engine",
]
