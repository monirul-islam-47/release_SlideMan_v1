# src/slideman/__main__.py

import sys
import logging
import logging.handlers
import traceback
import platform # For potential OS-specific adjustments
from pathlib import Path
import appdirs # For log path

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QSettings, QCoreApplication, Qt

# --- Architecture Link: Import necessary components ---
# Import the main window (Presentation Layer)
from .ui.main_window import MainWindow
# Import resource module (registers icons, qss)
from . import resources_rc
# Import theme handler (Utility / Presentation Support)
from . import theme
# Import state managers (Shared State) - will be instantiated
from .app_state import app_state 
from .event_bus import event_bus 
from .services.database import Database

# --- Application Configuration ---
ORG_NAME = "SlidemanDev" # Change as needed
APP_NAME = "Slideman"
APP_VERSION = "1.0.0" # Corresponds to pyproject.toml version

# --- Logging Setup ---
def setup_logging():
    log_dir = Path(appdirs.user_log_dir(APP_NAME, ORG_NAME))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    log_format = "%(asctime)s - %(levelname)s - [%(name)s] - %(message)s"
    # You can set the root logger level here or configure handlers individually
    logging.basicConfig(level=logging.DEBUG, format=log_format, force=True) # Use force=True if reconfiguring

    # Get the root logger
    root_logger = logging.getLogger()
    # Prevent duplicate handlers if setup_logging is called multiple times (shouldn't happen here)
    if root_logger.hasHandlers():
         root_logger.handlers.clear()


    # File Handler (Rotating) - Now logging.handlers should be available
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=2*1024*1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO) # Set level for this handler
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)
    except PermissionError:
         print(f"Warning: Could not write to log file due to permissions: {log_file}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Failed to set up file logging: {e}", file=sys.stderr)


    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG) # Or INFO for less noise
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)

    # Set overall level for the root logger (handlers won't receive messages below this level)
    root_logger.setLevel(logging.DEBUG) # Or INFO

    logging.info(f"Logging initialized. Log file: {log_file}")


# --- Global Exception Handling ---
def global_exception_hook(exc_type, exc_value, exc_tb):
    """Handles uncaught exceptions."""
    logger = logging.getLogger(__name__) # Get a logger instance
    logger.critical("Unhandled exception caught by hook:", exc_info=(exc_type, exc_value, exc_tb))

    # Format traceback for display
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    error_message = "".join(tb_lines)

    # Display user-friendly dialog
    error_dialog = QMessageBox()
    error_dialog.setIcon(QMessageBox.Critical)
    error_dialog.setWindowTitle("Unexpected Error")
    error_dialog.setText(f"An unexpected error occurred:\n\n{exc_value}\n\nPlease report this issue.")
    # Include log file location for easy reporting
    log_file_path = next((h.baseFilename for h in logging.getLogger().handlers if isinstance(h, logging.handlers.RotatingFileHandler)), "N/A")
    error_dialog.setInformativeText(f"Details have been logged to:\n{log_file_path}")
    # Add details button to show full traceback (optional)
    error_dialog.setDetailedText(error_message)
    error_dialog.exec()

    sys.exit(1) # Exit after showing the message


# --- Main Application Execution ---
def main():
    # --- Architecture: Application Setup & Orchestration ---

    # Set application details used by QSettings, etc.
    QCoreApplication.setOrganizationName(ORG_NAME)
    QCoreApplication.setApplicationName(APP_NAME)
    QCoreApplication.setApplicationVersion(APP_VERSION)

    # # Enable High DPI support
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    # Create the application instance
    app = QApplication(sys.argv)

    # Setup logging and exception handling
    setup_logging()
    sys.excepthook = global_exception_hook
    logging.info(f"Starting {APP_NAME} v{APP_VERSION} on {platform.system()} {platform.release()}")

    # --- Architecture Link: Initialize Shared State (Deferred) ---
    logging.info("Initializing AppState and EventBus...")
    _app_state = app_state # Access the singleton instance created in app_state.py
    _event_bus = event_bus # Access the singleton instance
    # _app_state.load_initial_state() # Load MRU etc.

    # --- Initialize Database Service ---
    db_dir = Path(appdirs.user_data_dir(APP_NAME, ORG_NAME))
    db_path = db_dir / "slideman_library.db"
    db_service = Database(db_path) # Create instance
    if not db_service.connect():
        # ... (Handle critical DB connection error) ...
        sys.exit(1)
    # --- Set DB service in AppState ---
    app_state.set_db_service(db_service)
    # ----------------------------------

    # --- Load initial state AFTER DB is set ---
    app_state.load_initial_state()
    # -----------------------------------------

    # Always apply dark theme regardless of settings
    try:
        theme.apply_theme(app, "dark")
        logging.info("Applied 'dark' theme.")
    except Exception as e:
        logging.error(f"Failed to apply initial theme: {e}", exc_info=True)

    # --- Architecture: Instantiate and Show Presentation Layer ---
    logging.info("Creating MainWindow...")
    # Pass db_service instance created above
    main_win = MainWindow(db_service=db_service)
    main_win.show()
    logging.info("Application started successfully.")

    result = app.exec()

    # --- Clean-up ---
    logging.info("Closing database connection...")
    db_service.close() # Close DB when app exits

    sys.exit(result)

# --- Script Entry Point ---
if __name__ == "__main__":
    main()