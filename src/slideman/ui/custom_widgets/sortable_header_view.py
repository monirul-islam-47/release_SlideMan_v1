# src/slideman/ui/custom_widgets/sortable_header_view.py

from PySide6.QtWidgets import QHeaderView
from PySide6.QtCore import Qt, Signal, QPoint, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QIcon

class SortableHeaderView(QHeaderView):
    """
    Enhanced header view that displays clear sort indicators and filter buttons.
    """
    # Signal emitted when a filter button is clicked
    filterClicked = Signal(int)  # Emits the column index
    
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        
        # Enable section movement
        self.setSectionsMovable(True)
        
        # Enable clickable sections for sorting
        self.setSectionsClickable(True)
        
        # Keep track of the current sort column and order
        self._sort_column = -1  # No column sorted initially
        self._sort_order = Qt.SortOrder.AscendingOrder
        
        # Keep track of filter states
        self._filtered_columns = set()
        
        # Set section resize mode
        self.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # Allow context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
    def paintSection(self, painter, rect, logicalIndex):
        """
        Custom paint method to add sort indicators and filter buttons
        """
        # Call the base implementation first
        super().paintSection(painter, rect, logicalIndex)
        
        # Only draw extras if the section is valid
        if rect.isValid():
            # Save painter state
            painter.save()
            
            # Get text alignment from base style
            text_alignment = self.defaultAlignment()
            
            # Get section text
            text = self.model().headerData(logicalIndex, self.orientation())
            if text is None:
                text = ""
                
            # Calculate text rect (need to leave space for indicators)
            indicator_width = 20
            text_rect = QRect(rect)
            if self.orientation() == Qt.Orientation.Horizontal:
                text_rect.setWidth(rect.width() - indicator_width)
            
            # Set up font
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            
            # Draw section text with adjustment for indicators
            painter.drawText(text_rect, text_alignment, text)
            
            # Draw sort indicator if this is the sort column
            if logicalIndex == self._sort_column:
                # Calculate indicator rect
                indicator_rect = QRect(
                    rect.right() - indicator_width,
                    rect.top() + (rect.height() - indicator_width) // 2,
                    indicator_width,
                    indicator_width
                )
                
                # Set up painter for indicator
                painter.setPen(QPen(QColor(0, 0, 0)))
                
                # Draw appropriate arrow based on sort order
                if self._sort_order == Qt.SortOrder.AscendingOrder:
                    # Draw up arrow
                    points = [
                        QPoint(indicator_rect.left() + indicator_rect.width() // 2, indicator_rect.top()),
                        QPoint(indicator_rect.left(), indicator_rect.bottom()),
                        QPoint(indicator_rect.right(), indicator_rect.bottom())
                    ]
                    painter.setBrush(QBrush(QColor(0, 0, 0)))
                    painter.drawPolygon(points)
                else:
                    # Draw down arrow
                    points = [
                        QPoint(indicator_rect.left() + indicator_rect.width() // 2, indicator_rect.bottom()),
                        QPoint(indicator_rect.left(), indicator_rect.top()),
                        QPoint(indicator_rect.right(), indicator_rect.top())
                    ]
                    painter.setBrush(QBrush(QColor(0, 0, 0)))
                    painter.drawPolygon(points)
            
            # Draw filter indicator if this column has a filter applied
            if logicalIndex in self._filtered_columns:
                # Calculate filter indicator rect
                filter_rect = QRect(
                    rect.right() - indicator_width - (20 if logicalIndex == self._sort_column else 0),
                    rect.top() + (rect.height() - indicator_width) // 2,
                    indicator_width,
                    indicator_width
                )
                
                # Draw a funnel icon to indicate filter
                painter.setPen(QPen(QColor(0, 0, 200)))
                painter.setBrush(QBrush(QColor(200, 200, 255)))
                
                # Draw a simple funnel shape
                points = [
                    QPoint(filter_rect.left(), filter_rect.top()),
                    QPoint(filter_rect.right(), filter_rect.top()),
                    QPoint(filter_rect.left() + filter_rect.width() * 3 // 4, filter_rect.bottom() - filter_rect.height() // 3),
                    QPoint(filter_rect.left() + filter_rect.width() * 3 // 4, filter_rect.bottom()),
                    QPoint(filter_rect.left() + filter_rect.width() // 4, filter_rect.bottom()),
                    QPoint(filter_rect.left() + filter_rect.width() // 4, filter_rect.bottom() - filter_rect.height() // 3)
                ]
                painter.drawPolygon(points)
            
            # Restore painter state
            painter.restore()
            
    def mousePressEvent(self, event):
        """
        Handle mouse press events to support filter button clicks
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # Get section at click position
            index = self.logicalIndexAt(event.position().toPoint())
            
            # Check if click is in the filter button area
            section_rect = self.sectionViewportPosition(index)
            filter_button_rect = QRect(
                section_rect + self.sectionSize(index) - 20,
                0,
                20,
                self.height()
            )
            
            if filter_button_rect.contains(event.position().toPoint()):
                # Toggle filter state for this column
                if index in self._filtered_columns:
                    self._filtered_columns.remove(index)
                else:
                    self._filtered_columns.add(index)
                    
                # Emit signal
                self.filterClicked.emit(index)
                
                # Redraw header
                self.viewport().update()
                return
        
        # Let base class handle other clicks
        super().mousePressEvent(event)
        
    def setSortIndicator(self, column, order):
        """
        Set which column should display a sort indicator and the sort order
        """
        self._sort_column = column
        self._sort_order = order
        self.viewport().update()  # Redraw header
        
    def setFilterIndicator(self, column, filtered=True):
        """
        Set whether a column should display a filter indicator
        """
        if filtered:
            self._filtered_columns.add(column)
        else:
            if column in self._filtered_columns:
                self._filtered_columns.remove(column)
                
        self.viewport().update()  # Redraw header
