"""Centralized message box utilities for consistent error handling and user feedback."""

from typing import Optional
from PySide6.QtWidgets import QWidget, QMessageBox

from ...services.exceptions import (
    DatabaseError, FileOperationError, ResourceNotFoundError, 
    ValidationError, PowerPointError, ExportError
)


def show_database_error(parent: Optional[QWidget], error: DatabaseError) -> None:
    """Show a database error message box.
    
    Args:
        parent: Parent widget for the message box
        error: The database error to display
    """
    QMessageBox.critical(
        parent,
        "Database Error",
        f"A database error occurred:\n\n{str(error)}"
    )


def show_file_operation_error(parent: Optional[QWidget], error: FileOperationError) -> None:
    """Show a file operation error message box.
    
    Args:
        parent: Parent widget for the message box
        error: The file operation error to display
    """
    QMessageBox.critical(
        parent,
        "File Operation Error",
        f"Failed to perform file operation:\n\n{str(error)}"
    )


def show_powerpoint_error(parent: Optional[QWidget], error: PowerPointError) -> None:
    """Show a PowerPoint error message box.
    
    Args:
        parent: Parent widget for the message box
        error: The PowerPoint error to display
    """
    QMessageBox.critical(
        parent,
        "PowerPoint Error",
        f"PowerPoint operation failed:\n\n{str(error)}"
    )


def show_validation_error(parent: Optional[QWidget], error: ValidationError) -> None:
    """Show a validation error message box.
    
    Args:
        parent: Parent widget for the message box
        error: The validation error to display
    """
    QMessageBox.warning(
        parent,
        "Validation Error",
        f"Invalid input:\n\n{str(error)}"
    )


def show_export_error(parent: Optional[QWidget], error: ExportError) -> None:
    """Show an export error message box.
    
    Args:
        parent: Parent widget for the message box
        error: The export error to display
    """
    QMessageBox.critical(
        parent,
        "Export Error",
        f"Failed to export presentation:\n\n{str(error)}"
    )


def show_resource_not_found(parent: Optional[QWidget], error: ResourceNotFoundError) -> None:
    """Show a resource not found error message box.
    
    Args:
        parent: Parent widget for the message box
        error: The resource not found error to display
    """
    QMessageBox.warning(
        parent,
        "Resource Not Found",
        f"The requested resource was not found:\n\n{str(error)}"
    )


def show_generic_error(parent: Optional[QWidget], title: str, message: str) -> None:
    """Show a generic error message box.
    
    Args:
        parent: Parent widget for the message box
        title: Title for the message box
        message: Error message to display
    """
    QMessageBox.critical(parent, title, message)


def show_warning(parent: Optional[QWidget], title: str, message: str) -> None:
    """Show a warning message box.
    
    Args:
        parent: Parent widget for the message box
        title: Title for the message box
        message: Warning message to display
    """
    QMessageBox.warning(parent, title, message)


def show_info(parent: Optional[QWidget], title: str, message: str) -> None:
    """Show an information message box.
    
    Args:
        parent: Parent widget for the message box
        title: Title for the message box
        message: Information message to display
    """
    QMessageBox.information(parent, title, message)


def ask_confirmation(
    parent: Optional[QWidget], 
    title: str, 
    message: str,
    default_button: QMessageBox.StandardButton = QMessageBox.StandardButton.No
) -> bool:
    """Show a yes/no confirmation dialog.
    
    Args:
        parent: Parent widget for the message box
        title: Title for the message box
        message: Question to ask
        default_button: Default button selection
        
    Returns:
        True if user clicked Yes, False otherwise
    """
    reply = QMessageBox.question(
        parent, 
        title, 
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        default_button
    )
    return reply == QMessageBox.StandardButton.Yes


def ask_save_changes(parent: Optional[QWidget], document_name: str = "document") -> QMessageBox.StandardButton:
    """Show a save changes dialog with Save, Don't Save, and Cancel options.
    
    Args:
        parent: Parent widget for the message box
        document_name: Name of the document being edited
        
    Returns:
        The button that was clicked
    """
    return QMessageBox.question(
        parent,
        "Save Changes?",
        f"Do you want to save changes to {document_name}?",
        QMessageBox.StandardButton.Save | 
        QMessageBox.StandardButton.Discard | 
        QMessageBox.StandardButton.Cancel,
        QMessageBox.StandardButton.Save
    )


def handle_service_error(
    parent: Optional[QWidget], 
    error: Exception,
    operation: str = "operation"
) -> None:
    """Handle service layer errors with appropriate message boxes.
    
    Args:
        parent: Parent widget for the message box
        error: The exception that occurred
        operation: Description of the operation that failed
    """
    if isinstance(error, DatabaseError):
        show_database_error(parent, error)
    elif isinstance(error, FileOperationError):
        show_file_operation_error(parent, error)
    elif isinstance(error, PowerPointError):
        show_powerpoint_error(parent, error)
    elif isinstance(error, ValidationError):
        show_validation_error(parent, error)
    elif isinstance(error, ExportError):
        show_export_error(parent, error)
    elif isinstance(error, ResourceNotFoundError):
        show_resource_not_found(parent, error)
    else:
        show_generic_error(
            parent,
            "Operation Failed",
            f"Failed to {operation}:\n\n{str(error)}"
        )