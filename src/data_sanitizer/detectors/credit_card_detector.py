"""Credit card detector for identifying credit card numbers in text.

This module implements credit card detection using regex patterns and
Luhn algorithm validation to identify valid credit card numbers regardless
of the field name they appear in.
"""

import re

from data_sanitizer.detectors.base import Detector
from data_sanitizer.models import DetectionResult, PIIType


class CreditCardDetector(Detector):
    """Detector for credit card numbers.

    This detector uses regex patterns to identify potential credit card numbers
    (13-19 digit sequences with optional spaces/dashes) and validates them using
    the Luhn algorithm. Only numbers that pass Luhn validation are detected as PII.

    The detector supports various formats:
    - No separators: 4532123456789010
    - Spaces: 4532 1234 5678 9010
    - Dashes: 4532-1234-5678-9010
    - Mixed: 4532 1234-5678 9010

    Attributes:
        CARD_PATTERN: Compiled regex pattern for credit card detection
    """

    # Regex pattern for credit card detection
    # Matches: 13-19 digits with optional spaces or dashes
    # Supports both 16-digit cards (4-4-4-4) and 15-digit Amex (4-6-5)
    CARD_PATTERN = re.compile(
        r"\b(?:\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{3,7}|\d{4}[\s\-]?\d{6}[\s\-]?\d{5})\b"
    )

    def detect(self, text: str, field_name: str = "") -> list[DetectionResult]:
        """Detect credit card numbers in the given text.

        This method scans the text for potential credit card numbers using regex
        pattern matching, then validates each candidate using the Luhn algorithm.
        Only numbers that pass Luhn validation are returned as detected PII.

        Args:
            text: The text to analyze for credit card numbers
            field_name: Optional field name (not used for credit card detection,
                as cards are detected regardless of field name)

        Returns:
            A list of DetectionResult objects, one for each valid credit card detected.
            Returns an empty list if no valid cards are found.

        Example:
            >>> detector = CreditCardDetector()
            >>> results = detector.detect("Card: 4532-1234-5678-9010")
            >>> len(results)
            1
            >>> results[0].pii_type
            PIIType.CREDIT_CARD
        """
        if not isinstance(text, str):
            return []

        results = []

        # Find all potential credit card matches in the text
        for match in self.CARD_PATTERN.finditer(text):
            card_with_separators = match.group(0)
            start_pos = match.start()
            end_pos = match.end()

            # Extract digits only for Luhn validation
            digits_only = re.sub(r"[\s\-]", "", card_with_separators)

            # Validate length (13-19 digits)
            if not (13 <= len(digits_only) <= 19):
                continue

            # Validate using Luhn algorithm
            if not self._luhn_check(digits_only):
                continue

            # Create detection result with high confidence (Luhn validation passed)
            result = DetectionResult(
                pii_type=PIIType.CREDIT_CARD,
                original_value=card_with_separators,
                confidence=1.0,
                start_pos=start_pos,
                end_pos=end_pos,
            )
            results.append(result)

        return results

    def _luhn_check(self, card_number: str) -> bool:
        """Validate a credit card number using the Luhn algorithm.

        The Luhn algorithm (also known as the modulus 10 algorithm) is a checksum
        formula used to validate credit card numbers. It works as follows:
        1. Starting from the rightmost digit, moving left, double every second digit
        2. If doubling results in a two-digit number, add the digits together
        3. Sum all the digits
        4. If the total modulo 10 is 0, the number is valid

        Args:
            card_number: Credit card number as a string of digits (no separators)

        Returns:
            True if the card number passes Luhn validation, False otherwise

        Example:
            >>> detector = CreditCardDetector()
            >>> detector._luhn_check("4532015112830366")
            True
            >>> detector._luhn_check("1234567890123456")
            False
        """
        if not card_number.isdigit():
            return False

        # Convert to list of integers, reversed for easier processing
        digits = [int(d) for d in card_number[::-1]]

        # Double every second digit (starting from index 1, which is second from right)
        for i in range(1, len(digits), 2):
            digits[i] *= 2
            # If doubling results in two digits, subtract 9 (equivalent to adding digits)
            if digits[i] > 9:
                digits[i] -= 9

        # Sum all digits and check if divisible by 10
        total = sum(digits)
        return total % 10 == 0
