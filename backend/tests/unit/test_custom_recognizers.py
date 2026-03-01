"""Unit tests for custom_recognizers.py — regex pattern recognizers.

These tests instantiate the recognizers directly and test their regex
patterns without needing spaCy or a full Presidio analyzer.
"""

import pytest
from custom_recognizers import (
    CustomerIDRecognizer,
    EmployeeIDRecognizer,
    ProjectCodeRecognizer,
    InternalHostnameRecognizer,
    FinancialAccountRecognizer,
    MedicalTermRecognizer,
    CUSTOM_RECOGNIZERS,
)

pytestmark = pytest.mark.unit


class TestCustomerIDRecognizer:
    def setup_method(self):
        self.recognizer = CustomerIDRecognizer()

    def test_supported_entity(self):
        assert self.recognizer.supported_entities == ["CUSTOMER_ID"]

    def test_pattern_matches_uppercase(self):
        patterns = self.recognizer.patterns
        assert any(p.regex for p in patterns)
        import re
        regex = patterns[0].regex
        assert re.search(regex, "CUST-123456")

    def test_pattern_matches_mixed_case(self):
        import re
        regex = self.recognizer.patterns[0].regex
        assert re.search(regex, "Cust-123456")

    def test_pattern_rejects_wrong_length(self):
        import re
        regex = self.recognizer.patterns[0].regex
        assert not re.search(regex, "CUST-12345")  # 5 digits
        assert not re.search(regex, "CUST-1234567")  # 7 digits


class TestEmployeeIDRecognizer:
    def setup_method(self):
        self.recognizer = EmployeeIDRecognizer()

    def test_supported_entity(self):
        assert self.recognizer.supported_entities == ["EMPLOYEE_ID"]

    def test_pattern_matches(self):
        import re
        regex = self.recognizer.patterns[0].regex
        assert re.search(regex, "EMP-12345")
        assert re.search(regex, "emp-12345")

    def test_pattern_rejects_wrong_format(self):
        import re
        regex = self.recognizer.patterns[0].regex
        assert not re.search(regex, "EMP-1234")  # 4 digits
        assert not re.search(regex, "EMPLOYEE-12345")  # wrong prefix


class TestProjectCodeRecognizer:
    def setup_method(self):
        self.recognizer = ProjectCodeRecognizer()

    def test_pattern_matches(self):
        import re
        regex = self.recognizer.patterns[0].regex
        assert re.search(regex, "PROJ-AB-123")
        assert re.search(regex, "PROJ-ABCD-123")

    def test_pattern_rejects_lowercase_suffix(self):
        import re
        regex = self.recognizer.patterns[0].regex
        # The regex requires uppercase letters after PROJ-
        assert not re.search(regex, "PROJ-ab-123")


class TestInternalHostnameRecognizer:
    def setup_method(self):
        self.recognizer = InternalHostnameRecognizer()

    def test_pattern_matches_internal(self):
        import re
        regex = self.recognizer.patterns[0].regex
        assert re.search(regex, "server-01.internal")
        assert re.search(regex, "db.corp")
        assert re.search(regex, "cache.local")

    def test_pattern_rejects_public_domains(self):
        import re
        regex = self.recognizer.patterns[0].regex
        assert not re.search(regex, "server.example.com")


class TestFinancialAccountRecognizer:
    def setup_method(self):
        self.recognizer = FinancialAccountRecognizer()

    def test_long_pattern_matches(self):
        import re
        regex = self.recognizer.patterns[0].regex
        assert re.search(regex, "1234-5678-9012-3456")
        assert re.search(regex, "1234 5678 9012 3456")

    def test_short_pattern_matches(self):
        import re
        regex = self.recognizer.patterns[1].regex
        assert re.search(regex, "123-456-789")


class TestMedicalTermRecognizer:
    def setup_method(self):
        self.recognizer = MedicalTermRecognizer()

    def test_has_multiple_patterns(self):
        assert len(self.recognizer.patterns) == 16

    def test_patterns_match_medical_terms(self):
        import re
        terms_to_check = ["diagnosis", "treatment", "medication", "patient", "hospital"]
        all_regexes = [p.regex for p in self.recognizer.patterns]
        for term in terms_to_check:
            assert any(re.search(r, term) for r in all_regexes), f"No pattern matched '{term}'"


class TestCustomRecognizersList:
    def test_all_six_recognizers_exported(self):
        assert len(CUSTOM_RECOGNIZERS) == 6

    def test_recognizer_types(self):
        entity_types = set()
        for r in CUSTOM_RECOGNIZERS:
            entity_types.update(r.supported_entities)
        expected = {
            "CUSTOMER_ID", "EMPLOYEE_ID", "PROJECT_CODE",
            "INTERNAL_HOSTNAME", "FINANCIAL_ACCOUNT", "MEDICAL_TERM",
        }
        assert entity_types == expected
