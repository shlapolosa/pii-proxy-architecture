"""Unit tests for pii_detection_service.py — PIIDetectionService

Uses conftest fixtures to mock Presidio, so no spaCy model needed.
"""

import pytest
from unittest.mock import MagicMock

pytestmark = pytest.mark.unit


class TestDetectPII:
    def test_no_pii_detected(self, pii_service_no_pii):
        has_pii, entities, score = pii_service_no_pii.detect_pii("Hello, world!")
        assert has_pii is False
        assert entities == []
        assert score == 0.0

    def test_pii_detected(self, pii_service_with_pii):
        text = "Contact: user@example.com for details"
        has_pii, entities, score = pii_service_with_pii.detect_pii(text)
        assert has_pii is True
        assert len(entities) == 1
        assert entities[0]["entity_type"] == "EMAIL_ADDRESS"
        assert score > 0

    def test_empty_text_returns_no_pii(self, pii_service_no_pii):
        has_pii, entities, score = pii_service_no_pii.detect_pii("")
        assert has_pii is False

    def test_none_text_returns_no_pii(self, pii_service_no_pii):
        has_pii, entities, score = pii_service_no_pii.detect_pii(None)
        assert has_pii is False

    def test_non_string_returns_no_pii(self, pii_service_no_pii):
        has_pii, entities, score = pii_service_no_pii.detect_pii(12345)
        assert has_pii is False

    def test_analyzer_exception_returns_fail_safe(self, pii_service_no_pii):
        pii_service_no_pii.analyzer.analyze.side_effect = RuntimeError("engine crash")
        has_pii, entities, score = pii_service_no_pii.detect_pii("some text")
        assert has_pii is True  # fail-safe
        assert score == 1.0
        # Reset
        pii_service_no_pii.analyzer.analyze.side_effect = None


class TestSanitizeContent:
    def test_sanitize_with_no_results(self, pii_service_no_pii):
        assert pii_service_no_pii.sanitize_content("hello", []) == "hello"

    def test_sanitize_with_empty_text(self, pii_service_no_pii):
        assert pii_service_no_pii.sanitize_content("", [{"entity_type": "X"}]) == ""

    def test_sanitize_calls_anonymizer(self, pii_service_no_pii):
        mock_result = MagicMock()
        mock_result.text = "Contact: <EMAIL_ADDRESS> for details"
        pii_service_no_pii.anonymizer.anonymize.return_value = mock_result

        pii_results = [{
            "entity_type": "EMAIL_ADDRESS",
            "start": 9,
            "end": 26,
            "score": 0.95,
        }]
        result = pii_service_no_pii.sanitize_content("Contact: user@example.com for details", pii_results)
        assert "<EMAIL_ADDRESS>" in result

    def test_sanitize_handles_exception(self, pii_service_no_pii):
        pii_service_no_pii.anonymizer.anonymize.side_effect = RuntimeError("fail")
        pii_results = [{
            "entity_type": "EMAIL_ADDRESS",
            "start": 0,
            "end": 5,
            "score": 0.9,
        }]
        # Should return original text on error
        result = pii_service_no_pii.sanitize_content("hello", pii_results)
        assert result == "hello"
        pii_service_no_pii.anonymizer.anonymize.side_effect = None


class TestGetPIISummary:
    def test_summary_counts_entity_types(self, pii_service_no_pii):
        entities = [
            {"entity_type": "EMAIL_ADDRESS"},
            {"entity_type": "PHONE_NUMBER"},
            {"entity_type": "EMAIL_ADDRESS"},
        ]
        summary = pii_service_no_pii.get_pii_summary(entities)
        assert summary == {"EMAIL_ADDRESS": 2, "PHONE_NUMBER": 1}

    def test_summary_empty_list(self, pii_service_no_pii):
        assert pii_service_no_pii.get_pii_summary([]) == {}
