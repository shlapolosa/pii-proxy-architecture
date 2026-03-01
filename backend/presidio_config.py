"""
PII Detection Configuration using Microsoft Presidio
This module sets up the analyzer and anonymizer for detecting and handling PII.
"""

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer import Pattern, PatternRecognizer, RecognizerResult
from typing import List, Optional
import re

# Import custom recognizers
from custom_recognizers import CUSTOM_RECOGNIZERS

def create_analyzer() -> AnalyzerEngine:
    """
    Create and configure the Presidio Analyzer Engine with extended PII detection
    """
    # Configure NLP engine
    nlp_configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}]
    }

    # Create NLP engine
    provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
    nlp_engine = provider.create_engine()

    # Create analyzer with default recognizers plus custom ones
    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        default_score_threshold=0.5
    )

    # Register all custom recognizers
    for recognizer in CUSTOM_RECOGNIZERS:
        analyzer.registry.add_recognizer(recognizer)

    return analyzer

def create_anonymizer() -> AnonymizerEngine:
    """
    Create and configure the Presidio Anonymizer Engine
    """
    return AnonymizerEngine()

# Pre-create instances for performance
analyzer_engine = create_analyzer()
anonymizer_engine = create_anonymizer()