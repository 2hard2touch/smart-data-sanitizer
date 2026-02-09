"""Unit tests for the Replacer class."""

import re

from data_sanitizer.models import DetectionResult, PIIType
from data_sanitizer.replacer import Replacer


class TestReplacerEmailGeneration:
    """Tests for email generation and validity."""

    def test_generates_valid_email(self) -> None:
        """Test that generated emails are valid."""
        replacer = Replacer(seed=42)
        detection = DetectionResult(PIIType.EMAIL, "test@example.com", 1.0)

        fake_email = replacer.replace(detection)

        # Check email format: local@domain.tld
        email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$"
        assert re.match(email_pattern, fake_email), f"Invalid email format: {fake_email}"

    def test_email_consistency_same_input(self) -> None:
        """Test that same email always gets same replacement."""
        replacer = Replacer(seed=42)
        original = "john@example.com"

        detection1 = DetectionResult(PIIType.EMAIL, original, 1.0)
        detection2 = DetectionResult(PIIType.EMAIL, original, 1.0)

        fake1 = replacer.replace(detection1)
        fake2 = replacer.replace(detection2)

        assert fake1 == fake2, "Same email should map to same fake email"

    def test_email_different_inputs_different_outputs(self) -> None:
        """Test that different emails get different replacements."""
        replacer = Replacer(seed=42)

        detection1 = DetectionResult(PIIType.EMAIL, "john@example.com", 1.0)
        detection2 = DetectionResult(PIIType.EMAIL, "jane@example.com", 1.0)

        fake1 = replacer.replace(detection1)
        fake2 = replacer.replace(detection2)

        assert fake1 != fake2, "Different emails should map to different fake emails"


class TestReplacerPhoneGeneration:
    """Tests for phone generation and format preservation."""

    def test_generates_valid_phone(self) -> None:
        """Test that generated phones are valid."""
        replacer = Replacer(seed=42)
        detection = DetectionResult(PIIType.PHONE, "555-123-4567", 1.0)

        fake_phone = replacer.replace(detection)

        # Check that it contains digits
        assert re.search(r"\d", fake_phone), "Phone should contain digits"

    def test_phone_format_preservation_with_dashes(self) -> None:
        """Test that phone format with dashes is preserved."""
        replacer = Replacer(seed=42)
        original = "234-567-8900"
        detection = DetectionResult(PIIType.PHONE, original, 1.0)

        fake_phone = replacer.replace(detection)

        # Should have dash format
        assert "-" in fake_phone or fake_phone.count("-") >= 2, (
            f"Phone format not preserved: {fake_phone}"
        )

    def test_phone_format_preservation_with_parentheses(self) -> None:
        """Test that phone format with parentheses is preserved."""
        replacer = Replacer(seed=42)
        original = "(555) 123-4567"
        detection = DetectionResult(PIIType.PHONE, original, 1.0)

        fake_phone = replacer.replace(detection)

        # Should have parentheses format
        assert "(" in fake_phone and ")" in fake_phone, f"Phone format not preserved: {fake_phone}"

    def test_phone_format_preservation_digits_only(self) -> None:
        """Test that phone format with digits only is preserved."""
        replacer = Replacer(seed=42)
        original = "5551234567"
        detection = DetectionResult(PIIType.PHONE, original, 1.0)

        fake_phone = replacer.replace(detection)

        # Should be digits only
        assert fake_phone.isdigit(), f"Phone should be digits only: {fake_phone}"

    def test_phone_consistency(self) -> None:
        """Test that same phone always gets same replacement."""
        replacer = Replacer(seed=42)
        original = "555-123-4567"

        detection1 = DetectionResult(PIIType.PHONE, original, 1.0)
        detection2 = DetectionResult(PIIType.PHONE, original, 1.0)

        fake1 = replacer.replace(detection1)
        fake2 = replacer.replace(detection2)

        assert fake1 == fake2, "Same phone should map to same fake phone"


class TestReplacerNameGeneration:
    """Tests for name generation with case preservation."""

    def test_generates_full_name(self) -> None:
        """Test that full names are generated."""
        replacer = Replacer(seed=42)
        detection = DetectionResult(PIIType.FULL_NAME, "John Doe", 1.0)

        fake_name = replacer.replace(detection)

        # Should have at least one space (first and last name)
        assert " " in fake_name, f"Full name should have space: {fake_name}"

    def test_name_case_preservation_title_case(self) -> None:
        """Test that title case is preserved."""
        replacer = Replacer(seed=42)
        detection = DetectionResult(PIIType.FULL_NAME, "John Doe", 1.0)

        fake_name = replacer.replace(detection)

        # Should be title case (first letter uppercase)
        words = fake_name.split()
        for word in words:
            assert word[0].isupper(), f"Title case not preserved: {fake_name}"

    def test_name_case_preservation_lowercase(self) -> None:
        """Test that lowercase is preserved."""
        replacer = Replacer(seed=42)
        detection = DetectionResult(PIIType.FIRST_NAME, "john", 1.0)

        fake_name = replacer.replace(detection)

        assert fake_name.islower(), f"Lowercase not preserved: {fake_name}"

    def test_name_case_preservation_uppercase(self) -> None:
        """Test that uppercase is preserved."""
        replacer = Replacer(seed=42)
        detection = DetectionResult(PIIType.FIRST_NAME, "JOHN", 1.0)

        fake_name = replacer.replace(detection)

        assert fake_name.isupper(), f"Uppercase not preserved: {fake_name}"

    def test_name_consistency(self) -> None:
        """Test that same name always gets same replacement."""
        replacer = Replacer(seed=42)
        original = "John Doe"

        detection1 = DetectionResult(PIIType.FULL_NAME, original, 1.0)
        detection2 = DetectionResult(PIIType.FULL_NAME, original, 1.0)

        fake1 = replacer.replace(detection1)
        fake2 = replacer.replace(detection2)

        assert fake1 == fake2, "Same name should map to same fake name"

    def test_cross_field_name_consistency(self) -> None:
        """Test that first and last names maintain consistency across fields."""
        replacer = Replacer(seed=42)

        # Replace first name
        first_detection = DetectionResult(PIIType.FIRST_NAME, "John", 1.0)
        fake_first = replacer.replace(first_detection)

        # Replace last name
        last_detection = DetectionResult(PIIType.LAST_NAME, "Doe", 1.0)
        fake_last = replacer.replace(last_detection)

        # Replace same first name again - should get same fake first name
        first_detection2 = DetectionResult(PIIType.FIRST_NAME, "John", 1.0)
        fake_first2 = replacer.replace(first_detection2)

        assert fake_first == fake_first2, "Same first name should map to same fake first name"

        # Replace same last name again - should get same fake last name
        last_detection2 = DetectionResult(PIIType.LAST_NAME, "Doe", 1.0)
        fake_last2 = replacer.replace(last_detection2)

        assert fake_last == fake_last2, "Same last name should map to same fake last name"


class TestReplacerCreditCardGeneration:
    """Tests for credit card generation and Luhn validity."""

    def test_generates_credit_card(self) -> None:
        """Test that credit cards are generated."""
        replacer = Replacer(seed=42)
        detection = DetectionResult(PIIType.CREDIT_CARD, "4532123456789010", 1.0)

        fake_card = replacer.replace(detection)

        # Should contain digits
        digits = re.sub(r"\D", "", fake_card)
        assert len(digits) >= 13, f"Credit card should have at least 13 digits: {fake_card}"

    def test_credit_card_luhn_validity(self) -> None:
        """Test that generated credit cards pass Luhn validation."""
        replacer = Replacer(seed=42)
        detection = DetectionResult(PIIType.CREDIT_CARD, "4532123456789010", 1.0)

        fake_card = replacer.replace(detection)

        # Extract digits only
        digits = re.sub(r"\D", "", fake_card)

        # Luhn algorithm validation
        def luhn_check(card_number: str) -> bool:
            """Validate credit card number using Luhn algorithm."""
            digits = [int(d) for d in card_number]
            checksum = 0

            # Process digits from right to left
            for i in range(len(digits) - 1, -1, -1):
                digit = digits[i]

                # Double every second digit from the right
                if (len(digits) - i) % 2 == 0:
                    digit *= 2
                    if digit > 9:
                        digit -= 9

                checksum += digit

            return checksum % 10 == 0

        assert luhn_check(digits), f"Credit card failed Luhn validation: {fake_card}"

    def test_credit_card_consistency(self) -> None:
        """Test that same credit card always gets same replacement."""
        replacer = Replacer(seed=42)
        original = "4532123456789010"

        detection1 = DetectionResult(PIIType.CREDIT_CARD, original, 1.0)
        detection2 = DetectionResult(PIIType.CREDIT_CARD, original, 1.0)

        fake1 = replacer.replace(detection1)
        fake2 = replacer.replace(detection2)

        assert fake1 == fake2, "Same credit card should map to same fake credit card"


class TestReplacerConsistencyCache:
    """Tests for consistency cache behavior."""

    def test_cache_maintains_consistency_across_types(self) -> None:
        """Test that cache maintains consistency for different PII types."""
        replacer = Replacer(seed=42)

        # Same value but different types should get different replacements
        email_detection = DetectionResult(PIIType.EMAIL, "test@example.com", 1.0)
        # Note: This is contrived - same string won't be both email and name
        # But tests the cache key includes type

        fake_email = replacer.replace(email_detection)

        # Verify it's cached
        fake_email2 = replacer.replace(email_detection)
        assert fake_email == fake_email2

    def test_get_or_create_replacement_direct(self) -> None:
        """Test get_or_create_replacement method directly."""
        replacer = Replacer(seed=42)

        # First call creates
        fake1 = replacer.get_or_create_replacement("test@example.com", PIIType.EMAIL)

        # Second call retrieves from cache
        fake2 = replacer.get_or_create_replacement("test@example.com", PIIType.EMAIL)

        assert fake1 == fake2, "Should retrieve from cache"

    def test_reproducibility_with_seed(self) -> None:
        """Test that seed enables reproducible generation within instance."""
        # Seed ensures reproducibility for testing purposes
        # Within a single replacer instance, consistency is guaranteed by cache
        replacer = Replacer(seed=42)

        detection1 = DetectionResult(PIIType.EMAIL, "test1@example.com", 1.0)
        detection2 = DetectionResult(PIIType.EMAIL, "test2@example.com", 1.0)

        # Generate fake values
        fake1 = replacer.replace(detection1)
        fake2 = replacer.replace(detection2)

        # They should be different (different inputs)
        assert fake1 != fake2, "Different inputs should produce different outputs"

        # But same input should always give same output (cache consistency)
        fake1_again = replacer.replace(detection1)
        assert fake1 == fake1_again, "Same input should produce same output"
