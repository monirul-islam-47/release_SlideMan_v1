# src/slideman/ui/pages/assembly_page.py

import logging
import time
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, 
    QLabel, QFrame, QListView, QPushButton, 
    QLineEdit, QComboBox, QAbstractItemView,
    QSizePolicy, QMenu, QDialog
)
from PySide6.QtCore import Qt, Slot, QSize, QAbstractListModel, QModelIndex, QTimer, Signal, QPoint, QMimeData
from PySide6.QtGui import QPixmap, QStandardItemModel, QStandardItem, QColor, QBrush, QAction, QPainter, QPen
from pathlib import Path
from ...app_state import app_state  # Need access to AppState
from ...services.database import Database  # For type hints
from ...services.thumbnail_cache import thumbnail_cache
from ...models.keyword import Keyword, KeywordKind
from ...models.slide import Slide
from ..widgets.assembly_preview_widget import AssemblyPreviewWidget

logger = logging.getLogger(__name__)


class KeywordListModel(QAbstractListModel):
    """Model for displaying keywords in a list view."""
    KeywordIdRole = Qt.ItemDataRole.UserRole + 1
    KeywordTextRole = Qt.ItemDataRole.UserRole + 2
    KeywordKindRole = Qt.ItemDataRole.UserRole + 3
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._keywords: List[Keyword] = []
        self.logger = logging.getLogger(__name__)
    
    def rowCount(self, parent=QModelIndex()) -> int:
        """Return the number of rows in the model"""
        return len(self._keywords) if not parent.isValid() else 0
    
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return data for the specified role"""
        if not index.isValid() or not (0 <= index.row() < len(self._keywords)):
            return None
            
        keyword = self._keywords[index.row()]
        
        if role == Qt.ItemDataRole.DisplayRole:
            return keyword.keyword
        elif role == Qt.ItemDataRole.ToolTipRole:
            return f"{keyword.keyword} (Kind: {keyword.kind})"
        elif role == self.KeywordIdRole:
            return keyword.id
        elif role == self.KeywordTextRole:
            return keyword.keyword
        elif role == self.KeywordKindRole:
            return keyword.kind
        elif role == Qt.ItemDataRole.BackgroundRole:
            # Different background colors based on keyword kind
            if keyword.kind == 'topic':
                return QBrush(QColor(230, 240, 250))  # Light blue
            elif keyword.kind == 'title':
                return QBrush(QColor(230, 250, 230))  # Light green
            elif keyword.kind == 'name':
                return QBrush(QColor(250, 240, 230))  # Light orange
            
        return None
        
    def setKeywords(self, keywords: List[Keyword]):
        """Replace the current keyword list with a new one"""
        self.beginResetModel()
        self._keywords = keywords.copy()  # Create a copy to avoid external modifications
        self.endResetModel()
        
    def addKeyword(self, keyword: Keyword) -> bool:
        """Add a keyword to the model if it doesn't already exist"""
        # Check if keyword already exists by ID
        if any(kw.id == keyword.id for kw in self._keywords):
            return False
            
        pos = len(self._keywords)
        self.beginInsertRows(QModelIndex(), pos, pos)
        self._keywords.append(keyword)
        self.endInsertRows()
        return True
        
    def removeKeyword(self, index: QModelIndex) -> Optional[Keyword]:
        """Remove a keyword at the specified index and return it"""
        if not index.isValid() or not (0 <= index.row() < len(self._keywords)):
            return None
            
        row = index.row()
        self.beginRemoveRows(QModelIndex(), row, row)
        removed_keyword = self._keywords.pop(row)
        self.endRemoveRows()
        return removed_keyword
        
    def removeKeywordById(self, keyword_id: int) -> Optional[Keyword]:
        """Remove a keyword with the specified ID and return it"""
        for i, keyword in enumerate(self._keywords):
            if keyword.id == keyword_id:
                self.beginRemoveRows(QModelIndex(), i, i)
                removed_keyword = self._keywords.pop(i)
                self.endRemoveRows()
                return removed_keyword
        return None
        
    def clear(self):
        """Clear all keywords from the model"""
        self.beginResetModel()
        self._keywords.clear()
        self.endResetModel()
        
    def keywords(self) -> List[Keyword]:
        """Return a copy of the current keywords"""
        return self._keywords.copy()
        
    def getKeywordById(self, keyword_id: int) -> Optional[Keyword]:
        """Get a keyword by its ID"""
        for keyword in self._keywords:
            if keyword.id == keyword_id:
                return keyword
        return None


class PreviewThumbnailModel(QAbstractListModel):
    SlideIdRole = Qt.ItemDataRole.UserRole + 10
    def __init__(self, slides=None, parent=None):
        super().__init__(parent)
        self._slides = slides or []
    def rowCount(self, parent=QModelIndex()):
        return len(self._slides) if not parent.isValid() else 0
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._slides)):
            return None
        slide = self._slides[index.row()]
        if role == Qt.ItemDataRole.DecorationRole:
            return thumbnail_cache.get_thumbnail(slide.id)
        if role == self.SlideIdRole:
            return slide.id
        if role == Qt.ItemDataRole.ToolTipRole:
            return f"Slide {slide.slide_index}"
        return None
    def setSlides(self, slides):
        self.beginResetModel()
        self._slides = slides.copy()
        self.endResetModel()


class AssemblyPreview(AssemblyPreviewWidget):
    """ListWidget-based assembly preview with drag-drop order persistence."""
    orderChanged = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize KeywordId with None to satisfy the validation check
        self.KeywordId = None
        
    def add_slide(self, slide_id, thumbnail, keywords):
        # Ensure KeywordId is in the keywords dict
        if 'KeywordId' not in keywords:
            keywords['KeywordId'] = None
        return super().add_slide(slide_id, thumbnail, keywords)
        
    def dropEvent(self, event):
        super().dropEvent(event)
        ids = self.get_ordered_slide_indices()
        app_state.set_assembly_order(ids)
        self.orderChanged.emit(ids)
        
    def get_ordered_slides(self):
        """Return all slide items in current order."""
        return [self.item(i) for i in range(self.count())]


class AssemblyManagerPage(QWidget):
    """
    Assembly Manager Page allows users to search for keywords,
    preview slides associated with those keywords, and build a 
    curated list of slides (assembly).
    
    Layout:
    - Left Panel: Keyword Search & Basket
    - Middle Panel: Slide Preview for selected keyword
    - Right Panel: Final Assembly Set
    """
    
    # Custom signals
    basketUpdated = Signal(list)  # Emits list of keyword_ids in basket
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Assembly Manager Page")
        
        # Get database service from AppState
        self.db = app_state.db_service
        if not self.db:
            self.logger.error("Database service not available in AppState!")
            
        # Create custom models for keywords
        self.keyword_results_model = KeywordListModel(self)
        self.keyword_basket_model = KeywordListModel(self)
        
        # Get current project ID for scope filter
        self.current_project_id = None
        # The current project might be stored in the database
        if app_state.current_project_path and self.db:
            # Retrieve the project ID from the database using the path
            project_id = self.db.get_project_id_by_path(app_state.current_project_path)
            if project_id is not None:
                self.current_project_id = project_id
                self.logger.debug(f"Current project ID: {self.current_project_id}")
            
        # Create a timer for debouncing search input
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)  # 300ms debounce delay
        self.search_timer.timeout.connect(self._update_keyword_search_results)
            
        # Main layout is a horizontal layout with three panels
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create a splitter for resizable panels
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === Left Panel: Keyword Search & Basket ===
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        # Search controls section
        search_section = QWidget()
        search_layout = QVBoxLayout(search_section)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add search input
        search_layout.addWidget(QLabel("Search Keywords:"))
        self.keyword_search_input = QLineEdit()
        self.keyword_search_input.setPlaceholderText("Enter keyword to search...")
        self.keyword_search_input.textChanged.connect(self._on_search_text_changed)
        # Connect Enter/Return key press to immediately search
        self.keyword_search_input.returnPressed.connect(self._update_keyword_search_results)
        search_layout.addWidget(self.keyword_search_input)
        
        # Add filter controls
        filters_layout = QHBoxLayout()
        
        # Kind filter
        kind_label = QLabel("Kind:")
        self.kind_filter = QComboBox()
        self.kind_filter.addItem("All", None)  # None means no filter
        self.kind_filter.addItem("Topic", "topic")
        self.kind_filter.addItem("Title", "title")
        self.kind_filter.addItem("Name", "name")
        self.kind_filter.currentIndexChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(kind_label)
        filters_layout.addWidget(self.kind_filter)
        
        # Project scope filter
        scope_label = QLabel("Scope:")
        self.project_scope_filter = QComboBox()
        self.project_scope_filter.addItem("Current Project", True)
        self.project_scope_filter.addItem("All Projects", False)
        self.project_scope_filter.currentIndexChanged.connect(self._on_filter_changed)
        filters_layout.addWidget(scope_label)
        filters_layout.addWidget(self.project_scope_filter)
        
        search_layout.addLayout(filters_layout)
        left_layout.addWidget(search_section)
        
        # Search results section
        left_layout.addWidget(QLabel("Keyword Results:"))
        self.keyword_results_view = QListView()
        self.keyword_results_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        # Set our custom model
        self.keyword_results_view.setModel(self.keyword_results_model)
        self.keyword_results_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.keyword_results_view.customContextMenuRequested.connect(self._show_results_context_menu)
        left_layout.addWidget(self.keyword_results_view)
        
        # Add button to add selected keyword to basket
        self.add_to_basket_button = QPushButton("Add to Basket")
        self.add_to_basket_button.clicked.connect(self._add_selected_keyword_to_basket)
        left_layout.addWidget(self.add_to_basket_button)
        
        # Basket section
        left_layout.addWidget(QLabel("Keyword Basket:"))
        self.keyword_basket_view = QListView()
        # Set our custom model
        self.keyword_basket_view.setModel(self.keyword_basket_model)
        self.keyword_basket_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.keyword_basket_view.customContextMenuRequested.connect(self._show_basket_context_menu)
        left_layout.addWidget(self.keyword_basket_view)
        
        # Add "Clear Basket" button
        self.clear_basket_button = QPushButton("Clear Basket")
        self.clear_basket_button.clicked.connect(self._clear_keyword_basket)
        left_layout.addWidget(self.clear_basket_button)
        
        # === Middle Panel: Slide Preview ===
        self.middle_panel = QWidget()
        middle_layout = QVBoxLayout(self.middle_panel)
        middle_layout.setContentsMargins(10, 10, 10, 10)
        
        self.preview_label = QLabel("Preview for Keyword: [None]")
        middle_layout.addWidget(self.preview_label)
        
        # Slide preview view
        self.slide_preview_view = QListView()
        self.slide_preview_view.setViewMode(QListView.ViewMode.IconMode)
        self.slide_preview_view.setFlow(QListView.Flow.LeftToRight)
        self.slide_preview_view.setWrapping(True)
        self.slide_preview_view.setResizeMode(QListView.ResizeMode.Adjust)
        self.slide_preview_view.setSpacing(5)
        self.slide_preview_view.setIconSize(QSize(160, 120))  # 4:3 aspect ratio
        
        # Initialize real preview model
        self.preview_model = PreviewThumbnailModel([], self)
        self.slide_preview_view.setModel(self.preview_model)
        
        middle_layout.addWidget(self.slide_preview_view)
        
        # Add button to add selected slide to assembly
        self.add_to_assembly_btn = QPushButton("Add Selected to Assembly")
        self.add_to_assembly_btn.clicked.connect(self._handle_add_to_assembly)
        middle_layout.addWidget(self.add_to_assembly_btn)
        
        # === Right Panel: Final Assembly Set ===
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        right_layout.addWidget(QLabel("Final Slide Set:"))
        
        # Final assembly view
        self.final_set_view = AssemblyPreview(self)
        self.final_set_view.setIconSize(QSize(160, 120))
        # Persist reorder via widget signal
        self.final_set_view.orderChanged.connect(self._on_final_order_changed)
        
        right_layout.addWidget(self.final_set_view)
        
        # Add buttons for assembly management
        buttons_layout = QHBoxLayout()
        self.remove_selected_btn = QPushButton("Remove Selected")
        self.clear_assembly_btn = QPushButton("Clear Assembly")
        buttons_layout.addWidget(self.remove_selected_btn)
        buttons_layout.addWidget(self.clear_assembly_btn)
        right_layout.addLayout(buttons_layout)
        
        # Export button
        self.export_assembly_btn = QPushButton("Export Assembly")
        right_layout.addWidget(self.export_assembly_btn)
        
        # Add the panels to the splitter with appropriate sizes
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.middle_panel)
        self.main_splitter.addWidget(self.right_panel)
        
        # Set initial sizes (proportional to the ratios mentioned: 25:35:40)
        self.main_splitter.setSizes([250, 350, 400])
        
        # Add the splitter to the main layout
        main_layout.addWidget(self.main_splitter)
        
        # Connect signals
        self._connect_signals()
        
        self.logger.info("Assembly Manager Page initialized")
        
    def _connect_signals(self):
        """Connect signals for the Assembly Manager Page"""
        # When a keyword is selected in the results view
        self.keyword_results_view.selectionModel().selectionChanged.connect(
            self._handle_keyword_selection_changed
        )
        
        # Double-click on a keyword in results view adds it to the basket
        self.keyword_results_view.doubleClicked.connect(self._add_selected_keyword_to_basket)
        
        # Update slide preview when keyword selection changes
        self.keyword_results_view.selectionModel().selectionChanged.connect(self._update_slide_preview)
        self.keyword_basket_view.selectionModel().selectionChanged.connect(self._update_slide_preview)
        
        # When a slide is selected in the preview (existing placeholder handler)
        self.slide_preview_view.selectionModel().selectionChanged.connect(self._handle_slide_selection_changed)
        
        # Double-click to show enlarged slide
        self.slide_preview_view.doubleClicked.connect(self._show_enlarged_slide)
        
        # When the add to assembly button is clicked
        self.add_to_assembly_btn.clicked.connect(self._handle_add_to_assembly)
        
        # When the remove selected button is clicked
        self.remove_selected_btn.clicked.connect(self._remove_selected_slides)
        
        # When the clear assembly button is clicked
        self.clear_assembly_btn.clicked.connect(self._clear_final_set)
        
        # When the export assembly button is clicked
        self.export_assembly_btn.clicked.connect(self._handle_export_assembly)
        
        # Connect basketUpdated signal to update final set
        app_state.assemblyBasketChanged.connect(self._update_final_set)
        
    # --- Signal handlers for keyword search and basket ---
    
    @Slot()
    def _handle_keyword_selection_changed(self):
        """Handle selection change in keyword results view"""
        # Update preview label with selected keyword
        selected_indexes = self.keyword_results_view.selectionModel().selectedIndexes()
        if not selected_indexes:
            self.preview_label.setText("Preview for Keyword: [None]")
            return
            
        selected_keyword_text = selected_indexes[0].data()
        kind = selected_indexes[0].data(KeywordListModel.KeywordKindRole)
        self.preview_label.setText(f"Preview for Keyword: {selected_keyword_text} (Kind: {kind})")
        
    @Slot(str)
    def _on_search_text_changed(self, text: str):
        """Handle search text changes with debounce"""
        # Restart the timer to debounce input
        self.search_timer.stop()
        self.search_timer.start()
        
    @Slot(int)
    def _on_filter_changed(self, index: int):
        """Handle changes to filter dropdowns"""
        # Immediately update search results when filters change
        self._update_keyword_search_results()
        
    @Slot()
    def _update_keyword_search_results(self):
        """Update the keyword search results based on current filters"""
        if not self.db:
            self.logger.error("Cannot update search results: Database service unavailable")
            return
            
        # Get the search term
        query_term = self.keyword_search_input.text().strip()
        
        # Get the kind filter
        kind = self.kind_filter.currentData()
        
        # Get project scope
        use_project_scope = self.project_scope_filter.currentData()
        project_id = self.current_project_id if use_project_scope else None
        
        try:
            # If query is empty, don't search
            if not query_term:
                self.keyword_results_model.setKeywords([])
                return
                
            # Search for keywords
            keywords = self.db.search_keywords(query_term, kind, project_id)
            
            # Update the model
            self.keyword_results_model.setKeywords(keywords)
            
            self.logger.debug(f"Found {len(keywords)} keywords matching '{query_term}'")
        except Exception as e:
            self.logger.error(f"Error searching keywords: {e}", exc_info=True)
            self.keyword_results_model.setKeywords([])
            
    @Slot()
    def _add_selected_keyword_to_basket(self):
        """Add currently selected keyword to the basket"""
        selected_indexes = self.keyword_results_view.selectionModel().selectedIndexes()
        if not selected_indexes:
            return
            
        # Get the selected keyword
        index = selected_indexes[0]
        keyword_id = index.data(KeywordListModel.KeywordIdRole)
        
        # Check if it's already in the basket
        existing = self.keyword_basket_model.getKeywordById(keyword_id)
        if existing:
            return  # Already in basket
            
        # Get the keyword object from the results model
        keyword = self.keyword_results_model.getKeywordById(keyword_id)
        if keyword:
            # Add to basket model
            self.keyword_basket_model.addKeyword(keyword)
            self._emit_basket_updated()
            
    @Slot(QPoint)
    def _show_results_context_menu(self, pos):
        """Show context menu for keyword results"""
        global_pos = self.keyword_results_view.mapToGlobal(pos)
        menu = QMenu(self)
        
        # Get the item under cursor
        index = self.keyword_results_view.indexAt(pos)
        if index.isValid():
            add_action = menu.addAction("Add to Basket")
            add_action.triggered.connect(self._add_selected_keyword_to_basket)
            
        menu.exec(global_pos)
    @Slot(QPoint)
    def _show_basket_context_menu(self, pos):
        """Show context menu for keyword basket"""
        global_pos = self.keyword_basket_view.mapToGlobal(pos)
        menu = QMenu(self)
        
        # Get the item under cursor
        index = self.keyword_basket_view.indexAt(pos)
        if index.isValid():
            remove_action = menu.addAction("Remove from Basket")
            # Use lambda to capture the index
            remove_action.triggered.connect(
                lambda: self._remove_keyword_from_basket(index)
            )
            
        menu.addSeparator()
        clear_action = menu.addAction("Clear Basket")
        clear_action.triggered.connect(self._clear_keyword_basket)
        
        menu.exec(global_pos)
        
    @Slot(QModelIndex)
    def _remove_keyword_from_basket(self, index: QModelIndex):
        """Remove a keyword from the basket"""
        if not index.isValid():
            return
            
        self.keyword_basket_model.removeKeyword(index)
        self._emit_basket_updated()
        
    @Slot()
    def _clear_keyword_basket(self):
        """Clear all keywords from the basket"""
        self.keyword_basket_model.clear()
        self._emit_basket_updated()
        
    def _emit_basket_updated(self):
        """Update AppState with current basket keywords."""
        keywords = self.keyword_basket_model.keywords()
        keyword_ids = [k.id for k in keywords]
        app_state.set_assembly_basket(keyword_ids)
        self.logger.debug(f"Assembly basket set: {keyword_ids}")
        
    # --- Slide preview slots ---
    
    @Slot()
    def _update_slide_preview(self):
        """Populate slide preview based on selected keyword."""
        # Determine selected keyword index
        sel = self.keyword_results_view.selectionModel().selectedIndexes()
        if sel:
            idx = sel[0]
        else:
            basket_sel = self.keyword_basket_view.selectionModel().selectedIndexes()
            if basket_sel:
                idx = basket_sel[0]
            else:
                self.preview_label.setText("Preview for Keyword: [None]")
                self.preview_model.setSlides([])
                return
        keyword_id = idx.data(KeywordListModel.KeywordIdRole)
        keyword_text = idx.data(KeywordListModel.KeywordTextRole)
        self.preview_label.setText(f"Preview for Keyword: {keyword_text}")
        # Fetch slides
        if self.current_project_id:
            slides = self.db.get_slides_for_keyword(keyword_id, project_id=self.current_project_id)
        else:
            slides = self.db.get_slides_for_keyword(keyword_id)
        self.preview_model.setSlides(slides)
        
    @Slot(QModelIndex)
    def _show_enlarged_slide(self, index: QModelIndex):
        """Show a dialog with an enlarged slide image."""
        slide_id = index.data(self.preview_model.SlideIdRole)
        # Attempt full-res image, fall back to thumbnail if missing
        using_full = True
        image_rel = self.db.get_slide_image_path(slide_id)
        if not image_rel:
            self.logger.warning(f"No full-res image for SlideID {slide_id}, falling back to thumbnail.")
            image_rel = self.db.get_slide_thumbnail_path(slide_id)
            using_full = False
        if not image_rel:
            self.logger.error(f"No image or thumbnail path for SlideID {slide_id}. Cannot enlarge.")
            return
        # Determine project root (AppState or derive via DB)
        proj_path = app_state.current_project_path
        if not proj_path:
            proj_path = self.db.get_project_folder_path_for_slide(slide_id)
            if not proj_path:
                self.logger.error(f"Cannot derive project path for SlideID {slide_id}, cannot show enlarged image.")
                return
        project_root = Path(proj_path)
        # Locate image file (try project-specific then shared)
        standard_path = project_root / image_rel
        shared_path = project_root.parent / image_rel
        if standard_path.exists():
            image_path = standard_path
        elif shared_path.exists():
            image_path = shared_path
        else:
            self.logger.error(f"Image for SlideID {slide_id} not found at {standard_path} or {shared_path}")
            return
        # Load and verify pixmap
        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self.logger.error(f"Failed to load image pixmap from {image_path}")
            return
        # Show enlarged image
        dialog = QDialog(self)
        title = f"Slide {slide_id}" + ("" if using_full else " (preview)")
        dialog.setWindowTitle(title)
        label = QLabel(dialog)
        label.setPixmap(pixmap.scaled(800, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout = QVBoxLayout(dialog)
        layout.addWidget(label)
        dialog.exec()
        
    # --- Placeholder signal handlers for slide preview and assembly ---
    
    @Slot()
    def _handle_slide_selection_changed(self):
        """Handle selection change in slide preview"""
        self.logger.debug("Slide selection changed (placeholder)")
        
    @Slot()
    def _handle_add_to_assembly(self):
        """Handle adding selected slides to the assembly"""
        self.logger.debug("Adding selected slides to assembly")
        selected = self.slide_preview_view.selectionModel().selectedIndexes()
        if not selected:
            self.logger.debug("No slides selected")
            return
            
        try:
            # Track new slides to log
            added_ids = []
            for idx in selected:
                slide_id = idx.data(PreviewThumbnailModel.SlideIdRole)
                # Get thumbnail
                pix = thumbnail_cache.get_thumbnail(slide_id)
                # Use an empty dictionary - let the widget handle defaults
                result = self.final_set_view.add_slide(slide_id, pix, {})
                if result:
                    added_ids.append(slide_id)
                    
            # Persist updated order of slide IDs
            ids = self.final_set_view.get_ordered_slide_indices()
            app_state.set_assembly_order(ids)
            self.logger.debug(f"Added slides {added_ids} to assembly. Full order: {ids}")
        except Exception as e:
            self.logger.error(f"Error adding slides to assembly: {e}", exc_info=True)
        
    @Slot()
    def _handle_remove_selected(self):
        """Handle removing selected slides from the assembly"""
        self.logger.debug("Remove selected clicked (placeholder)")
        
    @Slot()
    def _handle_clear_assembly(self):
        """Handle clearing the assembly"""
        self.logger.debug("Clear assembly clicked (placeholder)")
        
    @Slot()
    def _handle_export_assembly(self):
        """Handle exporting the assembly"""
        self.logger.debug("Export assembly clicked, persisting order to AppState")
        # Persist current assembly slide order to AppState
        # Get the slide IDs from the item data
        ids = [item.data(Qt.ItemDataRole.UserRole) for item in self.final_set_view.get_ordered_slides()]
        app_state.set_assembly_order(ids)
        
    @Slot(list)
    def _update_final_set(self, keyword_ids: list):
        """Populate final set based on current basket keywords."""
        self.logger.debug(f"Updating final set with keyword IDs: {keyword_ids}")
        try:
            # Clear and rebuild full set
            self.final_set_view.clear()
            
            if not keyword_ids:
                # No keywords: persist empty order
                app_state.set_assembly_order([])
                self.logger.debug("No keywords, cleared assembly")
                return
                
            # Aggregate unique slides
            slides_map: Dict[int, Slide] = {}
            for kid in keyword_ids:
                try:
                    slides = (self.db.get_slides_for_keyword(kid, project_id=self.current_project_id)
                            if self.current_project_id else self.db.get_slides_for_keyword(kid))
                    for s in slides:
                        slides_map[s.id] = s
                except Exception as e:
                    self.logger.warning(f"Error getting slides for keyword ID {kid}: {e}")
            
            self.logger.debug(f"Found {len(slides_map)} unique slides for {len(keyword_ids)} keywords")
            
            # Add each slide to assembly view
            added_count = 0
            for slide in slides_map.values():
                try:
                    pix = thumbnail_cache.get_thumbnail(slide.id)
                    # Use an empty dictionary - let the widget handle defaults
                    result = self.final_set_view.add_slide(slide.id, pix, {})
                    if result:
                        added_count += 1
                except Exception as e:
                    self.logger.warning(f"Error adding slide ID {slide.id} to assembly: {e}")
            
            # Persist new order of IDs
            ids = self.final_set_view.get_ordered_slide_indices()
            app_state.set_assembly_order(ids)
            self.logger.debug(f"Added {added_count} slides to assembly. Final order: {ids}")
            
        except Exception as e:
            self.logger.error(f"Error updating final set: {e}", exc_info=True)

    @Slot()
    def _remove_selected_slides(self):
        """Remove selected slides from the final set."""
        self.final_set_view.remove_selected_slides()
        ids = self.final_set_view.get_ordered_slide_indices()
        app_state.set_assembly_order(ids)
                
    @Slot()
    def _clear_final_set(self):
        """Clear all slides from the final set."""
        self.final_set_view.clear()
        app_state.set_assembly_order([])
        
    @Slot()
    def _on_final_order_changed(self):
        """Handle internal drag-and-drop reorder by persisting order."""
        ids = self.final_set_view.get_ordered_slide_indices()
        app_state.set_assembly_order(ids)
