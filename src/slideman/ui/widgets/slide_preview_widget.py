from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, Signal, Slot, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QColor, QPixmap

class SlidePreviewWidget(QWidget):
    """
    Widget for displaying a preview of a slide with element highlighting.
    Allows displaying a slide image with highlighted elements based on selection.
    """
    # Signals
    elementClicked = Signal(int)  # Emitted when an element is clicked in the preview
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # UI setup
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Preview label
        self.preview_label = QLabel(self)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.preview_label.setMinimumSize(300, 200)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        self.layout.addWidget(self.preview_label)
        
        # Data
        self.slide_pixmap = None
        self.elements = []
        self.highlighted_element_id = None
        self.highlighted_rect = None
        
    def clear(self):
        """Clear the preview"""
        self.slide_pixmap = None
        self.elements = []
        self.highlighted_element_id = None
        self.highlighted_rect = None
        self.preview_label.clear()
        self.preview_label.setText("No slide selected")
        
    def set_slide_image(self, pixmap):
        """Set the slide image to display"""
        if pixmap and not pixmap.isNull():
            self.slide_pixmap = pixmap
            self._update_display()
        else:
            self.clear()
            
    def set_elements(self, elements):
        """Set the slide elements with their bounding boxes"""
        self.elements = elements
        self._update_display()
        
    def highlight_element(self, element_id):
        """Highlight a specific element by ID"""
        self.highlighted_element_id = element_id
        
        # Find the element's bounding box
        for element in self.elements:
            if element.get('id') == element_id:
                bounds = element.get('bounds')
                if bounds:
                    x, y, width, height = bounds
                    self.highlighted_rect = QRect(x, y, width, height)
                    break
        else:
            self.highlighted_rect = None
            
        self._update_display()
        
    def _update_display(self):
        """Update the display with current slide and highlighting"""
        if not self.slide_pixmap or self.slide_pixmap.isNull():
            self.preview_label.setText("No slide image available")
            return
        
        # Create a copy of the pixmap to draw on
        display_pixmap = QPixmap(self.slide_pixmap)
        
        # Draw element highlights if needed
        if self.elements and display_pixmap:
            painter = QPainter(display_pixmap)
            
            # Draw all elements with a light outline
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            for element in self.elements:
                bounds = element.get('bounds')
                if bounds:
                    x, y, width, height = bounds
                    painter.drawRect(x, y, width, height)
            
            # Draw the highlighted element with a more visible outline
            if self.highlighted_rect:
                painter.setPen(QPen(QColor(0, 120, 215), 2))
                painter.drawRect(self.highlighted_rect)
                
                # Draw a semi-transparent fill for the highlighted element
                painter.fillRect(
                    self.highlighted_rect, 
                    QColor(0, 120, 215, 30)  # Semi-transparent blue
                )
                
            painter.end()
        
        # Set the pixmap to the label, scaling if needed
        label_size = self.preview_label.size()
        scaled_pixmap = display_pixmap.scaled(
            label_size, 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled_pixmap)
        
    def resizeEvent(self, event):
        """Handle resize events to scale the preview properly"""
        super().resizeEvent(event)
        self._update_display()
        
    def mousePressEvent(self, event):
        """Handle mouse clicks to select elements"""
        if not self.slide_pixmap or not self.elements:
            return super().mousePressEvent(event)
            
        # Calculate the scaling factor between the original pixmap and the displayed pixmap
        label_size = self.preview_label.size()
        pixmap_size = self.slide_pixmap.size()
        
        # Get the position of the pixmap within the label
        pixmap_rect = self.preview_label.pixmap().rect()
        label_rect = self.preview_label.rect()
        
        # Calculate the offset of the pixmap in the label (for centering)
        offset_x = (label_rect.width() - pixmap_rect.width()) / 2
        offset_y = (label_rect.height() - pixmap_rect.height()) / 2
        
        # Convert click position to coordinates in the original pixmap
        pos = event.position().toPoint()
        if (pos.x() < offset_x or pos.y() < offset_y or 
            pos.x() > offset_x + pixmap_rect.width() or 
            pos.y() > offset_y + pixmap_rect.height()):
            return super().mousePressEvent(event)
            
        # Adjust for the offset
        pos = QPoint(pos.x() - offset_x, pos.y() - offset_y)
        
        # Scale the position to the original pixmap coordinates
        scale_x = pixmap_size.width() / pixmap_rect.width()
        scale_y = pixmap_size.height() / pixmap_rect.height()
        original_x = int(pos.x() * scale_x)
        original_y = int(pos.y() * scale_y)
        
        # Check if the click is within any element
        for element in self.elements:
            bounds = element.get('bounds')
            if bounds:
                x, y, width, height = bounds
                if (x <= original_x <= x + width and
                    y <= original_y <= y + height):
                    # Emit the signal with the element ID
                    self.elementClicked.emit(element.get('id'))
                    return
                    
        # No element was clicked
        super().mousePressEvent(event)
