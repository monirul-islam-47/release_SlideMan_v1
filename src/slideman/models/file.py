# src/slideman/models/file.py
from typing import Optional, Literal, Union, Any
from pydantic import BaseModel, field_validator

FileStatus = Literal['Pending', 'In Progress', 'Completed', 'Failed']

class File(BaseModel):
    """Represents a single source PowerPoint file within a project.
    
    Attributes:
        id: Optional[int] - Database primary key, None if not yet saved
        project_id: int - Foreign key to the parent Project
        filename: str - The name of the file
        rel_path: str - Relative path to the file within the project
        slide_count: Optional[int] - Number of slides in the file, if known
        checksum: Optional[str] - Hash of the file contents for change detection
        conversion_status: FileStatus - Current processing status of the file
        created_at: Optional[str] - Timestamp when the file was added to the database
    """
    id: Optional[int] = None
    project_id: int
    filename: str
    rel_path: str
    slide_count: Optional[int] = None
    checksum: Optional[str] = None
    conversion_status: FileStatus = 'Pending'
    created_at: Optional[str] = None
    
    model_config = {
        "arbitrary_types_allowed": False,
        "validate_assignment": True,  # Validate when attributes are set
        "extra": "forbid"  # Forbid extra attributes
    }
    
    @field_validator('filename')
    @classmethod
    def filename_must_be_string(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise TypeError(f"filename must be a string, got {type(v).__name__}")
        if not v.strip():  # Check if empty or only whitespace
            raise ValueError("filename cannot be empty")
        return v
    
    @field_validator('rel_path')
    @classmethod
    def rel_path_must_be_string(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise TypeError(f"rel_path must be a string, got {type(v).__name__}")
        return v
    
    @field_validator('conversion_status')
    @classmethod
    def validate_status(cls, v: Any) -> FileStatus:
        valid_statuses = ['Pending', 'In Progress', 'Completed', 'Failed']
        if v not in valid_statuses:
            raise ValueError(f"conversion_status must be one of {valid_statuses}, got {v}")
        return v