"""
PII Detection Service
Main service for detecting and handling PII in requests
"""

from presidio_config import analyzer_engine, anonymizer_engine
from presidio_analyzer import RecognizerResult
from typing import List, Dict, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PIIDetectionService:
    """
    Service for detecting PII in text content with extended detection capabilities
    """

    def __init__(self):
        self.analyzer = analyzer_engine
        self.anonymizer = anonymizer_engine
        self.sensitivity_threshold = 0.5

    def detect_pii(self, text: str) -> Tuple[bool, List[Dict], float]:
        """
        Detect PII in text content

        Args:
            text (str): Text to analyze for PII

        Returns:
            Tuple[bool, List[Dict], float]: (has_pii, pii_entities, risk_score)
                - has_pii: Boolean indicating if PII was detected
                - pii_entities: List of detected PII entities with details
                - risk_score: Overall risk score (0.0 to 1.0)
        """
        if not text or not isinstance(text, str):
            return False, [], 0.0

        try:
            # Analyze text for PII
            results = self.analyzer.analyze(
                text=text,
                language="en",
                score_threshold=self.sensitivity_threshold
            )

            # Convert results to dictionary format
            pii_entities = []
            total_score = 0.0
            entity_count = 0

            for result in results:
                entity_info = {
                    "entity_type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "score": result.score,
                    "text": text[result.start:result.end]
                }
                pii_entities.append(entity_info)

                # Calculate weighted risk score
                total_score += result.score
                entity_count += 1

            # Calculate average risk score
            risk_score = total_score / entity_count if entity_count > 0 else 0.0

            # Determine if PII was detected based on presence of results
            has_pii = len(results) > 0

            if has_pii:
                logger.info(f"PII detected: {len(results)} entities found with risk score {risk_score:.2f}")

            return has_pii, pii_entities, risk_score

        except Exception as e:
            logger.error(f"Error during PII detection: {str(e)}")
            # Fail-safe: if detection fails, assume PII is present for safety
            return True, [{"error": "Detection failed"}], 1.0

    def sanitize_content(self, text: str, pii_results: List[Dict]) -> str:
        """
        Sanitize content by removing or replacing PII

        Args:
            text (str): Original text
            pii_results (List[Dict]): PII detection results

        Returns:
            str: Sanitized text
        """
        if not text or not pii_results:
            return text

        try:
            # Convert to Presidio format for anonymization
            recognizer_results = []
            for entity in pii_results:
                if "start" in entity and "end" in entity and "entity_type" in entity:
                    recognizer_result = RecognizerResult(
                        entity_type=entity["entity_type"],
                        start=entity["start"],
                        end=entity["end"],
                        score=entity.get("score", 0.5)
                    )
                    recognizer_results.append(recognizer_result)

            if recognizer_results:
                # Anonymize the text
                anonymized_result = self.anonymizer.anonymize(
                    text=text,
                    analyzer_results=recognizer_results
                )
                return anonymized_result.text

            return text

        except Exception as e:
            logger.error(f"Error during content sanitization: {str(e)}")
            # Return original text if sanitization fails
            return text

    def get_pii_summary(self, pii_entities: List[Dict]) -> Dict:
        """
        Generate a summary of detected PII entities

        Args:
            pii_entities (List[Dict]): List of detected PII entities

        Returns:
            Dict: Summary of PII types and counts
        """
        summary = {}
        for entity in pii_entities:
            entity_type = entity.get("entity_type", "UNKNOWN")
            if entity_type in summary:
                summary[entity_type] += 1
            else:
                summary[entity_type] = 1

        return summary

# Global instance for reuse
pii_service = PIIDetectionService()