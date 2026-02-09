"""Unit tests for PhoneDetector.

This module tests the phone number detection functionality, including:
- Detection of various phone number formats
- Format preservation information capture
- Non-detection of invalid phone numbers
- Field-name-agnostic detection
"""

import pytest

from data_sanitizer.detectors.phone_detector import PhoneDetector
from data_sanitizer.models import PIIType


class TestPhoneDetector:
    """Test suite for PhoneDetector."""

    @pytest.fixture
    def detector(self):
        """Create a PhoneDetector instance for testing."""
        return PhoneDetector()

    def test_detect_international_with_dashes(self, detector):
        """Test detection of international format with dashes (+1-234-567-8900)."""
        text = "Call +1-234-567-8900 for support"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].pii_type == PIIType.PHONE
        assert results[0].original_value == "+1-234-567-8900"
        assert results[0].confidence == 1.0
        assert results[0].start_pos == 5
        assert results[0].end_pos == 20

    def test_detect_parentheses_format(self, detector):
        """Test detection of parentheses format ((234) 567-8900)."""
        text = "Phone: (234) 567-8900"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].pii_type == PIIType.PHONE
        assert results[0].original_value == "(234) 567-8900"
        assert results[0].confidence == 1.0

    def test_detect_dashes_format(self, detector):
        """Test detection of dashes format (234-567-8900)."""
        text = "Contact: 234-567-8900"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].pii_type == PIIType.PHONE
        assert results[0].original_value == "234-567-8900"

    def test_detect_plain_digits(self, detector):
        """Test detection of plain digits format (2345678900)."""
        text = "Call 2345678900 today"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].pii_type == PIIType.PHONE
        assert results[0].original_value == "2345678900"

    def test_detect_with_spaces(self, detector):
        """Test detection of phone with spaces (234 567 8900)."""
        text = "Phone: 234 567 8900"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].pii_type == PIIType.PHONE
        assert results[0].original_value == "234 567 8900"

    def test_detect_international_with_spaces(self, detector):
        """Test detection of international format with spaces (+1 234 567 8900)."""
        text = "Call +1 234 567 8900"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].original_value == "+1 234 567 8900"

    def test_detect_with_dots(self, detector):
        """Test detection of phone with dots (234.567.8900)."""
        text = "Phone: 234.567.8900"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].original_value == "234.567.8900"

    def test_format_preservation_dashes(self, detector):
        """Test that format information is captured for dashes."""
        text = "555-123-4567"
        results = detector.detect(text)

        assert len(results) == 1
        # Original value preserves the format
        assert "-" in results[0].original_value
        assert results[0].original_value == "555-123-4567"

    def test_format_preservation_parentheses(self, detector):
        """Test that format information is captured for parentheses."""
        text = "(555) 123-4567"
        results = detector.detect(text)

        assert len(results) == 1
        # Original value preserves the format
        assert "(" in results[0].original_value
        assert ")" in results[0].original_value
        assert results[0].original_value == "(555) 123-4567"

    def test_format_preservation_international(self, detector):
        """Test that format information is captured for international."""
        text = "+1-555-123-4567"
        results = detector.detect(text)

        assert len(results) == 1
        # Original value preserves the format
        assert results[0].original_value.startswith("+")
        assert results[0].original_value == "+1-555-123-4567"

    def test_no_detection_too_few_digits(self, detector):
        """Test non-detection of numbers with too few digits (< 10)."""
        text = "Call 123-4567 for info"
        results = detector.detect(text)

        assert len(results) == 0

    def test_no_detection_too_many_digits(self, detector):
        """Test non-detection of numbers with too many digits (> 15)."""
        text = "Number: 12345678901234567890"
        results = detector.detect(text)

        assert len(results) == 0

    def test_no_detection_invalid_format(self, detector):
        """Test non-detection of various invalid formats."""
        invalid_phones = [
            "123-45-6789",  # SSN-like format (9 digits)
            "12-34-56",  # Too few digits
            "abc-def-ghij",  # No digits
        ]

        for text in invalid_phones:
            results = detector.detect(text)
            assert len(results) == 0, f"Should not detect: {text}"

    def test_detect_multiple_phones(self, detector):
        """Test detection of multiple phone numbers in same text."""
        text = "Call 234-567-8900 or (555) 123-4567 for help"
        results = detector.detect(text)

        assert len(results) == 2
        assert results[0].original_value == "234-567-8900"
        assert results[1].original_value == "(555) 123-4567"

    def test_detect_in_field_named_phone(self, detector):
        """Test detection in field named 'phone'."""
        text = "555-123-4567"
        results = detector.detect(text, field_name="phone")

        assert len(results) == 1
        assert results[0].original_value == "555-123-4567"

    def test_detect_in_field_named_mobile(self, detector):
        """Test detection in field named 'mobile'."""
        text = "(555) 123-4567"
        results = detector.detect(text, field_name="mobile")

        assert len(results) == 1
        assert results[0].original_value == "(555) 123-4567"

    def test_detect_in_field_named_contact(self, detector):
        """Test detection in field named 'contact'."""
        text = "+1-555-123-4567"
        results = detector.detect(text, field_name="contact")

        assert len(results) == 1
        assert results[0].original_value == "+1-555-123-4567"

    def test_detect_in_field_named_phone_number(self, detector):
        """Test detection in field named 'phone_number'."""
        text = "2345678900"
        results = detector.detect(text, field_name="phone_number")

        assert len(results) == 1
        assert results[0].original_value == "2345678900"

    def test_detect_in_arbitrary_field_name(self, detector):
        """Test detection works regardless of field name."""
        text = "555-123-4567"
        field_names = ["random_field", "description", "notes", "data", "info", ""]

        for field_name in field_names:
            results = detector.detect(text, field_name=field_name)
            assert len(results) == 1, f"Should detect in field: {field_name}"
            assert results[0].original_value == "555-123-4567"

    def test_detect_empty_string(self, detector):
        """Test detection on empty string."""
        results = detector.detect("")
        assert len(results) == 0

    def test_detect_non_string_input(self, detector):
        """Test detection handles non-string input gracefully."""
        results = detector.detect(None)
        assert len(results) == 0

    def test_detect_11_digit_number(self, detector):
        """Test detection of 11-digit number (valid range)."""
        text = "Call 12345678901"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].original_value == "12345678901"

    def test_detect_15_digit_number(self, detector):
        """Test detection of 15-digit number (max valid)."""
        text = "Call 123456789012345"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].original_value == "123456789012345"

    def test_detect_10_digit_number(self, detector):
        """Test detection of 10-digit number (min valid)."""
        text = "Call 1234567890"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].original_value == "1234567890"
