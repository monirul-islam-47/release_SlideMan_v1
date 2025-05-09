import logging
from typing import Optional, Dict, List, Union
from PySide6.QtWidgets import QWidget, QListWidget, QListWidgetItem, QAbstractItemView
from PySide6.QtCore import Qt, QSize, QPoint, QRect, Signal
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen
from ...app_state import app_state
from ...services.thumbnail_cache import thumbnail_cache
from .assembly_preview_widget import AssemblyPreviewWidget

logger = logging.getLogger(__name__)

class DeliveryPreviewWidget(AssemblyPreviewWidget):
    """ListWidget-based delivery preview with the same drag-drop behavior as AssemblyPreview."""
    orderChanged = Signal(list)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        # Initialize KeywordId with None to satisfy the validation check
        self.KeywordId = None
        # Set larger thumbnail size for delivery view
        self.setIconSize(QSize(180, 135))
        icon_width = self.iconSize().width()
        icon_height = self.iconSize().height()
        self.setGridSize(QSize(icon_width + 20, icon_height + 40))
        
    def add_slide(self, slide_id, thumbnail, keywords):
        # Ensure KeywordId is in the keywords dict
        if 'KeywordId' not in keywords:
            keywords['KeywordId'] = None
        return super().add_slide(slide_id, thumbnail, keywords)
        
    def dropEvent(self, event):
        logger.debug("DeliveryPreviewWidget: dropEvent")
        super().dropEvent(event)
        ids = self.get_ordered_slide_indices()
        app_state.set_assembly_order(ids)
        self.orderChanged.emit(ids)
        
    def get_ordered_slides(self):
        """Return current slides in order."""
        return [self.item(i) for i in range(self.count())]
