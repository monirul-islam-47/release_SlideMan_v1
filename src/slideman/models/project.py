# src/slideman/models/project.py

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Project:
    """Represents a single project within the application."""
    id: Optional[int] # Database primary key, None if not yet saved
    name: str
    folder_path: str
    created_at: Optional[str] = None # ISO format string from SQLite

    # Example of a field not directly in DB table, maybe calculated later
    # file_count: int = 0
    # slide_count: int = 0