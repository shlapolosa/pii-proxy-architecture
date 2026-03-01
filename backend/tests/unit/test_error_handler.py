"""Unit tests for error_handler.py — ErrorHandler + FallbackStrategy"""

import pytest
from error_handler import ErrorHandler, FallbackStrategy

pytestmark = pytest.mark.unit


class TestFallbackStrategies:
    def test_local_model_fallback_is_default(self):
        handler = ErrorHandler()
        result = handler.handle_pii_detection_error(ValueError("fail"), "some text")
        assert result["action"] == "route_to_local_model"
        assert result["model"] == "local-model"
        assert result["safe_to_process"] is True

    def test_block_fallback(self):
        handler = ErrorHandler(fallback_strategy=FallbackStrategy.BLOCK)
        result = handler.handle_pii_detection_error(ValueError("fail"), "text")
        assert result["action"] == "block"
        assert result["safe_to_process"] is False

    def test_sanitize_fallback(self):
        handler = ErrorHandler(fallback_strategy=FallbackStrategy.SANITIZE)
        result = handler.handle_pii_detection_error(ValueError("fail"), "email test@example.com")
        assert result["action"] == "sanitize"
        assert "[REDACTED_EMAIL]" in result["sanitized_text"]

    def test_allow_with_warning_fallback(self):
        handler = ErrorHandler(fallback_strategy=FallbackStrategy.ALLOW_WITH_WARNING)
        result = handler.handle_pii_detection_error(ValueError("fail"), "text")
        assert result["action"] == "allow_with_warning"
        assert "warning" in result
        assert result["safe_to_process"] is True


class TestErrorEscalation:
    def test_escalates_to_block_after_max_errors(self):
        handler = ErrorHandler(fallback_strategy=FallbackStrategy.LOCAL_MODEL)
        # Trigger max_errors + 1 errors
        for _ in range(11):
            handler.handle_pii_detection_error(ValueError("fail"), "text")
        # After escalation, strategy should be BLOCK
        assert handler.fallback_strategy == FallbackStrategy.BLOCK
        result = handler.handle_pii_detection_error(ValueError("fail"), "text")
        assert result["action"] == "block"

    def test_reset_error_count(self):
        handler = ErrorHandler()
        handler.error_count = 5
        handler.reset_error_count()
        assert handler.error_count == 0


class TestSimpleSanitization:
    def setup_method(self):
        self.handler = ErrorHandler()

    def test_sanitize_ssn(self):
        result = self.handler._simple_sanitization("My SSN is 123-45-6789")
        assert "[REDACTED_SSN]" in result
        assert "123-45-6789" not in result

    def test_sanitize_email(self):
        result = self.handler._simple_sanitization("Contact me at user@example.com")
        assert "[REDACTED_EMAIL]" in result

    def test_sanitize_phone(self):
        result = self.handler._simple_sanitization("Call me at (555)123-4567")
        assert "[REDACTED_PHONE]" in result

    def test_sanitize_credit_card(self):
        result = self.handler._simple_sanitization("Card: 4111-1111-1111-1111")
        assert "[REDACTED_CC]" in result

    def test_no_pii_unchanged(self):
        text = "Hello, how are you today?"
        result = self.handler._simple_sanitization(text)
        assert result == text


class TestWrapWithErrorHandling:
    def test_successful_function_passes_through(self):
        handler = ErrorHandler()
        wrapped = handler.wrap_with_error_handling(lambda x: x * 2)
        assert wrapped(5) == 10

    def test_failing_function_uses_fallback_strategy(self):
        handler = ErrorHandler()

        def fail(*args, **kwargs):
            raise ValueError("boom")

        wrapped = handler.wrap_with_error_handling(fail)
        result = wrapped("text")
        assert result["action"] == "route_to_local_model"

    def test_fallback_function_called_on_error(self):
        handler = ErrorHandler()

        def fail(*args, **kwargs):
            raise ValueError("boom")

        def fallback(*args, **kwargs):
            return "recovered"

        wrapped = handler.wrap_with_error_handling(fail, fallback_func=fallback)
        assert wrapped("text") == "recovered"
