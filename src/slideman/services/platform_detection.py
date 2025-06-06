# src/slideman/services/platform_detection.py

import sys
import platform
import logging
from typing import Tuple, Optional
from PySide6.QtWidgets import QMessageBox, QWidget

logger = logging.getLogger(__name__)

class PlatformCapabilities:
    """Detects and provides information about platform capabilities."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._powerpoint_available = None
        self._libreoffice_available = None
        
    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return platform.system() == "Windows"
    
    def is_macos(self) -> bool:
        """Check if running on macOS."""
        return platform.system() == "Darwin"
    
    def is_linux(self) -> bool:
        """Check if running on Linux."""
        return platform.system() == "Linux"
    
    def check_powerpoint_com(self) -> Tuple[bool, Optional[str]]:
        """
        Check if PowerPoint COM automation is available.
        
        Returns:
            Tuple of (is_available, error_message)
        """
        if not self.is_windows():
            return False, "PowerPoint COM automation is only available on Windows"
            
        if self._powerpoint_available is not None:
            return self._powerpoint_available, None
            
        try:
            import pythoncom
            import win32com.client
            import pywintypes
            
            # Try to create PowerPoint COM object
            pythoncom.CoInitialize()
            try:
                ppt = win32com.client.Dispatch("PowerPoint.Application")
                # Test basic functionality
                ppt.Visible = False
                version = ppt.Version
                ppt.Quit()
                self._powerpoint_available = True
                self.logger.info(f"PowerPoint COM available (version {version})")
                return True, None
                
            except pywintypes.com_error as e:
                error_msg = f"PowerPoint is installed but COM automation failed: {e}"
                self.logger.warning(error_msg)
                self._powerpoint_available = False
                return False, error_msg
                
            finally:
                pythoncom.CoUninitialize()
                
        except ImportError as e:
            error_msg = "pywin32 library not installed - PowerPoint COM unavailable"
            self.logger.warning(error_msg)
            self._powerpoint_available = False
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error checking PowerPoint COM: {e}"
            self.logger.error(error_msg)
            self._powerpoint_available = False
            return False, error_msg
    
    def check_libreoffice(self) -> Tuple[bool, Optional[str]]:
        """
        Check if LibreOffice is available for slide conversion.
        
        Returns:
            Tuple of (is_available, error_message)
        """
        if self._libreoffice_available is not None:
            return self._libreoffice_available, None
            
        try:
            import subprocess
            
            # Try to find LibreOffice executable
            possible_paths = [
                "libreoffice",  # Linux/macOS
                "soffice",      # Alternative name
                r"C:\Program Files\LibreOffice\program\soffice.exe",  # Windows default
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",  # Windows x86
            ]
            
            for path in possible_paths:
                try:
                    result = subprocess.run([path, "--version"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        version_info = result.stdout.strip()
                        self.logger.info(f"LibreOffice found: {version_info}")
                        self._libreoffice_available = True
                        return True, None
                except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                    continue
                    
            self._libreoffice_available = False
            return False, "LibreOffice not found in standard locations"
            
        except Exception as e:
            error_msg = f"Error checking LibreOffice availability: {e}"
            self.logger.error(error_msg)
            self._libreoffice_available = False
            return False, error_msg
    
    def get_conversion_capabilities(self) -> dict:
        """
        Get comprehensive information about slide conversion capabilities.
        
        Returns:
            Dictionary with capability information
        """
        capabilities = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": sys.version,
            "converters": {}
        }
        
        # Check PowerPoint COM
        ppt_available, ppt_error = self.check_powerpoint_com()
        capabilities["converters"]["powerpoint_com"] = {
            "available": ppt_available,
            "error": ppt_error,
            "recommended": self.is_windows() and ppt_available
        }
        
        # Check LibreOffice
        lo_available, lo_error = self.check_libreoffice()
        capabilities["converters"]["libreoffice"] = {
            "available": lo_available,
            "error": lo_error,
            "recommended": not self.is_windows() or not ppt_available
        }
        
        return capabilities
    
    def show_converter_setup_dialog(self, parent: QWidget = None) -> bool:
        """
        Show a dialog to help users set up slide conversion.
        
        Returns:
            True if user wants to continue, False if they want to quit
        """
        capabilities = self.get_conversion_capabilities()
        ppt_info = capabilities["converters"]["powerpoint_com"]
        lo_info = capabilities["converters"]["libreoffice"]
        
        # If PowerPoint is available, no need for dialog
        if ppt_info["available"]:
            return True
            
        # Build dialog message
        title = "Slide Conversion Setup"
        
        if self.is_windows():
            message = (
                "<b>PowerPoint Not Detected</b><br><br>"
                "SlideMan needs PowerPoint to convert slides to images for viewing and tagging.<br><br>"
                "<b>To fix this:</b><br>"
                "• Install Microsoft PowerPoint (part of Microsoft 365)<br>"
                "• Or install LibreOffice as a free alternative<br><br>"
            )
            
            if lo_info["available"]:
                message += "✅ LibreOffice detected - you can use this as an alternative!"
            else:
                message += (
                    "📥 <b>Free Alternative:</b><br>"
                    "Download LibreOffice from <a href='https://www.libreoffice.org/download/'>libreoffice.org</a><br>"
                    "After installation, restart SlideMan."
                )
        else:
            # macOS/Linux
            message = (
                "<b>Slide Conversion Setup</b><br><br>"
                "SlideMan can convert PowerPoint slides for viewing and tagging.<br><br>"
            )
            
            if lo_info["available"]:
                message += "✅ LibreOffice detected and ready to use!"
            else:
                message += (
                    "📥 <b>Install LibreOffice (Free):</b><br>"
                    "Download from <a href='https://www.libreoffice.org/download/'>libreoffice.org</a><br>"
                    "After installation, restart SlideMan to enable slide conversion."
                )
        
        message += "<br><br><b>You can still use SlideMan without slide conversion</b>, but you won't see slide previews."
        
        # Show dialog
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setTextFormat(1)  # RichText
        msg_box.setIcon(QMessageBox.Information)
        
        # Add custom buttons
        continue_btn = msg_box.addButton("Continue Anyway", QMessageBox.AcceptRole)
        setup_btn = msg_box.addButton("Setup Instructions", QMessageBox.HelpRole)
        quit_btn = msg_box.addButton("Quit", QMessageBox.RejectRole)
        
        msg_box.setDefaultButton(continue_btn)
        
        result = msg_box.exec()
        clicked_button = msg_box.clickedButton()
        
        if clicked_button == quit_btn:
            return False
        elif clicked_button == setup_btn:
            self._show_detailed_setup_instructions(parent)
            return True
        else:
            return True
    
    def _show_detailed_setup_instructions(self, parent: QWidget = None):
        """Show detailed setup instructions."""
        if self.is_windows():
            instructions = (
                "<b>Windows Setup Instructions</b><br><br>"
                
                "<b>Option 1: Microsoft PowerPoint (Recommended)</b><br>"
                "• Subscribe to Microsoft 365 at <a href='https://www.microsoft.com/microsoft-365'>microsoft.com</a><br>"
                "• Install PowerPoint through the Microsoft 365 installer<br>"
                "• Restart SlideMan after installation<br><br>"
                
                "<b>Option 2: LibreOffice (Free)</b><br>"
                "• Download from <a href='https://www.libreoffice.org/download/'>libreoffice.org</a><br>"
                "• Run the installer with default settings<br>"
                "• Restart SlideMan after installation<br><br>"
                
                "<b>Troubleshooting:</b><br>"
                "• Make sure to restart SlideMan after installing either program<br>"
                "• Run SlideMan as Administrator if you still have issues<br>"
                "• Check Windows Event Viewer if COM errors persist"
            )
        else:
            instructions = (
                "<b>macOS/Linux Setup Instructions</b><br><br>"
                
                "<b>LibreOffice Installation</b><br>"
                "• Download from <a href='https://www.libreoffice.org/download/'>libreoffice.org</a><br>"
                "• Choose your platform (macOS or Linux)<br>"
                "• Install with default settings<br>"
                "• Restart SlideMan after installation<br><br>"
                
                "<b>Alternative: Docker Setup</b><br>"
                "• Install Docker Desktop<br>"
                "• Pull the LibreOffice container: <code>docker pull linuxserver/libreoffice</code><br>"
                "• Configure SlideMan to use Docker converter (Advanced)<br><br>"
                
                "<b>Note:</b> PowerPoint is not available on macOS/Linux, but LibreOffice "
                "provides excellent compatibility with PowerPoint files."
            )
        
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle("Detailed Setup Instructions")
        msg_box.setText(instructions)
        msg_box.setTextFormat(1)  # RichText
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec()


# Global instance
platform_capabilities = PlatformCapabilities()