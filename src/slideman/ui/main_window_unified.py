# src/slideman/ui/main_window_unified.py

import logging
from pathlib import Path
import appdirs
import sys
from typing import List

from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QMenuBar, QStatusBar, QMessageBox, QSplitter,
                             QFrame, QLabel, QFileDialog, QInputDialog)
from PySide6.QtGui import QAction, QIcon, QKeySequence, QFont
from PySide6.QtCore import Slot, QSettings, Qt, QCoreApplication, QSize, QTimer

# Import new workspace components
from .components.header_widget import HeaderWidget
from .components.left_panel_widget import LeftPanelWidget
from .components.assembly_panel_widget import AssemblyPanelWidget

# Import existing components that we'll integrate
from .pages.slideview_page import SlideViewPage
from .components.welcome_dialog import WelcomeDialog
from .components.contextual_help import contextual_help, OnboardingChecklist

# Import core services and state management
from ..app_state import app_state
from ..event_bus import event_bus
from ..services.database import Database
from ..services.platform_detection import platform_capabilities
from ..services.demo_content import DemoContentService
from ..services import file_io
from .. import theme

# TODO this also exists in __main__.py
ORG_NAME = "SlidemanDev"
APP_NAME = "Slideman"


class UnifiedMainWindow(QMainWindow):
    """
    Unified main window implementing single-workspace design.
    Replaces the multi-page stacked widget approach with integrated panels.
    """
    
    def __init__(self, db_service: Database):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing UnifiedMainWindow")
        
        try:
            self.setWindowTitle("SlideMan")
            self.setMinimumSize(1200, 800)  # Ensure enough space for workspace
            
            # Initialize Database Service
            self.logger.info("Setting up database connection")
            self.db_service = db_service
            if not self.db_service.connect():
                error_msg = f"Could not connect to the database at: {self.db_service.db_path}"
                self.logger.critical(error_msg)
                QMessageBox.critical(self, "Database Error", error_msg)
                sys.exit(1)
                
            # Initialize workspace components
            self._setup_workspace()
            
            # Create menus and actions
            self._create_actions()
            self._create_menus()
            
            # Connect signals
            self._connect_signals()
            
            # Apply settings and styling
            self._load_settings()
            self._setup_visual_styling()
            self._setup_contextual_help()
            
            self.logger.info("UnifiedMainWindow initialization completed successfully")
            
        except Exception as e:
            self.logger.critical(f"Error during UnifiedMainWindow initialization: {e}", exc_info=True)
            QMessageBox.critical(self, "Initialization Error",
                               f"Failed to initialize application: {e}\n"
                               f"Application will exit.")
            sys.exit(1)
            
    def _setup_workspace(self):
        """Set up the unified workspace layout."""
        try:
            self.logger.info("Setting up unified workspace layout")
            
            # Create main widget and layout
            main_widget = QWidget()
            main_layout = QVBoxLayout(main_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            # Header widget (fixed at top)
            self.header_widget = HeaderWidget(self.db_service)
            main_layout.addWidget(self.header_widget)
            
            # Content splitter (left panel | main content | right panel)
            content_splitter = QSplitter(Qt.Horizontal)
            content_splitter.setObjectName("contentSplitter")
            
            # Left panel (project info, keywords, actions)
            self.left_panel = LeftPanelWidget(self.db_service)
            content_splitter.addWidget(self.left_panel)
            
            # Main content area (slide library)
            self.slide_library = SlideViewPage(self.db_service)
            self.slide_library.setObjectName("slideLibrary")
            content_splitter.addWidget(self.slide_library)
            
            # Right panel (assembly workspace)
            self.assembly_panel = AssemblyPanelWidget(self.db_service)
            content_splitter.addWidget(self.assembly_panel)
            
            # Set splitter proportions (left: 240px, main: flexible, right: 280px)
            # Initial sizes will be adjusted by fixed widths of panels
            content_splitter.setSizes([240, 600, 280])
            content_splitter.setCollapsible(0, False)  # Don't allow left panel to collapse completely
            content_splitter.setCollapsible(1, False)  # Don't allow main content to collapse
            content_splitter.setCollapsible(2, True)   # Allow assembly panel to collapse
            
            main_layout.addWidget(content_splitter, 1)  # Content area should expand
            
            # Status bar
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            self.status_bar.showMessage("Ready")
            
            # Set the central widget
            self.setCentralWidget(main_widget)
            
            self.logger.debug("Workspace layout created successfully")
            
        except Exception as e:
            self.logger.critical(f"Error setting up workspace: {e}", exc_info=True)
            raise Exception(f"Failed to setup workspace: {e}")
            
    def _create_actions(self):
        """Create application actions."""
        try:
            self.logger.info("Creating application actions")
            
            # File menu actions
            self.new_project_action = QAction("&New Project...", self)
            self.new_project_action.setShortcut(QKeySequence.New)
            self.new_project_action.setStatusTip("Create a new project")
            
            self.open_project_action = QAction("&Open Project...", self)
            self.open_project_action.setShortcut(QKeySequence.Open)
            self.open_project_action.setStatusTip("Open an existing project")
            
            self.import_files_action = QAction("&Import Files...", self)
            self.import_files_action.setShortcut(QKeySequence("Ctrl+I"))
            self.import_files_action.setStatusTip("Import PowerPoint files")
            
            self.export_assembly_action = QAction("&Export Assembly...", self)
            self.export_assembly_action.setShortcut(QKeySequence("Ctrl+E"))
            self.export_assembly_action.setStatusTip("Export current assembly to PowerPoint")
            
            self.exit_action = QAction("E&xit", self)
            self.exit_action.setShortcut(QKeySequence.Quit)
            self.exit_action.setStatusTip("Exit the application")
            
            # Edit menu actions
            self.undo_action = QAction("&Undo", self)
            self.undo_action.setShortcut(QKeySequence.Undo)
            
            self.redo_action = QAction("&Redo", self)
            self.redo_action.setShortcut(QKeySequence.Redo)
            
            # View menu actions
            self.toggle_left_panel_action = QAction("Toggle &Left Panel", self)
            self.toggle_left_panel_action.setShortcut(QKeySequence("F9"))
            self.toggle_left_panel_action.setCheckable(True)
            self.toggle_left_panel_action.setChecked(True)
            
            self.toggle_assembly_panel_action = QAction("Toggle &Assembly Panel", self)
            self.toggle_assembly_panel_action.setShortcut(QKeySequence("F10"))
            self.toggle_assembly_panel_action.setCheckable(True)
            self.toggle_assembly_panel_action.setChecked(True)
            
            self.toggle_theme_action = QAction("Toggle &Theme", self)
            self.toggle_theme_action.setShortcut(QKeySequence("Ctrl+T"))
            
            # Help menu actions
            self.show_help_action = QAction("&Help", self)
            self.show_help_action.setShortcut(QKeySequence.HelpContents)
            
            self.about_action = QAction("&About", self)
            self.about_action.setStatusTip("About SlideMan")
            
            self.logger.debug("Actions created successfully")
            
        except Exception as e:
            self.logger.critical(f"Failed to create actions: {e}", exc_info=True)
            raise Exception(f"Failed to create actions: {e}")
            
    def _create_menus(self):
        """Create application menus."""
        try:
            self.logger.info("Creating application menus")
            
            menubar = self.menuBar()
            
            # File menu
            file_menu = menubar.addMenu("&File")
            file_menu.addAction(self.new_project_action)
            file_menu.addAction(self.open_project_action)
            file_menu.addSeparator()
            file_menu.addAction(self.import_files_action)
            file_menu.addAction(self.export_assembly_action)
            file_menu.addSeparator()
            file_menu.addAction(self.exit_action)
            
            # Edit menu
            edit_menu = menubar.addMenu("&Edit")
            edit_menu.addAction(self.undo_action)
            edit_menu.addAction(self.redo_action)
            
            # View menu
            view_menu = menubar.addMenu("&View")
            view_menu.addAction(self.toggle_left_panel_action)
            view_menu.addAction(self.toggle_assembly_panel_action)
            view_menu.addSeparator()
            view_menu.addAction(self.toggle_theme_action)
            
            # Help menu
            help_menu = menubar.addMenu("&Help")
            help_menu.addAction(self.show_help_action)
            help_menu.addSeparator()
            help_menu.addAction(self.about_action)
            
            self.logger.debug("Menus created successfully")
            
        except Exception as e:
            self.logger.critical(f"Failed to create menus: {e}", exc_info=True)
            raise Exception(f"Failed to create menus: {e}")
            
    def _connect_signals(self):
        """Connect all signals for the unified workspace."""
        try:
            self.logger.info("Connecting signals")
            
            # Connect action signals
            self.new_project_action.triggered.connect(self._new_project)
            self.open_project_action.triggered.connect(self._open_project)
            self.import_files_action.triggered.connect(self._import_files)
            self.export_assembly_action.triggered.connect(self._export_assembly)
            self.exit_action.triggered.connect(self.close)
            
            # Connect undo/redo to app state
            self.undo_action.triggered.connect(app_state.undo_stack.undo)
            self.redo_action.triggered.connect(app_state.undo_stack.redo)
            
            # Connect view toggles
            self.toggle_left_panel_action.triggered.connect(self._toggle_left_panel)
            self.toggle_assembly_panel_action.triggered.connect(self._toggle_assembly_panel)
            self.toggle_theme_action.triggered.connect(self._toggle_theme)
            
            # Connect help actions
            self.show_help_action.triggered.connect(self._show_help)
            self.about_action.triggered.connect(self._show_about)
            
            # Connect header widget signals
            self.header_widget.projectSelected.connect(self._on_project_selected)
            self.header_widget.searchQueryChanged.connect(self._on_search_query_changed)
            self.header_widget.exportRequested.connect(self._export_assembly)
            
            # Connect left panel signals
            self.left_panel.importFilesRequested.connect(self._import_files)
            self.left_panel.loadDemoRequested.connect(self._load_demo_project)
            self.left_panel.keywordFilterChanged.connect(self._on_keyword_filter_changed)
            self.left_panel.newProjectRequested.connect(self._new_project)
            
            # Connect assembly panel signals
            self.assembly_panel.previewRequested.connect(self._preview_assembly)
            self.assembly_panel.exportRequested.connect(self._export_assembly)
            
            # Connect slide library to assembly (for drag-drop integration)
            # This will be implemented when integrating the slide library
            
            # Connect app state signals
            app_state.currentProjectChanged.connect(self._on_current_project_changed)
            app_state.undo_stack.cleanChanged.connect(self._update_window_title)
            app_state.undo_stack.canUndoChanged.connect(self.undo_action.setEnabled)
            app_state.undo_stack.canRedoChanged.connect(self.redo_action.setEnabled)
            
            # Connect event bus signals
            event_bus.onboardingProgressUpdate.connect(self._track_onboarding_progress)
            
            self.logger.debug("Signals connected successfully")
            
        except Exception as e:
            self.logger.critical(f"Failed to connect signals: {e}", exc_info=True)
            raise Exception(f"Failed to connect signals: {e}")
            
    def _setup_visual_styling(self):
        """Apply visual styling to the workspace."""
        try:
            # Apply dark theme by default
            theme.apply_theme(QApplication.instance(), "dark")
            
            # Additional workspace-specific styling
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                
                #contentSplitter::handle {
                    background-color: #3c3c3c;
                    width: 1px;
                    height: 1px;
                }
                
                #contentSplitter::handle:hover {
                    background-color: #555555;
                }
                
                #slideLibrary {
                    background-color: #2b2b2b;
                }
                
                QStatusBar {
                    background-color: #2b2b2b;
                    border-top: 1px solid #3c3c3c;
                    color: #cccccc;
                }
                
                QMenuBar {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border-bottom: 1px solid #3c3c3c;
                }
                
                QMenuBar::item {
                    padding: 8px 12px;
                    background-color: transparent;
                }
                
                QMenuBar::item:selected {
                    background-color: #3c3c3c;
                }
                
                QMenu {
                    background-color: #2b2b2b;
                    border: 1px solid #3c3c3c;
                    color: #ffffff;
                }
                
                QMenu::item {
                    padding: 8px 24px;
                }
                
                QMenu::item:selected {
                    background-color: #0078d4;
                }
                
                QMenu::separator {
                    height: 1px;
                    background-color: #3c3c3c;
                    margin: 4px 0px;
                }
            """)
            
        except Exception as e:
            self.logger.error(f"Failed to apply visual styling: {e}")
            
    def _setup_contextual_help(self):
        """Set up contextual help system."""
        try:
            # Initialize contextual help for workspace
            contextual_help.register_context("workspace", 
                "Use the left panel to filter slides by keywords, "
                "browse slides in the center, and build presentations "
                "in the assembly panel on the right.")
                
        except Exception as e:
            self.logger.error(f"Failed to setup contextual help: {e}")
            
    def _load_settings(self):
        """Load application settings."""
        try:
            settings = QSettings(ORG_NAME, APP_NAME)
            
            # Restore window geometry
            geometry = settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
                
            # Restore window state
            state = settings.value("windowState")
            if state:
                self.restoreState(state)
                
        except Exception as e:
            self.logger.warning(f"Failed to load settings: {e}")
            
    def _save_settings(self):
        """Save application settings."""
        try:
            settings = QSettings(ORG_NAME, APP_NAME)
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            
    # Slot implementations for actions
    @Slot()
    def _new_project(self):
        """Create a new project."""
        self.logger.info("New project requested")
        # Implementation will use existing project creation logic
        pass
        
    @Slot()
    def _open_project(self):
        """Open an existing project."""
        self.logger.info("Open project requested")
        # Implementation will use existing project opening logic
        pass
        
    @Slot()
    def _import_files(self):
        """Import PowerPoint files."""
        self.logger.info("Import files requested")
        # Implementation will use existing file import logic
        pass
        
    @Slot()
    def _export_assembly(self):
        """Export current assembly."""
        self.logger.info("Export assembly requested")
        # Implementation will use existing export logic
        pass
        
    @Slot()
    def _preview_assembly(self):
        """Preview current assembly."""
        self.logger.info("Preview assembly requested")
        # Implementation will create assembly preview
        pass
        
    @Slot()
    def _load_demo_project(self):
        """Load demo project."""
        self.logger.info("Load demo project requested")
        try:
            demo_service = DemoContentService(self.db_service)
            success = demo_service.create_demo_project()
            if success:
                self.status_bar.showMessage("Demo project loaded successfully", 3000)
            else:
                self.status_bar.showMessage("Failed to load demo project", 3000)
        except Exception as e:
            self.logger.error(f"Failed to load demo project: {e}")
            
    @Slot(bool)
    def _toggle_left_panel(self, visible: bool):
        """Toggle left panel visibility."""
        self.left_panel.setVisible(visible)
        
    @Slot(bool)
    def _toggle_assembly_panel(self, visible: bool):
        """Toggle assembly panel visibility."""
        self.assembly_panel.setVisible(visible)
        
    @Slot()
    def _toggle_theme(self):
        """Toggle application theme."""
        try:
            theme.apply_theme(QApplication.instance(), "dark")
            QSettings().setValue("theme", "dark")
            self.status_bar.showMessage("Dark theme applied", 2000)
        except Exception as e:
            self.logger.error(f"Failed to toggle theme: {e}")
            
    @Slot()
    def _show_help(self):
        """Show application help."""
        self.status_bar.showMessage("Help feature coming soon!", 3000)
        
    @Slot()
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(self,
                         f"About {QCoreApplication.applicationName()}",
                         f"<b>{QCoreApplication.applicationName()}</b> v{QCoreApplication.applicationVersion()}"
                         f"<p>A smart PowerPoint library and assembly tool.</p>"
                         f"<p>Organization: MaMa Marketing GmbH</p>"
                         f"<p>&copy; 2025 All rights reserved.</p>"
                         f"<p><small>Written by Monirul Islam</small></p>"
                         f"<p><small>For support: islam@mama-marketing.de</small></p>")
                         
    # Workspace-specific signal handlers
    @Slot(str)
    def _on_project_selected(self, project_path: str):
        """Handle project selection from header."""
        self.logger.info(f"Project selected: {project_path}")
        app_state.set_current_project_path(project_path)
        
    @Slot(str)
    def _on_search_query_changed(self, query: str):
        """Handle search query change from header."""
        self.logger.debug(f"Search query changed: {query}")
        # Apply search filter to slide library
        if hasattr(self.slide_library, 'apply_search_filter'):
            self.slide_library.apply_search_filter(query)
            
    @Slot(list)
    def _on_keyword_filter_changed(self, keyword_ids: List[int]):
        """Handle keyword filter change from left panel."""
        self.logger.debug(f"Keyword filter changed: {keyword_ids}")
        # Apply keyword filter to slide library
        if hasattr(self.slide_library, 'apply_keyword_filter'):
            self.slide_library.apply_keyword_filter(keyword_ids)
            
    @Slot(str)
    def _on_current_project_changed(self, project_path: str):
        """Handle current project change."""
        self.logger.info(f"Current project changed: {project_path}")
        self._update_window_title()
        
        # Refresh all panels
        self.left_panel.refresh_all()
        if hasattr(self.slide_library, 'refresh_for_project'):
            self.slide_library.refresh_for_project()
            
    @Slot(bool)
    def _update_window_title(self, is_clean: bool = True):
        """Update window title based on current state."""
        title = f"{QCoreApplication.applicationName()}"
        
        # Add project name if available
        if app_state.current_project_path:
            try:
                project = self.db_service.get_project_by_path(app_state.current_project_path)
                if project:
                    title += f" - {project.name}"
            except Exception:
                pass
                
        # Add modified indicator
        if not is_clean:
            title += " [*]"
            
        self.setWindowTitle(title)
        
    @Slot(int)
    def _track_onboarding_progress(self, completed_actions: int):
        """Track onboarding progress."""
        # Implementation for onboarding progress tracking
        pass
        
    def showEvent(self, event):
        """Override showEvent to show welcome dialog on first run."""
        super().showEvent(event)
        
        # Show welcome dialog on first run
        if app_state.is_first_run():
            self.logger.info("First run detected, showing welcome dialog")
            self._show_welcome_dialog()
            self._check_platform_capabilities()
            
    def _show_welcome_dialog(self):
        """Show the welcome dialog for new users."""
        welcome_dialog = WelcomeDialog(self)
        
        # Connect signals
        welcome_dialog.startTutorialRequested.connect(self._start_tutorial)
        welcome_dialog.importSlidesRequested.connect(self._import_files)
        welcome_dialog.loadDemoRequested.connect(self._load_demo_project)
        welcome_dialog.skipWelcomeRequested.connect(self._skip_welcome)
        
        welcome_dialog.exec()
        
    def _start_tutorial(self):
        """Start the interactive tutorial."""
        self.logger.info("Starting tutorial")
        app_state.complete_first_run()
        self.status_bar.showMessage("Tutorial feature coming soon!", 3000)
        
    def _skip_welcome(self):
        """Skip welcome and mark first run complete."""
        self.logger.info("Welcome skipped")
        app_state.complete_first_run()
        
    def _check_platform_capabilities(self):
        """Check platform capabilities and show warnings if needed."""
        if not platform_capabilities.has_powerpoint:
            QMessageBox.warning(self, "Platform Warning",
                              "PowerPoint is not detected on this system. "
                              "Slide conversion features may not work properly.")
                              
    def closeEvent(self, event):
        """Handle application close event."""
        self._save_settings()
        super().closeEvent(event)