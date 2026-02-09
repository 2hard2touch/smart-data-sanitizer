"""Unit tests for CreditCardDetector.

This module tests the credit card detection functionality, including:
- Detection of valid credit cards (Visa, MasterCard, Amex)
- Luhn algorithm validation (valid vs invalid)
- Detection with various spacing/dash patterns
- Non-detection of invalid card numbers
"""

import pytest

from data_sanitizer.detectors.credit_card_detector import CreditCardDetector
from data_sanitizer.models import PIIType


class TestCreditCardDetector:
    """Test suite for CreditCardDetector."""

    @pytest.fixture
    def detector(self):
        """Create a CreditCardDetector instance for testing."""
        return CreditCardDetector()

    def test_detect_visa_no_separators(self, detector):
        """Test detection of Visa card without separators."""
        # Valid Visa test card number
        text = "Card: 4532015112830366"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].pii_type == PIIType.CREDIT_CARD
        assert results[0].original_value == "4532015112830366"
        assert results[0].confidence == 1.0

    def test_detect_visa_with_spaces(self, detector):
        """Test detection of Visa card with spaces."""
        text = "Card: 4532 0151 1283 0366"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].pii_type == PIIType.CREDIT_CARD
        assert results[0].original_value == "4532 0151 1283 0366"
        assert results[0].confidence == 1.0

    def test_detect_visa_with_dashes(self, detector):
        """Test detection of Visa card with dashes."""
        text = "Payment: 4532-0151-1283-0366"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].pii_type == PIIType.CREDIT_CARD
        assert results[0].original_value == "4532-0151-1283-0366"

    def test_detect_mastercard(self, detector):
        """Test detection of MasterCard."""
        # Valid MasterCard test number
        text = "5425233430109903"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].pii_type == PIIType.CREDIT_CARD
        assert results[0].original_value == "5425233430109903"

    def test_detect_amex(self, detector):
        """Test detection of American Express card (15 digits)."""
        # Valid Amex test number
        text = "Amex: 378282246310005"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].pii_type == PIIType.CREDIT_CARD
        assert results[0].original_value == "378282246310005"

    def test_detect_amex_with_spaces(self, detector):
        """Test detection of Amex with spaces."""
        text = "3782 822463 10005"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].original_value == "3782 822463 10005"

    def test_luhn_validation_valid_numbers(self, detector):
        """Test Luhn algorithm with known valid numbers."""
        valid_cards = [
            "4532015112830366",  # Visa
            "5425233430109903",  # MasterCard
            "378282246310005",  # Amex
            "6011111111111117",  # Discover
        ]

        for card in valid_cards:
            assert detector._luhn_check(card), f"Should validate: {card}"

    def test_luhn_validation_invalid_numbers(self, detector):
        """Test Luhn algorithm rejects invalid numbers."""
        invalid_cards = [
            "4532015112830367",  # Last digit wrong
            "5425233430109904",  # Last digit wrong
            "378282246310006",  # Last digit wrong
            "1234567890123456",  # Random invalid
        ]

        for card in invalid_cards:
            assert not detector._luhn_check(card), f"Should reject: {card}"

    def test_no_detection_invalid_luhn(self, detector):
        """Test non-detection of numbers that fail Luhn validation."""
        text = "Invalid card: 1234567890123456"
        results = detector.detect(text)

        assert len(results) == 0

    def test_no_detection_too_short(self, detector):
        """Test non-detection of numbers too short (< 13 digits)."""
        text = "Too short: 123456789012"
        results = detector.detect(text)

        assert len(results) == 0

    def test_no_detection_too_long(self, detector):
        """Test non-detection of numbers too long (> 19 digits)."""
        text = "Too long: 12345678901234567890"
        results = detector.detect(text)

        assert len(results) == 0

    def test_detect_mixed_separators(self, detector):
        """Test detection with mixed spaces and dashes."""
        text = "Card: 4532 0151-1283 0366"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].original_value == "4532 0151-1283 0366"

    def test_detect_multiple_cards(self, detector):
        """Test detection of multiple cards in same text."""
        text = "Cards: 4532015112830366 and 5425233430109903"
        results = detector.detect(text)

        assert len(results) == 2
        assert results[0].original_value == "4532015112830366"
        assert results[1].original_value == "5425233430109903"

    def test_detect_in_various_field_names(self, detector):
        """Test detection works regardless of field name."""
        text = "4532015112830366"
        field_names = ["credit_card", "card", "payment", "cc", "random_field", ""]

        for field_name in field_names:
            results = detector.detect(text, field_name=field_name)
            assert len(results) == 1, f"Should detect in field: {field_name}"
            assert results[0].original_value == "4532015112830366"

    def test_detect_embedded_in_text(self, detector):
        """Test detection of card embedded in longer text."""
        text = "Please charge card 4532-0151-1283-0366 for the purchase."
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].original_value == "4532-0151-1283-0366"

    def test_detect_empty_string(self, detector):
        """Test detection on empty string."""
        results = detector.detect("")
        assert len(results) == 0

    def test_detect_non_string_input(self, detector):
        """Test detection handles non-string input gracefully."""
        results = detector.detect(None)
        assert len(results) == 0

    def test_no_detection_partial_card(self, detector):
        """Test non-detection of partial card numbers."""
        text = "Last 4 digits: 9010"
        results = detector.detect(text)

        assert len(results) == 0

    def test_position_tracking(self, detector):
        """Test that start and end positions are tracked correctly."""
        text = "Card number: 4532015112830366 is valid"
        results = detector.detect(text)

        assert len(results) == 1
        assert results[0].start_pos == 13
        assert results[0].end_pos == 29
        assert text[results[0].start_pos : results[0].end_pos] == "4532015112830366"
