"""Email detector for identifying email addresses in text.

This module implements email detection using regex patterns to identify
email addresses regardless of the field name they appear in.
"""

import re

from data_sanitizer.detectors.base import Detector
from data_sanitizer.models import DetectionResult, PIIType


class EmailDetector(Detector):
    """Detector for email addresses.

    This detector uses a regex pattern to identify email addresses in text.
    It detects emails regardless of the field name, supporting the requirement
    for field-name-agnostic PII detection.

    The regex pattern matches standard email formats including:
    - Standard emails: user@example.com
    - Emails with special characters: user+tag@example.co.uk
    - Emails with dots and underscores: first.last_name@domain.com

    Attributes:
        EMAIL_PATTERN: Compiled regex pattern for email detection
    """

    # Regex pattern for email detection
    # Matches: local-part@domain.tld
    # - Local part: alphanumeric, dots, underscores, percent, plus, hyphen
    # - Domain: alphanumeric, dots, hyphens
    # - TLD: 2+ alphabetic characters
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    def detect(self, text: str, field_name: str = "") -> list[DetectionResult]:
        """Detect email addresses in the given text.

        This method scans the text for email addresses using regex pattern
        matching. It returns all detected emails with their positions and
        a confidence score of 1.0 (regex-based detection is deterministic).

        Args:
            text: The text to analyze for email addresses
            field_name: Optional field name (not used for email detection,
                as emails are detected regardless of field name)

        Returns:
            A list of DetectionResult objects, one for each email detected.
            Returns an empty list if no emails are found.

        Example:
            >>> detector = EmailDetector()
            >>> results = detector.detect("Contact john@example.com for info")
            >>> len(results)
            1
            >>> results[0].original_value
            'john@example.com'
            >>> results[0].pii_type
            PIIType.EMAIL
        """
        if not isinstance(text, str):
            return []

        results = []

        # Find all email matches in the text
        for match in self.EMAIL_PATTERN.finditer(text):
            email = match.group(0)
            start_pos = match.start()
            end_pos = match.end()

            # Create detection result with high confidence (regex is deterministic)
            result = DetectionResult(
                pii_type=PIIType.EMAIL,
                original_value=email,
                confidence=1.0,
                start_pos=start_pos,
                end_pos=end_pos,
            )
            results.append(result)

        return results
