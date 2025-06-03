import logging
from typing import Optional
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPixmap
from ...app_state import app_state
from .base_preview_widget import BasePreviewWidget

logger = logging.getLogger(__name__)


class DeliveryPreviewWidget(BasePreviewWidget):
    """Delivery-specific preview widget with larger thumbnail size."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        # Initialize with larger delivery thumbnail size
        super().__init__(
            parent=parent,
            icon_size=(180, 135),
            grid_padding=(20, 40),
            spacing=10
        )
        self.KeywordId = None
        
    def add_slide(self, slide_id: int, thumbnail: QPixmap, keywords: dict):
        """Add slide ensuring KeywordId is present."""
        if 'KeywordId' not in keywords:
            keywords['KeywordId'] = None
        return super().add_slide(slide_id, thumbnail, keywords)
    
    def _on_order_changed(self, order: list[int]):
        """Handle order changes by updating app state."""
        app_state.set_assembly_order(order)
