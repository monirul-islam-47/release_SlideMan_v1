# src/slideman/models/element.py

from typing import Optional, Any
from pydantic import BaseModel, field_validator

class Element(BaseModel):
    """Represents a tagged element (shape, image, etc.) on a slide.
    
    Attributes:
        id: Optional[int] - Database primary key, None if not yet saved
        slide_id: int - Foreign key to the parent Slide
        element_type: str - Type identifier (e.g., "SHAPE", "PICTURE", "CHART")
        bbox_x: float - X-coordinate of the element's bounding box in EMU
        bbox_y: float - Y-coordinate of the element's bounding box in EMU
        bbox_w: float - Width of the element's bounding box in EMU
        bbox_h: float - Height of the element's bounding box in EMU
    """
    id: Optional[int] = None
    slide_id: int         # Foreign key to Slide
    element_type: str     # Type identifier (e.g., "SHAPE", "PICTURE", "CHART")
    # Bounding Box coordinates in English Metric Units (EMU)
    bbox_x: float
    bbox_y: float
    bbox_w: float
    bbox_h: float
    
    model_config = {
        "arbitrary_types_allowed": False,
        "validate_assignment": True,
        "extra": "forbid"
    }
    
    @field_validator('element_type')
    @classmethod
    def validate_element_type(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise TypeError(f"element_type must be a string, got {type(v).__name__}")
        if not v.strip():
            raise ValueError("element_type cannot be empty")
        return v
    
    @field_validator('bbox_x', 'bbox_y', 'bbox_w', 'bbox_h')
    @classmethod
    def validate_bbox(cls, v: Any, info: Any) -> float:
        if not isinstance(v, (int, float)):
            raise TypeError(f"{info.field_name} must be a number, got {type(v).__name__}")
        
        # For width and height, validate they are non-negative (allow 0 for existing data)
        if info.field_name in ['bbox_w', 'bbox_h'] and v < 0:
            raise ValueError(f"{info.field_name} must be non-negative, got {v}")
            
        return float(v)  # Convert to float if it's an int