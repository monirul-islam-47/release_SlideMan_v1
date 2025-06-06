#!/usr/bin/env python
# diagnose_crash.py - Diagnose SlideMan crash issue
import os
import sys
import traceback
import logging

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_resource_import():
    """Test if resources can be imported"""
    logger.info("Testing resource import...")
    try:
        from slideman import resources_rc
        logger.info("✓ Resources imported successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to import resources: {e}")
        traceback.print_exc()
        return False

def test_qt_import():
    """Test if Qt modules can be imported"""
    logger.info("Testing Qt imports...")
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QFile
        logger.info("✓ Qt modules imported successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to import Qt modules: {e}")
        return False

def test_resource_access():
    """Test if resources can be accessed"""
    logger.info("Testing resource access...")
    try:
        from PySide6.QtCore import QFile
        from slideman import resources_rc
        
        # Test if QSS file can be accessed
        qss_file = QFile(":/qss/dark.qss")
        if qss_file.exists():
            logger.info("✓ dark.qss resource found")
        else:
            logger.error("✗ dark.qss resource NOT found")
            
        # Test if an icon can be accessed
        icon_file = QFile(":/icons/cil-folder.png")
        if icon_file.exists():
            logger.info("✓ Icon resource found")
        else:
            logger.error("✗ Icon resource NOT found")
            
        return qss_file.exists()
    except Exception as e:
        logger.error(f"✗ Failed to access resources: {e}")
        traceback.print_exc()
        return False

def test_theme_loading():
    """Test if theme can be loaded"""
    logger.info("Testing theme loading...")
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if not app:
            app = QApplication([])
            
        from slideman import theme
        theme.apply_theme(app, "dark")
        logger.info("✓ Theme applied successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to apply theme: {e}")
        traceback.print_exc()
        return False

def test_minimal_window():
    """Test creating a minimal window"""
    logger.info("Testing minimal window creation...")
    try:
        from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
        
        app = QApplication.instance()
        if not app:
            app = QApplication([])
            
        window = QMainWindow()
        window.setWindowTitle("Test Window")
        
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("If you see this, Qt is working"))
        
        window.setCentralWidget(central)
        logger.info("✓ Minimal window created successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to create minimal window: {e}")
        traceback.print_exc()
        return False

def test_page_imports():
    """Test if UI pages can be imported"""
    logger.info("Testing UI page imports...")
    pages_to_test = [
        ("ProjectsPage", "slideman.ui.pages.projects_page"),
        ("SlideViewPage", "slideman.ui.pages.slideview_page"),
        ("KeywordManagerPage", "slideman.ui.pages.keyword_manager_page"),
        ("AssemblyManagerPage", "slideman.ui.pages.assembly_page"),
        ("DeliveryPage", "slideman.ui.pages.delivery_page")
    ]
    
    all_success = True
    for page_name, module_path in pages_to_test:
        try:
            module = __import__(module_path, fromlist=[page_name])
            page_class = getattr(module, page_name)
            logger.info(f"✓ {page_name} imported successfully")
        except Exception as e:
            logger.error(f"✗ Failed to import {page_name}: {e}")
            all_success = False
            
    return all_success

def main():
    logger.info("=== SlideMan Crash Diagnosis ===")
    
    tests = [
        ("Resource Import", test_resource_import),
        ("Qt Import", test_qt_import),
        ("Resource Access", test_resource_access),
        ("Theme Loading", test_theme_loading),
        ("Minimal Window", test_minimal_window),
        ("Page Imports", test_page_imports)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- Running: {test_name} ---")
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
    
    # Check for specific crash scenario
    if not results[2][1]:  # Resource Access failed
        logger.warning("\n⚠️  LIKELY CAUSE: Resources not properly compiled or registered")
        logger.warning("Try running: pyside6-rcc resources/resources.qrc -o src/slideman/resources_rc.py")
    
    failed_count = sum(1 for _, success in results if not success)
    logger.info(f"\nTotal: {len(results) - failed_count}/{len(results)} tests passed")

if __name__ == "__main__":
    main()