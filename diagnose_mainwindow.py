#!/usr/bin/env python
# diagnose_mainwindow.py - Diagnose MainWindow initialization crash
import os
import sys
import traceback
import logging
from pathlib import Path
import appdirs

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s")
logger = logging.getLogger(__name__)

ORG_NAME = "SlidemanDev"
APP_NAME = "SlidemanDebug"

def test_mainwindow_step_by_step():
    """Test MainWindow initialization step by step"""
    logger.info("=== Testing MainWindow Initialization ===")
    
    # Step 1: Create QApplication
    logger.info("Step 1: Creating QApplication...")
    app = QApplication(sys.argv)
    QCoreApplication.setOrganizationName(ORG_NAME)
    QCoreApplication.setApplicationName(APP_NAME)
    logger.info("✓ QApplication created")
    
    # Step 2: Initialize AppState and EventBus
    logger.info("\nStep 2: Initializing AppState and EventBus...")
    try:
        from slideman.app_state import app_state
        from slideman.event_bus import event_bus
        logger.info("✓ AppState and EventBus imported")
    except Exception as e:
        logger.error(f"✗ Failed to import AppState/EventBus: {e}")
        traceback.print_exc()
        return
    
    # Step 3: Initialize Database
    logger.info("\nStep 3: Initializing Database...")
    try:
        from slideman.services.database import Database
        db_dir = Path(appdirs.user_data_dir(APP_NAME, ORG_NAME))
        db_path = db_dir / "test_debug.db"
        db_service = Database(db_path)
        if not db_service.connect():
            logger.error("✗ Failed to connect to database")
            return
        logger.info("✓ Database connected")
        app_state.set_db_service(db_service)
        logger.info("✓ Database set in AppState")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        traceback.print_exc()
        return
    
    # Step 4: Load initial state
    logger.info("\nStep 4: Loading initial state...")
    try:
        app_state.load_initial_state()
        logger.info("✓ Initial state loaded")
    except Exception as e:
        logger.error(f"✗ Failed to load initial state: {e}")
        traceback.print_exc()
        return
    
    # Step 5: Apply theme
    logger.info("\nStep 5: Applying theme...")
    try:
        from slideman import theme
        theme.apply_theme(app, "dark")
        logger.info("✓ Theme applied")
    except Exception as e:
        logger.error(f"✗ Failed to apply theme: {e}")
        traceback.print_exc()
    
    # Step 6: Create MainWindow
    logger.info("\nStep 6: Creating MainWindow...")
    try:
        from slideman.ui.main_window import MainWindow
        logger.info("✓ MainWindow imported")
        
        # Test initialization with detailed logging
        logger.info("Calling MainWindow constructor...")
        main_win = MainWindow(db_service=db_service)
        logger.info("✓ MainWindow created successfully!")
        
        # Test showing the window
        logger.info("Attempting to show MainWindow...")
        main_win.show()
        logger.info("✓ MainWindow shown successfully!")
        
        # Don't exec the app, just test initialization
        logger.info("\n✓ ALL TESTS PASSED - MainWindow can be created and shown")
        
    except Exception as e:
        logger.error(f"✗ MainWindow creation failed: {e}")
        logger.error("Full traceback:")
        traceback.print_exc()
        
        # Try to get more specific error info
        logger.error("\nTrying to identify the specific failure point...")
        try:
            # Import MainWindow to see if import works
            from slideman.ui.main_window import MainWindow
            logger.info("MainWindow import successful")
            
            # Try creating with minimal setup
            try:
                win = MainWindow(db_service=db_service)
            except Exception as e2:
                logger.error(f"MainWindow constructor failed: {e2}")
                traceback.print_exc()
        except ImportError as ie:
            logger.error(f"MainWindow import failed: {ie}")
    
    # Cleanup
    logger.info("\nCleaning up...")
    if 'db_service' in locals():
        db_service.close()
        logger.info("Database closed")

if __name__ == "__main__":
    try:
        test_mainwindow_step_by_step()
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        traceback.print_exc()