# src/slideman/models/slide.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Slide:
    """Represents a single slide within a source file."""
    id: Optional[int]
    file_id: int
    slide_index: int
    title: Optional[str] = None
    # --- Use new column names ---
    thumb_rel_path: Optional[str] = None
    image_rel_path: Optional[str] = None
    # --------------------------
    
    @property
    def slide_num(self) -> int:
        """For backwards compatibility - returns slide_index as slide_num"""
        return self.slide_index