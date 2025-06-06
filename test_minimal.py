#!/usr/bin/env python
# test_minimal.py - Minimal test to identify crash point
import os
import sys
import logging
import traceback

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_imports():
    """Test if basic imports work"""
    logger.info("Testing imports...")
    
    try:
        logger.info("Importing PySide6...")
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QCoreApplication
        logger.info("✓ PySide6 imported")
    except Exception as e:
        logger.error(f"✗ PySide6 import failed: {e}")
        return False
    
    try:
        logger.info("Importing app modules...")
        from slideman.app_state import app_state
        from slideman.event_bus import event_bus
        logger.info("✓ App modules imported")
    except Exception as e:
        logger.error(f"✗ App modules import failed: {e}")
        traceback.print_exc()
        return False
    
    try:
        logger.info("Importing database...")
        from slideman.services.database import Database
        logger.info("✓ Database imported")
    except Exception as e:
        logger.error(f"✗ Database import failed: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_qt_app():
    """Test creating Qt application"""
    logger.info("\nTesting Qt application creation...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QCoreApplication
        
        logger.info("Creating QApplication...")
        app = QApplication(sys.argv)
        
        logger.info("Setting application properties...")
        QCoreApplication.setOrganizationName("SlidemanDev")
        QCoreApplication.setApplicationName("SlidemanTest")
        QCoreApplication.setApplicationVersion("1.0.0")
        
        logger.info("✓ Qt application created successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Qt application creation failed: {e}")
        traceback.print_exc()
        return False

def test_singletons():
    """Test singleton initialization"""
    logger.info("\nTesting singleton initialization...")
    
    try:
        logger.info("Getting app_state instance...")
        from slideman.app_state import app_state
        state = app_state
        logger.info(f"✓ app_state instance: {state}")
        
        logger.info("Getting event_bus instance...")
        from slideman.event_bus import event_bus
        bus = event_bus
        logger.info(f"✓ event_bus instance: {bus}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Singleton initialization failed: {e}")
        traceback.print_exc()
        return False

def test_database_path():
    """Test database path creation"""
    logger.info("\nTesting database path...")
    
    try:
        import appdirs
        from pathlib import Path
        
        db_dir = Path(appdirs.user_data_dir("SlidemanTest", "SlidemanDev"))
        logger.info(f"Database directory: {db_dir}")
        
        if not db_dir.exists():
            logger.info("Database directory doesn't exist, would be created")
        else:
            logger.info("Database directory exists")
        
        db_path = db_dir / "test.db"
        logger.info(f"Database path: {db_path}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Database path test failed: {e}")
        traceback.print_exc()
        return False

def main():
    logger.info("=== SlideMan Minimal Test ===")
    
    tests = [
        ("Imports", test_imports),
        ("Qt Application", test_qt_app),
        ("Singletons", test_singletons),
        ("Database Path", test_database_path)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            traceback.print_exc()
            results.append((test_name, False))
    
    logger.info("\n=== SUMMARY ===")
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{test_name}: {status}")

if __name__ == "__main__":
    main()