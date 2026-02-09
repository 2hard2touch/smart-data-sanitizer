"""Base class for PII detectors.

This module defines the abstract Detector base class that all concrete
PII detectors must implement. It provides a common interface for detecting
PII in text fields.
"""

from abc import ABC, abstractmethod

from data_sanitizer.models import DetectionResult


class Detector(ABC):
    """Abstract base class for PII detectors.

    All concrete detector implementations must inherit from this class
    and implement the detect() method. This ensures a consistent interface
    for PII detection across different detection strategies.

    The detector uses a plugin-based architecture to support extensibility,
    allowing new detection strategies (including future LLM-based detection)
    to be added without modifying core logic.
    """

    @abstractmethod
    def detect(self, text: str, field_name: str = "") -> list[DetectionResult]:
        """Detect PII in the given text.

        This method analyzes the provided text and returns a list of all
        detected PII instances. The field_name parameter provides additional
        context that can be used to improve detection accuracy (e.g., a field
        named "email" is more likely to contain an email address).

        Args:
            text: The text to analyze for PII. Can be any string value from
                a JSON field.
            field_name: Optional name of the field being analyzed. This provides
                context for detection (e.g., "first_name", "email", "phone").
                Defaults to empty string if not provided.

        Returns:
            A list of DetectionResult objects, one for each PII instance detected
            in the text. Returns an empty list if no PII is detected.

            Each DetectionResult contains:
            - pii_type: The type of PII detected (EMAIL, PHONE, etc.)
            - original_value: The actual PII value found
            - confidence: Detection confidence score (0.0 to 1.0)
            - start_pos: Starting character position in the text
            - end_pos: Ending character position in the text

        Raises:
            NotImplementedError: If a concrete detector does not implement
                this method.

        Example:
            >>> detector = EmailDetector()
            >>> results = detector.detect("Contact: john@example.com", "contact_info")
            >>> len(results)
            1
            >>> results[0].pii_type
            PIIType.EMAIL
        """
        pass
