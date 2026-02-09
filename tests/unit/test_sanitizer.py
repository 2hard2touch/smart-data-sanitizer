"""Unit tests for the Sanitizer orchestrator."""

import json
import tempfile
from pathlib import Path

import pytest

from data_sanitizer.detectors.base import Detector
from data_sanitizer.exceptions import (
    FileNotFoundError,
    JSONParseError,
)
from data_sanitizer.models import DetectionResult, PIIType
from data_sanitizer.replacer import Replacer
from data_sanitizer.sanitizer import Sanitizer


class MockDetector(Detector):
    """Mock detector for testing that detects a specific pattern."""

    def __init__(self, pattern: str, pii_type: PIIType):
        self.pattern = pattern
        self.pii_type = pii_type

    def detect(self, text: str, field_name: str = "") -> list[DetectionResult]:
        """Detect the mock pattern in text."""
        if self.pattern in text:
            start = text.find(self.pattern)
            return [
                DetectionResult(
                    pii_type=self.pii_type,
                    original_value=self.pattern,
                    confidence=1.0,
                    start_pos=start,
                    end_pos=start + len(self.pattern),
                )
            ]
        return []


class TestSanitizerInit:
    """Tests for Sanitizer initialization."""

    def test_init_with_detectors_and_replacer(self):
        """Test sanitizer initializes with detectors and replacer."""
        detectors = [MockDetector("test", PIIType.EMAIL)]
        replacer = Replacer(seed=42)

        sanitizer = Sanitizer(detectors, replacer)

        assert sanitizer._detectors == detectors
        assert sanitizer._replacer == replacer


class TestSanitizeValue:
    """Tests for sanitize_value method."""

    def test_sanitize_string_with_pii(self):
        """Test sanitizing a string containing PII."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        result = sanitizer.sanitize_value("This is secret data", "field")

        assert "secret" not in result
        assert "This is" in result
        assert "data" in result

    def test_sanitize_string_without_pii(self):
        """Test sanitizing a string without PII returns unchanged."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        result = sanitizer.sanitize_value("This is clean data", "field")

        assert result == "This is clean data"

    def test_sanitize_integer(self):
        """Test sanitizing an integer returns unchanged."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        result = sanitizer.sanitize_value(42, "age")

        assert result == 42

    def test_sanitize_float(self):
        """Test sanitizing a float returns unchanged."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        result = sanitizer.sanitize_value(3.14, "score")

        assert result == 3.14

    def test_sanitize_boolean(self):
        """Test sanitizing a boolean returns unchanged."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        result = sanitizer.sanitize_value(True, "active")

        assert result is True

    def test_sanitize_none(self):
        """Test sanitizing None returns unchanged."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        result = sanitizer.sanitize_value(None, "field")

        assert result is None

    def test_sanitize_nested_dict(self):
        """Test sanitizing a nested dictionary."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        value = {"user": {"name": "secret", "age": 30}}

        result = sanitizer.sanitize_value(value, "data")

        assert "secret" not in result["user"]["name"]
        assert result["user"]["age"] == 30

    def test_sanitize_list(self):
        """Test sanitizing a list."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        value = ["secret", "clean", 42]

        result = sanitizer.sanitize_value(value, "items")

        assert "secret" not in result[0]
        assert result[1] == "clean"
        assert result[2] == 42

    def test_sanitize_list_of_dicts(self):
        """Test sanitizing a list of dictionaries."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        value = [{"name": "secret", "id": 1}, {"name": "clean", "id": 2}]

        result = sanitizer.sanitize_value(value, "users")

        assert "secret" not in result[0]["name"]
        assert result[0]["id"] == 1
        assert result[1]["name"] == "clean"
        assert result[1]["id"] == 2


class TestSanitizeRecords:
    """Tests for sanitize_records method."""

    def test_sanitize_single_record(self):
        """Test sanitizing a single record."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        records = [{"name": "secret", "age": 30}]

        result = sanitizer.sanitize_records(records)

        assert len(result) == 1
        assert "secret" not in result[0]["name"]
        assert result[0]["age"] == 30

    def test_sanitize_multiple_records(self):
        """Test sanitizing multiple records."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        records = [
            {"name": "secret", "id": 1},
            {"name": "clean", "id": 2},
            {"name": "secret", "id": 3},
        ]

        result = sanitizer.sanitize_records(records)

        assert len(result) == 3
        assert "secret" not in result[0]["name"]
        assert result[1]["name"] == "clean"
        assert "secret" not in result[2]["name"]
        # Consistency: same PII should have same replacement
        assert result[0]["name"] == result[2]["name"]

    def test_sanitize_empty_records(self):
        """Test sanitizing empty list of records."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        records = []

        result = sanitizer.sanitize_records(records)

        assert result == []


class TestSanitizeFile:
    """Tests for sanitize_file method."""

    def test_sanitize_valid_file(self):
        """Test sanitizing a valid JSON file."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            input_path = Path(f.name)
            json.dump([{"name": "secret", "age": 30}], f)

        # Create temporary output file path
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = Path(f.name)

        try:
            result = sanitizer.sanitize_file(input_path, output_path)

            assert result.success is True
            assert result.records_processed == 1
            assert result.pii_fields_detected == 1
            assert result.pii_replacements_made == 1
            assert result.error_message is None

            # Verify output file was created
            assert output_path.exists()

            # Verify output content
            with open(output_path) as f:
                output_data = json.load(f)

            assert len(output_data) == 1
            assert "secret" not in output_data[0]["name"]
            assert output_data[0]["age"] == 30

        finally:
            # Cleanup
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

    def test_sanitize_file_not_found(self):
        """Test sanitizing a non-existent file."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        input_path = Path("nonexistent.json")
        output_path = Path("output.json")

        result = sanitizer.sanitize_file(input_path, output_path)

        assert result.success is False
        assert result.records_processed == 0
        assert result.error_message is not None
        assert "not found" in result.error_message.lower()

    def test_sanitize_invalid_json(self):
        """Test sanitizing a file with invalid JSON."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            input_path = Path(f.name)
            f.write("{invalid json")

        output_path = Path("output.json")

        try:
            result = sanitizer.sanitize_file(input_path, output_path)

            assert result.success is False
            assert result.records_processed == 0
            assert result.error_message is not None
            assert "line" in result.error_message.lower()
            assert "column" in result.error_message.lower()

        finally:
            input_path.unlink(missing_ok=True)

    def test_sanitize_non_array_json(self):
        """Test sanitizing a JSON file that is not an array."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        # Create temporary file with non-array JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            input_path = Path(f.name)
            json.dump({"name": "secret"}, f)

        output_path = Path("output.json")

        try:
            result = sanitizer.sanitize_file(input_path, output_path)

            assert result.success is False
            assert result.records_processed == 0
            assert result.error_message is not None
            assert "array" in result.error_message.lower()

        finally:
            input_path.unlink(missing_ok=True)

    def test_sanitize_output_path_created(self):
        """Test that output directory is created if it doesn't exist."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            input_path = Path(f.name)
            json.dump([{"name": "clean"}], f)

        # Create output path in temporary directory
        temp_dir = Path(tempfile.mkdtemp())
        output_path = temp_dir / "subdir" / "output.json"

        try:
            result = sanitizer.sanitize_file(input_path, output_path)

            assert result.success is True
            assert output_path.exists()
            assert output_path.parent.exists()

        finally:
            input_path.unlink(missing_ok=True)
            if output_path.exists():
                output_path.unlink()
            if output_path.parent.exists():
                output_path.parent.rmdir()
            if temp_dir.exists():
                temp_dir.rmdir()


class TestStructurePreservation:
    """Tests for structure preservation during sanitization."""

    def test_preserve_non_pii_fields(self):
        """Test that non-PII fields are preserved exactly."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        records = [
            {
                "name": "secret",
                "age": 30,
                "score": 95.5,
                "active": True,
                "notes": None,
                "tags": ["tag1", "tag2"],
            }
        ]

        result = sanitizer.sanitize_records(records)

        assert result[0]["age"] == 30
        assert result[0]["score"] == 95.5
        assert result[0]["active"] is True
        assert result[0]["notes"] is None
        assert result[0]["tags"] == ["tag1", "tag2"]

    def test_preserve_nested_structure(self):
        """Test that nested structure is preserved."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        records = [
            {"user": {"profile": {"name": "secret", "level": 5}, "settings": {"theme": "dark"}}}
        ]

        result = sanitizer.sanitize_records(records)

        assert "user" in result[0]
        assert "profile" in result[0]["user"]
        assert "settings" in result[0]["user"]
        assert result[0]["user"]["profile"]["level"] == 5
        assert result[0]["user"]["settings"]["theme"] == "dark"


class TestErrorHandling:
    """Tests for error handling."""

    def test_read_json_file_not_found(self):
        """Test reading a non-existent file raises FileNotFoundError."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        with pytest.raises(FileNotFoundError) as exc_info:
            sanitizer._read_json_file(Path("nonexistent.json"))

        assert "not found" in str(exc_info.value).lower()

    def test_read_json_invalid_json(self):
        """Test reading invalid JSON raises JSONParseError."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            input_path = Path(f.name)
            f.write("{invalid")

        try:
            with pytest.raises(JSONParseError) as exc_info:
                sanitizer._read_json_file(input_path)

            assert exc_info.value.line > 0
            assert exc_info.value.column > 0

        finally:
            input_path.unlink(missing_ok=True)

    def test_write_json_file_success(self):
        """Test writing JSON file succeeds."""
        detector = MockDetector("secret", PIIType.EMAIL)
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer([detector], replacer)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = Path(f.name)

        try:
            data = [{"name": "test", "age": 30}]
            sanitizer._write_json_file(output_path, data)

            assert output_path.exists()

            with open(output_path) as f:
                written_data = json.load(f)

            assert written_data == data

        finally:
            output_path.unlink(missing_ok=True)
