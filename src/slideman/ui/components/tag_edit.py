# src/slideman/ui/components/tag_edit.py

import logging
from typing import List, Set

from PySide6.QtCore import Qt, Signal, QSize, QStringListModel, QRect, QPoint
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QCompleter, 
    QPushButton, QScrollArea, QFrame, QSizePolicy, QLayout
)

logger = logging.getLogger(__name__)

class TagPill(QPushButton):
    """
    A styled button representing a single tag/keyword in the TagEdit widget.
    """
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #3584e4;
                color: white;
                border-radius: 10px;
                padding: 3px 8px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #5294e2;
            }
        """)
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Make the remove "X" part of the text
        self.setText(f"{text} ✕")
        
        # Set a reasonable size policy
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
    def get_tag_text(self) -> str:
        """Returns the tag text without the remove symbol."""
        text = self.text()
        return text.rstrip(" ✕")

class FlowLayout(QLayout):
    """
    Custom layout that arranges widgets in a flow, similar to how text 
    wraps in a paragraph. Adapted from Qt examples.
    """
    def __init__(self, parent=None, margin: int = 0, spacing: int = -1):
        super().__init__(parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self._items = []
        
    def __del__(self):
        while self._items:
            self.takeAt(0)
            
    def addItem(self, item):
        self._items.append(item)
        
    def count(self):
        return len(self._items)
        
    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None
        
    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None
        
    def expandingDirections(self):
        return Qt.Orientation.Horizontal
        
    def hasHeightForWidth(self):
        return True
        
    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)
        
    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)
        
    def sizeHint(self):
        return self.minimumSize()
        
    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins().left()
        size += QSize(2 * margin, 2 * margin)
        return size
        
    def _do_layout(self, rect, test_only=False):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()
        
        for item in self._items:
            widget = item.widget()
            style = widget.style() if widget else None
            
            # Layout with horizontal spacing
            next_x = x + item.sizeHint().width() + spacing
            if next_x - spacing > rect.right() and line_height > 0:
                # Wrap to next line
                x = rect.x()
                y = y + line_height + spacing
                next_x = x + item.sizeHint().width() + spacing
                line_height = 0
                
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
                
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
            
        return y + line_height - rect.y()

class TagEdit(QWidget):
    """
    Reusable widget for displaying and editing a collection of tags/keywords.
    Features:
    - Tag display as clickable pills
    - Input field with autocompletion
    - Add/remove tag functionality
    """
    # Signals
    tagAdded = Signal(str)      # Emitted when a tag is added
    tagRemoved = Signal(str)    # Emitted when a tag is removed
    
    def __init__(self, parent=None, placeholder_text: str = "Add tag..."):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initializing TagEdit widget")
        
        # Keep track of current tags (for quick duplicate checking)
        self._tags: Set[str] = set()
        
        # Main layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(5)
        
        # Create scrollable area for tags
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create container widget for tags with flow layout
        self._tags_container = QWidget()
        self._flow_layout = FlowLayout(self._tags_container, margin=0, spacing=5)
        self._tags_container.setLayout(self._flow_layout)
        
        # Add container to scroll area
        self._scroll_area.setWidget(self._tags_container)
        
        # Create input field for new tags
        self._input = QLineEdit()
        self._input.setPlaceholderText(placeholder_text)
        
        # Setup autocomplete
        self._completer_model = QStringListModel()
        self._completer = QCompleter()
        self._completer.setModel(self._completer_model)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._input.setCompleter(self._completer)
        
        # Add widgets to main layout
        self._main_layout.addWidget(self._scroll_area)
        self._main_layout.addWidget(self._input)
        
        # Connect signals
        self._input.returnPressed.connect(self._handle_input_return)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Set minimum height to show at least 2-3 rows of tags
        self._scroll_area.setMinimumHeight(80)
        
        self.logger.debug("TagEdit widget initialized")
        
    def _handle_input_return(self):
        """Handle Enter key press in the input field."""
        tag_text = self._input.text().strip()
        if tag_text:
            self.add_tag(tag_text)
            
    def _handle_tag_clicked(self):
        """Handle click on a tag pill button (remove the tag)."""
        sender = self.sender()
        if isinstance(sender, TagPill):
            tag_text = sender.get_tag_text()
            self.remove_tag(tag_text)
    
    def set_tags(self, tags: List[str]):
        """
        Set the displayed tags to match the provided list.
        
        Args:
            tags: List of tag strings to display
        """
        self.clear()
        for tag in tags:
            self.add_tag(tag, emit_signal=False)
            
    def get_tags(self) -> List[str]:
        """
        Get the currently displayed tags.
        
        Returns:
            List of tag strings
        """
        return list(self._tags)
    
    def add_tag(self, tag_text: str, emit_signal: bool = True):
        """
        Add a new tag if it doesn't already exist.
        
        Args:
            tag_text: The tag text to add
            emit_signal: Whether to emit the tagAdded signal
        
        Returns:
            True if tag was added, False if it was a duplicate
        """
        tag_text = tag_text.strip()
        if not tag_text:
            return False
            
        # Check for duplicates (case-insensitive)
        lower_tag = tag_text.lower()
        if any(t.lower() == lower_tag for t in self._tags):
            self.logger.debug(f"Tag '{tag_text}' not added - duplicate")
            return False
            
        # Create tag pill button
        tag_pill = TagPill(tag_text)
        tag_pill.clicked.connect(self._handle_tag_clicked)
        
        # Add to flow layout
        self._flow_layout.addWidget(tag_pill)
        
        # Add to internal set
        self._tags.add(tag_text)
        
        # Clear input field
        self._input.clear()
        
        # Emit signal if requested
        if emit_signal:
            self.tagAdded.emit(tag_text)
            
        self.logger.debug(f"Added tag: '{tag_text}'")
        return True
    
    def remove_tag(self, tag_text: str, emit_signal: bool = True):
        """
        Remove a tag from the display.
        
        Args:
            tag_text: The tag text to remove
            emit_signal: Whether to emit the tagRemoved signal
        
        Returns:
            True if tag was found and removed, False otherwise
        """
        # Find the tag pill widget
        for i in range(self._flow_layout.count()):
            item = self._flow_layout.itemAt(i)
            if item is None:
                continue
                
            widget = item.widget()
            if isinstance(widget, TagPill) and widget.get_tag_text() == tag_text:
                # Remove from layout
                self._flow_layout.takeAt(i)
                widget.deleteLater()
                
                # Remove from internal set
                self._tags.discard(tag_text)
                
                # Emit signal if requested
                if emit_signal:
                    self.tagRemoved.emit(tag_text)
                    
                self.logger.debug(f"Removed tag: '{tag_text}'")
                return True
                
        self.logger.debug(f"Tag '{tag_text}' not found for removal")
        return False
    
    def update_suggestions(self, suggestions: List[str]):
        """
        Update the autocompletion suggestions.
        
        Args:
            suggestions: List of suggestion strings
        """
        self._completer_model.setStringList(suggestions)
        self.logger.debug(f"Updated {len(suggestions)} tag suggestions")
    
    def clear(self):
        """Clear all tags."""
        # Remove all tags from the layout
        while self._flow_layout.count():
            item = self._flow_layout.takeAt(0)
            if item is None:
                continue
            
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Clear internal set
        self._tags.clear()
        self.logger.debug("Cleared all tags")
