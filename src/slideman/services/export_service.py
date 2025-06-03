# src/slideman/services/export_service.py

import logging
import os
from pathlib import Path
from typing import List, Optional, Tuple, Literal

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

try:
    import pythoncom
    import win32com.client
    from pywintypes import com_error
    HAS_COM = True
except ImportError:
    HAS_COM = False

from .database_worker import DatabaseWorker
from .exceptions import (
    DatabaseError, PowerPointError, COMInitializationError,
    PresentationAccessError, SlideExportError, ResourceNotFoundError
)

logger = logging.getLogger(__name__)


class ExportWorkerSignals(QObject):
    """
    Defines signals available from the export worker thread.
    """
    exportProgress = Signal(int, int)  # current, total
    exportFinished = Signal(str)       # output path or success message
    exportError = Signal(str)          # error message


class ExportWorker(QRunnable):
    """
    Thread-safe worker for exporting PowerPoint presentations.
    
    Args:
        ordered_slide_ids: List of slide IDs in the order they should appear
        output_mode: Either 'open' (leave open in PowerPoint) or 'save' (save to file)
        output_path: Path to save the presentation (required if output_mode is 'save')
        db_path: Path to database for worker connection
    """
    
    def __init__(
            self, 
            ordered_slide_ids: List[int], 
            output_mode: Literal['open', 'save'], 
            output_path: Optional[Path], 
            db_path: Path
        ):
        super().__init__()
        
        # Validate required libraries
        if not HAS_COM:
            raise ImportError("Missing required libraries (pywin32) for ExportWorker.")
        
        self.ordered_slide_ids = ordered_slide_ids
        self.output_mode = output_mode
        self.output_path = output_path
        self.db_path = db_path
        self.signals = ExportWorkerSignals()
        
        # Validation
        if not ordered_slide_ids:
            raise ValueError("ExportWorker requires a non-empty list of slide IDs.")
        
        if output_mode == 'save' and not output_path:
            raise ValueError("Output path is required when output_mode is 'save'.")
            
        self.is_cancelled = False
    
    @Slot()
    def run(self):
        """The main export logic executed in the background thread."""
        worker_id_str = f"ExportWorker ({len(self.ordered_slide_ids)} slides)"
        logger.info(f"[{worker_id_str}] Starting export in mode: {self.output_mode}")
        
        # Initialize thread-local resources
        db_worker = None
        com_initialized = False
        ppt_app = None
        new_pres = None
        
        try:
            # Initialize COM for this thread
            try:
                pythoncom.CoInitialize()
                com_initialized = True
                logger.debug(f"[{worker_id_str}] COM initialized")
            except Exception as e:
                raise COMInitializationError(f"Failed to initialize COM: {e}") from e
            
            # Create database worker
            db_worker = DatabaseWorker(self.db_path)
            
            # Process the presentation
            self._process_export(db_worker, worker_id_str)
            
        except COMInitializationError as e:
            logger.error(f"[{worker_id_str}] COM initialization failed: {e}")
            self.signals.exportError.emit(str(e))
            
        except PowerPointError as e:
            logger.error(f"[{worker_id_str}] PowerPoint error: {e}")
            self.signals.exportError.emit(str(e))
            
        except Exception as e:
            logger.error(f"[{worker_id_str}] Unexpected error: {e}", exc_info=True)
            self.signals.exportError.emit(f"Export failed: {str(e)}")
            
        finally:
            # Cleanup resources
            self._cleanup(db_worker, new_pres, ppt_app, com_initialized)
            
        logger.info(f"[{worker_id_str}] Export worker finished")
    
    def _process_export(self, db_worker: DatabaseWorker, worker_id_str: str):
        """
        Process the export operation.
        
        Args:
            db_worker: Database worker instance.
            worker_id_str: Worker identification string for logging.
            
        Raises:
            PowerPointError: If export fails.
        """
        ppt_app = None
        new_pres = None
        error_details = []
        slides_with_errors = []
        
        try:
            # Create PowerPoint Application instance
            try:
                ppt_app = win32com.client.Dispatch("PowerPoint.Application")
                if self.output_mode == 'open':
                    ppt_app.Visible = True
            except com_error as e:
                raise PowerPointError("Failed to create PowerPoint application") from e
            
            # Create a new presentation
            try:
                new_pres = ppt_app.Presentations.Add()
                logger.info(f"[{worker_id_str}] Created new PowerPoint presentation")
            except com_error as e:
                raise PowerPointError("Failed to create new presentation") from e
            
            total_slides = len(self.ordered_slide_ids)
            slides_processed = 0
            
            # Process each slide
            for idx, slide_id in enumerate(self.ordered_slide_ids):
                if self.is_cancelled:
                    logger.info(f"[{worker_id_str}] Export cancelled")
                    raise PowerPointError("Export cancelled by user")
                
                try:
                    self._process_single_slide(
                        db_worker, ppt_app, new_pres, slide_id, worker_id_str
                    )
                    slides_processed += 1
                    
                except Exception as e:
                    error_msg = f"Slide {idx + 1} (ID: {slide_id}): {str(e)}"
                    error_details.append(error_msg)
                    slides_with_errors.append(slide_id)
                    logger.error(f"[{worker_id_str}] {error_msg}")
                    # Continue processing other slides
                
                # Update progress
                self.signals.exportProgress.emit(slides_processed, total_slides)
            
            # Check if we have any successful slides
            if slides_processed == 0:
                raise SlideExportError("Failed to export any slides")
            
            # Handle the presentation based on output mode
            if self.output_mode == 'save':
                self._save_presentation(new_pres, ppt_app, worker_id_str)
            else:
                # Leave presentation open
                logger.info(f"[{worker_id_str}] Presentation left open in PowerPoint")
                self.signals.exportFinished.emit("Presentation opened in PowerPoint")
            
            # Report partial success if there were errors
            if error_details:
                warning_msg = (
                    f"Export completed with {len(error_details)} errors. "
                    f"Successfully exported {slides_processed}/{total_slides} slides."
                )
                logger.warning(f"[{worker_id_str}] {warning_msg}")
                if self.output_mode == 'save':
                    self.signals.exportFinished.emit(
                        f"Presentation saved with warnings: {self.output_path}"
                    )
                
        finally:
            # Cleanup handled in main finally block
            pass
    
    def _process_single_slide(self, db_worker: DatabaseWorker, ppt_app, 
                            new_pres, slide_id: int, worker_id_str: str):
        """
        Process a single slide for export.
        
        Args:
            db_worker: Database worker instance.
            ppt_app: PowerPoint application COM object.
            new_pres: New presentation COM object.
            slide_id: ID of slide to process.
            worker_id_str: Worker identification string.
            
        Raises:
            ResourceNotFoundError: If slide origin not found.
            SlideExportError: If slide processing fails.
        """
        # Get source file path and slide index from database
        try:
            # Using the worker's connection to get slide origin
            with db_worker.connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT p.folder_path, f.rel_path, s.slide_index 
                    FROM slides s 
                    JOIN files f ON s.file_id = f.id 
                    JOIN projects p ON f.project_id = p.id 
                    WHERE s.id = ?
                """
                cursor.execute(query, (slide_id,))
                result = cursor.fetchone()
                
                if not result:
                    raise ResourceNotFoundError("Slide", slide_id)
                
                folder_path = result['folder_path']
                rel_path = result['rel_path']
                slide_index = result['slide_index']
                source_file_path = Path(folder_path) / rel_path
                
        except DatabaseError as e:
            raise SlideExportError(f"Database error: {e}") from e
        
        # Validate source file exists
        if not source_file_path.exists():
            raise SlideExportError(
                f"Source file not found: {source_file_path.name}"
            )
        
        # Open source presentation and copy slide
        source_pres = None
        try:
            logger.debug(
                f"[{worker_id_str}] Inserting slide {slide_id} from "
                f"{source_file_path.name} index {slide_index}"
            )
            
            source_pres = ppt_app.Presentations.Open(
                str(source_file_path), ReadOnly=True, WithWindow=False
            )
            
            if slide_index > source_pres.Slides.Count:
                raise SlideExportError(
                    f"Slide index {slide_index} not found in {source_file_path.name}"
                )
            
            # Copy the slide to the new presentation
            source_pres.Slides(slide_index).Copy()
            new_pres.Slides.Paste()
            
        except com_error as e:
            raise PresentationAccessError(
                f"Failed to access {source_file_path.name}: {str(e)}"
            ) from e
            
        finally:
            # Always close source presentation
            if source_pres:
                try:
                    source_pres.Close()
                except Exception as e:
                    logger.warning(f"Error closing source presentation: {e}")
    
    def _save_presentation(self, new_pres, ppt_app, worker_id_str: str):
        """
        Save the presentation to disk.
        
        Args:
            new_pres: New presentation COM object.
            ppt_app: PowerPoint application COM object.
            worker_id_str: Worker identification string.
            
        Raises:
            SlideExportError: If save fails.
        """
        try:
            save_path = str(self.output_path)
            logger.info(f"[{worker_id_str}] Saving presentation to: {save_path}")
            
            # Ensure parent directory exists
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save the presentation
            new_pres.SaveAs(save_path)
            new_pres.Close()
            
            # Re-open the saved presentation for the user
            ppt_app.Visible = True
            ppt_app.Presentations.Open(save_path, ReadOnly=False, WithWindow=True)
            
            success_message = f"Presentation saved to: {save_path}"
            logger.info(f"[{worker_id_str}] {success_message}")
            self.signals.exportFinished.emit(success_message)
            
        except com_error as e:
            raise SlideExportError(f"Failed to save presentation: {e}") from e
        except Exception as e:
            raise SlideExportError(f"Save operation failed: {e}") from e
    
    def _cleanup(self, db_worker: Optional[DatabaseWorker], 
                new_pres, ppt_app, com_initialized: bool):
        """Clean up all resources."""
        # Close database connection
        if db_worker:
            try:
                db_worker.close()
                logger.debug("Export worker: Closed database connection")
            except Exception as e:
                logger.error(f"Error closing database: {e}")
        
        # Clean up COM objects
        if new_pres and self.output_mode == 'save':
            try:
                if hasattr(new_pres, 'Saved') and not new_pres.Saved:
                    new_pres.Close()
            except Exception as e:
                logger.error(f"Error closing presentation: {e}")
        
        # Quit PowerPoint only in save mode
        if ppt_app and self.output_mode == 'save':
            try:
                ppt_app.Quit()
                logger.debug("Export worker: Quit PowerPoint application")
            except Exception as e:
                logger.error(f"Error quitting PowerPoint: {e}")
        
        # Uninitialize COM
        if com_initialized:
            try:
                pythoncom.CoUninitialize()
                logger.debug("Export worker: COM uninitialized")
            except Exception as e:
                logger.warning(f"Error uninitializing COM: {e}")
    
    def cancel(self):
        """Request cancellation of the export process."""
        logger.info("Export cancellation requested")
        self.is_cancelled = True