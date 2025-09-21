from ...core.config import settings
from .topsis_engine import TOPSISEngine
from .wsum_engine import WSUMEngine

_engine = None


def get_voting_engine():
    global _engine
    if _engine is None:
        _engine = TOPSISEngine() if settings.VOTING_METHOD.upper() == "TOPSIS" else WSUMEngine()
    return _engine
