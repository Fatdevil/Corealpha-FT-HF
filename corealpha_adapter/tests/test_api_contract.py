from fastapi.testclient import TestClient

from ..app import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True


def test_flow():
    summary = client.post(
        "/summarize",
        json={"ticker": "NVDA", "text": "strong growth and record margins"},
    ).json()
    sentiment = client.post(
        "/sentiment",
        json={"ticker": "NVDA", "texts": [summary["summary"]]},
    ).json()
    proposals = []
    for agent_name in ["Sentiment", "Fundamental", "Technical"]:
        proposal = client.post(
            "/agent/propose",
            json={
                "ticker": "NVDA",
                "agent": agent_name,
                "sentiment": sentiment["score"],
            },
        ).json()
        proposals.append(
            {key: proposal[key] for key in ["agent", "vote", "weight", "confidence"]}
        )
    vote = client.post("/vote", json={"proposals": proposals}).json()
    assert vote["decision"] in ["BUY", "HOLD", "SELL"]
