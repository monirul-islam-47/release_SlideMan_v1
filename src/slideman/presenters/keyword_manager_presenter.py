"""Presenter for the Keyword Manager page."""

import logging
from typing import List, Dict, Optional, Tuple, Set
from PySide6.QtCore import QObject, Signal, QThreadPool
from ...app_state import app_state
from ...models import Keyword, Slide, Element
from ...services.interfaces import (
    IDatabaseService, IKeywordService, ISlideService, 
    IElementService, ISlideKeywordService, IElementKeywordService
)
from ...services.exceptions import (
    DatabaseError, ValidationError, ResourceNotFoundError
)
from ...services.keyword_tasks import FindSimilarKeywordsWorker
from ...commands.merge_keywords_cmd import MergeKeywordsCmd
from ...commands.manage_slide_keyword import ReplaceSlideKeywordsCmd
from ...commands.manage_element_keyword import LinkElementKeywordCmd, UnlinkElementKeywordCmd
from .base_presenter import BasePresenter, IView


class IKeywordManagerView(IView):
    """Interface for keyword manager view."""
    
    def update_keyword_table(self, slides_data: List[Dict]) -> None:
        """Update the keyword table with slide data."""
        pass
        
    def update_suggestions(self, suggestions: List[Dict]) -> None:
        """Update merge suggestions list."""
        pass
        
    def update_element_list(self, elements: List[Dict]) -> None:
        """Update element list for selected slide."""
        pass
        
    def update_slide_preview(self, slide_id: int, elements: List[Element]) -> None:
        """Update slide preview with elements."""
        pass
        
    def clear_editing_panels(self) -> None:
        """Clear all editing panels."""
        pass
        
    def show_editing_panels(self) -> None:
        """Show editing panels."""
        pass
        
    def get_selected_slide_id(self) -> Optional[int]:
        """Get currently selected slide ID."""
        pass
        
    def get_selected_element_id(self) -> Optional[int]:
        """Get currently selected element ID."""
        pass
        
    def get_slide_tag_edits(self) -> Tuple[List[str], List[str]]:
        """Get current topic and title tags from edit widgets."""
        pass
        
    def get_element_tag_edits(self) -> List[str]:
        """Get current element tags from edit widget."""
        pass
        
    def update_status(self, message: str) -> None:
        """Update status message."""
        pass
        
    def update_statistics(self, total_keywords: int, unused_keywords: int) -> None:
        """Update keyword statistics."""
        pass


class KeywordManagerPresenter(BasePresenter):
    """Presenter for keyword management functionality."""
    
    # Signals
    keywordsUpdated = Signal()
    suggestionsFound = Signal(int)  # Number of suggestions
    
    def __init__(self, view: IKeywordManagerView, services: Dict[str, any]):
        """Initialize the presenter.
        
        Args:
            view: View implementing IKeywordManagerView
            services: Dictionary of services from registry
        """
        super().__init__(view, services)
        
        # Get required services
        self.db_service = services.get('database')
        self.keyword_service = services.get('database')  # Using unified interface
        self.slide_service = services.get('database')
        self.element_service = services.get('database')
        
        # Thread pool for background tasks
        self._thread_pool = QThreadPool()
        
        # Cache and state
        self._current_project_id: Optional[int] = None
        self._ignored_merge_pairs: Set[Tuple[int, int]] = set()
        self._slides_data_cache: List[Dict] = []
        
        # Connect to app state
        app_state.projectLoaded.connect(self._on_project_loaded)
        app_state.projectClosed.connect(self._on_project_closed)
        
    def load_project_data(self, project_id: int):
        """Load all keyword data for a project.
        
        Args:
            project_id: ID of project to load
        """
        try:
            self.view.set_busy(True, "Loading keyword data...")
            
            # Get all slides for the project
            slides = self.slide_service.get_slides_for_project(project_id)
            
            # Process slides with their keywords
            slides_data = []
            for slide in slides:
                slide_data = self._process_slide_data(slide)
                slides_data.append(slide_data)
            
            self._slides_data_cache = slides_data
            self._current_project_id = project_id
            
            # Update view
            self.view.update_keyword_table(slides_data)
            
            # Update statistics
            self._update_keyword_statistics()
            
        except DatabaseError as e:
            self.logger.error(f"Failed to load project data: {e}")
            self.view.show_error("Database Error", f"Failed to load keyword data: {str(e)}")
        finally:
            self.view.set_busy(False)
    
    def _process_slide_data(self, slide: Dict) -> Dict:
        """Process slide data with keywords and elements.
        
        Args:
            slide: Slide dictionary from database
            
        Returns:
            Processed slide data dictionary
        """
        try:
            # Get keywords for slide
            keywords = self.keyword_service.get_keywords_for_slide(slide['id'])
            
            topic_keywords = [kw for kw in keywords if kw.kind == 'topic']
            title_keywords = [kw for kw in keywords if kw.kind == 'title']
            
            # Get elements and their tags
            elements = self.element_service.get_elements_for_slide(slide['id'])
            element_tag_count = 0
            element_tag_names = []
            
            for element in elements:
                element_keywords = self.keyword_service.get_keywords_for_element(element.id)
                name_keywords = [kw for kw in element_keywords if kw.kind == 'name']
                
                if name_keywords:
                    element_tag_count += 1
                    for kw in name_keywords:
                        if kw.keyword not in element_tag_names:
                            element_tag_names.append(kw.keyword)
            
            return {
                'slide_id': slide['id'],
                'slide_identifier': f"{slide['file_name']} - Slide {slide['slide_index']}",
                'thumbnail_path': slide['thumbnail_path'],
                'topic_tags': topic_keywords,
                'title_tags': title_keywords,
                'element_tag_count': element_tag_count,
                'element_tag_names': element_tag_names
            }
            
        except DatabaseError as e:
            self.logger.error(f"Error processing slide {slide.get('id')}: {e}")
            # Return partial data
            return {
                'slide_id': slide['id'],
                'slide_identifier': f"{slide['file_name']} - Slide {slide['slide_index']}",
                'thumbnail_path': slide['thumbnail_path'],
                'topic_tags': [],
                'title_tags': [],
                'element_tag_count': 0,
                'element_tag_names': []
            }
    
    def apply_slide_tag_changes(self):
        """Apply tag changes to the selected slide."""
        slide_id = self.view.get_selected_slide_id()
        if not slide_id:
            self.view.show_warning("No Selection", "Please select a slide to edit.")
            return
            
        try:
            # Get edited tags
            topic_tags, title_tags = self.view.get_slide_tag_edits()
            
            # Create and execute command
            cmd = ReplaceSlideKeywordsCmd(
                slide_id=slide_id,
                topic_keywords=topic_tags,
                title_keywords=title_tags,
                description="Update slide keywords"
            )
            
            if app_state.undo_stack:
                app_state.undo_stack.push(cmd)
            else:
                cmd.redo()
            
            # Reload data
            self.load_project_data(self._current_project_id)
            
            self.view.show_info("Success", "Keywords updated successfully.")
            
        except (DatabaseError, ValidationError) as e:
            self.logger.error(f"Failed to apply tag changes: {e}")
            self.view.show_error("Update Failed", f"Failed to update keywords: {str(e)}")
    
    def find_similar_keywords(self):
        """Start background task to find similar keywords."""
        if not self._current_project_id:
            self.view.show_warning("No Project", "Please open a project first.")
            return
            
        try:
            self.view.update_status("Finding similar keywords...")
            
            # Create worker
            worker = FindSimilarKeywordsWorker(self.db_service, similarity_threshold=80)
            
            # Connect signals
            worker.signals.resultsReady.connect(self._handle_suggestions_ready)
            worker.signals.error.connect(self._handle_suggestions_error)
            
            # Start worker
            self._thread_pool.start(worker)
            
        except Exception as e:
            self.logger.error(f"Failed to start similarity search: {e}")
            self.view.show_error("Search Failed", f"Failed to search for similar keywords: {str(e)}")
    
    def _handle_suggestions_ready(self, suggestions: List[Dict]):
        """Handle keyword similarity suggestions."""
        # Filter out ignored pairs
        filtered = []
        for suggestion in suggestions:
            pair_key = (suggestion['from'].id, suggestion['to'].id)
            if pair_key not in self._ignored_merge_pairs:
                filtered.append(suggestion)
        
        self.view.update_suggestions(filtered)
        self.view.update_status(f"Found {len(filtered)} similar keyword pairs")
        self.suggestionsFound.emit(len(filtered))
    
    def _handle_suggestions_error(self, error_msg: str):
        """Handle error from similarity search."""
        self.view.update_status(f"Error: {error_msg}")
        self.view.show_error("Search Error", f"Error finding similar keywords: {error_msg}")
    
    def merge_selected_keywords(self, from_id: int, to_id: int, kind: str):
        """Merge two keywords.
        
        Args:
            from_id: Source keyword ID
            to_id: Target keyword ID  
            kind: Keyword kind (topic/title/name)
        """
        try:
            # Create and execute merge command
            cmd = MergeKeywordsCmd(
                from_keyword_id=from_id,
                to_keyword_id=to_id,
                kind=kind,
                description=f"Merge keywords"
            )
            
            if app_state.undo_stack:
                app_state.undo_stack.push(cmd)
            else:
                cmd.redo()
                
            # Add to ignored pairs
            self._ignored_merge_pairs.add((from_id, to_id))
            
            # Reload data
            self.load_project_data(self._current_project_id)
            
            self.view.show_info("Success", "Keywords merged successfully.")
            
        except (DatabaseError, ValidationError) as e:
            self.logger.error(f"Failed to merge keywords: {e}")
            self.view.show_error("Merge Failed", f"Failed to merge keywords: {str(e)}")
    
    def ignore_merge_suggestion(self, from_id: int, to_id: int):
        """Mark a merge suggestion as ignored.
        
        Args:
            from_id: Source keyword ID
            to_id: Target keyword ID
        """
        self._ignored_merge_pairs.add((from_id, to_id))
        # Refresh suggestions view
        self.find_similar_keywords()
    
    def load_slide_elements(self, slide_id: int):
        """Load elements for a slide.
        
        Args:
            slide_id: ID of slide to load elements for
        """
        try:
            elements = self.element_service.get_elements_for_slide(slide_id)
            
            # Process element data
            elements_data = []
            for element in elements:
                keywords = self.keyword_service.get_keywords_for_element(element.id)
                name_keywords = [kw for kw in keywords if kw.kind == 'name']
                
                elements_data.append({
                    'id': element.id,
                    'index': element.element_index,
                    'type': element.element_type,
                    'text': element.text_content[:50] if element.text_content else '',
                    'keywords': name_keywords
                })
            
            self.view.update_element_list(elements_data)
            self.view.update_slide_preview(slide_id, elements)
            
        except DatabaseError as e:
            self.logger.error(f"Failed to load slide elements: {e}")
            self.view.show_error("Load Failed", f"Failed to load slide elements: {str(e)}")
    
    def update_element_tags(self, element_id: int, tags: List[str]):
        """Update tags for an element.
        
        Args:
            element_id: ID of element to update
            tags: New list of tag names
        """
        try:
            # Get current tags
            current_keywords = self.keyword_service.get_keywords_for_element(element_id)
            current_names = {kw.keyword for kw in current_keywords if kw.kind == 'name'}
            
            new_names = set(tags)
            
            # Determine changes
            to_add = new_names - current_names
            to_remove = current_names - new_names
            
            # Execute commands
            for name in to_add:
                keyword_id = self.keyword_service.get_or_create_keyword(name, 'name')
                cmd = LinkElementKeywordCmd(element_id, keyword_id, "Add element tag")
                if app_state.undo_stack:
                    app_state.undo_stack.push(cmd)
                else:
                    cmd.redo()
            
            for name in to_remove:
                keyword = next((kw for kw in current_keywords if kw.keyword == name), None)
                if keyword:
                    cmd = UnlinkElementKeywordCmd(element_id, keyword.id, "Remove element tag")
                    if app_state.undo_stack:
                        app_state.undo_stack.push(cmd)
                    else:
                        cmd.redo()
            
            # Reload current slide elements
            slide_id = self.view.get_selected_slide_id()
            if slide_id:
                self.load_slide_elements(slide_id)
                
        except (DatabaseError, ValidationError) as e:
            self.logger.error(f"Failed to update element tags: {e}")
            self.view.show_error("Update Failed", f"Failed to update element tags: {str(e)}")
    
    def export_keywords_to_csv(self, file_path: str):
        """Export keywords to CSV file.
        
        Args:
            file_path: Path to save CSV file
        """
        try:
            import csv
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=['slide_id', 'slide', 'topic_tags', 'title_tags', 'element_tags']
                )
                writer.writeheader()
                
                for slide_data in self._slides_data_cache:
                    writer.writerow({
                        'slide_id': slide_data['slide_id'],
                        'slide': slide_data['slide_identifier'],
                        'topic_tags': ', '.join([kw.keyword for kw in slide_data['topic_tags']]),
                        'title_tags': ', '.join([kw.keyword for kw in slide_data['title_tags']]),
                        'element_tags': ', '.join(slide_data['element_tag_names'])
                    })
                    
            self.view.show_info("Export Complete", f"Keywords exported to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export keywords: {e}")
            self.view.show_error("Export Failed", f"Failed to export keywords: {str(e)}")
    
    def _update_keyword_statistics(self):
        """Update keyword usage statistics."""
        try:
            if not self._current_project_id:
                return
                
            # Get all keywords for project
            all_keywords = self.keyword_service.get_keywords_for_project(self._current_project_id)
            total = len(all_keywords)
            
            # Count unused keywords
            unused = 0
            for keyword in all_keywords:
                slide_count = self.keyword_service.count_slides_with_keyword(keyword.id)
                element_count = self.keyword_service.count_elements_with_keyword(keyword.id)
                
                if slide_count == 0 and element_count == 0:
                    unused += 1
            
            self.view.update_statistics(total, unused)
            
        except DatabaseError as e:
            self.logger.error(f"Failed to update statistics: {e}")
    
    def _on_project_loaded(self):
        """Handle project loaded event."""
        project = app_state.current_project
        if project:
            self.load_project_data(project.id)
    
    def _on_project_closed(self):
        """Handle project closed event."""
        self._current_project_id = None
        self._slides_data_cache.clear()
        self._ignored_merge_pairs.clear()
        
        self.view.update_keyword_table([])
        self.view.update_suggestions([])
        self.view.clear_editing_panels()
        self.view.update_statistics(0, 0)