"""Custom exceptions for the data sanitizer.

This module defines custom exception classes for handling various error
conditions that may occur during data sanitization operations.
"""


class SanitizerError(Exception):
    """Base exception for all sanitizer-related errors.

    This is the parent class for all custom exceptions in the data sanitizer.
    It can be used to catch any sanitizer-specific error.
    """

    pass


class FileNotFoundError(SanitizerError):
    """Exception raised when the input file cannot be found.

    This exception is raised when attempting to sanitize a file that does not
    exist at the specified path.

    Attributes:
        message: Explanation of the error
        file_path: Path to the file that was not found
    """

    def __init__(self, message: str, file_path: str | None = None) -> None:
        """Initialize FileNotFoundError.

        Args:
            message: Error message describing the issue
            file_path: Optional path to the file that was not found
        """
        self.file_path = file_path
        super().__init__(message)


class JSONParseError(SanitizerError):
    """Exception raised when JSON parsing fails.

    This exception is raised when the input file contains invalid JSON.
    It includes position information (line and column) to help identify
    where the parsing error occurred.

    Attributes:
        message: Explanation of the error
        line: Line number where the error occurred
        column: Column number where the error occurred
    """

    def __init__(self, message: str, line: int, column: int) -> None:
        """Initialize JSONParseError with position information.

        Args:
            message: Error message describing the parsing issue
            line: Line number where the error occurred (1-indexed)
            column: Column number where the error occurred (1-indexed)
        """
        self.line = line
        self.column = column
        error_msg = f"{message} at line {line}, column {column}"
        super().__init__(error_msg)


class InvalidOutputPathError(SanitizerError):
    """Exception raised when the output path is invalid.

    This exception is raised when the output directory does not exist or
    when the output path cannot be written to.

    Attributes:
        message: Explanation of the error
        output_path: Path that was invalid
    """

    def __init__(self, message: str, output_path: str | None = None) -> None:
        """Initialize InvalidOutputPathError.

        Args:
            message: Error message describing the issue
            output_path: Optional path that was invalid
        """
        self.output_path = output_path
        super().__init__(message)
