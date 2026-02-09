"""PII replacement with consistency cache.

This module provides the Replacer class that generates semantically valid
fake data for detected PII while maintaining referential integrity through
a consistency cache. The same original PII value always maps to the same
fake value throughout the sanitization process.
"""

import re

from faker import Faker

from data_sanitizer.models import DetectionResult, PIIType


class Replacer:
    """Generates consistent fake data for detected PII.

    The Replacer uses the Faker library to generate realistic fake data
    and maintains a consistency cache to ensure that identical PII values
    are always replaced with the same fake value. This preserves referential
    integrity in the dataset.

    Attributes:
        _faker: Faker instance for generating fake data
        _cache: Consistency cache mapping (original_value, pii_type) to fake value
        _name_pairs: Cache for cross-field name consistency (first/last name pairs)
    """

    def __init__(self, seed: int | None = None) -> None:
        """Initialize replacer with optional seed for reproducibility.

        Args:
            seed: Optional random seed for Faker. If provided, the same seed
                will always generate the same sequence of fake values, enabling
                reproducible tests. If None, random values are generated.
        """
        if seed is not None:
            Faker.seed(seed)
        self._faker = Faker()

        # Consistency cache: (original_value, pii_type) -> fake_value
        self._cache: dict[tuple[str, PIIType], str] = {}

        # Cross-field name consistency: track first/last name pairs
        # Maps original first names to fake first names
        self._first_name_map: dict[str, str] = {}
        # Maps original last names to fake last names
        self._last_name_map: dict[str, str] = {}

    def replace(self, detection: DetectionResult) -> str:
        """Generate a fake replacement for detected PII.

        This method generates semantically valid fake data based on the PII type.
        It uses the consistency cache to ensure the same original value always
        maps to the same fake value.

        Args:
            detection: Detection result containing PII type and original value

        Returns:
            Fake replacement value that maintains semantic validity and consistency

        Example:
            >>> replacer = Replacer(seed=42)
            >>> detection = DetectionResult(PIIType.EMAIL, "john@example.com", 1.0)
            >>> fake_email = replacer.replace(detection)
            >>> # Same email always gets same replacement
            >>> fake_email2 = replacer.replace(detection)
            >>> fake_email == fake_email2
            True
        """
        return self.get_or_create_replacement(detection.original_value, detection.pii_type)

    def get_or_create_replacement(self, original: str, pii_type: PIIType) -> str:
        """Get existing replacement or create new one for consistency.

        This method checks the consistency cache first. If a replacement already
        exists for the given (original, pii_type) pair, it returns the cached
        value. Otherwise, it generates a new fake value, caches it, and returns it.

        Args:
            original: Original PII value
            pii_type: Type of PII

        Returns:
            Consistent fake replacement value
        """
        cache_key = (original, pii_type)

        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Generate new fake value based on PII type
        if pii_type == PIIType.EMAIL:
            fake_value = self._generate_email()
        elif pii_type == PIIType.PHONE:
            fake_value = self._generate_phone(original)
        elif pii_type == PIIType.FULL_NAME:
            fake_value = self._generate_full_name(original)
        elif pii_type == PIIType.FIRST_NAME:
            fake_value = self._generate_first_name(original)
        elif pii_type == PIIType.LAST_NAME:
            fake_value = self._generate_last_name(original)
        elif pii_type == PIIType.CREDIT_CARD:
            fake_value = self._generate_credit_card()
        else:
            # Fallback for unknown types
            fake_value = "[REDACTED]"

        # Cache and return
        self._cache[cache_key] = fake_value
        return fake_value

    def _generate_email(self) -> str:
        """Generate a valid fake email address.

        Returns:
            Fake email in format local@domain.tld
        """
        return self._faker.email()

    def _generate_phone(self, original: str) -> str:
        """Generate a fake phone number with format preservation.

        This method analyzes the original phone number format and generates
        a fake phone number that maintains the same format pattern (e.g.,
        with or without country code, same separators).

        Args:
            original: Original phone number

        Returns:
            Fake phone number with preserved format
        """
        # Generate a base fake phone number
        fake_phone = self._faker.phone_number()

        # Try to preserve the format of the original
        # Extract format pattern from original
        if "+" in original and "-" in original:
            # Format: +1-234-567-8900
            # Keep the format with + and dashes
            return fake_phone
        elif "(" in original and ")" in original:
            # Format: (234) 567-8900
            # Generate in this format
            digits = re.sub(r"\D", "", fake_phone)
            if len(digits) >= 10:
                return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
        elif "-" in original:
            # Format: 234-567-8900
            digits = re.sub(r"\D", "", fake_phone)
            if len(digits) >= 10:
                return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
        elif original.isdigit():
            # Format: 2345678900 (no separators)
            digits = re.sub(r"\D", "", fake_phone)
            return digits[: len(original)]

        # Default: return as-is
        return fake_phone

    def _generate_full_name(self, original: str) -> str:
        """Generate a fake full name with case preservation and cross-field consistency.

        This method checks if the full name can be constructed from existing
        first/last name mappings to maintain consistency across fields. For example,
        if "jane" and "smith" have already been mapped separately, "jane smith"
        will use those same mappings.

        Args:
            original: Original full name

        Returns:
            Fake full name with preserved case pattern
        """
        # Try to split the full name into first and last parts
        words = original.split()

        if len(words) >= 2:
            # Normalize for lookup (case-insensitive)
            first_normalized = words[0].lower()
            last_normalized = words[-1].lower()  # Use last word as last name

            # Check if we have existing mappings for both parts
            if first_normalized in self._first_name_map and last_normalized in self._last_name_map:
                # Construct full name from existing mappings
                fake_first = self._first_name_map[first_normalized]
                fake_last = self._last_name_map[last_normalized]
                fake_name = f"{fake_first} {fake_last}"
                return self._preserve_case(original, fake_name)

            # If we have a first name mapping but not last, create the last name mapping
            has_first = first_normalized in self._first_name_map
            has_last = last_normalized in self._last_name_map
            if has_first and not has_last:
                fake_first = self._first_name_map[first_normalized]
                self._last_name_map[last_normalized] = self._faker.last_name()
                fake_last = self._last_name_map[last_normalized]
                fake_name = f"{fake_first} {fake_last}"
                return self._preserve_case(original, fake_name)

            # If we have a last name mapping but not first, create the first name mapping
            if has_last and not has_first:
                self._first_name_map[first_normalized] = self._faker.first_name()
                fake_first = self._first_name_map[first_normalized]
                fake_last = self._last_name_map[last_normalized]
                fake_name = f"{fake_first} {fake_last}"
                return self._preserve_case(original, fake_name)

            # Neither part has been seen before - create both mappings
            self._first_name_map[first_normalized] = self._faker.first_name()
            self._last_name_map[last_normalized] = self._faker.last_name()
            fake_first = self._first_name_map[first_normalized]
            fake_last = self._last_name_map[last_normalized]
            fake_name = f"{fake_first} {fake_last}"
            return self._preserve_case(original, fake_name)

        # Single word name - just generate a full name
        fake_name = self._faker.name()
        return self._preserve_case(original, fake_name)

    def _generate_first_name(self, original: str) -> str:
        """Generate a fake first name with case preservation and cross-field consistency.

        This method maintains cross-field consistency by tracking first name
        mappings. If the same first name appears in multiple records, it will
        always map to the same fake first name.

        Args:
            original: Original first name

        Returns:
            Fake first name with preserved case pattern
        """
        # Normalize for lookup (case-insensitive)
        normalized = original.lower()

        # Check if we've seen this first name before
        if normalized not in self._first_name_map:
            self._first_name_map[normalized] = self._faker.first_name()

        fake_name = self._first_name_map[normalized]
        return self._preserve_case(original, fake_name)

    def _generate_last_name(self, original: str) -> str:
        """Generate a fake last name with case preservation and cross-field consistency.

        This method maintains cross-field consistency by tracking last name
        mappings. If the same last name appears in multiple records, it will
        always map to the same fake last name.

        Args:
            original: Original last name

        Returns:
            Fake last name with preserved case pattern
        """
        # Normalize for lookup (case-insensitive)
        normalized = original.lower()

        # Check if we've seen this last name before
        if normalized not in self._last_name_map:
            self._last_name_map[normalized] = self._faker.last_name()

        fake_name = self._last_name_map[normalized]
        return self._preserve_case(original, fake_name)

    def _generate_credit_card(self) -> str:
        """Generate a valid fake credit card number.

        The generated credit card number passes Luhn algorithm validation.

        Returns:
            Fake credit card number
        """
        return self._faker.credit_card_number()

    def _preserve_case(self, original: str, fake: str) -> str:
        """Preserve the case pattern of the original string in the fake string.

        This method analyzes the case pattern of the original string and applies
        it to the fake string. Supports:
        - Title Case (e.g., "John Doe")
        - lowercase (e.g., "john doe")
        - UPPERCASE (e.g., "JOHN DOE")

        Args:
            original: Original string with case pattern to preserve
            fake: Fake string to apply case pattern to

        Returns:
            Fake string with preserved case pattern
        """
        if original.isupper():
            return fake.upper()
        elif original.islower():
            return fake.lower()
        else:
            # Keep title case (default from Faker)
            return fake
