"""Unit tests for custom exceptions."""

import pytest

from src.data_sanitizer.exceptions import (
    FileNotFoundError,
    InvalidOutputPathError,
    JSONParseError,
    SanitizerError,
)


class TestSanitizerError:
    """Tests for the base SanitizerError exception."""

    def test_sanitizer_error_initialization(self) -> None:
        """Test that SanitizerError can be initialized with a message."""
        error = SanitizerError("Test error message")
        assert str(error) == "Test error message"

    def test_sanitizer_error_is_exception(self) -> None:
        """Test that SanitizerError is an Exception."""
        error = SanitizerError("Test error")
        assert isinstance(error, Exception)


class TestFileNotFoundError:
    """Tests for the FileNotFoundError exception."""

    def test_file_not_found_error_initialization(self) -> None:
        """Test FileNotFoundError initialization with message."""
        error = FileNotFoundError("File not found")
        assert str(error) == "File not found"
        assert error.file_path is None

    def test_file_not_found_error_with_path(self) -> None:
        """Test FileNotFoundError initialization with file path."""
        error = FileNotFoundError("File not found", file_path="/path/to/file.json")
        assert str(error) == "File not found"
        assert error.file_path == "/path/to/file.json"

    def test_file_not_found_error_is_sanitizer_error(self) -> None:
        """Test that FileNotFoundError is a SanitizerError."""
        error = FileNotFoundError("Test error")
        assert isinstance(error, SanitizerError)


class TestJSONParseError:
    """Tests for the JSONParseError exception."""

    def test_json_parse_error_initialization(self) -> None:
        """Test JSONParseError initialization with line and column."""
        error = JSONParseError("Invalid JSON", line=5, column=12)
        assert "Invalid JSON" in str(error)
        assert "line 5" in str(error)
        assert "column 12" in str(error)
        assert error.line == 5
        assert error.column == 12

    def test_json_parse_error_attributes(self) -> None:
        """Test that JSONParseError stores line and column attributes."""
        error = JSONParseError("Unexpected token", line=10, column=25)
        assert error.line == 10
        assert error.column == 25

    def test_json_parse_error_message_format(self) -> None:
        """Test that JSONParseError formats the message correctly."""
        error = JSONParseError("Missing comma", line=3, column=8)
        expected = "Missing comma at line 3, column 8"
        assert str(error) == expected

    def test_json_parse_error_is_sanitizer_error(self) -> None:
        """Test that JSONParseError is a SanitizerError."""
        error = JSONParseError("Test error", line=1, column=1)
        assert isinstance(error, SanitizerError)


class TestInvalidOutputPathError:
    """Tests for the InvalidOutputPathError exception."""

    def test_invalid_output_path_error_initialization(self) -> None:
        """Test InvalidOutputPathError initialization with message."""
        error = InvalidOutputPathError("Invalid output path")
        assert str(error) == "Invalid output path"
        assert error.output_path is None

    def test_invalid_output_path_error_with_path(self) -> None:
        """Test InvalidOutputPathError initialization with output path."""
        error = InvalidOutputPathError(
            "Directory does not exist", output_path="/invalid/path/output.json"
        )
        assert str(error) == "Directory does not exist"
        assert error.output_path == "/invalid/path/output.json"

    def test_invalid_output_path_error_is_sanitizer_error(self) -> None:
        """Test that InvalidOutputPathError is a SanitizerError."""
        error = InvalidOutputPathError("Test error")
        assert isinstance(error, SanitizerError)


class TestExceptionHierarchy:
    """Tests for exception hierarchy and catching."""

    def test_catch_all_sanitizer_errors(self) -> None:
        """Test that all custom exceptions can be caught as SanitizerError."""
        exceptions = [
            FileNotFoundError("File error"),
            JSONParseError("Parse error", line=1, column=1),
            InvalidOutputPathError("Path error"),
        ]

        for exc in exceptions:
            try:
                raise exc
            except SanitizerError:
                pass  # Successfully caught as SanitizerError
            else:
                pytest.fail(f"{type(exc).__name__} was not caught as SanitizerError")

    def test_catch_specific_exceptions(self) -> None:
        """Test that specific exceptions can be caught individually."""
        # Test FileNotFoundError
        with pytest.raises(FileNotFoundError):
            raise FileNotFoundError("File not found")

        # Test JSONParseError
        with pytest.raises(JSONParseError):
            raise JSONParseError("Parse error", line=1, column=1)

        # Test InvalidOutputPathError
        with pytest.raises(InvalidOutputPathError):
            raise InvalidOutputPathError("Invalid path")
