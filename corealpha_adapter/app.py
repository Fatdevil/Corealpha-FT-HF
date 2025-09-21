"""FastAPI application for the CoreAlpha adapter."""

import os
import time
import uuid
from typing import Set

import structlog
from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from prometheus_fastapi_instrumentator import Instrumentator
from secure import Secure
from secure import headers as secure_headers
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

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

# --- Trusted hosts ---
trusted_hosts = [h.strip() for h in os.getenv("TRUSTED_HOSTS", "").split(",") if h.strip()]
if trusted_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

# --- HTTPS redirect in prod ---
if ENV == "prod":
    app.add_middleware(HTTPSRedirectMiddleware)

# --- Security headers ---
_secure = Secure(
    hsts=secure_headers.StrictTransportSecurity(),
    xfo=secure_headers.XFrameOptions().deny(),
    xxp=secure_headers.XXSSProtection().set("1; mode=block"),
    content=secure_headers.XContentTypeOptions(),
    referrer=secure_headers.ReferrerPolicy(),
)
_CSP = os.getenv("CSP", "default-src 'self'")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        resp: Response = await call_next(request)
        _secure.framework.fastapi(resp)
        resp.headers.setdefault("Content-Security-Policy", _CSP)
        return resp


app.add_middleware(SecurityHeadersMiddleware)


# --- Body size limit (ASGI nivå) ---


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_bytes: int):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        mb = int(os.getenv("MAX_BODY_BYTES", str(self.max_bytes)))
        body = await request.body()
        if len(body) > mb:
            return PlainTextResponse("Request entity too large", status_code=413)
        request._body = body
        return await call_next(request)


app.add_middleware(BodySizeLimitMiddleware, max_bytes=int(os.getenv("MAX_BODY_BYTES", "1048576")))


# --- Rate limiting ---


def _rate_limit_key(request: StarletteRequest):
    api_key = request.headers.get("x-api-key")
    if api_key:
        return api_key
    return get_remote_address(request)


limiter = Limiter(
    key_func=_rate_limit_key,
    default_limits=[os.getenv("RATE_LIMIT", "60/minute")],
)


@app.exception_handler(RateLimitExceeded)
def _rate_limit_handler(request, exc):
    return PlainTextResponse("Too Many Requests", status_code=429)


app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


# --- Structured logging (JSON) ---
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
log = structlog.get_logger()


# --- Request ID / Correlation ID ---
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())
        start = time.time()
        response: Response = await call_next(request)
        dur_ms = int((time.time() - start) * 1000)
        response.headers.setdefault("x-request-id", rid)
        log.info(
            "access",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            ms=dur_ms,
            rid=rid,
        )
        return response


app.add_middleware(RequestIDMiddleware)


# --- Prometheus metrics ---
Instrumentator().instrument(app).expose(app, endpoint="/metrics", tags=["metrics"])


# --- Readiness ---
ready_router = APIRouter()


@ready_router.get("/readyz")
def readyz():
    checks = {
        "fingpt": True,
    }
    ok = all(checks.values())
    return {"ok": ok, "checks": checks}


# expose readiness endpoint
app.include_router(ready_router, tags=["ready"])

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

__all__ = ["app", "api_key_guard", "limiter"]
