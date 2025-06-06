#!/usr/bin/env python
# debug_app.py - Enhanced debug version of the SlideMan application
import os
import sys
import logging
import traceback
import argparse
import appdirs
from pathlib import Path

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                              QWidget, QMessageBox, QPushButton, QHBoxLayout,
                              QFrame, QStackedWidget, QStatusBar)
from PySide6.QtCore import QSettings, QCoreApplication, Qt, QSize

# Set up basic logging to console and file
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s")
logger = logging.getLogger(__name__)

# --- Constants ---
ORG_NAME = "SlidemanDev"
APP_NAME = "SlidemanDebug"

def setup_file_logging():
    # Set up file logging
    log_dir = Path(appdirs.user_log_dir(APP_NAME, ORG_NAME))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "debug.log"
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - [%(name)s] - %(message)s"))
    logging.getLogger().addHandler(file_handler)
    logger.info(f"Debug log file: {log_file}")

def create_simple_window():
    """Create a simple test window to verify Qt is working"""
    window = QMainWindow()
    window.setWindowTitle("SlideMan Debug Window")
    
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    label = QLabel("If you can see this, Qt is working properly.")
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    
    window.setCentralWidget(central_widget)
    window.resize(400, 300)
    return window

def test_database_connection():
    """Test connecting to the database"""
    from slideman.services.database import Database
    
    logger.info("Testing database connection...")
    db_dir = Path(appdirs.user_data_dir(APP_NAME, ORG_NAME))
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "debug_database.db"
    
    try:
        logger.info(f"Initializing database at: {db_path}")
        db_service = Database(db_path)
        
        if db_service.connect():
            logger.info("Database connection successful")
            db_service.close()
            return True, "Database connection successful"
        else:
            logger.error("Failed to connect to database")
            return False, "Failed to connect to database"
            
    except Exception as e:
        logger.error(f"Database error: {e}", exc_info=True)
        return False, f"Database error: {e}"

def test_theme_application():
    """Test applying a theme to the application"""
    from slideman import theme
    
    logger.info("Testing theme application...")
    try:
        app = QApplication.instance()
        theme.apply_theme(app, "dark")
        logger.info("Theme application successful")
        return True, "Theme application successful"
    except Exception as e:
        logger.error(f"Theme error: {e}", exc_info=True)
        return False, f"Theme error: {e}"

def create_minimal_main_window():
    """Create a minimal version of the MainWindow to test initialization"""
    logger.info("Creating minimal MainWindow...")
    try:
        # First test database connection
        success, message = test_database_connection()
        if not success:
            raise Exception(f"Database test failed: {message}")
        
        # Create a simplified MainWindow with minimal functionality
        class MinimalMainWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("SlideMan Minimal")
                self.resize(800, 600)
                
                # Create central widget and layout
                main_widget = QWidget()
                main_layout = QHBoxLayout(main_widget)
                main_layout.setContentsMargins(0, 0, 0, 0)
                main_layout.setSpacing(0)
                
                # Left navigation panel
                nav_frame = QFrame()
                nav_frame.setFixedWidth(150)
                nav_frame.setStyleSheet("background-color: #44475a;")
                nav_layout = QVBoxLayout(nav_frame)
                
                # Navigation buttons
                btn_test1 = QPushButton("Test 1")
                btn_test2 = QPushButton("Test 2")
                btn_test1.setObjectName("navButton")
                btn_test2.setObjectName("navButton")
                
                nav_layout.addWidget(btn_test1)
                nav_layout.addWidget(btn_test2)
                nav_layout.addStretch(1)
                
                # Content area
                stacked_widget = QStackedWidget()
                page1 = QWidget()
                page1_layout = QVBoxLayout(page1)
                page1_layout.addWidget(QLabel("Test Page 1"))
                
                page2 = QWidget()
                page2_layout = QVBoxLayout(page2)
                page2_layout.addWidget(QLabel("Test Page 2"))
                
                stacked_widget.addWidget(page1)
                stacked_widget.addWidget(page2)
                
                # Add to main layout
                main_layout.addWidget(nav_frame)
                main_layout.addWidget(stacked_widget, 1)
                
                # Set central widget
                self.setCentralWidget(main_widget)
                
                # Status bar
                self.status_bar = QStatusBar()
                self.setStatusBar(self.status_bar)
                self.status_bar.showMessage("Ready")
                
                # Connect signals
                btn_test1.clicked.connect(lambda: stacked_widget.setCurrentIndex(0))
                btn_test2.clicked.connect(lambda: stacked_widget.setCurrentIndex(1))
        
        # Create and return the window
        return MinimalMainWindow()
    except Exception as e:
        logger.error(f"MainWindow creation error: {e}", exc_info=True)
        raise

def parse_arguments():
    parser = argparse.ArgumentParser(description="SlideMan Debug Tool")
    parser.add_argument('--test', choices=['qt', 'db', 'theme', 'window', 'all'],
                        default='qt', help='Test to run')
    return parser.parse_args()

def debug_main():
    """Enhanced debug function with multiple test options"""
    setup_file_logging()
    args = parse_arguments()
    
    # Step 1: Create the Qt application
    logger.info("Step 1: Creating QApplication")
    app = QApplication(sys.argv)
    
    # Set application details
    QCoreApplication.setOrganizationName(ORG_NAME)
    QCoreApplication.setApplicationName(APP_NAME)
    
    test_results = []
    window = None
    
    try:
        # Run the specified test
        if args.test in ['qt', 'all']:
            logger.info("Running Qt test")
            window = create_simple_window()
            test_results.append((True, "Qt test successful"))
        
        if args.test in ['db', 'all']:
            logger.info("Running database test")
            success, message = test_database_connection()
            test_results.append((success, message))
        
        if args.test in ['theme', 'all']:
            logger.info("Running theme test")
            success, message = test_theme_application()
            test_results.append((success, message))
        
        if args.test in ['window', 'all']:
            logger.info("Running MainWindow test")
            try:
                window = create_minimal_main_window()
                test_results.append((True, "MainWindow test successful"))
            except Exception as e:
                test_results.append((False, f"MainWindow test failed: {e}"))
        
        # Show the window with test results
        if not window:
            window = create_simple_window()
        
        # Add test results to the window
        central_widget = window.centralWidget()
        layout = central_widget.layout()
        
        # Clear any existing widgets
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)
        
        # Add results header
        layout.addWidget(QLabel("Debug Test Results:"))
        
        # Add test results
        for success, message in test_results:
            result_label = QLabel(f"{'✓' if success else '✗'} {message}")
            result_label.setStyleSheet(f"color: {'green' if success else 'red'};")
            layout.addWidget(result_label)
        
        # Show the window
        window.show()
        logger.info("Debug window shown successfully")
        
        # Start the Qt event loop
        return app.exec()
        
    except Exception as e:
        logger.critical(f"Error: {e}", exc_info=True)
        
        # Show error message
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText(f"An error occurred: {e}")
        error_dialog.setDetailedText(traceback.format_exc())
        error_dialog.exec()
        
        return 1

if __name__ == "__main__":
    sys.exit(debug_main())
