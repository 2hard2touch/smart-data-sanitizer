"""Command-line interface for the Smart Data Sanitizer.

This module provides the CLI entry point for sanitizing JSON files containing PII.
It handles argument parsing, detector initialization, and user-friendly error display.
"""

import argparse
import sys
from pathlib import Path

from data_sanitizer.detectors import (
    CreditCardDetector,
    EmailDetector,
    PhoneDetector,
)
from data_sanitizer.detectors.name_detector import NameDetector
from data_sanitizer.replacer import Replacer
from data_sanitizer.sanitizer import Sanitizer


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments containing input_file, output_file, and optional flags

    Example:
        >>> args = parse_arguments()
        >>> print(args.input_file)
        'input.json'
    """
    parser = argparse.ArgumentParser(
        prog="data-sanitizer",
        description=(
            "Automatically detect and replace PII in JSON datasets "
            "with semantically valid fake data"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  data-sanitizer input.json output.json
  data-sanitizer dirty_data.json clean_data.json --verbose

For more information, visit: https://github.com/yourusername/data-sanitizer
        """,
    )

    # Required arguments
    parser.add_argument(
        "input_file", type=str, help="Path to input JSON file containing data to sanitize"
    )

    parser.add_argument(
        "output_file",
        type=str,
        help="Path to output JSON file where sanitized data will be written",
    )

    # Optional arguments
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output with detailed processing information",
    )

    return parser.parse_args()


def main() -> int:
    """Entry point for the CLI application.

    This function orchestrates the entire sanitization workflow:
    1. Parse command-line arguments
    2. Initialize detectors and replacer
    3. Create sanitizer and process the file
    4. Display results or error messages
    5. Return appropriate exit code

    Returns:
        Exit code: 0 for success, 1 for failure

    Example:
        >>> sys.exit(main())
    """
    try:
        # Parse arguments
        args = parse_arguments()

        if args.verbose:
            print("Smart Data Sanitizer")
            print("=" * 50)
            print(f"Input file: {args.input_file}")
            print(f"Output file: {args.output_file}")
            print()

        # Initialize detectors
        detectors = [
            EmailDetector(),
            PhoneDetector(),
            NameDetector(),
            CreditCardDetector(),
        ]

        if args.verbose:
            print("Initialized detectors:")
            for detector in detectors:
                print(f"  - {detector.__class__.__name__}")
            print()

        # Initialize replacer (no seed for random fake data)
        replacer = Replacer(seed=None)

        # Initialize sanitizer
        sanitizer = Sanitizer(detectors, replacer)

        # Convert paths to Path objects
        input_path = Path(args.input_file)
        output_path = Path(args.output_file)

        if args.verbose:
            print("Starting sanitization...")
            print()

        # Sanitize the file
        result = sanitizer.sanitize_file(input_path, output_path)

        # Check if sanitization was successful
        if not result.success:
            print(f"Error: {result.error_message}", file=sys.stderr)
            return 1

        # Display summary statistics
        print("Sanitization completed successfully!")
        print()
        print("Summary:")
        print(f"  Records processed: {result.records_processed}")
        print(f"  PII fields detected: {result.pii_fields_detected}")
        print(f"  PII replacements made: {result.pii_replacements_made}")
        print()
        print(f"Sanitized data written to: {args.output_file}")

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 1

    except Exception as e:
        # Catch any unexpected errors
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        if args.verbose if "args" in locals() else False:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
