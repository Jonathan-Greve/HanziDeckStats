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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Controls at top
        controls = self._create_controls()
        layout.addWidget(controls, stretch=0)

        # Stats display (HTML)
        self.webview = AnkiWebView(parent=self)
        layout.addWidget(self.webview, stretch=1)

        self.setLayout(layout)

    def _create_controls(self) -> QWidget:
        """Create the control panel at the top of the dialog."""
        controls_widget = QWidget()
        controls_widget.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333333;
                font-weight: bold;
            }
            QComboBox {
                background-color: white;
                color: #333333;
                border: 1px solid #cccccc;
                padding: 4px;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QCheckBox {
                color: #333333;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # First row: Deck and Field selectors
        row1 = QHBoxLayout()

        # Deck selector
        row1.addWidget(QLabel("Deck:"))
        self.deck_selector = QComboBox()
        self._populate_deck_selector()
        row1.addWidget(self.deck_selector, stretch=2)

        # Field selector
        row1.addWidget(QLabel("Fields:"))
        self.field_selector = QComboBox()
        self.field_selector.addItem("All Fields", "all")
        self.field_selector.addItem("Sort Field Only", "sortField")
        self.field_selector.addItem("1st Field", "1")
        self.field_selector.addItem("2nd Field", "2")
        self.field_selector.addItem("3rd Field", "3")
        self.field_selector.addItem("4th Field", "4")
        self.field_selector.addItem("5th Field", "5")
        # Set default from config
        default_field = self.config.get('fieldToUseForStats', 'all')
        for i in range(self.field_selector.count()):
            if self.field_selector.itemData(i) == default_field:
                self.field_selector.setCurrentIndex(i)
                break
        row1.addWidget(self.field_selector, stretch=1)

        main_layout.addLayout(row1)

        # Second row: Checkbox and Refresh button
        row2 = QHBoxLayout()

        # Include subdecks checkbox
        self.include_subdecks_cb = QCheckBox("Include subdecks")
        default_include = self.config.get('includeSubdecks', True)
        self.include_subdecks_cb.setChecked(default_include)
        row2.addWidget(self.include_subdecks_cb)

        row2.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_stats)
        row2.addWidget(refresh_btn)

        main_layout.addLayout(row2)

        controls_widget.setLayout(main_layout)
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

            # Get selected field and update config temporarily
            selected_field = self.field_selector.currentData()
            self.config['fieldToUseForStats'] = selected_field
            self.calculator.config = self.config

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

        # HSK 2021 (3.0)
        if any('HSK' in cat for cat in categories_to_show):
            html += "<h4>HSK 3.0 (2021)</h4>"
            html += self._generate_category_table(stats, 'hsk_2021')

        # Frequency
        if any('Top' in cat for cat in categories_to_show):
            html += "<h4>Frequency</h4>"
            html += self._generate_category_table(stats, 'frequency')

        return html

    def _generate_category_table(self, stats: DeckStatistics, category_type: str) -> str:
        """Generate HTML table for a specific category type."""
        import json
        import html as html_module

        total_cat = stats.total_categorized.get(category_type, {})
        reviewed_cat = stats.reviewed_categorized.get(category_type, {})

        if not total_cat:
            return "<p><em>No data available</em></p>"

        html = """
        <table class="category-table">
            <tr>
                <th>Category</th>
                <th class="tooltip-header" data-tooltip="Total unique Hanzi in this category found in your deck">Total ℹ️</th>
                <th class="tooltip-header" data-tooltip="Hanzi you've reviewed at least once">Reviewed ℹ️</th>
                <th>Progress</th>
            </tr>
        """

        for category_name, total_chars in total_cat.items():
            reviewed_chars = reviewed_cat.get(category_name, set())
            total_count = len(total_chars)
            reviewed_count = len(reviewed_chars)
            pct = (reviewed_count / total_count * 100) if total_count > 0 else 0

            # Calculate missing characters
            missing_chars = total_chars - reviewed_chars

            if total_count > 0:  # Only show categories with characters
                # Prepare character data for JavaScript
                char_data = {
                    'reviewed': sorted(list(reviewed_chars)),
                    'missing': sorted(list(missing_chars)),
                    'category': category_name
                }
                char_data_json = html_module.escape(json.dumps(char_data))

                html += f"""
                <tr class="clickable-row" data-chars='{char_data_json}' onclick="showCharacterDetails(this)" title="Click to see character details">
                    <td>{category_name}</td>
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
                .tooltip-header {
                    position: relative;
                    cursor: help;
                }
                .tooltip-header:hover::after {
                    content: attr(data-tooltip);
                    position: absolute;
                    bottom: 100%;
                    left: 50%;
                    transform: translateX(-50%);
                    background-color: #333;
                    color: white;
                    padding: 8px 12px;
                    border-radius: 4px;
                    white-space: nowrap;
                    font-size: 12px;
                    font-weight: normal;
                    z-index: 100;
                    margin-bottom: 5px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                }
                .tooltip-header:hover::before {
                    content: '';
                    position: absolute;
                    bottom: 100%;
                    left: 50%;
                    transform: translateX(-50%);
                    border: 5px solid transparent;
                    border-top-color: #333;
                    z-index: 100;
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
                .clickable-row {
                    cursor: pointer;
                    transition: background-color 0.2s;
                }
                .clickable-row:hover {
                    background-color: #e3f2fd !important;
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

                /* Modal styles */
                .modal {
                    display: none;
                    position: fixed;
                    z-index: 1000;
                    left: 0;
                    top: 0;
                    width: 100%;
                    height: 100%;
                    overflow: auto;
                    background-color: rgba(0,0,0,0.5);
                }
                .modal-content {
                    background-color: #fefefe;
                    margin: 5% auto;
                    padding: 0;
                    border: 1px solid #888;
                    border-radius: 8px;
                    width: 80%;
                    max-width: 800px;
                    max-height: 80vh;
                    display: flex;
                    flex-direction: column;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                }
                .modal-header {
                    padding: 20px;
                    background-color: #1976d2;
                    color: white;
                    border-radius: 8px 8px 0 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .modal-header h2 {
                    margin: 0;
                    color: white;
                    border: none;
                    padding: 0;
                }
                .modal-body {
                    padding: 20px;
                    overflow-y: auto;
                    flex: 1;
                }
                .close {
                    color: white;
                    font-size: 32px;
                    font-weight: bold;
                    cursor: pointer;
                    line-height: 1;
                    padding: 0 10px;
                }
                .close:hover {
                    opacity: 0.7;
                }
                .char-section {
                    margin-bottom: 25px;
                }
                .char-section h3 {
                    color: #424242;
                    margin-top: 0;
                    margin-bottom: 12px;
                    padding-bottom: 8px;
                    border-bottom: 2px solid #e0e0e0;
                }
                .char-list {
                    font-size: 28px;
                    line-height: 1.8;
                    letter-spacing: 8px;
                    padding: 15px;
                    background-color: #f5f5f5;
                    border-radius: 4px;
                    word-wrap: break-word;
                }
                .reviewed-section .char-list {
                    background-color: #e8f5e9;
                }
                .missing-section .char-list {
                    background-color: #ffebee;
                }
                .char-count {
                    font-size: 14px;
                    color: #666;
                    margin-top: 8px;
                    font-style: italic;
                }
            </style>
            <script>
                function showCharacterDetails(row) {
                    var charData = JSON.parse(row.getAttribute('data-chars'));
                    var modal = document.getElementById('charModal');
                    var modalTitle = document.getElementById('modalTitle');
                    var reviewedChars = document.getElementById('reviewedChars');
                    var missingChars = document.getElementById('missingChars');
                    var reviewedCount = document.getElementById('reviewedCount');
                    var missingCount = document.getElementById('missingCount');

                    modalTitle.textContent = charData.category + ' - Character Details';
                    reviewedChars.textContent = charData.reviewed.join(' ') || 'None';
                    missingChars.textContent = charData.missing.join(' ') || 'None';
                    reviewedCount.textContent = charData.reviewed.length + ' characters';
                    missingCount.textContent = charData.missing.length + ' characters';

                    modal.style.display = 'block';
                }

                function closeModal() {
                    document.getElementById('charModal').style.display = 'none';
                }

                window.onclick = function(event) {
                    var modal = document.getElementById('charModal');
                    if (event.target == modal) {
                        modal.style.display = 'none';
                    }
                }
            </script>
        </head>
        <body>
            <!-- Modal -->
            <div id="charModal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2 id="modalTitle">Character Details</h2>
                        <span class="close" onclick="closeModal()">&times;</span>
                    </div>
                    <div class="modal-body">
                        <div class="char-section reviewed-section">
                            <h3>✓ Reviewed Characters</h3>
                            <div class="char-list" id="reviewedChars"></div>
                            <div class="char-count" id="reviewedCount"></div>
                        </div>
                        <div class="char-section missing-section">
                            <h3>✗ Not Yet Reviewed</h3>
                            <div class="char-list" id="missingChars"></div>
                            <div class="char-count" id="missingCount"></div>
                        </div>
                    </div>
                </div>
            </div>
        """


def show_stats_dialog():
    """Show the Hanzi statistics dialog."""
    dialog = HanziStatsDialog(mw)
    dialog.exec()
