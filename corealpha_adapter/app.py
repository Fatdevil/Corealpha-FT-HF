"""FastAPI application for the CoreAlpha adapter."""

import os
from typing import Set

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

ENV = os.getenv("ENV", "dev").lower()
docs_url = None if ENV == "prod" else "/"
redoc_url = None if ENV == "prod" else "/redoc"

app = FastAPI(
    title="CoreAlpha Adapter API (v1.1)",
    version="0.1.1",
    docs_url=docs_url,
    redoc_url=redoc_url,
    description="DI‑vänligt adapter‑API för FinGPT + Agents + VotingEngine.",
)


def _parse_env_set(value: str) -> Set[str]:
    return {item.strip() for item in value.split(",") if item.strip()}


# --- CORS ---
origins = [
    origin.strip() for origin in os.getenv("TRUSTED_ORIGINS", "").split(",") if origin.strip()
]
allow_credentials = os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true"
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=allow_credentials,
    )
else:
    # Öppen CORS, men utan credentials för att undvika token/cookie-läckage
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )

# --- API-key auth (valfritt, aktiveras om API_KEYS inte är tom) ---
_API_KEYS = _parse_env_set(os.getenv("API_KEYS", ""))


def api_key_guard(req: Request):
    if not _API_KEYS:
        return  # auth avstängd
    key = req.headers.get("x-api-key")
    if not key or key not in _API_KEYS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


from .routers import agent, health, sentiment, summarize, vote  # noqa: E402

app.include_router(health.router, tags=["health"])
app.include_router(summarize.router, tags=["summarize"])
app.include_router(sentiment.router, tags=["sentiment"])
app.include_router(agent.router, tags=["agent"])
app.include_router(vote.router, tags=["vote"])

__all__ = ["app", "api_key_guard"]
