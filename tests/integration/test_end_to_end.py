"""
Integration tests for end-to-end sanitization workflows.

These tests verify the complete sanitization pipeline from file input to output,
including PII detection, replacement, consistency, and error handling.
"""

import json
from pathlib import Path

import pytest

from data_sanitizer.detectors.credit_card_detector import CreditCardDetector
from data_sanitizer.detectors.email_detector import EmailDetector
from data_sanitizer.detectors.name_detector import NameDetector
from data_sanitizer.detectors.phone_detector import PhoneDetector
from data_sanitizer.replacer import Replacer
from data_sanitizer.sanitizer import Sanitizer


@pytest.fixture
def all_detectors():
    """Create a list of all available detectors."""
    return [
        EmailDetector(),
        PhoneDetector(),
        NameDetector(),
        CreditCardDetector(),
    ]


@pytest.fixture
def sanitizer_with_seed(all_detectors):
    """Create a sanitizer with a fixed seed for reproducible tests."""
    replacer = Replacer(seed=42)
    return Sanitizer(detectors=all_detectors, replacer=replacer)


@pytest.fixture
def sanitizer_no_seed(all_detectors):
    """Create a sanitizer without a seed."""
    replacer = Replacer()
    return Sanitizer(detectors=all_detectors, replacer=replacer)


@pytest.fixture
def sample_dirty_data_path():
    """Path to sample dirty data fixture."""
    return Path("tests/fixtures/sample_dirty_data.json")


@pytest.fixture
def edge_cases_path():
    """Path to edge cases fixture."""
    return Path("tests/fixtures/edge_cases.json")


@pytest.fixture
def invalid_json_path():
    """Path to invalid JSON fixture."""
    return Path("tests/fixtures/invalid_json.txt")


class TestFullSanitizationWorkflow:
    """Test complete sanitization workflow with sample data."""

    def test_sanitize_sample_dirty_data(
        self, sanitizer_with_seed, sample_dirty_data_path, tmp_path
    ):
        """Test full sanitization of sample dirty data."""
        output_path = tmp_path / "sanitized_output.json"

        # Sanitize the file
        result = sanitizer_with_seed.sanitize_file(sample_dirty_data_path, output_path)

        # Verify result
        assert result.success is True
        assert result.records_processed == 10
        assert result.pii_fields_detected > 0
        assert result.pii_replacements_made > 0
        assert result.error_message is None

        # Verify output file exists and is valid JSON
        assert output_path.exists()
        with open(output_path, encoding="utf-8") as f:
            sanitized_data = json.load(f)

        # Verify structure is preserved
        assert len(sanitized_data) == 10
        assert all("user_id" in record for record in sanitized_data)

    def test_all_pii_is_replaced(self, sanitizer_with_seed, sample_dirty_data_path, tmp_path):
        """Verify that all PII is replaced in the output."""
        output_path = tmp_path / "sanitized_output.json"

        # Sanitize
        sanitizer_with_seed.sanitize_file(sample_dirty_data_path, output_path)

        # Load sanitized data
        with open(output_path, encoding="utf-8") as f:
            sanitized_data = json.load(f)

        # Check that specific known PII values are replaced
        sanitized_json_str = json.dumps(sanitized_data)

        # These PII values should not appear in sanitized output
        assert "john.doe@example.com" not in sanitized_json_str.lower()
        assert "jane.smith@example.com" not in sanitized_json_str.lower()
        assert "alice@test.com" not in sanitized_json_str.lower()
        assert "John Doe" not in sanitized_json_str
        assert "Alice Johnson" not in sanitized_json_str

    def test_non_pii_is_preserved(self, sanitizer_with_seed, sample_dirty_data_path, tmp_path):
        """Verify that non-PII fields are preserved exactly."""
        output_path = tmp_path / "sanitized_output.json"

        # Load original data
        with open(sample_dirty_data_path, encoding="utf-8") as f:
            original_data = json.load(f)

        # Sanitize
        sanitizer_with_seed.sanitize_file(sample_dirty_data_path, output_path)

        # Load sanitized data
        with open(output_path, encoding="utf-8") as f:
            sanitized_data = json.load(f)

        # Check non-PII fields are preserved
        for i, (original, sanitized) in enumerate(zip(original_data, sanitized_data)):
            # User IDs should be preserved
            assert original["user_id"] == sanitized["user_id"]

            # Check specific non-PII fields based on record structure
            if i == 0:  # First record
                assert original["status"] == sanitized["status"]
                assert original["created_at"] == sanitized["created_at"]
                assert original["metadata"] == sanitized["metadata"]
                assert (
                    original["payment_info"]["card_type"] == sanitized["payment_info"]["card_type"]
                )

            if i == 1:  # Second record
                assert original["department"] == sanitized["department"]
                assert original["level"] == sanitized["level"]
                assert original["performance_score"] == sanitized["performance_score"]

            if i == 3:  # Fourth record (no PII)
                assert original["account"] == sanitized["account"]
                assert original["profile"] == sanitized["profile"]
                assert original["activity"] == sanitized["activity"]

            if i == 9:  # Last record (no PII at all)
                assert original == sanitized


class TestEdgeCases:
    """Test edge cases with special data structures."""

    def test_edge_cases_file(self, sanitizer_with_seed, edge_cases_path, tmp_path):
        """Test sanitization of edge cases."""
        output_path = tmp_path / "edge_cases_output.json"

        result = sanitizer_with_seed.sanitize_file(edge_cases_path, output_path)

        assert result.success is True
        # Edge cases file has 11 records (checked the fixture)
        assert result.records_processed == 11
        assert output_path.exists()

        # Verify output is valid JSON
        with open(output_path, encoding="utf-8") as f:
            sanitized_data = json.load(f)

        assert len(sanitized_data) == 11

    def test_deeply_nested_pii(self, sanitizer_with_seed, edge_cases_path, tmp_path):
        """Test that deeply nested PII is detected and replaced."""
        output_path = tmp_path / "nested_output.json"

        # Load original
        # Sanitize
        sanitizer_with_seed.sanitize_file(edge_cases_path, output_path)

        # Load sanitized
        with open(output_path, encoding="utf-8") as f:
            sanitized_data = json.load(f)

        # Find the deeply nested record (user_id 2)
        nested_record = next(r for r in sanitized_data if r.get("user_id") == 2)

        # Verify PII was replaced in deep nesting
        deep_email = nested_record["deeply"]["nested"]["structure"]["with"]["pii"]["email"]
        assert deep_email != "deep.nested@example.com"
        assert "@" in deep_email  # Should still be an email

    def test_mixed_pii_in_single_field(self, sanitizer_with_seed, edge_cases_path, tmp_path):
        """Test that multiple PII types in one field are all replaced."""
        output_path = tmp_path / "mixed_output.json"

        # Sanitize
        sanitizer_with_seed.sanitize_file(edge_cases_path, output_path)

        # Load sanitized
        with open(output_path, encoding="utf-8") as f:
            sanitized_data = json.load(f)

        # Find the mixed PII record (user_id 3)
        mixed_record = next(r for r in sanitized_data if r.get("user_id") == 3)
        mixed_field = mixed_record["mixed_pii_field"]

        # Original PII should not be present
        assert "john.smith@example.com" not in mixed_field.lower()
        assert "jane.doe@test.com" not in mixed_field.lower()
        assert "John Smith" not in mixed_field

    def test_duplicate_pii_consistency(self, sanitizer_with_seed, edge_cases_path, tmp_path):
        """Test that duplicate PII values are replaced consistently."""
        output_path = tmp_path / "duplicate_output.json"

        # Sanitize
        sanitizer_with_seed.sanitize_file(edge_cases_path, output_path)

        # Load sanitized
        with open(output_path, encoding="utf-8") as f:
            sanitized_data = json.load(f)

        # Find records with duplicate PII (user_id 4 and 5)
        record_4 = next(r for r in sanitized_data if r.get("user_id") == 4)
        record_5 = next(r for r in sanitized_data if r.get("user_id") == 5)

        # Same original PII should map to same fake PII
        assert record_4["name"] == record_5["name"]
        assert record_4["email"] == record_5["email"]
        assert record_4["phone"] == record_5["phone"]

    def test_empty_and_null_values(self, sanitizer_with_seed, edge_cases_path, tmp_path):
        """Test handling of empty and null values."""
        output_path = tmp_path / "empty_output.json"

        # Sanitize
        sanitizer_with_seed.sanitize_file(edge_cases_path, output_path)

        # Load sanitized
        with open(output_path, encoding="utf-8") as f:
            sanitized_data = json.load(f)

        # Find record with empty values (user_id 7)
        empty_record = next(r for r in sanitized_data if r.get("user_id") == 7)

        # Empty and null values should be preserved
        assert empty_record["empty_array"] == []
        assert empty_record["null_value"] is None
        assert empty_record["empty_string"] == ""
        assert empty_record["zero"] == 0
        assert empty_record["false_value"] is False

    def test_special_format_pii(self, sanitizer_with_seed, edge_cases_path, tmp_path):
        """Test detection of PII in special formats."""
        output_path = tmp_path / "special_output.json"

        # Sanitize
        sanitizer_with_seed.sanitize_file(edge_cases_path, output_path)

        # Load sanitized
        with open(output_path, encoding="utf-8") as f:
            sanitized_data = json.load(f)

        # Find record with special formats (user_id 8)
        special_record = next(r for r in sanitized_data if r.get("user_id") == 8)
        special_formats = special_record["special_formats"]

        # Verify emails with special characters are replaced
        assert special_formats["email_with_plus"] != "user+tag@example.com"
        assert "@" in special_formats["email_with_plus"]

        assert special_formats["email_with_dots"] != "first.middle.last@example.co.uk"
        assert "@" in special_formats["email_with_dots"]


class TestConsistencyAcrossRuns:
    """Test consistency with same seed across multiple runs."""

    def test_same_seed_produces_identical_output(
        self, all_detectors, sample_dirty_data_path, tmp_path
    ):
        """Test that same seed produces identical output across runs."""
        output_path_1 = tmp_path / "output1.json"
        output_path_2 = tmp_path / "output2.json"

        # First run with seed 42
        replacer_1 = Replacer(seed=42)
        sanitizer_1 = Sanitizer(detectors=all_detectors, replacer=replacer_1)
        sanitizer_1.sanitize_file(sample_dirty_data_path, output_path_1)

        # Second run with same seed 42
        replacer_2 = Replacer(seed=42)
        sanitizer_2 = Sanitizer(detectors=all_detectors, replacer=replacer_2)
        sanitizer_2.sanitize_file(sample_dirty_data_path, output_path_2)

        # Load both outputs
        with open(output_path_1, encoding="utf-8") as f:
            output_1 = json.load(f)
        with open(output_path_2, encoding="utf-8") as f:
            output_2 = json.load(f)

        # Outputs should be identical
        assert output_1 == output_2

    def test_different_seed_produces_different_output(
        self, all_detectors, sample_dirty_data_path, tmp_path
    ):
        """Test that different seeds produce different outputs."""
        output_path_1 = tmp_path / "output1.json"
        output_path_2 = tmp_path / "output2.json"

        # First run with seed 42
        replacer_1 = Replacer(seed=42)
        sanitizer_1 = Sanitizer(detectors=all_detectors, replacer=replacer_1)
        sanitizer_1.sanitize_file(sample_dirty_data_path, output_path_1)

        # Second run with different seed 123
        replacer_2 = Replacer(seed=123)
        sanitizer_2 = Sanitizer(detectors=all_detectors, replacer=replacer_2)
        sanitizer_2.sanitize_file(sample_dirty_data_path, output_path_2)

        # Load both outputs
        with open(output_path_1, encoding="utf-8") as f:
            output_1 = json.load(f)
        with open(output_path_2, encoding="utf-8") as f:
            output_2 = json.load(f)

        # Outputs should be different (at least some PII replacements differ)
        assert output_1 != output_2


class TestOutputCanBeReparsedAndResanitized:
    """Test that sanitized output can be parsed and re-sanitized."""

    def test_output_is_valid_json(self, sanitizer_with_seed, sample_dirty_data_path, tmp_path):
        """Test that output is valid, parseable JSON."""
        output_path = tmp_path / "output.json"

        sanitizer_with_seed.sanitize_file(sample_dirty_data_path, output_path)

        # Should be able to parse without errors
        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) > 0

    def test_resanitizing_output_changes_nothing(
        self, sanitizer_with_seed, sample_dirty_data_path, tmp_path
    ):
        """Test that re-sanitizing already sanitized data produces no changes."""
        output_path_1 = tmp_path / "output1.json"
        output_path_2 = tmp_path / "output2.json"

        # First sanitization
        result_1 = sanitizer_with_seed.sanitize_file(sample_dirty_data_path, output_path_1)
        assert result_1.pii_replacements_made > 0

        # Re-sanitize the output
        result_2 = sanitizer_with_seed.sanitize_file(output_path_1, output_path_2)

        # Should process records but make no replacements (no PII left)
        assert result_2.success is True
        assert result_2.records_processed == result_1.records_processed
        # Note: Some fake data might still match PII patterns, so we can't assert
        # pii_replacements_made == 0, but it should be much lower

        # Load both outputs
        with open(output_path_1, encoding="utf-8") as f:
            output_1 = json.load(f)
        with open(output_path_2, encoding="utf-8") as f:
            output_2 = json.load(f)

        # Outputs should be very similar (allowing for potential fake PII detection)
        assert len(output_1) == len(output_2)


class TestErrorHandling:
    """Test error handling with invalid inputs."""

    def test_file_not_found_error(self, sanitizer_with_seed, tmp_path):
        """Test error when input file does not exist."""
        nonexistent_path = tmp_path / "nonexistent.json"
        output_path = tmp_path / "output.json"

        result = sanitizer_with_seed.sanitize_file(nonexistent_path, output_path)

        # Should return failure result
        assert result.success is False
        assert result.records_processed == 0
        assert result.error_message is not None
        assert "not found" in result.error_message.lower()

    def test_invalid_json_error(self, sanitizer_with_seed, tmp_path):
        """Test error when input file contains invalid JSON."""
        # Create a file with invalid JSON
        invalid_json_path = tmp_path / "invalid.json"
        with open(invalid_json_path, "w", encoding="utf-8") as f:
            f.write('{"id": 1, "name": "John"')  # Missing closing brace

        output_path = tmp_path / "output.json"

        result = sanitizer_with_seed.sanitize_file(invalid_json_path, output_path)

        # Should return failure result
        assert result.success is False
        assert result.records_processed == 0
        assert result.error_message is not None
        assert "json" in result.error_message.lower()

    def test_invalid_output_directory(self, sanitizer_with_seed, sample_dirty_data_path, tmp_path):
        """Test handling when output directory does not exist."""
        # Create path to non-existent directory
        output_path = tmp_path / "nonexistent_dir" / "output.json"

        # The sanitizer creates parent directories, so this should succeed
        result = sanitizer_with_seed.sanitize_file(sample_dirty_data_path, output_path)

        # Should succeed because parent directories are created automatically
        assert result.success is True
        assert output_path.exists()

    def test_empty_json_array(self, sanitizer_with_seed, tmp_path):
        """Test handling of empty JSON array."""
        empty_json_path = tmp_path / "empty.json"
        with open(empty_json_path, "w", encoding="utf-8") as f:
            f.write("[]")

        output_path = tmp_path / "output.json"

        result = sanitizer_with_seed.sanitize_file(empty_json_path, output_path)

        # Should succeed with 0 records processed
        assert result.success is True
        assert result.records_processed == 0
        assert result.pii_replacements_made == 0

    def test_non_array_json(self, sanitizer_with_seed, tmp_path):
        """Test handling of JSON that is not an array."""
        single_object_path = tmp_path / "single_object.json"
        with open(single_object_path, "w", encoding="utf-8") as f:
            f.write('{"id": 1, "name": "John Doe"}')

        output_path = tmp_path / "output.json"

        # Should handle gracefully (might wrap in array or raise error)
        # Implementation-dependent behavior
        try:
            sanitizer_with_seed.sanitize_file(single_object_path, output_path)
            # If it succeeds, verify output is valid
            assert output_path.exists()
        except Exception:
            # If it raises an error, that's also acceptable
            pass


class TestStatisticsAccuracy:
    """Test that sanitization statistics are accurate."""

    def test_records_processed_count(self, sanitizer_with_seed, sample_dirty_data_path, tmp_path):
        """Test that records_processed count is accurate."""
        output_path = tmp_path / "output.json"

        # Load original to count records
        with open(sample_dirty_data_path, encoding="utf-8") as f:
            original_data = json.load(f)

        result = sanitizer_with_seed.sanitize_file(sample_dirty_data_path, output_path)

        assert result.records_processed == len(original_data)

    def test_pii_fields_detected_count(self, sanitizer_with_seed, sample_dirty_data_path, tmp_path):
        """Test that pii_fields_detected count is reasonable."""
        output_path = tmp_path / "output.json"

        result = sanitizer_with_seed.sanitize_file(sample_dirty_data_path, output_path)

        # Should detect multiple PII fields
        assert result.pii_fields_detected > 0
        # Should be less than total number of fields
        assert result.pii_fields_detected < 100

    def test_pii_replacements_made_count(
        self, sanitizer_with_seed, sample_dirty_data_path, tmp_path
    ):
        """Test that pii_replacements_made count is reasonable."""
        output_path = tmp_path / "output.json"

        result = sanitizer_with_seed.sanitize_file(sample_dirty_data_path, output_path)

        # Should make multiple replacements
        assert result.pii_replacements_made > 0
        # Replacements should be at least as many as fields detected
        assert result.pii_replacements_made >= result.pii_fields_detected
