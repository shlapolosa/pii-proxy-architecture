"""Integration tests for the full middleware pipeline with real Presidio.

Requires: ./install.sh (spaCy en_core_web_lg model)
Run: pytest -m integration
"""

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def middleware():
    """Create a real PIIMiddleware with actual Presidio engine."""
    from litellm_middleware import PIIMiddleware
    return PIIMiddleware()


class TestMiddlewarePipeline:
    def test_clean_request_preserves_model(self, middleware):
        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "How do I sort a list in reverse order?"}],
        }
        processed, has_pii, model, details = middleware.preprocess_request(request)
        assert has_pii is False
        assert model == "gpt-4"
        assert processed["model"] == "gpt-4"

    def test_pii_request_routes_to_local(self, middleware):
        request = {
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "My email is john.doe@company.com and SSN is 123-45-6789"}
            ],
        }
        processed, has_pii, model, details = middleware.preprocess_request(request)
        assert has_pii is True
        assert model == "local-model"
        assert processed["model"] == "local-model"
        assert details["risk_score"] > 0

    def test_pii_in_conversation_history(self, middleware):
        request = {
            "model": "claude-3-opus",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "My phone is 555-123-4567"},
                {"role": "assistant", "content": "I see you shared a phone number."},
                {"role": "user", "content": "Can you remember it?"},
            ],
        }
        processed, has_pii, model, details = middleware.preprocess_request(request)
        assert has_pii is True
        assert model == "local-model"


class TestResponseEnrichment:
    def test_response_has_pii_metadata(self, middleware):
        response = {"choices": [{"message": {"content": "ok"}}]}
        pii_details = {
            "has_pii": True,
            "risk_score": 0.9,
            "original_model": "gpt-4",
            "selected_model": "local-model",
        }
        result = middleware.postprocess_response(response, pii_details)
        assert result["usage"]["pii_detected"] is True
        assert result["usage"]["model_switched"] is True
