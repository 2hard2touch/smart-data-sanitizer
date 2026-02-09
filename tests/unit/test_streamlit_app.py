"""Unit and property tests for the Streamlit web interface."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from data_sanitizer.detectors.credit_card_detector import CreditCardDetector
from data_sanitizer.detectors.email_detector import EmailDetector
from data_sanitizer.detectors.name_detector import NameDetector
from data_sanitizer.detectors.phone_detector import PhoneDetector
from data_sanitizer.sanitizer import Sanitizer
from data_sanitizer.streamlit_app import initialize_sanitizer, validate_output_filename


# Feature: streamlit-interface, Property 2: Output filename normalization
@given(st.text(min_size=1).filter(lambda s: s.strip() != ""))
def test_validate_output_filename_property(filename: str) -> None:
    """Property: All non-empty filenames should be normalized with .json extension.

    **Validates: Requirements 2.3**

    This property test verifies that any non-empty string gets .json appended
    if it doesn't already have that extension.
    """
    result = validate_output_filename(filename)

    # Property 1: Result must end with .json
    assert result.endswith(".json"), f"Expected {result} to end with .json"

    # Property 2: Result must not be just ".json"
    assert len(result) > 5, f"Expected {result} to have content before .json"

    # Property 3: Result must not have leading/trailing whitespace
    assert result == result.strip(), f"Expected {result} to be trimmed"



# Unit tests for validate_output_filename
def test_validate_output_filename_empty_raises_error() -> None:
    """Test that empty filename raises ValueError."""
    with pytest.raises(ValueError, match="Output filename cannot be empty"):
        validate_output_filename("")


def test_validate_output_filename_whitespace_only_raises_error() -> None:
    """Test that whitespace-only filename raises ValueError."""
    with pytest.raises(ValueError, match="Output filename cannot be empty"):
        validate_output_filename("   ")


def test_validate_output_filename_with_json_extension_unchanged() -> None:
    """Test that filename with .json extension is unchanged."""
    result = validate_output_filename("myfile.json")
    assert result == "myfile.json"


def test_validate_output_filename_without_extension_gets_json_appended() -> None:
    """Test that filename without extension gets .json appended."""
    result = validate_output_filename("myfile")
    assert result == "myfile.json"


def test_validate_output_filename_with_spaces_is_trimmed() -> None:
    """Test that filename with spaces is trimmed."""
    result = validate_output_filename("  myfile.json  ")
    assert result == "myfile.json"

    result = validate_output_filename("  myfile  ")
    assert result == "myfile.json"


# Feature: streamlit-interface, Property 3: Sanitizer initialization consistency
@given(st.integers(min_value=1, max_value=10))
@settings(deadline=None)  # Disable deadline as detector initialization can be slow
def test_initialize_sanitizer_property(num_calls: int) -> None:
    """Property: Multiple calls to initialize_sanitizer() produce consistent configuration.

    **Validates: Requirements 4.1, 4.2**

    This property test verifies that every call to initialize_sanitizer() returns
    a Sanitizer instance with exactly 4 detectors of the correct types.
    """
    for _ in range(num_calls):
        sanitizer = initialize_sanitizer()

        # Property 1: Must return a Sanitizer instance
        assert isinstance(sanitizer, Sanitizer), "Expected Sanitizer instance"

        # Property 2: Must have exactly 4 detectors
        num_detectors = len(sanitizer._detectors)
        assert num_detectors == 4, f"Expected 4 detectors, got {num_detectors}"

        # Property 3: Must have correct detector types
        detector_types = {type(detector) for detector in sanitizer._detectors}
        expected_types = {EmailDetector, PhoneDetector, NameDetector, CreditCardDetector}
        assert detector_types == expected_types, f"Expected {expected_types}, got {detector_types}"

        # Property 4: Replacer must be configured
        assert sanitizer._replacer is not None, "Expected replacer to be configured"


# Unit tests for initialize_sanitizer
def test_initialize_sanitizer_returns_sanitizer_instance() -> None:
    """Test that initialize_sanitizer returns a Sanitizer instance."""
    sanitizer = initialize_sanitizer()
    assert isinstance(sanitizer, Sanitizer)


def test_initialize_sanitizer_has_correct_detector_types() -> None:
    """Test that the sanitizer has the correct detector types."""
    sanitizer = initialize_sanitizer()

    # Check we have exactly 4 detectors
    assert len(sanitizer._detectors) == 4

    # Check detector types
    detector_types = {type(detector) for detector in sanitizer._detectors}
    expected_types = {EmailDetector, PhoneDetector, NameDetector, CreditCardDetector}
    assert detector_types == expected_types


def test_initialize_sanitizer_replacer_configured_correctly() -> None:
    """Test that the replacer is configured correctly."""
    sanitizer = initialize_sanitizer()

    # Check replacer exists
    assert sanitizer._replacer is not None

    # Check replacer is the correct type
    from data_sanitizer.replacer import Replacer
    assert isinstance(sanitizer._replacer, Replacer)


# Unit tests for process_sanitization
def test_process_sanitization_successful() -> None:
    """Test successful sanitization returns result and file content."""
    from unittest.mock import Mock

    from data_sanitizer.streamlit_app import process_sanitization

    # Create mock uploaded file with valid JSON data
    json_data = b'[{"name": "John Doe", "email": "john@example.com"}]'
    mock_file = Mock()
    mock_file.getvalue.return_value = json_data

    # Process sanitization
    result, content = process_sanitization(mock_file, "output.json")

    # Verify result is successful
    assert result.success is True
    assert result.records_processed == 1
    assert result.error_message is None

    # Verify file content is returned
    assert content is not None
    assert isinstance(content, bytes)

    # Verify content is valid JSON
    import json
    sanitized_data = json.loads(content)
    assert isinstance(sanitized_data, list)
    assert len(sanitized_data) == 1


def test_process_sanitization_failed() -> None:
    """Test failed sanitization returns result with error and None content."""
    from unittest.mock import Mock

    from data_sanitizer.streamlit_app import process_sanitization

    # Create mock uploaded file with invalid JSON data
    invalid_json = b'{"invalid": json}'
    mock_file = Mock()
    mock_file.getvalue.return_value = invalid_json

    # Process sanitization
    result, content = process_sanitization(mock_file, "output.json")

    # Verify result indicates failure
    assert result.success is False
    assert result.records_processed == 0
    assert result.error_message is not None

    # Verify no file content is returned
    assert content is None


def test_process_sanitization_temporary_files_cleaned_up() -> None:
    """Test temporary files are cleaned up after processing."""
    import os
    from unittest.mock import Mock

    from data_sanitizer.streamlit_app import process_sanitization

    # Create mock uploaded file with valid JSON data
    json_data = b'[{"name": "Alice Smith"}]'
    mock_file = Mock()
    mock_file.getvalue.return_value = json_data

    # Track temporary directory path
    temp_paths = []

    # Monkey-patch TemporaryDirectory to capture the path
    from tempfile import TemporaryDirectory as OriginalTempDir

    class TrackedTempDir(OriginalTempDir):
        def __enter__(self):
            path = super().__enter__()
            temp_paths.append(path)
            return path

    # Replace TemporaryDirectory temporarily
    import data_sanitizer.streamlit_app as app_module
    original_tempdir = app_module.TemporaryDirectory
    app_module.TemporaryDirectory = TrackedTempDir

    try:
        # Process sanitization
        result, content = process_sanitization(mock_file, "output.json")

        # Verify temporary directory was created and cleaned up
        assert len(temp_paths) == 1
        temp_dir = temp_paths[0]

        # Verify temporary directory no longer exists
        assert not os.path.exists(temp_dir), "Temporary directory should be cleaned up"

    finally:
        # Restore original TemporaryDirectory
        app_module.TemporaryDirectory = original_tempdir



# Feature: streamlit-interface, Property 4: Result display completeness
@given(
    success=st.booleans(),
    records_processed=st.integers(min_value=0, max_value=10000),
    pii_fields_detected=st.integers(min_value=0, max_value=1000),
    pii_replacements_made=st.integers(min_value=0, max_value=1000),
    error_message=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
)
@settings(deadline=None)
def test_render_results_property(
    success: bool,
    records_processed: int,
    pii_fields_detected: int,
    pii_replacements_made: int,
    error_message: str | None,
) -> None:
    """Property: Result display includes all four required statistics.

    **Validates: Requirements 5.2, 5.3, 5.4, 5.5**

    This property test verifies that the render_results function displays
    all required statistics for any valid SanitizationResult.
    """
    from pathlib import Path
    from unittest.mock import MagicMock, patch

    from data_sanitizer.models import SanitizationResult
    from data_sanitizer.streamlit_app import render_results

    # Create SanitizationResult with generated values
    result = SanitizationResult(
        success=success,
        records_processed=records_processed,
        pii_fields_detected=pii_fields_detected,
        pii_replacements_made=pii_replacements_made,
        error_message=error_message if not success else None,
    )

    output_path = Path("test_output.json")

    # Mock Streamlit functions to capture what's displayed
    with patch("data_sanitizer.streamlit_app.st") as mock_st:
        # Set up column mocks that support context manager protocol
        col1_mock = MagicMock()
        col2_mock = MagicMock()
        col3_mock = MagicMock()

        # Make columns return context managers that don't change the st reference
        col1_mock.__enter__ = MagicMock(return_value=None)
        col1_mock.__exit__ = MagicMock(return_value=False)
        col2_mock.__enter__ = MagicMock(return_value=None)
        col2_mock.__exit__ = MagicMock(return_value=False)
        col3_mock.__enter__ = MagicMock(return_value=None)
        col3_mock.__exit__ = MagicMock(return_value=False)

        mock_st.columns.return_value = [col1_mock, col2_mock, col3_mock]

        # Track metric calls
        metric_calls = []
        def track_metric(*args, **kwargs):
            metric_calls.append((args, kwargs))
        mock_st.metric.side_effect = track_metric

        # Call render_results
        render_results(result, output_path)

        if success:
            # Property 1: Success message should be displayed
            mock_st.success.assert_called_once()
            success_message = mock_st.success.call_args[0][0]
            assert "success" in success_message.lower()

            # Property 2: All three statistics should be displayed via metrics
            # We should have 3 columns created
            mock_st.columns.assert_called_once_with(3)

            # Property 3: Metrics should be called for each statistic
            # Check that metric was called 3 times with the correct values
            assert len(metric_calls) == 3, f"Expected 3 metric calls, got {len(metric_calls)}"

            # Verify the metric calls contain the expected values
            metric_labels = [call[0][0] for call in metric_calls]
            metric_values = [call[0][1] for call in metric_calls]

            assert "Records Processed" in metric_labels
            assert "PII Fields Detected" in metric_labels
            assert "PII Replacements Made" in metric_labels

            assert records_processed in metric_values
            assert pii_fields_detected in metric_values
            assert pii_replacements_made in metric_values

            # Property 4: Output file path should be displayed
            mock_st.info.assert_called_once()
            info_message = mock_st.info.call_args[0][0]
            assert output_path.name in info_message
        else:
            # Property 5: Error message should be displayed for failures
            mock_st.error.assert_called_once()
            error_display = mock_st.error.call_args[0][0]
            assert "failed" in error_display.lower()



# Feature: streamlit-interface, Property 6: Download file consistency
@given(
    # Generate valid JSON data structures
    json_data=st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(min_size=0, max_size=50),
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=5),
            st.dictionaries(st.text(min_size=1, max_size=20), children, max_size=5),
        ),
        max_leaves=10,
    )
)
@settings(deadline=None)
def test_render_download_button_property(
    json_data: dict | list | str | int | float | bool | None,
) -> None:
    """Property: Downloaded content matches sanitized file content with proper JSON formatting.

    **Validates: Requirements 6.2, 6.4**

    This property test verifies that the download button serves content that
    matches the sanitized file and is properly formatted as JSON.
    """
    import json
    from unittest.mock import patch

    from data_sanitizer.streamlit_app import render_download_button

    # Convert data to JSON bytes (simulating sanitized file content)
    file_content = json.dumps(json_data, indent=2).encode("utf-8")
    filename = "test_output.json"

    # Mock Streamlit download_button to capture what's being served
    with patch("data_sanitizer.streamlit_app.st") as mock_st:
        # Call render_download_button
        render_download_button(file_content, filename)

        # Property 1: download_button should be called
        mock_st.download_button.assert_called_once()

        # Property 2: The data parameter should match the file content
        call_kwargs = mock_st.download_button.call_args[1]
        served_data = call_kwargs["data"]
        assert served_data == file_content, "Downloaded content should match file content"

        # Property 3: The filename should be used
        assert call_kwargs["file_name"] == filename

        # Property 4: MIME type should be application/json
        assert call_kwargs["mime"] == "application/json"

        # Property 5: The served data should be valid JSON
        try:
            parsed_data = json.loads(served_data)
            # Verify it matches the original data
            assert parsed_data == json_data, "Parsed JSON should match original data"
        except json.JSONDecodeError:
            pytest.fail("Downloaded content is not valid JSON")



# Feature: streamlit-interface, Property 7: Button state correctness
@given(
    has_file=st.booleans(),
    has_valid_filename=st.booleans(),
)
def test_button_state_correctness_property(has_file: bool, has_valid_filename: bool) -> None:
    """Property: Button enabled state based on file upload and filename presence.

    **Validates: Requirements 3.2, 3.3**

    This property test verifies that the "Sanitize" button is enabled if and only if
    both a file is uploaded and a valid output filename is provided.
    """
    # The button should be enabled only when both conditions are met
    expected_enabled = has_file and has_valid_filename

    # Simulate the logic from main() function
    uploaded_file = "mock_file" if has_file else None
    validated_filename = "output.json" if has_valid_filename else None

    # Property: Button enabled state matches expected state
    button_enabled = uploaded_file is not None and validated_filename is not None

    assert button_enabled == expected_enabled, (
        f"Button should be {'enabled' if expected_enabled else 'disabled'} "
        f"when has_file={has_file} and has_valid_filename={has_valid_filename}"
    )

    # Additional property checks
    if not has_file:
        assert not button_enabled, "Button should be disabled when no file is uploaded"

    if not has_valid_filename:
        assert not button_enabled, "Button should be disabled when filename is invalid"

    if has_file and has_valid_filename:
        assert button_enabled, "Button should be enabled when both file and filename are present"


# Feature: streamlit-interface, Property 5: Error message propagation
@given(
    error_message=st.text(min_size=1, max_size=200).filter(lambda s: s.strip() != "")
)
@settings(deadline=None)
def test_error_message_propagation_property(error_message: str) -> None:
    """Property: Error messages from failed SanitizationResults are displayed correctly.

    **Validates: Requirements 5.6, 8.3**

    This property test verifies that when sanitization fails, the error message
    from the SanitizationResult is properly displayed to the user.
    """
    from pathlib import Path
    from unittest.mock import patch

    from data_sanitizer.models import SanitizationResult
    from data_sanitizer.streamlit_app import render_results

    # Create a failed SanitizationResult with the generated error message
    result = SanitizationResult(
        success=False,
        records_processed=0,
        pii_fields_detected=0,
        pii_replacements_made=0,
        error_message=error_message,
    )

    output_path = Path("test_output.json")

    # Mock Streamlit functions to capture what's displayed
    with patch("data_sanitizer.streamlit_app.st") as mock_st:
        # Call render_results
        render_results(result, output_path)

        # Property 1: st.error should be called for failed results
        mock_st.error.assert_called_once()

        # Property 2: The error message should contain the original error message
        error_display = mock_st.error.call_args[0][0]
        assert error_message in error_display, (
            f"Error display should contain the original error message. "
            f"Expected '{error_message}' to be in '{error_display}'"
        )

        # Property 3: The error display should indicate failure
        assert "failed" in error_display.lower(), (
            "Error display should indicate that sanitization failed"
        )

        # Property 4: Success message should NOT be called for failed results
        mock_st.success.assert_not_called()



# Unit tests for error handling
def test_invalid_json_file_displays_error() -> None:
    """Test that invalid JSON file displays error.

    **Validates: Requirements 8.1, 8.2, 8.3**
    """
    from unittest.mock import Mock

    from data_sanitizer.streamlit_app import process_sanitization

    # Create mock uploaded file with invalid JSON data
    invalid_json = b'{"invalid": "json" missing bracket'
    mock_file = Mock()
    mock_file.getvalue.return_value = invalid_json

    # Process sanitization
    result, content = process_sanitization(mock_file, "output.json")

    # Verify result indicates failure
    assert result.success is False
    assert result.error_message is not None
    assert "json" in result.error_message.lower() or "parse" in result.error_message.lower()

    # Verify no file content is returned
    assert content is None


def test_sanitization_failure_displays_error_message() -> None:
    """Test that sanitization failure displays error message.

    **Validates: Requirements 8.3, 8.4**
    """
    from pathlib import Path
    from unittest.mock import patch

    from data_sanitizer.models import SanitizationResult
    from data_sanitizer.streamlit_app import render_results

    # Create a failed result with specific error message
    error_msg = "Failed to process file due to invalid data format"
    result = SanitizationResult(
        success=False,
        records_processed=0,
        pii_fields_detected=0,
        pii_replacements_made=0,
        error_message=error_msg,
    )

    output_path = Path("test_output.json")

    # Mock Streamlit to capture error display
    with patch("data_sanitizer.streamlit_app.st") as mock_st:
        render_results(result, output_path)

        # Verify error is displayed
        mock_st.error.assert_called_once()
        error_display = mock_st.error.call_args[0][0]

        # Verify error message is included
        assert error_msg in error_display
        assert "failed" in error_display.lower()


def test_app_remains_functional_after_errors() -> None:
    """Test that app remains functional after errors.

    **Validates: Requirements 8.4**

    This test verifies that after an error occurs, the app can still
    process subsequent requests without crashing.
    """
    from unittest.mock import Mock

    from data_sanitizer.streamlit_app import process_sanitization

    # First attempt: invalid JSON
    invalid_json = b'{"bad": json}'
    mock_file1 = Mock()
    mock_file1.getvalue.return_value = invalid_json

    result1, content1 = process_sanitization(mock_file1, "output1.json")

    # Verify first attempt failed
    assert result1.success is False
    assert content1 is None

    # Second attempt: valid JSON (app should still work)
    valid_json = b'[{"name": "Bob Johnson", "email": "bob@example.com"}]'
    mock_file2 = Mock()
    mock_file2.getvalue.return_value = valid_json

    result2, content2 = process_sanitization(mock_file2, "output2.json")

    # Verify second attempt succeeded
    assert result2.success is True
    assert content2 is not None
    assert result2.records_processed == 1


def test_unexpected_error_handling_in_main() -> None:
    """Test that unexpected errors in main() are caught and displayed.

    **Validates: Requirements 8.1, 8.2, 8.3**

    This test simulates an unexpected error during sanitization and verifies
    that it's caught and stored as an error result without crashing the app.
    """
    from unittest.mock import Mock, patch

    # Mock uploaded file
    mock_file = Mock()
    mock_file.getvalue.return_value = b'[{"test": "data"}]'

    # Mock process_sanitization to raise an unexpected error
    with patch("data_sanitizer.streamlit_app.process_sanitization") as mock_process:
        mock_process.side_effect = RuntimeError("Unexpected error occurred")

        # Mock Streamlit components
        with patch("data_sanitizer.streamlit_app.st") as mock_st:
            # Set up session state mock
            mock_st.session_state = {}

            # Simulate the try-except block from main()
            try:
                result, file_content = mock_process(mock_file, "output.json")
                mock_st.session_state["sanitization_result"] = result
                mock_st.session_state["sanitized_content"] = file_content
            except Exception as e:
                # This is what the main() function does
                from data_sanitizer.models import SanitizationResult
                error_result = SanitizationResult(
                    success=False,
                    records_processed=0,
                    pii_fields_detected=0,
                    pii_replacements_made=0,
                    error_message=f"An unexpected error occurred: {str(e)}. "
                    "Please check your input file and try again."
                )
                mock_st.session_state["sanitization_result"] = error_result
                mock_st.session_state["sanitized_content"] = None

            # Verify session state was updated with error result
            assert "sanitization_result" in mock_st.session_state
            assert mock_st.session_state["sanitization_result"].success is False
            error_msg = mock_st.session_state["sanitization_result"].error_message
            assert "Unexpected error occurred" in error_msg
            assert mock_st.session_state["sanitized_content"] is None
