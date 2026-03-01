"""Integration tests for PII detection with real Presidio/spaCy.

Requires: ./install.sh (spaCy en_core_web_lg model)
Run: pytest -m integration
"""

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def pii_service():
    """Create a real PIIDetectionService with actual Presidio engine."""
    from pii_detection_service import PIIDetectionService
    return PIIDetectionService()


class TestBasicPIIDetection:
    def test_no_pii_in_clean_text(self, pii_service):
        has_pii, entities, score = pii_service.detect_pii(
            "What is the capital of France?"
        )
        assert has_pii is False
        assert entities == []

    def test_detects_email(self, pii_service):
        has_pii, entities, score = pii_service.detect_pii(
            "Contact me at john.doe@example.com"
        )
        assert has_pii is True
        types = [e["entity_type"] for e in entities]
        assert "EMAIL_ADDRESS" in types

    def test_detects_phone_number(self, pii_service):
        has_pii, entities, score = pii_service.detect_pii(
            "Call me at 555-123-4567"
        )
        assert has_pii is True
        types = [e["entity_type"] for e in entities]
        assert "PHONE_NUMBER" in types

    def test_detects_ssn(self, pii_service):
        has_pii, entities, score = pii_service.detect_pii(
            "My social security number is 123-45-6789"
        )
        assert has_pii is True

    def test_detects_credit_card(self, pii_service):
        has_pii, entities, score = pii_service.detect_pii(
            "My card number is 4111 1111 1111 1111"
        )
        assert has_pii is True


class TestCustomRecognizerIntegration:
    def test_detects_customer_id(self, pii_service):
        has_pii, entities, score = pii_service.detect_pii(
            "Customer account CUST-123456 needs attention"
        )
        assert has_pii is True
        types = [e["entity_type"] for e in entities]
        assert "CUSTOMER_ID" in types

    def test_detects_employee_id(self, pii_service):
        has_pii, entities, score = pii_service.detect_pii(
            "Employee EMP-12345 reported the issue"
        )
        assert has_pii is True
        types = [e["entity_type"] for e in entities]
        assert "EMPLOYEE_ID" in types

    def test_detects_project_code(self, pii_service):
        has_pii, entities, score = pii_service.detect_pii(
            "This relates to project PROJ-AB-123"
        )
        assert has_pii is True
        types = [e["entity_type"] for e in entities]
        assert "PROJECT_CODE" in types

    def test_detects_internal_hostname(self, pii_service):
        has_pii, entities, score = pii_service.detect_pii(
            "The server db-primary.internal is down"
        )
        assert has_pii is True
        types = [e["entity_type"] for e in entities]
        assert "INTERNAL_HOSTNAME" in types


class TestSanitization:
    def test_sanitize_email(self, pii_service):
        text = "Contact john.doe@example.com for details"
        has_pii, entities, score = pii_service.detect_pii(text)
        sanitized = pii_service.sanitize_content(text, entities)
        assert "john.doe@example.com" not in sanitized

    def test_sanitize_preserves_clean_text(self, pii_service):
        text = "Hello world"
        sanitized = pii_service.sanitize_content(text, [])
        assert sanitized == text


class TestRiskScoring:
    def test_risk_score_in_valid_range(self, pii_service):
        _, _, score = pii_service.detect_pii("Email: test@example.com phone: 555-123-4567")
        assert 0.0 <= score <= 1.0

    def test_clean_text_zero_risk(self, pii_service):
        _, _, score = pii_service.detect_pii("Hello world")
        assert score == 0.0
