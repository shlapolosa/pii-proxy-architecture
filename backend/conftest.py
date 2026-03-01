"""
Root conftest.py — provides fixtures that mock out spaCy/Presidio
so unit tests can import backend modules without heavy dependencies.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Ensure backend/ is on sys.path so tests can import modules directly
sys.path.insert(0, os.path.dirname(__file__))


def pytest_addoption(parser):
    parser.addoption(
        "--system",
        action="store_true",
        default=False,
        help="Run system-level smoke tests against live Docker stack",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--system"):
        skip_system = pytest.mark.skip(reason="need --system flag to run")
        for item in items:
            if "system" in item.keywords:
                item.add_marker(skip_system)


# ---------------------------------------------------------------------------
# Session-scoped mocks for Presidio engines (used by unit tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def mock_analyzer():
    analyzer = MagicMock()
    analyzer.analyze.return_value = []
    return analyzer


@pytest.fixture(scope="session")
def mock_anonymizer():
    return MagicMock()


# ---------------------------------------------------------------------------
# Function-scoped PII service fixtures that patch presidio_config globals
# ---------------------------------------------------------------------------

@pytest.fixture
def pii_service_no_pii(mock_analyzer, mock_anonymizer):
    """Returns a PIIDetectionService whose analyzer always finds no PII."""
    mock_analyzer.analyze.return_value = []

    with patch.dict("sys.modules", {
        "presidio_config": MagicMock(
            analyzer_engine=mock_analyzer,
            anonymizer_engine=mock_anonymizer,
        ),
    }):
        # Force re-import so module picks up the mock
        if "pii_detection_service" in sys.modules:
            del sys.modules["pii_detection_service"]
        from pii_detection_service import PIIDetectionService

        svc = PIIDetectionService.__new__(PIIDetectionService)
        svc.analyzer = mock_analyzer
        svc.anonymizer = mock_anonymizer
        svc.sensitivity_threshold = 0.5
        yield svc


@pytest.fixture
def pii_service_with_pii(mock_analyzer, mock_anonymizer):
    """Returns a PIIDetectionService whose analyzer always finds PII."""
    fake_result = MagicMock()
    fake_result.entity_type = "EMAIL_ADDRESS"
    fake_result.start = 10
    fake_result.end = 30
    fake_result.score = 0.95
    mock_analyzer.analyze.return_value = [fake_result]

    with patch.dict("sys.modules", {
        "presidio_config": MagicMock(
            analyzer_engine=mock_analyzer,
            anonymizer_engine=mock_anonymizer,
        ),
    }):
        if "pii_detection_service" in sys.modules:
            del sys.modules["pii_detection_service"]
        from pii_detection_service import PIIDetectionService

        svc = PIIDetectionService.__new__(PIIDetectionService)
        svc.analyzer = mock_analyzer
        svc.anonymizer = mock_anonymizer
        svc.sensitivity_threshold = 0.5
        yield svc
