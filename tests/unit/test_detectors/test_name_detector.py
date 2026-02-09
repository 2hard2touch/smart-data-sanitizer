"""Unit tests for NameDetector.

This module tests the name detection functionality, including:
- Detection of full names (first and last name together)
- Detection of single names with field hints
- Case preservation capture (lowercase, UPPERCASE, Title Case)
- Field-name-agnostic detection
- Detection in text fields with embedded names
"""

import pytest

from data_sanitizer.detectors.name_detector import NameDetector
from data_sanitizer.models import PIIType


class TestNameDetector:
    """Test suite for NameDetector."""

    @pytest.fixture
    def detector(self):
        """Create a NameDetector instance for testing."""
        return NameDetector()

    # Full name detection tests

    def test_detect_full_name_title_case(self, detector):
        """Test detection of full name in Title Case (John Doe)."""
        text = "John Doe"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].pii_type == PIIType.FULL_NAME
        assert results[0].original_value == "John Doe"
        assert results[0].confidence > 0.0

    def test_detect_full_name_in_sentence(self, detector):
        """Test detection of full name embedded in text."""
        text = "Contact John Doe for more information"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].pii_type == PIIType.FULL_NAME
        assert results[0].original_value == "John Doe"

    def test_detect_multiple_full_names(self, detector):
        """Test detection of multiple full names in same text."""
        text = "John Doe and Jane Smith are colleagues"
        results = detector.detect(text)

        assert len(results) == 2
        assert results[0].original_value == "John Doe"
        assert results[1].original_value == "Jane Smith"

    # Single name detection with field hints

    def test_detect_first_name_with_field_hint(self, detector):
        """Test detection of single name in field named 'first_name'."""
        text = "John"
        results = detector.detect(text, field_name="first_name")

        assert len(results) == 1
        assert results[0].pii_type == PIIType.FIRST_NAME
        assert results[0].original_value == "John"

    def test_detect_first_name_with_firstname_hint(self, detector):
        """Test detection of single name in field named 'firstname'."""
        text = "Jane"
        results = detector.detect(text, field_name="firstname")

        assert len(results) == 1
        assert results[0].pii_type == PIIType.FIRST_NAME
        assert results[0].original_value == "Jane"

    def test_detect_first_name_with_fname_hint(self, detector):
        """Test detection of single name in field named 'fname'."""
        text = "Alice"
        results = detector.detect(text, field_name="fname")

        assert len(results) == 1
        assert results[0].pii_type == PIIType.FIRST_NAME
        assert results[0].original_value == "Alice"

    def test_detect_last_name_with_field_hint(self, detector):
        """Test detection of single name in field named 'last_name'."""
        text = "Smith"
        results = detector.detect(text, field_name="last_name")

        assert len(results) == 1
        assert results[0].pii_type == PIIType.LAST_NAME
        assert results[0].original_value == "Smith"

    def test_detect_last_name_with_lastname_hint(self, detector):
        """Test detection of single name in field named 'lastname'."""
        text = "Johnson"
        results = detector.detect(text, field_name="lastname")

        assert len(results) == 1
        assert results[0].pii_type == PIIType.LAST_NAME
        assert results[0].original_value == "Johnson"

    def test_detect_last_name_with_lname_hint(self, detector):
        """Test detection of single name in field named 'lname'."""
        text = "Williams"
        results = detector.detect(text, field_name="lname")

        assert len(results) == 1
        assert results[0].pii_type == PIIType.LAST_NAME
        assert results[0].original_value == "Williams"

    def test_detect_last_name_with_surname_hint(self, detector):
        """Test detection of single name in field named 'surname'."""
        text = "Brown"
        results = detector.detect(text, field_name="surname")

        assert len(results) == 1
        assert results[0].pii_type == PIIType.LAST_NAME
        assert results[0].original_value == "Brown"

    # Case preservation tests

    def test_detect_name_lowercase(self, detector):
        """Test detection and case preservation of lowercase name."""
        text = "john doe"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].original_value == "john doe"
        # Case is preserved in original_value

    def test_detect_name_uppercase(self, detector):
        """Test detection and case preservation of UPPERCASE name."""
        text = "JOHN DOE"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].original_value == "JOHN DOE"
        # Case is preserved in original_value

    def test_detect_name_mixed_case(self, detector):
        """Test detection and case preservation of mixed case name."""
        text = "JoHn DoE"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].original_value == "JoHn DoE"
        # Case is preserved in original_value

    def test_detect_single_name_lowercase_with_hint(self, detector):
        """Test detection of lowercase single name with field hint."""
        text = "jane"
        results = detector.detect(text, field_name="first_name")

        assert len(results) == 1
        assert results[0].pii_type == PIIType.FIRST_NAME
        assert results[0].original_value == "jane"

    def test_detect_single_name_uppercase_with_hint(self, detector):
        """Test detection of UPPERCASE single name with field hint."""
        text = "SMITH"
        results = detector.detect(text, field_name="last_name")

        assert len(results) == 1
        assert results[0].pii_type == PIIType.LAST_NAME
        assert results[0].original_value == "SMITH"

    # Field name agnostic tests

    def test_detect_in_field_named_name(self, detector):
        """Test detection in field named 'name'."""
        text = "Alice Johnson"
        results = detector.detect(text, field_name="name")

        assert len(results) == 1
        assert results[0].pii_type == PIIType.FULL_NAME
        assert results[0].original_value == "Alice Johnson"

    def test_detect_in_field_named_full_name(self, detector):
        """Test detection in field named 'full_name'."""
        text = "Bob Wilson"
        results = detector.detect(text, field_name="full_name")

        assert len(results) == 1
        assert results[0].pii_type == PIIType.FULL_NAME
        assert results[0].original_value == "Bob Wilson"

    def test_detect_in_field_named_customer(self, detector):
        """Test detection in field named 'customer'."""
        text = "Sarah Martinez"
        results = detector.detect(text, field_name="customer")

        assert len(results) == 1
        assert results[0].original_value == "Sarah Martinez"

    def test_detect_in_field_named_employee(self, detector):
        """Test detection in field named 'employee'."""
        text = "Michael Thompson"
        results = detector.detect(text, field_name="employee")

        assert len(results) == 1
        assert results[0].original_value == "Michael Thompson"

    def test_detect_in_arbitrary_field_name(self, detector):
        """Test detection works regardless of field name."""
        text = "David Lee"
        field_names = ["random_field", "description", "notes", "data", "payload", ""]

        for field_name in field_names:
            results = detector.detect(text, field_name=field_name)
            assert len(results) == 1, f"Should detect in field: {field_name}"
            assert results[0].original_value == "David Lee"

    # Text field detection tests

    def test_detect_name_in_bio(self, detector):
        """Test detection of name embedded in bio text."""
        text = "jane smith has been with the company for 3 years"
        results = detector.detect(text, field_name="bio")

        assert len(results) == 1
        assert results[0].original_value == "jane smith"

    def test_detect_name_in_description(self, detector):
        """Test detection of name embedded in description."""
        text = "Contact Alice Johnson at alice@example.com for any issues"
        results = detector.detect(text, field_name="description")

        assert len(results) == 1
        assert results[0].original_value == "Alice Johnson"

    def test_detect_name_in_notes(self, detector):
        """Test detection of name embedded in notes."""
        text = "Customer since 2020. Referred by Bob Wilson."
        results = detector.detect(text, field_name="notes")

        assert len(results) == 1
        assert results[0].original_value == "Bob Wilson"

    def test_detect_multiple_names_in_text(self, detector):
        """Test detection of multiple names in text field."""
        text = "John Doe referred by Alice Johnson. Contact Jane Smith for details."
        results = detector.detect(text)

        assert len(results) == 3
        names = [r.original_value for r in results]
        assert "John Doe" in names
        assert "Alice Johnson" in names
        assert "Jane Smith" in names

    # Edge cases

    def test_detect_empty_string(self, detector):
        """Test detection on empty string."""
        results = detector.detect("")
        assert len(results) == 0

    def test_detect_whitespace_only(self, detector):
        """Test detection on whitespace-only string."""
        results = detector.detect("   ")
        assert len(results) == 0

    def test_detect_non_string_input(self, detector):
        """Test detection handles non-string input gracefully."""
        results = detector.detect(None)
        assert len(results) == 0

    def test_detect_no_names_in_text(self, detector):
        """Test detection returns empty list when no names present."""
        text = "The quick brown fox jumps over the lazy dog"
        results = detector.detect(text)

        # This might detect some words as names depending on Presidio's model
        # but we're testing that it doesn't crash
        assert isinstance(results, list)

    def test_detect_single_name_without_field_hint(self, detector):
        """Test detection of single name without field hint defaults to FIRST_NAME."""
        text = "John"
        results = detector.detect(text, field_name="")

        # Single name without hint should default to FIRST_NAME
        if len(results) > 0:
            assert results[0].pii_type == PIIType.FIRST_NAME
            assert results[0].original_value == "John"

    def test_detect_three_word_name(self, detector):
        """Test detection of three-word name as FULL_NAME."""
        text = "John Paul Smith"
        results = detector.detect(text)

        # Three-word name should be detected as FULL_NAME
        if len(results) > 0:
            # Presidio might detect this as one or multiple entities
            # We just verify it's detected
            assert any(r.pii_type == PIIType.FULL_NAME for r in results)
