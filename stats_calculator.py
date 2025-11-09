"""
Statistics calculator for Hanzi Deck Statistics addon.
Calculates per-deck statistics for total and reviewed Hanzi.
"""

from typing import Dict, Set, List, Tuple
from dataclasses import dataclass

from .hanzi_detector import HanziDetector
from .character_data import get_character_data


@dataclass
class DeckStatistics:
    """Statistics for a single deck."""
    deck_id: int
    deck_name: str
    total_hanzi: Set[str]  # All Hanzi in deck (including new cards)
    reviewed_hanzi: Set[str]  # Hanzi that have been reviewed
    total_categorized: Dict[str, Dict[str, Set[str]]]  # Categorized total Hanzi
    reviewed_categorized: Dict[str, Dict[str, Set[str]]]  # Categorized reviewed Hanzi

    def __init__(self, deck_id: int, deck_name: str):
        self.deck_id = deck_id
        self.deck_name = deck_name
        self.total_hanzi = set()
        self.reviewed_hanzi = set()
        self.total_categorized = {}
        self.reviewed_categorized = {}


class StatsCalculator:
    """Calculate Hanzi statistics for Anki decks."""

    def __init__(self, collection, config: dict):
        """
        Initialize stats calculator.

        Args:
            collection: Anki collection object (mw.col)
            config: Addon configuration dict
        """
        self.col = collection
        self.config = config
        self.character_data = get_character_data()

    def calculate_deck_stats(self, deck_id: int, include_subdecks: bool = True) -> DeckStatistics:
        """
        Calculate statistics for a specific deck.

        Args:
            deck_id: Deck ID to calculate stats for
            include_subdecks: Whether to include subdeck cards

        Returns:
            DeckStatistics object with all calculated statistics
        """
        # Get deck name
        deck_name = self.col.decks.name(deck_id) if deck_id != 0 else "All Decks"

        # Create stats object
        stats = DeckStatistics(deck_id, deck_name)

        # Get relevant deck IDs
        if deck_id == 0:
            # All decks - use all cards
            deck_ids = None
        elif include_subdecks:
            deck_ids = self.col.decks.deck_and_child_ids(deck_id)
        else:
            deck_ids = [deck_id]

        # Get field selection mode from config
        field_mode = self.config.get('fieldToUseForStats', 'sortField')

        # Query 1: All cards (including new/unseen cards)
        stats.total_hanzi = self._get_hanzi_from_cards(deck_ids, include_new=True, field_mode=field_mode)

        # Query 2: Only reviewed cards
        stats.reviewed_hanzi = self._get_hanzi_from_cards(deck_ids, include_new=False, field_mode=field_mode)

        # Categorize characters
        if self.config.get('showCategories', True):
            stats.total_categorized = self.character_data.categorize_characters(stats.total_hanzi)
            stats.reviewed_categorized = self.character_data.categorize_characters(stats.reviewed_hanzi)

        return stats

    def calculate_all_decks_stats(self, include_subdecks: bool = True) -> List[DeckStatistics]:
        """
        Calculate statistics for all decks.

        Args:
            include_subdecks: Whether to include subdeck cards for each deck

        Returns:
            List of DeckStatistics objects, one per top-level deck
        """
        all_stats = []

        # Get all top-level decks
        for deck_name_id in self.col.decks.all_names_and_ids():
            # Skip subdecks (they contain "::")
            if "::" not in deck_name_id.name:
                stats = self.calculate_deck_stats(deck_name_id.id, include_subdecks)
                all_stats.append(stats)

        return all_stats

    def _get_hanzi_from_cards(self, deck_ids: List[int], include_new: bool, field_mode: str) -> Set[str]:
        """
        Extract Hanzi characters from cards in specified decks.

        Args:
            deck_ids: List of deck IDs to query (None for all decks)
            include_new: Whether to include new/unseen cards
            field_mode: Which fields to extract from ('all', 'sortField', or field number)

        Returns:
            Set of unique Hanzi characters found
        """
        hanzi_set = set()

        # Build SQL query
        if include_new:
            # Include all cards (queue >= 0, excluding suspended/buried)
            if deck_ids is None:
                query = """
                    SELECT DISTINCT notes.flds
                    FROM cards
                    INNER JOIN notes ON cards.nid = notes.id
                    WHERE cards.queue >= 0
                """
                params = []
            else:
                placeholders = ','.join('?' * len(deck_ids))
                query = f"""
                    SELECT DISTINCT notes.flds
                    FROM cards
                    INNER JOIN notes ON cards.nid = notes.id
                    WHERE cards.did IN ({placeholders})
                      AND cards.queue >= 0
                """
                params = list(deck_ids)
        else:
            # Only reviewed cards (must have entry in revlog)
            if deck_ids is None:
                query = """
                    SELECT DISTINCT notes.flds
                    FROM cards
                    INNER JOIN notes ON cards.nid = notes.id
                    INNER JOIN revlog ON cards.id = revlog.cid
                    WHERE cards.queue > 0
                """
                params = []
            else:
                placeholders = ','.join('?' * len(deck_ids))
                query = f"""
                    SELECT DISTINCT notes.flds
                    FROM cards
                    INNER JOIN notes ON cards.nid = notes.id
                    INNER JOIN revlog ON cards.id = revlog.cid
                    WHERE cards.did IN ({placeholders})
                      AND cards.queue > 0
                """
                params = list(deck_ids)

        # Execute query and extract Hanzi
        try:
            for row in self.col.db.execute(query, *params):
                fields_str = row[0]
                # Split fields by field separator (\x1F)
                fields = fields_str.split('\x1f')
                # Extract Hanzi based on field mode
                chars = HanziDetector.extract_from_fields(fields, field_mode)
                hanzi_set.update(chars)
        except Exception as e:
            print(f"Error querying database: {e}")

        return hanzi_set

    def get_deck_list(self) -> List[Tuple[int, str]]:
        """
        Get list of all decks for UI dropdown.

        Returns:
            List of (deck_id, deck_name) tuples
        """
        decks = [(0, "All Decks")]  # Special "All Decks" option

        for deck_name_id in self.col.decks.all_names_and_ids():
            decks.append((deck_name_id.id, deck_name_id.name))

        return decks
