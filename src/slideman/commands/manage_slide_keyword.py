# src/slideman/commands/manage_slide_keyword.py

from PySide6.QtGui import QUndoCommand
import logging

from ..app_state import app_state

logger = logging.getLogger(__name__)

class LinkSlideKeywordCmd(QUndoCommand):
    """
    Command to link a slide to a keyword.
    Supports undo/redo operations.
    """
    def __init__(self, slide_id: int, keyword_id: int, description: str = None):
        """
        Initialize the command.
        
        Args:
            slide_id: The ID of the slide
            keyword_id: The ID of the keyword
            description: Optional description for the undo stack
        """
        if description is None:
            description = f"Link keyword to slide"
        super().__init__(description)
        self.slide_id = slide_id
        self.keyword_id = keyword_id
        self.logger = logging.getLogger(__name__)
        self.db = app_state.db_service
    
    def redo(self):
        """
        Execute the command: link the slide to the keyword.
        """
        if not self.db:
            self.logger.error("Database service not available")
            return
            
        success = self.db.link_slide_keyword(self.slide_id, self.keyword_id)
        if success:
            self.logger.debug(f"Linked slide ID {self.slide_id} to keyword ID {self.keyword_id}")
        else:
            self.logger.error(f"Failed to link slide ID {self.slide_id} to keyword ID {self.keyword_id}")
    
    def undo(self):
        """
        Undo the command: unlink the slide from the keyword.
        """
        if not self.db:
            self.logger.error("Database service not available")
            return
            
        success = self.db.unlink_slide_keyword(self.slide_id, self.keyword_id)
        if success:
            self.logger.debug(f"Unlinked slide ID {self.slide_id} from keyword ID {self.keyword_id}")
        else:
            self.logger.error(f"Failed to unlink slide ID {self.slide_id} from keyword ID {self.keyword_id}")


class UnlinkSlideKeywordCmd(QUndoCommand):
    """
    Command to unlink a slide from a keyword.
    Supports undo/redo operations.
    """
    def __init__(self, slide_id: int, keyword_id: int, description: str = None):
        """
        Initialize the command.
        
        Args:
            slide_id: The ID of the slide
            keyword_id: The ID of the keyword
            description: Optional description for the undo stack
        """
        if description is None:
            description = f"Remove keyword from slide"
        super().__init__(description)
        self.slide_id = slide_id
        self.keyword_id = keyword_id
        self.logger = logging.getLogger(__name__)
        self.db = app_state.db_service
    
    def redo(self):
        """
        Execute the command: unlink the slide from the keyword.
        """
        if not self.db:
            self.logger.error("Database service not available")
            return
            
        success = self.db.unlink_slide_keyword(self.slide_id, self.keyword_id)
        if success:
            self.logger.debug(f"Unlinked slide ID {self.slide_id} from keyword ID {self.keyword_id}")
        else:
            self.logger.error(f"Failed to unlink slide ID {self.slide_id} from keyword ID {self.keyword_id}")
    
    def undo(self):
        """
        Undo the command: link the slide to the keyword.
        """
        if not self.db:
            self.logger.error("Database service not available")
            return
            
        success = self.db.link_slide_keyword(self.slide_id, self.keyword_id)
        if success:
            self.logger.debug(f"Linked slide ID {self.slide_id} to keyword ID {self.keyword_id}")
        else:
            self.logger.error(f"Failed to link slide ID {self.slide_id} to keyword ID {self.keyword_id}")


class ReplaceSlideKeywordsCmd(QUndoCommand):
    """
    Command to replace all keywords of a specific kind for a slide.
    Supports undo/redo operations.
    """
    def __init__(self, slide_id: int, kind: str, new_keyword_texts: list, description: str = None):
        """
        Initialize the command.
        
        Args:
            slide_id: The ID of the slide
            kind: The kind of keywords ('topic', 'title', 'name')
            new_keyword_texts: List of new keyword texts to set
            description: Optional description for the undo stack
        """
        if description is None:
            description = f"Replace {kind} keywords for slide"
        super().__init__(description)
        self.slide_id = slide_id
        self.kind = kind
        self.new_keyword_texts = new_keyword_texts
        self.logger = logging.getLogger(__name__)
        self.db = app_state.db_service
        
        # Store the old keyword texts for undo
        self.old_keyword_texts = []
        if self.db:
            old_keywords = self.db.get_keywords_for_slide(slide_id, kind)
            self.old_keyword_texts = [kw.keyword for kw in old_keywords]
            self.logger.debug(f"Stored {len(self.old_keyword_texts)} original {kind} keywords for slide ID {slide_id}")
    
    def redo(self):
        """
        Execute the command: replace the slide's keywords.
        """
        if not self.db:
            self.logger.error("Database service not available")
            return
            
        success = self.db.replace_slide_keywords(self.slide_id, self.kind, self.new_keyword_texts)
        if success:
            self.logger.debug(f"Replaced {self.kind} keywords for slide ID {self.slide_id}")
        else:
            self.logger.error(f"Failed to replace {self.kind} keywords for slide ID {self.slide_id}")
    
    def undo(self):
        """
        Undo the command: restore the original keywords.
        """
        if not self.db:
            self.logger.error("Database service not available")
            return
            
        success = self.db.replace_slide_keywords(self.slide_id, self.kind, self.old_keyword_texts)
        if success:
            self.logger.debug(f"Restored original {self.kind} keywords for slide ID {self.slide_id}")
        else:
            self.logger.error(f"Failed to restore original {self.kind} keywords for slide ID {self.slide_id}")
