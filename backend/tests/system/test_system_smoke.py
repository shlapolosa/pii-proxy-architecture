"""System smoke tests — require a live Docker stack.

Run: docker-compose up -d && pytest -m system --system
"""

import os
import pytest

pytestmark = pytest.mark.system

BASE_URL = os.getenv("PII_PROXY_URL", "http://localhost:8000")
MASTER_KEY = os.getenv("LITELLM_MASTER_KEY", "")


@pytest.fixture(scope="module")
def client():
    import httpx
    headers = {}
    if MASTER_KEY:
        headers["Authorization"] = f"Bearer {MASTER_KEY}"
    with httpx.Client(base_url=BASE_URL, headers=headers, timeout=30) as c:
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
        assert "llama3" in model_ids


class TestBasicCompletion:
    def test_clean_request_to_llama3(self, client):
        resp = client.post("/v1/chat/completions", json={
            "model": "llama3",
            "messages": [{"role": "user", "content": "Say hello in one word."}],
            "max_tokens": 10,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "choices" in data
        assert len(data["choices"]) > 0
