"""
Service interfaces for the SLIDEMAN application.

This module defines abstract interfaces for all services, enabling:
- Clear contracts between components
- Easier testing with mock implementations
- Decoupling of implementations from consumers
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from ..models.project import Project
from ..models.file import File
from ..models.slide import Slide
from ..models.element import Element
from ..models.keyword import Keyword, KeywordKind


class IProjectService(ABC):
    """Interface for project management operations."""
    
    @abstractmethod
    def create_project(self, name: str, folder_path: str) -> int:
        """Create a new project."""
        pass
    
    @abstractmethod
    def get_project(self, project_id: int) -> Optional[Project]:
        """Get a project by ID."""
        pass
    
    @abstractmethod
    def get_project_by_path(self, folder_path: str) -> Optional[Project]:
        """Get a project by folder path."""
        pass
    
    @abstractmethod
    def get_all_projects(self) -> List[Project]:
        """Get all projects."""
        pass
    
    @abstractmethod
    def update_project(self, project_id: int, name: str) -> bool:
        """Update project details."""
        pass
    
    @abstractmethod
    def delete_project(self, project_id: int) -> bool:
        """Delete a project."""
        pass


class IFileService(ABC):
    """Interface for file management operations."""
    
    @abstractmethod
    def add_file(self, project_id: int, filename: str, rel_path: str, checksum: str) -> Optional[int]:
        """Add a file to a project."""
        pass
    
    @abstractmethod
    def get_file(self, file_id: int) -> Optional[File]:
        """Get a file by ID."""
        pass
    
    @abstractmethod
    def get_files_for_project(self, project_id: int, status: Optional[str] = None) -> List[File]:
        """Get files for a project, optionally filtered by status."""
        pass
    
    @abstractmethod
    def update_file_conversion_status(self, file_id: int, status: str) -> bool:
        """Update the conversion status of a file."""
        pass
    
    @abstractmethod
    def delete_files_for_project(self, project_id: int) -> int:
        """Delete all files for a project."""
        pass


class ISlideService(ABC):
    """Interface for slide management operations."""
    
    @abstractmethod
    def add_slide(self, file_id: int, slide_index: int, title: str, notes: str,
                  thumb_rel_path: str, image_rel_path: str) -> Optional[int]:
        """Add a slide to a file."""
        pass
    
    @abstractmethod
    def get_slide(self, slide_id: int) -> Optional[Slide]:
        """Get a slide by ID."""
        pass
    
    @abstractmethod
    def get_slides_for_file(self, file_id: int) -> List[Slide]:
        """Get all slides for a file."""
        pass
    
    @abstractmethod
    def get_slides_for_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all slides for a project with file information."""
        pass
    
    @abstractmethod
    def get_slide_image_path(self, slide_id: int) -> Optional[str]:
        """Get the full resolution image path for a slide."""
        pass
    
    @abstractmethod
    def get_slide_thumbnail_path(self, slide_id: int) -> Optional[str]:
        """Get the thumbnail path for a slide."""
        pass
    
    @abstractmethod
    def delete_slides_for_file(self, file_id: int) -> int:
        """Delete all slides for a file."""
        pass


class IElementService(ABC):
    """Interface for element management operations."""
    
    @abstractmethod
    def add_element(self, slide_id: int, element_type: str, text_content: str,
                   bbox: Tuple[float, float, float, float]) -> Optional[int]:
        """Add an element to a slide."""
        pass
    
    @abstractmethod
    def get_element(self, element_id: int) -> Optional[Element]:
        """Get an element by ID."""
        pass
    
    @abstractmethod
    def get_elements_for_slide(self, slide_id: int) -> List[Element]:
        """Get all elements for a slide."""
        pass
    
    @abstractmethod
    def delete_elements_for_slide(self, slide_id: int) -> int:
        """Delete all elements for a slide."""
        pass


class IKeywordService(ABC):
    """Interface for keyword management operations."""
    
    @abstractmethod
    def add_keyword(self, keyword: str, kind: KeywordKind) -> Optional[int]:
        """Add a new keyword."""
        pass
    
    @abstractmethod
    def add_keyword_if_not_exists(self, keyword: str, kind: KeywordKind) -> Optional[int]:
        """Add a keyword if it doesn't already exist."""
        pass
    
    @abstractmethod
    def get_keyword(self, keyword_id: int) -> Optional[Keyword]:
        """Get a keyword by ID."""
        pass
    
    @abstractmethod
    def get_keyword_id(self, keyword: str, kind: KeywordKind) -> Optional[int]:
        """Get the ID of a keyword by text and kind."""
        pass
    
    @abstractmethod
    def get_all_keywords(self, kind: Optional[KeywordKind] = None) -> List[Keyword]:
        """Get all keywords, optionally filtered by kind."""
        pass
    
    @abstractmethod
    def get_all_keyword_strings(self, kind: Optional[KeywordKind] = None) -> List[str]:
        """Get all keyword strings, optionally filtered by kind."""
        pass
    
    @abstractmethod
    def search_keywords(self, query: str, kind: Optional[KeywordKind] = None,
                       project_id: Optional[int] = None) -> List[Keyword]:
        """Search for keywords matching a query."""
        pass
    
    @abstractmethod
    def merge_keywords(self, source_id: int, target_id: int) -> bool:
        """Merge one keyword into another."""
        pass
    
    @abstractmethod
    def delete_keyword(self, keyword_id: int) -> bool:
        """Delete a keyword."""
        pass


class ISlideKeywordService(ABC):
    """Interface for slide-keyword association operations."""
    
    @abstractmethod
    def link_slide_keyword(self, slide_id: int, keyword_id: int) -> bool:
        """Associate a keyword with a slide."""
        pass
    
    @abstractmethod
    def unlink_slide_keyword(self, slide_id: int, keyword_id: int) -> bool:
        """Remove a keyword association from a slide."""
        pass
    
    @abstractmethod
    def get_keywords_for_slide(self, slide_id: int, kind: Optional[KeywordKind] = None) -> List[Keyword]:
        """Get keywords associated with a slide."""
        pass
    
    @abstractmethod
    def get_slides_for_keyword(self, keyword_id: int, project_id: Optional[int] = None) -> List[Slide]:
        """Get slides associated with a keyword."""
        pass
    
    @abstractmethod
    def replace_slide_keywords(self, slide_id: int, keyword_ids: List[int], kind: KeywordKind) -> bool:
        """Replace all keywords of a specific kind for a slide."""
        pass


class IElementKeywordService(ABC):
    """Interface for element-keyword association operations."""
    
    @abstractmethod
    def link_element_keyword(self, element_id: int, keyword_id: int) -> bool:
        """Associate a keyword with an element."""
        pass
    
    @abstractmethod
    def unlink_element_keyword(self, element_id: int, keyword_id: int) -> bool:
        """Remove a keyword association from an element."""
        pass
    
    @abstractmethod
    def get_keywords_for_element(self, element_id: int) -> List[Keyword]:
        """Get keywords associated with an element."""
        pass


class IFileIOService(ABC):
    """Interface for file system operations."""
    
    @abstractmethod
    def get_projects_root_folder(self) -> Path:
        """Get the root folder for all projects."""
        pass
    
    @abstractmethod
    def get_project_folder(self, project_name: str) -> Path:
        """Get the folder path for a specific project."""
        pass
    
    @abstractmethod
    def get_shared_folder(self) -> Path:
        """Get the shared folder path."""
        pass
    
    @abstractmethod
    def ensure_project_structure(self, project_name: str) -> Path:
        """Ensure project folder structure exists."""
        pass
    
    @abstractmethod
    def copy_files_to_project(self, source_files: List[Path], project_name: str) -> Dict[str, str]:
        """Copy files to a project, returning relative paths and checksums."""
        pass
    
    @abstractmethod
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        pass
    
    @abstractmethod
    def delete_project_folder(self, project_path: Path) -> bool:
        """Delete a project folder and all its contents."""
        pass


class IThumbnailCacheService(ABC):
    """Interface for thumbnail caching operations."""
    
    @abstractmethod
    def get_thumbnail(self, slide_id: int) -> Optional[Any]:
        """Get a thumbnail for a slide."""
        pass
    
    @abstractmethod
    def preload_thumbnails(self, slide_ids: List[int]) -> None:
        """Preload thumbnails for multiple slides."""
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """Clear the thumbnail cache."""
        pass
    
    @abstractmethod
    def get_cache_size(self) -> int:
        """Get the current cache size in bytes."""
        pass


class IExportService(ABC):
    """Interface for PowerPoint export operations."""
    
    @abstractmethod
    def export_slides(self, slide_ids: List[int], output_path: Path, 
                     mode: str = "powerpoint") -> Path:
        """Export slides to PowerPoint or PDF."""
        pass
    
    @abstractmethod
    def validate_slides_exist(self, slide_ids: List[int]) -> Tuple[bool, List[int]]:
        """Validate that slide source files exist."""
        pass
    
    @abstractmethod
    def get_export_progress(self) -> Tuple[int, int]:
        """Get current export progress (current, total)."""
        pass
    
    @abstractmethod
    def cancel_export(self) -> None:
        """Cancel the current export operation."""
        pass


class ISlideConverterService(ABC):
    """Interface for slide conversion operations."""
    
    @abstractmethod
    def convert_file(self, file_id: int, file_path: Path) -> bool:
        """Convert a PowerPoint file to slides."""
        pass
    
    @abstractmethod
    def get_conversion_progress(self) -> Tuple[int, int]:
        """Get current conversion progress (current, total)."""
        pass
    
    @abstractmethod
    def cancel_conversion(self) -> None:
        """Cancel the current conversion operation."""
        pass


class IDatabaseService(IProjectService, IFileService, ISlideService, 
                      IElementService, IKeywordService, ISlideKeywordService,
                      IElementKeywordService):
    """
    Combined interface for all database operations.
    
    This interface extends all the specific service interfaces to provide
    a complete database service contract.
    """
    
    @abstractmethod
    def begin_transaction(self) -> None:
        """Begin a database transaction."""
        pass
    
    @abstractmethod
    def commit_transaction(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the database connection."""
        pass