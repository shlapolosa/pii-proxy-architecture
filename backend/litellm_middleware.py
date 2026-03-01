"""
LiteLLM Middleware for PII Detection and Model Routing
Middleware that intercepts requests, detects PII, and routes to appropriate models
"""

from pii_detection_service import pii_service
from typing import Dict, Any, Tuple, Optional
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PIIMiddleware:
    """
    Middleware for PII detection and intelligent model routing
    """

    def __init__(self):
        self.pii_service = pii_service
        # Default models for different sensitivity levels
        self.models = {
            "non_sensitive": "claude-3-opus",  # Default cloud model for non-sensitive content
            "sensitive": "local-model"              # Default local model for sensitive content
        }

    def preprocess_request(self, request_body: Dict[str, Any]) -> Tuple[Dict[str, Any], bool, str, Dict]:
        """
        Preprocess incoming request to detect PII and determine routing

        Args:
            request_body (Dict[str, Any]): Original request body

        Returns:
            Tuple[Dict[str, Any], bool, str, Dict]: (processed_request, has_pii, selected_model, pii_details)
        """
        try:
            # Extract message content from request
            messages = request_body.get("messages", [])
            user_preference_model = request_body.get("model", "claude-3-opus")

            # Combine all message content for PII detection
            combined_content = ""
            for message in messages:
                if isinstance(message, dict) and "content" in message:
                    content = message["content"]
                    if isinstance(content, str):
                        combined_content += content + " "
                    elif isinstance(content, list):
                        # Handle multi-modal content
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                combined_content += item.get("text", "") + " "

            # Detect PII in combined content
            has_pii, pii_entities, risk_score = self.pii_service.detect_pii(combined_content)

            # Determine which model to route to
            if has_pii:
                # Route to local model for sensitive content
                selected_model = self.models["sensitive"]
                logger.info(f"PII detected (risk: {risk_score:.2f}), routing to local model: {selected_model}")
            else:
                # Use user's preferred model for non-sensitive content
                selected_model = user_preference_model
                logger.info(f"No PII detected, using user preferred model: {selected_model}")

            # Update request with selected model
            processed_request = request_body.copy()
            processed_request["model"] = selected_model

            # Prepare PII details for notification
            pii_details = {
                "has_pii": has_pii,
                "risk_score": risk_score,
                "entities": self.pii_service.get_pii_summary(pii_entities) if has_pii else {},
                "original_model": user_preference_model,
                "selected_model": selected_model
            }

            return processed_request, has_pii, selected_model, pii_details

        except Exception as e:
            logger.error(f"Error in preprocessing request: {str(e)}")
            # Fail-safe: route to local model if processing fails
            processed_request = request_body.copy()
            processed_request["model"] = self.models["sensitive"]
            return processed_request, True, self.models["sensitive"], {
                "has_pii": True,
                "error": str(e),
                "selected_model": self.models["sensitive"]
            }

    def postprocess_response(self, response: Dict[str, Any], pii_details: Dict) -> Dict[str, Any]:
        """
        Postprocess response to add PII-related metadata

        Args:
            response (Dict[str, Any]): Original response
            pii_details (Dict): PII detection details

        Returns:
            Dict[str, Any]: Response with added metadata
        """
        try:
            # Add PII information to response metadata
            response_copy = response.copy()

            if "usage" not in response_copy:
                response_copy["usage"] = {}

            response_copy["usage"]["pii_detected"] = pii_details.get("has_pii", False)
            response_copy["usage"]["pii_risk_score"] = pii_details.get("risk_score", 0.0)
            response_copy["usage"]["model_switched"] = (
                pii_details.get("original_model") != pii_details.get("selected_model")
            ) if pii_details.get("original_model") and pii_details.get("selected_model") else False

            return response_copy

        except Exception as e:
            logger.error(f"Error in postprocessing response: {str(e)}")
            # Return original response if postprocessing fails
            return response

# Global instance for middleware
pii_middleware = PIIMiddleware()