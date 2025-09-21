# Corealpha-FT-HF

## Dev setup (lint & tests)
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install           # aktiverar hooks lokalt
pre-commit run --all-files   # kör på hela repo
pytest -q

## Run & Deploy

### Run (Docker)
```
docker run -p 8000:8000 ghcr.io/fatdevil/corealpha-adapter:latest
# eller bygg lokalt:
docker build -t corealpha-adapter .
docker run -p 8000:8000 corealpha-adapter
```

### Env
```
# sätt APP_MODULE om du vill peka explicit:
# docker run -e APP_MODULE="core.main:app" -p 8000:8000 ghcr.io/fatdevil/corealpha-adapter:latest
```

### Frontend deploy (Vercel)
```
# Lägg GitHub Secrets: VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID
# Push till main under frontend/ triggar deploy-workflow.
```
