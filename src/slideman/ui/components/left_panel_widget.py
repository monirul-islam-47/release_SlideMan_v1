# src/slideman/ui/components/left_panel_widget.py

import logging
from typing import Optional, List, Dict
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QScrollArea, QListWidget,
                             QListWidgetItem, QCheckBox, QFileDialog, QMessageBox,
                             QSizePolicy, QGroupBox)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QFont, QIcon

from ...app_state import app_state
from ...event_bus import event_bus
from ...models.project import Project
from ...models.keyword import Keyword
from ...services.database import Database
from ...services.exceptions import DatabaseError
from ...services import file_io

class KeywordFilterWidget(QWidget):
    """Widget for displaying and filtering by keywords."""
    
    keywordSelectionChanged = Signal(list)  # List of selected keyword IDs
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.selected_keywords: List[int] = []
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the keyword filter UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        header_label = QLabel("🏷️ Keywords")
        header_label.setObjectName("sectionHeader")
        font = QFont()
        font.setBold(True)
        header_label.setFont(font)
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("clearButton")
        clear_btn.clicked.connect(self.clear_selection)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Keyword list
        self.keyword_list = QListWidget()
        self.keyword_list.setObjectName("keywordList")
        self.keyword_list.setMaximumHeight(300)
        layout.addWidget(self.keyword_list)
        
        # Add keyword button
        add_keyword_btn = QPushButton("+ Add Keyword")
        add_keyword_btn.setObjectName("addKeywordButton")
        add_keyword_btn.clicked.connect(self._add_keyword_requested)
        layout.addWidget(add_keyword_btn)
        
        self._apply_styling()
        
    def _apply_styling(self):
        """Apply styling to the keyword widget."""
        self.setStyleSheet("""
            #sectionHeader {
                color: #ffffff;
                font-weight: bold;
                font-size: 11pt;
            }
            
            #keywordList {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                alternate-background-color: #2b2b2b;
            }
            
            #keywordList::item {
                padding: 4px;
                border: none;
            }
            
            #keywordList::item:hover {
                background-color: #4a4a4a;
            }
            
            #keywordList::item:selected {
                background-color: #0078d4;
            }
            
            #clearButton, #addKeywordButton {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px 8px;
                color: #ffffff;
                font-size: 9pt;
            }
            
            #clearButton:hover, #addKeywordButton:hover {
                background-color: #4a4a4a;
                border-color: #777777;
            }
            
            #addKeywordButton {
                background-color: #0078d4;
                border-color: #0078d4;
            }
            
            #addKeywordButton:hover {
                background-color: #106ebe;
                border-color: #106ebe;
            }
        """)
        
    def update_keywords(self, keywords: List[Keyword]):
        """Update the keyword list."""
        self.keyword_list.clear()
        
        for keyword in keywords:
            item = QListWidgetItem()
            checkbox = QCheckBox(f"{keyword.text} ({keyword.usage_count if hasattr(keyword, 'usage_count') else 0})")
            checkbox.setObjectName("keywordCheckbox")
            checkbox.setStyleSheet("""
                #keywordCheckbox {
                    color: #ffffff;
                    spacing: 5px;
                }
                #keywordCheckbox::indicator {
                    width: 16px;
                    height: 16px;
                }
                #keywordCheckbox::indicator:unchecked {
                    background-color: #3c3c3c;
                    border: 1px solid #555555;
                    border-radius: 3px;
                }
                #keywordCheckbox::indicator:checked {
                    background-color: #0078d4;
                    border: 1px solid #0078d4;
                    border-radius: 3px;
                    image: url(:/icons/cil-check.png);
                }
                #keywordCheckbox::indicator:hover {
                    border-color: #777777;
                }
            """)
            
            checkbox.stateChanged.connect(lambda state, kid=keyword.id: self._on_keyword_toggled(kid, state))
            
            item.setSizeHint(checkbox.sizeHint())
            self.keyword_list.addItem(item)
            self.keyword_list.setItemWidget(item, checkbox)
            
    def _on_keyword_toggled(self, keyword_id: int, state: int):
        """Handle keyword checkbox toggle."""
        if state == Qt.Checked:
            if keyword_id not in self.selected_keywords:
                self.selected_keywords.append(keyword_id)
        else:
            if keyword_id in self.selected_keywords:
                self.selected_keywords.remove(keyword_id)
                
        self.keywordSelectionChanged.emit(self.selected_keywords.copy())
        
    def clear_selection(self):
        """Clear all keyword selections."""
        self.selected_keywords.clear()
        
        # Uncheck all checkboxes
        for i in range(self.keyword_list.count()):
            item = self.keyword_list.item(i)
            checkbox = self.keyword_list.itemWidget(item)
            if checkbox:
                checkbox.setChecked(False)
                
        self.keywordSelectionChanged.emit([])
        
    def _add_keyword_requested(self):
        """Handle add keyword button click."""
        # This will be connected to the main application's keyword management
        event_bus.addKeywordRequested.emit()


class LeftPanelWidget(QWidget):
    """
    Left panel widget containing project information, quick actions, and keyword filtering.
    Provides context and navigation aids for the workspace.
    """
    
    # Signals
    importFilesRequested = Signal()
    loadDemoRequested = Signal()
    keywordFilterChanged = Signal(list)  # List of selected keyword IDs
    newProjectRequested = Signal()
    
    def __init__(self, db_service: Database, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.db_service = db_service
        self.logger = logging.getLogger(__name__)
        
        self.setFixedWidth(240)  # Fixed width for left panel
        self.setObjectName("leftPanel")
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Set up the left panel UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 8, 16)
        main_layout.setSpacing(20)
        
        # Project section
        self._create_project_section(main_layout)
        
        # Quick actions section
        self._create_quick_actions_section(main_layout)
        
        # Keywords section
        self._create_keywords_section(main_layout)
        
        # Spacer at bottom
        main_layout.addStretch()
        
        # Workflow help section (at bottom)
        self._create_workflow_help_section(main_layout)
        
        self._apply_styling()
        
    def _create_project_section(self, parent_layout: QVBoxLayout):
        """Create the project information section."""
        # Project info group
        project_group = QGroupBox("🗂️ Current Project")
        project_group.setObjectName("projectGroup")
        project_layout = QVBoxLayout(project_group)
        project_layout.setSpacing(8)
        
        # Current project label
        self.current_project_label = QLabel("No project selected")
        self.current_project_label.setObjectName("currentProjectLabel")
        self.current_project_label.setWordWrap(True)
        project_layout.addWidget(self.current_project_label)
        
        # Project stats
        self.project_stats_label = QLabel("")
        self.project_stats_label.setObjectName("projectStatsLabel")
        self.project_stats_label.setWordWrap(True)
        project_layout.addWidget(self.project_stats_label)
        
        # Recent files section
        recent_label = QLabel("Recent Files:")
        recent_label.setObjectName("sectionSubheader")
        project_layout.addWidget(recent_label)
        
        self.recent_files_list = QListWidget()
        self.recent_files_list.setObjectName("recentFilesList")
        self.recent_files_list.setMaximumHeight(120)
        project_layout.addWidget(self.recent_files_list)
        
        parent_layout.addWidget(project_group)
        
    def _create_quick_actions_section(self, parent_layout: QVBoxLayout):
        """Create the quick actions section."""
        actions_group = QGroupBox("⚡ Quick Actions")
        actions_group.setObjectName("actionsGroup")
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setSpacing(8)
        
        # New project button
        new_project_btn = QPushButton("📁 New Project")
        new_project_btn.setObjectName("actionButton")
        new_project_btn.clicked.connect(self._new_project_clicked)
        actions_layout.addWidget(new_project_btn)
        
        # Import files button
        import_btn = QPushButton("📥 Import Files")
        import_btn.setObjectName("actionButton")
        import_btn.clicked.connect(self._import_files_clicked)
        actions_layout.addWidget(import_btn)
        
        # Demo project button
        demo_btn = QPushButton("📊 Load Demo")
        demo_btn.setObjectName("actionButton")
        demo_btn.clicked.connect(self._load_demo_clicked)
        actions_layout.addWidget(demo_btn)
        
        parent_layout.addWidget(actions_group)
        
    def _create_keywords_section(self, parent_layout: QVBoxLayout):
        """Create the keywords filtering section."""
        self.keyword_widget = KeywordFilterWidget()
        self.keyword_widget.keywordSelectionChanged.connect(self._on_keyword_filter_changed)
        
        parent_layout.addWidget(self.keyword_widget)
        
    def _create_workflow_help_section(self, parent_layout: QVBoxLayout):
        """Create the workflow help section."""
        help_group = QGroupBox("💡 Workflow Help")
        help_group.setObjectName("helpGroup")
        help_layout = QVBoxLayout(help_group)
        
        self.help_text = QLabel("Select a project to get started")
        self.help_text.setObjectName("helpText")
        self.help_text.setWordWrap(True)
        help_layout.addWidget(self.help_text)
        
        parent_layout.addWidget(help_group)
        
    def _apply_styling(self):
        """Apply custom styling to the left panel."""
        self.setStyleSheet("""
            #leftPanel {
                background-color: #2b2b2b;
                border-right: 1px solid #3c3c3c;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 5px;
                color: #ffffff;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
                font-size: 10pt;
            }
            
            #currentProjectLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 11pt;
            }
            
            #projectStatsLabel {
                color: #cccccc;
                font-size: 9pt;
            }
            
            #sectionSubheader {
                color: #cccccc;
                font-weight: 500;
                font-size: 9pt;
            }
            
            #recentFilesList {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                font-size: 9pt;
                color: #ffffff;
            }
            
            #recentFilesList::item {
                padding: 2px;
                border: none;
            }
            
            #recentFilesList::item:hover {
                background-color: #4a4a4a;
            }
            
            #actionButton {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
                font-size: 10pt;
                text-align: left;
            }
            
            #actionButton:hover {
                background-color: #4a4a4a;
                border-color: #777777;
            }
            
            #actionButton:pressed {
                background-color: #2b2b2b;
            }
            
            #helpText {
                color: #cccccc;
                font-size: 9pt;
                font-style: italic;
            }
        """)
        
    def _connect_signals(self):
        """Connect internal and external signals."""
        # Connect to app state changes
        app_state.currentProjectChanged.connect(self._on_current_project_changed)
        
        # Connect to event bus
        event_bus.projectLoaded.connect(self._refresh_project_info)
        
    @Slot()
    def _new_project_clicked(self):
        """Handle new project button click."""
        self.logger.info("New project requested from left panel")
        self.newProjectRequested.emit()
        
    @Slot()
    def _import_files_clicked(self):
        """Handle import files button click."""
        self.logger.info("Import files requested from left panel")
        self.importFilesRequested.emit()
        
    @Slot()
    def _load_demo_clicked(self):
        """Handle load demo button click."""
        self.logger.info("Load demo requested from left panel")
        self.loadDemoRequested.emit()
        
    @Slot(list)
    def _on_keyword_filter_changed(self, keyword_ids: List[int]):
        """Handle keyword filter change."""
        self.logger.debug(f"Keyword filter changed: {keyword_ids}")
        self.keywordFilterChanged.emit(keyword_ids)
        
    @Slot(str)
    def _on_current_project_changed(self, project_path: str):
        """Handle current project change."""
        self._refresh_project_info()
        self._refresh_keywords()
        self._update_workflow_help()
        
    def _refresh_project_info(self):
        """Refresh the project information display."""
        try:
            if not app_state.current_project_path:
                self.current_project_label.setText("No project selected")
                self.project_stats_label.setText("")
                self.recent_files_list.clear()
                return
                
            # Get current project
            project = self.db_service.get_project_by_path(app_state.current_project_path)
            if not project:
                self.current_project_label.setText("Project not found")
                return
                
            # Update project name
            self.current_project_label.setText(project.name)
            
            # Get project statistics
            slides_count = self.db_service.get_slide_count_for_project(project.id)
            files_count = self.db_service.get_file_count_for_project(project.id)
            
            stats_text = f"{slides_count} slides • {files_count} files"
            self.project_stats_label.setText(stats_text)
            
            # Update recent files
            self._refresh_recent_files(project.id)
            
        except DatabaseError as e:
            self.logger.error(f"Failed to refresh project info: {e}")
            
    def _refresh_recent_files(self, project_id: int):
        """Refresh the recent files list."""
        try:
            self.recent_files_list.clear()
            
            files = self.db_service.get_files_for_project(project_id)
            # Show only the most recent 5 files
            recent_files = sorted(files, key=lambda f: f.created_at, reverse=True)[:5]
            
            for file in recent_files:
                filename = Path(file.rel_path).name
                item = QListWidgetItem(filename)
                item.setToolTip(file.rel_path)
                self.recent_files_list.addItem(item)
                
        except DatabaseError as e:
            self.logger.error(f"Failed to refresh recent files: {e}")
            
    def _refresh_keywords(self):
        """Refresh the keywords list."""
        try:
            if not app_state.current_project_path:
                self.keyword_widget.update_keywords([])
                return
                
            project = self.db_service.get_project_by_path(app_state.current_project_path)
            if not project:
                return
                
            keywords = self.db_service.get_keywords_for_project(project.id)
            self.keyword_widget.update_keywords(keywords)
            
        except DatabaseError as e:
            self.logger.error(f"Failed to refresh keywords: {e}")
            
    def _update_workflow_help(self):
        """Update the workflow help text based on current context."""
        if not app_state.current_project_path:
            self.help_text.setText("Select a project to get started")
            return
            
        try:
            project = self.db_service.get_project_by_path(app_state.current_project_path)
            if not project:
                return
                
            slides_count = self.db_service.get_slide_count_for_project(project.id)
            
            if slides_count == 0:
                self.help_text.setText("Import PowerPoint files to add slides to your project")
            elif slides_count < 10:
                self.help_text.setText("Tag your slides to organize them and make them easier to find")
            else:
                self.help_text.setText("Use keywords to filter slides, then drag them to Assembly to build presentations")
                
        except DatabaseError as e:
            self.logger.error(f"Failed to update workflow help: {e}")
            self.help_text.setText("Ready to work with your slides")
            
    def refresh_all(self):
        """Refresh all data in the left panel."""
        self._refresh_project_info()
        self._refresh_keywords()
        self._update_workflow_help()