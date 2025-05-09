# src/slideman/models/keyword.py

from dataclasses import dataclass
from typing import Literal, Optional

# Define the allowed keyword kinds using Literal for type safety
KeywordKind = Literal["topic", "title", "name"]

@dataclass
class Keyword:
    """Represents a single keyword entry in the canonical list."""
    id: Optional[int]
    keyword: str      # The actual tag text (case-insensitive unique in DB)
    kind: KeywordKind # Type of keyword ('topic', 'title', 'name')