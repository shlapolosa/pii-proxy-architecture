"""
Error Handler for PII Detection Service
Robust error handling and fallback strategies
"""

import logging
from typing import Dict, Any, Callable, Optional
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FallbackStrategy(Enum):
    """Fallback strategies when PII detection fails"""
    BLOCK = "block"
    SANITIZE = "sanitize"
    ALLOW_WITH_WARNING = "allow_with_warning"
    LOCAL_MODEL = "local_model"

class ErrorHandler:
    """
    Error handler with multiple fallback approaches
    """

    def __init__(self, fallback_strategy: FallbackStrategy = FallbackStrategy.LOCAL_MODEL):
        self.fallback_strategy = fallback_strategy
        self.error_count = 0
        self.max_errors = 10

    def handle_pii_detection_error(self, error: Exception, original_text: str) -> Dict[str, Any]:
        """
        Handle errors during PII detection

        Args:
            error (Exception): The error that occurred
            original_text (str): Original text being analyzed

        Returns:
            Dict[str, Any]: Error handling result
        """
        self.error_count += 1
        logger.error(f"PII detection error: {str(error)}")

        # If too many errors, escalate
        if self.error_count > self.max_errors:
            logger.critical("Too many PII detection errors, escalating")
            self.fallback_strategy = FallbackStrategy.BLOCK

        # Apply fallback strategy
        if self.fallback_strategy == FallbackStrategy.BLOCK:
            return self._handle_block_fallback(original_text, str(error))
        elif self.fallback_strategy == FallbackStrategy.SANITIZE:
            return self._handle_sanitize_fallback(original_text, str(error))
        elif self.fallback_strategy == FallbackStrategy.ALLOW_WITH_WARNING:
            return self._handle_allow_fallback(original_text, str(error))
        else:  # LOCAL_MODEL
            return self._handle_local_model_fallback(original_text, str(error))

    def _handle_block_fallback(self, text: str, error: str) -> Dict[str, Any]:
        """Block the request when PII detection fails"""
        logger.warning("Blocking request due to PII detection failure")
        return {
            "action": "block",
            "reason": f"PII detection failed: {error}",
            "safe_to_process": False,
            "error": error
        }

    def _handle_sanitize_fallback(self, text: str, error: str) -> Dict[str, Any]:
        """Attempt to sanitize content when PII detection fails"""
        logger.warning("Sanitizing content due to PII detection failure")
        # Simple sanitization - remove common PII patterns
        sanitized_text = self._simple_sanitization(text)
        return {
            "action": "sanitize",
            "reason": f"PII detection failed: {error}",
            "sanitized_text": sanitized_text,
            "safe_to_process": True,
            "error": error
        }

    def _handle_allow_fallback(self, text: str, error: str) -> Dict[str, Any]:
        """Allow processing with warning when PII detection fails"""
        logger.warning("Allowing request with warning due to PII detection failure")
        return {
            "action": "allow_with_warning",
            "reason": f"PII detection failed: {error}",
            "warning": "Content not checked for PII due to detection service error",
            "safe_to_process": True,
            "error": error
        }

    def _handle_local_model_fallback(self, text: str, error: str) -> Dict[str, Any]:
        """Route to local model when PII detection fails"""
        logger.warning("Routing to local model due to PII detection failure")
        return {
            "action": "route_to_local_model",
            "reason": f"PII detection failed: {error}",
            "model": "local-model",  # Default local model
            "safe_to_process": True,
            "error": error
        }

    def _simple_sanitization(self, text: str) -> str:
        """
        Simple sanitization for fallback when Presidio fails
        """
        import re

        # Remove common PII patterns
        # SSN pattern
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_SSN]', text)
        # Credit card pattern
        text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[REDACTED_CC]', text)
        # Email pattern
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]', text)
        # Phone number pattern
        text = re.sub(r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[REDACTED_PHONE]', text)

        return text

    def reset_error_count(self):
        """Reset error counter"""
        self.error_count = 0

    def wrap_with_error_handling(self, func: Callable, fallback_func: Optional[Callable] = None):
        """
        Decorator to wrap functions with error handling

        Args:
            func (Callable): Function to wrap
            fallback_func (Callable, optional): Fallback function to call on error

        Returns:
            Wrapped function with error handling
        """
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                if fallback_func:
                    try:
                        return fallback_func(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(f"Fallback function also failed: {str(fallback_error)}")
                        # Handle with default strategy
                        return self.handle_pii_detection_error(e, str(args))
                else:
                    # Handle with default strategy
                    return self.handle_pii_detection_error(e, str(args))

        return wrapper

# Global instance
error_handler = ErrorHandler()