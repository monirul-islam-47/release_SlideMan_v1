# src/slideman/ui/components/header_widget.py

import logging
from typing import Optional, List
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QComboBox, QLineEdit, QPushButton, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QFont, QIcon

from ...app_state import app_state
from ...event_bus import event_bus
from ...models.project import Project
from ...services.database import Database
from ...services.exceptions import DatabaseError
from .debounced_search import DebouncedSearchEdit

class HeaderWidget(QWidget):
    """
    Header widget containing project selector, search, and export functionality.
    This widget provides persistent context and global actions for the workspace.
    """
    
    # Signals
    projectSelected = Signal(str)  # project_path
    searchQueryChanged = Signal(str)  # search_query
    exportRequested = Signal()
    
    def __init__(self, db_service: Database, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.db_service = db_service
        self.logger = logging.getLogger(__name__)
        
        self._setup_ui()
        self._connect_signals()
        self._load_projects()
        
    def _setup_ui(self):
        """Set up the header UI layout."""
        self.setFixedHeight(60)  # Fixed header height
        self.setObjectName("headerWidget")
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)
        
        # App branding
        app_label = QLabel("SlideMan")
        app_label.setObjectName("appTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        app_label.setFont(font)
        layout.addWidget(app_label)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setObjectName("separator")
        layout.addWidget(separator1)
        
        # Project selector section
        project_layout = QHBoxLayout()
        project_layout.setSpacing(8)
        
        project_label = QLabel("Project:")
        project_label.setObjectName("sectionLabel")
        project_layout.addWidget(project_label)
        
        self.project_combo = QComboBox()
        self.project_combo.setObjectName("projectSelector")
        self.project_combo.setMinimumWidth(200)
        self.project_combo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        project_layout.addWidget(self.project_combo)
        
        layout.addLayout(project_layout)
        
        # Spacer to push search and export to the right
        layout.addStretch(1)
        
        # Search section
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        
        search_label = QLabel("🔍")
        search_label.setObjectName("searchIcon")
        search_layout.addWidget(search_label)
        
        self.search_edit = DebouncedSearchEdit()
        self.search_edit.setObjectName("universalSearch")
        self.search_edit.setPlaceholderText("Search slides...")
        self.search_edit.setMinimumWidth(300)
        search_layout.addWidget(self.search_edit)
        
        layout.addLayout(search_layout)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setObjectName("separator")
        layout.addWidget(separator2)
        
        # Export button
        self.export_btn = QPushButton("📤 Export")
        self.export_btn.setObjectName("exportButton")
        self.export_btn.setMinimumWidth(100)
        layout.addWidget(self.export_btn)
        
        # Apply styling
        self._apply_styling()
        
    def _apply_styling(self):
        """Apply custom styling to the header widget."""
        self.setStyleSheet("""
            #headerWidget {
                background-color: #2b2b2b;
                border-bottom: 2px solid #3c3c3c;
            }
            
            #appTitle {
                color: #ffffff;
                font-weight: bold;
                font-size: 14pt;
            }
            
            #sectionLabel {
                color: #cccccc;
                font-weight: 500;
            }
            
            #projectSelector {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
                color: #ffffff;
                font-size: 11pt;
            }
            
            #projectSelector:hover {
                border-color: #777777;
            }
            
            #projectSelector:focus {
                border-color: #0078d4;
                outline: none;
            }
            
            #projectSelector::drop-down {
                border: none;
                width: 20px;
            }
            
            #projectSelector::down-arrow {
                image: url(:/icons/cil-chevron-bottom.png);
                width: 12px;
                height: 12px;
            }
            
            #universalSearch {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 12px;
                color: #ffffff;
                font-size: 11pt;
            }
            
            #universalSearch:hover {
                border-color: #777777;
            }
            
            #universalSearch:focus {
                border-color: #0078d4;
                outline: none;
            }
            
            #exportButton {
                background-color: #0078d4;
                border: 1px solid #0078d4;
                border-radius: 4px;
                padding: 8px 16px;
                color: #ffffff;
                font-weight: 500;
                font-size: 11pt;
            }
            
            #exportButton:hover {
                background-color: #106ebe;
                border-color: #106ebe;
            }
            
            #exportButton:pressed {
                background-color: #005a9e;
                border-color: #005a9e;
            }
            
            #exportButton:disabled {
                background-color: #555555;
                border-color: #555555;
                color: #888888;
            }
            
            #searchIcon {
                color: #cccccc;
                font-size: 14pt;
            }
            
            #separator {
                color: #555555;
                max-width: 1px;
            }
        """)
        
    def _connect_signals(self):
        """Connect internal signals."""
        self.project_combo.currentTextChanged.connect(self._on_project_changed)
        self.search_edit.searchChanged.connect(self._on_search_changed)
        self.export_btn.clicked.connect(self._on_export_clicked)
        
        # Connect to app state changes
        app_state.currentProjectChanged.connect(self._on_current_project_changed)
        
    def _load_projects(self):
        """Load available projects into the combo box."""
        try:
            self.project_combo.clear()
            self.project_combo.addItem("Select a project...", None)
            
            projects = self.db_service.get_all_projects()
            for project in projects:
                self.project_combo.addItem(project.name, project.folder_path)
                
            # If there's a current project, select it
            if app_state.current_project_path:
                self._select_current_project()
                
        except DatabaseError as e:
            self.logger.error(f"Failed to load projects: {e}")
            
    def _select_current_project(self):
        """Select the current project in the combo box."""
        current_path = app_state.current_project_path
        if not current_path:
            return
            
        for i in range(self.project_combo.count()):
            if self.project_combo.itemData(i) == current_path:
                self.project_combo.setCurrentIndex(i)
                break
                
    @Slot(str)
    def _on_project_changed(self, project_name: str):
        """Handle project selection change."""
        if not project_name or project_name == "Select a project...":
            return
            
        # Get the project path from combo data
        current_index = self.project_combo.currentIndex()
        project_path = self.project_combo.itemData(current_index)
        
        if project_path and project_path != app_state.current_project_path:
            self.logger.info(f"Project changed to: {project_name}")
            self.projectSelected.emit(project_path)
            
    @Slot(str)
    def _on_search_changed(self, query: str):
        """Handle search query change."""
        self.logger.debug(f"Search query changed: {query}")
        self.searchQueryChanged.emit(query)
        
    @Slot()
    def _on_export_clicked(self):
        """Handle export button click."""
        self.logger.info("Export requested from header")
        self.exportRequested.emit()
        
    @Slot(str)
    def _on_current_project_changed(self, project_path: str):
        """Handle current project change from app state."""
        self._select_current_project()
        
        # Update export button state based on assembly content
        # This will be connected to assembly state later
        self._update_export_button_state()
        
    def _update_export_button_state(self):
        """Update export button enabled state based on context."""
        # For now, enable if there's a current project
        # Later this will check if there are slides in the assembly
        has_project = bool(app_state.current_project_path)
        self.export_btn.setEnabled(has_project)
        
        if not has_project:
            self.export_btn.setToolTip("Select a project to enable export")
        else:
            self.export_btn.setToolTip("Export current assembly to PowerPoint")
            
    def refresh_projects(self):
        """Refresh the project list (call when projects are added/removed)."""
        self._load_projects()
        
    def get_search_query(self) -> str:
        """Get the current search query."""
        return self.search_edit.text()
        
    def set_search_query(self, query: str):
        """Set the search query programmatically."""
        self.search_edit.setText(query)
        
    def clear_search(self):
        """Clear the search query."""
        self.search_edit.clear()
        
    def get_current_project_path(self) -> Optional[str]:
        """Get the currently selected project path."""
        current_index = self.project_combo.currentIndex()
        if current_index > 0:  # Skip "Select a project..." option
            return self.project_combo.itemData(current_index)
        return None