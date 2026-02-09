"""Streamlit web interface for the Smart Data Sanitizer.

This module provides a user-friendly web application for sanitizing JSON files
by detecting and replacing PII (Personally Identifiable Information) with fake data.
The interface allows users to upload JSON files, configure output settings, trigger
sanitization, view results, and download sanitized files.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from data_sanitizer.detectors.credit_card_detector import CreditCardDetector
from data_sanitizer.detectors.email_detector import EmailDetector
from data_sanitizer.detectors.name_detector import NameDetector
from data_sanitizer.detectors.phone_detector import PhoneDetector
from data_sanitizer.models import SanitizationResult
from data_sanitizer.replacer import Replacer
from data_sanitizer.sanitizer import Sanitizer


def validate_output_filename(filename: str) -> str:
    """Validate and normalize output filename.

    Ensures the filename is not empty and has a .json extension.

    Args:
        filename: User-provided output filename

    Returns:
        Normalized filename with .json extension

    Raises:
        ValueError: If filename is empty or contains only whitespace

    Example:
        >>> validate_output_filename("myfile")
        'myfile.json'
        >>> validate_output_filename("data.json")
        'data.json'
    """
    if not filename or filename.strip() == "":
        raise ValueError("Output filename cannot be empty")

    filename = filename.strip()
    if not filename.endswith(".json"):
        filename += ".json"

    return filename


def initialize_sanitizer() -> Sanitizer:
    """Initialize sanitizer with all detectors and replacer.

    Creates a Sanitizer instance configured with all four PII detectors
    (EmailDetector, PhoneDetector, NameDetector, CreditCardDetector) and
    a Replacer instance for generating fake data replacements.

    Returns:
        Configured Sanitizer instance ready for use

    Example:
        >>> sanitizer = initialize_sanitizer()
        >>> isinstance(sanitizer, Sanitizer)
        True
    """
    # Initialize all four detectors
    detectors = [
        EmailDetector(),
        PhoneDetector(),
        NameDetector(),
        CreditCardDetector(),
    ]

    # Create Replacer instance with seed=None for random fake data
    replacer = Replacer(seed=None)

    # Create and return Sanitizer instance
    return Sanitizer(detectors=detectors, replacer=replacer)


def process_sanitization(
    uploaded_file: UploadedFile, output_filename: str
) -> tuple[SanitizationResult, bytes | None]:
    """Process file sanitization.

    Handles the complete sanitization workflow: writes the uploaded file to a
    temporary location, initializes the sanitizer, performs sanitization, and
    reads the sanitized output. Temporary files are automatically cleaned up.

    Args:
        uploaded_file: Streamlit uploaded file object containing JSON data
        output_filename: Desired output filename (should include .json extension)

    Returns:
        Tuple containing:
        - SanitizationResult with statistics and status
        - Sanitized file content as bytes (None if sanitization failed)

    Example:
        >>> result, content = process_sanitization(uploaded_file, "output.json")
        >>> if result.success:
        ...     print(f"Processed {result.records_processed} records")
    """
    # Create temporary directory for file operations
    with TemporaryDirectory() as tmpdir:
        # Write uploaded file content to temporary input file
        input_path = Path(tmpdir) / "input.json"
        input_path.write_bytes(uploaded_file.getvalue())

        # Create output path in temporary directory
        output_path = Path(tmpdir) / output_filename

        # Initialize sanitizer and call sanitize_file()
        sanitizer = initialize_sanitizer()
        result = sanitizer.sanitize_file(input_path, output_path)

        # If successful, read sanitized file content as bytes
        if result.success:
            file_content = output_path.read_bytes()
            return result, file_content

        # Return result with None content if failed
        return result, None


def render_header() -> None:
    """Render the application header with title and description.

    Displays the main title and a brief description of the application's
    purpose using Streamlit's title and markdown components.

    Example:
        >>> render_header()  # Displays title and description in Streamlit UI
    """
    st.title("Smart Data Sanitizer - Web Interface")
    st.markdown(
        "Sanitize JSON files by detecting and replacing PII "
        "(emails, phone numbers, names, credit card numbers) with fake data."
    )

    # Add usage instructions in an info box
    st.info(
        "**How to use:**\n\n"
        "1. Upload a JSON file containing data to sanitize\n"
        "2. Specify an output filename (optional - defaults to 'sanitized_output.json')\n"
        "3. Click 'Sanitize File' to process your data\n"
        "4. Download the sanitized file with all PII replaced"
    )


def render_file_upload() -> UploadedFile | None:
    """Render file upload widget and return uploaded file.

    Creates a file uploader widget that accepts JSON files and provides
    helpful instructions to the user.

    Returns:
        Uploaded file object or None if no file uploaded

    Example:
        >>> uploaded_file = render_file_upload()
        >>> if uploaded_file:
        ...     print(f"File uploaded: {uploaded_file.name}")
    """
    uploaded_file = st.file_uploader(
        "📁 Upload JSON File",
        type=["json"],
        help="Select a JSON file containing data to sanitize. "
        "The file should contain valid JSON data with records to process.",
    )
    return uploaded_file


def render_output_config() -> str:
    """Render output file configuration input.

    Creates a text input widget for specifying the output filename with
    a default value and helpful label.

    Returns:
        Output filename string (may need validation and normalization)

    Example:
        >>> filename = render_output_config()
        >>> print(f"Output filename: {filename}")
    """
    filename = st.text_input(
        "📝 Output Filename",
        value="sanitized_output.json",
        placeholder="e.g., sanitized_output.json or my_data.json",
        help="Specify the name for the sanitized output file. "
        "The .json extension will be added automatically if not provided.",
    )
    return filename


def render_results(result: SanitizationResult, output_path: Path) -> None:
    """Render sanitization results and statistics.

    Displays the results of the sanitization process, including success/failure
    status and detailed statistics about records processed and PII detected.

    Args:
        result: SanitizationResult from sanitization process
        output_path: Path to sanitized output file

    Example:
        >>> result = SanitizationResult(
        ...     success=True,
        ...     records_processed=100,
        ...     pii_fields_detected=25,
        ...     pii_replacements_made=30,
        ...     error_message=None
        ... )
        >>> render_results(result, Path("output.json"))
    """
    if result.success:
        st.success("✅ Sanitization completed successfully!")

        # Display statistics using metrics for better visual presentation
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Records Processed", result.records_processed)

        with col2:
            st.metric("PII Fields Detected", result.pii_fields_detected)

        with col3:
            st.metric("PII Replacements Made", result.pii_replacements_made)

        # Display output file path
        st.info(f"📄 Output file: {output_path.name}")
    else:
        # Handle failure case
        st.error(f"❌ Sanitization failed: {result.error_message}")


def render_download_button(file_content: bytes, filename: str) -> None:
    """Render download button for sanitized file.

    Creates a download button that allows users to download the sanitized
    JSON file with the specified filename.

    Args:
        file_content: Sanitized file content as bytes
        filename: Filename to use for download

    Example:
        >>> content = b'{"data": "sanitized"}'
        >>> render_download_button(content, "output.json")
    """
    st.download_button(
        label="⬇️ Download Sanitized File",
        data=file_content,
        file_name=filename,
        mime="application/json",
        help="Click to download the sanitized JSON file to your computer.",
    )


def main() -> None:
    """Main entry point for the Streamlit application.

    Sets up the page configuration, renders the UI components,
    and handles the sanitization workflow. This function orchestrates
    the entire user interface and processing flow.

    Example:
        >>> main()  # Starts the Streamlit application
    """
    # Set page configuration
    st.set_page_config(
        page_title="Smart Data Sanitizer",
        page_icon="🔒",
        layout="centered",
    )

    # Render header
    render_header()

    # Initialize session state if needed
    if "sanitization_result" not in st.session_state:
        st.session_state["sanitization_result"] = None
    if "sanitized_content" not in st.session_state:
        st.session_state["sanitized_content"] = None
    if "output_filename" not in st.session_state:
        st.session_state["output_filename"] = None

    # File upload section
    st.divider()
    st.subheader("📁 Step 1: Upload Your File")
    uploaded_file = render_file_upload()

    # Display file info if file uploaded
    if uploaded_file:
        # Check if file has .json extension
        if not uploaded_file.name.lower().endswith('.json'):
            st.warning(
                "⚠️ Warning: The uploaded file does not have a .json extension. "
                "Please ensure you are uploading a valid JSON file."
            )
        st.info(f"📄 File: {uploaded_file.name} ({uploaded_file.size:,} bytes)")
    else:
        st.warning("⚠️ Please upload a JSON file to begin.")

    # Output configuration section
    st.divider()
    st.subheader("📝 Step 2: Configure Output")
    output_filename = render_output_config()

    # Validate filename
    validated_filename = None
    try:
        validated_filename = validate_output_filename(output_filename)
        st.session_state["output_filename"] = validated_filename
    except ValueError as e:
        st.error(f"❌ Invalid filename: {e}")
        validated_filename = None

    # Sanitize button section
    st.divider()
    st.subheader("🔒 Step 3: Sanitize Your Data")

    # Determine if button should be enabled
    button_enabled = uploaded_file is not None and validated_filename is not None

    # Create sanitize button
    if st.button("🔒 Sanitize File", disabled=not button_enabled, type="primary"):
        # Show progress spinner
        with st.spinner("Processing... Please wait while we sanitize your file."):
            try:
                # Call process_sanitization
                result, file_content = process_sanitization(uploaded_file, validated_filename)

                # Store result and file content in session state
                st.session_state["sanitization_result"] = result
                st.session_state["sanitized_content"] = file_content
            except Exception as e:
                # Catch any unexpected errors and store error result
                error_result = SanitizationResult(
                    success=False,
                    records_processed=0,
                    pii_fields_detected=0,
                    pii_replacements_made=0,
                    error_message=f"An unexpected error occurred: {str(e)}. "
                    "Please check your input file and try again."
                )
                st.session_state["sanitization_result"] = error_result
                st.session_state["sanitized_content"] = None

    # Results display section
    if st.session_state["sanitization_result"] is not None:
        st.divider()
        st.subheader("📊 Step 4: View Results & Download")
        result = st.session_state["sanitization_result"]

        # Display results (handles both success and failure)
        render_results(result, Path(st.session_state["output_filename"]))

        # Show download button only for successful sanitization
        if result.success and st.session_state["sanitized_content"] is not None:
            st.write("")  # Add spacing
            render_download_button(
                st.session_state["sanitized_content"],
                st.session_state["output_filename"]
            )


if __name__ == "__main__":
    main()
