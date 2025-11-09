"""
Statistics dialog UI for Hanzi Deck Statistics addon.
"""

from typing import List, Dict

from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
    QCheckBox, QPushButton, QLabel, QWidget, QScrollArea, QFrame, QGroupBox
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

        # Store deck selection data: {deck_id: {'name': str, 'checkbox': QCheckBox, 'fields': [QCheckBox], 'subdecks': [QCheckBox]}}
        self.deck_data: Dict[int, Dict] = {}

        # Flag to prevent refreshes during UI setup
        self._is_loading = True

        # Setup UI
        self._setup_ui()

        # Setup complete, enable auto-refresh
        self._is_loading = False

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
            QGroupBox {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #1976d2;
                font-weight: bold;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Title row
        title_label = QLabel("Select Decks to Analyze:")
        title_label.setStyleSheet("font-size: 10px;")
        main_layout.addWidget(title_label)

        # Scrollable area for deck selections
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(5)

        # Populate deck checkboxes
        self._populate_deck_checkboxes(scroll_layout)

        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        controls_widget.setLayout(main_layout)
        return controls_widget

    def _populate_deck_checkboxes(self, layout: QVBoxLayout):
        """Populate deck checkboxes with field and subdeck options."""
        deck_list = self.calculator.get_deck_list()

        # Skip "All Decks" entry (deck_id == 0)
        for deck_id, deck_name in deck_list:
            if deck_id == 0:  # Skip "All Decks"
                continue

            # Skip subdecks (we'll handle them separately)
            if "::" in deck_name:
                continue

            # Create container widget for this deck
            deck_widget = QWidget()
            deck_widget.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 6px;
                }
            """)
            deck_layout = QVBoxLayout()
            deck_layout.setContentsMargins(6, 6, 6, 6)
            deck_layout.setSpacing(8)

            # Header row with checkbox and deck name
            header_row = QHBoxLayout()
            deck_cb = QCheckBox()
            # Load saved state from config
            saved_decks = self.config.get('selectedDecks', {})
            deck_cb.setChecked(saved_decks.get(str(deck_id), {}).get('selected', False))
            deck_cb.setStyleSheet("""
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
            """)
            deck_cb.stateChanged.connect(lambda state, did=deck_id: self._on_deck_toggled(did, state))
            deck_cb.stateChanged.connect(self.refresh_stats)

            deck_label = QLabel(deck_name)
            deck_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #1976d2;")

            header_row.addWidget(deck_cb)
            header_row.addWidget(deck_label)
            header_row.addStretch()
            deck_layout.addLayout(header_row)

            # Options container (hidden by default)
            options_widget = QWidget()
            options_layout = QVBoxLayout()
            options_layout.setContentsMargins(25, 0, 0, 0)
            options_layout.setSpacing(6)

            # Field selection checkboxes
            fields_label = QLabel("Fields to include:")
            fields_label.setStyleSheet("font-weight: bold; font-size: 9px; color: #666;")
            options_layout.addWidget(fields_label)

            # Get field names for this deck
            field_names = self._get_field_names_for_deck(deck_id)

            field_options = [
                ("all", "All Fields"),
                ("sortField", "Sort Field Only"),
            ]

            # Add individual field options with actual names
            for i, field_name in enumerate(field_names[:5], 1):  # Limit to first 5 fields
                field_options.append((str(i), field_name))

            field_checkboxes = []
            saved_fields = saved_decks.get(str(deck_id), {}).get('fields', ['all'])
            for field_value, field_label in field_options:
                field_cb = QCheckBox(field_label)
                field_cb.setStyleSheet("margin-left: 8px; font-size: 9px;")
                # Check if this field was previously selected
                field_cb.setChecked(field_value in saved_fields)
                field_cb.stateChanged.connect(self.refresh_stats)
                options_layout.addWidget(field_cb)
                field_checkboxes.append((field_value, field_cb))

            # Subdeck selection checkboxes
            subdeck_checkboxes = []
            saved_subdecks = saved_decks.get(str(deck_id), {}).get('subdecks', [])
            # Get subdecks for this deck
            subdecks_exist = False
            for sub_id, sub_name in deck_list:
                if sub_name.startswith(deck_name + "::"):
                    if not subdecks_exist:
                        # Add label for subdecks
                        subdecks_label = QLabel("Subdecks to include:")
                        subdecks_label.setStyleSheet("font-weight: bold; font-size: 9px; color: #666; margin-top: 6px;")
                        options_layout.addWidget(subdecks_label)
                        subdecks_exist = True

                    subdeck_cb = QCheckBox(sub_name.split("::")[-1])  # Just show the last part
                    subdeck_cb.setStyleSheet("margin-left: 8px; font-size: 9px;")
                    # Restore saved state, default to True if not saved yet
                    if saved_subdecks:
                        subdeck_cb.setChecked(sub_id in saved_subdecks)
                    else:
                        subdeck_cb.setChecked(True)  # Default to including subdecks
                    subdeck_cb.stateChanged.connect(self.refresh_stats)
                    options_layout.addWidget(subdeck_cb)
                    subdeck_checkboxes.append((sub_id, sub_name, subdeck_cb))

            options_widget.setLayout(options_layout)
            # Show options if deck was previously selected
            options_widget.setVisible(deck_cb.isChecked())
            deck_layout.addWidget(options_widget)

            deck_widget.setLayout(deck_layout)
            layout.addWidget(deck_widget)

            # Store deck data
            self.deck_data[deck_id] = {
                'name': deck_name,
                'checkbox': deck_cb,
                'fields': field_checkboxes,
                'subdecks': subdeck_checkboxes,
                'options_widget': options_widget
            }

        layout.addStretch()

    def _get_field_names_for_deck(self, deck_id: int) -> List[str]:
        """Get field names from the most common note type in a deck."""
        try:
            # Get deck and its subdecks
            deck_ids = mw.col.decks.deck_and_child_ids(deck_id)

            # Query to find the most common note type in this deck (including subdecks)
            placeholders = ','.join('?' * len(deck_ids))
            query = f"""
                SELECT notes.mid, COUNT(*) as cnt
                FROM cards
                INNER JOIN notes ON cards.nid = notes.id
                WHERE cards.did IN ({placeholders})
                GROUP BY notes.mid
                ORDER BY cnt DESC
                LIMIT 1
            """
            results = mw.col.db.execute(query, *deck_ids)

            if results and len(results) > 0:
                model_id = results[0][0]
                model = mw.col.models.get(model_id)
                if model:
                    field_names = [field['name'] for field in model['flds']]
                    return field_names
        except Exception as e:
            print(f"Error getting field names for deck {deck_id}: {e}")
            import traceback
            traceback.print_exc()

        # Fallback to generic names
        return ["1st Field", "2nd Field", "3rd Field", "4th Field", "5th Field"]

    def _on_deck_toggled(self, deck_id: int, state: int):
        """Handle deck checkbox toggle - show/hide field and subdeck options."""
        is_checked = state == 2  # Qt.Checked == 2
        deck_info = self.deck_data.get(deck_id)

        if deck_info:
            # Show/hide the options widget
            deck_info['options_widget'].setVisible(is_checked)

    def _save_selections(self):
        """Save current deck/field/subdeck selections to config."""
        selected_decks = {}

        for deck_id, deck_info in self.deck_data.items():
            # Get selected fields
            selected_fields = []
            for field_value, field_cb in deck_info['fields']:
                if field_cb.isChecked():
                    selected_fields.append(field_value)

            # Get selected subdecks
            selected_subdecks = []
            for sub_id, sub_name, subdeck_cb in deck_info['subdecks']:
                if subdeck_cb.isChecked():
                    selected_subdecks.append(sub_id)

            # Save this deck's state
            selected_decks[str(deck_id)] = {
                'selected': deck_info['checkbox'].isChecked(),
                'fields': selected_fields,
                'subdecks': selected_subdecks
            }

        # Update config
        self.config['selectedDecks'] = selected_decks
        mw.addonManager.writeConfig(__name__.split('.')[0], self.config)

    def refresh_stats(self):
        """Recalculate and display statistics."""
        # Skip refresh during UI setup
        if self._is_loading:
            return

        # Save current selections to config
        self._save_selections()

        # Show progress indicator
        mw.progress.start(label="Calculating Hanzi statistics...")

        try:
            all_stats = []

            # Process each selected deck
            for deck_id, deck_info in self.deck_data.items():
                if not deck_info['checkbox'].isChecked():
                    continue  # Skip unselected decks

                # Get selected fields for this deck
                selected_fields = []
                for field_value, field_cb in deck_info['fields']:
                    if field_cb.isChecked():
                        selected_fields.append(field_value)

                # If no fields selected, skip this deck
                if not selected_fields:
                    continue

                # Get selected subdecks
                selected_subdeck_ids = [deck_id]  # Always include the main deck
                for sub_id, sub_name, subdeck_cb in deck_info['subdecks']:
                    if subdeck_cb.isChecked():
                        selected_subdeck_ids.append(sub_id)

                # Calculate stats with combined fields
                stats = self._calculate_deck_stats_with_combined_fields(
                    deck_id,
                    deck_info['name'],
                    selected_subdeck_ids,
                    selected_fields
                )
                all_stats.append(stats)

            # Generate HTML
            if len(all_stats) == 0:
                html = self._generate_no_selection_html()
            elif len(all_stats) == 1:
                html = self._generate_single_deck_html(all_stats[0])
            else:
                html = self._generate_multi_deck_html(all_stats)

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

    def _calculate_deck_stats_with_combined_fields(self, deck_id: int, deck_name: str,
                                                     subdeck_ids: List[int], field_values: List[str]):
        """Calculate stats for a deck combining multiple fields."""
        from .stats_calculator import DeckStatistics

        # Create descriptive name with selected fields
        field_names = self._get_field_names_for_deck(deck_id)
        field_labels = []

        for field_value in field_values:
            if field_value == 'all':
                field_labels.append('All Fields')
            elif field_value == 'sortField':
                field_labels.append('Sort Field')
            elif field_value.isdigit():
                field_index = int(field_value) - 1
                if 0 <= field_index < len(field_names):
                    field_labels.append(field_names[field_index])
                else:
                    field_labels.append(f"Field {field_value}")
            else:
                field_labels.append(field_value)

        if len(field_labels) == 1:
            display_name = f"{deck_name} ({field_labels[0]})"
        else:
            display_name = f"{deck_name} ({', '.join(field_labels)})"

        stats = DeckStatistics(deck_id, display_name)

        # Combine hanzi from all selected fields
        total_hanzi_combined = set()
        reviewed_hanzi_combined = set()

        for field_value in field_values:
            # Update config temporarily
            self.config['fieldToUseForStats'] = field_value
            self.calculator.config = self.config

            # Get hanzi for this field
            field_total = self.calculator._get_hanzi_from_cards(subdeck_ids, include_new=True, field_mode=field_value)
            field_reviewed = self.calculator._get_hanzi_from_cards(subdeck_ids, include_new=False, field_mode=field_value)

            # Union with existing sets
            total_hanzi_combined.update(field_total)
            reviewed_hanzi_combined.update(field_reviewed)

        stats.total_hanzi = total_hanzi_combined
        stats.reviewed_hanzi = reviewed_hanzi_combined

        # Categorize characters
        if self.config.get('showCategories', True):
            stats.total_categorized = self.calculator.character_data.categorize_characters(stats.total_hanzi)
            stats.reviewed_categorized = self.calculator.character_data.categorize_characters(stats.reviewed_hanzi)

        return stats

    def _calculate_deck_stats_with_specific_decks(self, deck_id: int, deck_name: str,
                                                    subdeck_ids: List[int], field_value: str):
        """Calculate stats for a deck with specific subdeck IDs."""
        from .stats_calculator import DeckStatistics

        # Create stats object with a descriptive name
        # Get the actual field name for this deck
        field_names = self._get_field_names_for_deck(deck_id)

        if field_value == 'all':
            field_label = 'All Fields'
        elif field_value == 'sortField':
            field_label = 'Sort Field'
        elif field_value.isdigit():
            field_index = int(field_value) - 1  # Convert to 0-based index
            if 0 <= field_index < len(field_names):
                field_label = field_names[field_index]
            else:
                field_label = f"Field {field_value}"
        else:
            field_label = field_value

        display_name = f"{deck_name} ({field_label})"

        stats = DeckStatistics(deck_id, display_name)

        # Get field mode
        field_mode = field_value

        # Query for all cards (including new/unseen cards)
        stats.total_hanzi = self.calculator._get_hanzi_from_cards(subdeck_ids, include_new=True, field_mode=field_mode)

        # Query for only reviewed cards
        stats.reviewed_hanzi = self.calculator._get_hanzi_from_cards(subdeck_ids, include_new=False, field_mode=field_mode)

        # Categorize characters
        if self.config.get('showCategories', True):
            stats.total_categorized = self.calculator.character_data.categorize_characters(stats.total_hanzi)
            stats.reviewed_categorized = self.calculator.character_data.categorize_characters(stats.reviewed_hanzi)

        return stats

    def _generate_no_selection_html(self) -> str:
        """Generate HTML when no decks are selected."""
        html = self._get_html_header()
        html += """
        <h1>Hanzi Deck Statistics</h1>
        <p style="font-size: 1.2em; color: #666; margin-top: 50px; text-align: center;">
            Please select at least one deck and one field to view statistics.
        </p>
        </body></html>
        """
        return html

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

        # HSK 2012 (2.0)
        if any('HSK 2.0' in cat or 'Level' in cat for cat in categories_to_show):
            html += "<h4>HSK 2.0 (2012)</h4>"
            html += self._generate_category_table(stats, 'hsk_2012')

        # HSK 2021 (3.0)
        if any('HSK 3.0' in cat or 'Band' in cat for cat in categories_to_show):
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

        # Get official character lists for HSK types
        official_chars = {}
        if category_type == 'hsk_2012':
            official_chars = self.calculator.character_data.get_official_hsk_2012_characters()
        elif category_type == 'hsk_2021':
            official_chars = self.calculator.character_data.get_official_hsk_2021_characters()

        html = """
        <table class="category-table">
            <tr>
                <th>Category</th>
                <th class="tooltip-header" data-tooltip="Total unique Hanzi in this category found in your deck">In Deck ℹ️</th>
                <th class="tooltip-header" data-tooltip="Hanzi you've reviewed at least once">Reviewed ℹ️</th>
        """

        # Add Official column for HSK categories
        if official_chars:
            html += '<th class="tooltip-header" data-tooltip="Total Hanzi in official HSK list for this category">Official ℹ️</th>'

        html += """
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

            # Get official characters and calculate not-in-deck
            official_category_chars = official_chars.get(category_name, set()) if official_chars else set()
            not_in_deck_chars = official_category_chars - total_chars
            official_count = len(official_category_chars)

            if total_count > 0 or official_count > 0:  # Show categories with characters
                # Prepare character data for JavaScript
                char_data = {
                    'reviewed': sorted(list(reviewed_chars)),
                    'missing': sorted(list(missing_chars)),
                    'notInDeck': sorted(list(not_in_deck_chars)),
                    'category': category_name
                }
                char_data_json = html_module.escape(json.dumps(char_data))

                html += f"""
                <tr class="clickable-row" data-chars='{char_data_json}' onclick="showCharacterDetails(this)" title="Click to see character details">
                    <td>{category_name}</td>
                    <td>{total_count}</td>
                    <td>{reviewed_count}</td>
                """

                # Add official count if applicable
                if official_chars:
                    html += f"<td>{official_count}</td>"

                html += f"""
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
                .not-in-deck-section .char-list {
                    background-color: #fff3e0;
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
                    var notInDeckChars = document.getElementById('notInDeckChars');
                    var reviewedCount = document.getElementById('reviewedCount');
                    var missingCount = document.getElementById('missingCount');
                    var notInDeckCount = document.getElementById('notInDeckCount');
                    var notInDeckSection = document.getElementById('notInDeckSection');

                    modalTitle.textContent = charData.category + ' - Character Details';
                    reviewedChars.textContent = charData.reviewed.join(' ') || 'None';
                    missingChars.textContent = charData.missing.join(' ') || 'None';
                    reviewedCount.textContent = charData.reviewed.length + ' characters';
                    missingCount.textContent = charData.missing.length + ' characters';

                    // Show/hide "Not in Deck" section based on whether we have data
                    if (charData.notInDeck && charData.notInDeck.length > 0) {
                        notInDeckChars.textContent = charData.notInDeck.join(' ');
                        notInDeckCount.textContent = charData.notInDeck.length + ' characters';
                        notInDeckSection.style.display = 'block';
                    } else {
                        notInDeckSection.style.display = 'none';
                    }

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
                        <div class="char-section not-in-deck-section" id="notInDeckSection">
                            <h3>⊘ Not in Deck</h3>
                            <div class="char-list" id="notInDeckChars"></div>
                            <div class="char-count" id="notInDeckCount"></div>
                        </div>
                    </div>
                </div>
            </div>
        """


def show_stats_dialog():
    """Show the Hanzi statistics dialog."""
    dialog = HanziStatsDialog(mw)
    dialog.exec()
