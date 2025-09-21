import importlib

import pytest
from fastapi.testclient import TestClient


def test_health_endpoints():
    from corealpha_adapter.app import app

    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/healthz").status_code == 200


def test_limits_rejects_long_text():
    from pydantic import ValidationError

    from corealpha_adapter.schemas import MAX_TEXT_LEN, SummarizeRequest

    with pytest.raises(ValidationError):
        SummarizeRequest(text="x" * (MAX_TEXT_LEN + 1))


def test_auth_guard_when_enabled(monkeypatch):
    monkeypatch.setenv("API_KEYS", "k1")
    appmod = importlib.import_module("corealpha_adapter.app")

    importlib.reload(appmod)
    client = TestClient(appmod.app)

    # health endpoints remain open
    assert client.get("/health").status_code == 200

    # protected endpoints require an API key
    resp = client.post("/summarize", json={"text": "Hello"})
    assert resp.status_code == 401

    ok = client.post("/summarize", json={"text": "Hello"}, headers={"x-api-key": "k1"})
    assert ok.status_code == 200

    monkeypatch.delenv("API_KEYS", raising=False)
    importlib.reload(appmod)
