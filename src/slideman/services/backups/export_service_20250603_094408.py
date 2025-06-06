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
    Supported signals are:
    exportProgress: Emits current slide and total slides (int, int)
    exportFinished: Emits output path or success message (str)
    exportError: Emits error message (str)
    """
    exportProgress = Signal(int, int)  # current, total
    exportFinished = Signal(str)       # output path or success message
    exportError = Signal(str)          # error message

class ExportWorker(QRunnable):
    """
    Worker thread for exporting PowerPoint presentations.
    Inherits from QRunnable to run on a thread from QThreadPool.

    Args:
        ordered_slide_ids: List of slide IDs in the order they should appear in the presentation
        output_mode: Either 'open' (leave open in PowerPoint) or 'save' (save to file)
        output_path: Path to save the presentation (required if output_mode is 'save')
        db_service: Database service instance
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
        
        try:
            # Initialize COM for this thread
            pythoncom.CoInitialize()
            com_initialized = True
            logger.debug(f"[{worker_id_str}] COM initialized")
            
            # Create database worker
            db_worker = DatabaseWorker(self.db_path)
            
        except Exception as e:
            error_message = f"Failed to initialize: {e}"
            logger.error(f"[{worker_id_str}] {error_message}", exc_info=True)
            self.signals.exportError.emit(error_message)
            return
        
        ppt_app = None
        new_pres = None
        overall_success = True
        error_details = []
        
        try:
            # Create PowerPoint Application instance
            ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            
            if self.output_mode == 'open':
                ppt_app.Visible = True  # Show PowerPoint only when explicitly opening
            # Removed explicit hide for save mode; default COM instance remains hidden
            
            # Create a new presentation
            new_pres = ppt_app.Presentations.Add()
            logger.info(f"[{worker_id_str}] Created new PowerPoint presentation")
            
            total_slides = len(self.ordered_slide_ids)
            slides_processed = 0
            
            # Process each slide
            for slide_id in self.ordered_slide_ids:
                if self.is_cancelled:
                    logger.info(f"[{worker_id_str}] Export cancelled")
                    overall_success = False
                    break
                
                try:
                    # Get source file path and slide index from the database
                    slide_origin = self.db_service.get_slide_origin(slide_id)
                    
                    if not slide_origin:
                        error_msg = f"Could not find origin information for slide ID: {slide_id}"
                        logger.error(f"[{worker_id_str}] {error_msg}")
                        error_details.append(error_msg)
                        overall_success = False
                        continue
                    
                    source_file_path, slide_index = slide_origin
                    
                    # Ensure the source file exists
                    if not os.path.exists(source_file_path):
                        error_msg = f"Source file does not exist: {source_file_path} for slide ID: {slide_id}"
                        logger.error(f"[{worker_id_str}] {error_msg}")
                        error_details.append(error_msg)
                        overall_success = False
                        continue
                    
                    # Insert the slide from the source file
                    logger.debug(f"[{worker_id_str}] Inserting slide {slide_id} from {source_file_path} index {slide_index}")
                    
                    # Open the source presentation to get the slide
                    try:
                        source_pres = ppt_app.Presentations.Open(source_file_path, ReadOnly=True, WithWindow=False)
                        if slide_index > source_pres.Slides.Count:
                            logger.warning(f"[{worker_id_str}] Slide index {slide_index} exceeds slide count {source_pres.Slides.Count} in {source_file_path}")
                            error_msg = f"Slide index {slide_index} not found in {os.path.basename(source_file_path)}"
                            error_details.append(error_msg)
                            source_pres.Close()
                            continue
                            
                        # Copy the slide to the new presentation
                        source_pres.Slides(slide_index).Copy()
                        new_pres.Slides.Paste()
                        source_pres.Close()
                    except com_error as ce:
                        logger.error(f"[{worker_id_str}] COM error opening source presentation {source_file_path}: {ce}")
                        error_msg = f"Failed to access source presentation: {os.path.basename(source_file_path)}"
                        error_details.append(error_msg)
                        overall_success = False
                        continue
                    
                except com_error as ce:
                    error_msg = f"COM error processing slide ID {slide_id}: {ce}"
                    logger.error(f"[{worker_id_str}] {error_msg}", exc_info=True)
                    error_details.append(error_msg)
                    overall_success = False
                    # Continue with other slides
                
                except Exception as e:
                    error_msg = f"Error processing slide ID {slide_id}: {e}"
                    logger.error(f"[{worker_id_str}] {error_msg}", exc_info=True)
                    error_details.append(error_msg)
                    overall_success = False
                    # Continue with other slides
                
                # Update progress
                slides_processed += 1
                self.signals.exportProgress.emit(slides_processed, total_slides)
            
            # Handle the presentation based on the output mode
            if self.output_mode == 'save' and self.output_path:
                try:
                    # Save the presentation
                    save_path = str(self.output_path)
                    logger.info(f"[{worker_id_str}] Saving presentation to: {save_path}")
                    new_pres.SaveAs(save_path)
                    new_pres.Close()
                    ppt_app.Visible = True
                    ppt_app.Presentations.Open(save_path, ReadOnly=False, WithWindow=True)
                    success_message = f"Presentation saved to: {save_path}"
                except Exception as e:
                    error_msg = f"Failed to save presentation: {e}"
                    logger.error(f"[{worker_id_str}] {error_msg}", exc_info=True)
                    error_details.append(error_msg)
                    overall_success = False
                    success_message = "Failed to save presentation"
            else:
                # Leave presentation open
                success_message = "Presentation opened in PowerPoint"
                logger.info(f"[{worker_id_str}] Presentation left open in PowerPoint")
                # Don't close new_pres here
            
            # Emit final signal based on success
            if overall_success:
                logger.info(f"[{worker_id_str}] Export completed successfully: {success_message}")
                self.signals.exportFinished.emit(success_message)
            else:
                combined_errors = "; ".join(error_details)
                error_message = f"Export completed with errors: {combined_errors}"
                logger.warning(f"[{worker_id_str}] {error_message}")
                self.signals.exportError.emit(error_message)
                
        except Exception as e:
            error_message = f"Critical export error: {e}"
            logger.error(f"[{worker_id_str}] {error_message}", exc_info=True)
            self.signals.exportError.emit(error_message)
        
        finally:
            # Clean up resources
            # Release COM objects properly
            if new_pres is not None and self.output_mode == 'save':
                try:
                    # Only close if we're in save mode
                    if not new_pres.Saved:  # Check if presentation is already saved
                        new_pres.Close()
                except Exception as e:
                    logger.error(f"[{worker_id_str}] Error closing presentation: {e}")
            
            # Quit PowerPoint application only if we're in save mode
            # In 'open' mode, leave PowerPoint running for the user
            if ppt_app is not None and self.output_mode == 'save':
                try:
                    ppt_app.Quit()
                    logger.debug(f"[{worker_id_str}] Quit PowerPoint application")
                except Exception as e:
                    logger.error(f"[{worker_id_str}] Error quitting PowerPoint: {e}")
            
            # Release COM references
            new_pres = None
            ppt_app = None
            
            # Uninitialize COM
            try:
                pythoncom.CoUninitialize()
            except Exception as e:
                logger.error(f"[{worker_id_str}] Error uninitializing COM: {e}")
            
            logger.info(f"[{worker_id_str}] Export worker execution finished")
    
    def cancel(self):
        """Requests cancellation of the export process."""
        logger.info("Cancellation requested for ExportWorker")
        self.is_cancelled = True
