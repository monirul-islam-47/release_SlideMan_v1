# src/slideman/services/thumbnail_cache.py

import logging
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtGui import QPixmap
from PySide6.QtCore import QObject, Slot, Qt

# Import AppState to access current project path and DB service
# This creates a dependency cycle if AppState also imports this.
# Alternative: Pass needed info explicitly. Let's try accessing AppState first.
from ..app_state import app_state
# Need Database service type hint
from .database import Database

logger = logging.getLogger(__name__)

# We'll create the placeholder pixmap on-demand rather than at module load time
# to avoid creating QPixmap before QApplication exists

class ThumbnailCache(QObject):
    """
    Manages an in-memory cache for slide thumbnail QPixmap objects.
    Loads from disk if not found in cache.
    Designed as a singleton accessed via global instance 'thumbnail_cache'.
    """
    _instance = None
    _placeholder_thumbnail = None  # Lazy-loaded placeholder

    def __new__(cls):
        if cls._instance is None:
            logger.debug("Creating ThumbnailCache instance")
            cls._instance = super().__new__(cls)
            # Initialize cache ONLY once
            cls._instance._memory_cache: Dict[int, QPixmap] = {} # slide_id -> QPixmap
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initializes the ThumbnailCache singleton."""
        if self._initialized:
            return
        super().__init__()
        # Connect to project closed signal to clear cache
        app_state.projectClosed.connect(self.clear_cache)
        self._initialized = True
        logger.info("ThumbnailCache initialized and connected to projectClosed signal.")
    
    def _get_placeholder(self) -> QPixmap:
        """Create the placeholder pixmap on demand"""
        if ThumbnailCache._placeholder_thumbnail is None:
            try:
                placeholder = QPixmap(100, 100)
                placeholder.fill(Qt.GlobalColor.darkGray)
                ThumbnailCache._placeholder_thumbnail = placeholder
                logger.debug("Created placeholder thumbnail pixmap")
            except Exception as e:
                logger.error(f"Failed to create placeholder pixmap: {e}")
                # Return an empty pixmap as last resort
                ThumbnailCache._placeholder_thumbnail = QPixmap()
        return ThumbnailCache._placeholder_thumbnail

    def get_thumbnail(self, slide_id: int) -> Optional[QPixmap]:
        """
        Retrieves a thumbnail QPixmap for a given slide ID.
        Checks memory cache first, then attempts to load from disk path
        retrieved via the database service accessed through AppState.

        Args:
            slide_id: The database ID of the slide.

        Returns:
            The QPixmap thumbnail, or a placeholder/None if not found/load fails.
        """
        # 1. Check memory cache
        if slide_id in self._memory_cache:
            # logger.debug(f"Thumbnail cache HIT for SlideID: {slide_id}")
            return self._memory_cache[slide_id]

        logger.debug(f"Thumbnail cache MISS for SlideID: {slide_id}. Attempting disk load.")

        # 2. Get necessary info from AppState (Project Path, DB Service)
        current_project_path_str = app_state.current_project_path
        db_service = app_state.db_service

        # Ensure DB service is present
        if not db_service:
            logger.error(f"Cannot load thumbnail for SlideID {slide_id}: DB service missing in AppState.")
            return self._get_placeholder()

        # Derive project path if not set in AppState
        if not current_project_path_str:
            try:
                cur = db_service._conn.cursor()
                cur.execute(
                    "SELECT p.folder_path FROM projects p "
                    "JOIN files f ON f.project_id = p.id "
                    "JOIN slides s ON s.file_id = f.id WHERE s.id = ?;",
                    (slide_id,)
                )
                row = cur.fetchone()
                if row and row[0]:
                    current_project_path_str = row[0]
                else:
                    logger.warning(f"Cannot derive project path for SlideID {slide_id}, using placeholder thumbnail.")
                    return self._get_placeholder()
            except Exception as e:
                logger.warning(
                    f"Failed to derive project path for SlideID {slide_id}: {e}, using placeholder.",
                    exc_info=True
                )
                return self._get_placeholder()

        project_root = Path(current_project_path_str)

        # 3. Get thumbnail relative path from database
        thumb_rel_path_str = db_service.get_slide_thumbnail_path(slide_id)

        if not thumb_rel_path_str:
            logger.warning(f"No thumbnail path found in DB for SlideID: {slide_id}")
            return self._get_placeholder()

        # 4. Construct full path and try from multiple locations
        
        # Path from the database (assumes project/converted_data/...)
        standard_path = project_root / thumb_rel_path_str
        
        # FIX: The thumbnails are actually in a shared folder at the root rather than in project-specific locations
        # Get the shared location at Documents/SlidemanProjects/converted_data/...
        projects_root = project_root.parent  # Go up one level to get the SlidemanProjects folder
        shared_path = projects_root / thumb_rel_path_str
        
        logger.debug(f"Looking for thumbnail in standard path: {standard_path}")
        logger.debug(f"Looking for thumbnail in shared path: {shared_path}")
        
        # Try the shared location first (since we know it exists)
        if shared_path.exists():
            logger.info(f"Found thumbnail at shared location: {shared_path}")
            pixmap = QPixmap(str(shared_path))
            if not pixmap.isNull():
                self._memory_cache[slide_id] = pixmap
                return pixmap
        
        # Fall back to standard location
        if standard_path.exists():
            logger.info(f"Found thumbnail at standard location: {standard_path}")
            pixmap = QPixmap(str(standard_path))
            if not pixmap.isNull():
                self._memory_cache[slide_id] = pixmap
                return pixmap
                
        # If we reach here, we couldn't find the thumbnail anywhere
        logger.warning(f"Thumbnail not found at any location for SlideID {slide_id}")
        return self._get_placeholder()

    @Slot() # Slot to connect to AppState.projectClosed signal
    def clear_cache(self):
        """Clears the in-memory thumbnail cache."""
        logger.info(f"Clearing thumbnail memory cache ({len(self._memory_cache)} items). Project closed.")
        self._memory_cache.clear()

    def get_cache_size(self) -> int:
         """Returns the number of items currently in the memory cache."""
         return len(self._memory_cache)


# --- Global Singleton Instance ---
thumbnail_cache = ThumbnailCache()