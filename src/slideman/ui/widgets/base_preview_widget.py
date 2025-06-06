"""Base preview widget for slide thumbnails with drag-and-drop support."""

import logging
from typing import Optional, Dict, List, Union, Set
from PySide6.QtWidgets import QWidget, QListWidget, QListWidgetItem, QAbstractItemView
from PySide6.QtCore import Qt, QSize, QPoint, QRect, Signal
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen

logger = logging.getLogger(__name__)


class BasePreviewWidget(QListWidget):
    """Base class for slide preview widgets with drag-and-drop functionality."""
    
    orderChanged = Signal(list)
    
    def __init__(
        self, 
        parent: Optional[QWidget] = None,
        icon_size: tuple[int, int] = (160, 120),
        grid_padding: tuple[int, int] = (10, 30),
        spacing: int = 10
    ):
        """Initialize the base preview widget.
        
        Args:
            parent: Parent widget
            icon_size: Size of thumbnails as (width, height)
            grid_padding: Additional padding for grid as (horizontal, vertical)
            spacing: Spacing between items
        """
        super().__init__(parent)
        
        # Configure view mode and icons
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setIconSize(QSize(*icon_size))
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Snap)
        self.setFlow(QListWidget.Flow.LeftToRight)
        self.setWrapping(True)
        
        # Selection and drag-drop
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)
        
        # Grid size configuration
        icon_width, icon_height = icon_size
        pad_h, pad_v = grid_padding
        self.setGridSize(QSize(icon_width + pad_h, icon_height + pad_v))
        self.setSpacing(spacing)
        
        # Internal state
        self._added_indices: Set[int] = set()
        self._drop_target_row: int = -1
        self._drop_indicator_rect: QRect = QRect()
        
        # Default keyword ID (can be overridden by subclasses)
        self.KeywordId: Optional[int] = None
    
    def add_slide(
        self, 
        slide_id: int, 
        thumbnail: QPixmap, 
        keywords: Dict[str, Union[str, None]]
    ) -> bool:
        """Add a slide thumbnail if not already present.
        
        Args:
            slide_id: Unique identifier for the slide
            thumbnail: Thumbnail pixmap to display
            keywords: Additional data to store with the item
            
        Returns:
            True if slide was added, False if already present
        """
        if slide_id in self._added_indices:
            return False
            
        # Ensure KeywordId is provided or use default
        if "KeywordId" not in keywords:
            keywords["KeywordId"] = self.KeywordId
            
        # Create list item
        item = QListWidgetItem()
        item.setIcon(QIcon(thumbnail))
        item.setData(Qt.ItemDataRole.UserRole, slide_id)
        item.setText(str(slide_id))
        item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        
        # Store keywords as item data
        for key, value in keywords.items():
            role = Qt.ItemDataRole.UserRole + 100 + hash(key) % 100
            item.setData(role, value)
            
        self.addItem(item)
        self._added_indices.add(slide_id)
        
        # Emit signal for subclasses to handle
        self._on_slide_added(slide_id, item)
        
        return True
    
    def remove_slide(self, slide_id: int) -> bool:
        """Remove a specific slide by ID.
        
        Args:
            slide_id: ID of slide to remove
            
        Returns:
            True if slide was removed, False if not found
        """
        for i in range(self.count()):
            item = self.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == slide_id:
                self.takeItem(i)
                self._added_indices.discard(slide_id)
                self._on_slide_removed(slide_id)
                return True
        return False
    
    def remove_selected_slides(self):
        """Remove all selected slides."""
        for item in self.selectedItems():
            slide_id = item.data(Qt.ItemDataRole.UserRole)
            row = self.row(item)
            self.takeItem(row)
            self._added_indices.discard(slide_id)
            self._on_slide_removed(slide_id)
    
    def clear(self):
        """Remove all items and reset state."""
        super().clear()
        self._added_indices.clear()
        self._on_cleared()
    
    def get_ordered_slide_indices(self) -> List[int]:
        """Return current order of slide IDs."""
        return [
            self.item(i).data(Qt.ItemDataRole.UserRole) 
            for i in range(self.count())
        ]
    
    def get_ordered_slides(self) -> List[QListWidgetItem]:
        """Return current slides in order."""
        return [self.item(i) for i in range(self.count())]
    
    # Drag and drop handling
    def dragEnterEvent(self, event):
        """Handle drag enter events."""
        if event.source() == self:
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move events with visual feedback."""
        if event.source() == self:
            pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
            self._drop_target_row = self._get_drop_index(pos)
            self._update_drop_indicator_rect(pos)
            self.viewport().update()
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            self._drop_target_row = -1
            self._drop_indicator_rect = QRect()
            self.viewport().update()
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave events."""
        self._drop_target_row = -1
        self._drop_indicator_rect = QRect()
        self.viewport().update()
        event.accept()
    
    def dropEvent(self, event):
        """Handle drop events with reordering."""
        logger.debug(f"{self.__class__.__name__}: dropEvent")
        
        current = self._drop_target_row
        self._drop_target_row = -1
        self._drop_indicator_rect = QRect()
        self.viewport().update()
        
        if event.source() != self:
            event.ignore()
            return
            
        items = self.selectedItems()
        if not items:
            event.ignore()
            return
            
        # Perform the move
        src = self.row(items[0])
        dragged = self.takeItem(src)
        target = current
        
        if src < target:
            target -= 1
            
        if src == target:
            self.insertItem(src, dragged)
            event.ignore()
            return
            
        self.insertItem(target, dragged)
        self.setCurrentItem(dragged)
        self.scrollToItem(dragged, QAbstractItemView.ScrollHint.PositionAtCenter)
        event.acceptProposedAction()
        
        # Notify about order change
        order = self.get_ordered_slide_indices()
        self.orderChanged.emit(order)
        self._on_order_changed(order)
    
    def paintEvent(self, event):
        """Paint event with drop indicator."""
        super().paintEvent(event)
        
        if not self._drop_indicator_rect.isNull():
            painter = QPainter(self.viewport())
            pen = QPen(Qt.GlobalColor.blue)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(self._drop_indicator_rect.adjusted(1, 1, -1, -1))
            painter.end()
    
    # Protected methods for subclasses to override
    def _on_slide_added(self, slide_id: int, item: QListWidgetItem):
        """Called when a slide is added. Override in subclasses."""
        pass
    
    def _on_slide_removed(self, slide_id: int):
        """Called when a slide is removed. Override in subclasses."""
        pass
    
    def _on_cleared(self):
        """Called when widget is cleared. Override in subclasses."""
        pass
    
    def _on_order_changed(self, order: List[int]):
        """Called when slide order changes. Override in subclasses."""
        pass
    
    # Private helper methods
    def _get_drop_index(self, pos: QPoint) -> int:
        """Get the index where a drop would occur at the given position."""
        count = self.count()
        if count == 0:
            return 0
            
        # Check if pos has a valid item
        item_at_pos = self.itemAt(pos)
        if item_at_pos:
            return self.row(item_at_pos)
            
        # If not, find the closest item
        min_dist = float('inf')
        closest = count
        
        for i in range(count):
            item = self.item(i)
            if not item:
                continue
                
            rect = self.visualItemRect(item)
            if not rect.isValid():
                continue
                
            center = rect.center()
            dist = (pos.x() - center.x())**2 + (pos.y() - center.y())**2
            
            if dist < min_dist:
                min_dist = dist
                closest = i
                
        return closest
    
    def _update_drop_indicator_rect(self, pos: QPoint):
        """Update the drop indicator rectangle."""
        if self._drop_target_row == -1:
            self._drop_indicator_rect = QRect()
        else:
            item = self.item(self._drop_target_row)
            if item:
                self._drop_indicator_rect = self.visualItemRect(item)
            else:
                self._drop_indicator_rect = QRect()