# src/slideman/models/keyword.py

from typing import Literal, Optional, Any
from pydantic import BaseModel, field_validator

# Define the allowed keyword kinds using Literal for type safety
KeywordKind = Literal["topic", "title", "name"]

class Keyword(BaseModel):
    """Represents a single keyword entry in the canonical list.
    
    Attributes:
        id: Optional[int] - Database primary key, None if not yet saved
        keyword: str - The actual keyword/tag text (case-insensitive unique in DB)
        kind: KeywordKind - Type of keyword ('topic', 'title', 'name')
    """
    id: Optional[int] = None
    keyword: str      # The actual tag text (case-insensitive unique in DB)
    kind: KeywordKind # Type of keyword ('topic', 'title', 'name')
    
    model_config = {
        "arbitrary_types_allowed": False,
        "validate_assignment": True,
        "extra": "forbid"
    }
    
    @field_validator('keyword')
    @classmethod
    def validate_keyword(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise TypeError(f"keyword must be a string, got {type(v).__name__}")
        if not v.strip():
            raise ValueError("keyword cannot be empty")
        return v
    
    @field_validator('kind')
    @classmethod
    def validate_kind(cls, v: Any) -> KeywordKind:
        valid_kinds = ["topic", "title", "name"]
        if v not in valid_kinds:
            raise ValueError(f"kind must be one of {valid_kinds}, got {v}")
        return v