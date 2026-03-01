"""Unit tests for litellm_middleware.py — PIIMiddleware

Uses __new__() to skip __init__ and injects a mock pii_service directly.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys

pytestmark = pytest.mark.unit


def _make_middleware(mock_pii_service):
    """Create a PIIMiddleware without triggering __init__ (avoids spaCy import)."""
    # Patch presidio_config and pii_detection_service in sys.modules
    with patch.dict("sys.modules", {
        "presidio_config": MagicMock(),
        "pii_detection_service": MagicMock(pii_service=mock_pii_service),
    }):
        if "litellm_middleware" in sys.modules:
            del sys.modules["litellm_middleware"]
        from litellm_middleware import PIIMiddleware

        mw = PIIMiddleware.__new__(PIIMiddleware)
        mw.pii_service = mock_pii_service
        mw.models = {
            "non_sensitive": "claude-3-opus",
            "sensitive": "llama3",
        }
        return mw


class TestPreprocessRequest:
    def test_no_pii_preserves_user_model(self):
        mock_svc = MagicMock()
        mock_svc.detect_pii.return_value = (False, [], 0.0)
        mock_svc.get_pii_summary.return_value = {}
        mw = _make_middleware(mock_svc)

        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "What is Python?"}],
        }
        processed, has_pii, model, details = mw.preprocess_request(request)
        assert has_pii is False
        assert model == "gpt-4"
        assert processed["model"] == "gpt-4"

    def test_pii_routes_to_local_model(self):
        mock_svc = MagicMock()
        mock_svc.detect_pii.return_value = (True, [{"entity_type": "EMAIL_ADDRESS"}], 0.9)
        mock_svc.get_pii_summary.return_value = {"EMAIL_ADDRESS": 1}
        mw = _make_middleware(mock_svc)

        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Email me at user@example.com"}],
        }
        processed, has_pii, model, details = mw.preprocess_request(request)
        assert has_pii is True
        assert model == "llama3"
        assert processed["model"] == "llama3"
        assert details["has_pii"] is True

    def test_fail_safe_on_detection_error(self):
        mock_svc = MagicMock()
        mock_svc.detect_pii.side_effect = RuntimeError("boom")
        mw = _make_middleware(mock_svc)

        request = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "hello"}],
        }
        processed, has_pii, model, details = mw.preprocess_request(request)
        assert has_pii is True  # fail-safe
        assert model == "llama3"

    def test_multimodal_content_extraction(self):
        mock_svc = MagicMock()
        mock_svc.detect_pii.return_value = (False, [], 0.0)
        mock_svc.get_pii_summary.return_value = {}
        mw = _make_middleware(mock_svc)

        request = {
            "model": "claude-3-opus",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image"},
                    {"type": "image_url", "image_url": {"url": "http://example.com/img.png"}},
                ],
            }],
        }
        mw.preprocess_request(request)
        # Verify the text was extracted and passed to detect_pii
        call_args = mock_svc.detect_pii.call_args[0][0]
        assert "Describe this image" in call_args

    def test_default_model_when_none_specified(self):
        mock_svc = MagicMock()
        mock_svc.detect_pii.return_value = (False, [], 0.0)
        mock_svc.get_pii_summary.return_value = {}
        mw = _make_middleware(mock_svc)

        request = {
            "messages": [{"role": "user", "content": "hi"}],
        }
        processed, has_pii, model, details = mw.preprocess_request(request)
        assert model == "claude-3-opus"  # default


class TestPostprocessResponse:
    def test_adds_pii_metadata(self):
        mock_svc = MagicMock()
        mw = _make_middleware(mock_svc)

        response = {"choices": [{"message": {"content": "hello"}}]}
        pii_details = {
            "has_pii": True,
            "risk_score": 0.85,
            "original_model": "gpt-4",
            "selected_model": "llama3",
        }
        result = mw.postprocess_response(response, pii_details)
        assert result["usage"]["pii_detected"] is True
        assert result["usage"]["pii_risk_score"] == 0.85
        assert result["usage"]["model_switched"] is True

    def test_no_pii_metadata(self):
        mock_svc = MagicMock()
        mw = _make_middleware(mock_svc)

        response = {"choices": [{"message": {"content": "hello"}}]}
        pii_details = {
            "has_pii": False,
            "risk_score": 0.0,
            "original_model": "gpt-4",
            "selected_model": "gpt-4",
        }
        result = mw.postprocess_response(response, pii_details)
        assert result["usage"]["pii_detected"] is False
        assert result["usage"]["model_switched"] is False

    def test_preserves_existing_usage(self):
        mock_svc = MagicMock()
        mw = _make_middleware(mock_svc)

        response = {"usage": {"prompt_tokens": 10}}
        pii_details = {"has_pii": False, "risk_score": 0.0}
        result = mw.postprocess_response(response, pii_details)
        assert result["usage"]["prompt_tokens"] == 10
        assert "pii_detected" in result["usage"]
