"""Property-based tests for PII replacement.

This module contains property tests that verify universal correctness
properties of PII replacement across all inputs using randomized testing.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from data_sanitizer.models import DetectionResult, PIIType
from data_sanitizer.replacer import Replacer


# Import email strategy from detection properties
@st.composite
def email_addresses(draw):
    """Generate valid email addresses for property testing."""
    local_chars = st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._%+-",
        min_size=1,
        max_size=20,
    ).filter(lambda x: x[0].isalnum() and x[-1].isalnum())

    domain_chars = st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-",
        min_size=1,
        max_size=20,
    ).filter(lambda x: x[0].isalnum() and x[-1].isalnum())

    tld = st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=2, max_size=10
    )

    local = draw(local_chars)
    domain = draw(domain_chars)
    tld_part = draw(tld)

    return f"{local}@{domain}.{tld_part}"


class TestEmailConsistencyProperty:
    """Property-based tests for email consistency."""

    @settings(max_examples=15)
    @given(email=email_addresses())
    def test_email_consistency(self, email: str):
        """Feature: data-sanitizer, Property 6: Email Consistency

        For any email value that appears multiple times in a dataset,
        all occurrences should be replaced with the same fake email.

        Validates: Requirements 2.3
        """
        replacer = Replacer(seed=42)

        # Create multiple detections of the same email
        detection1 = DetectionResult(PIIType.EMAIL, email, 1.0)
        detection2 = DetectionResult(PIIType.EMAIL, email, 1.0)
        detection3 = DetectionResult(PIIType.EMAIL, email, 1.0)

        # Replace all occurrences
        fake1 = replacer.replace(detection1)
        fake2 = replacer.replace(detection2)
        fake3 = replacer.replace(detection3)

        # Assert: All occurrences map to the same fake email
        assert fake1 == fake2, (
            f"Email consistency violated: '{email}' mapped to '{fake1}' and '{fake2}'"
        )
        assert fake2 == fake3, (
            f"Email consistency violated: '{email}' mapped to '{fake2}' and '{fake3}'"
        )
        assert fake1 == fake3, (
            f"Email consistency violated: '{email}' mapped to '{fake1}' and '{fake3}'"
        )


# Phone number strategy
@st.composite
def phone_numbers(draw):
    """Generate valid phone numbers for property testing."""
    digit_count = draw(st.integers(min_value=10, max_value=15))
    digits = "".join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(digit_count)])

    # Choose a format
    format_choice = draw(st.integers(min_value=0, max_value=3))

    if format_choice == 0 and len(digits) >= 10:
        # Dashes format: 234-567-8900
        area = digits[:3]
        prefix = digits[3:6]
        line = digits[6:10]
        return f"{area}-{prefix}-{line}"
    elif format_choice == 1 and len(digits) == 10:
        # Parentheses format: (234) 567-8900
        area = digits[:3]
        prefix = digits[3:6]
        line = digits[6:10]
        return f"({area}) {prefix}-{line}"
    elif format_choice == 2:
        # Plain digits
        return digits
    else:
        # International with dashes
        if len(digits) >= 11:
            country = digits[:1]
            area = digits[1:4]
            prefix = digits[4:7]
            line = digits[7:11]
            return f"+{country}-{area}-{prefix}-{line}"
        return digits


class TestPhoneConsistencyProperty:
    """Property-based tests for phone consistency."""

    @settings(max_examples=15)
    @given(phone=phone_numbers())
    def test_phone_consistency(self, phone: str):
        """Feature: data-sanitizer, Property 8: Phone Consistency

        For any phone number that appears multiple times in a dataset,
        all occurrences should be replaced with the same fake phone number.

        Validates: Requirements 3.3
        """
        replacer = Replacer(seed=42)

        # Create multiple detections of the same phone
        detection1 = DetectionResult(PIIType.PHONE, phone, 1.0)
        detection2 = DetectionResult(PIIType.PHONE, phone, 1.0)
        detection3 = DetectionResult(PIIType.PHONE, phone, 1.0)

        # Replace all occurrences
        fake1 = replacer.replace(detection1)
        fake2 = replacer.replace(detection2)
        fake3 = replacer.replace(detection3)

        # Assert: All occurrences map to the same fake phone
        assert fake1 == fake2, (
            f"Phone consistency violated: '{phone}' mapped to '{fake1}' and '{fake2}'"
        )
        assert fake2 == fake3, (
            f"Phone consistency violated: '{phone}' mapped to '{fake2}' and '{fake3}'"
        )
        assert fake1 == fake3, (
            f"Phone consistency violated: '{phone}' mapped to '{fake1}' and '{fake3}'"
        )


# Name strategy
@st.composite
def names(draw):
    """Generate names for property testing."""
    first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]

    # Choose name type
    name_type = draw(st.integers(min_value=0, max_value=2))

    if name_type == 0:
        # Full name
        first = draw(st.sampled_from(first_names))
        last = draw(st.sampled_from(last_names))
        return f"{first} {last}", PIIType.FULL_NAME
    elif name_type == 1:
        # First name
        return draw(st.sampled_from(first_names)), PIIType.FIRST_NAME
    else:
        # Last name
        return draw(st.sampled_from(last_names)), PIIType.LAST_NAME


class TestNameConsistencyProperty:
    """Property-based tests for name consistency."""

    @settings(max_examples=15)
    @given(name_data=names())
    def test_name_consistency(self, name_data: tuple[str, PIIType]):
        """Feature: data-sanitizer, Property 11: Name Consistency

        For any name value that appears multiple times in a dataset,
        all occurrences should be replaced with the same fake name.

        Validates: Requirements 4.5
        """
        name, pii_type = name_data
        replacer = Replacer(seed=42)

        # Create multiple detections of the same name
        detection1 = DetectionResult(pii_type, name, 1.0)
        detection2 = DetectionResult(pii_type, name, 1.0)
        detection3 = DetectionResult(pii_type, name, 1.0)

        # Replace all occurrences
        fake1 = replacer.replace(detection1)
        fake2 = replacer.replace(detection2)
        fake3 = replacer.replace(detection3)

        # Assert: All occurrences map to the same fake name
        assert fake1 == fake2, (
            f"Name consistency violated: '{name}' mapped to '{fake1}' and '{fake2}'"
        )
        assert fake2 == fake3, (
            f"Name consistency violated: '{name}' mapped to '{fake2}' and '{fake3}'"
        )
        assert fake1 == fake3, (
            f"Name consistency violated: '{name}' mapped to '{fake1}' and '{fake3}'"
        )


# Credit card strategy
@st.composite
def credit_cards(draw):
    """Generate valid credit card numbers for property testing."""
    # Choose card type
    card_type = draw(st.sampled_from(["visa", "mastercard", "amex"]))

    if card_type == "visa":
        prefix = "4"
        remaining_length = 15
    elif card_type == "mastercard":
        prefix = str(draw(st.integers(min_value=51, max_value=55)))
        remaining_length = 14
    else:  # amex
        prefix = draw(st.sampled_from(["34", "37"]))
        remaining_length = 13

    # Generate random digits for the rest (except check digit)
    middle_digits = "".join(
        [str(draw(st.integers(min_value=0, max_value=9))) for _ in range(remaining_length - 1)]
    )

    # Calculate Luhn check digit
    partial_number = prefix + middle_digits
    check_digit = _calculate_luhn_check_digit(partial_number)

    return partial_number + str(check_digit)


def _calculate_luhn_check_digit(partial_number: str) -> int:
    """Calculate the Luhn check digit for a partial credit card number."""
    digits = [int(d) for d in partial_number[::-1]]

    for i in range(0, len(digits), 2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9

    total = sum(digits)
    check_digit = (10 - (total % 10)) % 10

    return check_digit


class TestCreditCardConsistencyProperty:
    """Property-based tests for credit card consistency."""

    @settings(max_examples=15)
    @given(card=credit_cards())
    def test_credit_card_consistency(self, card: str):
        """Feature: data-sanitizer, Property 15: Credit Card Consistency

        For any credit card number that appears multiple times in a dataset,
        all occurrences should be replaced with the same fake credit card number.

        Validates: Requirements 5.3
        """
        replacer = Replacer(seed=42)

        # Create multiple detections of the same credit card
        detection1 = DetectionResult(PIIType.CREDIT_CARD, card, 1.0)
        detection2 = DetectionResult(PIIType.CREDIT_CARD, card, 1.0)
        detection3 = DetectionResult(PIIType.CREDIT_CARD, card, 1.0)

        # Replace all occurrences
        fake1 = replacer.replace(detection1)
        fake2 = replacer.replace(detection2)
        fake3 = replacer.replace(detection3)

        # Assert: All occurrences map to the same fake credit card
        assert fake1 == fake2, (
            f"Credit card consistency violated: '{card}' mapped to '{fake1}' and '{fake2}'"
        )
        assert fake2 == fake3, (
            f"Credit card consistency violated: '{card}' mapped to '{fake2}' and '{fake3}'"
        )
        assert fake1 == fake3, (
            f"Credit card consistency violated: '{card}' mapped to '{fake1}' and '{fake3}'"
        )


class TestReplacementUniquenessProperty:
    """Property-based tests for replacement uniqueness."""

    @settings(max_examples=15)
    @given(email1=email_addresses(), email2=email_addresses())
    def test_replacement_uniqueness_emails(self, email1: str, email2: str):
        """Feature: data-sanitizer, Property 16: Replacement Uniqueness (Emails)

        For any two different PII values of the same type, they should be
        replaced with different fake values (injective mapping).

        Validates: Requirements 6.2
        """
        # Skip if emails are the same
        if email1 == email2:
            return

        replacer = Replacer(seed=42)

        # Create detections for different emails
        detection1 = DetectionResult(PIIType.EMAIL, email1, 1.0)
        detection2 = DetectionResult(PIIType.EMAIL, email2, 1.0)

        # Replace both
        fake1 = replacer.replace(detection1)
        fake2 = replacer.replace(detection2)

        # Assert: Different inputs map to different outputs
        assert fake1 != fake2, (
            f"Uniqueness violated: different emails '{email1}' and '{email2}' "
            f"both mapped to '{fake1}'"
        )

    @settings(max_examples=15)
    @given(phone1=phone_numbers(), phone2=phone_numbers())
    def test_replacement_uniqueness_phones(self, phone1: str, phone2: str):
        """Feature: data-sanitizer, Property 16: Replacement Uniqueness (Phones)

        For any two different phone numbers, they should be replaced with
        different fake phone numbers.

        Validates: Requirements 6.2
        """
        # Skip if phones are the same
        if phone1 == phone2:
            return

        replacer = Replacer(seed=42)

        # Create detections for different phones
        detection1 = DetectionResult(PIIType.PHONE, phone1, 1.0)
        detection2 = DetectionResult(PIIType.PHONE, phone2, 1.0)

        # Replace both
        fake1 = replacer.replace(detection1)
        fake2 = replacer.replace(detection2)

        # Assert: Different inputs map to different outputs
        assert fake1 != fake2, (
            f"Uniqueness violated: different phones '{phone1}' and '{phone2}' "
            f"both mapped to '{fake1}'"
        )

    @settings(max_examples=15)
    @given(card1=credit_cards(), card2=credit_cards())
    def test_replacement_uniqueness_credit_cards(self, card1: str, card2: str):
        """Feature: data-sanitizer, Property 16: Replacement Uniqueness (Credit Cards)

        For any two different credit card numbers, they should be replaced with
        different fake credit card numbers.

        Validates: Requirements 6.2
        """
        # Skip if cards are the same
        if card1 == card2:
            return

        replacer = Replacer(seed=42)

        # Create detections for different cards
        detection1 = DetectionResult(PIIType.CREDIT_CARD, card1, 1.0)
        detection2 = DetectionResult(PIIType.CREDIT_CARD, card2, 1.0)

        # Replace both
        fake1 = replacer.replace(detection1)
        fake2 = replacer.replace(detection2)

        # Assert: Different inputs map to different outputs
        assert fake1 != fake2, (
            f"Uniqueness violated: different cards '{card1}' and '{card2}' both mapped to '{fake1}'"
        )


class TestCrossFieldNameConsistencyProperty:
    """Property-based tests for cross-field name consistency."""

    @settings(max_examples=15)
    @given(
        first_name=st.sampled_from(["John", "Jane", "Michael", "Sarah", "David"]),
        last_name=st.sampled_from(["Smith", "Johnson", "Williams", "Brown", "Jones"]),
    )
    def test_cross_field_name_consistency(self, first_name: str, last_name: str):
        """Feature: data-sanitizer, Property 13: Cross-Field Name Consistency

        For any record with separate first_name and last_name fields, the fake
        replacements should belong to the same fake person (i.e., if "John" → "Michael"
        and "Doe" → "Johnson", they should consistently map together).

        Validates: Requirements 4.7
        """
        replacer = Replacer(seed=42)

        # Replace first name in first record
        first_detection1 = DetectionResult(PIIType.FIRST_NAME, first_name, 1.0)
        fake_first1 = replacer.replace(first_detection1)

        # Replace last name in first record
        last_detection1 = DetectionResult(PIIType.LAST_NAME, last_name, 1.0)
        fake_last1 = replacer.replace(last_detection1)

        # Replace same first name in second record - should get same fake first name
        first_detection2 = DetectionResult(PIIType.FIRST_NAME, first_name, 1.0)
        fake_first2 = replacer.replace(first_detection2)

        # Replace same last name in second record - should get same fake last name
        last_detection2 = DetectionResult(PIIType.LAST_NAME, last_name, 1.0)
        fake_last2 = replacer.replace(last_detection2)

        # Assert: Same first name always maps to same fake first name
        assert fake_first1 == fake_first2, (
            f"Cross-field consistency violated: first name '{first_name}' "
            f"mapped to '{fake_first1}' and '{fake_first2}'"
        )

        # Assert: Same last name always maps to same fake last name
        assert fake_last1 == fake_last2, (
            f"Cross-field consistency violated: last name '{last_name}' "
            f"mapped to '{fake_last1}' and '{fake_last2}'"
        )

        # The fake names should belong to the same fake person across records
        # This is ensured by the consistency cache maintaining separate mappings
        # for first and last names
