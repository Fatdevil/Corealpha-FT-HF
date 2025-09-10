from fastapi import APIRouter
from datetime import datetime
router = APIRouter()
@router.get('/health')
def health():
    return {'ok': True, 'time': datetime.utcnow().isoformat(), 'service': 'CoreAlpha Adapter v1.1'}
