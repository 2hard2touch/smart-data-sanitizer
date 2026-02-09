"""Main orchestrator for PII detection and replacement.

This module provides the Sanitizer class that coordinates the entire
sanitization workflow: reading JSON files, detecting PII, replacing it
with fake data, and writing sanitized output.
"""

import json
from pathlib import Path
from typing import Any

from data_sanitizer.detectors.base import Detector
from data_sanitizer.exceptions import (
    FileNotFoundError,
    InvalidOutputPathError,
    JSONParseError,
)
from data_sanitizer.models import SanitizationResult
from data_sanitizer.replacer import Replacer


class Sanitizer:
    """Main orchestrator for PII detection and replacement.

    The Sanitizer coordinates all aspects of the sanitization process:
    - Reading and parsing JSON input files
    - Detecting PII using configured detectors
    - Replacing PII with consistent fake data
    - Writing sanitized output
    - Tracking statistics and handling errors

    Attributes:
        _detectors: List of PII detectors to use
        _replacer: Replacer instance for generating fake data
        _pii_fields_detected: Counter for fields containing PII
        _pii_replacements_made: Counter for PII values replaced
    """

    def __init__(self, detectors: list[Detector], replacer: Replacer) -> None:
        """Initialize sanitizer with detection and replacement strategies.

        Args:
            detectors: List of Detector instances to use for PII detection.
                Each detector is responsible for identifying a specific type
                of PII (emails, phones, names, credit cards, etc.).
            replacer: Replacer instance for generating consistent fake data.
                The replacer maintains a consistency cache to ensure identical
                PII values are always replaced with the same fake value.

        Example:
            >>> detectors = [EmailDetector(), PhoneDetector(), NameDetector()]
            >>> replacer = Replacer(seed=42)
            >>> sanitizer = Sanitizer(detectors, replacer)
        """
        self._detectors = detectors
        self._replacer = replacer
        self._pii_fields_detected = 0
        self._pii_replacements_made = 0

    def sanitize_file(self, input_path: Path, output_path: Path) -> SanitizationResult:
        """Sanitize a JSON file by detecting and replacing PII.

        This method orchestrates the complete sanitization workflow:
        1. Read and parse the input JSON file
        2. Sanitize all records by detecting and replacing PII
        3. Write the sanitized data to the output file
        4. Return statistics about the operation

        Args:
            input_path: Path to input JSON file containing records to sanitize
            output_path: Path where sanitized JSON output will be written.
                If the file exists, it will be overwritten.

        Returns:
            SanitizationResult containing:
            - success: True if sanitization completed, False if error occurred
            - records_processed: Number of records sanitized
            - pii_fields_detected: Number of fields containing PII
            - pii_replacements_made: Number of PII values replaced
            - error_message: Error description if failed, None if successful

        Raises:
            FileNotFoundError: If input file does not exist or is not readable
            JSONParseError: If input file contains invalid JSON
            InvalidOutputPathError: If output path is invalid or not writable

        Example:
            >>> sanitizer = Sanitizer(detectors, replacer)
            >>> result = sanitizer.sanitize_file(
            ...     Path("input.json"),
            ...     Path("output.json")
            ... )
            >>> print(f"Processed {result.records_processed} records")
        """
        # Reset counters for this operation
        self._pii_fields_detected = 0
        self._pii_replacements_made = 0

        try:
            # Read input file
            records = self._read_json_file(input_path)

            # Sanitize records
            sanitized_records = self.sanitize_records(records)

            # Write output file
            self._write_json_file(output_path, sanitized_records)

            # Return success result
            return SanitizationResult(
                success=True,
                records_processed=len(records),
                pii_fields_detected=self._pii_fields_detected,
                pii_replacements_made=self._pii_replacements_made,
                error_message=None,
            )

        except (FileNotFoundError, JSONParseError, InvalidOutputPathError) as e:
            # Return failure result with error message
            return SanitizationResult(
                success=False,
                records_processed=0,
                pii_fields_detected=0,
                pii_replacements_made=0,
                error_message=str(e),
            )
        except Exception as e:
            # Catch unexpected errors and return user-friendly message
            return SanitizationResult(
                success=False,
                records_processed=0,
                pii_fields_detected=0,
                pii_replacements_made=0,
                error_message=f"Unexpected error during sanitization: {str(e)}",
            )

    def sanitize_records(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sanitize a list of records.

        This method processes each record in the list, detecting and replacing
        PII in all fields while preserving the overall structure.

        Args:
            records: List of dictionaries representing JSON objects to sanitize

        Returns:
            List of sanitized records with PII replaced by fake data.
            The structure and non-PII fields remain unchanged.

        Example:
            >>> records = [{"name": "John Doe", "age": 30}]
            >>> sanitized = sanitizer.sanitize_records(records)
            >>> sanitized[0]["age"]  # Non-PII preserved
            30
        """
        sanitized_records = []

        for record in records:
            sanitized_record = {}
            for field_name, value in record.items():
                sanitized_record[field_name] = self.sanitize_value(value, field_name)
            sanitized_records.append(sanitized_record)

        return sanitized_records

    def sanitize_value(self, value: Any, field_name: str) -> Any:
        """Sanitize a single value by detecting and replacing PII.

        This method handles different value types appropriately:
        - Strings: Run all detectors and replace detected PII
        - Dicts: Recursively sanitize all nested fields
        - Lists: Recursively sanitize all elements
        - Primitives (int, float, bool, None): Return unchanged

        Args:
            value: The value to sanitize (can be any JSON-compatible type)
            field_name: The name of the field being analyzed. This provides
                context for detection (e.g., "email", "first_name").

        Returns:
            Sanitized value with PII replaced. Non-PII values and structure
            are preserved exactly.

        Example:
            >>> sanitizer.sanitize_value("john@example.com", "email")
            "fake@example.org"
            >>> sanitizer.sanitize_value(42, "age")
            42
            >>> sanitizer.sanitize_value({"name": "John"}, "user")
            {"name": "Michael"}
        """
        # Handle strings: detect and replace PII
        if isinstance(value, str):
            return self._sanitize_string(value, field_name)

        # Handle nested dicts: recurse
        elif isinstance(value, dict):
            sanitized_dict = {}
            for key, nested_value in value.items():
                sanitized_dict[key] = self.sanitize_value(nested_value, key)
            return sanitized_dict

        # Handle lists: recurse
        elif isinstance(value, list):
            return [self.sanitize_value(item, field_name) for item in value]

        # Handle primitives: return unchanged
        else:
            return value

    def _sanitize_string(self, text: str, field_name: str) -> str:
        """Sanitize a string by detecting and replacing PII.

        This method runs all configured detectors on the text and replaces
        any detected PII with fake data. Multiple PII instances in the same
        string are all replaced.

        Args:
            text: Text to sanitize
            field_name: Name of the field for detection context

        Returns:
            Sanitized text with all PII replaced
        """
        # Collect all detections from all detectors
        all_detections = []
        for detector in self._detectors:
            detections = detector.detect(text, field_name)
            all_detections.extend(detections)

        # If no PII detected, return original text
        if not all_detections:
            return text

        # Track that we found PII in this field
        self._pii_fields_detected += 1

        # Sort detections by position (reverse order to replace from end to start)
        # This prevents position shifts when replacing
        all_detections.sort(key=lambda d: d.start_pos, reverse=True)

        # Replace each detected PII
        sanitized_text = text
        for detection in all_detections:
            # Get fake replacement
            fake_value = self._replacer.replace(detection)

            # Replace in text
            if detection.start_pos >= 0 and detection.end_pos > detection.start_pos:
                # Use position information if available
                sanitized_text = (
                    sanitized_text[: detection.start_pos]
                    + fake_value
                    + sanitized_text[detection.end_pos :]
                )
            else:
                # Fallback: simple string replacement
                sanitized_text = sanitized_text.replace(
                    detection.original_value,
                    fake_value,
                    1,  # Replace only first occurrence
                )

            # Track replacement
            self._pii_replacements_made += 1

        return sanitized_text

    def _read_json_file(self, input_path: Path) -> list[dict[str, Any]]:
        """Read and parse a JSON file.

        Args:
            input_path: Path to JSON file to read

        Returns:
            Parsed JSON data as list of dictionaries

        Raises:
            FileNotFoundError: If file does not exist or is not readable
            JSONParseError: If file contains invalid JSON
        """
        # Check if file exists
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}", str(input_path))

        # Check if file is readable
        if not input_path.is_file():
            raise FileNotFoundError(f"Input path is not a file: {input_path}", str(input_path))

        try:
            # Read and parse JSON
            with open(input_path, encoding="utf-8") as f:
                data = json.load(f)

            # Ensure data is a list
            if not isinstance(data, list):
                raise JSONParseError("JSON root must be an array", line=1, column=1)

            return data

        except json.JSONDecodeError as e:
            # Convert JSON decode error to our custom exception
            raise JSONParseError(f"Invalid JSON: {e.msg}", line=e.lineno, column=e.colno)
        except PermissionError:
            raise FileNotFoundError(
                f"Permission denied reading file: {input_path}", str(input_path)
            )
        except Exception as e:
            # Catch other file reading errors
            raise FileNotFoundError(f"Error reading file: {str(e)}", str(input_path))

    def _write_json_file(self, output_path: Path, data: list[dict[str, Any]]) -> None:
        """Write data to a JSON file.

        Args:
            output_path: Path where JSON will be written
            data: Data to write as JSON

        Raises:
            InvalidOutputPathError: If output path is invalid or not writable
        """
        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write JSON with pretty formatting
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except PermissionError:
            raise InvalidOutputPathError(
                f"Permission denied writing to: {output_path}", str(output_path)
            )
        except OSError as e:
            raise InvalidOutputPathError(f"Error writing output file: {str(e)}", str(output_path))
        except Exception as e:
            raise InvalidOutputPathError(
                f"Unexpected error writing output: {str(e)}", str(output_path)
            )
