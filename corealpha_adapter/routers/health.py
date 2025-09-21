from datetime import datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {
        "ok": True,
        "time": datetime.utcnow().isoformat(),
        "service": "CoreAlpha Adapter v1.1",
    }
