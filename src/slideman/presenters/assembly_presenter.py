"""Presenter for the Assembly page."""

import logging
from typing import List, Dict, Optional, Set
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap
from ...app_state import app_state
from ...models import Slide
from ...services.interfaces import (
    IDatabaseService, ISlideService, IThumbnailCacheService
)
from ...services.exceptions import DatabaseError
from .base_presenter import BasePresenter, IView


class IAssemblyView(IView):
    """Interface for assembly view."""
    
    def add_slide_to_preview(self, slide_id: int, thumbnail: QPixmap, metadata: Dict) -> bool:
        """Add a slide to the assembly preview.
        
        Args:
            slide_id: ID of slide to add
            thumbnail: Slide thumbnail
            metadata: Additional slide metadata
            
        Returns:
            True if slide was added, False if already present
        """
        pass
        
    def remove_slide_from_preview(self, slide_id: int) -> bool:
        """Remove a slide from the assembly preview.
        
        Args:
            slide_id: ID of slide to remove
            
        Returns:
            True if slide was removed
        """
        pass
        
    def clear_preview(self) -> None:
        """Clear all slides from preview."""
        pass
        
    def get_assembly_order(self) -> List[int]:
        """Get current slide order in assembly.
        
        Returns:
            List of slide IDs in order
        """
        return []
        
    def update_slide_count(self, count: int) -> None:
        """Update the displayed slide count."""
        pass
        
    def set_assembly_order(self, order: List[int]) -> None:
        """Set the slide order in assembly preview."""
        pass


class AssemblyPresenter(BasePresenter):
    """Presenter for slide assembly functionality."""
    
    # Signals
    assemblyChanged = Signal(list)  # List of slide IDs in assembly
    slideCountChanged = Signal(int)  # Number of slides in assembly
    
    def __init__(self, view: IAssemblyView, services: Dict[str, any]):
        """Initialize the presenter.
        
        Args:
            view: View implementing IAssemblyView
            services: Dictionary of services from registry
        """
        super().__init__(view, services)
        
        # Get required services
        self.db_service = services.get('database')
        self.slide_service = services.get('database')
        self.thumbnail_cache = services.get('thumbnail_cache')
        
        # State
        self._assembly_slides: Set[int] = set()
        self._slide_order: List[int] = []
        
        # Connect to app state
        app_state.slidesUpdated.connect(self._on_slides_updated)
        app_state.projectClosed.connect(self._on_project_closed)
        
        # Load any existing assembly state
        self._load_assembly_state()
    
    def add_slide_to_assembly(self, slide_id: int) -> bool:
        """Add a slide to the assembly.
        
        Args:
            slide_id: ID of slide to add
            
        Returns:
            True if slide was added, False if already present
        """
        if slide_id in self._assembly_slides:
            return False
            
        try:
            # Get slide data
            slide = self.slide_service.get_slide_by_id(slide_id)
            if not slide:
                raise ValueError(f"Slide {slide_id} not found")
            
            # Get thumbnail
            thumbnail = self.thumbnail_cache.get_thumbnail(slide_id)
            if thumbnail is None or thumbnail.isNull():
                self.logger.warning(f"No thumbnail for slide {slide_id}")
                thumbnail = self.thumbnail_cache.get_placeholder()
            
            # Prepare metadata
            metadata = {
                'file_name': slide.file_name,
                'slide_index': slide.slide_index,
                'title': slide.title or '',
                'KeywordId': None  # For compatibility with preview widget
            }
            
            # Add to view
            if self.view.add_slide_to_preview(slide_id, thumbnail, metadata):
                self._assembly_slides.add(slide_id)
                self._slide_order.append(slide_id)
                
                # Update state
                self._save_assembly_state()
                self.view.update_slide_count(len(self._assembly_slides))
                
                # Emit signals
                self.assemblyChanged.emit(self._slide_order)
                self.slideCountChanged.emit(len(self._assembly_slides))
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add slide {slide_id}: {e}")
            self.view.show_error("Add Failed", f"Failed to add slide: {str(e)}")
            
        return False
    
    def add_slides_to_assembly(self, slide_ids: List[int]):
        """Add multiple slides to the assembly.
        
        Args:
            slide_ids: List of slide IDs to add
        """
        added_count = 0
        
        try:
            self.view.set_busy(True, "Adding slides to assembly...")
            
            for slide_id in slide_ids:
                if self.add_slide_to_assembly(slide_id):
                    added_count += 1
            
            if added_count > 0:
                self.view.show_info(
                    "Slides Added", 
                    f"Added {added_count} slide(s) to assembly."
                )
            else:
                self.view.show_warning(
                    "No Slides Added",
                    "All selected slides are already in the assembly."
                )
                
        finally:
            self.view.set_busy(False)
    
    def remove_slide_from_assembly(self, slide_id: int) -> bool:
        """Remove a slide from the assembly.
        
        Args:
            slide_id: ID of slide to remove
            
        Returns:
            True if slide was removed
        """
        if slide_id not in self._assembly_slides:
            return False
            
        if self.view.remove_slide_from_preview(slide_id):
            self._assembly_slides.discard(slide_id)
            self._slide_order = [sid for sid in self._slide_order if sid != slide_id]
            
            # Update state
            self._save_assembly_state()
            self.view.update_slide_count(len(self._assembly_slides))
            
            # Emit signals
            self.assemblyChanged.emit(self._slide_order)
            self.slideCountChanged.emit(len(self._assembly_slides))
            
            return True
            
        return False
    
    def remove_selected_slides(self):
        """Remove currently selected slides from assembly."""
        # Get selected slides from the current order in view
        current_order = self.view.get_assembly_order()
        selected_ids = []  # View should provide selected IDs
        
        if not selected_ids:
            self.view.show_warning("No Selection", "Please select slides to remove.")
            return
            
        removed_count = 0
        for slide_id in selected_ids:
            if self.remove_slide_from_assembly(slide_id):
                removed_count += 1
        
        if removed_count > 0:
            self.view.show_info(
                "Slides Removed",
                f"Removed {removed_count} slide(s) from assembly."
            )
    
    def clear_assembly(self):
        """Clear all slides from the assembly."""
        if not self._assembly_slides:
            return
            
        # Confirm with user
        if not self.view.ask_confirmation(
            "Clear Assembly",
            "Remove all slides from the assembly?"
        ):
            return
            
        # Clear view
        self.view.clear_preview()
        
        # Clear state
        self._assembly_slides.clear()
        self._slide_order.clear()
        
        # Update state
        self._save_assembly_state()
        self.view.update_slide_count(0)
        
        # Emit signals
        self.assemblyChanged.emit([])
        self.slideCountChanged.emit(0)
        
        self.view.show_info("Assembly Cleared", "All slides removed from assembly.")
    
    def update_slide_order(self, new_order: List[int]):
        """Update the order of slides in the assembly.
        
        Args:
            new_order: New slide order
        """
        # Validate order contains same slides
        if set(new_order) != self._assembly_slides:
            self.logger.warning("Invalid slide order - slides don't match assembly")
            return
            
        self._slide_order = new_order
        
        # Update state
        self._save_assembly_state()
        
        # Emit signal
        self.assemblyChanged.emit(self._slide_order)
    
    def get_assembly_slides(self) -> List[Dict]:
        """Get detailed information about slides in assembly.
        
        Returns:
            List of slide data dictionaries in assembly order
        """
        slides_data = []
        
        for slide_id in self._slide_order:
            try:
                slide = self.slide_service.get_slide_by_id(slide_id)
                if slide:
                    slides_data.append({
                        'id': slide_id,
                        'file_name': slide.file_name,
                        'slide_index': slide.slide_index,
                        'title': slide.title or f"Slide {slide.slide_index}",
                        'thumbnail_path': self.thumbnail_cache.get_thumbnail_path(slide_id)
                    })
            except DatabaseError as e:
                self.logger.error(f"Failed to get slide {slide_id}: {e}")
                
        return slides_data
    
    def move_slide_up(self, slide_id: int):
        """Move a slide up in the assembly order.
        
        Args:
            slide_id: ID of slide to move
        """
        try:
            index = self._slide_order.index(slide_id)
            if index > 0:
                # Swap with previous
                self._slide_order[index], self._slide_order[index-1] = \
                    self._slide_order[index-1], self._slide_order[index]
                
                # Update view
                self.view.set_assembly_order(self._slide_order)
                
                # Save state
                self._save_assembly_state()
                self.assemblyChanged.emit(self._slide_order)
                
        except ValueError:
            self.logger.warning(f"Slide {slide_id} not in assembly")
    
    def move_slide_down(self, slide_id: int):
        """Move a slide down in the assembly order.
        
        Args:
            slide_id: ID of slide to move
        """
        try:
            index = self._slide_order.index(slide_id)
            if index < len(self._slide_order) - 1:
                # Swap with next
                self._slide_order[index], self._slide_order[index+1] = \
                    self._slide_order[index+1], self._slide_order[index]
                
                # Update view
                self.view.set_assembly_order(self._slide_order)
                
                # Save state
                self._save_assembly_state()
                self.assemblyChanged.emit(self._slide_order)
                
        except ValueError:
            self.logger.warning(f"Slide {slide_id} not in assembly")
    
    def _load_assembly_state(self):
        """Load assembly state from app state."""
        order = app_state.get_assembly_order()
        if order:
            self._slide_order = order
            self._assembly_slides = set(order)
            
            # Populate view
            for slide_id in order:
                try:
                    slide = self.slide_service.get_slide_by_id(slide_id)
                    if slide:
                        thumbnail = self.thumbnail_cache.get_thumbnail(slide_id)
                        metadata = {
                            'file_name': slide.file_name,
                            'slide_index': slide.slide_index,
                            'title': slide.title or '',
                            'KeywordId': None
                        }
                        self.view.add_slide_to_preview(slide_id, thumbnail, metadata)
                except Exception as e:
                    self.logger.error(f"Failed to load slide {slide_id}: {e}")
            
            self.view.update_slide_count(len(self._assembly_slides))
    
    def _save_assembly_state(self):
        """Save assembly state to app state."""
        app_state.set_assembly_order(self._slide_order)
    
    def _on_slides_updated(self):
        """Handle slides updated event."""
        # Check if any assembly slides were deleted
        removed = []
        for slide_id in self._assembly_slides:
            try:
                slide = self.slide_service.get_slide_by_id(slide_id)
                if not slide:
                    removed.append(slide_id)
            except:
                removed.append(slide_id)
        
        # Remove deleted slides
        for slide_id in removed:
            self.remove_slide_from_assembly(slide_id)
    
    def _on_project_closed(self):
        """Handle project closed event."""
        # Clear assembly
        self.view.clear_preview()
        self._assembly_slides.clear()
        self._slide_order.clear()
        self.view.update_slide_count(0)
        
        # Clear saved state
        app_state.set_assembly_order([])