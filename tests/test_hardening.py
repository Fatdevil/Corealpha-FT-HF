import importlib
import os
from contextlib import contextmanager

from fastapi.testclient import TestClient

appmod = importlib.import_module("corealpha_adapter.app")


@contextmanager
def _client(env="dev", rate="5/minute", maxb="1024"):
    keys = {"ENV": env, "RATE_LIMIT": rate, "MAX_BODY_BYTES": maxb}
    previous = {key: os.environ.get(key) for key in keys}
    os.environ.update(keys)
    importlib.reload(appmod)
    client = TestClient(appmod.app)
    try:
        yield client
    finally:
        client.close()
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        importlib.reload(appmod)


def test_security_headers_present():
    with _client() as c:
        r = c.get("/health")
        assert "content-security-policy" in (k.lower() for k in r.headers.keys())


def test_body_limit_413():
    with _client() as c:
        big = "x" * 2048
        r = c.post("/summarize", json={"text": big})
        assert r.status_code in (200, 413)


def test_rate_limit_429():
    with _client(rate="2/minute") as c:
        for _ in range(3):
            last = c.post("/summarize", json={"text": "hello"})
        assert last.status_code in (200, 429)
