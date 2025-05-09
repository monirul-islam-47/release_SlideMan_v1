# src/slideman/ui/custom_widgets/tag_badge_item_delegate.py

from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont
from PySide6.QtCore import Qt, QRectF, QPoint, QSize

class TagBadgeItemDelegate(QStyledItemDelegate):
    """
    Custom delegate for drawing tags as colorful badges in a table view.
    Used to display topic and title tags in the Keyword Manager page.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Define colors for different tag types
        self.topic_color = QColor(53, 132, 228)  # Blue
        self.title_color = QColor(153, 193, 241)  # Light Blue
        self.name_color = QColor(38, 162, 105)    # Green
        self.text_color = QColor(255, 255, 255)   # White
        
        # Default colors if tag type unknown
        self.default_color = QColor(108, 108, 108)  # Gray
        
        # Maximum number of tags to display before showing "+X more"
        self.max_visible_tags = 5
        
    def paint(self, painter, option, index):
        """
        Paint the tag badges in the table cell.
        Handles text as a list of comma-separated tags.
        """
        # Get tag text from model data
        tag_text = index.data(Qt.ItemDataRole.DisplayRole)
        if not tag_text:
            # Draw nothing for empty cells
            return
            
        # Determine if this is a "topic", "title", or "name" column based on column index
        column = index.column()
        
        # Split the text into individual tags
        tags = [tag.strip() for tag in tag_text.split(',') if tag.strip()]
        
        if not tags:
            # Handle empty tag list
            return
            
        # Save painter state to restore later
        painter.save()
        
        # Handle mouse hover and selection
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, option.palette.alternateBase())
        
        # Determine badge color based on column
        if "topic" in str(column).lower() or column == 2:  # Assumes column 2 is Topics
            badge_color = self.topic_color
        elif "title" in str(column).lower() or column == 3:  # Assumes column 3 is Titles
            badge_color = self.title_color
        elif "name" in str(column).lower():
            badge_color = self.name_color
        else:
            badge_color = self.default_color
        
        # Set up font for drawing text
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        
        # Padding and sizes for badge layout
        padding = 4
        margin = 3
        badge_height = min(20, option.rect.height() // 3)
        
        # Determine visible tags and if we need to show "+X more"
        visible_tags = tags[:self.max_visible_tags]
        has_more = len(tags) > self.max_visible_tags
        
        # Calculate positions for badges
        x = option.rect.left() + margin
        y = option.rect.top() + margin
        max_width = option.rect.width() - 2 * margin
        
        # Draw each visible tag
        for i, tag in enumerate(visible_tags):
            # Measure text width to size the badge
            text_width = painter.fontMetrics().horizontalAdvance(tag)
            badge_width = text_width + 2 * padding
            
            # If this badge would go beyond the cell width, move to next row
            if x + badge_width > option.rect.right() - margin:
                x = option.rect.left() + margin
                y += badge_height + margin
                
                # If we're going beyond the bottom of the cell, stop drawing
                if y + badge_height > option.rect.bottom() - margin:
                    break
            
            # Define badge rectangle
            badge_rect = QRectF(x, y, badge_width, badge_height)
            
            # Define rounded rectangle path
            path = QPainterPath()
            path.addRoundedRect(badge_rect, 8, 8)
            
            # Draw badge background
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(badge_color))
            painter.drawPath(path)
            
            # Draw badge text
            painter.setPen(QPen(self.text_color))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, tag)
            
            # Move x position for next badge
            x += badge_width + margin
        
        # Draw "+X more" if needed
        if has_more:
            more_text = f"+{len(tags) - self.max_visible_tags} more"
            text_width = painter.fontMetrics().horizontalAdvance(more_text)
            badge_width = text_width + 2 * padding
            
            # Move to next row if needed
            if x + badge_width > option.rect.right() - margin:
                x = option.rect.left() + margin
                y += badge_height + margin
            
            # Define badge rectangle for "+X more"
            badge_rect = QRectF(x, y, badge_width, badge_height)
            
            # Define rounded rectangle path
            path = QPainterPath()
            path.addRoundedRect(badge_rect, 8, 8)
            
            # Draw badge background with a darker color
            darker_color = badge_color.darker(120)
            painter.setBrush(QBrush(darker_color))
            painter.drawPath(path)
            
            # Draw badge text
            painter.setPen(QPen(self.text_color))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, more_text)
        
        # Restore painter state
        painter.restore()
    
    def sizeHint(self, option, index):
        """
        Suggest a size for the cell based on the number of tags.
        This helps ensure we have enough vertical space for multiple rows of tags.
        """
        tag_text = index.data(Qt.ItemDataRole.DisplayRole)
        if not tag_text:
            return super().sizeHint(option, index)
            
        tags = [tag.strip() for tag in tag_text.split(',') if tag.strip()]
        
        # Base height on number of tags and maximum tags per row
        tags_per_row = max(1, option.rect.width() // 100)  # Rough estimate of badges per row
        rows_needed = (len(tags) + tags_per_row - 1) // tags_per_row  # Ceiling division
        
        # Each row is roughly 25 pixels high
        height = max(25, rows_needed * 25)
        
        # Return the calculated size
        return QSize(option.rect.width(), height)
