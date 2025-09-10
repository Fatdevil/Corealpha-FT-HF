from core.config import settings
from .wsum_engine import WSUMEngine
from .topsis_engine import TOPSISEngine
_engine=None

def get_voting_engine():
    global _engine
    if _engine is None:
        _engine = TOPSISEngine() if settings.VOTING_METHOD.upper()=='TOPSIS' else WSUMEngine()
    return _engine
