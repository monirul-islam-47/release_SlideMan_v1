# src/slideman/services/debug_info.py

import sys
import platform
import os
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

class DebugInfoCollector:
    """Collects comprehensive debug information for troubleshooting."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def collect_all_info(self) -> Dict[str, Any]:
        """Collect all available debug information."""
        info = {
            "timestamp": datetime.now().isoformat(),
            "system": self._collect_system_info(),
            "application": self._collect_app_info(),
            "environment": self._collect_environment_info(),
            "database": self._collect_database_info(),
            "recent_logs": self._collect_recent_logs(),
            "settings": self._collect_settings_info(),
            "platform_capabilities": self._collect_platform_capabilities()
        }
        
        return info
        
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information."""
        try:
            return {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "python_version": sys.version,
                "python_executable": sys.executable,
                "python_path": sys.path[:5],  # First 5 entries only
                "working_directory": os.getcwd(),
                "user_home": str(Path.home()),
                "environment_vars": {
                    key: value for key, value in os.environ.items() 
                    if key.upper() in [
                        'PATH', 'PYTHONPATH', 'APPDATA', 'LOCALAPPDATA', 
                        'TEMP', 'TMP', 'USERNAME', 'COMPUTERNAME'
                    ]
                }
            }
        except Exception as e:
            self.logger.error(f"Error collecting system info: {e}")
            return {"error": str(e)}
            
    def _collect_app_info(self) -> Dict[str, Any]:
        """Collect application-specific information."""
        try:
            app = QApplication.instance()
            app_info = {
                "app_exists": app is not None,
                "qt_version": "Unknown",
                "pyside_version": "Unknown"
            }
            
            if app:
                app_info.update({
                    "app_name": app.applicationName(),
                    "app_version": app.applicationVersion(),
                    "organization_name": app.organizationName(),
                    "organization_domain": app.organizationDomain()
                })
                
            # Try to get Qt/PySide versions
            try:
                from PySide6 import __version__ as pyside_version
                app_info["pyside_version"] = pyside_version
            except ImportError:
                pass
                
            try:
                from PySide6.QtCore import qVersion
                app_info["qt_version"] = qVersion()
            except ImportError:
                pass
                
            # Add module information
            try:
                import pythoncom
                app_info["pythoncom_available"] = True
            except ImportError:
                app_info["pythoncom_available"] = False
                
            try:
                import win32com.client
                app_info["win32com_available"] = True
            except ImportError:
                app_info["win32com_available"] = False
                
            try:
                from pptx import Presentation
                app_info["python_pptx_available"] = True
            except ImportError:
                app_info["python_pptx_available"] = False
                
            return app_info
            
        except Exception as e:
            self.logger.error(f"Error collecting app info: {e}")
            return {"error": str(e)}
            
    def _collect_environment_info(self) -> Dict[str, Any]:
        """Collect environment-specific information."""
        try:
            # Check for common issues
            issues = []
            
            # Check write permissions
            try:
                temp_file = Path.home() / "Documents" / "test_write.tmp"
                temp_file.write_text("test")
                temp_file.unlink()
            except Exception:
                issues.append("Cannot write to Documents folder")
                
            # Check AppData access
            try:
                if platform.system() == "Windows":
                    appdata = Path(os.environ.get("APPDATA", ""))
                    if not appdata.exists():
                        issues.append("APPDATA directory not accessible")
            except Exception:
                issues.append("Error checking AppData access")
                
            return {
                "detected_issues": issues,
                "disk_space_home": self._get_disk_space(Path.home()),
                "disk_space_temp": self._get_disk_space(Path.home() / "temp"),
                "file_associations": self._check_file_associations()
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting environment info: {e}")
            return {"error": str(e)}
            
    def _collect_database_info(self) -> Dict[str, Any]:
        """Collect database-related information."""
        try:
            from ..services.database import Database
            from ..app_state import app_state
            
            db_info = {
                "database_class_available": True,
                "app_state_available": hasattr(app_state, 'db_service')
            }
            
            if hasattr(app_state, 'db_service') and app_state.db_service:
                db = app_state.db_service
                db_info.update({
                    "database_path": str(db.db_path) if hasattr(db, 'db_path') else "Unknown",
                    "database_exists": db.db_path.exists() if hasattr(db, 'db_path') else False,
                })
                
                # Try to get basic stats
                try:
                    projects = db.get_all_projects()
                    db_info["project_count"] = len(projects)
                except Exception as e:
                    db_info["database_error"] = str(e)
                    
            return db_info
            
        except Exception as e:
            self.logger.error(f"Error collecting database info: {e}")
            return {"error": str(e)}
            
    def _collect_recent_logs(self) -> List[str]:
        """Collect recent log entries."""
        try:
            # This is a simplified version - in a real implementation,
            # you'd want to read from the actual log files
            log_entries = []
            
            # Get recent log records from the logging system
            # This would require setting up a custom log handler to capture recent entries
            log_entries.append("Log collection not fully implemented - check log files directly")
            
            return log_entries[-50:]  # Last 50 entries
            
        except Exception as e:
            self.logger.error(f"Error collecting logs: {e}")
            return [f"Error collecting logs: {e}"]
            
    def _collect_settings_info(self) -> Dict[str, Any]:
        """Collect application settings (non-sensitive)."""
        try:
            settings = QSettings("SlidemanDev", "Slideman")
            
            # Only collect non-sensitive settings
            safe_keys = [
                "first_run_completed",
                "completed_actions", 
                "theme",
                "mainWindowGeometry",
                "user_level"
            ]
            
            settings_info = {}
            for key in safe_keys:
                if settings.contains(key):
                    settings_info[key] = settings.value(key)
                    
            return settings_info
            
        except Exception as e:
            self.logger.error(f"Error collecting settings: {e}")
            return {"error": str(e)}
            
    def _collect_platform_capabilities(self) -> Dict[str, Any]:
        """Collect platform capability information."""
        try:
            from .platform_detection import platform_capabilities
            
            capabilities = platform_capabilities.get_conversion_capabilities()
            return capabilities
            
        except Exception as e:
            self.logger.error(f"Error collecting platform capabilities: {e}")
            return {"error": str(e)}
            
    def _get_disk_space(self, path: Path) -> Dict[str, Any]:
        """Get disk space information for a path."""
        try:
            if not path.exists():
                return {"error": "Path does not exist"}
                
            stat = os.statvfs(str(path)) if hasattr(os, 'statvfs') else None
            if stat:
                return {
                    "total_bytes": stat.f_blocks * stat.f_frsize,
                    "free_bytes": stat.f_bavail * stat.f_frsize,
                    "used_bytes": (stat.f_blocks - stat.f_bavail) * stat.f_frsize
                }
            else:
                # Windows fallback
                try:
                    import shutil
                    total, used, free = shutil.disk_usage(str(path))
                    return {
                        "total_bytes": total,
                        "free_bytes": free,
                        "used_bytes": used
                    }
                except Exception:
                    return {"error": "Cannot determine disk space"}
                    
        except Exception as e:
            return {"error": str(e)}
            
    def _check_file_associations(self) -> Dict[str, Any]:
        """Check file associations for PowerPoint files."""
        try:
            associations = {}
            
            if platform.system() == "Windows":
                try:
                    import winreg
                    
                    # Check .pptx association
                    try:
                        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ".pptx") as key:
                            prog_id = winreg.QueryValue(key, "")
                            associations["pptx_prog_id"] = prog_id
                    except Exception:
                        associations["pptx_prog_id"] = "Not found"
                        
                except ImportError:
                    associations["error"] = "winreg not available"
                    
            return associations
            
        except Exception as e:
            return {"error": str(e)}
            
    def save_debug_info(self, file_path: Path = None) -> Path:
        """Save debug information to a file."""
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = Path.home() / "Documents" / f"slideman_debug_{timestamp}.json"
            
        debug_info = self.collect_all_info()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(debug_info, f, indent=2, default=str)
                
            self.logger.info(f"Debug info saved to: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Error saving debug info: {e}")
            raise
            
    def get_debug_summary(self) -> str:
        """Get a text summary of debug information."""
        info = self.collect_all_info()
        
        lines = []
        lines.append("=== SlideMan Debug Summary ===")
        lines.append(f"Generated: {info['timestamp']}")
        lines.append("")
        
        # System info
        sys_info = info.get('system', {})
        lines.append(f"Platform: {sys_info.get('platform', 'Unknown')} {sys_info.get('platform_release', '')}")
        lines.append(f"Python: {sys_info.get('python_version', 'Unknown')}")
        
        # App info
        app_info = info.get('application', {})
        lines.append(f"PySide6: {app_info.get('pyside_version', 'Unknown')}")
        lines.append(f"Qt: {app_info.get('qt_version', 'Unknown')}")
        
        # Platform capabilities
        capabilities = info.get('platform_capabilities', {})
        converters = capabilities.get('converters', {})
        ppt_info = converters.get('powerpoint_com', {})
        lines.append(f"PowerPoint COM: {'Available' if ppt_info.get('available') else 'Not Available'}")
        
        # Database info
        db_info = info.get('database', {})
        lines.append(f"Projects: {db_info.get('project_count', 'Unknown')}")
        
        # Issues
        env_info = info.get('environment', {})
        issues = env_info.get('detected_issues', [])
        if issues:
            lines.append("")
            lines.append("Detected Issues:")
            for issue in issues:
                lines.append(f"  - {issue}")
                
        return "\n".join(lines)


# Global instance
debug_collector = DebugInfoCollector()