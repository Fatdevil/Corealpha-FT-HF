# Corealpha-FT-HF

![CI](https://github.com/Fatdevil/Corealpha-FT-HF/actions/workflows/ci.yml/badge.svg)
![Lint](https://github.com/Fatdevil/Corealpha-FT-HF/actions/workflows/lint.yml/badge.svg)
![E2E](https://github.com/Fatdevil/Corealpha-FT-HF/actions/workflows/e2e-adapter.yml/badge.svg)

## Dev setup (lint & tests)
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install           # aktiverar hooks lokalt
pre-commit run --all-files   # kör på hela repo
pytest -q

## Run & Deploy

### Run (Docker)
```
docker run -e APP_MODULE="corealpha_adapter.app:app" -p 8000:8000 ghcr.io/fatdevil/corealpha-adapter:latest
# eller bygg lokalt:
docker build -t corealpha-adapter .
docker run -p 8000:8000 corealpha-adapter
```

### Run locally

# with GHCR image
cp .env.example .env
docker compose up -d
open http://localhost:8000/healthz

### Env
```
# sätt APP_MODULE om du vill peka explicit:
# docker run -e APP_MODULE="corealpha_adapter.app:app" -p 8000:8000 ghcr.io/fatdevil/corealpha-adapter:latest
```

### Providers & Config

Backendens LLM‑anrop går via ett utbytbart provider‑lager med FinGPT som default. Konfigurationen styrs via `.env`:

| Variabel | Beskrivning |
| --- | --- |
| `LLM_PROVIDER` | `fingpt` (default) eller `openai` (stub). |
| `FINGPT_BASE_URL` / `FINGPT_API_KEY` | Endpoint + nyckel mot FinGPT. Lämna tomt i dev för stubbar. |
| `HTTP_TIMEOUT_SECONDS` | Per-request timeout för FinGPT-klienten. |
| `HTTP_MAX_RETRIES` | Antal retries med backoff (0 = av). |
| `CACHE_TTL_SECONDS` | In‑memory TTL-cache för identiska prompts/responser. |

Fel från provider rapporteras med JSON `{ "error": <kod>, "message": <text> }`. I `ENV=prod` ges HTTP 502 (Bad Gateway) vid t.ex. `provider_timeout`, `provider_network` eller `provider_circuit_open` (circuit breaker efter 3 misslyckanden). Utan konfigurerad FinGPT fallback: stubbar som efterliknar tidigare beteende.

### Security & limits

| Variable | Description |
| --- | --- |
| `RATE_LIMIT` | Global limit per IP/API-nyckel, t.ex. `60/minute` eller `1000/hour`. |
| `MAX_BODY_BYTES` | Max request body (ASGI-nivå). Default `1048576` (1 MiB). |
| `TRUSTED_HOSTS` | Komma-separerad lista för Starlette TrustedHostMiddleware. |
| `CSP` | Content-Security-Policy header, default `default-src 'self'`. |
| `API_KEYS` | Aktiverar API-nyckelkrav (`X-API-Key: <key>` i request). |

Alla värden kan sättas i `.env`; API-nycklar skickas som header `X-API-Key: <key>`.

### Observability

- `/metrics` (Prometheus) – latency, fel och throughput via instrumentatorn.
- `/health`, `/healthz` – liveness.
- `/readyz` – readiness med externa beroenden (FinGPT stub).
- JSON-strukturerade loggar med `x-request-id` i både headers och loggar.

### Frontend deploy (Vercel)
```
# Lägg GitHub Secrets: VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID
# Push till main under frontend/ triggar deploy-workflow.
```
