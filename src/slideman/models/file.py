# src/slideman/models/file.py
from dataclasses import dataclass
from typing import Optional, Literal

FileStatus = Literal['Pending', 'In Progress', 'Completed', 'Failed']

@dataclass
class File:
    """Represents a single source PowerPoint file within a project."""
    id: Optional[int]
    project_id: int
    filename: str
    rel_path: str
    slide_count: Optional[int] = None
    checksum: Optional[str] = None
    conversion_status: FileStatus = 'Pending' # Add field with default