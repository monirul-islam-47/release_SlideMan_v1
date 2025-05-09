import logging
from typing import Optional, Dict, List, Union
from PySide6.QtWidgets import QWidget, QListWidget, QListWidgetItem, QAbstractItemView
from PySide6.QtCore import Qt, QSize, QPoint, QRect, Signal
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen
from ...app_state import app_state
from ...services.thumbnail_cache import thumbnail_cache

logger = logging.getLogger(__name__)

class AssemblyPreviewWidget(QListWidget):
    """ListWidget-based assembly preview with improved drag-and-drop."""
    orderChanged = Signal(list)
    
    # Add default class attribute for KeywordId
    KeywordId = None

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setIconSize(QSize(160, 120))
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Snap)
        self.setFlow(QListWidget.Flow.LeftToRight)
        self.setWrapping(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)

        icon_width = self.iconSize().width()
        icon_height = self.iconSize().height()
        self.setGridSize(QSize(icon_width + 10, icon_height + 30))
        self.setSpacing(10)

        self._added_indices = set()
        self._drop_target_row = -1
        self._drop_indicator_rect = QRect()

    def add_slide(self, slide_id: int, thumbnail: QPixmap, keywords: Dict[str, Union[str, None]]):
        """Adds a slide thumbnail if not already present."""
        if slide_id in self._added_indices:
            return False
            
        # Ensure KeywordId is provided or use default
        if "KeywordId" not in keywords:
            keywords["KeywordId"] = self.KeywordId
            
        item = QListWidgetItem()
        item.setIcon(QIcon(thumbnail))
        item.setData(Qt.ItemDataRole.UserRole, slide_id)
        item.setText(str(slide_id))
        item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        
        # Store keywords as item data
        for key, value in keywords.items():
            role = Qt.ItemDataRole.UserRole + 100 + hash(key) % 100  # Create a unique role
            item.setData(role, value)
            
        self.addItem(item)
        self._added_indices.add(slide_id)
        return True

    def remove_selected_slides(self):
        """Remove selected items."""
        for item in self.selectedItems():
            slide_id = item.data(Qt.ItemDataRole.UserRole)
            row = self.row(item)
            self.takeItem(row)
            self._added_indices.discard(slide_id)

    def clear(self):
        """Remove all items and reset added indices."""
        super().clear()
        self._added_indices.clear()

    def get_ordered_slide_indices(self) -> List[int]:
        """Return current order of slide IDs."""
        return [self.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.count())]

    def dragEnterEvent(self, e):
        if e.source() == self:
            e.setDropAction(Qt.DropAction.MoveAction)
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.source() == self:
            pos = e.position().toPoint() if hasattr(e, 'position') else e.pos()
            self._drop_target_row = self._get_drop_index(pos)
            self._update_drop_indicator_rect(pos)
            self.viewport().update()
            e.setDropAction(Qt.DropAction.MoveAction)
            e.accept()
        else:
            self._drop_target_row = -1
            self._drop_indicator_rect = QRect()
            self.viewport().update()
            e.ignore()

    def dragLeaveEvent(self, e):
        self._drop_target_row = -1
        self._drop_indicator_rect = QRect()
        self.viewport().update()
        e.accept()

    def dropEvent(self, e):
        logger.debug("AssemblyPreviewWidget: dropEvent")
        current = self._drop_target_row
        self._drop_target_row = -1
        self._drop_indicator_rect = QRect()
        self.viewport().update()
        if e.source() != self:
            e.ignore()
            return
        items = self.selectedItems()
        if not items:
            e.ignore()
            return
        src = self.row(items[0])
        dragged = self.takeItem(src)
        target = current
        if src < target:
            target -= 1
        if src == target:
            self.insertItem(src, dragged)
            e.ignore()
            return
        self.insertItem(target, dragged)
        self.setCurrentItem(dragged)
        self.scrollToItem(dragged, QAbstractItemView.ScrollHint.PositionAtCenter)
        e.acceptProposedAction()
        order = self.get_ordered_slide_indices()
        self.orderChanged.emit(order)
        app_state.set_assembly_order(order)

    def _get_drop_index(self, pos: QPoint) -> int:
        count = self.count()
        if count == 0:
            return 0
            
        # Check if pos has a valid item
        item_at_pos = self.itemAt(pos)
        if item_at_pos:
            return self.row(item_at_pos)
            
        # If not, find the closest item
        min_dist, closest = float('inf'), count
        for i in range(count):
            item = self.item(i)
            if not item:
                continue
                
            rect = self.visualItemRect(item)
            if not rect.isValid():
                continue
                
            c = rect.center()
            d = (pos.x() - c.x())**2 + (pos.y() - c.y())**2
            if d < min_dist:
                min_dist, closest = d, i
                
        return closest

    def _update_drop_indicator_rect(self, pos: QPoint):
        if self._drop_target_row == -1:
            self._drop_indicator_rect = QRect()
        else:
            # Use QListWidget's way of getting visual rect - the item rect at index
            item = self.item(self._drop_target_row)
            if item:
                self._drop_indicator_rect = self.visualItemRect(item)
            else:
                self._drop_indicator_rect = QRect()

    def paintEvent(self, ev):
        super().paintEvent(ev)
        if not self._drop_indicator_rect.isNull():
            painter = QPainter(self.viewport())
            pen = QPen(Qt.GlobalColor.blue)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(self._drop_indicator_rect.adjusted(1, 1, -1, -1))
            painter.end()
