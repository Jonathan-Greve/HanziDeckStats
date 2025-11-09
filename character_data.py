"""
Character data loader for Hanzi Deck Statistics addon.
Loads HSK 2012, HSK 2021, and frequency data from CSV files.
"""

import csv
import os
from typing import Dict, List, Set


class CharacterData:
    """Loads and manages character categorization data."""

    def __init__(self):
        self.hsk_2021_map: Dict[str, int] = {}  # char -> level (1-9)
        self.hsk_2012_map: Dict[str, int] = {}  # char -> level (1-6)
        self.frequency_rank_map: Dict[str, int] = {}  # char -> frequency rank

        # Load data
        self._load_hsk_2021()
        self._load_frequency_and_hsk_2012()

    def _get_data_path(self, filename: str) -> str:
        """Get path to data file in datasets directory."""
        addon_dir = os.path.dirname(__file__)
        return os.path.join(addon_dir, 'datasets', filename)

    def _load_hsk_2021(self):
        """Load HSK 3.0 (2021) character data from hsk30-chars.csv"""
        csv_path = self._get_data_path('hsk30-chars.csv')

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    char = row['Hanzi']
                    level = int(row['Level'])

                    # Store simplified character
                    self.hsk_2021_map[char] = level

                    # Also store traditional variant if different
                    traditional = row.get('Traditional', '')
                    if traditional and traditional != char:
                        self.hsk_2021_map[traditional] = level
        except FileNotFoundError:
            print(f"Warning: HSK 2021 data file not found: {csv_path}")
        except Exception as e:
            print(f"Error loading HSK 2021 data: {e}")

    def _load_frequency_and_hsk_2012(self):
        """Load frequency and HSK 2012 data from mega_hanzi_compilation.csv"""
        csv_path = self._get_data_path('mega_hanzi_compilation.csv')

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Get characters
                    simplified = row.get('simplified', '')
                    traditional = row.get('traditional', '')

                    # Parse frequency rank (Jun Da)
                    freq_str = row.get('frequency_junda', '')
                    if freq_str and freq_str.isdigit():
                        freq_rank = int(freq_str)
                        if simplified:
                            self.frequency_rank_map[simplified] = freq_rank
                        if traditional and traditional != simplified:
                            self.frequency_rank_map[traditional] = freq_rank

                    # Parse HSK 2012 level (stored as "HSK_L1", "HSK_L2", etc in hsk30_level column)
                    hsk_level_str = row.get('hsk30_level', '')
                    if hsk_level_str and hsk_level_str.startswith('HSK_L'):
                        try:
                            level = int(hsk_level_str.replace('HSK_L', ''))
                            # Only store levels 1-6 (HSK 2012)
                            if 1 <= level <= 6:
                                if simplified:
                                    self.hsk_2012_map[simplified] = level
                                if traditional and traditional != simplified:
                                    self.hsk_2012_map[traditional] = level
                        except ValueError:
                            pass
        except FileNotFoundError:
            print(f"Warning: Frequency data file not found: {csv_path}")
        except Exception as e:
            print(f"Error loading frequency data: {e}")

    def get_hsk_2021_level(self, char: str) -> int:
        """Get HSK 2021 level (1-9) for a character, or 0 if not in HSK."""
        return self.hsk_2021_map.get(char, 0)

    def get_hsk_2012_level(self, char: str) -> int:
        """Get HSK 2012 level (1-6) for a character, or 0 if not in HSK."""
        return self.hsk_2012_map.get(char, 0)

    def get_frequency_rank(self, char: str) -> int:
        """Get frequency rank for a character, or 0 if not ranked."""
        return self.frequency_rank_map.get(char, 0)

    def get_frequency_category(self, char: str) -> str:
        """Get frequency category (Top 500, 1000, 1500, 2000) or empty string."""
        rank = self.get_frequency_rank(char)
        if rank == 0:
            return ""
        elif rank <= 500:
            return "Top 500"
        elif rank <= 1000:
            return "Top 1000"
        elif rank <= 1500:
            return "Top 1500"
        elif rank <= 2000:
            return "Top 2000"
        else:
            return ""

    def categorize_characters(self, characters: Set[str]) -> Dict[str, Dict[str, Set[str]]]:
        """
        Categorize a set of characters into HSK levels and frequency bands.

        Returns:
            Dict with keys 'hsk_2012', 'hsk_2021', 'frequency', each containing
            a dict mapping category names to sets of characters.
        """
        result = {
            'hsk_2012': {f'Level {i}': set() for i in range(1, 7)},
            'hsk_2021': {f'Band {i}': set() for i in range(1, 10)},
            'frequency': {
                'Top 500': set(),
                'Top 1000': set(),
                'Top 1500': set(),
                'Top 2000': set(),
            }
        }

        for char in characters:
            # HSK 2012
            hsk_2012_level = self.get_hsk_2012_level(char)
            if hsk_2012_level > 0:
                result['hsk_2012'][f'Level {hsk_2012_level}'].add(char)

            # HSK 2021
            hsk_2021_level = self.get_hsk_2021_level(char)
            if hsk_2021_level > 0:
                result['hsk_2021'][f'Band {hsk_2021_level}'].add(char)

            # Frequency
            freq_category = self.get_frequency_category(char)
            if freq_category:
                result['frequency'][freq_category].add(char)

        return result


# Global instance (will be initialized by the addon)
character_data = None


def get_character_data() -> CharacterData:
    """Get the global CharacterData instance, creating it if necessary."""
    global character_data
    if character_data is None:
        character_data = CharacterData()
    return character_data
