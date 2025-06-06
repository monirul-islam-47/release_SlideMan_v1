"""Presenter for the Delivery page."""

import logging
from pathlib import Path
from typing import List, Dict, Optional
from PySide6.QtCore import QObject, Signal, QThreadPool
from PySide6.QtGui import QPixmap
from ...app_state import app_state
from ...services.interfaces import (
    IDatabaseService, ISlideService, IThumbnailCacheService,
    IExportService
)
from ...services.exceptions import (
    DatabaseError, ExportError, FileOperationError
)
from ...services.export_service import ExportWorker
from .base_presenter import BasePresenter, IView


class IDeliveryView(IView):
    """Interface for delivery view."""
    
    def update_preview(self, slides: List[Dict]) -> None:
        """Update the delivery preview with slides."""
        pass
        
    def clear_preview(self) -> None:
        """Clear the delivery preview."""
        pass
        
    def update_export_progress(self, progress: int, message: str = "") -> None:
        """Update export progress.
        
        Args:
            progress: Progress percentage (0-100)
            message: Optional status message
        """
        pass
        
    def show_export_complete(self, file_path: str) -> None:
        """Show export completion message."""
        pass
        
    def get_export_settings(self) -> Dict[str, any]:
        """Get current export settings.
        
        Returns:
            Dictionary with export settings
        """
        return {}
        
    def set_export_enabled(self, enabled: bool) -> None:
        """Enable or disable export functionality."""
        pass
        
    def get_assembly_order(self) -> List[int]:
        """Get current slide order for export."""
        return []


class DeliveryPresenter(BasePresenter):
    """Presenter for presentation delivery/export functionality."""
    
    # Signals
    exportStarted = Signal()
    exportProgress = Signal(int, str)  # progress, message
    exportCompleted = Signal(str)  # file path
    exportFailed = Signal(str)  # error message
    
    def __init__(self, view: IDeliveryView, services: Dict[str, any]):
        """Initialize the presenter.
        
        Args:
            view: View implementing IDeliveryView
            services: Dictionary of services from registry
        """
        super().__init__(view, services)
        
        # Get required services
        self.db_service = services.get('database')
        self.slide_service = services.get('database')
        self.thumbnail_cache = services.get('thumbnail_cache')
        self.export_service = services.get('export_service')
        
        # Thread pool for export operations
        self._thread_pool = QThreadPool()
        
        # State
        self._current_export_worker: Optional[ExportWorker] = None
        self._assembly_slides: List[int] = []
        
        # Connect to app state
        app_state.assemblyOrderChanged.connect(self._on_assembly_changed)
        app_state.projectClosed.connect(self._on_project_closed)
        
        # Load initial assembly
        self._load_assembly()
    
    def _load_assembly(self):
        """Load current assembly from app state."""
        order = app_state.get_assembly_order()
        if order:
            self._update_preview(order)
            self._assembly_slides = order
            self.view.set_export_enabled(True)
        else:
            self.view.set_export_enabled(False)
    
    def _update_preview(self, slide_ids: List[int]):
        """Update the preview with given slides.
        
        Args:
            slide_ids: List of slide IDs to show
        """
        try:
            slides_data = []
            
            for slide_id in slide_ids:
                try:
                    slide = self.slide_service.get_slide_by_id(slide_id)
                    if slide:
                        thumbnail = self.thumbnail_cache.get_thumbnail(slide_id)
                        
                        slides_data.append({
                            'id': slide_id,
                            'thumbnail': thumbnail,
                            'file_name': slide.file_name,
                            'slide_index': slide.slide_index,
                            'title': slide.title or f"Slide {slide.slide_index}",
                            'metadata': {'KeywordId': None}  # For widget compatibility
                        })
                except DatabaseError as e:
                    self.logger.error(f"Failed to load slide {slide_id}: {e}")
            
            self.view.update_preview(slides_data)
            
        except Exception as e:
            self.logger.error(f"Failed to update preview: {e}")
            self.view.show_error("Preview Error", f"Failed to update preview: {str(e)}")
    
    def export_presentation(self):
        """Export the current assembly as a PowerPoint presentation."""
        if not self._assembly_slides:
            self.view.show_warning("No Slides", "No slides in assembly to export.")
            return
        
        # Get export settings
        settings = self.view.get_export_settings()
        
        # Get output path
        project_name = app_state.current_project.name if app_state.current_project else "presentation"
        suggested_name = f"{project_name}_export.pptx"
        
        output_path = self.view.ask_save_file(
            "Export Presentation",
            suggested_name,
            "PowerPoint Files (*.pptx);;All Files (*.*)"
        )
        
        if not output_path:
            return
            
        # Ensure .pptx extension
        output_path = Path(output_path)
        if output_path.suffix.lower() != '.pptx':
            output_path = output_path.with_suffix('.pptx')
        
        try:
            # Disable export during operation
            self.view.set_export_enabled(False)
            
            # Get current order from view (in case it was reordered)
            current_order = self.view.get_assembly_order()
            if current_order:
                self._assembly_slides = current_order
            
            # Create export worker
            self._current_export_worker = ExportWorker(
                self.export_service,
                self._assembly_slides,
                str(output_path),
                settings.get('include_notes', True),
                settings.get('optimize_size', False)
            )
            
            # Connect signals
            self._current_export_worker.signals.started.connect(self._on_export_started)
            self._current_export_worker.signals.progress.connect(self._on_export_progress)
            self._current_export_worker.signals.result.connect(self._on_export_completed)
            self._current_export_worker.signals.error.connect(self._on_export_error)
            self._current_export_worker.signals.finished.connect(self._on_export_finished)
            
            # Start export
            self._thread_pool.start(self._current_export_worker)
            
            self.exportStarted.emit()
            
        except Exception as e:
            self.logger.error(f"Failed to start export: {e}")
            self.view.show_error("Export Failed", f"Failed to start export: {str(e)}")
            self.view.set_export_enabled(True)
    
    def cancel_export(self):
        """Cancel the current export operation."""
        if self._current_export_worker:
            self._current_export_worker.cancel()
            self.view.show_info("Export Cancelled", "Export operation was cancelled.")
    
    def _on_export_started(self):
        """Handle export started signal."""
        self.view.update_export_progress(0, "Starting export...")
    
    def _on_export_progress(self, progress: int):
        """Handle export progress signal.
        
        Args:
            progress: Progress percentage
        """
        message = f"Exporting... {progress}%"
        self.view.update_export_progress(progress, message)
        self.exportProgress.emit(progress, message)
    
    def _on_export_completed(self, file_path: str):
        """Handle export completed signal.
        
        Args:
            file_path: Path to exported file
        """
        self.view.show_export_complete(file_path)
        self.exportCompleted.emit(file_path)
        
        # Ask if user wants to open the file
        if self.view.ask_confirmation("Open File?", 
                                     "Export complete. Open the presentation?"):
            self._open_file(file_path)
    
    def _on_export_error(self, error: Exception):
        """Handle export error signal.
        
        Args:
            error: The exception that occurred
        """
        error_msg = str(error)
        self.logger.error(f"Export failed: {error}", exc_info=True)
        
        if isinstance(error, ExportError):
            self.view.show_error("Export Failed", f"Failed to export presentation:\n{error_msg}")
        elif isinstance(error, FileOperationError):
            self.view.show_error("File Error", f"File operation failed:\n{error_msg}")
        else:
            self.view.show_error("Export Error", f"An error occurred during export:\n{error_msg}")
            
        self.exportFailed.emit(error_msg)
    
    def _on_export_finished(self):
        """Handle export finished signal."""
        self._current_export_worker = None
        self.view.set_export_enabled(True)
        self.view.update_export_progress(0, "")
    
    def _open_file(self, file_path: str):
        """Open the exported file with default application.
        
        Args:
            file_path: Path to file to open
        """
        try:
            import os
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{file_path}"')
            else:  # Linux
                os.system(f'xdg-open "{file_path}"')
                
        except Exception as e:
            self.logger.error(f"Failed to open file: {e}")
            self.view.show_warning("Open Failed", 
                                  f"Could not open file. Please open it manually:\n{file_path}")
    
    def update_slide_order(self, new_order: List[int]):
        """Update the order of slides for export.
        
        Args:
            new_order: New slide order
        """
        self._assembly_slides = new_order
        app_state.set_assembly_order(new_order)
    
    def get_export_preview_data(self) -> Dict[str, any]:
        """Get data for export preview.
        
        Returns:
            Dictionary with preview information
        """
        total_slides = len(self._assembly_slides)
        
        # Calculate estimated file size (rough estimate)
        estimated_size_mb = total_slides * 0.5  # Assume ~0.5MB per slide
        
        # Get unique source files
        source_files = set()
        for slide_id in self._assembly_slides:
            try:
                slide = self.slide_service.get_slide_by_id(slide_id)
                if slide:
                    source_files.add(slide.file_name)
            except:
                pass
        
        return {
            'total_slides': total_slides,
            'source_files': len(source_files),
            'estimated_size_mb': estimated_size_mb,
            'has_notes': any(self._check_slide_has_notes(sid) for sid in self._assembly_slides)
        }
    
    def _check_slide_has_notes(self, slide_id: int) -> bool:
        """Check if a slide has notes.
        
        Args:
            slide_id: ID of slide to check
            
        Returns:
            True if slide has notes
        """
        try:
            slide = self.slide_service.get_slide_by_id(slide_id)
            return bool(slide and slide.notes)
        except:
            return False
    
    def _on_assembly_changed(self, order: List[int]):
        """Handle assembly order changed event.
        
        Args:
            order: New slide order
        """
        self._assembly_slides = order
        self._update_preview(order)
        self.view.set_export_enabled(bool(order))
    
    def _on_project_closed(self):
        """Handle project closed event."""
        # Cancel any ongoing export
        if self._current_export_worker:
            self._current_export_worker.cancel()
        
        # Clear state
        self._assembly_slides.clear()
        self.view.clear_preview()
        self.view.set_export_enabled(False)