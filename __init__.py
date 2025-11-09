"""
Hanzi Deck Statistics - Anki Addon
Track Hanzi characters learned per deck with HSK and frequency breakdowns.
"""

from aqt import mw, gui_hooks
from aqt.qt import QAction

from .stats_dialog import show_stats_dialog


def setup_menu():
    """Add menu item to Tools menu."""
    action = QAction("Hanzi Deck Stats", mw)
    action.triggered.connect(show_stats_dialog)
    mw.form.menuTools.addAction(action)


# Initialize addon when Anki starts
gui_hooks.main_window_did_init.append(setup_menu)
