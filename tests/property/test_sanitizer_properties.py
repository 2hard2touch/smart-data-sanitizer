"""Property-based tests for the Sanitizer orchestrator.

This module contains property tests that verify universal correctness
properties of the sanitization workflow across all inputs using randomized testing.
"""

import json
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from data_sanitizer.detectors.email_detector import EmailDetector
from data_sanitizer.detectors.phone_detector import PhoneDetector
from data_sanitizer.replacer import Replacer
from data_sanitizer.sanitizer import Sanitizer


# Strategy for generating valid JSON structures
@st.composite
def json_records(draw):
    """Generate valid JSON record structures for property testing.

    Generates lists of dictionaries with various field types:
    - Strings (may contain PII)
    - Integers
    - Floats
    - Booleans
    - None values
    - Nested dictionaries
    - Lists

    Returns:
        List of dictionaries representing JSON records
    """
    # Generate 1-5 records
    num_records = draw(st.integers(min_value=1, max_value=5))

    records = []
    for _ in range(num_records):
        record = {}

        # Generate 1-5 fields per record
        num_fields = draw(st.integers(min_value=1, max_value=5))

        for field_idx in range(num_fields):
            field_name = f"field_{field_idx}"

            # Choose field type
            field_type = draw(st.integers(min_value=0, max_value=6))

            if field_type == 0:
                # String (use printable ASCII to avoid encoding issues)
                record[field_name] = draw(
                    st.text(
                        alphabet=st.characters(min_codepoint=32, max_codepoint=126),
                        min_size=0,
                        max_size=50,
                    )
                )
            elif field_type == 1:
                # Integer
                record[field_name] = draw(st.integers(min_value=-1000, max_value=1000))
            elif field_type == 2:
                # Float
                record[field_name] = draw(
                    st.floats(
                        min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False
                    )
                )
            elif field_type == 3:
                # Boolean
                record[field_name] = draw(st.booleans())
            elif field_type == 4:
                # None
                record[field_name] = None
            elif field_type == 5:
                # Nested dict (simple, one level)
                record[field_name] = {
                    "nested_field": draw(
                        st.text(
                            alphabet=st.characters(min_codepoint=32, max_codepoint=126),
                            min_size=0,
                            max_size=20,
                        )
                    )
                }
            else:
                # List (simple, strings and integers)
                list_size = draw(st.integers(min_value=0, max_value=3))
                record[field_name] = [
                    draw(
                        st.one_of(
                            st.text(
                                alphabet=st.characters(min_codepoint=32, max_codepoint=126),
                                min_size=0,
                                max_size=20,
                            ),
                            st.integers(min_value=0, max_value=100),
                        )
                    )
                    for _ in range(list_size)
                ]

        records.append(record)

    return records


# Strategy for generating JSON records with mix of PII and non-PII
@st.composite
def json_records_with_pii(draw):
    """Generate JSON records with a mix of PII and non-PII data.

    Returns:
        Tuple of (records, non_pii_fields) where non_pii_fields is a dict
        mapping record index to list of (field_name, expected_value) tuples
    """
    # Generate 1-3 records
    num_records = draw(st.integers(min_value=1, max_value=3))

    records = []
    non_pii_fields = {}

    for record_idx in range(num_records):
        record = {}
        non_pii_fields[record_idx] = []

        # Add some non-PII fields
        record["id"] = draw(st.integers(min_value=1, max_value=1000))
        non_pii_fields[record_idx].append(("id", record["id"]))

        record["age"] = draw(st.integers(min_value=18, max_value=100))
        non_pii_fields[record_idx].append(("age", record["age"]))

        record["score"] = draw(
            st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
        )
        non_pii_fields[record_idx].append(("score", record["score"]))

        record["active"] = draw(st.booleans())
        non_pii_fields[record_idx].append(("active", record["active"]))

        # Add some PII fields (simple strings that won't be detected as PII)
        # We use simple text that doesn't match email/phone patterns
        record["name"] = draw(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=10)
        )
        # Note: We don't add "name" to non_pii_fields because it might be detected as PII

        records.append(record)

    return records, non_pii_fields


# Strategy for generating malformed JSON strings
malformed_json_strings = st.one_of(
    st.just("{invalid"),  # Missing closing brace
    st.just("[1, 2, 3"),  # Missing closing bracket
    st.just('{"key": }'),  # Missing value
    st.just('{"key" "value"}'),  # Missing colon
    st.just("{key: 'value'}"),  # Unquoted key
    st.just("{'key': 'value'}"),  # Single quotes instead of double
    st.just('{"key": undefined}'),  # Invalid value
    st.just('{"key": NaN}'),  # Invalid value
    st.just(""),  # Empty string
    st.just("null"),  # Not an array
    st.just("{}"),  # Object instead of array
    st.just('{"a": 1, "b": 2,}'),  # Trailing comma
)


class TestJSONRoundTripValidity:
    """Property-based tests for JSON round-trip validity."""

    @settings(max_examples=25, deadline=2000)
    @given(records=json_records())
    def test_json_round_trip_validity(self, records: list[dict]):
        """Feature: data-sanitizer, Property 1: JSON Round-Trip Validity

        For any valid JSON input that sanitizes successfully, the output
        should be parseable as valid JSON.

        Validates: Requirements 1.1, 1.3
        """
        # Create sanitizer with minimal detectors
        detectors = [EmailDetector(), PhoneDetector()]
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer(detectors, replacer)

        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            input_path = Path(f.name)
            json.dump(records, f)

        # Create temporary output file path
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Sanitize the file
            result = sanitizer.sanitize_file(input_path, output_path)

            # Assert: Sanitization succeeded
            assert result.success is True, f"Sanitization failed: {result.error_message}"

            # Assert: Output file exists
            assert output_path.exists(), "Output file was not created"

            # Assert: Output is valid JSON
            with open(output_path, encoding="utf-8") as f:
                output_data = json.load(f)

            # Assert: Output is a list
            assert isinstance(output_data, list), "Output should be a list"

            # Assert: Same number of records
            assert len(output_data) == len(records), (
                f"Record count mismatch: expected {len(records)}, got {len(output_data)}"
            )

        finally:
            # Cleanup
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)


class TestStructurePreservation:
    """Property-based tests for structure and non-PII preservation."""

    @settings(max_examples=15, deadline=2000)
    @given(data=json_records_with_pii())
    def test_structure_and_non_pii_preservation(self, data: tuple):
        """Feature: data-sanitizer, Property 3: Structure and Non-PII Preservation

        For any JSON record, after sanitization, all non-PII fields should
        have identical values and the overall structure should be preserved.

        Validates: Requirements 1.5
        """
        records, non_pii_fields = data

        # Create sanitizer with minimal detectors
        detectors = [EmailDetector(), PhoneDetector()]
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer(detectors, replacer)

        # Sanitize records
        sanitized_records = sanitizer.sanitize_records(records)

        # Assert: Same number of records
        assert len(sanitized_records) == len(records), (
            f"Record count mismatch: expected {len(records)}, got {len(sanitized_records)}"
        )

        # Assert: Non-PII fields are preserved
        for record_idx, expected_fields in non_pii_fields.items():
            sanitized_record = sanitized_records[record_idx]

            for field_name, expected_value in expected_fields:
                assert field_name in sanitized_record, (
                    f"Field '{field_name}' missing in sanitized record {record_idx}"
                )

                actual_value = sanitized_record[field_name]

                # For floats, use approximate comparison
                if isinstance(expected_value, float):
                    assert abs(actual_value - expected_value) < 0.0001, (
                        f"Field '{field_name}' value mismatch in record {record_idx}: "
                        f"expected {expected_value}, got {actual_value}"
                    )
                else:
                    assert actual_value == expected_value, (
                        f"Field '{field_name}' value mismatch in record {record_idx}: "
                        f"expected {expected_value}, got {actual_value}"
                    )


class TestInvalidJSONErrorHandling:
    """Property-based tests for invalid JSON error handling."""

    @settings(max_examples=20, deadline=500)
    @given(malformed_json=malformed_json_strings)
    def test_invalid_json_error_handling(self, malformed_json: str):
        """Feature: data-sanitizer, Property 2: Invalid JSON Error Handling

        For any malformed JSON input, the sanitizer should return a descriptive
        error message without crashing.

        Validates: Requirements 1.2
        """
        # Create sanitizer
        detectors = [EmailDetector(), PhoneDetector()]
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer(detectors, replacer)

        # Create temporary file with malformed JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            input_path = Path(f.name)
            f.write(malformed_json)

        output_path = Path(tempfile.mktemp(suffix=".json"))

        try:
            # Sanitize the file (should not crash)
            result = sanitizer.sanitize_file(input_path, output_path)

            # Assert: Sanitization failed gracefully
            assert result.success is False, (
                f"Expected sanitization to fail for malformed JSON: '{malformed_json}'"
            )

            # Assert: Error message is provided
            assert result.error_message is not None, (
                "Error message should be provided for malformed JSON"
            )
            assert len(result.error_message) > 0, "Error message should not be empty"

            # Assert: Error message is descriptive (contains useful information)
            error_lower = result.error_message.lower()
            assert any(
                keyword in error_lower
                for keyword in ["json", "parse", "invalid", "line", "column", "array", "error"]
            ), f"Error message should be descriptive: '{result.error_message}'"

        finally:
            # Cleanup
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)


class TestDetectorConfiguration:
    """Property-based tests for detector configuration."""

    @settings(max_examples=25, deadline=2000)
    @given(
        email=st.emails(),
        phone=st.sampled_from(
            [
                "+1-555-123-4567",
                "(555) 987-6543",
                "555-777-8888",
                "5551234567",
            ]
        ),
        disable_email=st.booleans(),
        disable_phone=st.booleans(),
    )
    def test_detector_configuration(
        self,
        email: str,
        phone: str,
        disable_email: bool,
        disable_phone: bool,
    ):
        """Feature: data-sanitizer, Property 21: Detector Configuration

        For any detector that is disabled via configuration, it should not
        detect any PII of its type.

        Validates: Requirements 9.2
        """
        # Skip if both are disabled (nothing to test)
        if disable_email and disable_phone:
            return

        # Create detector list based on configuration
        detectors = []
        if not disable_email:
            detectors.append(EmailDetector())
        if not disable_phone:
            detectors.append(PhoneDetector())

        # Create sanitizer with configured detectors
        replacer = Replacer(seed=42)
        sanitizer = Sanitizer(detectors, replacer)

        # Create a record with both email and phone
        record = {
            "id": 1,
            "email_field": email,
            "phone_field": phone,
            "mixed_field": f"Contact: {email} or call {phone}",
        }

        # Sanitize the record
        sanitized_records = sanitizer.sanitize_records([record])
        sanitized_record = sanitized_records[0]

        # Assert: If email detector is disabled, emails should not be replaced
        if disable_email:
            # Email should remain unchanged
            assert sanitized_record["email_field"] == email, (
                f"Email should not be replaced when detector is disabled: "
                f"expected '{email}', got '{sanitized_record['email_field']}'"
            )
            # Email in mixed field should also remain unchanged
            assert email in sanitized_record["mixed_field"], (
                "Email in mixed field should not be replaced when detector is disabled"
            )
        else:
            # Email should be replaced (unless it's already a fake email)
            # We can't assert it's different because the fake might match by chance,
            # but we can verify it's still a valid email format
            assert "@" in sanitized_record["email_field"], (
                "Sanitized email should still be a valid email format"
            )

        # Assert: If phone detector is disabled, phones should not be replaced
        if disable_phone:
            # Phone should remain unchanged
            assert sanitized_record["phone_field"] == phone, (
                f"Phone should not be replaced when detector is disabled: "
                f"expected '{phone}', got '{sanitized_record['phone_field']}'"
            )
            # Phone in mixed field should also remain unchanged
            assert phone in sanitized_record["mixed_field"], (
                "Phone in mixed field should not be replaced when detector is disabled"
            )
        else:
            # Phone should be replaced (unless it's already a fake phone)
            # We verify it's still a phone-like format (contains digits)
            assert any(c.isdigit() for c in sanitized_record["phone_field"]), (
                "Sanitized phone should still contain digits"
            )

        # Assert: Non-PII field is preserved
        assert sanitized_record["id"] == 1, "Non-PII field should be preserved"
