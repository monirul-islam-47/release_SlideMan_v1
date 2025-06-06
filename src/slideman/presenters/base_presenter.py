"""
Base presenter class and view interface for the MVP pattern.

This module defines the base classes for implementing the Model-View-Presenter pattern
in the SLIDEMAN application. The presenter handles all business logic and coordinates
between the view (UI) and services.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from PySide6.QtCore import QObject


class IView(ABC):
    """
    Base interface for all views in the MVP pattern.
    
    Views should implement this interface to ensure proper communication
    with their presenters.
    """
    
    @abstractmethod
    def show_error(self, title: str, message: str) -> None:
        """Display an error message to the user."""
        pass
    
    @abstractmethod
    def show_warning(self, title: str, message: str) -> None:
        """Display a warning message to the user."""
        pass
    
    @abstractmethod
    def show_info(self, title: str, message: str) -> None:
        """Display an information message to the user."""
        pass
    
    @abstractmethod
    def set_busy(self, busy: bool, message: str = "") -> None:
        """Set the view's busy state with an optional status message."""
        pass


class BasePresenter(QObject):
    """
    Base presenter class for the MVP pattern.
    
    This class provides common functionality for all presenters, including:
    - View reference management
    - Service injection
    - Logging setup
    - Common error handling
    """
    
    def __init__(self, view: IView, services: Dict[str, Any]):
        """
        Initialize the base presenter.
        
        Args:
            view: The view this presenter manages
            services: Dictionary of services injected into the presenter
        """
        super().__init__()
        self._view = view
        self._services = services
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @property
    def view(self) -> IView:
        """Get the view associated with this presenter."""
        return self._view
        
    def get_service(self, service_name: str) -> Optional[Any]:
        """
        Get a service by name.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            The service instance or None if not found
        """
        return self._services.get(service_name)
        
    def handle_error(self, error: Exception, title: str = "Error") -> None:
        """
        Handle an error by logging it and showing it to the user.
        
        Args:
            error: The exception that occurred
            title: Title for the error dialog
        """
        self.logger.error(f"{title}: {error}", exc_info=True)
        self._view.show_error(title, str(error))
        
    def handle_warning(self, message: str, title: str = "Warning") -> None:
        """
        Handle a warning by logging it and showing it to the user.
        
        Args:
            message: The warning message
            title: Title for the warning dialog
        """
        self.logger.warning(f"{title}: {message}")
        self._view.show_warning(title, message)
        
    def handle_info(self, message: str, title: str = "Information") -> None:
        """
        Show an information message to the user.
        
        Args:
            message: The information message
            title: Title for the info dialog
        """
        self.logger.info(f"{title}: {message}")
        self._view.show_info(title, message)
        
    def cleanup(self) -> None:
        """
        Clean up presenter resources.
        
        This method should be called when the presenter is no longer needed.
        Subclasses should override this to perform specific cleanup.
        """
        pass