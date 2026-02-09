"""Unit tests for data models.

Tests for PIIType enum, DetectionResult, SanitizationResult, and SanitizerConfig.
"""

import pytest

from data_sanitizer.models import (
    DetectionResult,
    PIIType,
    SanitizationResult,
    SanitizerConfig,
)


class TestPIIType:
    """Tests for PIIType enum."""

    def test_enum_values(self) -> None:
        """Test that all expected PII types exist with correct values."""
        assert PIIType.EMAIL.value == "email"
        assert PIIType.PHONE.value == "phone"
        assert PIIType.FULL_NAME.value == "full_name"
        assert PIIType.FIRST_NAME.value == "first_name"
        assert PIIType.LAST_NAME.value == "last_name"
        assert PIIType.CREDIT_CARD.value == "credit_card"

    def test_enum_string_representation(self) -> None:
        """Test string representation of enum values."""
        assert str(PIIType.EMAIL) == "PIIType.EMAIL"
        assert str(PIIType.PHONE) == "PIIType.PHONE"
        assert str(PIIType.FULL_NAME) == "PIIType.FULL_NAME"

    def test_enum_equality(self) -> None:
        """Test enum equality comparison."""
        assert PIIType.EMAIL == PIIType.EMAIL
        assert PIIType.EMAIL != PIIType.PHONE

    def test_enum_membership(self) -> None:
        """Test that all PII types are members of the enum."""
        all_types = list(PIIType)
        assert PIIType.EMAIL in all_types
        assert PIIType.PHONE in all_types
        assert PIIType.FULL_NAME in all_types
        assert PIIType.FIRST_NAME in all_types
        assert PIIType.LAST_NAME in all_types
        assert PIIType.CREDIT_CARD in all_types
        assert len(all_types) == 6


class TestDetectionResult:
    """Tests for DetectionResult dataclass."""

    def test_initialization_with_required_fields(self) -> None:
        """Test initialization with only required fields."""
        result = DetectionResult(
            pii_type=PIIType.EMAIL, original_value="test@example.com", confidence=0.95
        )

        assert result.pii_type == PIIType.EMAIL
        assert result.original_value == "test@example.com"
        assert result.confidence == 0.95
        assert result.start_pos == 0
        assert result.end_pos == 0

    def test_initialization_with_all_fields(self) -> None:
        """Test initialization with all fields including optional ones."""
        result = DetectionResult(
            pii_type=PIIType.PHONE,
            original_value="+1-555-123-4567",
            confidence=0.99,
            start_pos=10,
            end_pos=26,
        )

        assert result.pii_type == PIIType.PHONE
        assert result.original_value == "+1-555-123-4567"
        assert result.confidence == 0.99
        assert result.start_pos == 10
        assert result.end_pos == 26

    def test_field_access(self) -> None:
        """Test accessing individual fields."""
        result = DetectionResult(
            pii_type=PIIType.FULL_NAME,
            original_value="John Doe",
            confidence=0.85,
            start_pos=5,
            end_pos=13,
        )

        # Test field access
        assert result.pii_type.value == "full_name"
        assert len(result.original_value) == 8
        assert result.confidence < 1.0
        assert result.end_pos > result.start_pos

    def test_equality(self) -> None:
        """Test dataclass equality comparison."""
        result1 = DetectionResult(
            pii_type=PIIType.EMAIL,
            original_value="test@example.com",
            confidence=0.95,
            start_pos=0,
            end_pos=16,
        )

        result2 = DetectionResult(
            pii_type=PIIType.EMAIL,
            original_value="test@example.com",
            confidence=0.95,
            start_pos=0,
            end_pos=16,
        )

        result3 = DetectionResult(
            pii_type=PIIType.EMAIL,
            original_value="different@example.com",
            confidence=0.95,
            start_pos=0,
            end_pos=16,
        )

        assert result1 == result2
        assert result1 != result3

    def test_hashing(self) -> None:
        """Test that DetectionResult instances are not hashable by default."""
        result = DetectionResult(
            pii_type=PIIType.EMAIL, original_value="test@example.com", confidence=0.95
        )

        # Dataclasses are not hashable by default (unless frozen=True)
        # This test documents that behavior
        with pytest.raises(TypeError, match="unhashable type"):
            hash(result)


class TestSanitizationResult:
    """Tests for SanitizationResult dataclass."""

    def test_initialization_success_case(self) -> None:
        """Test initialization for successful sanitization."""
        result = SanitizationResult(
            success=True, records_processed=100, pii_fields_detected=25, pii_replacements_made=25
        )

        assert result.success is True
        assert result.records_processed == 100
        assert result.pii_fields_detected == 25
        assert result.pii_replacements_made == 25
        assert result.error_message is None

    def test_initialization_failure_case(self) -> None:
        """Test initialization for failed sanitization."""
        result = SanitizationResult(
            success=False,
            records_processed=0,
            pii_fields_detected=0,
            pii_replacements_made=0,
            error_message="File not found",
        )

        assert result.success is False
        assert result.records_processed == 0
        assert result.pii_fields_detected == 0
        assert result.pii_replacements_made == 0
        assert result.error_message == "File not found"

    def test_field_access(self) -> None:
        """Test accessing individual fields."""
        result = SanitizationResult(
            success=True, records_processed=50, pii_fields_detected=10, pii_replacements_made=10
        )

        # Test field access and calculations
        assert result.records_processed > 0
        assert result.pii_fields_detected <= result.records_processed
        assert result.pii_replacements_made == result.pii_fields_detected

    def test_equality(self) -> None:
        """Test dataclass equality comparison."""
        result1 = SanitizationResult(
            success=True, records_processed=100, pii_fields_detected=25, pii_replacements_made=25
        )

        result2 = SanitizationResult(
            success=True, records_processed=100, pii_fields_detected=25, pii_replacements_made=25
        )

        result3 = SanitizationResult(
            success=True, records_processed=50, pii_fields_detected=10, pii_replacements_made=10
        )

        assert result1 == result2
        assert result1 != result3

    def test_hashing(self) -> None:
        """Test that SanitizationResult instances are not hashable by default."""
        result = SanitizationResult(
            success=True, records_processed=100, pii_fields_detected=25, pii_replacements_made=25
        )

        # Dataclasses are not hashable by default (unless frozen=True)
        # This test documents that behavior
        with pytest.raises(TypeError, match="unhashable type"):
            hash(result)


class TestSanitizerConfig:
    """Tests for SanitizerConfig dataclass."""

    def test_initialization_with_required_fields(self) -> None:
        """Test initialization with only required fields."""
        config = SanitizerConfig(enabled_detectors=["email", "phone"])

        assert config.enabled_detectors == ["email", "phone"]
        assert config.faker_seed is None
        assert config.verbose is False

    def test_initialization_with_all_fields(self) -> None:
        """Test initialization with all fields."""
        config = SanitizerConfig(
            enabled_detectors=["email", "phone", "name", "credit_card"], faker_seed=42, verbose=True
        )

        assert config.enabled_detectors == ["email", "phone", "name", "credit_card"]
        assert config.faker_seed == 42
        assert config.verbose is True

    def test_field_access(self) -> None:
        """Test accessing individual fields."""
        config = SanitizerConfig(enabled_detectors=["email"], faker_seed=123)

        # Test field access
        assert len(config.enabled_detectors) == 1
        assert "email" in config.enabled_detectors
        assert config.faker_seed > 0
        assert not config.verbose

    def test_empty_detectors_list(self) -> None:
        """Test configuration with empty detectors list."""
        config = SanitizerConfig(enabled_detectors=[])

        assert config.enabled_detectors == []
        assert len(config.enabled_detectors) == 0

    def test_equality(self) -> None:
        """Test dataclass equality comparison."""
        config1 = SanitizerConfig(enabled_detectors=["email", "phone"], faker_seed=42, verbose=True)

        config2 = SanitizerConfig(enabled_detectors=["email", "phone"], faker_seed=42, verbose=True)

        config3 = SanitizerConfig(enabled_detectors=["email"], faker_seed=42, verbose=True)

        assert config1 == config2
        assert config1 != config3

    def test_hashing(self) -> None:
        """Test that SanitizerConfig instances can be hashed."""
        # Note: Lists are not hashable, so we need to handle this carefully
        # This test verifies the behavior when trying to hash
        config = SanitizerConfig(enabled_detectors=["email", "phone"], faker_seed=42)

        # Dataclasses with mutable fields (lists) are not hashable by default
        # This test documents that behavior
        with pytest.raises(TypeError):
            hash(config)
