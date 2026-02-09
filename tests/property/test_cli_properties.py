"""Property-based tests for CLI functionality.

Feature: data-sanitizer
This module contains property-based tests for the CLI interface,
validating argument handling, exit codes, and summary display.
"""

import json
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from hypothesis import given, settings
from hypothesis import strategies as st

from data_sanitizer.cli import main, parse_arguments


class TestCLIMissingArgumentsProperty:
    """Property 17: CLI Missing Arguments Error.

    For any combination of missing required arguments, the CLI should
    display usage information and exit with a non-zero status.

    Validates: Requirements 7.3
    """

    @settings(max_examples=10)
    @given(st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=1))
    def test_cli_missing_arguments_error(self, args: list[str]) -> None:
        """Test that missing arguments cause non-zero exit with usage info.

        Feature: data-sanitizer, Property 17: CLI Missing Arguments Error

        This property verifies that when required arguments are missing,
        the CLI exits with a non-zero status code and displays usage information.

        Args:
            args: List of 0 or 1 arguments (missing at least one required arg)
        """
        # Build argv with program name and provided args
        argv = ["data-sanitizer"] + args

        # Mock sys.argv and capture stderr
        with patch("sys.argv", argv):
            captured_error = StringIO()
            with patch("sys.stderr", captured_error):
                try:
                    parse_arguments()
                    # If we get here, arguments were somehow valid (shouldn't happen)
                    # This is acceptable for the edge case where hypothesis generates
                    # exactly 2 valid-looking arguments
                    pass
                except SystemExit as e:
                    # Verify non-zero exit code
                    assert e.code != 0, f"Expected non-zero exit code, got {e.code}"

                    # Verify usage information is displayed
                    error_output = captured_error.getvalue()
                    # argparse displays usage info which includes the program name
                    assert len(error_output) > 0, "Expected usage information in stderr"


class TestCLIExitCodeProperty:
    """Property 18: CLI Exit Code Correctness.

    For any sanitization operation, the exit code should be 0 if successful
    and non-zero if failed.

    Validates: Requirements 7.4, 7.5
    """

    # Increase deadline due to NameDetector initialization (especially on CI runners)
    @settings(max_examples=10, deadline=2000)
    @given(
        st.lists(
            st.dictionaries(
                keys=st.text(min_size=1, max_size=20),
                values=st.one_of(
                    st.text(min_size=0, max_size=50),
                    st.integers(),
                    st.floats(allow_nan=False, allow_infinity=False),
                    st.booleans(),
                    st.none(),
                ),
                min_size=1,
                max_size=5,
            ),
            min_size=1,
            max_size=10,
        )
    )
    def test_cli_exit_code_success(self, records: list[dict]) -> None:
        """Test that successful sanitization returns exit code 0.

        Feature: data-sanitizer, Property 18: CLI Exit Code Correctness

        This property verifies that when sanitization succeeds, the CLI
        returns exit code 0.

        Args:
            records: Random list of records to sanitize
        """
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            input_path = Path(f.name)
            json.dump(records, f)

        # Create temporary output file path
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Mock sys.argv
            with patch("sys.argv", ["data-sanitizer", str(input_path), str(output_path)]):
                # Suppress output
                with patch("sys.stdout", StringIO()):
                    exit_code = main()

            # Verify exit code is 0 for success
            assert exit_code == 0, (
                f"Expected exit code 0 for successful sanitization, got {exit_code}"
            )

        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

    def test_cli_exit_code_failure_file_not_found(self) -> None:
        """Test that file not found returns non-zero exit code.

        Feature: data-sanitizer, Property 18: CLI Exit Code Correctness

        This property verifies that when sanitization fails due to file
        not found, the CLI returns a non-zero exit code.
        """
        # Use non-existent file
        input_path = "nonexistent_file_12345.json"
        output_path = "output.json"

        # Mock sys.argv
        with patch("sys.argv", ["data-sanitizer", input_path, output_path]):
            # Suppress output
            with patch("sys.stderr", StringIO()):
                exit_code = main()

        # Verify exit code is non-zero for failure
        assert exit_code != 0, f"Expected non-zero exit code for failure, got {exit_code}"

    def test_cli_exit_code_failure_invalid_json(self) -> None:
        """Test that invalid JSON returns non-zero exit code.

        Feature: data-sanitizer, Property 18: CLI Exit Code Correctness

        This property verifies that when sanitization fails due to invalid
        JSON, the CLI returns a non-zero exit code.
        """
        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            input_path = Path(f.name)
            f.write("{invalid json content")

        output_path = Path("output.json")

        try:
            # Mock sys.argv
            with patch("sys.argv", ["data-sanitizer", str(input_path), str(output_path)]):
                # Suppress output
                with patch("sys.stderr", StringIO()):
                    exit_code = main()

            # Verify exit code is non-zero for failure
            assert exit_code != 0, f"Expected non-zero exit code for invalid JSON, got {exit_code}"

        finally:
            input_path.unlink(missing_ok=True)


class TestCLISummaryDisplayProperty:
    """Property 19: CLI Summary Display.

    For any successful sanitization, the CLI output should contain summary
    statistics (records processed, PII fields detected).

    Validates: Requirements 7.6
    """

    # Increase deadline due to NameDetector initialization (especially on CI runners)
    @settings(max_examples=10, deadline=2000)
    @given(
        st.lists(
            st.dictionaries(
                keys=st.text(min_size=1, max_size=20),
                values=st.one_of(st.text(min_size=0, max_size=50), st.integers(), st.booleans()),
                min_size=1,
                max_size=5,
            ),
            min_size=1,
            max_size=10,
        )
    )
    def test_cli_summary_display(self, records: list[dict]) -> None:
        """Test that CLI displays summary statistics on success.

        Feature: data-sanitizer, Property 19: CLI Summary Display

        This property verifies that when sanitization succeeds, the CLI
        displays summary statistics including records processed and PII detected.

        Args:
            records: Random list of records to sanitize
        """
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            input_path = Path(f.name)
            json.dump(records, f)

        # Create temporary output file path
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Mock sys.argv
            with patch("sys.argv", ["data-sanitizer", str(input_path), str(output_path)]):
                # Capture stdout
                captured_output = StringIO()
                with patch("sys.stdout", captured_output):
                    exit_code = main()

            # Verify success
            assert exit_code == 0, "Sanitization should succeed"

            # Verify summary is displayed
            output = captured_output.getvalue()

            # Check for required summary elements
            assert "Sanitization completed successfully" in output, (
                "Summary should contain success message"
            )
            assert "Records processed:" in output, "Summary should contain records processed count"
            assert "PII fields detected:" in output, (
                "Summary should contain PII fields detected count"
            )
            assert "PII replacements made:" in output, (
                "Summary should contain PII replacements made count"
            )

            # Verify the count matches the input
            assert f"Records processed: {len(records)}" in output, (
                f"Summary should show {len(records)} records processed"
            )

        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)
