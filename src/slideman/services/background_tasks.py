# src/slideman/services/background_tasks.py

import logging
import shutil
from pathlib import Path
from typing import List, Dict, Optional

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

# Import our file_io functions
from . import file_io

logger = logging.getLogger(__name__)

class WorkerSignals(QObject):
    """
    Defines signals available from a running worker thread.
    Supported signals are:
    finished: Dict[str, Optional[str]] - Emitted on success, payload is copied_files_info
    error: str - Emitted on failure with error message
    progress: int - Emitted periodically with percentage (0-100) complete
    """
    finished = Signal(dict) # Dict[rel_path_str, checksum_or_None]
    error = Signal(str)
    progress = Signal(int)


class FileCopyWorker(QRunnable):
    """
    Worker thread for copying project files in the background.
    Inherits from QRunnable to run on a thread from QThreadPool.

    Args:
        source_paths: List of source file Paths.
        project_folder: Destination project folder Path.
    """
    def __init__(self, source_paths: List[Path], project_folder: Path, signals: WorkerSignals):
        super().__init__()
        self.source_paths = source_paths
        self.project_folder = project_folder
        self.signals = signals # Signal emitter

        # Basic validation
        if not source_paths or not project_folder:
             raise ValueError("FileCopyWorker requires source_paths and project_folder.")

        self.is_cancelled = False # Flag for cancellation (optional)

        # Replace the entire run method in src/slideman/services/background_tasks.py
    @Slot()
    def run(self):
        """The main work executed in the background thread."""
        worker_file_id_str = f"FileCopyWorker FIDs:{[p.name for p in self.source_paths]}" # For logging context
        logger.info(f"[{worker_file_id_str}] Starting copy for {len(self.source_paths)} files to '{self.project_folder}'")

        # Initialize results/status
        copied_files_info: Dict[str, Optional[str]] = {}
        files_processed = 0
        total_files = 0
        encountered_error_in_loop = False
        error_message = "" # Keep track of first significant error

        try:
            # --- Disk Space Check & Prep ---
            logger.debug(f"[{worker_file_id_str}] Performing pre-checks...")
            total_size = 0
            valid_source_paths = []
            for p in self.source_paths:
                if p.is_file():
                    try:
                        total_size += p.stat().st_size
                        valid_source_paths.append(p)
                    except OSError as stat_e:
                        logger.warning(f"[{worker_file_id_str}] Could not stat file, skipping: {p}. Error: {stat_e}")
                else:
                     logger.warning(f"[{worker_file_id_str}] Skipping non-file source: {p}")

            if not valid_source_paths:
                 raise ValueError("No valid source files found to copy.")

            total_files = len(valid_source_paths)
            logger.debug(f"[{worker_file_id_str}] Found {total_files} valid files, total size {total_size} bytes.")

            # Check disk space (add ~10% margin)
            required_space = int(total_size * 1.1) if total_size > 0 else 0
            has_space, free_space = file_io.check_disk_space(self.project_folder, required_space)
            if not has_space:
                 raise OSError(f"Insufficient disk space. Required: ~{required_space} bytes, Available: {free_space} bytes.")

            # Ensure Destination Folder Exists
            self.project_folder.mkdir(parents=True, exist_ok=True)
            logger.debug(f"[{worker_file_id_str}] Output directory ensured: {self.project_folder}")
            # ----------------------------

            # --- Copy Loop ---
            logger.debug(f"[{worker_file_id_str}] Starting copy loop...")
            for src_path in valid_source_paths:
                if self.is_cancelled:
                    logger.info(f"[{worker_file_id_str}] File copy cancelled by request during loop.")
                    error_message = "File copy operation was cancelled."
                    break # Exit loop

                relative_path_str = src_path.name # Simple copy to root
                dest_path = self.project_folder / relative_path_str
                logger.debug(f"[{worker_file_id_str}] Worker copying '{src_path.name}'")
                try:
                    shutil.copy2(src_path, dest_path)
                    checksum = file_io.calculate_checksum(dest_path)
                    copied_files_info[relative_path_str] = checksum
                except Exception as copy_err:
                     logger.error(f"[{worker_file_id_str}] Worker failed to copy file '{src_path.name}': {copy_err}", exc_info=True)
                     encountered_error_in_loop = True # Flag that at least one file failed
                     if not error_message: # Store first error message
                         error_message = f"Failed to copy {src_path.name}: {copy_err}"

                files_processed += 1
                progress_percent = int((files_processed / total_files) * 100) if total_files > 0 else 0
                self.signals.progress.emit(progress_percent)
            # --- End of Copy Loop ---
            logger.debug(f"[{worker_file_id_str}] Copy loop finished.")


            # --- Emit Final Signal based on outcome ---
            if self.is_cancelled:
                 # Error message already set above
                 logger.warning(f"[{worker_file_id_str}] Emitting ERROR signal (Cancelled): {error_message}")
                 self.signals.error.emit(error_message)
            elif encountered_error_in_loop:
                 # Error message already set above (first error encountered)
                 final_msg = f"Finished with errors. Copied: {len(copied_files_info)}/{total_files}. First error: {error_message}"
                 logger.error(f"[{worker_file_id_str}] Emitting ERROR signal (Loop errors): {final_msg}")
                 # We could emit finished with the partial dict, but emitting error might be clearer
                 self.signals.error.emit(final_msg)
            elif not copied_files_info and total_files > 0:
                 # Catch case where loop ran but nothing got copied (maybe all failed silently?)
                 error_message = "File copy finished, but no files seem to have been copied successfully."
                 logger.error(f"[{worker_file_id_str}] Emitting ERROR signal (No files copied): {error_message}")
                 self.signals.error.emit(error_message)
            else:
                 # Success case
                 success_message = f"Finished copying files. Successfully copied: {len(copied_files_info)}/{total_files}"
                 logger.info(f"[{worker_file_id_str}] {success_message}")
                 logger.debug(f"[{worker_file_id_str}] Emitting FINISHED signal with {len(copied_files_info)} items.")
                 self.signals.finished.emit(copied_files_info)
                 logger.debug(f"[{worker_file_id_str}] FINISHED signal emitted.")
            # ---------------------------------------------

        except Exception as e:
            # Catch major errors from setup (disk space, mkdir, initial checks)
            logger.error(f"[{worker_file_id_str}] FileCopyWorker failed critically during setup: {e}", exc_info=True)
            error_message = f"Failed to start file copy: {e}"
            logger.debug(f"[{worker_file_id_str}] Emitting ERROR signal (Critical setup failure): {error_message}")
            self.signals.error.emit(error_message)

        # --- Final log message ---
        logger.info(f"[{worker_file_id_str}] Worker execution finished.")

    def cancel(self):
         """Sets the cancellation flag."""
         logger.info("Cancellation requested for FileCopyWorker.")
         self.is_cancelled = True