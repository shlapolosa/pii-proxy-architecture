#!/usr/bin/env python3

"""
Test script for PII detection functionality
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from pii_detection_service import PIIDetectionService

def test_pii_detection():
    """Test the PII detection service with various inputs"""

    # Initialize the PII detection service
    pii_service = PIIDetectionService()

    # Test cases with different types of PII
    test_cases = [
        # No PII
        ("Hello, how are you today?", False),

        # Basic PII
        ("My email is john.doe@example.com", True),
        ("Call me at 555-123-4567", True),
        ("My SSN is 123-45-6789", True),

        # Extended PII
        ("My name is John Smith", True),  # Names can be PII
        ("I live at 123 Main Street", True),  # Addresses can be PII
        ("My credit card is 4111-1111-1111-1111", True),

        # Domain-specific PII
        ("Customer ID: CUST-123456", True),
        ("Employee ID: EMP-98765", True),
        ("Project code: PROJ-AB-001", True),
        ("Internal server: db01.internal.company.com", True),

        # Medical terms
        ("Patient was diagnosed with diabetes", True),
        ("Prescription for medication XYZ", True),

        # Financial information
        ("Bank account: 123456789", True),
    ]

    print("Testing PII Detection Service")
    print("=" * 40)

    passed = 0
    failed = 0

    for i, (text, should_have_pii) in enumerate(test_cases, 1):
        try:
            has_pii, pii_entities, risk_score = pii_service.detect_pii(text)

            # Check if result matches expectation
            if has_pii == should_have_pii:
                status = "PASS"
                passed += 1
            else:
                status = "FAIL"
                failed += 1

            print(f"Test {i:2d}: {status}")
            print(f"  Input: {text}")
            print(f"  Expected PII: {should_have_pii}, Detected PII: {has_pii}")
            if has_pii:
                print(f"  Entities: {len(pii_entities)}, Risk Score: {risk_score:.2f}")
            print()

        except Exception as e:
            print(f"Test {i:2d}: ERROR")
            print(f"  Input: {text}")
            print(f"  Error: {str(e)}")
            print()
            failed += 1

    print("=" * 40)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("All tests passed! 🎉")
        return True
    else:
        print(f"{failed} tests failed. Please review.")
        return False

if __name__ == "__main__":
    success = test_pii_detection()
    sys.exit(0 if success else 1)