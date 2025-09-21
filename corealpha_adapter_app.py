"""Expose the packaged CoreAlpha adapter FastAPI app and ensure /healthz."""
from __future__ import annotations

import pathlib
import sys

from fastapi import FastAPI

# Instantiate a placeholder app so the auto-discovery logic can detect this module.
app = FastAPI(title="CoreAlpha Adapter")

# Make sure the packaged adapter zip is importable so we can reuse the real app.
_zip_path = pathlib.Path(__file__).resolve().parent / "corealpha_end2end_v1_1_FIXED.zip"
if _zip_path.exists():
    sys.path.insert(0, str(_zip_path))

try:
    from corealpha_end2end_v1_1.backend.app import app as _packaged_app  # type: ignore
except Exception:  # pragma: no cover - packaged app might be unavailable in some contexts
    _packaged_app = None

if _packaged_app is not None:
    app = _packaged_app

# --- Health router (auto-added) ---
try:
    from fastapi import APIRouter

    _health_router = APIRouter()

    @_health_router.get("/healthz")
    def _healthz():
        return {"ok": True}

    # inkludera en gång
    if "app" in globals():
        try:
            app.include_router(_health_router)
        except Exception:
            pass
except Exception:
    pass
# --- end health router ---
