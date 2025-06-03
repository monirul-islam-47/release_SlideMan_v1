# src/slideman/ui/pages/keyword_manager_page.py

import logging
from pathlib import Path
from typing import List, Dict, Optional, Any

from PySide6.QtCore import Qt, Slot, QModelIndex, QAbstractTableModel, QItemSelection, QThreadPool
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame, QLabel, 
    QToolBar, QLineEdit, QComboBox, QCheckBox, QPushButton, QSizePolicy,
    QTableView, QHeaderView, QGroupBox, QFormLayout, QTreeView, QAbstractItemView,
    QMessageBox
)
from PySide6.QtGui import QPixmap, QStandardItemModel, QStandardItem

from ...app_state import app_state
from ...services.thumbnail_cache import ThumbnailCache
from ...services.exceptions import (
    DatabaseError, ResourceNotFoundError, ValidationError,
    FileOperationError
)
from ...services.keyword_tasks import FindSimilarKeywordsWorker
from ..components.tag_edit import TagEdit
from ..custom_widgets.tag_badge_item_delegate import TagBadgeItemDelegate
from ..custom_widgets.sortable_header_view import SortableHeaderView
from ..custom_widgets.tag_edit_delegate import TagEditDelegate
from ..widgets.slide_preview_widget import SlidePreviewWidget
from ...commands.manage_slide_keyword import ReplaceSlideKeywordsCmd
from ...commands.merge_keywords_cmd import MergeKeywordsCmd
from ...commands.manage_element_keyword import LinkElementKeywordCmd, UnlinkElementKeywordCmd
import csv

class KeywordTableModel(QAbstractTableModel):
    """
    Table model for slides with their associated keywords
    """
    # Column indices
    THUMBNAIL_COL = 0
    SLIDE_COL = 1
    TOPIC_COL = 2
    TITLE_COL = 3
    ELEMENTS_COL = 4
    
    def __init__(self, db, thumbnail_cache, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.db = db
        self.thumbnail_cache = thumbnail_cache
        self._data = []  # Will contain slide data with keyword info
        self._full_data = []  # Unfiltered data
        
        # Filter properties
        self._text_filter = ""
        self._kind_filter = "All"
        self._unused_filter = False
    
    def rowCount(self, parent=None):
        return len(self._data)
    
    def columnCount(self, parent=None):
        return 5  # Thumbnail, Slide ID, Topic Tags, Title Tags, Element Tags
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            headers = ["Thumbnail", "Slide", "Topics", "Titles", "Element Tags"]
            return headers[section]
        return None
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._data)):
            return None
        
        slide_data = self._data[index.row()]
        
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == self.SLIDE_COL:
                return slide_data['slide_identifier']
            elif index.column() == self.TOPIC_COL:
                topic_tags = [kw.keyword for kw in slide_data.get('topic_tags', [])]
                return ", ".join(topic_tags)
            elif index.column() == self.TITLE_COL:
                title_tags = [kw.keyword for kw in slide_data.get('title_tags', [])]
                return ", ".join(title_tags)
            elif index.column() == self.ELEMENTS_COL:
                # Get element tags
                element_tag_count = slide_data.get('element_tag_count', 0)
                if element_tag_count > 0:
                    # Show more informative text about element tags
                    tags_sample = slide_data.get('element_tag_names', [])
                    if tags_sample:
                        sample_txt = ", ".join(tags_sample[:2])
                        if len(tags_sample) > 2:
                            sample_txt += "..."
                        return f"{element_tag_count} element(s): {sample_txt}"
                    return f"{element_tag_count} element(s) with tags"
                return "No tagged elements"
        
        elif role == Qt.ItemDataRole.DecorationRole and index.column() == self.THUMBNAIL_COL:
            # Return a thumbnail image - use the slide_id directly
            slide_id = slide_data['slide_id']
            if slide_id:
                # Call the get_thumbnail method with slide_id as it expects
                thumbnail = self.thumbnail_cache.get_thumbnail(slide_id)
                if thumbnail and not thumbnail.isNull():
                    # Make sure we return an appropriate sized thumbnail to match column width
                    return thumbnail
                else:
                    self.logger.warning(f"No thumbnail found for slide ID {slide_id}")
        
        elif role == Qt.ItemDataRole.BackgroundRole:
            # Add alternating row colors for better readability
            if index.row() % 2 == 0:
                return Qt.GlobalColor.lightGray
            
        elif role == Qt.ItemDataRole.ForegroundRole:
            # Highlight rows with missing keywords (empty fields)
            if (index.column() == self.TOPIC_COL and not slide_data.get('topic_tags', [])) or \
               (index.column() == self.TITLE_COL and not slide_data.get('title_tags', [])):
                return Qt.GlobalColor.darkRed
            
        elif role == Qt.ItemDataRole.UserRole:
            # Return the entire slide data for custom operations
            return slide_data
            
        return None
    
    def load_data(self, project_id):
        """Load slides and keywords for a project"""
        if not self.db:
            self.logger.error("Database service not available")
            return
        
        try:
            # Get all slides for the project
            slides = self.db.get_slides_for_project(project_id)
            
            # Process slides
            data = []
            for slide in slides:
                try:
                    # Get keywords for each slide
                    topic_keywords = []
                    title_keywords = []
                    
                    keywords = self.db.get_keywords_for_slide(slide['id'])
                    
                    for kw in keywords:
                        if kw.kind == 'topic':
                            topic_keywords.append(kw)
                        elif kw.kind == 'title':
                            title_keywords.append(kw)
                    
                    # Count elements with tags and collect sample tag names
                    elements = self.db.get_elements_for_slide(slide['id'])
                    element_tag_count = 0
                    element_tag_names = []
                    for element in elements:
                        try:
                            element_keywords = self.db.get_keywords_for_element(element.id)
                            # Filter for name keywords
                            name_keywords = [kw for kw in element_keywords if kw.kind == 'name']
                            if name_keywords:
                                element_tag_count += 1
                                for kw in name_keywords:
                                    if kw.keyword not in element_tag_names:
                                        element_tag_names.append(kw.keyword)
                        except DatabaseError as e:
                            self.logger.warning(f"Error getting keywords for element {element.id}: {e}")
                            continue
                    
                    # Build the data row
                    slide_data = {
                        'slide_id': slide['id'],
                        'slide_identifier': f"{slide['file_name']} - Slide {slide['slide_index']}",
                        'thumbnail_path': slide['thumbnail_path'],
                        'topic_tags': topic_keywords,
                        'title_tags': title_keywords,
                        'element_tag_count': element_tag_count,
                        'element_tag_names': element_tag_names
                    }
                    
                    data.append(slide_data)
                    
                except DatabaseError as e:
                    self.logger.error(f"Database error processing slide {slide.get('id', 'unknown')}: {e}")
                    continue
            
            # Store the loaded data
            self._full_data = data
            
            # Apply any active filters
            self._apply_filters_internal()
            
            # Notify views that the model has changed
            self.beginResetModel()
            self.endResetModel()
            
            self.logger.debug(f"Loaded {len(data)} slides with keywords")
            
        except DatabaseError as e:
            self.logger.error(f"Database error loading slide data: {e}", exc_info=True)
            self._full_data = []
            self._data = []
            self.beginResetModel()
            self.endResetModel()
        except Exception as e:
            self.logger.error(f"Unexpected error loading slide data: {e}", exc_info=True)
            self._full_data = []
            self._data = []
            self.beginResetModel()
            self.endResetModel()
    
    def set_filters(self, text_filter="", kind_filter="All", unused_filter=False):
        """Set the filters and update the visible data"""
        # Update filter properties
        self._text_filter = text_filter.lower()
        self._kind_filter = kind_filter
        self._unused_filter = unused_filter
        
        # Apply the filters
        self._apply_filters_internal()
        
        # Notify views that the model has changed
        self.beginResetModel()
        self.endResetModel()
    
    def _apply_filters_internal(self):
        """Apply current filters to the full data set"""
        # Start with all data
        filtered_data = self._full_data.copy()
        
        # Apply text filter (case insensitive)
        if self._text_filter:
            text_filtered = []
            for slide in filtered_data:
                # Check if any topic matches
                topics_match = any(self._text_filter in kw.keyword.lower() for kw in slide.get('topic_tags', []))
                
                # Check if any title matches
                titles_match = any(self._text_filter in kw.keyword.lower() for kw in slide.get('title_tags', []))
                
                # Check if slide identifier matches
                identifier_match = self._text_filter in slide['slide_identifier'].lower()
                
                if topics_match or titles_match or identifier_match:
                    text_filtered.append(slide)
            
            filtered_data = text_filtered
        
        # Apply kind filter
        if self._kind_filter != "All":
            kind_filtered = []
            kind_lower = self._kind_filter.lower()
            
            for slide in filtered_data:
                if kind_lower == "topic":
                    # Include slide if it has at least one topic tag
                    if slide.get('topic_tags', []):
                        kind_filtered.append(slide)
                        
                elif kind_lower == "title":
                    # Include slide if it has at least one title tag
                    if slide.get('title_tags', []):
                        kind_filtered.append(slide)
                        
                elif kind_lower == "name":
                    # For name tags, would need to implement similarly
                    pass
            
            filtered_data = kind_filtered
        
        # Apply unused filter
        if self._unused_filter:
            unused_filtered = []
            for slide in filtered_data:
                # A slide is "unused" if it has no topic tags and no title tags
                if not slide.get('topic_tags', []) and not slide.get('title_tags', []):
                    unused_filtered.append(slide)
            
            filtered_data = unused_filtered
        
        # Update the filtered data
        self._data = filtered_data
    
    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        """Sort the data based on the selected column and order"""
        self.logger.debug(f"Sorting by column {column}, order {order}")
        
        try:
            # Create a sorting key function based on the column
            if column == self.SLIDE_COL:
                # Sort by slide identifier
                key_func = lambda item: item['slide_identifier']
                
            elif column == self.TOPIC_COL:
                # Sort by first topic tag or empty string if none
                key_func = lambda item: item['topic_tags'][0].keyword.lower() if item.get('topic_tags') else ""
                
            elif column == self.TITLE_COL:
                # Sort by first title tag or empty string if none
                key_func = lambda item: item['title_tags'][0].keyword.lower() if item.get('title_tags') else ""
                
            elif column == self.THUMBNAIL_COL:
                # Not meaningful to sort by thumbnail, fallback to slide identifier
                key_func = lambda item: item['slide_identifier']
                
            elif column == self.ELEMENTS_COL:
                # Sort by element tag count
                key_func = lambda item: item['element_tag_count']
                
            else:
                # Default to slide identifier
                key_func = lambda item: item['slide_identifier']
            
            # Sort the data
            reverse_sort = (order == Qt.SortOrder.DescendingOrder)
            self._data.sort(key=key_func, reverse=reverse_sort)
            
            # Notify views that the layout has changed
            self.layoutChanged.emit()
            
        except Exception as e:
            self.logger.error(f"Error sorting data: {str(e)}", exc_info=True)

class KeywordManagerPage(QWidget):
    """
    Page for managing project-wide keywords, including:
    - Listing and filtering all keywords
    - Editing and deletion
    - Fuzzy merging of similar keywords
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Keyword Manager Page")
        
        # Get database service and thumbnail cache from AppState
        self.db = app_state.db_service
        if not self.db:
            self.logger.error("Database service not available in AppState!")
            
        # Create thumbnail cache
        self.thumbnail_cache = ThumbnailCache()
        
        # Selected slide for editing
        self._selected_slide_id_for_edit = None
        
        # ThreadPool for background tasks
        self._thread_pool = QThreadPool.globalInstance()
        
        # Main layout for the page
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # ----- Filter Bar Area -----
        filter_frame = QFrame()
        filter_frame.setFrameShape(QFrame.Shape.StyledPanel)
        filter_layout = QHBoxLayout(filter_frame)
        
        # Search filter
        filter_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter keywords...")
        filter_layout.addWidget(self.search_edit)
        
        # Kind filter
        filter_layout.addWidget(QLabel("Kind:"))
        self.kind_combo = QComboBox()
        self.kind_combo.addItems(["All", "Topic", "Title", "Name"])
        filter_layout.addWidget(self.kind_combo)
        
        # Show unused only filter
        self.unused_check = QCheckBox("Show Unused Only")
        filter_layout.addWidget(self.unused_check)
        
        # Find Similar button
        self.find_similar_button = QPushButton("Find Similar")
        filter_layout.addWidget(self.find_similar_button)
        
        # Export button
        self.export_button = QPushButton("Export Keywords")
        filter_layout.addWidget(self.export_button)
        
        # Add filter bar to main layout
        main_layout.addWidget(filter_frame)
        
        # ----- Main Splitter -----
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # ----- Left Pane (Table + Editing Area) -----
        left_pane_widget = QWidget()
        left_pane_layout = QVBoxLayout(left_pane_widget)
        left_pane_layout.setContentsMargins(0, 0, 0, 0)
        
        # Keyword table view
        self.keyword_table_view = QTableView()
        self.keyword_model = KeywordTableModel(self.db, self.thumbnail_cache, self)
        self.keyword_table_view.setModel(self.keyword_model)
        
        # Set up enhanced header view with sort indicators
        self.enhanced_header = SortableHeaderView(Qt.Orientation.Horizontal, self.keyword_table_view)
        self.keyword_table_view.setHorizontalHeader(self.enhanced_header)
        
        # Configure table view appearance
        self.keyword_table_view.verticalHeader().hide()
        self.keyword_table_view.horizontalHeader().setStretchLastSection(False)
        self.keyword_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.keyword_table_view.setSortingEnabled(True)
        
        # Enable alternating row colors for better readability
        self.keyword_table_view.setAlternatingRowColors(True)
        
        # Add subtle grid lines for better separation
        self.keyword_table_view.setShowGrid(True)
        self.keyword_table_view.setGridStyle(Qt.PenStyle.DotLine)
        
        # Set fixed row height for thumbnails - ensure it's large enough (200px)
        self.keyword_table_view.verticalHeader().setDefaultSectionSize(250)
        
        # Set a MUCH larger thumbnail column width (380px to ensure full thumbnail display)
        header = self.keyword_table_view.horizontalHeader()
        
        # First set all columns to a reasonable minimum width
        self.keyword_table_view.setColumnWidth(KeywordTableModel.THUMBNAIL_COL, 400)
        self.keyword_table_view.setColumnWidth(KeywordTableModel.SLIDE_COL, 200)
        self.keyword_table_view.setColumnWidth(KeywordTableModel.TOPIC_COL, 200)
        self.keyword_table_view.setColumnWidth(KeywordTableModel.TITLE_COL, 200)
        self.keyword_table_view.setColumnWidth(KeywordTableModel.ELEMENTS_COL, 200)
        
        # Set custom delegates for tag columns (displays tags as badges instead of comma-separated text)
        tag_delegate = TagBadgeItemDelegate(self.keyword_table_view)
        self.keyword_table_view.setItemDelegateForColumn(KeywordTableModel.TOPIC_COL, tag_delegate)
        self.keyword_table_view.setItemDelegateForColumn(KeywordTableModel.TITLE_COL, tag_delegate)
        
        # Set up tag editing delegate for direct editing of tags in the table
        self.tag_edit_delegate = TagEditDelegate(self.keyword_table_view)
        
        # Connect the tag edit signal to our handler
        self.tag_edit_delegate.tagsEdited.connect(self._handle_inline_tag_edit)
        
        # Enable double-click editing on topic and title columns
        self.keyword_table_view.setEditTriggers(QTableView.EditTrigger.DoubleClicked)
        
        # Force the thumbnail column to ALWAYS maintain its width and never be resized
        header.setSectionResizeMode(KeywordTableModel.THUMBNAIL_COL, QHeaderView.ResizeMode.Fixed)
        
        # Do not let other columns steal space from the thumbnail column 
        # instead they should share the remaining space
        header.setSectionResizeMode(KeywordTableModel.SLIDE_COL, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(KeywordTableModel.TOPIC_COL, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(KeywordTableModel.TITLE_COL, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(KeywordTableModel.ELEMENTS_COL, QHeaderView.ResizeMode.Interactive)
        
        # Set minimal section size for other columns to prevent them from disappearing
        header.setMinimumSectionSize(100)
        
        left_pane_layout.addWidget(self.keyword_table_view, 1)  # Set stretch factor
        
        # Editing area
        edit_widget = QWidget()
        edit_layout = QHBoxLayout(edit_widget)
        edit_layout.setContentsMargins(5, 5, 5, 5)
        
        # Left side - Slide tags and preview
        edit_left_widget = QWidget()
        edit_left_layout = QVBoxLayout(edit_left_widget)
        edit_left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Slide preview
        self.slide_preview_group = QGroupBox("Slide Preview")
        slide_preview_layout = QVBoxLayout(self.slide_preview_group)
        
        # Add slide preview widget with enhanced features
        self.slide_preview = SlidePreviewWidget(self)
        self.slide_preview.setMinimumHeight(300)  # Give it enough space to be useful
        slide_preview_layout.addWidget(self.slide_preview)
        
        # Add to left side layout
        edit_left_layout.addWidget(self.slide_preview_group)
        
        # Slide tags
        self.slide_edit_group = QGroupBox("Edit Slide Tags")
        slide_edit_layout = QFormLayout(self.slide_edit_group)
        
        # Topic tags
        topic_label = QLabel("Topics:")
        self.edit_topic_tags = TagEdit(placeholder_text="Add topic tag...")
        slide_edit_layout.addRow(topic_label, self.edit_topic_tags)
        
        # Title tags
        title_label = QLabel("Titles:")
        self.edit_title_tags = TagEdit(placeholder_text="Add title tag...")
        slide_edit_layout.addRow(title_label, self.edit_title_tags)
        
        # Apply changes button for slide tags
        self.apply_slide_button = QPushButton("Apply Slide Changes")
        self.apply_slide_button.setEnabled(False)
        slide_edit_layout.addRow("", self.apply_slide_button)
        
        # Add to left side layout
        edit_left_layout.addWidget(self.slide_edit_group)
        
        # Add left side widget to edit layout
        edit_layout.addWidget(edit_left_widget, 1)  # Give more space to preview and slide tags
        
        # Right side - Element tags
        self.element_edit_group = QGroupBox("Edit Element Tags")
        element_edit_layout = QFormLayout(self.element_edit_group)
        
        # Element list for managing element-specific tags
        element_list_label = QLabel("Elements:")
        self.element_list = QTreeView()
        self.element_list.setAlternatingRowColors(True)
        self.element_model = QStandardItemModel(0, 2)
        self.element_model.setHorizontalHeaderLabels(["Element", "Tags"])
        self.element_list.setModel(self.element_model)
        self.element_list.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.element_list.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        element_edit_layout.addRow(element_list_label, self.element_list)
        
        # Name tags for elements
        name_label = QLabel("Element Names:")
        self.edit_element_name_tags = TagEdit(placeholder_text="Add element name tag...")
        element_edit_layout.addRow(name_label, self.edit_element_name_tags)
        
        # Add element edit group to edit layout
        edit_layout.addWidget(self.element_edit_group)
        
        # Initially hide the edit groups
        self.slide_preview_group.setVisible(False)
        self.slide_edit_group.setVisible(False)
        self.element_edit_group.setVisible(False)
        
        left_pane_layout.addWidget(edit_widget)
        
        # Add left pane to splitter
        self.splitter.addWidget(left_pane_widget)
        
        # ----- Right Pane (Fuzzy Merge Panel) -----
        self.suggestion_panel = QGroupBox("Fuzzy Merge Suggestions")
        self.suggestion_panel.setCheckable(True)
        self.suggestion_panel.setChecked(False)  # Start collapsed
        suggestion_layout = QVBoxLayout(self.suggestion_panel)
        
        # Status label for merge panel
        self.merge_status_label = QLabel("Click 'Find Similar' to discover similar keywords")
        self.merge_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        suggestion_layout.addWidget(self.merge_status_label)
        
        # Create suggestion TreeView
        self.suggestion_view = QTreeView()
        self.suggestion_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.suggestion_view.setRootIsDecorated(False)  # No expand/collapse icons
        
        # Create model for suggestions
        self.suggestion_model = QStandardItemModel(0, 3, self)
        self.suggestion_model.setHorizontalHeaderLabels(["From", "To", "Score"])
        self.suggestion_view.setModel(self.suggestion_model)
        
        # Custom roles for storing data
        self.FROM_KEYWORD_ID_ROLE = Qt.ItemDataRole.UserRole + 1
        self.TO_KEYWORD_ID_ROLE = Qt.ItemDataRole.UserRole + 2
        self.KEYWORD_KIND_ROLE = Qt.ItemDataRole.UserRole + 3
        
        # Configure TreeView appearance
        self.suggestion_view.setColumnWidth(0, 120)  # From column
        self.suggestion_view.setColumnWidth(1, 120)  # To column
        
        suggestion_layout.addWidget(self.suggestion_view, 1)  # Set stretch factor
        
        # Merge action buttons
        merge_buttons_layout = QHBoxLayout()
        self.merge_button = QPushButton("Merge Selected")
        self.merge_button.setEnabled(False)
        self.ignore_button = QPushButton("Ignore")
        self.ignore_button.setEnabled(False)
        merge_buttons_layout.addWidget(self.merge_button)
        merge_buttons_layout.addWidget(self.ignore_button)
        suggestion_layout.addLayout(merge_buttons_layout)
        
        # Add right pane to splitter
        self.splitter.addWidget(self.suggestion_panel)
        
        # Set initial splitter sizes (60/40 split)
        self.splitter.setStretchFactor(0, 6)
        self.splitter.setStretchFactor(1, 4)
        
        # Add splitter to main layout
        main_layout.addWidget(self.splitter, 1)  # Set stretch factor
        
        # Add a status bar showing count of slides with/without tags
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(5, 2, 5, 2)
        
        self.status_label = QLabel("Loading tag statistics...")
        status_layout.addWidget(self.status_label)
        
        main_layout.addWidget(status_widget)
        
        # Connect signals
        self._connect_signals()
        
        # Ignored pairs for merge suggestions (prevent repeated suggestions)
        self._ignored_merge_pairs = set()
        
        self.logger.debug("Keyword Manager Page UI initialized")
    
    def _connect_signals(self):
        """Connect signals for this page"""
        # Connect to AppState signals
        app_state.projectLoaded.connect(self._load_data_for_current_project)
        app_state.projectClosed.connect(self._clear_data)
        
        # Connect search and filter controls
        self.search_edit.textChanged.connect(self._apply_filters)
        self.kind_combo.currentTextChanged.connect(self._apply_filters)
        self.unused_check.stateChanged.connect(self._apply_filters)
        
        # Connect table view selection
        self.keyword_table_view.selectionModel().selectionChanged.connect(self._handle_table_selection_changed)
        
        # Connect buttons
        self.apply_slide_button.clicked.connect(self._apply_slide_tag_changes)
        self.find_similar_button.clicked.connect(self._start_find_similar_keywords)
        self.merge_button.clicked.connect(self._handle_merge_selected)
        self.ignore_button.clicked.connect(self._handle_ignore_selected)
        self.export_button.clicked.connect(self._export_keywords)
        
        # Connect enhanced header signals
        self.enhanced_header.sortIndicatorChanged.connect(self._update_sort_indicator)
        self.enhanced_header.filterClicked.connect(self._handle_filter_column_clicked)
        
        # Connect suggestion view selection signal
        self.suggestion_view.selectionModel().selectionChanged.connect(self._handle_suggestion_selection_changed)
        self.suggestion_panel.toggled.connect(self._handle_suggestion_panel_toggle)
        
        # Connect slide preview signals
        self.slide_preview.elementClicked.connect(self._handle_element_clicked_in_preview)
        
        # Connect element list selection
        self.element_list.selectionModel().selectionChanged.connect(self._handle_element_selection_changed)
    
    @Slot()
    def _start_find_similar_keywords(self):
        """Start the background task to find similar keywords"""
        # Safety check
        if app_state.current_project_path is None:
            QMessageBox.warning(self, "No Project", "Please open a project first.")
            return
        
        # Update UI
        self.merge_status_label.setText("Finding similar keywords...")
        self.find_similar_button.setEnabled(False)
        
        # Clear previous suggestions
        self.suggestion_model.clear()
        self.suggestion_model.setHorizontalHeaderLabels(["From", "To", "Score"])
        
        # Create worker
        worker = FindSimilarKeywordsWorker(self.db, similarity_threshold=80)
        
        # Connect signals
        worker.signals.resultsReady.connect(self._handle_suggestions_ready)
        worker.signals.error.connect(self._handle_suggestions_error)
        
        # Submit to thread pool
        self._thread_pool.start(worker)
        self.logger.debug("Started FindSimilarKeywordsWorker")
    
    @Slot(list)
    def _handle_suggestions_ready(self, suggestions):
        """Handle suggestions from worker"""
        self.logger.info(f"Received {len(suggestions)} keyword merge suggestions")
        
        # Reset UI
        self.find_similar_button.setEnabled(True)
        
        # Filter out ignored suggestions
        filtered_suggestions = []
        for suggestion in suggestions:
            pair_key = (suggestion['from'].id, suggestion['to'].id)
            if pair_key not in self._ignored_merge_pairs:
                filtered_suggestions.append(suggestion)
        
        if not filtered_suggestions:
            self.merge_status_label.setText("No similar keywords found")
            return
        
        # Update status
        self.merge_status_label.setText(f"Found {len(filtered_suggestions)} similar keyword pairs")
        
        # Populate model
        self.suggestion_model.clear()
        self.suggestion_model.setHorizontalHeaderLabels(["From", "To", "Score"])
        
        for suggestion in filtered_suggestions:
            from_item = QStandardItem(suggestion['from'].keyword)
            from_item.setData(suggestion['from'].id, self.FROM_KEYWORD_ID_ROLE)
            
            to_item = QStandardItem(suggestion['to'].keyword)
            to_item.setData(suggestion['to'].id, self.TO_KEYWORD_ID_ROLE)
            
            score_item = QStandardItem(f"{suggestion['score']}%")
            
            # Store kind in both items for later use
            from_item.setData(suggestion['kind'], self.KEYWORD_KIND_ROLE)
            to_item.setData(suggestion['kind'], self.KEYWORD_KIND_ROLE)
            
            row = [from_item, to_item, score_item]
            self.suggestion_model.appendRow(row)
        
        # Resize columns to content
        self.suggestion_view.resizeColumnToContents(2)  # Score column
    
    @Slot(str)
    def _handle_suggestions_error(self, error_msg):
        """Handle error from worker"""
        self.logger.error(f"Error finding similar keywords: {error_msg}")
        
        # Reset UI
        self.find_similar_button.setEnabled(True)
        self.merge_status_label.setText(f"Error: {error_msg}")
        
        # Show error dialog
        QMessageBox.warning(self, "Error", f"Error finding similar keywords: {error_msg}")
    
    @Slot(QItemSelection, QItemSelection)
    def _handle_suggestion_selection_changed(self, selected, deselected):
        """Handle selection change in suggestion view"""
        # Enable/disable buttons based on selection
        has_selection = len(self.suggestion_view.selectionModel().selectedRows()) > 0
        self.merge_button.setEnabled(has_selection)
        self.ignore_button.setEnabled(has_selection)
    
    @Slot(QItemSelection, QItemSelection)
    def _handle_table_selection_changed(self, selected, deselected):
        """Handle selection change in the keyword table view"""
        indexes = self.keyword_table_view.selectionModel().selectedRows()
        
        if len(indexes) == 1:
            # Get the slide ID from the selected row
            index = indexes[0]
            slide_data = self.keyword_model.data(index, Qt.ItemDataRole.UserRole)
            slide_id = slide_data['slide_id']
            
            if slide_id is not None:
                self._selected_slide_id_for_edit = slide_id
                self.logger.debug(f"Selected slide ID {slide_id} for editing")
                
                # Fetch current keywords for this slide
                topic_keywords = self.db.get_keywords_for_slide(slide_id, kind='topic')
                topic_texts = [kw.keyword for kw in topic_keywords]
                
                title_keywords = self.db.get_keywords_for_slide(slide_id, kind='title')
                title_texts = [kw.keyword for kw in title_keywords]
                
                # Update tag edit widgets
                self.edit_topic_tags.set_tags(topic_texts)
                self.edit_title_tags.set_tags(title_texts)
                
                # Store the current index for possible later editing
                self._current_edit_index = index
                
                # NOTE: We're not setting per-index delegates since QTableView doesn't support that
                # Instead, we're using column-based delegates that are already set up in __init__
                
                # Load elements for this slide
                elements = self._load_elements_for_slide(slide_id)
                
                # Update slide preview with elements
                self._update_slide_preview(slide_id, elements)
                
                # Show editing panels
                self.slide_preview_group.setVisible(True)
                self.slide_edit_group.setVisible(True)
                self.element_edit_group.setVisible(True)
                self.apply_slide_button.setEnabled(True)
                
                return
                
        # No valid selection, clear the edit area
        self._selected_slide_id_for_edit = None
        self._current_edit_index = None
        
        # Clear editing widgets
        self.edit_topic_tags.clear()
        self.edit_title_tags.clear()
        self.element_model.clear()
        self.element_model.setHorizontalHeaderLabels(["Element", "Tags"])
        self.slide_preview.clear()
        
        # Hide editing panels
        self.slide_preview_group.setVisible(False)
        self.slide_edit_group.setVisible(False)
        self.element_edit_group.setVisible(False)
        self.apply_slide_button.setEnabled(False)
    
    def _load_elements_for_slide(self, slide_id):
        """Load elements and their tags for the selected slide"""
        if not self.db:
            return []
            
        # Clear the element model
        self.element_model.clear()
        self.element_model.setHorizontalHeaderLabels(["Element", "Tags"])
        
        try:
            # Get all elements for this slide
            elements = self.db.get_elements_for_slide(slide_id)
            
            # Get name keywords for each element
            for element in elements:
                element_keywords = self.db.get_keywords_for_element(element.id)
                # Filter for name keywords after retrieving all keywords
                name_texts = [kw.keyword for kw in element_keywords if kw.kind == 'name']
                
                # Add element to the model with more descriptive element type
                element_type = self._get_friendly_element_type(element.element_type)
                element_item = QStandardItem(f"{element_type} {element.id}")
                element_item.setData(element.id, Qt.ItemDataRole.UserRole)
                
                # Format tags display
                tags_item = QStandardItem()
                if name_texts:
                    tags_text = ", ".join(name_texts)
                    tags_item.setText(tags_text)
                    # Highlight elements with tags
                    tags_item.setForeground(Qt.GlobalColor.darkBlue)
                    element_item.setForeground(Qt.GlobalColor.darkBlue)
                else:
                    tags_item.setText("No tags")
                    # Highlight elements without tags in red
                    tags_item.setForeground(Qt.GlobalColor.darkRed)
                
                self.element_model.appendRow([element_item, tags_item])
            
            # Connect element selection to tag editing
            self.element_list.selectionModel().selectionChanged.connect(self._handle_element_selection_changed)
                
            return elements
                
        except Exception as e:
            self.logger.error(f"Error loading elements for slide {slide_id}: {str(e)}")
            return []
    
    def _update_slide_preview(self, slide_id, elements):
        """Update the slide preview with the selected slide"""
        if not slide_id or not self.thumbnail_cache:
            self.slide_preview.clear()
            return
            
        # Get thumbnail for this slide
        thumbnail = self.thumbnail_cache.get_thumbnail(slide_id)
        if not thumbnail or thumbnail.isNull():
            self.logger.warning(f"No thumbnail found for slide ID {slide_id}")
            self.slide_preview.clear()
            return
            
        # Set the slide image on the preview widget
        self.slide_preview.set_slide_image(thumbnail)
        
        # Process elements for preview
        elements_with_bounds = []
        for element in elements:
            # Check if element has bounds information
            if hasattr(element, 'bounds') and element.bounds:
                try:
                    # Parse bounds if it's a string "x,y,width,height"
                    if isinstance(element.bounds, str):
                        x, y, width, height = map(int, element.bounds.split(","))
                    else:
                        # Or use directly if it's already a tuple
                        x, y, width, height = element.bounds
                        
                    # Add to elements list for preview
                    elements_with_bounds.append({
                        "id": element.id,
                        "type": element.element_type,
                        "name": f"{self._get_friendly_element_type(element.element_type)} {element.id}",
                        "bounds": (x, y, width, height)
                    })
                except (ValueError, AttributeError, TypeError) as e:
                    self.logger.warning(f"Invalid element bounds for element {element.id}: {e}")
        
        # Update the preview with processed elements
        self.slide_preview.set_elements(elements_with_bounds)
    
    @Slot(int)
    def _handle_element_clicked_in_preview(self, element_id):
        """Handle when an element is clicked in the preview"""
        if not element_id:
            return
            
        # Find the row with this element ID
        for row in range(self.element_model.rowCount()):
            item = self.element_model.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == element_id:
                # Select this element in the list
                self.element_list.setCurrentIndex(self.element_model.index(row, 0))
                break
    
    def _get_friendly_element_type(self, type_code):
        """Convert element type code to a friendly name"""
        element_types = {
            "PICTURE": "Image",
            "SHAPE": "Shape",
            "TABLE": "Table",
            "GROUP": "Group",
            "TEXT": "Text",
            "CHART": "Chart"
        }
        return element_types.get(type_code, type_code)
    
    @Slot(QItemSelection, QItemSelection)
    def _handle_element_selection_changed(self, selected, deselected):
        """Handle selection change in the element list"""
        indexes = self.element_list.selectionModel().selectedRows()
        
        if len(indexes) == 1:
            # Get the element ID from the selected row
            index = indexes[0]
            element_id = self.element_model.data(index, Qt.ItemDataRole.UserRole)
            
            if element_id is not None:
                # Get name keywords for this element
                name_keywords = self.db.get_keywords_for_element(element_id)
                # Filter for name keywords after retrieval
                name_texts = [kw.keyword for kw in name_keywords if kw.kind == 'name']
                
                # Update tag edit widget
                self.edit_element_name_tags.set_tags(name_texts)
                
                # Connect tag signals
                self.edit_element_name_tags.tagAdded.connect(
                    lambda tag: self._handle_element_tag_added(element_id, tag)
                )
                self.edit_element_name_tags.tagRemoved.connect(
                    lambda tag: self._handle_element_tag_removed(element_id, tag)
                )
                
                # Highlight the element in the preview
                self.slide_preview.highlight_element(element_id)
                
                return
        
        # If no row or multiple rows selected, clear element name tags
        self.edit_element_name_tags.clear()
        
        # Clear highlight in preview
        self.slide_preview.highlight_element(None)
    
    def _handle_element_tag_added(self, element_id, tag):
        """Handle adding a tag to an element"""
        if not self.db or not element_id:
            return
            
        # Create and push command
        cmd = LinkElementKeywordCmd(element_id, tag, 'name', f"Add '{tag}' name tag to element")
        app_state.undo_stack.push(cmd)
        
        # Update element list
        self._refresh_element_list_item(element_id)
    
    def _handle_element_tag_removed(self, element_id, tag):
        """Handle removing a tag from an element"""
        if not self.db or not element_id:
            return
            
        # Create and push command
        cmd = UnlinkElementKeywordCmd(element_id, tag, 'name', f"Remove '{tag}' name tag from element")
        app_state.undo_stack.push(cmd)
        
        # Update element list
        self._refresh_element_list_item(element_id)
    
    def _refresh_element_list_item(self, element_id):
        """Refresh a specific item in the element list after tag changes"""
        # Find the row with the specified element ID
        for row in range(self.element_model.rowCount()):
            item = self.element_model.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == element_id:
                # Get updated keywords
                name_keywords = self.db.get_keywords_for_element(element_id)
                # Filter for name keywords after retrieval
                name_texts = [kw.keyword for kw in name_keywords if kw.kind == 'name']
                
                # Update tags display
                tags_text = ", ".join(name_texts) if name_texts else "No tags"
                self.element_model.item(row, 1).setText(tags_text)
                break
    
    @Slot()
    def _apply_slide_tag_changes(self):
        """Apply the changes made to the slide tags"""
        if not self._selected_slide_id_for_edit:
            self.logger.warning("Cannot apply changes: No slide selected")
            return
        
        slide_id = self._selected_slide_id_for_edit
        
        # Get current tags from edit widgets
        topic_tags = self.edit_topic_tags.get_tags()
        title_tags = self.edit_title_tags.get_tags()
        
        self.logger.info(f"Applying tag changes to slide ID {slide_id}")
        self.logger.debug(f"New topic tags: {topic_tags}")
        self.logger.debug(f"New title tags: {title_tags}")
        
        # Create and push commands to undo stack
        topic_cmd = ReplaceSlideKeywordsCmd(slide_id, 'topic', topic_tags, f"Update topic tags for slide")
        title_cmd = ReplaceSlideKeywordsCmd(slide_id, 'title', title_tags, f"Update title tags for slide")
        
        app_state.undo_stack.push(topic_cmd)
        app_state.undo_stack.push(title_cmd)
        
        # Refresh the table model to show updated tags
        project_id = self.db.get_project_id_by_path(app_state.current_project_path)
        if project_id:
            self.keyword_model.load_data(project_id)
            
    @Slot()
    def _update_sort_indicator(self, column, order):
        """Update the sort indicator in the enhanced header"""
        self.enhanced_header.setSortIndicator(column, order)
        
    def _handle_filter_column_clicked(self, column):
        """Handle filter button click on a column"""
        # Get column name
        column_name = self.keyword_model.headerData(column, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        
        # Show filter dialog or apply preset filter
        if column == KeywordTableModel.TOPIC_COL:
            # Show topics filter dialog
            self.kind_combo.setCurrentText("Topic")
            self.search_edit.setFocus()
            self.enhanced_header.setFilterIndicator(column, True)
        elif column == KeywordTableModel.TITLE_COL:
            # Show titles filter dialog
            self.kind_combo.setCurrentText("Title")
            self.search_edit.setFocus()
            self.enhanced_header.setFilterIndicator(column, True)
        elif column == KeywordTableModel.ELEMENTS_COL:
            # Toggle between showing all or only with elements
            current_state = column in self.enhanced_header._filtered_columns
            if current_state:
                # Remove filter
                self.unused_check.setChecked(False)
                self.enhanced_header.setFilterIndicator(column, False)
            else:
                # Show only slides with element tags
                self.unused_check.setChecked(True)
                self.enhanced_header.setFilterIndicator(column, True)
                
        # Apply filters
        self._apply_filters()
        
    @Slot(int, str, list)
    def _handle_inline_tag_edit(self, slide_id, tag_type, tags):
        """
        Handle when tags are edited directly in the table via the tag edit delegate
        
        Args:
            slide_id: The ID of the slide whose tags were edited
            tag_type: The type of tag ("Topic" or "Title")
            tags: List of new tag texts
        """
        self.logger.info(f"Inline editing of {tag_type.lower()} tags for slide ID {slide_id}")
        self.logger.debug(f"New {tag_type.lower()} tags: {tags}")
        
        # Create and push command to undo stack
        kind = tag_type.lower()
        cmd = ReplaceSlideKeywordsCmd(slide_id, kind, tags, f"Update {kind} tags for slide")
        app_state.undo_stack.push(cmd)
        
        # Refresh the model to show updated tags
        project_id = self.db.get_project_id_by_path(app_state.current_project_path)
        if project_id:
            self.keyword_model.load_data(project_id)
            
            # If this was the selected slide, also update the edit panels
            if self._selected_slide_id_for_edit == slide_id:
                # Update tag edit widgets to reflect the changes
                if kind == 'topic':
                    self.edit_topic_tags.set_tags(tags)
                elif kind == 'title':
                    self.edit_title_tags.set_tags(tags)

    def _clear_data(self):
        """Clear data when project is closed"""
        self.logger.info("Project closed, clearing keyword data")
        
        # Clear model data
        self.keyword_model._full_data = []
        self.keyword_model._data = []
        self.keyword_model.beginResetModel()
        self.keyword_model.endResetModel()
        
        # Clear edit area
        self._selected_slide_id_for_edit = None
        self._current_edit_index = None
        self.slide_preview_group.setVisible(False)
        self.slide_edit_group.setVisible(False)
        self.element_edit_group.setVisible(False)
        self.apply_slide_button.setEnabled(False)
        
        # Clear tag editors
        self.edit_topic_tags.clear()
        self.edit_title_tags.clear()
        self.edit_element_name_tags.clear()
        
        # Clear element list
        self.element_model.clear()
        self.element_model.setHorizontalHeaderLabels(["Element", "Tags"])
        
        # Clear slide preview
        self.slide_preview.clear()
        
        # Clear suggestion panel
        self.suggestion_model.clear()
        self.suggestion_model.setHorizontalHeaderLabels(["From", "To", "Score"])
        self.merge_status_label.setText("Click 'Find Similar' to discover similar keywords")
        
        # Reset status label
        self.status_label.setText("No project loaded")

    @Slot()
    def _load_data_for_current_project(self):
        """Load keyword data for the current project"""
        if not app_state.current_project_path or not self.db:
            self.logger.warning("Cannot load data: No project path or database")
            return
            
        self.logger.info(f"Loading keyword data for project at {app_state.current_project_path}")
        
        try:
            # Get project ID from path
            project_id = self.db.get_project_id_by_path(app_state.current_project_path)
            if not project_id:
                self.logger.error(f"No project found with path {app_state.current_project_path}")
                return
                
            # Load data into model
            self.keyword_model.load_data(project_id)
            
            # Update tag status information
            self._update_tag_statistics(project_id)
            
        except ResourceNotFoundError:
            self.logger.error(f"Project not found at path {app_state.current_project_path}")
            QMessageBox.warning(self, "Project Not Found", 
                                f"The project at '{app_state.current_project_path}' was not found in the database.")
        except DatabaseError as e:
            self.logger.error(f"Database error loading project data: {e}", exc_info=True)
            QMessageBox.critical(self, "Database Error", f"Failed to load project data:\n{e}")

    def _update_tag_statistics(self, project_id):
        """Update the status bar with tag statistics for the current project"""
        if not self.db or not project_id:
            self.status_label.setText("No project loaded")
            return
            
        try:
            # Get slide count from the model instead of directly from DB
            # This avoids needing to add a new method to the Database class
            total_slides = len(self.keyword_model._full_data)
            
            if total_slides == 0:
                self.status_label.setText("No slides in project")
                return
                
            # Count slides with different types of tags
            slides_with_topic_tags = 0
            slides_with_title_tags = 0
            
            for slide_data in self.keyword_model._full_data:
                if slide_data.get('topic_tags', []):
                    slides_with_topic_tags += 1
                if slide_data.get('title_tags', []):
                    slides_with_title_tags += 1
            
            # Calculate percentages
            topic_pct = (slides_with_topic_tags / total_slides) * 100 if total_slides > 0 else 0
            title_pct = (slides_with_title_tags / total_slides) * 100 if total_slides > 0 else 0
            
            # Format and set status text
            status_text = (
                f"Slides: {total_slides} | "
                f"With Topic Tags: {slides_with_topic_tags} ({topic_pct:.1f}%) | "
                f"With Title Tags: {slides_with_title_tags} ({title_pct:.1f}%)"
            )
            
            self.status_label.setText(status_text)
            
        except Exception as e:
            self.logger.error(f"Error updating tag statistics: {str(e)}")
            self.status_label.setText("Error updating statistics")
    
    def _apply_filters(self):
        """Apply current filters to the keyword model"""
        # Get filter values
        search_text = self.search_edit.text().strip()
        kind_filter = self.kind_combo.currentText()
        show_unused_only = self.unused_check.isChecked()
        
        # Translate kind filter
        if kind_filter == "All":
            kind_filter = None
        else:
            kind_filter = kind_filter.lower()
            
        # Apply filters to the model
        self.keyword_model.set_filters(
            text_filter=search_text,
            kind_filter=kind_filter,
            unused_filter=show_unused_only
        )
        
        # Update status text with filter counts
        filtered_count = self.keyword_model.rowCount()
        total_count = len(self.keyword_model._full_data)
        
        if filtered_count < total_count:
            # Add filter info to status
            current_status = self.status_label.text()
            if " | Filtered: " in current_status:
                # Update existing filter info
                base_status = current_status.split(" | Filtered: ")[0]
                self.status_label.setText(f"{base_status} | Filtered: {filtered_count}/{total_count}")
            else:
                # Add new filter info
                self.status_label.setText(f"{current_status} | Filtered: {filtered_count}/{total_count}")

    @Slot()
    def _handle_merge_selected(self):
        """Handle merging selected keywords"""
        if not self.db:
            self.logger.warning("Cannot merge: Database not available")
            return
            
        # Get selected rows
        indexes = self.suggestion_view.selectionModel().selectedRows()
        if not indexes:
            return
            
        # Prepare merge commands
        merge_cmds = []
        merge_pairs = []
        
        for index in indexes:
            row = index.row()
            
            # Get from and to keyword IDs and texts
            from_id = self.suggestion_model.item(row, 0).data(self.FROM_KEYWORD_ID_ROLE)
            to_id = self.suggestion_model.item(row, 1).data(self.TO_KEYWORD_ID_ROLE)
            kind = self.suggestion_model.item(row, 0).data(self.KEYWORD_KIND_ROLE)
            from_text = self.suggestion_model.item(row, 0).text()
            to_text = self.suggestion_model.item(row, 1).text()
            
            # Skip if we already have this pair
            pair = (from_id, to_id)
            if pair in merge_pairs:
                continue
                
            # Create merge command with all required parameters
            cmd = MergeKeywordsCmd(from_id, to_id, from_text, to_text, kind)
            merge_cmds.append(cmd)
            merge_pairs.append(pair)
            
            # Add to ignored pairs to prevent showing again
            self._ignored_merge_pairs.add((from_id, to_id))
        
        # Execute commands through the undo stack
        for cmd in merge_cmds:
            app_state.undo_stack.push(cmd)
            
        # Remove merged suggestions from the model
        self._refresh_suggestion_list()
        
        # Refresh the table model to show updated tags
        project_id = self.db.get_project_id_by_path(app_state.current_project_path)
        if project_id:
            self.keyword_model.load_data(project_id)
            
    @Slot()
    def _handle_ignore_selected(self):
        """Handle ignoring selected keyword pairs"""
        # Get selected rows
        indexes = self.suggestion_view.selectionModel().selectedRows()
        if not indexes:
            return
            
        # Add selected pairs to ignored set
        for index in indexes:
            row = index.row()
            
            # Get from and to keyword IDs
            from_id = self.suggestion_model.item(row, 0).data(self.FROM_KEYWORD_ID_ROLE)
            to_id = self.suggestion_model.item(row, 1).data(self.TO_KEYWORD_ID_ROLE)
            
            # Add to ignored pairs
            self._ignored_merge_pairs.add((from_id, to_id))
        
        # Refresh the suggestion list
        self._refresh_suggestion_list()
        
    def _refresh_suggestion_list(self):
        """Refresh the suggestion list after merges or ignores"""
        # Create a new list excluding ignored pairs
        filtered_suggestions = []
        
        for row in range(self.suggestion_model.rowCount()):
            from_id = self.suggestion_model.item(row, 0).data(self.FROM_KEYWORD_ID_ROLE)
            to_id = self.suggestion_model.item(row, 1).data(self.TO_KEYWORD_ID_ROLE)
            
            pair = (from_id, to_id)
            if pair not in self._ignored_merge_pairs:
                filtered_suggestions.append({
                    'from_id': from_id,
                    'to_id': to_id,
                    'from_text': self.suggestion_model.item(row, 0).text(),
                    'to_text': self.suggestion_model.item(row, 1).text(),
                    'score': self.suggestion_model.item(row, 2).text(),
                    'kind': self.suggestion_model.item(row, 0).data(self.KEYWORD_KIND_ROLE)
                })
        
        # Update model with filtered list
        self.suggestion_model.clear()
        self.suggestion_model.setHorizontalHeaderLabels(["From", "To", "Score"])
        
        for suggestion in filtered_suggestions:
            from_item = QStandardItem(suggestion['from_text'])
            from_item.setData(suggestion['from_id'], self.FROM_KEYWORD_ID_ROLE)
            
            to_item = QStandardItem(suggestion['to_text'])
            to_item.setData(suggestion['to_id'], self.TO_KEYWORD_ID_ROLE)
            
            score_item = QStandardItem(suggestion['score'])
            
            # Store kind in both items
            from_item.setData(suggestion['kind'], self.KEYWORD_KIND_ROLE)
            to_item.setData(suggestion['kind'], self.KEYWORD_KIND_ROLE)
            
            self.suggestion_model.appendRow([from_item, to_item, score_item])
            
        # Update status
        count = self.suggestion_model.rowCount()
        if count > 0:
            self.merge_status_label.setText(f"{count} similar keyword pairs")
        else:
            self.merge_status_label.setText("No similar keywords found")
            
    @Slot(bool)
    def _handle_suggestion_panel_toggle(self, checked):
        """Handle toggling the suggestion panel"""
        # Resize splitter when panel is toggled
        if checked:
            # Show with reasonable size
            sizes = self.splitter.sizes()
            total = sum(sizes)
            self.splitter.setSizes([int(total * 0.6), int(total * 0.4)])
        else:
            # Hide panel (give all space to left pane)
            self.splitter.setSizes([1, 0])
    
    @Slot()
    def _export_keywords(self):
        """Export keywords to a CSV file"""
        if not self.db or not app_state.current_project_path:
            self.logger.warning("Cannot export: No database or project")
            return
            
        try:
            # Get project ID
            project_id = self.db.get_project_id_by_path(app_state.current_project_path)
            if not project_id:
                self.logger.error("Cannot export: Project not found")
                return
                
            # Get export file path
            project_dir = Path(app_state.current_project_path).parent
            export_path = project_dir / "keyword_export.csv"
            
            # Get all keywords for this project
            topics = self.db.get_all_keywords_by_kind(project_id, 'topic')
            titles = self.db.get_all_keywords_by_kind(project_id, 'title')
            names = self.db.get_all_keywords_by_kind(project_id, 'name')
            
            # Write to CSV
            with open(export_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Type', 'Keyword', 'Usage Count'])
                
                # Write topics
                for topic in topics:
                    writer.writerow(['topic', topic.keyword, topic.usage_count])
                    
                # Write titles
                for title in titles:
                    writer.writerow(['title', title.keyword, title.usage_count])
                    
                # Write names
                for name in names:
                    writer.writerow(['name', name.keyword, name.usage_count])
            
            self.logger.info(f"Exported {len(topics) + len(titles) + len(names)} keywords to {export_path}")
            
            # Show success message
            QMessageBox.information(
                self, 
                "Export Complete", 
                f"Exported {len(topics) + len(titles) + len(names)} keywords to:\n{export_path}"
            )
            
        except DatabaseError as e:
            self.logger.error(f"Database error exporting keywords: {e}", exc_info=True)
            QMessageBox.critical(self, "Database Error", f"Failed to retrieve keywords from database:\n{e}")
        except FileOperationError as e:
            self.logger.error(f"File error exporting keywords: {e}", exc_info=True)
            QMessageBox.critical(self, "File Error", f"Failed to write export file:\n{e}")
        except Exception as e:
            self.logger.error(f"Unexpected error exporting keywords: {e}", exc_info=True)
            QMessageBox.critical(self, "Export Error", f"Failed to export keywords:\n{e}")
