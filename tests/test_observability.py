from fastapi.testclient import TestClient

from corealpha_adapter.app import app


def test_readyz_and_metrics():
    client = TestClient(app)
    assert client.get("/readyz").status_code == 200
    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert "http_request_duration_seconds" in metrics_response.text
