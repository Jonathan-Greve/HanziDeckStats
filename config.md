# Hanzi Deck Statistics Configuration

This addon tracks how many Hanzi characters you've seen in each deck, with breakdowns by HSK level and frequency.

## Configuration Options

### fieldToUseForStats

Which field(s) to extract Hanzi characters from:

- **"sortField"** (default): Only extract from the sort field (first field)
- **"all"**: Extract from all fields in the note
- **"1"**, **"2"**, **"3"**, etc.: Extract from a specific field number

### includeSubdecks

Whether to include subdeck cards when calculating statistics:

- **true** (default): When viewing "Chinese", include "Chinese::HSK1", "Chinese::HSK2", etc.
- **false**: Show only cards in the exact deck selected

### showCategories

Whether to show category breakdowns (HSK levels, frequency bands):

- **true** (default): Show detailed breakdowns
- **false**: Show only total/reviewed counts

### categoriesToShow

List of categories to display in the statistics. Available categories:

**HSK 2012 (Old HSK):**
- HSK (2012) Level 1
- HSK (2012) Level 2
- HSK (2012) Level 3
- HSK (2012) Level 4
- HSK (2012) Level 5
- HSK (2012) Level 6

**HSK 2021 (New HSK 3.0):**
- HSK (2021) Band 1
- HSK (2021) Band 2
- HSK (2021) Band 3
- HSK (2021) Band 4
- HSK (2021) Band 5
- HSK (2021) Band 6
- HSK (2021) Band 7
- HSK (2021) Band 8
- HSK (2021) Band 9

**Frequency:**
- Top 500
- Top 1000
- Top 1500
- Top 2000

## Statistics Explained

### Total Hanzi

All unique Hanzi characters found in the deck, including:
- New cards (not yet studied)
- Learning cards
- Review cards
- Relearning cards

Excludes suspended and buried cards.

### Reviewed Hanzi

Unique Hanzi characters from cards you've actually reviewed at least once. These are cards that appear in your review history.

This metric shows what you've been exposed to, not necessarily what you've mastered.

## Data Sources

- **HSK 2021 Data**: 3,000 characters from the official HSK 3.0 (2021) standard
- **HSK 2012 Data**: Legacy HSK levels 1-6
- **Frequency Data**: Based on Jun Da's Modern Chinese Character Frequency List (193 million character corpus)

## Usage

1. Go to **Tools → Hanzi Deck Stats**
2. Select a deck from the dropdown (or "All Decks")
3. Check/uncheck "Include subdecks" as needed
4. Click "Refresh" to recalculate statistics

The report shows:
- Total vs. Reviewed counts with progress bars
- Category breakdowns (if enabled)
- Multiple decks when viewing "All Decks"
