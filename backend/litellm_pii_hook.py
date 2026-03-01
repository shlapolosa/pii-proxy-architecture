"""
LiteLLM PII Routing Hook

CustomLogger that intercepts LLM requests, scans for PII using Presidio,
and reroutes sensitive requests to a local model.
"""

import json
import logging
import os
from datetime import datetime, timezone

from litellm.integrations.custom_logger import CustomLogger

from pii_detection_service import pii_service

logger = logging.getLogger(__name__)

SENSITIVE_MODEL = "local-model"
PII_REROUTE_ENABLED = os.getenv("PII_REROUTE_ENABLED", "true").lower() == "true"
PII_EVENT_LOG = "/app/pii-events.jsonl"

# Entity types that trigger rerouting — actual sensitive PII only
SENSITIVE_ENTITY_TYPES = {
    "EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD",
    "US_BANK_NUMBER", "IBAN_CODE", "IP_ADDRESS", "US_PASSPORT",
    "US_DRIVER_LICENSE", "CRYPTO", "MEDICAL_LICENSE",
    "CUSTOMER_ID", "EMPLOYEE_ID",  # custom recognizers
}


class PIIRoutingHook(CustomLogger):
    """
    LiteLLM hook that scans request messages for PII and reroutes
    to a local model when PII is detected.
    """

    def __init__(self):
        super().__init__()
        self.pii_service = pii_service

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        """
        Called before each LLM API call. Scans messages for PII
        and mutates data["model"] to reroute if needed.
        """
        if call_type not in ("completion", "acompletion", "text_completion", "anthropic_messages"):
            return data

        try:
            model = data.get("model", "unknown")
            messages = data.get("messages", [])
            combined_content = self._extract_text(messages)
            content_preview = combined_content[:80] + "..." if len(combined_content) > 80 else combined_content

            logger.info(
                f"[request] model={model} call_type={call_type} "
                f"content_len={len(combined_content)} preview=\"{content_preview}\""
            )

            if not combined_content.strip():
                return data

            has_pii, pii_entities, risk_score = self.pii_service.detect_pii(combined_content)

            # Filter to only sensitive entity types (ignore PERSON, ORG, DATE, etc.)
            sensitive_entities = [
                e for e in pii_entities
                if e.get("entity_type") in SENSITIVE_ENTITY_TYPES
            ]
            has_sensitive_pii = len(sensitive_entities) > 0

            if has_sensitive_pii:
                original_model = model
                if PII_REROUTE_ENABLED:
                    data["model"] = SENSITIVE_MODEL
                    logger.info(
                        f"[PII REROUTE] risk={risk_score:.2f} "
                        f"entities={self.pii_service.get_pii_summary(sensitive_entities)} "
                        f"route: {original_model} -> {SENSITIVE_MODEL}"
                    )
                else:
                    logger.info(
                        f"[PII PASSTHROUGH] risk={risk_score:.2f} "
                        f"entities={self.pii_service.get_pii_summary(sensitive_entities)} "
                        f"reroute disabled, staying on {model}"
                    )
            else:
                if has_pii:
                    logger.info(
                        f"[PASS] low-risk entities only "
                        f"({self.pii_service.get_pii_summary(pii_entities)}), "
                        f"passing through to {model}"
                    )
                else:
                    logger.info(f"[CLEAN] no PII detected, passing through to {model}")
            has_pii = has_sensitive_pii

            # Attach metadata for post-call hook
            metadata = data.get("metadata", {})
            metadata["pii_detected"] = has_pii
            metadata["pii_risk_score"] = risk_score
            if has_pii:
                metadata["pii_original_model"] = original_model
                metadata["pii_entities"] = self.pii_service.get_pii_summary(pii_entities)
            data["metadata"] = metadata

            # Write PII event to log file for status line consumption
            # Skip suggestion mode requests — they overwrite real user events
            if not combined_content.startswith("[SUGGESTION MODE:"):
                event = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "pii_detected": has_pii,
                    "original_model": original_model if has_pii else None,
                    "routed_model": data["model"],
                    "risk_score": risk_score,
                    "entities": metadata.get("pii_entities"),
                }
                try:
                    with open(PII_EVENT_LOG, "a") as f:
                        f.write(json.dumps(event) + "\n")
                except OSError as log_err:
                    logger.warning(f"Could not write PII event log: {log_err}")

        except Exception as e:
            logger.error(f"PII detection error, fail-safe routing to local model: {e}")
            data["model"] = SENSITIVE_MODEL
            metadata = data.get("metadata", {})
            metadata["pii_detected"] = True
            metadata["pii_error"] = str(e)
            data["metadata"] = metadata

        return data

    async def async_post_call_success_hook(self, data, user_api_key_dict, response):
        """Inject PII metadata into the response."""
        try:
            metadata = data.get("metadata", {})
            if metadata.get("pii_detected") is not None:
                if hasattr(response, "usage") and response.usage is not None:
                    response.usage.pii_detected = metadata.get("pii_detected", False)
                    response.usage.pii_risk_score = metadata.get("pii_risk_score", 0.0)
        except Exception as e:
            logger.error(f"Error in post-call PII metadata injection: {e}")

    def _extract_text(self, messages):
        """Extract text from the last user message only."""
        # Scan only the latest user message — prior history was already scanned
        for message in reversed(messages):
            if not isinstance(message, dict):
                continue
            if message.get("role") != "user":
                continue
            content = message.get("content", "")
            texts = []
            if isinstance(content, str):
                texts.append(content)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        texts.append(item.get("text", ""))
            cleaned = self._strip_tags(" ".join(texts))
            return cleaned
        return ""

    @staticmethod
    def _strip_tags(text):
        """Remove all XML-style tagged blocks (framework/tool metadata)."""
        import re
        # Remove all <tag>...</tag> blocks (framework injected content)
        cleaned = re.sub(r"<[a-zA-Z_-]+>.*?</[a-zA-Z_-]+>", "", text, flags=re.DOTALL)
        # Remove any remaining self-closing or orphan tags
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        return cleaned


# Module-level instance — LiteLLM picks this up via config.yaml callbacks
proxy_handler_instance = PIIRoutingHook()
