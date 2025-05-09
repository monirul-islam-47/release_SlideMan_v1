# src/slideman/models/element.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class Element:
    """Represents a tagged element (shape, image, etc.) on a slide."""
    id: Optional[int]
    slide_id: int         # Foreign key to Slide
    element_type: str     # Type identifier (e.g., "SHAPE", "PICTURE", "CHART") - needs consistent definition
    # Bounding Box coordinates in English Metric Units (EMU)
    bbox_x: float
    bbox_y: float
    bbox_w: float
    bbox_h: float
    # Could add original shape name or ID from PPTX if needed for reconciliation
    # source_shape_id: Optional[str] = None