# src/slideman/ui/custom_widgets/slide_preview_widget.py

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame, QSizePolicy
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush
from PySide6.QtCore import Qt, QSize, QRect, QPoint, Signal

class SlidePreviewWidget(QWidget):
    """
    Widget that displays a larger preview of a slide with its elements highlighted.
    """
    # Signal emitted when the preview is clicked
    elementClicked = Signal(int)  # element ID
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create label for displaying the slide
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFrameShape(QFrame.Shape.Panel)
        self.image_label.setFrameShadow(QFrame.Shadow.Sunken)
        self.image_label.setLineWidth(1)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Add to layout
        layout.addWidget(self.image_label)
        
        # Store slide data
        self._slide_id = None
        self._slide_thumbnail = None
        self._elements = []  # List of elements with their bounding boxes
        self._element_tags = {}  # Dict mapping element ID to tags
        
    def set_slide(self, slide_id, thumbnail, elements=None, element_tags=None):
        """
        Set the slide to display
        
        Args:
            slide_id: The ID of the slide
            thumbnail: QPixmap of the slide
            elements: List of element objects with properties: id, x, y, width, height
            element_tags: Dict mapping element ID to a list of tag strings
        """
        self._slide_id = slide_id
        self._slide_thumbnail = thumbnail
        self._elements = elements or []
        self._element_tags = element_tags or {}
        
        # Update the display
        self._update_display()
        
    def clear(self):
        """Clear the preview"""
        self._slide_id = None
        self._slide_thumbnail = None
        self._elements = []
        self._element_tags = {}
        
        # Clear the label
        self.image_label.setPixmap(QPixmap())
        
    def _update_display(self):
        """Update the display with the current slide and elements"""
        if not self._slide_id or not self._slide_thumbnail:
            self.image_label.setText("No slide selected")
            return
            
        # Create a copy of the thumbnail so we can draw on it
        preview_pixmap = QPixmap(self._slide_thumbnail)
        
        # Create a painter to draw element highlights
        painter = QPainter(preview_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw each element's bounding box
        for element in self._elements:
            # Skip if no position data
            if not hasattr(element, 'x') or not hasattr(element, 'y'):
                continue
                
            # Get element properties
            element_id = element.id
            x, y = element.x, element.y
            width = getattr(element, 'width', 100)
            height = getattr(element, 'height', 100)
            
            # Scale coordinates to thumbnail size
            scale_x = preview_pixmap.width() / 1280  # Assuming slide is 1280px wide
            scale_y = preview_pixmap.height() / 720   # Assuming slide is 720px high
            
            scaled_x = int(x * scale_x)
            scaled_y = int(y * scale_y)
            scaled_width = int(width * scale_x)
            scaled_height = int(height * scale_y)
            
            # Determine color based on whether element has tags
            has_tags = element_id in self._element_tags and bool(self._element_tags[element_id])
            
            if has_tags:
                # Green for elements with tags
                pen_color = QColor(0, 200, 0)
                brush_color = QColor(0, 200, 0, 50)  # Semi-transparent
            else:
                # Red for elements without tags
                pen_color = QColor(200, 0, 0)
                brush_color = QColor(200, 0, 0, 30)  # Semi-transparent
                
            # Draw the element highlight
            painter.setPen(QPen(pen_color, 2))
            painter.setBrush(QBrush(brush_color))
            painter.drawRect(scaled_x, scaled_y, scaled_width, scaled_height)
            
        # End painting
        painter.end()
        
        # Update the label with the modified pixmap
        self.image_label.setPixmap(preview_pixmap)
        
    def sizeHint(self):
        """Suggest a size for the widget"""
        if self._slide_thumbnail:
            # Return a size proportional to the thumbnail
            return QSize(400, 225)  # 16:9 aspect ratio
        return QSize(400, 225)
        
    def mousePressEvent(self, event):
        """Handle mouse press events to detect clicks on elements"""
        if not self._slide_id or not self._slide_thumbnail or not self._elements:
            return
            
        # Get click position
        pos = event.position().toPoint()
        
        # Translate to pixmap coordinates
        label_rect = self.image_label.rect()
        pixmap_rect = self.image_label.pixmap().rect()
        
        # If the pixmap is smaller than the label, it will be centered
        if pixmap_rect.width() < label_rect.width() or pixmap_rect.height() < label_rect.height():
            # Calculate offset
            offset_x = (label_rect.width() - pixmap_rect.width()) // 2
            offset_y = (label_rect.height() - pixmap_rect.height()) // 2
            
            # Adjust click position
            pos.setX(pos.x() - offset_x)
            pos.setY(pos.y() - offset_y)
            
        # Check if click is inside the pixmap
        if not QRect(0, 0, pixmap_rect.width(), pixmap_rect.height()).contains(pos):
            return
            
        # Scale factors
        scale_x = pixmap_rect.width() / 1280  # Assuming slide is 1280px wide
        scale_y = pixmap_rect.height() / 720   # Assuming slide is 720px high
        
        # Check if click is inside any element
        for element in self._elements:
            # Skip if no position data
            if not hasattr(element, 'x') or not hasattr(element, 'y'):
                continue
                
            # Get element properties
            element_id = element.id
            x, y = element.x, element.y
            width = getattr(element, 'width', 100)
            height = getattr(element, 'height', 100)
            
            # Scale coordinates to thumbnail size
            scaled_x = int(x * scale_x)
            scaled_y = int(y * scale_y)
            scaled_width = int(width * scale_x)
            scaled_height = int(height * scale_y)
            
            # Check if click is inside this element
            element_rect = QRect(scaled_x, scaled_y, scaled_width, scaled_height)
            if element_rect.contains(pos):
                # Emit signal with element ID
                self.elementClicked.emit(element_id)
                return
                
        # If no element was clicked, call the parent class implementation
        super().mousePressEvent(event)
