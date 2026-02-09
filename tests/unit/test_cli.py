"""Unit tests for the CLI module."""

import json
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from data_sanitizer.cli import main, parse_arguments


class TestParseArguments:
    """Tests for argument parsing."""

    def test_parse_required_arguments(self):
        """Test parsing required input and output file arguments."""
        with patch("sys.argv", ["data-sanitizer", "input.json", "output.json"]):
            args = parse_arguments()

            assert args.input_file == "input.json"
            assert args.output_file == "output.json"
            assert args.verbose is False

    def test_parse_with_verbose_flag(self):
        """Test parsing with --verbose flag."""
        with patch("sys.argv", ["data-sanitizer", "input.json", "output.json", "--verbose"]):
            args = parse_arguments()

            assert args.input_file == "input.json"
            assert args.output_file == "output.json"
            assert args.verbose is True

    def test_parse_missing_arguments(self):
        """Test that missing required arguments causes SystemExit."""
        with patch("sys.argv", ["data-sanitizer"]):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()

            # argparse exits with code 2 for missing arguments
            assert exc_info.value.code == 2

    def test_parse_missing_output_file(self):
        """Test that missing output file argument causes SystemExit."""
        with patch("sys.argv", ["data-sanitizer", "input.json"]):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()

            assert exc_info.value.code == 2


class TestMainFunction:
    """Tests for the main function."""

    def test_main_successful_sanitization(self):
        """Test main function with successful sanitization."""
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            input_path = Path(f.name)
            json.dump([{"name": "John Doe", "age": 30}], f)

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

            # Verify exit code
            assert exit_code == 0

            # Verify output message
            output = captured_output.getvalue()
            assert "Sanitization completed successfully" in output
            assert "Records processed:" in output
            assert "PII fields detected:" in output
            assert "PII replacements made:" in output

            # Verify output file was created
            assert output_path.exists()

        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

    def test_main_with_verbose_flag(self):
        """Test main function with verbose flag."""
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            input_path = Path(f.name)
            json.dump([{"name": "test", "age": 30}], f)

        # Create temporary output file path
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Mock sys.argv with --verbose
            with patch(
                "sys.argv", ["data-sanitizer", str(input_path), str(output_path), "--verbose"]
            ):
                # Capture stdout
                captured_output = StringIO()
                with patch("sys.stdout", captured_output):
                    exit_code = main()

            # Verify exit code
            assert exit_code == 0

            # Verify verbose output
            output = captured_output.getvalue()
            assert "Smart Data Sanitizer" in output
            assert "Input file:" in output
            assert "Output file:" in output
            assert "Initialized detectors:" in output
            assert "EmailDetector" in output
            assert "PhoneDetector" in output
            assert "NameDetector" in output
            assert "CreditCardDetector" in output
            assert "Starting sanitization..." in output

        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

    def test_main_file_not_found(self):
        """Test main function with non-existent input file."""
        input_path = "nonexistent_file.json"
        output_path = "output.json"

        # Mock sys.argv
        with patch("sys.argv", ["data-sanitizer", input_path, output_path]):
            # Capture stderr
            captured_error = StringIO()
            with patch("sys.stderr", captured_error):
                exit_code = main()

        # Verify exit code is non-zero
        assert exit_code == 1

        # Verify error message
        error = captured_error.getvalue()
        assert "Error:" in error
        assert "not found" in error.lower()

    def test_main_invalid_json(self):
        """Test main function with invalid JSON input."""
        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            input_path = Path(f.name)
            f.write("{invalid json")

        output_path = Path("output.json")

        try:
            # Mock sys.argv
            with patch("sys.argv", ["data-sanitizer", str(input_path), str(output_path)]):
                # Capture stderr
                captured_error = StringIO()
                with patch("sys.stderr", captured_error):
                    exit_code = main()

            # Verify exit code is non-zero
            assert exit_code == 1

            # Verify error message
            error = captured_error.getvalue()
            assert "Error:" in error

        finally:
            input_path.unlink(missing_ok=True)

    def test_main_keyboard_interrupt(self):
        """Test main function handles KeyboardInterrupt gracefully."""
        # Mock parse_arguments to raise KeyboardInterrupt
        with patch("data_sanitizer.cli.parse_arguments", side_effect=KeyboardInterrupt()):
            # Capture stderr
            captured_error = StringIO()
            with patch("sys.stderr", captured_error):
                exit_code = main()

        # Verify exit code is non-zero
        assert exit_code == 1

        # Verify error message
        error = captured_error.getvalue()
        assert "cancelled by user" in error.lower()

    def test_main_unexpected_error(self):
        """Test main function handles unexpected errors gracefully."""
        # Mock parse_arguments to raise unexpected error
        with patch(
            "data_sanitizer.cli.parse_arguments", side_effect=RuntimeError("Unexpected error")
        ):
            # Capture stderr
            captured_error = StringIO()
            with patch("sys.stderr", captured_error):
                exit_code = main()

        # Verify exit code is non-zero
        assert exit_code == 1

        # Verify error message
        error = captured_error.getvalue()
        assert "Unexpected error" in error

    def test_main_displays_summary_statistics(self):
        """Test that main displays summary statistics correctly."""
        # Create temporary input file with PII
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            input_path = Path(f.name)
            json.dump(
                [
                    {"email": "john@example.com", "age": 30},
                    {"email": "jane@example.com", "phone": "555-1234"},
                ],
                f,
            )

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

            # Verify exit code
            assert exit_code == 0

            # Verify summary contains statistics
            output = captured_output.getvalue()
            assert "Records processed: 2" in output
            # At least 2 PII fields should be detected (emails)
            assert "PII fields detected:" in output
            assert "PII replacements made:" in output

        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

    def test_main_exit_code_zero_on_success(self):
        """Test that main returns exit code 0 on success."""
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            input_path = Path(f.name)
            json.dump([{"name": "test"}], f)

        # Create temporary output file path
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Mock sys.argv
            with patch("sys.argv", ["data-sanitizer", str(input_path), str(output_path)]):
                # Suppress output
                with patch("sys.stdout", StringIO()):
                    exit_code = main()

            # Verify exit code is 0
            assert exit_code == 0

        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

    def test_main_exit_code_nonzero_on_failure(self):
        """Test that main returns non-zero exit code on failure."""
        input_path = "nonexistent.json"
        output_path = "output.json"

        # Mock sys.argv
        with patch("sys.argv", ["data-sanitizer", input_path, output_path]):
            # Suppress output
            with patch("sys.stderr", StringIO()):
                exit_code = main()

        # Verify exit code is non-zero
        assert exit_code == 1


class TestCLIIntegration:
    """Integration tests for CLI workflow."""

    def test_cli_end_to_end_workflow(self):
        """Test complete CLI workflow from input to output."""
        # Create input data with various PII types
        input_data = [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "555-1234",
                "age": 30,
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane@example.com",
                "department": "Engineering",
            },
        ]

        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            input_path = Path(f.name)
            json.dump(input_data, f)

        # Create temporary output file path
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Run CLI
            with patch("sys.argv", ["data-sanitizer", str(input_path), str(output_path)]):
                with patch("sys.stdout", StringIO()):
                    exit_code = main()

            # Verify success
            assert exit_code == 0

            # Read output file
            with open(output_path) as f:
                output_data = json.load(f)

            # Verify structure preserved
            assert len(output_data) == 2
            assert output_data[0]["id"] == 1
            assert output_data[0]["age"] == 30
            assert output_data[1]["id"] == 2
            assert output_data[1]["department"] == "Engineering"

            # Verify PII was replaced (emails should be different)
            assert output_data[0]["email"] != "john@example.com"
            assert output_data[1]["email"] != "jane@example.com"

            # Verify output is valid JSON
            assert isinstance(output_data, list)
            assert all(isinstance(record, dict) for record in output_data)

        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)
