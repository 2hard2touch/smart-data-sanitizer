"""Unit tests for the base Detector class.

This module tests the abstract Detector base class to ensure:
1. The base class cannot be instantiated directly
2. Abstract method enforcement works correctly
"""

import pytest

from data_sanitizer.detectors.base import Detector
from data_sanitizer.models import DetectionResult, PIIType


def test_detector_cannot_be_instantiated_directly() -> None:
    """Test that the abstract Detector base class cannot be instantiated.

    The Detector class is abstract and should raise a TypeError when
    attempting to instantiate it directly without implementing the
    abstract detect() method.
    """
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        Detector()  # type: ignore


def test_abstract_method_enforcement() -> None:
    """Test that concrete detectors must implement the detect() method.

    A concrete detector that inherits from Detector but does not implement
    the detect() method should raise a TypeError when instantiated.
    """

    class IncompleteDetector(Detector):
        """A detector that doesn't implement the abstract method."""

        pass

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteDetector()  # type: ignore


def test_concrete_detector_can_be_instantiated() -> None:
    """Test that a properly implemented concrete detector can be instantiated.

    A concrete detector that implements the detect() method should be
    instantiable and callable.
    """

    class ConcreteDetector(Detector):
        """A minimal concrete detector implementation."""

        def detect(self, text: str, field_name: str = "") -> list[DetectionResult]:
            """Minimal implementation that returns empty list."""
            return []

    # Should not raise any exception
    detector = ConcreteDetector()
    assert detector is not None

    # Should be callable
    results = detector.detect("test text", "test_field")
    assert results == []
    assert isinstance(results, list)


def test_concrete_detector_returns_detection_results() -> None:
    """Test that a concrete detector can return DetectionResult objects.

    Verifies that the detect() method signature works correctly with
    DetectionResult objects.
    """

    class TestDetector(Detector):
        """A detector that returns a mock detection result."""

        def detect(self, text: str, field_name: str = "") -> list[DetectionResult]:
            """Return a mock detection result for testing."""
            if "test@example.com" in text:
                return [
                    DetectionResult(
                        pii_type=PIIType.EMAIL,
                        original_value="test@example.com",
                        confidence=1.0,
                        start_pos=0,
                        end_pos=16,
                    )
                ]
            return []

    detector = TestDetector()

    # Test with PII
    results = detector.detect("test@example.com", "email")
    assert len(results) == 1
    assert results[0].pii_type == PIIType.EMAIL
    assert results[0].original_value == "test@example.com"
    assert results[0].confidence == 1.0

    # Test without PII
    results = detector.detect("no pii here", "text")
    assert len(results) == 0
