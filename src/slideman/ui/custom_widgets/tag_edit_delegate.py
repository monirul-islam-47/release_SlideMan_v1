# src/slideman/ui/custom_widgets/tag_edit_delegate.py

from PySide6.QtWidgets import QStyledItemDelegate, QWidget, QHBoxLayout, QVBoxLayout, QDialog, QPushButton
from PySide6.QtCore import Qt, Signal, QEvent, QSize
from PySide6.QtGui import QCursor

from ..components.tag_edit import TagEdit

class TagEditDialog(QDialog):
    """
    Dialog for editing tags directly from a table cell.
    """
    def __init__(self, parent=None, tags=None, tag_type="Tag"):
        super().__init__(parent)
        self.setWindowTitle(f"Edit {tag_type}s")
        self.setMinimumWidth(400)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Tag edit widget
        self.tag_edit = TagEdit(self)
        if tags:
            self.tag_edit.set_tags(tags)
        layout.addWidget(self.tag_edit)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Create buttons
        self.ok_button = QPushButton("Apply")
        self.cancel_button = QPushButton("Cancel")
        
        # Add buttons to layout
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        # Add button layout to main layout
        layout.addLayout(button_layout)
        
        # Connect signals
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
    def get_tags(self):
        """Get the current tags from the tag edit widget"""
        return self.tag_edit.get_tags()


class TagEditDelegate(QStyledItemDelegate):
    """
    Delegate for editing tags directly in the table.
    Displays a tag edit dialog when the user double-clicks a cell.
    """
    # Signal emitted when tags are edited
    tagsEdited = Signal(int, str, list)  # slide_id, tag_type, tags
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
        self._edit_column = -1  # Column this delegate is assigned to
        
    def set_edit_column(self, column):
        """Set which column this delegate is editing"""
        self._edit_column = column
        
    def createEditor(self, parent, option, index):
        """
        Create a tag edit dialog when the user edits a cell.
        """
        # Determine tag type based on column
        tag_type = self._get_tag_type(index.column())
        
        # Get current tags
        current_tags = []
        tag_text = index.data(Qt.ItemDataRole.DisplayRole)
        if tag_text:
            current_tags = [tag.strip() for tag in tag_text.split(',')]
        
        # Create and show dialog
        dialog = TagEditDialog(parent, current_tags, tag_type)
        return dialog
        
    def setEditorData(self, editor, index):
        """
        Set the editor data based on the model data.
        """
        # Already set in createEditor
        pass
        
    def setModelData(self, editor, model, index):
        """
        Update the model data when the user finishes editing.
        """
        if isinstance(editor, TagEditDialog):
            # Get the edited tags
            tags = editor.get_tags()
            
            # Get the slide ID
            slide_data = model.data(index, Qt.ItemDataRole.UserRole)
            if slide_data and 'slide_id' in slide_data:
                slide_id = slide_data['slide_id']
                
                # Determine tag type
                tag_type = self._get_tag_type(index.column())
                
                # Emit signal with slide ID, tag type, and the new tags
                self.tagsEdited.emit(slide_id, tag_type, tags)
                
    def updateEditorGeometry(self, editor, option, index):
        """
        Position the editor dialog near the edited cell.
        """
        # Position dialog relative to cursor
        cursor_pos = QCursor.pos()
        editor.move(cursor_pos.x() - 200, cursor_pos.y() - 50)
        
    def sizeHint(self, option, index):
        """
        Return the size hint for the cell.
        """
        return QSize(option.rect.width(), 60)  # Reasonable height for tag display
        
    def editorEvent(self, event, model, option, index):
        """
        Handle editor events (double-click).
        """
        if event.type() == QEvent.Type.MouseButtonDblClick:
            return False  # Let the default handler create the editor
            
        return super().editorEvent(event, model, option, index)
        
    def _get_tag_type(self, column):
        """Determine tag type based on column index"""
        if column == 2:  # Assuming column 2 is Topics
            return "Topic"
        elif column == 3:  # Assuming column 3 is Titles
            return "Title"
        else:
            return "Tag"
