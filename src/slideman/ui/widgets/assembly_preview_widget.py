import logging
from typing import Optional
from PySide6.QtWidgets import QWidget
from ...app_state import app_state
from .base_preview_widget import BasePreviewWidget

logger = logging.getLogger(__name__)


class AssemblyPreviewWidget(BasePreviewWidget):
    """Assembly-specific preview widget with standard thumbnail size."""

    def __init__(self, parent: Optional[QWidget] = None):
        # Initialize with standard assembly thumbnail size
        super().__init__(
            parent=parent,
            icon_size=(160, 120),
            grid_padding=(10, 30),
            spacing=10
        )
        self.KeywordId = None

    def _on_order_changed(self, order: list[int]):
        """Handle order changes by updating app state."""
        app_state.set_assembly_order(order)

