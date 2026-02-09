"""Phone number detector for identifying phone numbers in text.

This module implements phone number detection using regex patterns to identify
phone numbers in various formats regardless of the field name they appear in.
"""

import re

from data_sanitizer.detectors.base import Detector
from data_sanitizer.models import DetectionResult, PIIType


class PhoneDetector(Detector):
    """Detector for phone numbers.

    This detector uses regex patterns to identify phone numbers in various formats.
    It detects phones regardless of the field name, supporting the requirement
    for field-name-agnostic PII detection.

    Supported formats:
    - International with dashes: +1-234-567-8900
    - Parentheses format: (234) 567-8900
    - Dashes format: 234-567-8900
    - Plain digits: 2345678900
    - With spaces: 234 567 8900
    - International with spaces: +1 234 567 8900

    The detector validates that the number contains 10-15 digits total.

    Attributes:
        PHONE_PATTERNS: List of compiled regex patterns for phone detection
    """

    # Regex patterns for various phone number formats
    # Pattern 1: International format with dashes (+1-234-567-8900)
    # Pattern 2: Parentheses format ((234) 567-8900)
    # Pattern 3: Dashes format (234-567-8900)
    # Pattern 4: Plain digits (2345678900)
    # Pattern 5: With spaces (234 567 8900)
    PHONE_PATTERNS = [
        re.compile(r"\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}"),
        re.compile(r"\(\d{3}\)\s?\d{3}[-.\s]?\d{4}"),
        re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b"),
        re.compile(r"\b\d{10,15}\b"),
    ]

    def detect(self, text: str, field_name: str = "") -> list[DetectionResult]:
        """Detect phone numbers in the given text.

        This method scans the text for phone numbers using multiple regex patterns
        to support various formats. It validates that detected numbers have 10-15
        digits and returns all matches with their positions.

        Args:
            text: The text to analyze for phone numbers
            field_name: Optional field name (not used for phone detection,
                as phones are detected regardless of field name)

        Returns:
            A list of DetectionResult objects, one for each phone number detected.
            Returns an empty list if no phone numbers are found.

        Example:
            >>> detector = PhoneDetector()
            >>> results = detector.detect("Call +1-555-123-4567 for info")
            >>> len(results)
            1
            >>> results[0].original_value
            '+1-555-123-4567'
            >>> results[0].pii_type
            PIIType.PHONE
        """
        if not isinstance(text, str):
            return []

        # Collect all potential matches from all patterns
        all_matches = []
        for pattern in self.PHONE_PATTERNS:
            for match in pattern.finditer(text):
                phone = match.group(0)
                start_pos = match.start()
                end_pos = match.end()

                # Validate digit count (10-15 digits)
                digit_count = sum(c.isdigit() for c in phone)
                if digit_count < 10 or digit_count > 15:
                    continue

                all_matches.append((start_pos, end_pos, phone))

        # Remove overlapping matches, keeping the longest ones
        # Sort by start position, then by length (descending)
        all_matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))

        results = []
        used_ranges = []

        for start_pos, end_pos, phone in all_matches:
            # Check if this match overlaps with any already selected match
            overlaps = False
            for used_start, used_end in used_ranges:
                # Check for overlap
                if not (end_pos <= used_start or start_pos >= used_end):
                    overlaps = True
                    break

            if not overlaps:
                # Add this match
                used_ranges.append((start_pos, end_pos))
                result = DetectionResult(
                    pii_type=PIIType.PHONE,
                    original_value=phone,
                    confidence=1.0,
                    start_pos=start_pos,
                    end_pos=end_pos,
                )
                results.append(result)

        # Sort results by start position for consistent ordering
        results.sort(key=lambda x: x.start_pos)

        return results
