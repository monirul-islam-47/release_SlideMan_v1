# src/slideman/ui/utils/enhanced_dialogs.py

import sys
import traceback
import platform
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTextEdit, QFrame, QWidget,
                               QMessageBox, QApplication, QCheckBox, QSplitter)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QClipboard
import logging
from typing import Optional, Dict, Any

class EnhancedErrorDialog(QDialog):
    """Enhanced error dialog with expandable details and debugging information."""
    
    def __init__(self, title: str, message: str, details: str = "", 
                 error_type: str = "Error", parent=None):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.details = details
        self.error_type = error_type
        self.logger = logging.getLogger(__name__)
        
        self.setWindowTitle(f"SlideMan - {error_type}")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Set up the error dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header section
        header_layout = QHBoxLayout()
        
        # Error icon
        icon_label = QLabel()
        if self.error_type.lower() == "warning":
            icon_text = "⚠️"
        elif self.error_type.lower() == "info":
            icon_text = "ℹ️"
        else:
            icon_text = "❌"
            
        icon_label.setText(icon_text)
        icon_font = QFont()
        icon_font.setPointSize(24)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignTop)
        
        # Message section
        message_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setWordWrap(True)
        
        # Message
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: #2c3e50; line-height: 1.4;")
        
        message_layout.addWidget(title_label)
        message_layout.addWidget(message_label)
        
        header_layout.addWidget(icon_label)
        header_layout.addLayout(message_layout)
        header_layout.setStretch(1, 1)
        
        layout.addLayout(header_layout)
        
        # Details section (collapsible)
        if self.details:
            self.details_frame = QFrame()
            self.details_frame.setFrameStyle(QFrame.Box)
            self.details_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                }
            """)
            
            details_layout = QVBoxLayout(self.details_frame)
            
            # Details header
            details_header = QHBoxLayout()
            
            self.details_toggle = QPushButton("▶ Show Details")
            self.details_toggle.setFlat(True)
            self.details_toggle.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    border: none;
                    padding: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(52, 152, 219, 0.1);
                }
            """)
            
            copy_button = QPushButton("📋 Copy Details")
            copy_button.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
            """)
            copy_button.clicked.connect(self._copy_details)
            
            details_header.addWidget(self.details_toggle)
            details_header.addStretch()
            details_header.addWidget(copy_button)
            
            # Details text (initially hidden)
            self.details_text = QTextEdit()
            self.details_text.setPlainText(self.details)
            self.details_text.setReadOnly(True)
            self.details_text.setMaximumHeight(200)
            self.details_text.setFont(QFont("Consolas", 9))
            self.details_text.hide()
            
            details_layout.addLayout(details_header)
            details_layout.addWidget(self.details_text)
            
            layout.addWidget(self.details_frame)
            
            # Connect toggle
            self.details_toggle.clicked.connect(self._toggle_details)
        
        # Buttons section
        buttons_layout = QHBoxLayout()
        
        # Report bug checkbox (for errors)
        if self.error_type.lower() == "error":
            self.report_checkbox = QCheckBox("Include in bug report")
            self.report_checkbox.setChecked(True)
            buttons_layout.addWidget(self.report_checkbox)
        
        buttons_layout.addStretch()
        
        # Action buttons
        if self.error_type.lower() == "error":
            self.report_button = QPushButton("🐛 Report Bug")
            self.report_button.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            self.report_button.clicked.connect(self._report_bug)
            buttons_layout.addWidget(self.report_button)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.ok_button.setDefault(True)
        buttons_layout.addWidget(self.ok_button)
        
        layout.addLayout(buttons_layout)
        
    def _connect_signals(self):
        """Connect dialog signals."""
        self.ok_button.clicked.connect(self.accept)
        
    def _toggle_details(self):
        """Toggle the details section visibility."""
        if self.details_text.isVisible():
            self.details_text.hide()
            self.details_toggle.setText("▶ Show Details")
            self.resize(self.width(), self.sizeHint().height())
        else:
            self.details_text.show()
            self.details_toggle.setText("▼ Hide Details")
            
    def _copy_details(self):
        """Copy details to clipboard."""
        clipboard = QApplication.clipboard()
        full_text = f"Title: {self.title}\n\nMessage: {self.message}\n\nDetails:\n{self.details}"
        clipboard.setText(full_text)
        
        # Show temporary feedback
        original_text = self.details_toggle.text()
        self.details_toggle.setText("✓ Copied!")
        QTimer.singleShot(2000, lambda: self.details_toggle.setText(original_text))
        
    def _report_bug(self):
        """Handle bug reporting."""
        # In a real implementation, this would open a bug report dialog
        # or send data to a bug tracking system
        bug_dialog = BugReportDialog(
            error_title=self.title,
            error_message=self.message,
            error_details=self.details,
            parent=self
        )
        bug_dialog.exec()
        
    @staticmethod
    def show_error(title: str, message: str, details: str = "", parent=None):
        """Show an error dialog."""
        dialog = EnhancedErrorDialog(title, message, details, "Error", parent)
        return dialog.exec()
        
    @staticmethod
    def show_warning(title: str, message: str, details: str = "", parent=None):
        """Show a warning dialog."""
        dialog = EnhancedErrorDialog(title, message, details, "Warning", parent)
        return dialog.exec()
        
    @staticmethod
    def show_info(title: str, message: str, details: str = "", parent=None):
        """Show an info dialog."""
        dialog = EnhancedErrorDialog(title, message, details, "Info", parent)
        return dialog.exec()


class BugReportDialog(QDialog):
    """Dialog for collecting bug report information."""
    
    def __init__(self, error_title: str = "", error_message: str = "", 
                 error_details: str = "", parent=None):
        super().__init__(parent)
        self.error_title = error_title
        self.error_message = error_message
        self.error_details = error_details
        
        self.setWindowTitle("Report Bug")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the bug report dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("🐛 Help us improve SlideMan")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Description
        desc_label = QLabel(
            "Please describe what you were doing when this error occurred. "
            "Your feedback helps us fix bugs and improve the application."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # User description
        user_desc_label = QLabel("What were you trying to do?")
        user_desc_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(user_desc_label)
        
        self.user_description = QTextEdit()
        self.user_description.setPlaceholderText(
            "Example: I was trying to import a PowerPoint file when the error occurred..."
        )
        self.user_description.setMaximumHeight(100)
        layout.addWidget(self.user_description)
        
        # System info
        system_info_label = QLabel("System Information (automatically included)")
        system_info_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(system_info_label)
        
        self.system_info = QTextEdit()
        self.system_info.setPlainText(self._get_system_info())
        self.system_info.setReadOnly(True)
        self.system_info.setMaximumHeight(120)
        self.system_info.setFont(QFont("Consolas", 9))
        layout.addWidget(self.system_info)
        
        # Error details
        if self.error_details:
            error_label = QLabel("Error Details")
            error_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(error_label)
            
            self.error_text = QTextEdit()
            self.error_text.setPlainText(f"{self.error_title}\n\n{self.error_message}\n\n{self.error_details}")
            self.error_text.setReadOnly(True)
            self.error_text.setMaximumHeight(100)
            self.error_text.setFont(QFont("Consolas", 9))
            layout.addWidget(self.error_text)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.send_button = QPushButton("📤 Send Report")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.send_button)
        
        layout.addLayout(buttons_layout)
        
        # Connect signals
        self.cancel_button.clicked.connect(self.reject)
        self.send_button.clicked.connect(self._send_report)
        
    def _get_system_info(self) -> str:
        """Get system information for bug reports."""
        try:
            info = []
            info.append(f"Platform: {platform.system()} {platform.release()}")
            info.append(f"Architecture: {platform.machine()}")
            info.append(f"Python: {sys.version}")
            
            # Try to get Qt version
            try:
                from PySide6 import __version__ as pyside_version
                info.append(f"PySide6: {pyside_version}")
            except ImportError:
                info.append("PySide6: Unknown")
                
            # Try to get app version (if available)
            try:
                app = QApplication.instance()
                if app:
                    info.append(f"SlideMan: {app.applicationVersion()}")
            except:
                info.append("SlideMan: Unknown version")
                
            return "\n".join(info)
        except Exception as e:
            return f"Error collecting system info: {e}"
            
    def _send_report(self):
        """Send the bug report."""
        # In a real implementation, this would send the report to a server
        # For now, we'll just copy it to clipboard and show instructions
        
        report = self._generate_report()
        
        clipboard = QApplication.clipboard()
        clipboard.setText(report)
        
        QMessageBox.information(
            self,
            "Bug Report Copied",
            "Your bug report has been copied to the clipboard.\n\n"
            "Please email it to: support@slideman.com\n"
            "or create an issue at: https://github.com/slideman/issues\n\n"
            "Thank you for helping us improve SlideMan!"
        )
        
        self.accept()
        
    def _generate_report(self) -> str:
        """Generate the full bug report text."""
        report_parts = []
        
        report_parts.append("=== SlideMan Bug Report ===")
        report_parts.append("")
        
        if self.user_description.toPlainText().strip():
            report_parts.append("User Description:")
            report_parts.append(self.user_description.toPlainText())
            report_parts.append("")
        
        if self.error_title or self.error_message:
            report_parts.append("Error Information:")
            if self.error_title:
                report_parts.append(f"Title: {self.error_title}")
            if self.error_message:
                report_parts.append(f"Message: {self.error_message}")
            report_parts.append("")
        
        if self.error_details:
            report_parts.append("Error Details:")
            report_parts.append(self.error_details)
            report_parts.append("")
        
        report_parts.append("System Information:")
        report_parts.append(self.system_info.toPlainText())
        
        return "\n".join(report_parts)


class ExceptionHandler:
    """Global exception handler with enhanced error dialogs."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._original_excepthook = sys.excepthook
        
    def install(self):
        """Install the exception handler."""
        sys.excepthook = self.handle_exception
        
    def uninstall(self):
        """Restore the original exception handler."""
        sys.excepthook = self._original_excepthook
        
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        # Log the exception
        self.logger.critical(
            "Uncaught exception", 
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        # Format the error
        error_title = f"Unexpected Error: {exc_type.__name__}"
        error_message = str(exc_value) if exc_value else "An unexpected error occurred"
        error_details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # Show enhanced error dialog
        try:
            EnhancedErrorDialog.show_error(
                error_title,
                error_message + "\n\nThe application may continue to work, but some features might be unstable.",
                error_details
            )
        except Exception as dialog_error:
            # Fallback to basic message box if our dialog fails
            self.logger.error(f"Error dialog failed: {dialog_error}")
            QMessageBox.critical(
                None,
                "Critical Error",
                f"A critical error occurred:\n\n{error_message}\n\n"
                "Please restart the application."
            )


# Global exception handler instance
exception_handler = ExceptionHandler()