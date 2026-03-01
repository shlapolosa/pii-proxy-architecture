"""
Notification Handler for PII Detection Service
Handles user notifications for PII detection and model switching
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationHandler:
    """
    Notification handler for PII detection alerts and model switching notifications
    """

    def __init__(self):
        self.notifications = []

    def create_pii_notification(self, pii_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create notification for PII detection

        Args:
            pii_details (Dict[str, Any]): Details about detected PII

        Returns:
            Dict[str, Any]: Notification object
        """
        has_pii = pii_details.get("has_pii", False)
        risk_score = pii_details.get("risk_score", 0.0)
        entities = pii_details.get("entities", {})
        original_model = pii_details.get("original_model", "unknown")
        selected_model = pii_details.get("selected_model", "unknown")

        if has_pii:
            message = f"PII detected in your request (risk score: {risk_score:.2f}). "
            message += f"For your protection, we've automatically switched from {original_model} to {selected_model}. "
            message += f"Detected entities: {', '.join([f'{k}: {v}' for k, v in entities.items()])}"

            notification = {
                "type": "pii_detected",
                "level": "warning",
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "risk_score": risk_score,
                    "entities": entities,
                    "original_model": original_model,
                    "selected_model": selected_model,
                    "model_switched": original_model != selected_model
                }
            }
        else:
            notification = {
                "type": "request_processed",
                "level": "info",
                "message": f"Request processed using {selected_model}",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "model_used": selected_model
                }
            }

        self.notifications.append(notification)
        logger.info(f"Created notification: {notification['message']}")
        return notification

    def create_model_switch_notification(self, original_model: str, selected_model: str, reason: str) -> Dict[str, Any]:
        """
        Create notification for model switching

        Args:
            original_model (str): Original model requested
            selected_model (str): Model that was actually used
            reason (str): Reason for switching

        Returns:
            Dict[str, Any]: Notification object
        """
        message = f"Model automatically switched from {original_model} to {selected_model}: {reason}"

        notification = {
            "type": "model_switched",
            "level": "info",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": {
                "original_model": original_model,
                "selected_model": selected_model,
                "reason": reason
            }
        }

        self.notifications.append(notification)
        logger.info(f"Created model switch notification: {message}")
        return notification

    def create_error_notification(self, error: str, fallback_action: str) -> Dict[str, Any]:
        """
        Create notification for errors and fallback actions

        Args:
            error (str): Error description
            fallback_action (str): Action taken as fallback

        Returns:
            Dict[str, Any]: Notification object
        """
        message = f"Error occurred: {error}. Fallback action taken: {fallback_action}"

        notification = {
            "type": "error_occurred",
            "level": "error",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": {
                "error": error,
                "fallback_action": fallback_action
            }
        }

        self.notifications.append(notification)
        logger.error(f"Created error notification: {message}")
        return notification

    def get_recent_notifications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent notifications

        Args:
            limit (int): Maximum number of notifications to return

        Returns:
            List[Dict[str, Any]]: Recent notifications
        """
        return self.notifications[-limit:] if self.notifications else []

    def clear_notifications(self):
        """Clear all notifications"""
        self.notifications.clear()
        logger.info("Cleared all notifications")

    def format_notification_for_user(self, notification: Dict[str, Any]) -> str:
        """
        Format notification for user display

        Args:
            notification (Dict[str, Any]): Notification to format

        Returns:
            str: Formatted notification string
        """
        level = notification.get("level", "info").upper()
        message = notification.get("message", "")
        timestamp = notification.get("timestamp", "")

        return f"[{level}] {timestamp}: {message}"

# Global instance
notification_handler = NotificationHandler()