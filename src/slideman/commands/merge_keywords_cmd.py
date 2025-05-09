# src/slideman/commands/merge_keywords_cmd.py

import logging
import sqlite3
from typing import List, Dict, Tuple, Optional

from PySide6.QtGui import QUndoCommand

from ..app_state import app_state
from ..models.keyword import Keyword

logger = logging.getLogger(__name__)

class MergeKeywordsCmd(QUndoCommand):
    """
    Command to merge one keyword into another.
    Supports undo/redo operations.
    """
    def __init__(self, from_keyword_id: int, to_keyword_id: int, from_keyword_text: str, to_keyword_text: str, kind: str):
        """
        Initialize the command.
        
        Args:
            from_keyword_id: ID of the keyword to merge from (will be removed)
            to_keyword_id: ID of the keyword to merge into (will be kept)
            from_keyword_text: Text of the keyword to merge from (for display and undo)
            to_keyword_text: Text of the keyword to merge into (for display)
            kind: The kind of the keywords ('topic', 'title', 'name')
        """
        description = f"Merge keyword '{from_keyword_text}' into '{to_keyword_text}'"
        super().__init__(description)
        self.from_keyword_id = from_keyword_id
        self.to_keyword_id = to_keyword_id
        self.from_keyword_text = from_keyword_text
        self.to_keyword_text = to_keyword_text
        self.kind = kind
        self.logger = logging.getLogger(__name__)
        self.db = app_state.db_service
        
        # Store data for undo
        self.slide_links: List[int] = []
        self.element_links: List[int] = []
        
        # Store the original links before merging
        if self.db:
            try:
                # Get slide links
                cursor = self.db._conn.cursor()
                cursor.execute(
                    "SELECT slide_id FROM slide_keywords WHERE keyword_id = ?",
                    (from_keyword_id,)
                )
                self.slide_links = [row[0] for row in cursor.fetchall()]
                
                # Get element links
                cursor.execute(
                    "SELECT element_id FROM element_keywords WHERE keyword_id = ?",
                    (from_keyword_id,)
                )
                self.element_links = [row[0] for row in cursor.fetchall()]
                
                self.logger.debug(f"Stored {len(self.slide_links)} slide links and {len(self.element_links)} element links for undo")
            except sqlite3.Error as e:
                self.logger.error(f"Error storing original links for undo: {str(e)}")
    
    def redo(self):
        """
        Execute the command: merge the keywords.
        """
        if not self.db:
            self.logger.error("Database service not available")
            return
            
        success = self.db.merge_keywords(self.from_keyword_id, self.to_keyword_id)
        if success:
            self.logger.debug(f"Merged keyword '{self.from_keyword_text}' into '{self.to_keyword_text}'")
        else:
            self.logger.error(f"Failed to merge keyword '{self.from_keyword_text}' into '{self.to_keyword_text}'")
    
    def undo(self):
        """
        Undo the command: restore the original keyword and its links.
        """
        if not self.db:
            self.logger.error("Database service not available")
            return
        
        try:
            # Use mutex for thread safety during write operations
            with self.db._write_mutex:
                # Start a transaction
                self.db._conn.execute("BEGIN TRANSACTION")
                
                # Re-create the original keyword
                cursor = self.db._conn.cursor()
                cursor.execute(
                    "INSERT INTO keywords (id, keyword, kind) VALUES (?, ?, ?)",
                    (self.from_keyword_id, self.from_keyword_text, self.kind)
                )
                
                # Restore slide links
                for slide_id in self.slide_links:
                    cursor.execute(
                        "INSERT OR IGNORE INTO slide_keywords (slide_id, keyword_id) VALUES (?, ?)",
                        (slide_id, self.from_keyword_id)
                    )
                
                # Restore element links
                for element_id in self.element_links:
                    cursor.execute(
                        "INSERT OR IGNORE INTO element_keywords (element_id, keyword_id) VALUES (?, ?)",
                        (element_id, self.from_keyword_id)
                    )
                
                # Commit the transaction
                self.db._conn.execute("COMMIT")
                self.logger.debug(f"Undid merge: Restored keyword '{self.from_keyword_text}' with {len(self.slide_links)} slide links and {len(self.element_links)} element links")
                
        except Exception as e:
            # Rollback on error
            self.db._conn.execute("ROLLBACK")
            self.logger.error(f"Error undoing keyword merge: {str(e)}")
