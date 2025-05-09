# src/slideman/ui/main_window.py
import logging
from pathlib import Path
import appdirs
import sys

from PySide6.QtWidgets import (QApplication, QMainWindow, QStackedWidget,
                             QVBoxLayout, QWidget, QMenuBar, QStatusBar,
                             QMessageBox, QPushButton, QHBoxLayout, QFrame, QLabel) # Added QMessageBox for About dialog
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtCore import Slot, QSettings, Qt, QCoreApplication, QSize # Added QCoreApplication and QSize

# Architecture Link: These imports will connect to other layers later
# from .. import theme # Connects to Theme handling
from ..app_state import app_state # Connects to Shared State (AppState singleton)
from ..event_bus import event_bus
from ..services.database import Database
from .pages.projects_page import ProjectsPage # Example Page from Presentation Layer
from .pages.slideview_page import SlideViewPage # Added SlideViewPage
from .pages.keyword_manager_page import KeywordManagerPage # Import the KeywordManagerPage
from .pages.assembly_page import AssemblyManagerPage # Import the AssemblyManagerPage
from .pages.delivery_page import DeliveryPage  # Import the DeliveryPage

# TODO this also exists in __main__.py
ORG_NAME = "SlidemanDev" # Change as needed
APP_NAME = "Slideman"

# --- Architecture: Presentation Layer ---
class MainWindow(QMainWindow):
    def __init__(self, db_service: Database):
        super().__init__()
        self.setWindowTitle("Slideman") # Updated App Name
        self.setWindowIcon(QIcon(":/icons/cil-mood-good.png")) # Assumes icon exists in resources

        # --- Initialize Database Service ---
        
        self.db_service = db_service # Use the provided service instance
        if not self.db_service.connect():
            # Critical error if DB can't connect on startup
            QMessageBox.critical(self, "Database Error",
                                 f"Could not connect to the database at:\n{db_path}\n"
                                 f"Please check permissions and disk space.\nApplication will exit.")
            sys.exit(1) # Exit if DB connection fails
        # --------------------------------

        # Core layout elements (Part of Presentation Layer)
        # self.projects_page = ProjectsPage(...) # Will need DB service, etc.
        # self.stacked_widget.addWidget(self.projects_page)

        # --- UI Structure ---
        # This layout will eventually include the left navigation buttons/list
        # interacting with self.stacked_widget
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Left Navigation Panel ---
        self.nav_frame = QFrame()
        self.nav_frame.setFixedWidth(150) # Example fixed width
        self.nav_frame.setStyleSheet("background-color: #44475a;") # Example color (adjust theme)
        nav_layout = QVBoxLayout(self.nav_frame)
        nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        nav_layout.setContentsMargins(5, 10, 5, 10)
        nav_layout.setSpacing(10)

        # Enhanced Navigation Buttons with icons
        self.btn_projects = QPushButton(" Projects")
        self.btn_projects.setObjectName("navButton")
        self.btn_projects.setIcon(QIcon(":/icons/cil-folder.png"))
        self.btn_projects.setIconSize(QSize(18, 18))
        
        self.btn_slideview = QPushButton(" SlideView")
        self.btn_slideview.setObjectName("navButton")
        self.btn_slideview.setIcon(QIcon(":/icons/cil-image1.png"))
        self.btn_slideview.setIconSize(QSize(18, 18))
        
        self.btn_keywords = QPushButton(" Keywords")
        self.btn_keywords.setObjectName("navButton")
        self.btn_keywords.setIcon(QIcon(":/icons/cil-tags.png"))
        self.btn_keywords.setIconSize(QSize(18, 18))
        
        self.btn_assembly = QPushButton(" Assembly")
        self.btn_assembly.setObjectName("navButton")
        self.btn_assembly.setIcon(QIcon(":/icons/cil-layers.png"))
        self.btn_assembly.setIconSize(QSize(18, 18))
        
        self.btn_delivery = QPushButton(" Delivery")
        self.btn_delivery.setObjectName("navButton")
        self.btn_delivery.setIcon(QIcon(":/icons/cil-paper-plane.png"))
        self.btn_delivery.setIconSize(QSize(18, 18))

        nav_layout.addWidget(self.btn_projects)
        nav_layout.addWidget(self.btn_slideview)
        nav_layout.addWidget(self.btn_keywords)
        nav_layout.addWidget(self.btn_assembly)
        nav_layout.addWidget(self.btn_delivery)
        # Add spacer to push buttons up
        nav_layout.addStretch(1)

        # --- Content Area (Stacked Widget) ---
        self.stacked_widget = QStackedWidget()

        # Instantiate and add pages
        self.projects_page = ProjectsPage(db_service=self.db_service, parent=self) # Pass db_service
        # TODO: Instantiate other pages later
        self.stacked_widget.addWidget(self.projects_page)
        # Add placeholder pages for now to test navigation
        self.slideview_page = SlideViewPage(parent=self)
        self.stacked_widget.addWidget(self.slideview_page)
        self.keyword_manager_page = KeywordManagerPage(parent=self)  # Create the KeywordManagerPage instance
        self.stacked_widget.addWidget(self.keyword_manager_page)  # Add it to the stacked widget
        self.assembly_manager_page = AssemblyManagerPage(parent=self)  # Create the AssemblyManagerPage instance
        self.stacked_widget.addWidget(self.assembly_manager_page)  # Add it to the stacked widget
        self.delivery_page = DeliveryPage(parent=self)  # Create the Delivery page instance
        self.stacked_widget.addWidget(self.delivery_page)  # Add it to the stacked widget

        # --- Assemble Main Layout ---
        main_layout.addWidget(self.nav_frame)
        main_layout.addWidget(self.stacked_widget)

        self.setCentralWidget(main_widget)

        # ... (StatusBar, Actions, Menus, Settings) ...

        # Set buttons to checkable and create a button group for exclusive selection
        self.nav_buttons = [self.btn_projects, self.btn_slideview, self.btn_keywords, 
                           self.btn_assembly, self.btn_delivery]
        
        for btn in self.nav_buttons:
            btn.setCheckable(True)
            
        # Connect navigation buttons and implement active state tracking
        self.btn_projects.clicked.connect(lambda: self._handle_nav_button_click(0))
        self.btn_slideview.clicked.connect(lambda: self._handle_nav_button_click(1))
        self.btn_keywords.clicked.connect(lambda: self._handle_nav_button_click(2))
        self.btn_assembly.clicked.connect(lambda: self._handle_nav_button_click(3))
        self.btn_delivery.clicked.connect(lambda: self._handle_nav_button_click(4))

        # Set initial page and active button
        self.stacked_widget.setCurrentIndex(0)
        self.btn_projects.setChecked(True)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready", 3000) # Initial status message

        self._connect_signals() # Ensure this is called

        # Setup Actions, Menus (UI concern)
        self._create_actions()
        self._create_menus()
        # self._create_toolbar() # Optional

        # Connect signals
        self._connect_signals()

        # Connects to Persistence Layer (via QSettings)
        self._load_settings()

    def _create_actions(self):
        # File Menu Actions
        self.quit_action = QAction(QIcon(":/icons/cil-x.png"), "&Quit", self, shortcut=QKeySequence.StandardKey.Quit, statusTip="Exit application", triggered=self.close)
        # Edit Menu Actions (Connects to Shared State - QUndoStack)
        self.undo_action = app_state.undo_stack.createUndoAction(self, "&Undo")
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.redo_action = app_state.undo_stack.createRedoAction(self, "&Redo")
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        # View Menu Actions
        self.toggle_theme_action = QAction("Toggle &Theme", self, statusTip="Switch between light and dark themes", triggered=self.toggle_theme)
        # Help Menu Actions
        self.about_action = QAction("&About", self, statusTip="Show About box", triggered=self.show_about_dialog)

    def _create_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self.quit_action)

        edit_menu = menu_bar.addMenu("&Edit")
        edit_menu.addAction(self.undo_action) 
        edit_menu.addAction(self.redo_action) 

        view_menu = menu_bar.addMenu("&View")
        view_menu.addAction(self.toggle_theme_action)

        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction(self.about_action)
        
    def _connect_signals(self):
        # Example: Update status bar based on undo stack changes
                # Connect AppState signals
        if app_state: # Check if app_state is imported/available
            app_state.undo_stack.cleanChanged.connect(self.update_window_title_based_on_clean_state)
            app_state.undo_stack.indexChanged.connect(self.log_undo_index)

        # --- Connect EventBus signals ---
        event_bus.statusMessageUpdate.connect(self.update_status_bar)
        # Connect other EventBus signals here later
        # ------------------------------

        
    # --- closeEvent needs db_service reference ---
    def closeEvent(self, event):
        # Close Database Connection on Exit
        if hasattr(self, 'db_service') and self.db_service: # Check if it exists
            self.logger.info("Closing database connection from MainWindow...") # Add logger if needed
            self.db_service.close()
        else:
            self.logger.warning("db_service not found on MainWindow during closeEvent.")

        self._save_settings()
        event.accept()
    
    @Slot(str, int)
    def update_status_bar(self, message: str, timeout: int = 0):
        """Updates the main window's status bar."""
        if timeout > 0:
            self.status_bar.showMessage(message, timeout)
        else:
            self.status_bar.showMessage(message) # Show permanently until changed
        logging.debug(f"Status bar updated: '{message}' (timeout: {timeout}ms)")
    # -----------------------------------------

    def _handle_nav_button_click(self, index):
        """Handle navigation button clicks - update active button and stacked widget page"""
        # Update the stacked widget page
        self.stacked_widget.setCurrentIndex(index)
        
        # Update the checked state of the buttons
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        
        # Refresh data for specific pages when they become active
        if index == 2:  # Index 2 is the Keyword Manager page
            # If there's a current project, refresh the keyword manager data
            if app_state.current_project_path:
                self.keyword_manager_page._load_data_for_current_project()
    
    @Slot(bool)
    def update_window_title_based_on_clean_state(self, is_clean):
         # Add [*] to title if there are unsaved changes (stack is not clean)
         title = f"{QCoreApplication.applicationName()}"
         if not is_clean:
             title += "[*]"
         self.setWindowTitle(title)

    @Slot(int)
    def log_undo_index(self, idx):
        logging.debug(f"Undo stack index changed: {idx}")
    @Slot()
    def toggle_theme(self):
        # Original code - commented out
        # # Assumes theme module is imported and works
        # # Needs access to QApplication instance
        # try:
        #     from .. import theme # Local import for now
        #     current = theme.get_current_theme()
        #     new = "light" if current == "dark" else "dark"
        #     theme.apply_theme(QApplication.instance(), new)
        #     QSettings().setValue("theme", new) # Persist
        #     self.status_bar.showMessage(f"Theme changed to {new}", 2000)
        # except ImportError:
        #     self.status_bar.showMessage("Theme module not available yet.", 2000)
        
        # New code - always use dark theme
        try:
            from .. import theme # Local import for now
            theme.apply_theme(QApplication.instance(), "dark")
            QSettings().setValue("theme", "dark") # Persist setting
            self.status_bar.showMessage("Dark theme applied", 2000)
        except ImportError:
            self.status_bar.showMessage("Theme module not available yet.", 2000)


    @Slot()
    def show_about_dialog(self):
        QMessageBox.about(self,
                           f"About {QCoreApplication.applicationName()}",
                           f"<b>{QCoreApplication.applicationName()}</b> v{QCoreApplication.applicationVersion()}"
                           f"<p>A smart PowerPoint library and assembly tool.</p>"
                        #    f"<p>Organization: {QCoreApplication.organizationName()}</p>"
                           f"<p>Organization: MaMa Marketing GmbH</p>"
                           f"<p>&copy; 2025 All rights reserved.</p>"
                           f"<p><small>Written by Monirul Islam</small></p>"
                           f"<p><small>For support and feature requests: islam@mama-marketing.de</small></p>"
                           # You can add more information as needed
                          )

    def closeEvent(self, event):
        self._save_settings()
        event.accept()

    def _load_settings(self):
        # Architecture Link: Uses QSettings for persistence
        # Define company/app names in main or config module
        settings = QSettings("SlidemanDev", "Slideman") # Use your company/app name
        geom = settings.value("mainWindowGeometry")
        if geom:
            self.restoreGeometry(geom)
        else:
             # Sensible default size if no settings saved
             self.resize(1024, 768)


    def _save_settings(self):
        # Architecture Link: Uses QSettings for persistence
        settings = QSettings("SlidemanDev", "Slideman")
        settings.setValue("mainWindowGeometry", self.saveGeometry())