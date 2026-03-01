"""System smoke tests — require a live Docker stack.

Run: docker-compose up -d && pytest -m system --system
Requires: LITELLM_MASTER_KEY env var set
"""

import os
import pytest

pytestmark = pytest.mark.system

BASE_URL = os.getenv("PII_PROXY_URL", "http://localhost:8080")
MASTER_KEY = os.getenv("LITELLM_MASTER_KEY", "")


@pytest.fixture(scope="module")
def client():
    import httpx
    headers = {}
    if MASTER_KEY:
        headers["Authorization"] = f"Bearer {MASTER_KEY}"
    with httpx.Client(base_url=BASE_URL, headers=headers, timeout=60) as c:
        yield c


class TestHealthCheck:
    def test_litellm_proxy_reachable(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200


class TestModelList:
    def test_models_endpoint_returns_configured_models(self, client):
        resp = client.get("/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        model_ids = [m["id"] for m in data.get("data", [])]
        assert "local-model" in model_ids


class TestBasicCompletion:
    def test_clean_request_to_local_model(self, client):
        resp = client.post("/v1/chat/completions", json={
            "model": "local-model",
            "messages": [{"role": "user", "content": "Say hello in one word."}],
            "max_tokens": 10,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "choices" in data
        assert len(data["choices"]) > 0


class TestPIIRouting:
    def test_pii_request_reroutes_to_local_model(self, client):
        """Send PII content requesting a cloud model — should be rerouted to local-model."""
        resp = client.post("/v1/chat/completions", json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "My email is john@example.com and SSN is 123-45-6789"}],
            "max_tokens": 20,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "choices" in data
        # PII hook injects metadata into usage
        usage = data.get("usage", {})
        assert usage.get("pii_detected") is True, f"Expected pii_detected=True, got {usage}"
        assert usage.get("pii_risk_score", 0) > 0

    def test_clean_request_stays_on_cloud_model(self, client):
        """Send clean content requesting a cloud model — should stay on cloud."""
        resp = client.post("/v1/chat/completions", json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "How do I sort a list in reverse order?"}],
            "max_tokens": 20,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "choices" in data
        # No PII — should not be rerouted
        usage = data.get("usage", {})
        assert usage.get("pii_detected") is not True, f"Expected no PII, got {usage}"
