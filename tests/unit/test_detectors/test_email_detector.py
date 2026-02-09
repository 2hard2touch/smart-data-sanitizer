"""Unit tests for EmailDetector.

This module tests the email detection functionality, including:
- Detection of standard email formats
- Detection of emails with special characters
- Non-detection of invalid email formats
- Field-name-agnostic detection
"""

import pytest

from data_sanitizer.detectors.email_detector import EmailDetector
from data_sanitizer.models import PIIType


class TestEmailDetector:
    """Test suite for EmailDetector."""

    @pytest.fixture
    def detector(self):
        """Create an EmailDetector instance for testing."""
        return EmailDetector()

    def test_detect_standard_email(self, detector):
        """Test detection of standard email format (user@example.com)."""
        text = "Contact user@example.com for more info"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].pii_type == PIIType.EMAIL
        assert results[0].original_value == "user@example.com"
        assert results[0].confidence == 1.0
        assert results[0].start_pos == 8
        assert results[0].end_pos == 24

    def test_detect_email_with_plus(self, detector):
        """Test detection of email with plus sign (user+tag@example.com)."""
        text = "Email: user+tag@example.com"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].pii_type == PIIType.EMAIL
        assert results[0].original_value == "user+tag@example.com"
        assert results[0].confidence == 1.0

    def test_detect_email_with_subdomain(self, detector):
        """Test detection of email with subdomain (user@mail.example.co.uk)."""
        text = "user+tag@example.co.uk"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].pii_type == PIIType.EMAIL
        assert results[0].original_value == "user+tag@example.co.uk"

    def test_detect_email_with_dots_and_underscores(self, detector):
        """Test detection of email with dots and underscores."""
        text = "first.last_name@example.com"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].original_value == "first.last_name@example.com"

    def test_no_detection_missing_at_symbol(self, detector):
        """Test non-detection of text missing @ symbol."""
        text = "This is not an email: userexample.com"
        results = detector.detect(text)

        assert len(results) == 0

    def test_no_detection_missing_domain(self, detector):
        """Test non-detection of text missing domain."""
        text = "Invalid email: user@"
        results = detector.detect(text)

        assert len(results) == 0

    def test_no_detection_missing_tld(self, detector):
        """Test non-detection of email missing TLD."""
        text = "Invalid: user@domain"
        results = detector.detect(text)

        assert len(results) == 0

    def test_no_detection_invalid_format(self, detector):
        """Test non-detection of various invalid formats."""
        invalid_emails = [
            "@example.com",  # Missing local part
            "user@.com",  # Missing domain
            "user @example.com",  # Space in email
            "user@example",  # Missing TLD
        ]

        for text in invalid_emails:
            results = detector.detect(text)
            assert len(results) == 0, f"Should not detect: {text}"

    def test_detect_multiple_emails(self, detector):
        """Test detection of multiple emails in same text."""
        text = "Contact john@example.com or jane@test.org for help"
        results = detector.detect(text)

        assert len(results) == 2
        assert results[0].original_value == "john@example.com"
        assert results[1].original_value == "jane@test.org"

    def test_detect_in_field_named_email(self, detector):
        """Test detection in field named 'email'."""
        text = "user@example.com"
        results = detector.detect(text, field_name="email")

        assert len(results) == 1
        assert results[0].original_value == "user@example.com"

    def test_detect_in_field_named_contact(self, detector):
        """Test detection in field named 'contact'."""
        text = "contact@example.com"
        results = detector.detect(text, field_name="contact")

        assert len(results) == 1
        assert results[0].original_value == "contact@example.com"

    def test_detect_in_field_named_info(self, detector):
        """Test detection in field named 'info'."""
        text = "info@example.com"
        results = detector.detect(text, field_name="info")

        assert len(results) == 1
        assert results[0].original_value == "info@example.com"

    def test_detect_in_field_named_payload(self, detector):
        """Test detection in field named 'payload'."""
        text = "Data: admin@example.com"
        results = detector.detect(text, field_name="payload")

        assert len(results) == 1
        assert results[0].original_value == "admin@example.com"

    def test_detect_in_arbitrary_field_name(self, detector):
        """Test detection works regardless of field name."""
        text = "test@example.com"
        field_names = ["random_field", "description", "notes", "data", ""]

        for field_name in field_names:
            results = detector.detect(text, field_name=field_name)
            assert len(results) == 1, f"Should detect in field: {field_name}"
            assert results[0].original_value == "test@example.com"

    def test_detect_empty_string(self, detector):
        """Test detection on empty string."""
        results = detector.detect("")
        assert len(results) == 0

    def test_detect_non_string_input(self, detector):
        """Test detection handles non-string input gracefully."""
        results = detector.detect(None)
        assert len(results) == 0
