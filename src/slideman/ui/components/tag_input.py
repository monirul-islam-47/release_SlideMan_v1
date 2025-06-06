# src/slideman/ui/components/tag_input.py

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, 
                               QCompleter, QLabel, QPushButton, QFrame, QFlowLayout,
                               QSizePolicy, QApplication)
from PySide6.QtCore import Qt, Signal, QStringListModel, QTimer, QRect
from PySide6.QtGui import QFont, QPalette, QColor, QKeySequence
import logging
from typing import List, Set, Optional

class QFlowLayout(QHBoxLayout):
    """A simple flow layout implementation for tag badges."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)


class TagBadge(QWidget):
    """A visual tag badge with delete functionality."""
    
    tagRemoved = Signal(str)  # Emitted when tag is removed
    
    def __init__(self, tag_text: str, removable: bool = True, parent=None):
        super().__init__(parent)
        self.tag_text = tag_text
        self.removable = removable
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the tag badge UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # Tag text label
        self.label = QLabel(self.tag_text)
        self.label.setStyleSheet("color: white; font-weight: bold; font-size: 11px;")
        layout.addWidget(self.label)
        
        # Remove button (if removable)
        if self.removable:
            self.remove_btn = QPushButton("×")
            self.remove_btn.setFixedSize(16, 16)
            self.remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.3);
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-weight: bold;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.5);
                }
            """)
            self.remove_btn.clicked.connect(lambda: self.tagRemoved.emit(self.tag_text))
            layout.addWidget(self.remove_btn)
        
        # Style the badge
        self.setStyleSheet("""
            TagBadge {
                background-color: #3498db;
                border-radius: 12px;
                margin: 2px;
            }
        """)
        
        # Set fixed height
        self.setFixedHeight(24)
        
    def get_tag_text(self) -> str:
        """Get the tag text."""
        return self.tag_text


class SmartTagCompleter(QCompleter):
    """Enhanced completer for tag input with better filtering and suggestions."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterMode(Qt.MatchContains)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.setMaxVisibleItems(10)
        
        # Custom styling
        popup = self.popup()
        if popup:
            popup.setStyleSheet("""
                QListView {
                    border: 1px solid #3498db;
                    border-radius: 4px;
                    background-color: white;
                    selection-background-color: #3498db;
                    selection-color: white;
                    padding: 2px;
                }
                QListView::item {
                    padding: 6px 8px;
                    border: none;
                }
                QListView::item:hover {
                    background-color: #ecf0f1;
                }
            """)
            
    def splitPath(self, path: str) -> List[str]:
        """Override to handle comma-separated tags."""
        # Split by comma and return the last part for completion
        parts = [part.strip() for part in path.split(',')]
        return [parts[-1]] if parts else ['']
        
    def pathFromIndex(self, index):
        """Override to handle comma-separated insertion."""
        # Get the current text
        current_text = self.widget().text() if self.widget() else ""
        parts = [part.strip() for part in current_text.split(',')]
        
        # Replace the last part with the selected completion
        if parts:
            parts[-1] = self.model().data(index, Qt.DisplayRole)
        else:
            parts = [self.model().data(index, Qt.DisplayRole)]
            
        return ', '.join(parts)


class TagInputWidget(QWidget):
    """
    Advanced tag input widget with auto-complete, suggestions, and validation.
    """
    
    # Signals
    tagsChanged = Signal(list)       # Emitted when tag list changes
    tagAdded = Signal(str)           # Emitted when a tag is added
    tagRemoved = Signal(str)         # Emitted when a tag is removed
    newTagRequested = Signal(str)    # Emitted when user wants to create new tag
    
    def __init__(self, placeholder: str = "Add tags...", parent=None):
        super().__init__(parent)
        self.placeholder = placeholder
        self.logger = logging.getLogger(__name__)
        
        # State
        self._tags: Set[str] = set()
        self._suggestions: List[str] = []
        self._max_tags: Optional[int] = None
        self._allow_duplicates = False
        self._allow_new_tags = True
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Set up the tag input UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # Input container
        input_container = QFrame()
        input_container.setStyleSheet("""
            QFrame {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
                padding: 4px;
            }
            QFrame:focus-within {
                border-color: #3498db;
            }
        """)
        
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(8)
        
        # Tags container
        self.tags_container = QWidget()
        self.tags_layout = QFlowLayout(self.tags_container)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.addWidget(self.tags_container)
        
        # Input field
        input_row = QHBoxLayout()
        
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText(self.placeholder)
        self.tag_input.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 14px;
                padding: 4px;
            }
        """)
        
        # Add button
        self.add_button = QPushButton("Add")
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.add_button.setEnabled(False)
        
        input_row.addWidget(self.tag_input)
        input_row.addWidget(self.add_button)
        input_layout.addLayout(input_row)
        
        main_layout.addWidget(input_container)
        
        # Set up completer
        self.completer = SmartTagCompleter(self)
        self.tag_input.setCompleter(self.completer)
        
        # Suggestions label
        self.suggestions_label = QLabel()
        self.suggestions_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 11px;
                font-style: italic;
                padding: 4px;
            }
        """)
        self.suggestions_label.hide()
        main_layout.addWidget(self.suggestions_label)
        
    def _connect_signals(self):
        """Connect internal signals."""
        self.tag_input.textChanged.connect(self._on_text_changed)
        self.tag_input.returnPressed.connect(self._add_current_tag)
        self.add_button.clicked.connect(self._add_current_tag)
        self.completer.activated.connect(self._on_completion_selected)
        
    def _on_text_changed(self, text: str):
        """Handle text changes in the input field."""
        # Enable/disable add button
        self.add_button.setEnabled(bool(text.strip()))
        
        # Show suggestions if available
        self._update_suggestions_display(text.strip())
        
    def _on_completion_selected(self, completion: str):
        """Handle completion selection."""
        # Auto-add the completed tag after a short delay
        QTimer.singleShot(100, self._add_current_tag)
        
    def _add_current_tag(self):
        """Add the current input as a tag."""
        tag_text = self.tag_input.text().strip()
        
        if not tag_text:
            return
            
        # Handle comma-separated tags
        new_tags = [tag.strip() for tag in tag_text.split(',') if tag.strip()]
        
        for tag in new_tags:
            self._add_tag(tag)
            
        # Clear input
        self.tag_input.clear()
        self.add_button.setEnabled(False)
        
    def _add_tag(self, tag_text: str):
        """Add a single tag."""
        # Validate tag
        if not self._validate_tag(tag_text):
            return
            
        # Check if tag already exists
        if not self._allow_duplicates and tag_text in self._tags:
            self.logger.debug(f"Tag '{tag_text}' already exists")
            return
            
        # Check max tags limit
        if self._max_tags and len(self._tags) >= self._max_tags:
            self.logger.warning(f"Maximum tag limit ({self._max_tags}) reached")
            return
            
        # Check if tag exists in suggestions (for new tag handling)
        if tag_text not in self._suggestions and self._allow_new_tags:
            self.newTagRequested.emit(tag_text)
            
        # Add tag
        self._tags.add(tag_text)
        self._create_tag_badge(tag_text)
        
        # Emit signals
        self.tagAdded.emit(tag_text)
        self.tagsChanged.emit(list(self._tags))
        
        self.logger.debug(f"Added tag: '{tag_text}'")
        
    def _create_tag_badge(self, tag_text: str):
        """Create and add a tag badge to the UI."""
        badge = TagBadge(tag_text, removable=True)
        badge.tagRemoved.connect(self._remove_tag)
        self.tags_layout.addWidget(badge)
        
    def _remove_tag(self, tag_text: str):
        """Remove a tag."""
        if tag_text in self._tags:
            self._tags.remove(tag_text)
            
            # Remove badge from UI
            for i in range(self.tags_layout.count()):
                item = self.tags_layout.itemAt(i)
                if item and item.widget():
                    badge = item.widget()
                    if isinstance(badge, TagBadge) and badge.get_tag_text() == tag_text:
                        badge.deleteLater()
                        break
            
            # Emit signals
            self.tagRemoved.emit(tag_text)
            self.tagsChanged.emit(list(self._tags))
            
            self.logger.debug(f"Removed tag: '{tag_text}'")
            
    def _validate_tag(self, tag_text: str) -> bool:
        """Validate a tag before adding."""
        # Basic validation
        if not tag_text or len(tag_text.strip()) == 0:
            return False
            
        # Length check
        if len(tag_text) > 50:  # Reasonable tag length limit
            return False
            
        # Character validation (allow alphanumeric, spaces, hyphens, underscores)
        if not all(c.isalnum() or c in ' -_' for c in tag_text):
            return False
            
        return True
        
    def _update_suggestions_display(self, current_text: str):
        """Update the suggestions display."""
        if not current_text or not self._suggestions:
            self.suggestions_label.hide()
            return
            
        # Find matching suggestions
        matches = [s for s in self._suggestions 
                  if current_text.lower() in s.lower() and s not in self._tags]
        
        if matches:
            # Show top 5 suggestions
            display_matches = matches[:5]
            suggestion_text = f"Suggestions: {', '.join(display_matches)}"
            if len(matches) > 5:
                suggestion_text += f" and {len(matches) - 5} more..."
            self.suggestions_label.setText(suggestion_text)
            self.suggestions_label.show()
        else:
            self.suggestions_label.hide()
            
    # Public API methods
    
    def set_tags(self, tags: List[str]):
        """Set the current tags."""
        # Clear existing tags
        self.clear_tags()
        
        # Add new tags
        for tag in tags:
            self._add_tag(tag)
            
    def get_tags(self) -> List[str]:
        """Get the current tags as a list."""
        return list(self._tags)
        
    def clear_tags(self):
        """Remove all tags."""
        # Clear the set
        self._tags.clear()
        
        # Remove all badge widgets
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
                
        # Emit signal
        self.tagsChanged.emit([])
        
    def set_suggestions(self, suggestions: List[str]):
        """Set auto-complete suggestions."""
        self._suggestions = suggestions
        model = QStringListModel(suggestions)
        self.completer.setModel(model)
        
    def add_suggestion(self, suggestion: str):
        """Add a single suggestion."""
        if suggestion not in self._suggestions:
            self._suggestions.append(suggestion)
            self.set_suggestions(self._suggestions)
            
    def set_max_tags(self, max_tags: Optional[int]):
        """Set maximum number of tags allowed."""
        self._max_tags = max_tags
        
    def set_allow_duplicates(self, allow: bool):
        """Set whether duplicate tags are allowed."""
        self._allow_duplicates = allow
        
    def set_allow_new_tags(self, allow: bool):
        """Set whether new tags can be created."""
        self._allow_new_tags = allow
        
    def focus_input(self):
        """Focus the tag input field."""
        self.tag_input.setFocus()
        
    def has_tags(self) -> bool:
        """Check if any tags are present."""
        return len(self._tags) > 0