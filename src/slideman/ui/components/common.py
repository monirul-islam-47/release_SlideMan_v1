"""Common UI components and mixins for consistent behavior across the application."""

import logging
from typing import Optional, Tuple

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QWidget, QLabel, QListView, QGroupBox, QVBoxLayout, 
    QHBoxLayout, QPushButton, QProgressBar
)

from ..components.tag_edit import TagEdit


logger = logging.getLogger(__name__)


class BusyStateMixin:
    """Mixin for consistent busy state management across UI components."""
    
    def set_ui_busy(self, is_busy: bool, message: str = ""):
        """Set the busy state of the UI with optional message.
        
        Args:
            is_busy: Whether the UI should be in busy state
            message: Optional message to display during busy state
        """
        if not isinstance(self, QWidget):
            raise TypeError("BusyStateMixin can only be used with QWidget subclasses")
            
        if is_busy:
            self.setCursor(QCursor(Qt.CursorShape.WaitCursor))
            # Disable main interactive elements
            for child in self.findChildren(QPushButton):
                child.setEnabled(False)
            for child in self.findChildren(QListView):
                child.setEnabled(False)
                
            # Update status message if available
            if hasattr(self, 'status_label') and message:
                self.status_label.setText(message)
            elif hasattr(self, 'statusBar') and callable(self.statusBar) and message:
                self.statusBar().showMessage(message)
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            # Re-enable interactive elements
            for child in self.findChildren(QPushButton):
                child.setEnabled(True)
            for child in self.findChildren(QListView):
                child.setEnabled(True)
                
            # Clear status message
            if hasattr(self, 'status_label'):
                self.status_label.clear()
            elif hasattr(self, 'statusBar') and callable(self.statusBar):
                self.statusBar().clearMessage()


def create_thumbnail_list_view(
    icon_size: Tuple[int, int] = (160, 120),
    uniform_item_sizes: bool = True,
    spacing: int = 10,
    resize_mode: QListView.ResizeMode = QListView.ResizeMode.Adjust
) -> QListView:
    """Factory function for creating consistent thumbnail list views.
    
    Args:
        icon_size: Size of icons as (width, height) tuple
        uniform_item_sizes: Whether all items should have uniform size
        spacing: Spacing between items
        resize_mode: How the view should resize items
        
    Returns:
        Configured QListView instance
    """
    view = QListView()
    view.setViewMode(QListView.ViewMode.IconMode)
    view.setIconSize(QSize(*icon_size))
    view.setResizeMode(resize_mode)
    view.setUniformItemSizes(uniform_item_sizes)
    view.setSpacing(spacing)
    view.setMovement(QListView.Movement.Static)
    view.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
    view.setWordWrap(True)
    view.setTextElideMode(Qt.TextElideMode.ElideRight)
    
    # Common style
    view.setStyleSheet("""
        QListView {
            background-color: palette(base);
            border: 1px solid palette(mid);
            border-radius: 4px;
        }
        QListView::item {
            padding: 5px;
        }
        QListView::item:selected {
            background-color: palette(highlight);
            color: palette(highlighted-text);
        }
    """)
    
    return view


def create_tag_edit_section(
    label_text: str, 
    kind: str,
    parent: Optional[QWidget] = None
) -> Tuple[QLabel, TagEdit]:
    """Factory function for creating consistent tag edit sections.
    
    Args:
        label_text: Text for the label
        kind: Kind identifier for the tag edit (used in object name)
        parent: Optional parent widget
        
    Returns:
        Tuple of (label, tag_edit) widgets
    """
    label = QLabel(label_text, parent)
    label.setStyleSheet("font-weight: bold; color: palette(text);")
    
    tag_edit = TagEdit(parent)
    tag_edit.setObjectName(f"{kind}_tag_edit")
    tag_edit.setPlaceholderText(f"Add {kind} tags...")
    
    return label, tag_edit


def create_tag_group_box(
    title: str,
    kind: str,
    parent: Optional[QWidget] = None,
    include_add_button: bool = False
) -> Tuple[QGroupBox, TagEdit, Optional[QPushButton]]:
    """Create a complete tag editing group box with optional add button.
    
    Args:
        title: Title for the group box
        kind: Kind identifier for the tag edit
        parent: Optional parent widget
        include_add_button: Whether to include an add button
        
    Returns:
        Tuple of (group_box, tag_edit, add_button or None)
    """
    group_box = QGroupBox(title, parent)
    layout = QVBoxLayout(group_box)
    
    # Create tag edit
    tag_edit = TagEdit(group_box)
    tag_edit.setObjectName(f"{kind}_tag_edit")
    tag_edit.setPlaceholderText(f"Add {kind} tags...")
    
    if include_add_button:
        # Horizontal layout for tag edit and button
        h_layout = QHBoxLayout()
        h_layout.addWidget(tag_edit, 1)
        
        add_button = QPushButton("Add", group_box)
        add_button.setObjectName(f"{kind}_add_button")
        add_button.setMaximumWidth(60)
        h_layout.addWidget(add_button)
        
        layout.addLayout(h_layout)
        return group_box, tag_edit, add_button
    else:
        layout.addWidget(tag_edit)
        return group_box, tag_edit, None


def create_progress_widget(parent: Optional[QWidget] = None) -> Tuple[QWidget, QProgressBar, QLabel]:
    """Create a standard progress widget with progress bar and label.
    
    Args:
        parent: Optional parent widget
        
    Returns:
        Tuple of (container_widget, progress_bar, status_label)
    """
    container = QWidget(parent)
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    
    # Status label
    status_label = QLabel(container)
    status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(status_label)
    
    # Progress bar
    progress_bar = QProgressBar(container)
    progress_bar.setTextVisible(True)
    progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(progress_bar)
    
    # Initially hidden
    container.setVisible(False)
    
    return container, progress_bar, status_label


class ErrorHandlingMixin:
    """Mixin for consistent error handling and display in UI components."""
    
    def handle_error(self, error: Exception, title: str = "Error", 
                    operation: str = "operation", show_dialog: bool = True):
        """Handle an error with logging and optional user notification.
        
        Args:
            error: The exception that occurred
            title: Title for the error dialog
            operation: Description of the operation that failed
            show_dialog: Whether to show an error dialog to the user
        """
        logger.error(f"Error during {operation}: {error}", exc_info=True)
        
        if show_dialog and hasattr(self, 'show_error'):
            # Use the view's show_error method if available
            self.show_error(title, f"Failed to {operation}:\n{str(error)}")
        elif show_dialog:
            # Fallback to QMessageBox if no show_error method
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self if isinstance(self, QWidget) else None, 
                               title, f"Failed to {operation}:\n{str(error)}")