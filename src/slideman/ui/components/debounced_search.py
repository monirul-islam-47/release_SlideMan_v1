# src/slideman/ui/components/debounced_search.py

from PySide6.QtWidgets import (QLineEdit, QWidget, QHBoxLayout, QVBoxLayout, 
                               QLabel, QPushButton, QFrame, QCompleter)
from PySide6.QtCore import QTimer, Signal, Qt, QStringListModel, QRunnable, QThreadPool
from PySide6.QtGui import QIcon
import logging
from typing import List, Optional, Callable

class SearchWorker(QRunnable):
    """Worker for performing search operations in background thread."""
    
    def __init__(self, search_term: str, search_function: Callable, callback: Callable):
        super().__init__()
        self.search_term = search_term
        self.search_function = search_function
        self.callback = callback
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        """Execute the search in background thread."""
        try:
            self.logger.debug(f"Executing search for: '{self.search_term}'")
            results = self.search_function(self.search_term)
            # Note: Cannot directly emit signals from QRunnable
            # Results are passed back via callback
            self.callback(self.search_term, results)
        except Exception as e:
            self.logger.error(f"Search worker failed: {e}", exc_info=True)
            self.callback(self.search_term, [])


class DebouncedSearchWidget(QWidget):
    """
    A search widget with debouncing, auto-complete, and background search capabilities.
    """
    
    # Signals
    searchRequested = Signal(str)           # Emitted when search should be performed
    searchCleared = Signal()                # Emitted when search is cleared
    searchResultsReady = Signal(str, list)  # Emitted when background search completes
    
    def __init__(self, placeholder: str = "Search...", debounce_ms: int = 300, parent=None):
        super().__init__(parent)
        self.placeholder = placeholder
        self.debounce_delay = debounce_ms
        self.logger = logging.getLogger(__name__)
        
        # State
        self._search_function: Optional[Callable] = None
        self._suggestions: List[str] = []
        self._last_search_term = ""
        self._is_searching = False
        
        # Timer for debouncing
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._perform_search)
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Set up the search widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.placeholder)
        self.search_input.setClearButtonEnabled(True)
        
        # Style the search input
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #ddd;
                border-radius: 20px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
                outline: none;
            }
            QLineEdit[text=""] {
                font-style: italic;
            }
        """)
        
        # Search button (optional - mainly for visual clarity)
        self.search_button = QPushButton("🔍")
        self.search_button.setFixedSize(32, 32)
        self.search_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 16px;
                background-color: #3498db;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        
        # Clear button
        self.clear_button = QPushButton("✕")
        self.clear_button.setFixedSize(24, 24)
        self.clear_button.setVisible(False)
        self.clear_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 12px;
                background-color: #95a5a6;
                color: white;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_button)
        layout.addWidget(self.clear_button)
        
        # Set up auto-completer (will be populated later)
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.search_input.setCompleter(self.completer)
        
    def _connect_signals(self):
        """Connect internal signals."""
        self.search_input.textChanged.connect(self._on_text_changed)
        self.search_input.returnPressed.connect(self._on_return_pressed)
        self.search_button.clicked.connect(self._on_search_clicked)
        self.clear_button.clicked.connect(self.clear_search)
        
    def _on_text_changed(self, text: str):
        """Handle text changes with debouncing."""
        # Show/hide clear button
        self.clear_button.setVisible(bool(text))
        
        # Stop any existing timer
        self.debounce_timer.stop()
        
        if text.strip():
            # Start debounce timer
            self.debounce_timer.start(self.debounce_delay)
        else:
            # Immediately clear if empty
            self._clear_search_results()
            
    def _on_return_pressed(self):
        """Handle return key press - immediate search."""
        self.debounce_timer.stop()
        self._perform_search()
        
    def _on_search_clicked(self):
        """Handle search button click."""
        self.debounce_timer.stop()
        self._perform_search()
        
    def _perform_search(self):
        """Perform the actual search."""
        search_term = self.search_input.text().strip()
        
        if not search_term:
            self._clear_search_results()
            return
            
        if search_term == self._last_search_term:
            # Same search term, don't repeat
            return
            
        self._last_search_term = search_term
        self.logger.debug(f"Performing search for: '{search_term}'")
        
        # Update UI to show searching state
        self._set_searching_state(True)
        
        # Emit search signal for immediate UI updates
        self.searchRequested.emit(search_term)
        
        # If background search function is set, also perform background search
        if self._search_function:
            worker = SearchWorker(
                search_term, 
                self._search_function, 
                self._on_background_search_complete
            )
            QThreadPool.globalInstance().start(worker)
    
    def _on_background_search_complete(self, search_term: str, results: list):
        """Handle completion of background search."""
        # Only process if this is still the current search
        if search_term == self._last_search_term:
            self.searchResultsReady.emit(search_term, results)
            
        self._set_searching_state(False)
        
    def _clear_search_results(self):
        """Clear search results."""
        self._last_search_term = ""
        self._set_searching_state(False)
        self.searchCleared.emit()
        
    def _set_searching_state(self, is_searching: bool):
        """Update UI to show searching state."""
        self._is_searching = is_searching
        
        if is_searching:
            self.search_button.setText("⏳")
            self.search_button.setEnabled(False)
        else:
            self.search_button.setText("🔍")
            self.search_button.setEnabled(True)
            
    def clear_search(self):
        """Clear the search input and results."""
        self.search_input.clear()
        self._clear_search_results()
        
    def set_search_function(self, search_func: Callable):
        """
        Set the function to call for background searches.
        
        Args:
            search_func: Function that takes a search term and returns results
        """
        self._search_function = search_func
        
    def set_suggestions(self, suggestions: List[str]):
        """
        Update auto-complete suggestions.
        
        Args:
            suggestions: List of suggestion strings
        """
        self._suggestions = suggestions
        model = QStringListModel(suggestions)
        self.completer.setModel(model)
        
    def add_suggestion(self, suggestion: str):
        """Add a single suggestion to auto-complete."""
        if suggestion not in self._suggestions:
            self._suggestions.append(suggestion)
            self.set_suggestions(self._suggestions)
            
    def get_search_term(self) -> str:
        """Get the current search term."""
        return self.search_input.text().strip()
        
    def set_search_term(self, term: str):
        """Set the search term programmatically."""
        self.search_input.setText(term)
        
    def is_searching(self) -> bool:
        """Check if a search is currently in progress."""
        return self._is_searching
        
    def set_placeholder(self, placeholder: str):
        """Update the placeholder text."""
        self.placeholder = placeholder
        self.search_input.setPlaceholderText(placeholder)
        
    def set_debounce_delay(self, delay_ms: int):
        """Update the debounce delay."""
        self.debounce_delay = delay_ms


class SearchResultsWidget(QWidget):
    """Widget to display search results with filtering and sorting options."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the search results UI."""
        layout = QVBoxLayout(self)
        
        # Results header
        self.results_header = QLabel()
        self.results_header.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                padding: 8px;
                background-color: #ecf0f1;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.results_header)
        
        # Results container (to be filled by parent)
        self.results_container = QFrame()
        layout.addWidget(self.results_container)
        
    def update_results_count(self, count: int, search_term: str = ""):
        """Update the results header with count information."""
        if count == 0:
            if search_term:
                text = f"No results found for '{search_term}'"
            else:
                text = "No results"
        else:
            if search_term:
                text = f"Found {count} result{'s' if count != 1 else ''} for '{search_term}'"
            else:
                text = f"Showing {count} result{'s' if count != 1 else ''}"
                
        self.results_header.setText(text)
        
    def get_results_container(self) -> QFrame:
        """Get the container widget for results."""
        return self.results_container


class DebouncedSearchEdit(QLineEdit):
    """
    Simple debounced search line edit widget.
    Lighter alternative to DebouncedSearchWidget for cases where you just need a search input.
    """
    
    # Signals
    searchChanged = Signal(str)  # Emitted when search term changes (debounced)
    
    def __init__(self, placeholder: str = "Search...", debounce_ms: int = 300, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        
        # Timer for debouncing
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._emit_search_changed)
        self.debounce_delay = debounce_ms
        
        # Connect text changed signal
        self.textChanged.connect(self._on_text_changed)
        self.returnPressed.connect(self._on_return_pressed)
        
        self._last_emitted_text = ""
        
    def _on_text_changed(self, text: str):
        """Handle text changes with debouncing."""
        # Stop any existing timer
        self.debounce_timer.stop()
        
        if text.strip() != self._last_emitted_text:
            # Start debounce timer
            self.debounce_timer.start(self.debounce_delay)
            
    def _on_return_pressed(self):
        """Handle return key press - immediate search."""
        self.debounce_timer.stop()
        self._emit_search_changed()
        
    def _emit_search_changed(self):
        """Emit the search changed signal."""
        current_text = self.text().strip()
        if current_text != self._last_emitted_text:
            self._last_emitted_text = current_text
            self.searchChanged.emit(current_text)
            
    def set_debounce_delay(self, delay_ms: int):
        """Update the debounce delay."""
        self.debounce_delay = delay_ms