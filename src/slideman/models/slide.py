# src/slideman/models/slide.py
from typing import Optional, Any
from pydantic import BaseModel, field_validator, computed_field

class Slide(BaseModel):
    """Represents a single slide within a source file.
    
    Attributes:
        id: Optional[int] - Database primary key, None if not yet saved
        file_id: int - Foreign key to the parent File
        slide_index: int - Index of the slide within the file (0-based)
        title: Optional[str] - Title of the slide, if available
        thumb_rel_path: Optional[str] - Relative path to the slide thumbnail
        image_rel_path: Optional[str] - Relative path to the full-size slide image
    """
    id: Optional[int] = None
    file_id: int
    slide_index: int
    title: Optional[str] = None
    thumb_rel_path: Optional[str] = None
    image_rel_path: Optional[str] = None
    
    model_config = {
        "arbitrary_types_allowed": False,
        "validate_assignment": True,
        "extra": "forbid"
    }
    
    @field_validator('slide_index')
    @classmethod
    def validate_slide_index(cls, v: Any) -> int:
        if not isinstance(v, int):
            raise TypeError(f"slide_index must be an integer, got {type(v).__name__}")
        if v < 0:
            raise ValueError(f"slide_index must be non-negative, got {v}")
        return v
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Any) -> Optional[str]:
        if v is not None and not isinstance(v, str):
            raise TypeError(f"title must be a string or None, got {type(v).__name__}")
        return v
    
    @field_validator('thumb_rel_path', 'image_rel_path')
    @classmethod
    def validate_path(cls, v: Any, info: Any) -> Optional[str]:
        path_type = info.field_name
        if v is not None and not isinstance(v, str):
            raise TypeError(f"{path_type} must be a string or None, got {type(v).__name__}")
        return v
    
    @computed_field
    @property
    def slide_num(self) -> int:
        """For backwards compatibility - returns slide_index as slide_num"""
        return self.slide_index