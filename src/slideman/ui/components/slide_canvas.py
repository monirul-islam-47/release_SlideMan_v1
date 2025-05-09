# src/slideman/ui/components/slide_canvas.py

import logging
from pathlib import Path
from typing import Optional, List, Dict

from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
from PySide6.QtGui import QPixmap, QPainter, QWheelEvent, QMouseEvent, QColor, QBrush, QPen

from ...models.element import Element

logger = logging.getLogger(__name__)

class SlideCanvas(QGraphicsView):
    """
    Custom QGraphicsView for displaying and interacting with slide images.
    Supports zooming, panning, and will be extended to support element overlays.
    """
    # Custom role for storing element ID in rect items
    ELEMENT_ID_ROLE = Qt.UserRole + 1
    
    # Signal emitted when an element is selected/deselected (-1 means deselected)
    elementSelected = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("Initializing SlideCanvas")
        
        # Create the scene to hold the slide image
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Internal state variables
        self._current_pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._current_slide_id: Optional[int] = None
        self._zoom_factor = 1.0
        self._min_zoom = 0.1
        self._max_zoom = 5.0
        
        # Element overlay variables
        self._element_items: Dict[int, QGraphicsRectItem] = {}  # element_id -> rect_item
        self._selected_element_item: Optional[QGraphicsRectItem] = None
        
        # Standard slide dimensions in EMU (English Metric Units)
        # These are for a standard 4:3 PowerPoint slide
        self.WIDTH_EMU = 9144000
        self.HEIGHT_EMU = 6858000
        
        # Define display styles for element overlays
        self.DEFAULT_PEN = QPen(QColor(100, 100, 255, 150), 1, Qt.PenStyle.DashLine)
        self.HIGHLIGHT_PEN = QPen(QColor(50, 200, 50, 200), 2, Qt.PenStyle.SolidLine)
        self.DEFAULT_BRUSH = QBrush(QColor(100, 100, 255, 30))  # Semi-transparent fill
        
        # Configure view properties for optimal rendering and interaction
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Allow focus to enable key events later
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        
        logger.info("SlideCanvas initialized")
    
    def load_slide(self, slide_id: int, image_full_path: Path, elements: List[Element] = None):
        """
        Loads a slide image into the canvas and overlays element bounding boxes if provided.
        
        Args:
            slide_id: Database ID of the slide
            image_full_path: Path to the full-resolution image file
            elements: Optional list of Element objects to overlay on the slide
        """
        logger.info(f"Loading slide ID {slide_id} from path: {image_full_path}")
        
        # Store current slide ID
        self._current_slide_id = slide_id
        
        # Clear existing content
        self.clear()
        
        # Validate image path
        if not image_full_path.is_file():
            logger.error(f"Image file not found: {image_full_path}")
            return
        
        # Load the image
        pixmap = QPixmap(str(image_full_path))
        if pixmap.isNull():
            logger.error(f"Failed to load image: {image_full_path}")
            return
        
        # Create and add the pixmap item to the scene
        self._current_pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self._current_pixmap_item)
        
        # Update scene rectangle to match the pixmap
        self.scene.setSceneRect(self._current_pixmap_item.boundingRect())
        
        # Add element overlays if provided
        if elements:
            self._draw_element_overlays(elements, pixmap.width(), pixmap.height())
        
        # Reset zoom and fit the slide to the view
        self._zoom_factor = 1.0
        self.fit_slide_to_view()
        
        logger.debug(f"Slide {slide_id} loaded successfully. Image size: {pixmap.width()}x{pixmap.height()}")
    
    def _draw_element_overlays(self, elements: List[Element], pixmap_width: int, pixmap_height: int):
        """
        Creates and adds QGraphicsRectItems to represent element bounding boxes.
        
        Args:
            elements: List of Element objects to draw
            pixmap_width: Width of the loaded slide image in pixels
            pixmap_height: Height of the loaded slide image in pixels
        """
        logger.debug(f"Drawing overlays for {len(elements)} elements")
        
        # Clear any existing elements
        self._clear_element_items()
        
        for element in elements:
            # Convert EMU coordinates to scene (pixmap) coordinates
            scene_x = (element.bbox_x / self.WIDTH_EMU) * pixmap_width
            scene_y = (element.bbox_y / self.HEIGHT_EMU) * pixmap_height
            scene_w = (element.bbox_w / self.WIDTH_EMU) * pixmap_width
            scene_h = (element.bbox_h / self.HEIGHT_EMU) * pixmap_height
            
            # Create rectangle item
            rect_item = QGraphicsRectItem(scene_x, scene_y, scene_w, scene_h)
            
            # Store element ID as item data
            rect_item.setData(self.ELEMENT_ID_ROLE, element.id)
            
            # Set visual style
            rect_item.setBrush(self.DEFAULT_BRUSH)
            rect_item.setPen(self.DEFAULT_PEN)
            
            # Make item selectable and focusable
            rect_item.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
            
            # Add to scene
            self.scene.addItem(rect_item)
            
            # Store reference
            self._element_items[element.id] = rect_item
            
            logger.debug(f"Added element overlay: ID={element.id}, Type={element.element_type}, " 
                        f"Pos=({scene_x:.1f},{scene_y:.1f}), Size=({scene_w:.1f}x{scene_h:.1f})")
    
    def _clear_element_items(self):
        """Removes all element overlay items from the scene."""
        # Remove from scene and clear references
        for item in self._element_items.values():
            self.scene.removeItem(item)
        
        self._element_items.clear()
        self._selected_element_item = None
    
    def clear(self):
        """Clears the canvas, removing any loaded slide and element overlays."""
        logger.debug("Clearing slide canvas")
        self._clear_element_items()
        self.scene.clear()
        self._current_pixmap_item = None
        self._current_slide_id = None
        self._zoom_factor = 1.0
    
    def fit_slide_to_view(self):
        """Scales the view to fit the entire slide while maintaining aspect ratio."""
        if not self._current_pixmap_item:
            logger.debug("No pixmap item to fit to view")
            return
        
        # Reset transformation and fit the slide to view
        self.resetTransform()
        self.fitInView(self._current_pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        
        # Update zoom factor based on current transform
        self._zoom_factor = self._get_current_zoom_factor()
        logger.debug(f"Fitted slide to view. Zoom factor: {self._zoom_factor:.2f}")
    
    def _get_current_zoom_factor(self) -> float:
        """Calculate the current zoom factor from the transform matrix."""
        return self.transform().m11()  # m11 is the horizontal scaling factor
    
    def wheelEvent(self, event: QWheelEvent):
        """
        Handle mouse wheel events for zooming in/out.
        
        Args:
            event: The wheel event containing scroll direction and amount
        """
        if not self._current_pixmap_item:
            return super().wheelEvent(event)
        
        # Get the scroll amount
        delta = event.angleDelta().y()
        
        # Define zoom step factor
        zoom_step = 1.15
        
        # Calculate new zoom factor
        if delta > 0:  # Zoom in
            new_zoom = self._zoom_factor * zoom_step
        else:  # Zoom out
            new_zoom = self._zoom_factor / zoom_step
        
        # Clamp zoom factor to min/max values
        new_zoom = max(self._min_zoom, min(new_zoom, self._max_zoom))
        
        # Calculate the zoom ratio to apply
        zoom_ratio = new_zoom / self._zoom_factor
        
        # Apply zoom
        self.scale(zoom_ratio, zoom_ratio)
        
        # Update current zoom factor
        self._zoom_factor = new_zoom
        
        logger.debug(f"Zoom changed to {self._zoom_factor:.2f}")
        
        # Skip default event processing
        event.accept()
    
    def mousePressEvent(self, event: QMouseEvent):
        """
        Handle mouse press events for element selection and panning.
        
        Args:
            event: The mouse event containing button and position
        """
        # Let parent class handle panning (middle button drag)
        super().mousePressEvent(event)
        
        # Only handle left-click for element selection
        if event.button() != Qt.MouseButton.LeftButton:
            return
        
        # Convert mouse position to scene coordinates
        scene_pos = self.mapToScene(event.pos())
        
        # Get items at click position (topmost first)
        items = self.scene.items(scene_pos)
        
        # Find first item that has our element ID role data
        clicked_element_item = None
        for item in items:
            if isinstance(item, QGraphicsRectItem) and item.data(self.ELEMENT_ID_ROLE) is not None:
                clicked_element_item = item
                break
        
        # Deselect current element if any
        if self._selected_element_item:
            self._selected_element_item.setPen(self.DEFAULT_PEN)
            previous_element_id = self._selected_element_item.data(self.ELEMENT_ID_ROLE)
            self._selected_element_item = None
            
            # Only emit deselection signal if we're not selecting a new element
            if not clicked_element_item:
                logger.debug(f"Element deselected: ID={previous_element_id}")
                self.elementSelected.emit(-1)
        
        # Select new element if clicked
        if clicked_element_item:
            self._selected_element_item = clicked_element_item
            clicked_element_item.setPen(self.HIGHLIGHT_PEN)
            element_id = clicked_element_item.data(self.ELEMENT_ID_ROLE)
            logger.debug(f"Element selected: ID={element_id}")
            self.elementSelected.emit(element_id)
    
    def resizeEvent(self, event):
        """Ensure slide remains properly fitted when the widget is resized."""
        super().resizeEvent(event)
        if self._current_pixmap_item and self.isVisible():
            # Only refit if zoom is approximately 1.0 (initial fit)
            if 0.9 <= self._zoom_factor <= 1.1:
                self.fit_slide_to_view()
    
    def select_element(self, element_id: int):
        """
        Programmatically select an element by its ID.
        
        Args:
            element_id: The ID of the element to select
        """
        # First deselect the current element if any
        if self._selected_element_item:
            self._selected_element_item.setPen(self.DEFAULT_PEN)
            self._selected_element_item = None
            
        # Find the element item with the matching ID
        if element_id in self._element_items:
            # Select the element
            self._selected_element_item = self._element_items[element_id]
            self._selected_element_item.setPen(self.HIGHLIGHT_PEN)
            
            # Ensure element is visible in the viewport
            self.ensureVisible(self._selected_element_item)
            
            # Emit signal
            logger.debug(f"Element selected programmatically: ID={element_id}")
            self.elementSelected.emit(element_id)
            return True
        else:
            logger.warning(f"Cannot select element: ID {element_id} not found")
            return False
