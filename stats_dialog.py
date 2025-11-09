"""
Statistics dialog UI for Hanzi Deck Statistics addon.
"""

from typing import List

from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
    QCheckBox, QPushButton, QLabel, QWidget
)
from aqt.webview import AnkiWebView

from .stats_calculator import StatsCalculator, DeckStatistics


class HanziStatsDialog(QDialog):
    """Dialog window for displaying Hanzi deck statistics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hanzi Deck Statistics")
        self.resize(800, 700)

        # Get config
        self.config = mw.addonManager.getConfig(__name__.split('.')[0])

        # Create calculator
        self.calculator = StatsCalculator(mw.col, self.config)

        # Setup UI
        self._setup_ui()

        # Load initial stats
        self.refresh_stats()

    def _setup_ui(self):
        """Setup the dialog UI layout."""
        layout = QVBoxLayout()

        # Controls at top
        controls = self._create_controls()
        layout.addWidget(controls)

        # Stats display (HTML)
        self.webview = AnkiWebView(parent=self)
        layout.addWidget(self.webview)

        self.setLayout(layout)

    def _create_controls(self) -> QWidget:
        """Create the control panel at the top of the dialog."""
        controls_widget = QWidget()
        controls_layout = QHBoxLayout()

        # Deck selector
        controls_layout.addWidget(QLabel("Deck:"))
        self.deck_selector = QComboBox()
        self._populate_deck_selector()
        controls_layout.addWidget(self.deck_selector, stretch=2)

        # Include subdecks checkbox
        self.include_subdecks_cb = QCheckBox("Include subdecks")
        default_include = self.config.get('includeSubdecks', True)
        self.include_subdecks_cb.setChecked(default_include)
        controls_layout.addWidget(self.include_subdecks_cb)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_stats)
        controls_layout.addWidget(refresh_btn)

        controls_widget.setLayout(controls_layout)
        return controls_widget

    def _populate_deck_selector(self):
        """Populate the deck selector dropdown."""
        self.deck_selector.clear()

        deck_list = self.calculator.get_deck_list()
        for deck_id, deck_name in deck_list:
            self.deck_selector.addItem(deck_name, deck_id)

    def refresh_stats(self):
        """Recalculate and display statistics."""
        # Show progress indicator
        mw.progress.start(label="Calculating Hanzi statistics...")

        try:
            # Get selected deck
            deck_id = self.deck_selector.currentData()
            include_subdecks = self.include_subdecks_cb.isChecked()

            # Calculate stats
            if deck_id == 0:
                # All decks
                all_stats = self.calculator.calculate_all_decks_stats(include_subdecks)
                html = self._generate_multi_deck_html(all_stats)
            else:
                # Single deck
                stats = self.calculator.calculate_deck_stats(deck_id, include_subdecks)
                html = self._generate_single_deck_html(stats)

            # Display HTML
            self.webview.stdHtml(html)

        except Exception as e:
            error_html = f"""
            <html>
            <body style="font-family: sans-serif; padding: 20px;">
                <h1 style="color: #d32f2f;">Error</h1>
                <p>An error occurred while calculating statistics:</p>
                <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 5px;">{str(e)}</pre>
            </body>
            </html>
            """
            self.webview.stdHtml(error_html)
            print(f"Error in refresh_stats: {e}")
            import traceback
            traceback.print_exc()

        finally:
            mw.progress.finish()

    def _generate_multi_deck_html(self, all_stats: List[DeckStatistics]) -> str:
        """Generate HTML report for multiple decks."""
        html = self._get_html_header()
        html += "<h1>Hanzi Statistics - All Decks</h1>"

        # Generate section for each deck
        for stats in all_stats:
            html += self._generate_deck_section(stats)

        html += "</body></html>"
        return html

    def _generate_single_deck_html(self, stats: DeckStatistics) -> str:
        """Generate HTML report for a single deck."""
        html = self._get_html_header()
        html += f"<h1>Hanzi Statistics - {stats.deck_name}</h1>"
        html += self._generate_deck_section(stats, show_title=False)
        html += "</body></html>"
        return html

    def _generate_deck_section(self, stats: DeckStatistics, show_title: bool = True) -> str:
        """Generate HTML section for a single deck's statistics."""
        total_count = len(stats.total_hanzi)
        reviewed_count = len(stats.reviewed_hanzi)
        reviewed_pct = (reviewed_count / total_count * 100) if total_count > 0 else 0

        html = ""

        if show_title:
            html += f"<h2>{stats.deck_name}</h2>"

        # Summary table
        html += """
        <table class="summary-table">
            <tr>
                <th>Metric</th>
                <th>Count</th>
                <th>Percentage</th>
                <th>Progress</th>
            </tr>
        """

        html += f"""
            <tr>
                <td><strong>Total Hanzi</strong></td>
                <td>{total_count}</td>
                <td>100%</td>
                <td>
                    <div class="progress">
                        <div class="progress-bar" style="width: 100%"></div>
                    </div>
                </td>
            </tr>
            <tr>
                <td><strong>Reviewed Hanzi</strong></td>
                <td>{reviewed_count}</td>
                <td>{reviewed_pct:.1f}%</td>
                <td>
                    <div class="progress">
                        <div class="progress-bar progress-bar-reviewed" style="width: {reviewed_pct}%"></div>
                    </div>
                </td>
            </tr>
        """

        html += "</table>"

        # Category breakdown if enabled
        if self.config.get('showCategories', True):
            html += self._generate_category_breakdown(stats)

        return html

    def _generate_category_breakdown(self, stats: DeckStatistics) -> str:
        """Generate HTML for category breakdown (HSK levels, frequency)."""
        html = "<h3>Category Breakdown</h3>"

        categories_to_show = self.config.get('categoriesToShow', [])

        # HSK 2012
        if any('HSK (2012)' in cat for cat in categories_to_show):
            html += "<h4>HSK 2012</h4>"
            html += self._generate_category_table(stats, 'hsk_2012', 'Level')

        # HSK 2021
        if any('HSK (2021)' in cat or 'HSK (2020)' in cat for cat in categories_to_show):
            html += "<h4>HSK 2021</h4>"
            html += self._generate_category_table(stats, 'hsk_2021', 'Band')

        # Frequency
        if any('Top' in cat for cat in categories_to_show):
            html += "<h4>Frequency</h4>"
            html += self._generate_category_table(stats, 'frequency', '')

        return html

    def _generate_category_table(self, stats: DeckStatistics, category_type: str, prefix: str) -> str:
        """Generate HTML table for a specific category type."""
        total_cat = stats.total_categorized.get(category_type, {})
        reviewed_cat = stats.reviewed_categorized.get(category_type, {})

        if not total_cat:
            return "<p><em>No data available</em></p>"

        html = """
        <table class="category-table">
            <tr>
                <th>Category</th>
                <th>Total</th>
                <th>Reviewed</th>
                <th>Progress</th>
            </tr>
        """

        for category_name, total_chars in total_cat.items():
            reviewed_chars = reviewed_cat.get(category_name, set())
            total_count = len(total_chars)
            reviewed_count = len(reviewed_chars)
            pct = (reviewed_count / total_count * 100) if total_count > 0 else 0

            if total_count > 0:  # Only show categories with characters
                display_name = f"{prefix} {category_name}" if prefix else category_name
                html += f"""
                <tr>
                    <td>{display_name}</td>
                    <td>{total_count}</td>
                    <td>{reviewed_count}</td>
                    <td>
                        <div class="progress">
                            <div class="progress-bar progress-bar-category" style="width: {pct}%"></div>
                        </div>
                    </td>
                </tr>
                """

        html += "</table>"
        return html

    def _get_html_header(self) -> str:
        """Get HTML header with styles."""
        return """
        <html>
        <head>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    padding: 20px;
                    color: #333;
                    background-color: #fafafa;
                }
                h1 {
                    color: #1976d2;
                    border-bottom: 3px solid #1976d2;
                    padding-bottom: 10px;
                }
                h2 {
                    color: #424242;
                    border-bottom: 2px solid #e0e0e0;
                    padding-bottom: 8px;
                    margin-top: 30px;
                }
                h3 {
                    color: #616161;
                    margin-top: 25px;
                }
                h4 {
                    color: #757575;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }
                table {
                    border-collapse: collapse;
                    width: 100%;
                    background-color: white;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                    border-radius: 4px;
                    margin-bottom: 20px;
                }
                th, td {
                    padding: 12px 16px;
                    text-align: left;
                }
                th {
                    background-color: #f5f5f5;
                    font-weight: 600;
                    color: #424242;
                    border-bottom: 2px solid #e0e0e0;
                }
                td {
                    border-bottom: 1px solid #f0f0f0;
                }
                tr:last-child td {
                    border-bottom: none;
                }
                tr:hover {
                    background-color: #fafafa;
                }
                .summary-table {
                    font-size: 1.1em;
                }
                .category-table {
                    font-size: 0.95em;
                    margin-left: 20px;
                }
                .progress {
                    background-color: #e0e0e0;
                    height: 24px;
                    border-radius: 12px;
                    overflow: hidden;
                    min-width: 100px;
                }
                .progress-bar {
                    background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
                    height: 100%;
                    transition: width 0.3s ease;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 0.85em;
                    font-weight: 500;
                }
                .progress-bar-reviewed {
                    background: linear-gradient(90deg, #2196F3 0%, #1976D2 100%);
                }
                .progress-bar-category {
                    background: linear-gradient(90deg, #FF9800 0%, #F57C00 100%);
                }
            </style>
        </head>
        <body>
        """


def show_stats_dialog():
    """Show the Hanzi statistics dialog."""
    dialog = HanziStatsDialog(mw)
    dialog.exec()
