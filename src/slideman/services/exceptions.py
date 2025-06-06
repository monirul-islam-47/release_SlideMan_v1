# src/slideman/services/exceptions.py
"""
Custom exceptions for the SLIDEMAN service layer.

This module provides standardized exception classes for consistent error handling
across all services. Each exception type represents a specific category of error
that can occur in the application.
"""

from typing import Optional, Any


class SlidemanException(Exception):
    """Base exception for all SLIDEMAN-specific errors."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details


class DatabaseError(SlidemanException):
    """Raised when database operations fail."""
    pass


class ConnectionError(DatabaseError):
    """Raised when database connection cannot be established."""
    pass


class TransactionError(DatabaseError):
    """Raised when database transaction fails."""
    pass


class FileOperationError(SlidemanException):
    """Raised when file system operations fail."""
    pass


class FileNotFoundError(FileOperationError):
    """Raised when a required file cannot be found."""
    pass


class InsufficientSpaceError(FileOperationError):
    """Raised when there is not enough disk space for an operation."""
    pass


class PowerPointError(SlidemanException):
    """Raised when PowerPoint COM operations fail."""
    pass


class COMInitializationError(PowerPointError):
    """Raised when COM cannot be initialized."""
    pass


class PresentationAccessError(PowerPointError):
    """Raised when a PowerPoint presentation cannot be accessed."""
    pass


class SlideExportError(PowerPointError):
    """Raised when slide export operations fail."""
    pass


class ResourceNotFoundError(SlidemanException):
    """Raised when a requested resource (project, slide, keyword) is not found."""
    
    def __init__(self, resource_type: str, resource_id: Any):
        super().__init__(f"{resource_type} with ID {resource_id} not found")
        self.resource_type = resource_type
        self.resource_id = resource_id


class ValidationError(SlidemanException):
    """Raised when input validation fails."""
    pass


class DuplicateResourceError(SlidemanException):
    """Raised when attempting to create a duplicate resource."""
    
    def __init__(self, resource_type: str, identifier: str):
        super().__init__(f"{resource_type} '{identifier}' already exists")
        self.resource_type = resource_type
        self.identifier = identifier


class ServiceNotAvailableError(SlidemanException):
    """Raised when a required service is not available."""
    
    def __init__(self, service_name: str):
        super().__init__(f"Service '{service_name}' is not available")
        self.service_name = service_name


class OperationCancelledError(SlidemanException):
    """Raised when an operation is cancelled by user or system."""
    pass


class ThreadSafetyError(SlidemanException):
    """Raised when thread safety violations are detected."""
    pass