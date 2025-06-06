"""
Base command class for standardized command pattern implementation.

This module provides a base class for all commands in the SLIDEMAN application,
ensuring consistent error handling, logging, and service access across all commands.
"""

import logging
from typing import Dict, Any, Optional
from PySide6.QtGui import QUndoCommand

from ..services.service_registry import service_registry
from ..services.exceptions import (
    SlidemanException, DatabaseError, ValidationError
)


class BaseCommand(QUndoCommand):
    """
    Base class for all undoable commands in SLIDEMAN.
    
    This class provides:
    - Standardized service access via dependency injection
    - Consistent error handling and logging
    - Common functionality for all commands
    """
    
    def __init__(self, description: str, services: Optional[Dict[str, Any]] = None):
        """
        Initialize the base command.
        
        Args:
            description: Human-readable description of the command
            services: Optional dictionary of services. If not provided,
                     services will be retrieved from the registry.
        """
        super().__init__(description)
        self._services = services or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self._executed = False
        self._error: Optional[Exception] = None
        
    def get_service(self, service_name: str) -> Optional[Any]:
        """
        Get a service by name.
        
        First checks the injected services, then falls back to the registry.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            The service instance or None if not found
        """
        # Check injected services first
        if service_name in self._services:
            return self._services[service_name]
            
        # Fall back to registry
        return service_registry.get(service_name)
        
    def get_required_service(self, service_name: str) -> Any:
        """
        Get a required service by name.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            The service instance
            
        Raises:
            ValidationError: If the service is not found
        """
        service = self.get_service(service_name)
        if service is None:
            raise ValidationError(f"Required service '{service_name}' not available")
        return service
        
    def redo(self) -> None:
        """
        Execute the command.
        
        This method wraps do_execute() with error handling and logging.
        """
        try:
            self.logger.info(f"Executing: {self.text()}")
            self.do_execute()
            self._executed = True
            self._error = None
            self.logger.info(f"Successfully executed: {self.text()}")
            
        except SlidemanException as e:
            # Handle known exceptions
            self._error = e
            self.logger.error(f"Error executing {self.text()}: {e}", exc_info=True)
            self.handle_error(e)
            
        except Exception as e:
            # Handle unexpected exceptions
            self._error = e
            self.logger.error(f"Unexpected error executing {self.text()}: {e}", exc_info=True)
            self.handle_error(e)
            
    def undo(self) -> None:
        """
        Undo the command.
        
        This method wraps do_undo() with error handling and logging.
        """
        if not self._executed:
            self.logger.warning(f"Cannot undo {self.text()}: Command was not executed successfully")
            return
            
        try:
            self.logger.info(f"Undoing: {self.text()}")
            self.do_undo()
            self._executed = False
            self.logger.info(f"Successfully undone: {self.text()}")
            
        except SlidemanException as e:
            # Handle known exceptions
            self.logger.error(f"Error undoing {self.text()}: {e}", exc_info=True)
            self.handle_error(e)
            
        except Exception as e:
            # Handle unexpected exceptions
            self.logger.error(f"Unexpected error undoing {self.text()}: {e}", exc_info=True)
            self.handle_error(e)
            
    def do_execute(self) -> None:
        """
        Perform the actual command execution.
        
        Subclasses must implement this method.
        
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement do_execute()")
        
    def do_undo(self) -> None:
        """
        Perform the actual command undo.
        
        Subclasses must implement this method.
        
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement do_undo()")
        
    def handle_error(self, error: Exception) -> None:
        """
        Handle errors that occur during command execution.
        
        This method can be overridden by subclasses to provide
        custom error handling, such as showing user notifications.
        
        Args:
            error: The exception that occurred
        """
        # Default implementation just logs
        # Subclasses can override to show UI notifications
        pass
        
    def merge_with(self, other: QUndoCommand) -> bool:
        """
        Attempt to merge this command with another.
        
        By default, commands don't merge. Subclasses can override
        this to implement command merging for better undo/redo UX.
        
        Args:
            other: The command to potentially merge with
            
        Returns:
            True if the commands were merged
        """
        return False
        
    @property
    def was_successful(self) -> bool:
        """Check if the command executed successfully."""
        return self._executed and self._error is None
        
    @property
    def error(self) -> Optional[Exception]:
        """Get any error that occurred during execution."""
        return self._error