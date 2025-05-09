# src/slideman/models/project.py

from typing import Optional, Union, Any
from pydantic import BaseModel, field_validator


class Project(BaseModel):
    """Represents a single project within the application.
    
    Attributes:
        id: Optional[Union[int, str]] - Database primary key, None if not yet saved
        name: str - The name of the project
        folder_path: str - Path to the project folder
        created_at: Optional[str] - ISO format string from SQLite, None if not set
    """
    id: Optional[Union[int, str]] = None  # Database primary key, None if not yet saved
    name: str
    folder_path: str
    created_at: Optional[str] = None  # ISO format string from SQLite
    
    model_config = {
        "arbitrary_types_allowed": False,
        "validate_assignment": True,  # Validate when attributes are set
        "extra": "forbid"  # Forbid extra attributes
    }
    
    @field_validator('name')
    @classmethod
    def name_must_be_string(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise TypeError(f"name must be a string, got {type(v).__name__}")
        return v
    
    @field_validator('folder_path')
    @classmethod
    def folder_path_must_be_string(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise TypeError(f"folder_path must be a string, got {type(v).__name__}")
        return v
    
    @field_validator('created_at')
    @classmethod
    def created_at_must_be_string_or_none(cls, v: Any) -> Optional[str]:
        if v is not None and not isinstance(v, str):
            raise TypeError(f"created_at must be a string or None, got {type(v).__name__}")
        return v