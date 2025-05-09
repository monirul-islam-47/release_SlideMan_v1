# src/slideman/commands/manage_element_keyword.py

from PySide6.QtGui import QUndoCommand
import logging

from ..app_state import app_state

logger = logging.getLogger(__name__)

class LinkElementKeywordCmd(QUndoCommand):
    """
    Command to link an element to a keyword.
    Supports undo/redo operations.
    """
    def __init__(self, element_id: int, keyword_id: int, description: str = None):
        """
        Initialize the command.
        
        Args:
            element_id: The ID of the element
            keyword_id: The ID of the keyword
            description: Optional description for the undo stack
        """
        if description is None:
            description = f"Link keyword to element"
        super().__init__(description)
        self.element_id = element_id
        self.keyword_id = keyword_id
        self.logger = logging.getLogger(__name__)
        self.db = app_state.db_service
    
    def redo(self):
        """
        Execute the command: link the element to the keyword.
        """
        if not self.db:
            self.logger.error("Database service not available")
            return
            
        success = self.db.link_element_keyword(self.element_id, self.keyword_id)
        if success:
            self.logger.debug(f"Linked element ID {self.element_id} to keyword ID {self.keyword_id}")
        else:
            self.logger.error(f"Failed to link element ID {self.element_id} to keyword ID {self.keyword_id}")
    
    def undo(self):
        """
        Undo the command: unlink the element from the keyword.
        """
        if not self.db:
            self.logger.error("Database service not available")
            return
            
        success = self.db.unlink_element_keyword(self.element_id, self.keyword_id)
        if success:
            self.logger.debug(f"Unlinked element ID {self.element_id} from keyword ID {self.keyword_id}")
        else:
            self.logger.error(f"Failed to unlink element ID {self.element_id} from keyword ID {self.keyword_id}")


class UnlinkElementKeywordCmd(QUndoCommand):
    """
    Command to unlink an element from a keyword.
    Supports undo/redo operations.
    """
    def __init__(self, element_id: int, keyword_id: int, description: str = None):
        """
        Initialize the command.
        
        Args:
            element_id: The ID of the element
            keyword_id: The ID of the keyword
            description: Optional description for the undo stack
        """
        if description is None:
            description = f"Remove keyword from element"
        super().__init__(description)
        self.element_id = element_id
        self.keyword_id = keyword_id
        self.logger = logging.getLogger(__name__)
        self.db = app_state.db_service
    
    def redo(self):
        """
        Execute the command: unlink the element from the keyword.
        """
        if not self.db:
            self.logger.error("Database service not available")
            return
            
        success = self.db.unlink_element_keyword(self.element_id, self.keyword_id)
        if success:
            self.logger.debug(f"Unlinked element ID {self.element_id} from keyword ID {self.keyword_id}")
        else:
            self.logger.error(f"Failed to unlink element ID {self.element_id} from keyword ID {self.keyword_id}")
    
    def undo(self):
        """
        Undo the command: link the element to the keyword.
        """
        if not self.db:
            self.logger.error("Database service not available")
            return
            
        success = self.db.link_element_keyword(self.element_id, self.keyword_id)
        if success:
            self.logger.debug(f"Linked element ID {self.element_id} to keyword ID {self.keyword_id}")
        else:
            self.logger.error(f"Failed to link element ID {self.element_id} to keyword ID {self.keyword_id}")
