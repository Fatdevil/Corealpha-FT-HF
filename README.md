# Corealpha-FT-HF

## Dev setup (lint & tests)
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install           # aktiverar hooks lokalt
pre-commit run --all-files   # kör på hela repo
pytest -q
