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
        self.hsk_2021_map: Dict[str, int] = {}  # char -> level (1-7, where 7 = bands 7-9)
        self.frequency_rank_map: Dict[str, int] = {}  # char -> frequency rank

        # Load data
        self._load_hsk_2021()
        self._load_frequency()

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
                    level_str = row['Level']

                    # Handle "7-9" for bands 7-9
                    if level_str == "7-9":
                        # Store as level 7 for simplicity (could also be 8 or 9)
                        level = 7
                    else:
                        try:
                            level = int(level_str)
                        except ValueError:
                            continue

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

    def _load_frequency(self):
        """Load frequency data from mega_hanzi_compilation.csv"""
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
        except FileNotFoundError:
            print(f"Warning: Frequency data file not found: {csv_path}")
        except Exception as e:
            print(f"Error loading frequency data: {e}")

    def get_hsk_2021_level(self, char: str) -> int:
        """Get HSK 2021 level (1-7, where 7=bands 7-9) for a character, or 0 if not in HSK."""
        return self.hsk_2021_map.get(char, 0)

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
            Dict with keys 'hsk_2021', 'frequency', each containing
            a dict mapping category names to sets of characters.
        """
        result = {
            'hsk_2021': {
                'Band 1': set(),
                'Band 2': set(),
                'Band 3': set(),
                'Band 4': set(),
                'Band 5': set(),
                'Band 6': set(),
                'Bands 7-9': set(),
            },
            'frequency': {
                'Top 500': set(),
                'Top 1000': set(),
                'Top 1500': set(),
                'Top 2000': set(),
            }
        }

        for char in characters:
            # HSK 2021
            hsk_2021_level = self.get_hsk_2021_level(char)
            if hsk_2021_level > 0:
                if hsk_2021_level >= 7:
                    result['hsk_2021']['Bands 7-9'].add(char)
                else:
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
