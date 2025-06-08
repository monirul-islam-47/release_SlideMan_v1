"""
Core data models for the PrezI application.
Implements the domain model from the founders briefcase specifications.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from uuid import uuid4


class ProjectStatus(str, Enum):
    """Project status enumeration"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class SlideType(str, Enum):
    """Slide type classification"""
    TITLE = "title"
    CONTENT = "content"
    CHART = "chart"
    IMAGE = "image"
    TABLE = "table"
    CONCLUSION = "conclusion"
    UNKNOWN = "unknown"


class ElementType(str, Enum):
    """Slide element type classification"""
    TEXT = "text"
    IMAGE = "image"
    CHART = "chart"
    TABLE = "table"
    SHAPE = "shape"
    UNKNOWN = "unknown"


class Keyword(BaseModel):
    """Keyword model for tagging slides and elements"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(default="#3B82F6")  # Default blue color
    description: Optional[str] = Field(None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.now)
    usage_count: int = Field(default=0)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class Element(BaseModel):
    """Individual slide element (text box, image, chart, etc.)"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    slide_id: str
    element_type: ElementType = ElementType.UNKNOWN
    content: Optional[str] = Field(None, max_length=10000)
    position_x: float = 0.0
    position_y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    keywords: List[str] = Field(default_factory=list)  # Keyword IDs
    ai_analysis: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class Slide(BaseModel):
    """Individual presentation slide"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    file_id: str
    slide_number: int = Field(..., ge=1)
    title: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=5000)
    slide_type: SlideType = SlideType.UNKNOWN
    thumbnail_path: Optional[str] = None
    full_image_path: Optional[str] = None
    elements: List[Element] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)  # Keyword IDs
    ai_analysis: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class File(BaseModel):
    """PowerPoint file container"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    filename: str = Field(..., min_length=1, max_length=255)
    file_path: str = Field(..., min_length=1)
    file_size: int = Field(..., ge=0)
    slide_count: int = Field(default=0, ge=0)
    slides: List[Slide] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)  # Keyword IDs
    ai_analysis: Optional[Dict[str, Any]] = Field(default_factory=dict)
    processed: bool = Field(default=False)
    processing_error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class Project(BaseModel):
    """Project container for organizing files and slides"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: ProjectStatus = ProjectStatus.ACTIVE
    files: List[File] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)  # Keyword IDs
    ai_analysis: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def total_slides(self) -> int:
        """Calculate total slides across all files"""
        return sum(file.slide_count for file in self.files)

    @property
    def total_files(self) -> int:
        """Get total file count"""
        return len(self.files)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class Assembly(BaseModel):
    """Slide assembly for creating new presentations"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    slide_ids: List[str] = Field(default_factory=list)  # Ordered list of slide IDs
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def slide_count(self) -> int:
        """Get number of slides in assembly"""
        return len(self.slide_ids)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class SearchResult(BaseModel):
    """Search result container"""
    slides: List[Slide] = Field(default_factory=list)
    files: List[File] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    total_results: int = 0
    search_time_ms: float = 0.0
    query: str = ""
    filters: Dict[str, Any] = Field(default_factory=dict)


class AIAnalysisRequest(BaseModel):
    """Request model for AI analysis"""
    content_type: str = Field(..., regex="^(slide|element|file|project)$")
    content_id: str
    analysis_type: str = Field(..., regex="^(keywords|classification|summary|insights)$")
    additional_context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AIAnalysisResponse(BaseModel):
    """Response model for AI analysis"""
    content_id: str
    analysis_type: str
    results: Dict[str, Any]
    confidence: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: float
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ExportRequest(BaseModel):
    """Request model for exporting presentations"""
    assembly_id: Optional[str] = None
    slide_ids: Optional[List[str]] = None
    export_format: str = Field(..., regex="^(pptx|pdf)$")
    filename: str = Field(..., min_length=1, max_length=200)
    include_notes: bool = Field(default=True)
    apply_styling: bool = Field(default=True)


class ExportResponse(BaseModel):
    """Response model for export operations"""
    export_id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    file_path: str
    file_size: int
    slide_count: int
    export_format: str
    processing_time_ms: float
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


# Request/Response models for API endpoints

class CreateProjectRequest(BaseModel):
    """Request model for creating projects"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class UpdateProjectRequest(BaseModel):
    """Request model for updating projects"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[ProjectStatus] = None


class CreateKeywordRequest(BaseModel):
    """Request model for creating keywords"""
    name: str = Field(..., min_length=1, max_length=100)
    color: Optional[str] = Field("#3B82F6")
    description: Optional[str] = Field(None, max_length=500)


class UpdateKeywordRequest(BaseModel):
    """Request model for updating keywords"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)


class TagRequest(BaseModel):
    """Request model for tagging content with keywords"""
    keyword_ids: List[str]
    action: str = Field(..., regex="^(add|remove|replace)$")


class SearchRequest(BaseModel):
    """Request model for search operations"""
    query: Optional[str] = None
    keyword_filters: Optional[List[str]] = Field(default_factory=list)
    project_filters: Optional[List[str]] = Field(default_factory=list)
    slide_type_filters: Optional[List[SlideType]] = Field(default_factory=list)
    element_type_filters: Optional[List[ElementType]] = Field(default_factory=list)
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)