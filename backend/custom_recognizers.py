"""
Custom Recognizers for Domain-Specific PII Patterns
Additional recognizers for organization-specific PII patterns
"""

from presidio_analyzer import Pattern, PatternRecognizer
from typing import List, Optional

class CustomerIDRecognizer(PatternRecognizer):
    """
    Recognizer for customer IDs in format CUST-###### or cust-######
    """
    def __init__(self):
        patterns = [
            Pattern(
                name="customer_id",
                regex=r"\b[Cc][Uu][Ss][Tt]-\d{6}\b",
                score=0.8
            )
        ]
        super().__init__(
            supported_entity="CUSTOMER_ID",
            patterns=patterns,
            context=["customer", "client", "account"],
            supported_language="en"
        )

class EmployeeIDRecognizer(PatternRecognizer):
    """
    Recognizer for employee IDs in format EMP-##### or emp-#####
    """
    def __init__(self):
        patterns = [
            Pattern(
                name="employee_id",
                regex=r"\b[Ee][Mm][Pp]-\d{5}\b",
                score=0.8
            )
        ]
        super().__init__(
            supported_entity="EMPLOYEE_ID",
            patterns=patterns,
            context=["employee", "staff", "worker"],
            supported_language="en"
        )

class ProjectCodeRecognizer(PatternRecognizer):
    """
    Recognizer for project codes in format PROJ-XX-### or proj-xx-###
    """
    def __init__(self):
        patterns = [
            Pattern(
                name="project_code",
                regex=r"\b[Pp][Rr][Oo][Jj]-[A-Z]{2,4}-\d{3}\b",
                score=0.7
            )
        ]
        super().__init__(
            supported_entity="PROJECT_CODE",
            patterns=patterns,
            context=["project", "program", "initiative"],
            supported_language="en"
        )

class InternalHostnameRecognizer(PatternRecognizer):
    """
    Recognizer for internal hostnames ending in .internal, .corp, or .local
    """
    def __init__(self):
        patterns = [
            Pattern(
                name="internal_hostname",
                regex=r"\b[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\.(?:internal|corp|local)\b",
                score=0.6
            )
        ]
        super().__init__(
            supported_entity="INTERNAL_HOSTNAME",
            patterns=patterns,
            context=["server", "host", "machine", "instance"],
            supported_language="en"
        )

class FinancialAccountRecognizer(PatternRecognizer):
    """
    Recognizer for financial account numbers (generic patterns)
    """
    def __init__(self):
        patterns = [
            Pattern(
                name="financial_account",
                regex=r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
                score=0.7
            ),
            Pattern(
                name="financial_account_short",
                regex=r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b",
                score=0.6
            )
        ]
        super().__init__(
            supported_entity="FINANCIAL_ACCOUNT",
            patterns=patterns,
            context=["account", "bank", "credit", "debit", "financial"],
            supported_language="en"
        )

class MedicalTermRecognizer(PatternRecognizer):
    """
    Recognizer for medical terms and health information indicators
    """
    def __init__(self):
        # Common medical terms that might indicate health information
        medical_terms = [
            r"\bdiagnosis\b", r"\btreatment\b", r"\bmedication\b", r"\bprescription\b",
            r"\bsymptom\b", r"\bcondition\b", r"\bpatient\b", r"\bhospital\b",
            r"\bclinic\b", r"\bdoctor\b", r"\bnurse\b", r"\bmedical\b",
            r"\bhealth\b", r"\billness\b", r"\bdisease\b", r"\btherapy\b"
        ]

        patterns = [
            Pattern(
                name=f"medical_term_{i}",
                regex=term,
                score=0.6
            ) for i, term in enumerate(medical_terms)
        ]

        super().__init__(
            supported_entity="MEDICAL_TERM",
            patterns=patterns,
            context=["medical", "health", "patient", "doctor", "hospital"],
            supported_language="en"
        )

# Export all recognizers
CUSTOM_RECOGNIZERS = [
    CustomerIDRecognizer(),
    EmployeeIDRecognizer(),
    ProjectCodeRecognizer(),
    InternalHostnameRecognizer(),
    FinancialAccountRecognizer(),
    MedicalTermRecognizer()
]