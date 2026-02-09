"""Name detector for identifying person names in text.

This module implements name detection using Presidio's PERSON entity recognizer
to identify full names, first names, and last names in text fields.
"""

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

from data_sanitizer.detectors.base import Detector
from data_sanitizer.models import DetectionResult, PIIType


class NameDetector(Detector):
    """Detector for person names.

    This detector uses Presidio's PERSON entity recognizer to identify names
    in text. It distinguishes between full names (2+ words), first names, and
    last names based on the text content and field name hints.

    The detector captures case information (Title Case, lowercase, UPPERCASE)
    to enable case-preserving replacement.

    Field name hints that influence detection:
    - "first_name", "firstname", "fname" -> FIRST_NAME
    - "last_name", "lastname", "lname", "surname" -> LAST_NAME
    - "name", "full_name", "fullname" -> context-dependent

    Attributes:
        analyzer: Presidio AnalyzerEngine for PII detection
    """

    def __init__(self) -> None:
        """Initialize the name detector with Presidio analyzer."""
        # Create NLP engine provider with spaCy
        provider = NlpEngineProvider()
        nlp_engine = provider.create_engine()

        # Create analyzer with default recognizers
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

    def detect(self, text: str, field_name: str = "") -> list[DetectionResult]:
        """Detect person names in the given text.

        This method uses Presidio to detect PERSON entities and classifies them
        as full names, first names, or last names based on word count and field
        name hints.

        Args:
            text: The text to analyze for person names
            field_name: Optional field name that provides hints about name type

        Returns:
            A list of DetectionResult objects, one for each name detected.
            Returns an empty list if no names are found.

        Example:
            >>> detector = NameDetector()
            >>> results = detector.detect("John Doe", "full_name")
            >>> len(results)
            1
            >>> results[0].pii_type
            PIIType.FULL_NAME
        """
        if not isinstance(text, str) or not text.strip():
            return []

        results = []

        # Analyze text with Presidio
        analyzer_results = self.analyzer.analyze(text=text, language="en", entities=["PERSON"])

        # Process each detected person entity
        for result in analyzer_results:
            name_text = text[result.start : result.end]

            # Determine name type based on word count and field hints
            pii_type = self._determine_name_type(name_text, field_name)

            detection = DetectionResult(
                pii_type=pii_type,
                original_value=name_text,
                confidence=result.score,
                start_pos=result.start,
                end_pos=result.end,
            )
            results.append(detection)

        return results

    def _determine_name_type(self, name_text: str, field_name: str) -> PIIType:
        """Determine whether a name is a full name, first name, or last name.

        This method uses word count and field name hints to classify the name type.

        Args:
            name_text: The detected name text
            field_name: The field name that may contain hints

        Returns:
            PIIType indicating FULL_NAME, FIRST_NAME, or LAST_NAME
        """
        # Normalize field name for comparison
        field_lower = field_name.lower().replace("_", "").replace("-", "")

        # Check for full name hints
        full_name_hints = ["fullname", "name"]
        if any(hint == field_lower for hint in full_name_hints):
            return PIIType.FULL_NAME

        # Check for first name hints
        first_name_hints = ["firstname", "fname", "givenname", "first"]
        if any(hint == field_lower for hint in first_name_hints):
            return PIIType.FIRST_NAME

        # Check for last name hints
        last_name_hints = ["lastname", "lname", "surname", "familyname", "last"]
        if any(hint == field_lower for hint in last_name_hints):
            return PIIType.LAST_NAME

        # Count words in the name (split by whitespace)
        words = name_text.split()

        # If 2+ words, it's a full name
        if len(words) >= 2:
            return PIIType.FULL_NAME

        # Single word with no field hints - default to FIRST_NAME
        # (This is a reasonable default as single names are more commonly first names)
        return PIIType.FIRST_NAME
