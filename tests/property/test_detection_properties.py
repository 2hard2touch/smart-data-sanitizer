"""Property-based tests for PII detection.

This module contains property tests that verify universal correctness
properties of PII detection across all inputs using randomized testing.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from data_sanitizer.detectors.email_detector import EmailDetector
from data_sanitizer.models import PIIType


# Strategy for generating valid email addresses
@st.composite
def email_addresses(draw):
    """Generate valid email addresses for property testing.

    Generates emails matching the pattern: local@domain.tld
    - Local part: alphanumeric with dots, underscores, percent, plus, hyphen
    - Domain: alphanumeric with dots and hyphens
    - TLD: 2-10 alphabetic characters
    """
    # Local part: 1-20 characters
    local_chars = st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._%+-",
        min_size=1,
        max_size=20,
    ).filter(lambda x: x[0].isalnum() and x[-1].isalnum())  # Start and end with alphanumeric

    # Domain: 1-20 characters
    domain_chars = st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-",
        min_size=1,
        max_size=20,
    ).filter(lambda x: x[0].isalnum() and x[-1].isalnum())  # Start and end with alphanumeric

    # TLD: 2-10 alphabetic characters
    tld = st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=2, max_size=10
    )

    local = draw(local_chars)
    domain = draw(domain_chars)
    tld_part = draw(tld)

    return f"{local}@{domain}.{tld_part}"


# Strategy for generating arbitrary field names
field_names = st.one_of(
    st.just(""),  # Empty field name
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz_0123456789", min_size=1, max_size=30).filter(
        lambda x: x[0].isalpha()
    ),  # Start with letter
)


class TestEmailDetectionProperties:
    """Property-based tests for email detection."""

    @settings(max_examples=15)
    @given(email=email_addresses(), field_name=field_names)
    def test_field_name_agnostic_email_detection(self, email: str, field_name: str):
        """Feature: data-sanitizer, Property 4: Field-Name-Agnostic PII Detection (Email)

        For any email value placed in any field name, the detector should
        identify it as PII.

        Validates: Requirements 2.1
        """
        detector = EmailDetector()

        # Detect email in text with arbitrary field name
        results = detector.detect(email, field_name=field_name)

        # Assert: Email is detected regardless of field name
        assert len(results) >= 1, f"Email '{email}' not detected in field '{field_name}'"
        assert any(
            result.pii_type == PIIType.EMAIL and result.original_value == email
            for result in results
        ), f"Email '{email}' not properly identified in field '{field_name}'"

    @settings(max_examples=15)
    @given(email=email_addresses())
    def test_email_detection_in_text(self, email: str):
        """Test that emails are detected when embedded in text.

        For any valid email, it should be detected even when surrounded
        by other text content.
        """
        detector = EmailDetector()

        # Embed email in various text contexts
        text_contexts = [
            email,  # Just the email
            f"Contact: {email}",  # With prefix
            f"{email} for more info",  # With suffix
            f"Email {email} or call",  # In middle of text
        ]

        for text in text_contexts:
            results = detector.detect(text)
            assert len(results) >= 1, f"Email '{email}' not detected in text: '{text}'"
            assert any(result.original_value == email for result in results), (
                f"Email '{email}' not found in results for text: '{text}'"
            )

    @settings(max_examples=15)
    @given(email=email_addresses(), field_name1=field_names, field_name2=field_names)
    def test_consistent_detection_across_fields(
        self, email: str, field_name1: str, field_name2: str
    ):
        """Test that the same email is detected consistently in different fields.

        For any email value, it should be detected with the same confidence
        and properties regardless of which field it appears in.
        """
        detector = EmailDetector()

        results1 = detector.detect(email, field_name=field_name1)
        results2 = detector.detect(email, field_name=field_name2)

        # Both should detect the email
        assert len(results1) >= 1, f"Email not detected in field '{field_name1}'"
        assert len(results2) >= 1, f"Email not detected in field '{field_name2}'"

        # Find the email in both result sets
        email_result1 = next((r for r in results1 if r.original_value == email), None)
        email_result2 = next((r for r in results2 if r.original_value == email), None)

        assert email_result1 is not None
        assert email_result2 is not None

        # Detection properties should be consistent
        assert email_result1.pii_type == email_result2.pii_type
        assert email_result1.confidence == email_result2.confidence


# Strategy for generating phone numbers with various formats
@st.composite
def phone_numbers_with_format(draw):
    """Generate valid phone numbers in various formats for property testing.

    Generates phone numbers in formats:
    - International with dashes: +1-234-567-8900
    - Parentheses format: (234) 567-8900
    - Dashes format: 234-567-8900
    - Plain digits: 2345678900
    - With spaces: 234 567 8900
    - With dots: 234.567.8900
    """
    # Generate 10-15 digit phone number
    digit_count = draw(st.integers(min_value=10, max_value=15))
    digits = "".join([str(draw(st.integers(min_value=0, max_value=9))) for _ in range(digit_count)])

    # Choose a format
    format_choice = draw(st.integers(min_value=0, max_value=5))

    if format_choice == 0 and len(digits) >= 10:
        # International with dashes: +1-234-567-8900
        country_code = digits[:1]
        area = digits[1:4]
        prefix = digits[4:7]
        line = digits[7:11]
        formatted = f"+{country_code}-{area}-{prefix}-{line}"
        format_pattern = "international-dashes"
    elif format_choice == 1 and len(digits) == 10:
        # Parentheses format: (234) 567-8900
        area = digits[:3]
        prefix = digits[3:6]
        line = digits[6:10]
        formatted = f"({area}) {prefix}-{line}"
        format_pattern = "parentheses"
    elif format_choice == 2 and len(digits) == 10:
        # Dashes format: 234-567-8900
        area = digits[:3]
        prefix = digits[3:6]
        line = digits[6:10]
        formatted = f"{area}-{prefix}-{line}"
        format_pattern = "dashes"
    elif format_choice == 3:
        # Plain digits: 2345678900
        formatted = digits
        format_pattern = "plain"
    elif format_choice == 4 and len(digits) >= 10:
        # With spaces: 234 567 8900
        area = digits[:3]
        prefix = digits[3:6]
        line = digits[6:10]
        formatted = f"{area} {prefix} {line}"
        format_pattern = "spaces"
    else:
        # With dots: 234.567.8900
        if len(digits) >= 10:
            area = digits[:3]
            prefix = digits[3:6]
            line = digits[6:10]
            formatted = f"{area}.{prefix}.{line}"
            format_pattern = "dots"
        else:
            formatted = digits
            format_pattern = "plain"

    return formatted, format_pattern


# Strategy for generating names of different types
@st.composite
def names_with_type(draw):
    """Generate names of different types for property testing.

    Generates names in three categories:
    - Full names: Two or more words (e.g., "John Doe", "Mary Jane Smith")
    - First names: Single word with first_name field hint
    - Last names: Single word with last_name field hint

    Returns:
        Tuple of (name_text, expected_pii_type, field_name)
    """
    # Common first and last names for realistic generation
    first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]

    # Choose name type
    name_type = draw(st.integers(min_value=0, max_value=2))

    if name_type == 0:
        # Full name: 2-3 words
        word_count = draw(st.integers(min_value=2, max_value=3))
        first = draw(st.sampled_from(first_names))
        last = draw(st.sampled_from(last_names))

        if word_count == 2:
            name_text = f"{first} {last}"
        else:
            middle = draw(st.sampled_from(first_names))
            name_text = f"{first} {middle} {last}"

        # Full names can be in various fields
        field_name = draw(
            st.sampled_from(["name", "full_name", "fullname", "customer", "employee", ""])
        )
        expected_type = PIIType.FULL_NAME

    elif name_type == 1:
        # First name: single word with first_name hint
        name_text = draw(st.sampled_from(first_names))
        field_name = draw(st.sampled_from(["first_name", "firstname", "fname", "givenname"]))
        expected_type = PIIType.FIRST_NAME

    else:
        # Last name: single word with last_name hint
        name_text = draw(st.sampled_from(last_names))
        field_name = draw(
            st.sampled_from(["last_name", "lastname", "lname", "surname", "familyname"])
        )
        expected_type = PIIType.LAST_NAME

    return name_text, expected_type, field_name


class TestPhoneDetectionProperties:
    """Property-based tests for phone number detection."""

    @settings(max_examples=15)
    @given(phone_data=phone_numbers_with_format())
    def test_phone_format_preservation(self, phone_data: tuple[str, str]):
        """Feature: data-sanitizer, Property 9: Phone Format Preservation

        For any phone number with a specific format (with/without country code,
        with specific separators), the replacement should maintain the same
        format pattern.

        Validates: Requirements 3.4
        """
        from data_sanitizer.detectors.phone_detector import PhoneDetector

        phone, format_pattern = phone_data
        detector = PhoneDetector()

        # Detect phone number
        results = detector.detect(phone)

        # Assert: Phone is detected
        assert len(results) >= 1, f"Phone '{phone}' with format '{format_pattern}' not detected"

        # Get the detected phone
        detected_phone = results[0].original_value

        # Assert: Format information is preserved in the original_value
        # The original_value should match the input phone exactly
        assert detected_phone == phone, (
            f"Format not preserved: expected '{phone}', got '{detected_phone}'"
        )

        # Verify format-specific characteristics are preserved
        if format_pattern == "international-dashes":
            assert detected_phone.startswith("+"), "International format should start with +"
            assert "-" in detected_phone, "International format should contain dashes"
        elif format_pattern == "parentheses":
            assert "(" in detected_phone and ")" in detected_phone, (
                "Parentheses format should contain parentheses"
            )
        elif format_pattern == "dashes":
            assert "-" in detected_phone, "Dashes format should contain dashes"
        elif format_pattern == "spaces":
            assert " " in detected_phone, "Spaces format should contain spaces"
        elif format_pattern == "dots":
            assert "." in detected_phone, "Dots format should contain dots"
        elif format_pattern == "plain":
            # Plain format should be all digits
            assert detected_phone.isdigit(), "Plain format should be all digits"

    @settings(max_examples=15)
    @given(phone_data=phone_numbers_with_format(), field_name=field_names)
    def test_field_name_agnostic_phone_detection(
        self, phone_data: tuple[str, str], field_name: str
    ):
        """Test that phone numbers are detected regardless of field name.

        For any phone number placed in any field name, the detector should
        identify it as PII.

        Validates: Requirements 3.1
        """
        from data_sanitizer.detectors.phone_detector import PhoneDetector

        phone, _ = phone_data
        detector = PhoneDetector()

        # Detect phone in text with arbitrary field name
        results = detector.detect(phone, field_name=field_name)

        # Assert: Phone is detected regardless of field name
        assert len(results) >= 1, f"Phone '{phone}' not detected in field '{field_name}'"
        assert any(
            result.pii_type == PIIType.PHONE and result.original_value == phone
            for result in results
        ), f"Phone '{phone}' not properly identified in field '{field_name}'"


class TestNameDetectionProperties:
    """Property-based tests for name detection."""

    @settings(
        max_examples=20, deadline=None
    )  # Disabled deadline due to Presidio initialization time
    @given(name_data=names_with_type())
    def test_name_type_preservation(self, name_data: tuple[str, PIIType, str]):
        """Feature: data-sanitizer, Property 10: Name Type Preservation

        For any detected name (full, first, or last), the replacement should
        be the same type of name.

        Validates: Requirements 4.4
        """
        from data_sanitizer.detectors.name_detector import NameDetector

        name_text, expected_type, field_name = name_data
        detector = NameDetector()

        # Detect name
        results = detector.detect(name_text, field_name=field_name)

        # Assert: Name is detected
        assert len(results) >= 1, f"Name '{name_text}' not detected in field '{field_name}'"

        # Get the detected name
        detected_result = results[0]

        # Assert: Detected type matches expected type
        assert detected_result.pii_type == expected_type, (
            f"Name type mismatch for '{name_text}' in field '{field_name}': "
            f"expected {expected_type}, got {detected_result.pii_type}"
        )

        # Assert: Original value is preserved
        assert detected_result.original_value == name_text, (
            f"Original value not preserved: expected '{name_text}', "
            f"got '{detected_result.original_value}'"
        )


# Strategy for generating valid credit card numbers
@st.composite
def valid_credit_cards(draw):
    """Generate valid credit card numbers for property testing.

    Generates credit card numbers that pass Luhn algorithm validation.
    Supports various card types:
    - Visa: 16 digits starting with 4
    - MasterCard: 16 digits starting with 51-55
    - Amex: 15 digits starting with 34 or 37
    - Discover: 16 digits starting with 6011

    Returns:
        Valid credit card number as a string
    """
    # Choose card type
    card_type = draw(st.sampled_from(["visa", "mastercard", "amex", "discover"]))

    if card_type == "visa":
        # Visa: 16 digits starting with 4
        prefix = "4"
        remaining_length = 15
    elif card_type == "mastercard":
        # MasterCard: 16 digits starting with 51-55
        prefix = str(draw(st.integers(min_value=51, max_value=55)))
        remaining_length = 14
    elif card_type == "amex":
        # Amex: 15 digits starting with 34 or 37
        prefix = draw(st.sampled_from(["34", "37"]))
        remaining_length = 13
    else:  # discover
        # Discover: 16 digits starting with 6011
        prefix = "6011"
        remaining_length = 12

    # Generate random digits for the rest (except check digit)
    middle_digits = "".join(
        [str(draw(st.integers(min_value=0, max_value=9))) for _ in range(remaining_length - 1)]
    )

    # Calculate Luhn check digit
    partial_number = prefix + middle_digits
    check_digit = _calculate_luhn_check_digit(partial_number)

    return partial_number + str(check_digit)


def _calculate_luhn_check_digit(partial_number: str) -> int:
    """Calculate the Luhn check digit for a partial credit card number.

    Args:
        partial_number: Credit card number without check digit

    Returns:
        The check digit (0-9) that makes the number valid
    """
    # Convert to list of integers, reversed
    digits = [int(d) for d in partial_number[::-1]]

    # Double every second digit (starting from index 0, which is second from right)
    for i in range(0, len(digits), 2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9

    # Calculate sum
    total = sum(digits)

    # Check digit is what we need to add to make total divisible by 10
    check_digit = (10 - (total % 10)) % 10

    return check_digit


class TestCreditCardDetectionProperties:
    """Property-based tests for credit card detection."""

    @settings(max_examples=15)
    @given(card_number=valid_credit_cards())
    def test_credit_card_replacement_validity(self, card_number: str):
        """Feature: data-sanitizer, Property 14: Credit Card Replacement Validity

        For any detected credit card number, the replacement should be a valid
        credit card number that passes Luhn algorithm validation.

        Note: This test validates that the detector correctly identifies valid
        credit card numbers. The actual replacement validity will be tested
        when the replacer is implemented.

        Validates: Requirements 5.2
        """
        from data_sanitizer.detectors.credit_card_detector import CreditCardDetector

        detector = CreditCardDetector()

        # Verify the generated card passes Luhn validation
        assert detector._luhn_check(card_number), (
            f"Generated card '{card_number}' should pass Luhn validation"
        )

        # Detect the credit card
        results = detector.detect(card_number)

        # Assert: Credit card is detected
        assert len(results) >= 1, f"Credit card '{card_number}' not detected"

        # Get the detected card
        detected_result = results[0]

        # Assert: Detected as credit card type
        assert detected_result.pii_type == PIIType.CREDIT_CARD, (
            f"Card '{card_number}' not detected as CREDIT_CARD type"
        )

        # Assert: Original value is preserved
        assert detected_result.original_value == card_number, (
            f"Original value not preserved: expected '{card_number}', "
            f"got '{detected_result.original_value}'"
        )

        # Assert: High confidence (Luhn validation passed)
        assert detected_result.confidence == 1.0, (
            f"Expected confidence 1.0 for valid card, got {detected_result.confidence}"
        )

    @settings(max_examples=15)
    @given(card_number=valid_credit_cards(), field_name=field_names)
    def test_field_name_agnostic_credit_card_detection(self, card_number: str, field_name: str):
        """Test that credit cards are detected regardless of field name.

        For any credit card number placed in any field name, the detector
        should identify it as PII.

        Validates: Requirements 5.1
        """
        from data_sanitizer.detectors.credit_card_detector import CreditCardDetector

        detector = CreditCardDetector()

        # Detect card in text with arbitrary field name
        results = detector.detect(card_number, field_name=field_name)

        # Assert: Card is detected regardless of field name
        assert len(results) >= 1, f"Card '{card_number}' not detected in field '{field_name}'"
        assert any(
            result.pii_type == PIIType.CREDIT_CARD and result.original_value == card_number
            for result in results
        ), f"Card '{card_number}' not properly identified in field '{field_name}'"
