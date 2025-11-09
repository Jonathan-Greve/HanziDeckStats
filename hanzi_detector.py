"""
Hanzi character detection utilities for Anki addon.
"""

import re
import unicodedata
from typing import Set, List


class HanziDetector:
    """Detect and extract Hanzi characters from text."""

    # Unicode range for CJK Unified Ideographs
    CJK_PATTERN = re.compile(r'[\u3400-\u9fff\uf900-\ufaff]')

    @staticmethod
    def is_hanzi(char: str) -> bool:
        """
        Check if a character is a Hanzi (Chinese character).

        Args:
            char: Single character to check

        Returns:
            True if the character is a Hanzi, False otherwise
        """
        if not char:
            return False

        try:
            name = unicodedata.name(char)
            return ('CJK UNIFIED IDEOGRAPH' in name or
                    'CJK COMPATIBILITY IDEOGRAPH' in name or
                    'BOPOMOFO' in name)
        except ValueError:
            # Character has no name (control character or invalid)
            return False

    @staticmethod
    def extract_hanzi(text: str) -> Set[str]:
        """
        Extract all unique Hanzi characters from text.

        Args:
            text: Text to extract characters from

        Returns:
            Set of unique Hanzi characters in normalized form
        """
        if not text:
            return set()

        chars = set()
        for char in text:
            if HanziDetector.CJK_PATTERN.match(char):
                # Normalize to NFC form (canonical composition)
                normalized = unicodedata.normalize('NFC', char)
                chars.add(normalized)

        return chars

    @staticmethod
    def extract_from_fields(fields: List[str], field_selection: str) -> Set[str]:
        """
        Extract Hanzi characters from note fields based on selection mode.

        Args:
            fields: List of field values from a note (split by \\x1F)
            field_selection: How to select fields:
                - "all": Extract from all fields
                - "sortField": Extract only from first field (sort field)
                - "1", "2", "3", etc.: Extract from specific field number

        Returns:
            Set of unique Hanzi characters found
        """
        if not fields:
            return set()

        chars = set()

        if field_selection == "all":
            # Extract from all fields
            for field in fields:
                chars.update(HanziDetector.extract_hanzi(field))

        elif field_selection == "sortField":
            # Extract only from first field (sort field)
            if len(fields) > 0:
                chars.update(HanziDetector.extract_hanzi(fields[0]))

        elif field_selection.isdigit():
            # Extract from specific field number (1-indexed)
            field_idx = int(field_selection) - 1
            if 0 <= field_idx < len(fields):
                chars.update(HanziDetector.extract_hanzi(fields[field_idx]))

        return chars

    @staticmethod
    def count_hanzi_in_text(text: str) -> int:
        """
        Count total Hanzi characters in text (including duplicates).

        Args:
            text: Text to count characters in

        Returns:
            Number of Hanzi characters found
        """
        if not text:
            return 0

        count = 0
        for char in text:
            if HanziDetector.CJK_PATTERN.match(char):
                count += 1

        return count
