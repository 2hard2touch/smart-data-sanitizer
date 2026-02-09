"""Data models for the Smart Data Sanitizer.

This module defines the core data structures used throughout the sanitizer,
including PII types, detection results, sanitization results, and configuration.
"""

from dataclasses import dataclass
from enum import Enum


class PIIType(Enum):
    """Enumeration of supported PII types.

    Attributes:
        EMAIL: Email address (e.g., user@example.com)
        PHONE: Phone number in various formats
        FULL_NAME: Full name with first and last name
        FIRST_NAME: First name only
        LAST_NAME: Last name only
        CREDIT_CARD: Credit card number
    """

    EMAIL = "email"
    PHONE = "phone"
    FULL_NAME = "full_name"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    CREDIT_CARD = "credit_card"


@dataclass
class DetectionResult:
    """Result of PII detection in a text field.

    Attributes:
        pii_type: The type of PII detected
        original_value: The original PII value found in the text
        confidence: Confidence score of the detection (0.0 to 1.0)
        start_pos: Starting position of the PII in the text (default: 0)
        end_pos: Ending position of the PII in the text (default: 0)
    """

    pii_type: PIIType
    original_value: str
    confidence: float
    start_pos: int = 0
    end_pos: int = 0


@dataclass
class SanitizationResult:
    """Result of a sanitization operation.

    Attributes:
        success: Whether the sanitization completed successfully
        records_processed: Number of records processed
        pii_fields_detected: Number of fields containing PII
        pii_replacements_made: Number of PII values replaced
        error_message: Error message if sanitization failed (None if successful)
    """

    success: bool
    records_processed: int
    pii_fields_detected: int
    pii_replacements_made: int
    error_message: str | None = None


@dataclass
class SanitizerConfig:
    """Configuration for the sanitizer.

    Attributes:
        enabled_detectors: List of detector names to enable
        faker_seed: Optional seed for Faker to ensure reproducible results (None for random)
        verbose: Whether to enable verbose logging (default: False)
    """

    enabled_detectors: list[str]
    faker_seed: int | None = None
    verbose: bool = False
