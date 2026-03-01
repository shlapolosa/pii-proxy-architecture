"""Unit tests for notification_handler.py — NotificationHandler"""

import pytest
from notification_handler import NotificationHandler

pytestmark = pytest.mark.unit


class TestPIINotification:
    def setup_method(self):
        self.handler = NotificationHandler()

    def test_pii_detected_notification(self):
        details = {
            "has_pii": True,
            "risk_score": 0.85,
            "entities": {"EMAIL_ADDRESS": 1, "PHONE_NUMBER": 1},
            "original_model": "claude-3-opus",
            "selected_model": "llama3",
        }
        notif = self.handler.create_pii_notification(details)
        assert notif["type"] == "pii_detected"
        assert notif["level"] == "warning"
        assert "0.85" in notif["message"]
        assert notif["details"]["model_switched"] is True

    def test_no_pii_notification(self):
        details = {
            "has_pii": False,
            "selected_model": "claude-3-opus",
        }
        notif = self.handler.create_pii_notification(details)
        assert notif["type"] == "request_processed"
        assert notif["level"] == "info"

    def test_notification_stored_in_history(self):
        self.handler.create_pii_notification({"has_pii": False, "selected_model": "x"})
        assert len(self.handler.notifications) == 1


class TestModelSwitchNotification:
    def test_model_switch_notification(self):
        handler = NotificationHandler()
        notif = handler.create_model_switch_notification(
            "claude-3-opus", "llama3", "PII detected"
        )
        assert notif["type"] == "model_switched"
        assert "claude-3-opus" in notif["message"]
        assert "llama3" in notif["message"]


class TestErrorNotification:
    def test_error_notification(self):
        handler = NotificationHandler()
        notif = handler.create_error_notification("Service timeout", "route_to_local")
        assert notif["type"] == "error_occurred"
        assert notif["level"] == "error"
        assert "Service timeout" in notif["message"]


class TestNotificationHistory:
    def setup_method(self):
        self.handler = NotificationHandler()

    def test_get_recent_notifications(self):
        for i in range(15):
            self.handler.create_pii_notification({"has_pii": False, "selected_model": "x"})
        recent = self.handler.get_recent_notifications(limit=5)
        assert len(recent) == 5

    def test_get_recent_empty(self):
        assert self.handler.get_recent_notifications() == []

    def test_clear_notifications(self):
        self.handler.create_pii_notification({"has_pii": False, "selected_model": "x"})
        self.handler.clear_notifications()
        assert len(self.handler.notifications) == 0

    def test_format_notification_for_user(self):
        notif = {
            "level": "warning",
            "message": "PII detected",
            "timestamp": "2024-01-01T00:00:00",
        }
        formatted = self.handler.format_notification_for_user(notif)
        assert formatted.startswith("[WARNING]")
        assert "PII detected" in formatted
