"""Module entry point for running the adapter via ``python -m``."""

from .app import app

try:  # pragma: no cover - only executed when uvicorn is available
    import uvicorn
except ModuleNotFoundError:  # pragma: no cover
    raise SystemExit(
        "uvicorn måste vara installerat för att köra 'python -m corealpha_adapter'."
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
