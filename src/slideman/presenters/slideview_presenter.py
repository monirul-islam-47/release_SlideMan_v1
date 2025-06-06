"""Presenter for the SlideView page."""

import logging
from typing import List, Dict, Optional, Set
from PySide6.QtCore import QObject, Signal
from ...app_state import app_state
from ...models import Slide, Keyword
from ...services.interfaces import (
    IDatabaseService, ISlideService, IKeywordService,
    ISlideKeywordService, IThumbnailCacheService
)
from ...services.exceptions import (
    DatabaseError, ValidationError, ResourceNotFoundError
)
from ...commands.manage_slide_keyword import (
    AddSlideKeywordCmd, RemoveSlideKeywordCmd, ReplaceSlideKeywordsCmd
)
from .base_presenter import BasePresenter, IView


class ISlideViewView(IView):
    """Interface for slide view."""
    
    def update_slide_list(self, slides: List[Dict]) -> None:
        """Update the slide list display."""
        pass
        
    def update_keyword_filter(self, keywords: List[Keyword]) -> None:
        """Update available keywords for filtering."""
        pass
        
    def clear_slide_list(self) -> None:
        """Clear the slide list."""
        pass
        
    def set_filter_state(self, has_filters: bool) -> None:
        """Update UI based on filter state."""
        pass
        
    def get_selected_slide_ids(self) -> List[int]:
        """Get currently selected slide IDs."""
        return []
        
    def get_current_filters(self) -> Dict[str, any]:
        """Get current filter settings."""
        return {}


class SlideViewPresenter(BasePresenter):
    """Presenter for slide viewing and filtering functionality."""
    
    # Signals
    slidesLoaded = Signal(int)  # Number of slides loaded
    selectionChanged = Signal(list)  # Selected slide IDs
    
    def __init__(self, view: ISlideViewView, services: Dict[str, any]):
        """Initialize the presenter.
        
        Args:
            view: View implementing ISlideViewView
            services: Dictionary of services from registry
        """
        super().__init__(view, services)
        
        # Get required services
        self.db_service = services.get('database')
        self.slide_service = services.get('database')
        self.keyword_service = services.get('database')
        self.thumbnail_cache = services.get('thumbnail_cache')
        
        # State
        self._current_project_id: Optional[int] = None
        self._all_slides: List[Dict] = []
        self._filtered_slides: List[Dict] = []
        self._available_keywords: Dict[str, List[Keyword]] = {
            'topic': [],
            'title': []
        }
        
        # Connect to app state
        app_state.projectLoaded.connect(self._on_project_loaded)
        app_state.projectClosed.connect(self._on_project_closed)
        app_state.slidesUpdated.connect(self._on_slides_updated)
    
    def load_project_slides(self, project_id: int):
        """Load all slides for a project.
        
        Args:
            project_id: ID of project to load
        """
        try:
            self.view.set_busy(True, "Loading slides...")
            
            # Get all slides
            slides = self.slide_service.get_slides_for_project(project_id)
            
            # Process slides
            self._all_slides = []
            for slide in slides:
                slide_data = self._process_slide(slide)
                self._all_slides.append(slide_data)
            
            self._current_project_id = project_id
            
            # Load available keywords for filtering
            self._load_available_keywords(project_id)
            
            # Update view
            self._filtered_slides = self._all_slides.copy()
            self.view.update_slide_list(self._filtered_slides)
            
            self.slidesLoaded.emit(len(self._filtered_slides))
            
        except DatabaseError as e:
            self.logger.error(f"Failed to load slides: {e}")
            self.view.show_error("Database Error", f"Failed to load slides: {str(e)}")
        finally:
            self.view.set_busy(False)
    
    def _process_slide(self, slide: Dict) -> Dict:
        """Process slide data for display.
        
        Args:
            slide: Raw slide data from database
            
        Returns:
            Processed slide data
        """
        try:
            # Get keywords
            keywords = self.keyword_service.get_keywords_for_slide(slide['id'])
            topic_keywords = [kw for kw in keywords if kw.kind == 'topic']
            title_keywords = [kw for kw in keywords if kw.kind == 'title']
            
            # Get thumbnail
            thumbnail_path = self.thumbnail_cache.get_thumbnail_path(slide['id'])
            
            return {
                'id': slide['id'],
                'file_name': slide['file_name'],
                'slide_index': slide['slide_index'],
                'title': slide.get('title', ''),
                'notes': slide.get('notes', ''),
                'thumbnail_path': thumbnail_path,
                'topic_keywords': topic_keywords,
                'title_keywords': title_keywords,
                'identifier': f"{slide['file_name']} - Slide {slide['slide_index']}"
            }
            
        except Exception as e:
            self.logger.error(f"Error processing slide {slide.get('id')}: {e}")
            return {
                'id': slide['id'],
                'file_name': slide['file_name'],
                'slide_index': slide['slide_index'],
                'title': slide.get('title', ''),
                'notes': '',
                'thumbnail_path': None,
                'topic_keywords': [],
                'title_keywords': [],
                'identifier': f"{slide['file_name']} - Slide {slide['slide_index']}"
            }
    
    def _load_available_keywords(self, project_id: int):
        """Load available keywords for filtering.
        
        Args:
            project_id: Project ID
        """
        try:
            # Get all keywords used in the project
            all_keywords = self.keyword_service.get_keywords_for_project(project_id)
            
            # Separate by kind
            self._available_keywords = {
                'topic': [kw for kw in all_keywords if kw.kind == 'topic'],
                'title': [kw for kw in all_keywords if kw.kind == 'title']
            }
            
            # Update view
            self.view.update_keyword_filter(all_keywords)
            
        except DatabaseError as e:
            self.logger.error(f"Failed to load keywords: {e}")
    
    def apply_filters(self):
        """Apply current filters to slide list."""
        filters = self.view.get_current_filters()
        
        self._filtered_slides = []
        
        for slide in self._all_slides:
            if self._slide_matches_filters(slide, filters):
                self._filtered_slides.append(slide)
        
        # Update view
        self.view.update_slide_list(self._filtered_slides)
        self.view.set_filter_state(bool(filters))
        
        self.slidesLoaded.emit(len(self._filtered_slides))
    
    def _slide_matches_filters(self, slide: Dict, filters: Dict) -> bool:
        """Check if slide matches current filters.
        
        Args:
            slide: Slide data
            filters: Filter criteria
            
        Returns:
            True if slide matches all filters
        """
        # Text filter
        text_filter = filters.get('text', '').lower()
        if text_filter:
            searchable = [
                slide.get('title', ''),
                slide.get('notes', ''),
                slide.get('file_name', ''),
                str(slide.get('slide_index', ''))
            ]
            # Add keyword text
            for kw in slide.get('topic_keywords', []):
                searchable.append(kw.keyword)
            for kw in slide.get('title_keywords', []):
                searchable.append(kw.keyword)
                
            text_found = any(text_filter in text.lower() for text in searchable)
            if not text_found:
                return False
        
        # Keyword filters
        topic_filter = filters.get('topic_keywords', [])
        if topic_filter:
            slide_topics = {kw.id for kw in slide.get('topic_keywords', [])}
            if not any(kw_id in slide_topics for kw_id in topic_filter):
                return False
        
        title_filter = filters.get('title_keywords', [])
        if title_filter:
            slide_titles = {kw.id for kw in slide.get('title_keywords', [])}
            if not any(kw_id in slide_titles for kw_id in title_filter):
                return False
        
        # File filter
        file_filter = filters.get('file_name')
        if file_filter and file_filter != "All Files":
            if slide.get('file_name') != file_filter:
                return False
        
        return True
    
    def clear_filters(self):
        """Clear all filters and show all slides."""
        self._filtered_slides = self._all_slides.copy()
        self.view.update_slide_list(self._filtered_slides)
        self.view.set_filter_state(False)
        self.slidesLoaded.emit(len(self._filtered_slides))
    
    def add_keyword_to_selected(self, keyword: str, kind: str):
        """Add keyword to selected slides.
        
        Args:
            keyword: Keyword text
            kind: Keyword kind (topic/title)
        """
        selected_ids = self.view.get_selected_slide_ids()
        if not selected_ids:
            self.view.show_warning("No Selection", "Please select slides to tag.")
            return
            
        try:
            # Get or create keyword
            keyword_id = self.keyword_service.get_or_create_keyword(keyword, kind)
            
            # Add to each selected slide
            for slide_id in selected_ids:
                cmd = AddSlideKeywordCmd(
                    slide_id=slide_id,
                    keyword_id=keyword_id,
                    description=f"Add {kind} keyword to slide"
                )
                
                if app_state.undo_stack:
                    app_state.undo_stack.push(cmd)
                else:
                    cmd.redo()
            
            # Reload slides
            self.load_project_slides(self._current_project_id)
            
            self.view.show_info("Success", f"Added '{keyword}' to {len(selected_ids)} slides.")
            
        except (DatabaseError, ValidationError) as e:
            self.logger.error(f"Failed to add keyword: {e}")
            self.view.show_error("Operation Failed", f"Failed to add keyword: {str(e)}")
    
    def remove_keyword_from_selected(self, keyword_id: int):
        """Remove keyword from selected slides.
        
        Args:
            keyword_id: ID of keyword to remove
        """
        selected_ids = self.view.get_selected_slide_ids()
        if not selected_ids:
            self.view.show_warning("No Selection", "Please select slides to untag.")
            return
            
        try:
            # Remove from each selected slide
            for slide_id in selected_ids:
                cmd = RemoveSlideKeywordCmd(
                    slide_id=slide_id,
                    keyword_id=keyword_id,
                    description="Remove keyword from slide"
                )
                
                if app_state.undo_stack:
                    app_state.undo_stack.push(cmd)
                else:
                    cmd.redo()
            
            # Reload slides
            self.load_project_slides(self._current_project_id)
            
            self.view.show_info("Success", f"Removed keyword from {len(selected_ids)} slides.")
            
        except (DatabaseError, ValidationError) as e:
            self.logger.error(f"Failed to remove keyword: {e}")
            self.view.show_error("Operation Failed", f"Failed to remove keyword: {str(e)}")
    
    def get_selected_slides(self) -> List[Dict]:
        """Get data for currently selected slides.
        
        Returns:
            List of slide data dictionaries
        """
        selected_ids = self.view.get_selected_slide_ids()
        return [
            slide for slide in self._filtered_slides 
            if slide['id'] in selected_ids
        ]
    
    def get_unique_files(self) -> List[str]:
        """Get list of unique file names in current project.
        
        Returns:
            Sorted list of file names
        """
        files = set()
        for slide in self._all_slides:
            files.add(slide.get('file_name', ''))
        return sorted(list(files))
    
    def _on_project_loaded(self):
        """Handle project loaded event."""
        project = app_state.current_project
        if project:
            self.load_project_slides(project.id)
    
    def _on_project_closed(self):
        """Handle project closed event."""
        self._current_project_id = None
        self._all_slides.clear()
        self._filtered_slides.clear()
        self._available_keywords.clear()
        
        self.view.clear_slide_list()
        self.view.update_keyword_filter([])
    
    def _on_slides_updated(self):
        """Handle slides updated event."""
        if self._current_project_id:
            self.load_project_slides(self._current_project_id)