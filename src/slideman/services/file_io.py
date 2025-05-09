# src/slideman/services/file_io.py

import shutil
import os
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import platform


# --- Constants ---
# Buffer size for file hashing to avoid loading large files into memory
HASH_BUFFER_SIZE = 65536 # 64 KB

# --- Setup Logger ---
logger = logging.getLogger(__name__)

# --- Core Functions ---

def check_disk_space(target_path: Path, required_bytes: int) -> Tuple[bool, int]:
    """
    Checks if there is enough free disk space on the target drive.
    Works on Windows by checking the drive root.

    Args:
        target_path: A path (file or directory) on the target drive.
        required_bytes: The minimum number of free bytes required.

    Returns:
        A tuple: (True if enough space, free_bytes found) or (False, free_bytes found).
    """
    try:
        # Make sure the path is absolute to correctly find the anchor/drive
        abs_target_path = target_path.resolve() # Get absolute path

        # On Windows, anchor is the drive (e.g., 'C:\')
        # On Unix, anchor is '/'
        drive_root = Path(abs_target_path.anchor)

        if not drive_root.exists():
            # If the drive itself doesn't exist (unlikely but possible)
            logger.error(f"Cannot check disk space: Drive '{drive_root}' for path '{target_path}' not found.")
            return False, 0

        usage = shutil.disk_usage(drive_root)
        free_bytes = usage.free
        logger.debug(f"Checking disk space on '{drive_root}': Free: {free_bytes} bytes, Required: {required_bytes} bytes")

        if free_bytes >= required_bytes:
            return True, free_bytes
        else:
            logger.warning(f"Insufficient disk space on '{drive_root}'. Required: {required_bytes}, Available: {free_bytes}")
            return False, free_bytes

    except FileNotFoundError:
         # This might happen if the initial target_path doesn't exist and resolve() fails
         logger.error(f"Cannot check disk space: Path '{target_path}' could not be resolved.")
         return False, 0
    except Exception as e:
        logger.error(f"Error checking disk space for '{target_path}' (checking '{drive_root}'): {e}", exc_info=True)
        return False, 0

def calculate_checksum(file_path: Path) -> Optional[str]:
    """
    Calculates the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        The hex digest of the SHA-256 checksum, or None if the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read and update hash string value in blocks
            while True:
                buffer = f.read(HASH_BUFFER_SIZE)
                if not buffer:
                    break
                sha256_hash.update(buffer)
        checksum = sha256_hash.hexdigest()
        logger.debug(f"Calculated checksum for '{file_path}': {checksum[:8]}...") # Log truncated hash
        return checksum
    except FileNotFoundError:
        logger.error(f"Checksum calculation failed: File not found at '{file_path}'")
        return None
    except OSError as e:
         logger.error(f"Checksum calculation failed: OS error reading file '{file_path}': {e}", exc_info=True)
         return None
    except Exception as e:
        logger.error(f"Checksum calculation failed: Unexpected error for file '{file_path}': {e}", exc_info=True)
        return None

def copy_files_to_project(source_paths: List[Path], project_folder: Path) -> Dict[str, Optional[str]]:
    """
    Copies source files into the project folder and calculates checksums.

    Creates the project folder if it doesn't exist. Skips files that fail to copy.

    Args:
        source_paths: A list of Path objects for the source files.
        project_folder: The Path object for the destination project folder.

    Returns:
        A dictionary mapping the relative path (as string) within the project folder
        to its calculated checksum (or None if checksum failed). Only includes
        successfully copied files.
    """
    copied_files_info: Dict[str, Optional[str]] = {}
    project_folder.mkdir(parents=True, exist_ok=True)
    logger.info(f"Starting copy of {len(source_paths)} files to '{project_folder}'")

    total_size = sum(p.stat().st_size for p in source_paths if p.is_file())
    # Check disk space (consider adding a safety margin, e.g., * 1.1)
    has_space, free_space = check_disk_space(project_folder, int(total_size * 1.1))
    if not has_space:
         logger.error(f"Cannot copy files: Insufficient disk space. Required: ~{int(total_size*1.1)} bytes, Available: {free_space} bytes.")
         # Consider raising a specific exception here?
         raise OSError(f"Insufficient disk space to copy project files.") # Raise error to stop process


    for src_path in source_paths:
        if not src_path.is_file():
            logger.warning(f"Skipping non-file source path: '{src_path}'")
            continue

        relative_path_str = src_path.name # Simple copy to root of project folder
        # If you want to preserve subdirectories, calculate relative path differently
        # relative_path = src_path.relative_to(common_ancestor_path)
        # dest_path = project_folder / relative_path

        dest_path = project_folder / relative_path_str
        logger.debug(f"Copying '{src_path}' to '{dest_path}'")

        try:
            # Copy file including metadata (permissions, timestamps)
            shutil.copy2(src_path, dest_path)
            # Calculate checksum *after* successful copy
            checksum = calculate_checksum(dest_path)
            copied_files_info[relative_path_str] = checksum

        except OSError as e:
            logger.error(f"Failed to copy file '{src_path}' to '{dest_path}': {e}", exc_info=True)
            # Optionally try to clean up partially copied file if possible
            if dest_path.exists():
                try: dest_path.unlink()
                except OSError: pass
        except Exception as e:
             logger.error(f"Unexpected error copying file '{src_path}': {e}", exc_info=True)

    successful_copies = len(copied_files_info)
    logger.info(f"Finished copying files. Successfully copied: {successful_copies}/{len(source_paths)}")
    return copied_files_info