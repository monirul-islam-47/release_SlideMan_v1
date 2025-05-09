# src/slideman/theme.py
from PySide6.QtCore import QFile, QTextStream, QIODevice
from PySide6.QtWidgets import QApplication
import logging # For logging errors

_current_theme = "dark" # Default

def load_stylesheet(theme_name: str) -> str:
    logger = logging.getLogger(__name__)
    qss_path = f":/qss/{theme_name}.qss"
    file = QFile(qss_path)
    stylesheet = ""
    # Use try-except for file operations
    try:
        if not file.exists():
            logger.error(f"Stylesheet resource not found: {qss_path}")
            return ""
        if file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
            stream = QTextStream(file)
            stylesheet = stream.readAll()
        else:
            logger.error(f"Could not open stylesheet resource: {qss_path}, Error: {file.errorString()}")
    except Exception as e:
         logger.error(f"Error loading stylesheet {qss_path}: {e}", exc_info=True)
    finally:
        if file.isOpen():
            file.close()
    return stylesheet

def apply_theme(app: QApplication, theme_name: str):
    """Loads and applies the specified theme stylesheet to the application."""
    logger = logging.getLogger(__name__)
    global _current_theme
    stylesheet = load_stylesheet(theme_name)
    if stylesheet:
        app.setStyleSheet(stylesheet)
        _current_theme = theme_name
        logger.info(f"Successfully applied theme: {theme_name}")
    else:
        logger.error(f"Failed to load stylesheet for theme: {theme_name}. Applying no style.")
        # Optionally apply a default minimal style or leave it as is
        # app.setStyleSheet("") # Clear existing style

def get_current_theme() -> str:
    """Returns the name of the currently applied theme."""
    return _current_theme