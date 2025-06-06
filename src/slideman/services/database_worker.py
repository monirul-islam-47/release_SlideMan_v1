# src/slideman/services/database_worker.py
"""
Thread-safe database proxy for worker threads.

This module provides a simplified database interface specifically designed
for use in worker threads, ensuring proper connection management and
thread safety.
"""

import sqlite3
import threading
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from contextlib import contextmanager

from .exceptions import DatabaseError, ConnectionError


class DatabaseWorker:
    """
    Thread-safe database proxy for worker threads.
    
    Each worker thread should create its own instance of this class
    to ensure proper connection isolation.
    """
    
    def __init__(self, db_path: Path):
        """
        Initialize the database worker proxy.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._local = threading.local()
        self.logger = logging.getLogger(f"{__name__}.{threading.current_thread().name}")
        
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get or create a thread-local database connection.
        
        Returns:
            A database connection for the current thread.
            
        Raises:
            ConnectionError: If unable to create connection.
        """
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            try:
                self._local.conn = sqlite3.connect(self.db_path)
                self._local.conn.row_factory = sqlite3.Row
                self._local.conn.execute("PRAGMA foreign_keys = ON;")
                self._local.conn.execute("PRAGMA journal_mode = WAL;")
                self._local.conn.execute("PRAGMA busy_timeout = 5000;")
                self.logger.debug(f"Created new database connection for thread {threading.current_thread().name}")
            except sqlite3.Error as e:
                raise ConnectionError(f"Failed to create worker database connection: {e}") from e
                
        return self._local.conn
    
    @contextmanager
    def connection(self):
        """
        Context manager for database connection.
        
        Yields:
            Database connection for the current thread.
        """
        conn = self._get_connection()
        try:
            yield conn
        except Exception:
            # Don't close on error, connection can be reused
            raise
    
    def close(self) -> None:
        """Close the thread-local database connection."""
        if hasattr(self._local, 'conn') and self._local.conn:
            try:
                self._local.conn.close()
                self.logger.debug(f"Closed database connection for thread {threading.current_thread().name}")
            except Exception as e:
                self.logger.error(f"Error closing worker connection: {e}")
            finally:
                self._local.conn = None
    
    # Slide conversion specific methods
    
    def update_file_conversion_status(self, file_id: int, status: str) -> None:
        """
        Update the conversion status of a file.
        
        Args:
            file_id: ID of the file to update.
            status: New conversion status ('Pending', 'In Progress', 'Completed', 'Failed').
            
        Raises:
            DatabaseError: If update fails.
        """
        with self.connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE files SET conversion_status = ? WHERE id = ?",
                    (status, file_id)
                )
                conn.commit()
                self.logger.debug(f"Updated file {file_id} conversion status to '{status}'")
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Failed to update conversion status: {e}") from e
    
    def update_file_slide_count(self, file_id: int, slide_count: int) -> None:
        """
        Update the slide count for a file.
        
        Args:
            file_id: ID of the file to update.
            slide_count: Number of slides in the file.
            
        Raises:
            DatabaseError: If update fails.
        """
        with self.connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE files SET slide_count = ? WHERE id = ?",
                    (slide_count, file_id)
                )
                conn.commit()
                self.logger.debug(f"Updated file {file_id} slide count to {slide_count}")
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Failed to update slide count: {e}") from e
    
    def add_slide_with_paths(self, file_id: int, slide_index: int, 
                           thumb_rel_path: Optional[str] = None,
                           image_rel_path: Optional[str] = None) -> int:
        """
        Add a slide record with thumbnail and image paths.
        
        Args:
            file_id: ID of the file this slide belongs to.
            slide_index: 1-based index of the slide within the file.
            thumb_rel_path: Relative path to thumbnail image.
            image_rel_path: Relative path to full-size image.
            
        Returns:
            ID of the newly created slide record.
            
        Raises:
            DatabaseError: If insertion fails.
        """
        with self.connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO slides (file_id, slide_index, thumb_rel_path, image_rel_path) 
                       VALUES (?, ?, ?, ?)""",
                    (file_id, slide_index, thumb_rel_path, image_rel_path)
                )
                conn.commit()
                slide_id = cursor.lastrowid
                self.logger.debug(f"Added slide {slide_index} for file {file_id} with ID {slide_id}")
                return slide_id
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Failed to add slide: {e}") from e
    
    def add_element(self, slide_id: int, element_type: str, content: str) -> int:
        """
        Add an element to a slide.
        
        Args:
            slide_id: ID of the slide this element belongs to.
            element_type: Type of element (e.g., 'text', 'title').
            content: Element content.
            
        Returns:
            ID of the newly created element.
            
        Raises:
            DatabaseError: If insertion fails.
        """
        with self.connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO elements (slide_id, element_type, content) VALUES (?, ?, ?)",
                    (slide_id, element_type, content)
                )
                conn.commit()
                element_id = cursor.lastrowid
                self.logger.debug(f"Added {element_type} element to slide {slide_id} with ID {element_id}")
                return element_id
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Failed to add element: {e}") from e
    
    def get_slide_thumbnail_path(self, slide_id: int) -> Optional[str]:
        """
        Get the thumbnail path for a slide.
        
        Args:
            slide_id: ID of the slide.
            
        Returns:
            Relative path to thumbnail, or None if not found.
            
        Raises:
            DatabaseError: If query fails.
        """
        with self.connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT thumb_rel_path FROM slides WHERE id = ?",
                    (slide_id,)
                )
                result = cursor.fetchone()
                return result['thumb_rel_path'] if result else None
            except sqlite3.Error as e:
                raise DatabaseError(f"Failed to get thumbnail path: {e}") from e
    
    def batch_update_slide_texts(self, slide_texts: List[Tuple[int, Optional[str], Optional[str]]]) -> None:
        """
        Update title and notes for multiple slides in a single transaction.
        
        Args:
            slide_texts: List of tuples (slide_id, title, notes).
            
        Raises:
            DatabaseError: If update fails.
        """
        with self.connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("BEGIN TRANSACTION")
                
                for slide_id, title, notes in slide_texts:
                    # Update in FTS table (simplified for worker)
                    cursor.execute(
                        """UPDATE slides_fts 
                           SET title = COALESCE(?, title), notes = COALESCE(?, notes) 
                           WHERE slide_id = ?""",
                        (title, notes, slide_id)
                    )
                
                conn.commit()
                self.logger.debug(f"Updated text for {len(slide_texts)} slides")
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Failed to update slide texts: {e}") from e