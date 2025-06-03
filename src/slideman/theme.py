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
        logger.warning(f"Failed to load stylesheet resource for theme: {theme_name}. Applying fallback style.")
        # Apply a fallback dark stylesheet that doesn't rely on resource files
        fallback_stylesheet = """
        /* Fallback Dark Theme - Basic Styling */
        QWidget {
            background-color: #2D2D30;
            color: #FFFFFF;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        QMainWindow, QDialog {
            background-color: #252526;
        }
        
        QPushButton {
            background-color: #3C3C3C;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 5px 10px;
            color: #FFFFFF;
        }
        
        QPushButton:hover {
            background-color: #45A5F5;
        }
        
        QPushButton:pressed {
            background-color: #1C97EA;
        }
        
        QPushButton[objectName="navButton"] {
            background-color: #3E3E40;
            border-radius: 0;
            text-align: left;
            padding: 8px 12px;
            font-weight: bold;
        }
        
        QPushButton[objectName="navButton"]:hover {
            background-color: #45A5F5;
        }
        
        QPushButton[objectName="navButton"]:checked {
            background-color: #1C97EA;
            border-left: 4px solid #FFFFFF;
        }
        
        QTableView, QListView, QTreeView {
            background-color: #252526;
            alternate-background-color: #2D2D30;
            border: 1px solid #3F3F46;
            gridline-color: #3F3F46;
        }
        
        QHeaderView::section {
            background-color: #3E3E40;
            color: #FFFFFF;
            padding: 5px;
            border: 1px solid #3F3F46;
        }
        
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #333337;
            border: 1px solid #3F3F46;
            border-radius: 2px;
            color: #FFFFFF;
            padding: 2px 4px;
        }
        
        QMenuBar {
            background-color: #2D2D30;
            color: #FFFFFF;
        }
        
        QMenuBar::item:selected {
            background-color: #3E3E40;
        }
        
        QMenu {
            background-color: #2D2D30;
            color: #FFFFFF;
            border: 1px solid #3F3F46;
        }
        
        QMenu::item:selected {
            background-color: #3E3E40;
        }
        
        QTabWidget::pane {
            border: 1px solid #3F3F46;
        }
        
        QTabBar::tab {
            background-color: #2D2D30;
            color: #FFFFFF;
            border: 1px solid #3F3F46;
            padding: 5px 10px;
        }
        
        QTabBar::tab:selected {
            background-color: #3E3E40;
        }
        
        QStatusBar {
            background-color: #007ACC;
            color: #FFFFFF;
        }
        
        QScrollBar:vertical {
            background-color: #2D2D30;
            width: 12px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #3E3E40;
            min-height: 20px;
        }
        
        QScrollBar:horizontal {
            background-color: #2D2D30;
            height: 12px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #3E3E40;
            min-width: 20px;
        }
        """
        app.setStyleSheet(fallback_stylesheet)
        _current_theme = f"{theme_name}_fallback"
        logger.info(f"Applied fallback {theme_name} theme.")
        

def get_current_theme() -> str:
    """Returns the name of the currently applied theme."""
    return _current_theme