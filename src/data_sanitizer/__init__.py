"""Smart Data Sanitizer - Automatically detect and replace PII in JSON datasets.

This package provides tools for automatically detecting and replacing Personally
Identifiable Information (PII) in JSON datasets with semantically valid fake data
while maintaining referential integrity.

Main Components:
    - Sanitizer: Main orchestrator for PII detection and replacement
    - Detector: Abstract base class for PII detection strategies
    - Replacer: Generates consistent fake data for detected PII

Example:
    >>> from data_sanitizer import Sanitizer, Replacer
    >>> from data_sanitizer.detectors.email_detector import EmailDetector
    >>> from pathlib import Path
    >>>
    >>> detectors = [EmailDetector()]
    >>> replacer = Replacer(seed=42)
    >>> sanitizer = Sanitizer(detectors, replacer)
    >>> result = sanitizer.sanitize_file(Path("input.json"), Path("output.json"))
"""

__version__ = "0.1.0"

from data_sanitizer.detectors.base import Detector
from data_sanitizer.replacer import Replacer
from data_sanitizer.sanitizer import Sanitizer

__all__ = ["Sanitizer", "Detector", "Replacer", "__version__"]
