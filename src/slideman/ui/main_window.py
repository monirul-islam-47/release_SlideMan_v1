# src/slideman/ui/main_window.py
import logging
from pathlib import Path
import appdirs
import sys

from PySide6.QtWidgets import (QApplication, QMainWindow, QStackedWidget,
                             QVBoxLayout, QWidget, QMenuBar, QStatusBar,
                             QMessageBox, QPushButton, QHBoxLayout, QFrame, QLabel) # Added QMessageBox for About dialog
from PySide6.QtGui import QAction, QIcon, QKeySequence, QFont
from PySide6.QtCore import Slot, QSettings, Qt, QCoreApplication, QSize, QTimer # Added QCoreApplication, QSize, and QTimer

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
from .components.welcome_dialog import WelcomeDialog  # Import the WelcomeDialog
from .components.contextual_help import contextual_help, OnboardingChecklist  # Import contextual help
from ..services.platform_detection import platform_capabilities  # Import platform detection

# TODO this also exists in __main__.py
ORG_NAME = "SlidemanDev" # Change as needed
APP_NAME = "Slideman"

# --- Architecture: Presentation Layer ---
class MainWindow(QMainWindow):
    def __init__(self, db_service: Database):
        super().__init__()
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing MainWindow")
        
        try:
            self.setWindowTitle("Slideman") # Updated App Name
            # Comment out icon - resource file is missing
            # self.setWindowIcon(QIcon(":/icons/cil-mood-good.png")) # Assumes icon exists in resources
            self.logger.debug("Window title set")

            # --- Initialize Database Service ---
            self.logger.info("Setting up database connection")
            self.db_service = db_service # Use the provided service instance
            if not self.db_service.connect():
                # Critical error if DB can't connect on startup
                error_msg = f"Could not connect to the database at: {self.db_service.db_path}"
                self.logger.critical(error_msg)
                QMessageBox.critical(self, "Database Error",
                                     f"{error_msg}\n"
                                     f"Please check permissions and disk space.\nApplication will exit.")
                sys.exit(1) # Exit if DB connection fails
            self.logger.info("Database connection successful")
        except Exception as e:
            self.logger.critical(f"Error during MainWindow initialization (basic setup): {e}", exc_info=True)
            QMessageBox.critical(self, "Initialization Error",
                               f"Error initializing application (basic setup): {e}\n"
                               f"Application will exit.")
            sys.exit(1)
        # --------------------------------

        # Core layout elements (Part of Presentation Layer)
        # self.projects_page = ProjectsPage(...) # Will need DB service, etc.
        # self.stacked_widget.addWidget(self.projects_page)

        # --- UI Structure ---
        try:
            self.logger.info("Creating UI structure")
            # This layout will eventually include the left navigation buttons/list
            # interacting with self.stacked_widget
            main_widget = QWidget()
            self.logger.debug("Created main widget")
            
            main_layout = QHBoxLayout(main_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            self.logger.debug("Set up main layout")

            # --- Left Navigation Panel ---
            self.logger.debug("Creating navigation panel")
            self.nav_frame = QFrame()
            self.nav_frame.setFixedWidth(200) # Increased width for enhanced styling
            self.nav_frame.setStyleSheet("background-color: #44475a;") # Temporary - will be overridden in _setup_visual_styling
            nav_layout = QVBoxLayout(self.nav_frame)
            nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            nav_layout.setContentsMargins(5, 10, 5, 10)
            nav_layout.setSpacing(10)
            self.logger.debug("Navigation panel created successfully")
        except Exception as e:
            self.logger.critical(f"Error creating UI structure: {e}", exc_info=True)
            QMessageBox.critical(self, "UI Initialization Error",
                               f"Error initializing UI structure: {e}\n"
                               f"Application will exit.")
            sys.exit(1)

        # Enhanced Navigation Buttons with icons
        try:
            self.logger.info("Creating navigation buttons")
            
            self.btn_projects = QPushButton("📁  Projects")
            self.btn_projects.setObjectName("navButton")
            self.logger.debug("Created Projects button")
            
            self.btn_slideview = QPushButton("🎞️  SlideView")
            self.btn_slideview.setObjectName("navButton")
            self.logger.debug("Created SlideView button")
            
            self.btn_keywords = QPushButton("🏷️  Keywords")
            self.btn_keywords.setObjectName("navButton")
            self.logger.debug("Created Keywords button")
        except Exception as e:
            self.logger.critical(f"Error creating navigation buttons: {e}", exc_info=True)
            QMessageBox.critical(self, "UI Initialization Error",
                               f"Error creating navigation buttons: {e}\n"
                               f"Application will exit.")
            sys.exit(1)
        # self.btn_keywords.setIconSize(QSize(18, 18))
        
        try:
            self.logger.info("Creating additional navigation buttons")
            
            self.btn_assembly = QPushButton("🎯  Assembly")
            self.btn_assembly.setObjectName("navButton")
            self.logger.debug("Created Assembly button")
            
            self.btn_delivery = QPushButton("🚚  Delivery")
            self.btn_delivery.setObjectName("navButton")
            self.logger.debug("Created Delivery button")

            # Add navigation buttons to layout
            self.logger.info("Adding buttons to navigation layout")
            nav_layout.addWidget(self.btn_projects)
            nav_layout.addWidget(self.btn_slideview)
            nav_layout.addWidget(self.btn_keywords)
            nav_layout.addWidget(self.btn_assembly)
            nav_layout.addWidget(self.btn_delivery)
            
            # Replace ugly white thumbnails with beautiful progress cards
            if app_state.user_level == "beginner":
                nav_layout.addSpacing(20)
                
                # Create elegant progress indicator instead of ugly checklist
                progress_card = self._create_elegant_progress_card()
                nav_layout.addWidget(progress_card)
            
            nav_layout.addStretch(1)  # Push buttons to top
            self.logger.debug("Added all buttons to navigation layout")
        except Exception as e:
            self.logger.critical(f"Error setting up navigation layout: {e}", exc_info=True)
            QMessageBox.critical(self, "UI Initialization Error",
                               f"Error setting up navigation layout: {e}\n"
                               f"Application will exit.")
            sys.exit(1)

        # --- Content Area (Stacked Widget) ---
        try:
            self.logger.info("Setting up content area with stacked widget")
            self.stacked_widget = QStackedWidget()
            self.stacked_widget.setStyleSheet("""
                QStackedWidget {
                    background: transparent;
                    border-radius: 15px 0px 0px 15px;
                    margin-left: 5px;
                }
            """)
            self.logger.debug("Created stacked widget")

            # Create the individual pages and add them to the stacked widget
            self.logger.info("Creating content pages")
            # Each one will need references to db_service, app_state, etc.
            # IMPORTANT: Use the same INDEX ORDER as navigation buttons!
            try:
                self.logger.debug("Creating ProjectsPage")
                self.projects_page = ProjectsPage(self.db_service) # Index 0
                self.logger.debug("Created ProjectsPage successfully")
            except Exception as e:
                self.logger.critical(f"Failed to create ProjectsPage: {e}", exc_info=True)
                raise Exception(f"Failed to create ProjectsPage: {e}")
                
            try:
                self.logger.debug("Creating SlideViewPage")
                self.slideview_page = SlideViewPage(self.db_service) # Index 1 - now expects db_service
                self.logger.debug("Created SlideViewPage successfully")
            except Exception as e:
                self.logger.critical(f"Failed to create SlideViewPage: {e}", exc_info=True)
                raise Exception(f"Failed to create SlideViewPage: {e}")
                
            try:
                self.logger.debug("Creating KeywordManagerPage")
                self.keyword_manager_page = KeywordManagerPage() # Index 2 - no db_service
                self.logger.debug("Created KeywordManagerPage successfully")
            except Exception as e:
                self.logger.critical(f"Failed to create KeywordManagerPage: {e}", exc_info=True)
                raise Exception(f"Failed to create KeywordManagerPage: {e}")
                
            try:
                self.logger.debug("Creating AssemblyManagerPage")
                self.assembly_manager_page = AssemblyManagerPage() # Index 3 - no db_service
                self.logger.debug("Created AssemblyManagerPage successfully")
            except Exception as e:
                self.logger.critical(f"Failed to create AssemblyManagerPage: {e}", exc_info=True)
                raise Exception(f"Failed to create AssemblyManagerPage: {e}")
                
            try:
                self.logger.debug("Creating DeliveryPage")
                self.delivery_page = DeliveryPage() # Index 4 - no db_service
                self.logger.debug("Created DeliveryPage successfully")
            except Exception as e:
                self.logger.critical(f"Failed to create DeliveryPage: {e}", exc_info=True)
                raise Exception(f"Failed to create DeliveryPage: {e}")

            # Add pages to stacked widget
            self.logger.info("Adding pages to stacked widget")
            self.stacked_widget.addWidget(self.projects_page)
            self.stacked_widget.addWidget(self.slideview_page)
            self.stacked_widget.addWidget(self.keyword_manager_page)
            self.stacked_widget.addWidget(self.assembly_manager_page)
            self.stacked_widget.addWidget(self.delivery_page)
            self.logger.debug("Added all pages to stacked widget")

            # Add both panels to the main layout
            self.logger.info("Finalizing main layout")
            main_layout.addWidget(self.nav_frame)
            main_layout.addWidget(self.stacked_widget, 1) # Content area should expand

            self.setCentralWidget(main_widget)
            self.logger.debug("Set central widget successfully")
        except Exception as e:
            self.logger.critical(f"Error setting up content area: {e}", exc_info=True)
            QMessageBox.critical(self, "UI Initialization Error",
                               f"Error setting up content area: {e}\n"
                               f"Application will exit.")
            sys.exit(1)

        try:
            self.logger.info("Setting up navigation button properties")
            # Set buttons to checkable and create a button group for exclusive selection
            self.nav_buttons = [self.btn_projects, self.btn_slideview, self.btn_keywords, self.btn_assembly, self.btn_delivery]
            for btn in self.nav_buttons:
                btn.setCheckable(True)
                btn.setAutoExclusive(True)
            self.logger.debug("Navigation buttons configured successfully")
            
            # Set up status bar
            self.logger.info("Setting up status bar")
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            self.logger.debug("Status bar created")
            
            # Create UI actions, menus, and connect signals
            try:
                self.logger.info("Creating actions")
                self._create_actions()
                self.logger.debug("Actions created successfully")
            except Exception as e:
                self.logger.critical(f"Failed to create actions: {e}", exc_info=True)
                raise Exception(f"Failed to create actions: {e}")
                
            try:
                self.logger.info("Creating menus")
                self._create_menus()
                self.logger.debug("Menus created successfully")
            except Exception as e:
                self.logger.critical(f"Failed to create menus: {e}", exc_info=True)
                raise Exception(f"Failed to create menus: {e}")
                
            try:
                self.logger.info("Connecting signals")
                self._connect_signals()
                # Connect onboarding progress tracking
                event_bus.onboardingProgressUpdate.connect(self._track_onboarding_progress)
                self.logger.debug("Signals connected successfully")
            except Exception as e:
                self.logger.critical(f"Failed to connect signals: {e}", exc_info=True)
                raise Exception(f"Failed to connect signals: {e}")
            
            # Apply settings
            try:
                self.logger.info("Loading settings")
                self._load_settings()
                self.logger.debug("Settings loaded successfully")
            except Exception as e:
                self.logger.warning(f"Failed to load settings: {e}", exc_info=True)
                # Don't raise exception for settings - app can function without them
            
            # Set up visual styling
            self._setup_visual_styling()
            
            # Set up contextual help
            self._setup_contextual_help()
            
            # Set the initial active tab (first button)
            self.logger.info("Setting initial active tab")
            self.btn_projects.setChecked(True)
            self.stacked_widget.setCurrentIndex(0)
            self.logger.debug("Initial tab set successfully")
            self.logger.info("MainWindow initialization completed successfully")
        except Exception as e:
            self.logger.critical(f"Error during final MainWindow initialization: {e}", exc_info=True)
            QMessageBox.critical(self, "UI Initialization Error",
                               f"Error during final UI initialization: {e}\n"
                               f"Application will exit.")
            sys.exit(1)

        # The initial page and button state are already set above at lines 285-286
        self.status_bar.showMessage("Ready", 3000) # Initial status message
        # self._create_toolbar() # Optional

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
        self.show_welcome_action = QAction("Show &Welcome Dialog", self, statusTip="Show the welcome dialog again", triggered=self._show_welcome_dialog_again)
        self.debug_info_action = QAction("Copy &Debug Info", self, statusTip="Copy debug information to clipboard", triggered=self._copy_debug_info)
        self.save_debug_action = QAction("&Save Debug Report", self, statusTip="Save debug report to file", triggered=self._save_debug_report)

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
        help_menu.addSeparator()
        help_menu.addAction(self.show_welcome_action)
        help_menu.addSeparator()
        help_menu.addAction(self.debug_info_action)
        help_menu.addAction(self.save_debug_action)
        
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
        
        # --- Connect navigation button signals ---
        self.btn_projects.clicked.connect(lambda: self._handle_nav_button_click(0))
        self.btn_slideview.clicked.connect(lambda: self._handle_nav_button_click(1))
        self.btn_keywords.clicked.connect(lambda: self._handle_nav_button_click(2))
        self.btn_assembly.clicked.connect(lambda: self._handle_nav_button_click(3))
        self.btn_delivery.clicked.connect(lambda: self._handle_nav_button_click(4))

        
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

    def showEvent(self, event):
        """Override showEvent to show welcome dialog on first run."""
        super().showEvent(event)
        
        # Show welcome dialog on first run
        if app_state.is_first_run():
            self.logger.info("First run detected, showing welcome dialog")
            self._show_welcome_dialog()
            
            # After welcome dialog, check platform capabilities
            self._check_platform_capabilities()
    
    def _show_welcome_dialog(self):
        """Show the welcome dialog for new users."""
        welcome_dialog = WelcomeDialog(self)
        
        # Connect signals
        welcome_dialog.startTutorialRequested.connect(self._start_tutorial)
        welcome_dialog.importSlidesRequested.connect(self._import_slides_action)
        welcome_dialog.loadDemoRequested.connect(self._load_demo_project)
        welcome_dialog.skipWelcomeRequested.connect(self._skip_welcome)
        
        welcome_dialog.exec()
        
    def _start_tutorial(self):
        """Start the interactive tutorial."""
        self.logger.info("Starting tutorial")
        app_state.complete_first_run()
        app_state.increment_completed_actions()
        # TODO: Implement tutorial system
        self.status_bar.showMessage("Tutorial feature coming soon!", 3000)
        
    def _import_slides_action(self):
        """Handle import slides from welcome dialog."""
        self.logger.info("User chose to import slides from welcome")
        app_state.complete_first_run()
        # Navigate to projects page and trigger import
        self.btn_projects.setChecked(True)
        self.stacked_widget.setCurrentIndex(0)
        # TODO: Trigger import action on projects page
        self.status_bar.showMessage("Click 'New Project' to start importing slides", 5000)
        
    def _load_demo_project(self):
        """Load a demo project for exploration."""
        self.logger.info("User chose to load demo project")
        app_state.complete_first_run()
        
        try:
            from ..services.demo_content import DemoContentService
            demo_service = DemoContentService(self.db_service)
            
            # Check if demo project already exists
            if demo_service.has_demo_project():
                self.status_bar.showMessage("Demo project already exists! Check your Projects list.", 5000)
            else:
                # Create demo project
                project_id = demo_service.create_demo_project()
                if project_id:
                    # Also populate sample keywords for better auto-complete
                    demo_service.populate_sample_keywords()
                    
                    self.status_bar.showMessage("Demo project created successfully! Explore the SlideView and Keywords pages.", 8000)
                    
                    # Navigate to projects page and refresh
                    self.btn_projects.setChecked(True)
                    self.stacked_widget.setCurrentIndex(0)
                    
                    # Refresh the projects list
                    if hasattr(self.projects_page, 'load_projects_from_db'):
                        self.projects_page.load_projects_from_db()
                        
                    if hasattr(app_state, 'increment_completed_actions'):
                        app_state.increment_completed_actions()
                    else:
                        self.status_bar.showMessage("Failed to create demo project. Please try creating a project manually.", 5000)
                    
        except Exception as e:
            self.logger.error(f"Failed to create demo project: {e}", exc_info=True)
            self.status_bar.showMessage("Error creating demo project. Check logs for details.", 5000)
        
    def _skip_welcome(self):
        """Skip the welcome experience."""
        self.logger.info("User skipped welcome")
        app_state.complete_first_run()

    def _check_platform_capabilities(self):
        """Check platform capabilities and show setup dialogs if needed."""
        try:
            # Check if PowerPoint COM is available
            ppt_available, ppt_error = platform_capabilities.check_powerpoint_com()
            
            if not ppt_available:
                self.logger.warning(f"PowerPoint COM not available: {ppt_error}")
                
                # Show setup dialog for slide conversion
                continue_app = platform_capabilities.show_converter_setup_dialog(self)
                
                if not continue_app:
                    self.logger.info("User chose to quit due to missing slide conversion capabilities")
                    self.close()
                    return
                else:
                    self.logger.info("User chose to continue without slide conversion")
                    self.status_bar.showMessage(
                        "Note: Slide conversion disabled - install PowerPoint or LibreOffice for full functionality", 
                        10000
                    )
            else:
                self.logger.info("PowerPoint COM available - full slide conversion enabled")
                
        except Exception as e:
            self.logger.error(f"Error checking platform capabilities: {e}", exc_info=True)

    def _setup_visual_styling(self):
        """Set up enhanced visual styling following the established design system."""
        try:
            # Enhanced navigation panel styling using EXACT welcome dialog gradient
            self.nav_frame.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                    border-right: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 0px 15px 15px 0px;
                }
            """)
            
            # Add time-based greeting at top of navigation
            self._add_navigation_greeting()
            
            # Enhanced navigation button styling matching welcome dialog aesthetic
            nav_button_style = """
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.1);
                    color: white;
                    text-align: left;
                    padding: 12px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    margin: 4px 8px;
                    min-height: 40px;
                }
                
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.2);
                    border-color: rgba(255, 255, 255, 0.4);
                    transform: translateY(-1px);
                }
                
                QPushButton:checked {
                    background-color: #27ae60;
                    color: white;
                    font-weight: bold;
                    border: 1px solid #2ecc71;
                }
                
                QPushButton:checked:hover {
                    background-color: #2ecc71;
                }
                
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 0.05);
                }
            """
            
            # Apply styling to all navigation buttons
            for btn in self.nav_buttons:
                btn.setStyleSheet(nav_button_style)
                
            # Enhanced status bar styling following welcome dialog gradient design
            self.status_bar.setStyleSheet("""
                QStatusBar {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                    color: white;
                    font-size: 12px;
                    padding: 8px 15px;
                    border-top: 1px solid rgba(255, 255, 255, 0.2);
                    font-weight: 500;
                }
                QStatusBar::item {
                    border: none;
                }
            """)
            
            # Add contextual tips to status bar
            self._show_contextual_status_tip()
            
            # Main window styling harmonized with welcome dialog gradient theme
            self.setStyleSheet("""
                QMainWindow {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                }
                QMenuBar {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                    color: white;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
                    font-weight: 500;
                    padding: 4px;
                }
                QMenuBar::item {
                    background-color: transparent;
                    padding: 8px 16px;
                    border-radius: 6px;
                    margin: 2px 4px;
                }
                QMenuBar::item:selected {
                    background-color: rgba(255, 255, 255, 0.2);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                }
                QMenuBar::item:pressed {
                    background-color: rgba(255, 255, 255, 0.1);
                }
                QMenu {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                    color: white;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 8px;
                    padding: 8px;
                }
                QMenu::item {
                    background-color: transparent;
                    padding: 8px 20px;
                    border-radius: 6px;
                    margin: 2px;
                }
                QMenu::item:selected {
                    background-color: rgba(255, 255, 255, 0.2);
                }
                QMenu::separator {
                    height: 1px;
                    background-color: rgba(255, 255, 255, 0.2);
                    margin: 4px 10px;
                }
                QToolTip {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                    color: white;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    padding: 8px 12px;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 500;
                }
            """)
            
            self.logger.debug("Visual styling applied successfully")
        except Exception as e:
            self.logger.warning(f"Failed to set up visual styling: {e}", exc_info=True)

    def _setup_contextual_help(self):
        """Set up contextual help tooltips and help bubbles."""
        try:
            # Add enhanced tooltips to navigation buttons following design guide
            self.btn_projects.setToolTip("📁 Manage your PowerPoint projects and import files")
            self.btn_slideview.setToolTip("🎞️ Browse, search, and organize all your slides")
            self.btn_keywords.setToolTip("🏷️ Create and manage keywords for better organization")
            self.btn_assembly.setToolTip("🎯 Build new presentations from existing slides")
            self.btn_delivery.setToolTip("🚚 Export and share your completed presentations")
            
            # Set object names for help system
            self.btn_projects.setObjectName("projects_nav_button")
            self.btn_slideview.setObjectName("slideview_nav_button")
            self.btn_keywords.setObjectName("keywords_nav_button")
            self.btn_assembly.setObjectName("assembly_nav_button")
            self.btn_delivery.setObjectName("delivery_nav_button")
            
            # Show contextual help for first-time users
            if app_state.user_level == "beginner":
                # Delay help bubbles to show after UI is fully loaded
                QTimer.singleShot(2000, self._show_beginner_help)
                
            self.logger.debug("Contextual help set up successfully")
        except Exception as e:
            self.logger.warning(f"Failed to set up contextual help: {e}", exc_info=True)
    
    def _show_beginner_help(self):
        """Show help bubbles for beginner users."""
        if not app_state.is_first_run():  # Only show if not first run (welcome dialog already shown)
            return
            
        try:
            # Show help for the projects button first
            contextual_help.show_help_bubble(
                self.btn_projects,
                "Start here! Create a new project and import your PowerPoint files.",
                "right",
                "projects_nav_help"
            )
            
            # Show additional help after a delay
            QTimer.singleShot(5000, lambda: self._show_delayed_help())
            
        except Exception as e:
            self.logger.warning(f"Failed to show beginner help: {e}", exc_info=True)
    
    def _show_delayed_help(self):
        """Show additional help bubbles with delay."""
        try:
            if app_state.user_level == "beginner":
                contextual_help.show_help_bubble(
                    self.btn_slideview,
                    "Once you have slides, use this to search and browse them.",
                    "right",
                    "slideview_nav_help"
                )
        except Exception as e:
            self.logger.warning(f"Failed to show delayed help: {e}", exc_info=True)
    
    @Slot(str)
    def _on_onboarding_task_completed(self, task_name):
        """Handle completion of onboarding tasks."""
        try:
            self.logger.info(f"Onboarding task completed: {task_name}")
            if hasattr(app_state, 'increment_completed_actions'):
                app_state.increment_completed_actions()
            self.status_bar.showMessage(f"Great! You completed: {task_name}", 3000)
        except Exception as e:
            self.logger.warning(f"Failed to handle onboarding task completion: {e}", exc_info=True)
    
    def _create_elegant_progress_card(self):
        """Create an elegant progress card following welcome dialog standards - NO WHITE THUMBNAILS!"""
        from PySide6.QtWidgets import QFrame, QVBoxLayout, QProgressBar
        
        progress_frame = QFrame()
        progress_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                padding: 20px;
                margin: 8px;
            }
            QFrame:hover {
                background-color: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.3);
            }
        """)
        
        layout = QVBoxLayout(progress_frame)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Elegant title with emoji
        title_label = QLabel("🎯 Getting Started")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white; margin-bottom: 8px;")
        
        # Beautiful progress bar
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(getattr(app_state, 'completed_actions', 0) * 25)  # Assuming 4 key actions
        progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 8px;
                height: 16px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #27ae60, stop:1 #2ecc71);
                border-radius: 8px;
            }
        """)
        
        # Encouraging subtitle
        subtitle_label = QLabel(f"You're {min(getattr(app_state, 'completed_actions', 0) * 25, 100)}% ready!")
        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        
        layout.addWidget(title_label)
        layout.addWidget(progress_bar)
        layout.addWidget(subtitle_label)
        
        return progress_frame

    def _copy_debug_info(self):
        """Copy debug information to clipboard."""
        try:
            from ..services.debug_info import debug_collector
            
            debug_summary = debug_collector.get_debug_summary()
            clipboard = QApplication.clipboard()
            clipboard.setText(debug_summary)
            
            self.status_bar.showMessage("Debug information copied to clipboard", 3000)
            
        except Exception as e:
            self.logger.error(f"Failed to copy debug info: {e}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Failed to copy debug info: {e}")
            
    def _save_debug_report(self):
        """Save debug report to file."""
        try:
            from ..services.debug_info import debug_collector
            
            file_path = debug_collector.save_debug_info()
            
            QMessageBox.information(
                self, 
                "Debug Report Saved", 
                f"Debug report saved to:\n{file_path}\n\n"
                "You can include this file when reporting bugs."
            )
            
        except Exception as e:
            self.logger.error(f"Failed to save debug report: {e}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Failed to save debug report: {e}")
    
    def _show_welcome_dialog_again(self):
        """Show the welcome dialog again by resetting first run status."""
        try:
            self.logger.info("User requested to show welcome dialog again")
            app_state.reset_first_run()
            self._show_welcome_dialog()
            self.status_bar.showMessage("Welcome dialog shown - first run status reset", 3000)
        except Exception as e:
            self.logger.error(f"Failed to show welcome dialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Failed to show welcome dialog: {e}")

    def _on_onboarding_task_completed(self, task_id: str):
        """Handle completion of onboarding tasks."""
        self.logger.info(f"Onboarding task completed: {task_id}")
        app_state.increment_completed_actions()
        
        # Show contextual help based on completed task
        if task_id == "import_first":
            self.status_bar.showMessage("Great! Your first project is ready. Try exploring the SlideView page next.", 5000)
        elif task_id == "first_search":
            self.status_bar.showMessage("Awesome! You've mastered search. Try organizing slides with keywords.", 5000)
        elif task_id == "tag_slides":
            self.status_bar.showMessage("Excellent! Your slides are now organized. You can build presentations in Assembly.", 5000)
            
    def _track_onboarding_progress(self, action: str):
        """Track user actions for onboarding progress."""
        if not hasattr(self, 'onboarding_checklist'):
            return
            
        if action == "project_created":
            self.onboarding_checklist.mark_task_completed("import_first")
        elif action == "search_performed":
            self.onboarding_checklist.mark_task_completed("first_search")
        elif action == "slide_tagged":
            # Update progress for tagging task
            current_progress = getattr(self, '_tag_progress', 0) + 1
            self._tag_progress = current_progress
            self.onboarding_checklist.update_task_progress("tag_slides", current_progress)
        elif action == "presentation_created":
            self.onboarding_checklist.mark_task_completed("create_presentation")
        elif action == "advanced_feature_used":
            self.onboarding_checklist.mark_task_completed("advanced_features")

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
    
    def _add_navigation_greeting(self):
        """Add time-based greeting to navigation panel following design guide."""
        try:
            import datetime
            current_hour = datetime.datetime.now().hour
            
            if current_hour < 12:
                greeting = "Good morning!"
            elif current_hour < 18:
                greeting = "Good afternoon!"
            else:
                greeting = "Good evening!"
            
            # Create greeting widget following welcome dialog pattern
            greeting_widget = QWidget()
            greeting_layout = QVBoxLayout(greeting_widget)
            greeting_layout.setContentsMargins(15, 15, 15, 15)
            greeting_layout.setSpacing(5)
            
            # Main greeting using welcome dialog styling
            greeting_label = QLabel(greeting)
            greeting_label.setStyleSheet("""
                color: white;
                font-size: 18px;
                font-weight: bold;
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            """)
            greeting_label.setAlignment(Qt.AlignCenter)
            
            # Subtitle using welcome dialog pattern
            stats_label = QLabel("Transform how you manage PowerPoint slides")
            stats_label.setStyleSheet("""
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                padding: 8px;
                margin: 2px;
            """)
            stats_label.setAlignment(Qt.AlignCenter)
            stats_label.setWordWrap(True)
            
            greeting_layout.addWidget(greeting_label)
            greeting_layout.addWidget(stats_label)
            
            # Insert at top of navigation layout
            nav_layout = self.nav_frame.layout()
            nav_layout.insertWidget(0, greeting_widget)
            nav_layout.insertSpacing(1, 15)
            
            self.logger.debug("Navigation greeting added successfully")
        except Exception as e:
            self.logger.warning(f"Failed to add navigation greeting: {e}", exc_info=True)
    
    def _show_contextual_status_tip(self):
        """Show contextual tips in status bar based on user level."""
        try:
            if app_state.user_level == "beginner":
                tips = [
                    "💡 Tip: Start by creating your first project in the Projects tab",
                    "🔍 Tip: Use keywords to organize your slides for quick searching",
                    "✨ Tip: Hover over buttons to see helpful tooltips",
                    "🎯 Tip: Build presentations faster using the Assembly feature"
                ]
            elif app_state.user_level == "intermediate":
                tips = [
                    "⚡ Pro tip: Use Ctrl+F to quickly search slides",
                    "🏷️ Pro tip: Bulk tag slides to save time organizing",
                    "🔄 Pro tip: Use the Assembly page to reuse slides across projects",
                    "📊 Pro tip: Keywords help you find slides across all projects"
                ]
            else:  # expert
                tips = [
                    "🚀 Expert mode: Try advanced search operators",
                    "⌨️ Expert tip: Use keyboard shortcuts for faster workflow",
                    "🔧 Advanced: Customize your keyword organization system",
                    "📈 Power user: Export templates for reusable presentations"
                ]
            
            import random
            tip = random.choice(tips)
            
            # Show tip after a delay to not interfere with other status messages
            QTimer.singleShot(3000, lambda: self.status_bar.showMessage(tip, 10000))
            
        except Exception as e:
            self.logger.warning(f"Failed to show contextual status tip: {e}", exc_info=True)