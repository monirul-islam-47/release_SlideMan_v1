# src/slideman/ui/pages/slideview_page.py

import logging
from typing import Optional, List, Dict
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
                             QLabel, QFrame, QListView, QAbstractItemView, QMessageBox,
                             QComboBox, QToolBar, QSizePolicy)
from PySide6.QtCore import Qt, Slot, QAbstractListModel, QObject, QModelIndex, QSize
from PySide6.QtGui import QPixmap, QAction, QStandardItemModel, QStandardItem
from typing import Any
from pathlib import Path
# Import other dependencies later as needed
from ..components.slide_canvas import SlideCanvas
from ..components.tag_edit import TagEdit
# from ..components.thumbnail_bar import ThumbnailBar # Or implement directly here
# from ..components.keyword_panel import KeywordPanel # Or implement directly here

from ...models.slide import Slide # Need Slide model for type hints
from ...models.file import File # Need File model for type hints
from ...models.element import Element # Need Element model for element overlays
from ...services.thumbnail_cache import thumbnail_cache # Import singleton cache instance
from ...services.exceptions import (
    DatabaseError, ResourceNotFoundError, ValidationError,
    FileNotFoundError as SlidemanFileNotFoundError
)
from ...app_state import app_state # Need access to AppState
from ...commands.manage_slide_keyword import LinkSlideKeywordCmd, UnlinkSlideKeywordCmd
from ...commands.manage_element_keyword import LinkElementKeywordCmd, UnlinkElementKeywordCmd

logger = logging.getLogger(__name__)

class SlideThumbnailModel(QAbstractListModel):
    """
    Model for providing slide thumbnails to the QListView.
    Uses ThumbnailCache service for efficient loading.
    """
    SlideIdRole = Qt.UserRole + 1 # Role to retrieve the database slide ID
    
    # FIX: Define a consistent thumbnail size
    THUMBNAIL_SIZE = QSize(160, 120)  # 4:3 aspect ratio

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._slides: List[Slide] = [] # Store Slide objects (or just IDs/paths)
        self.logger = logging.getLogger(__name__)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._slides) if not parent.isValid() else 0

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Gets data for the thumbnail view."""
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None

        slide = self._slides[index.row()]
        slide_id = slide.id # Assuming slide object has an ID

        if role == Qt.ItemDataRole.DecorationRole: # We want the image itself
            if slide_id is None:
                 self.logger.warning("Slide object has no ID, cannot fetch thumbnail.")
                 return None # Or return placeholder?
            # Fetch from cache service
            pixmap = thumbnail_cache.get_thumbnail(slide_id)
            if pixmap:
                 # FIX: Ensure proper scaling of the pixmap to our desired size
                 return pixmap.scaled(self.THUMBNAIL_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            else:
                 # Return placeholder if cache fails
                 self.logger.warning(f"Thumbnail not found in cache or disk for SlideID: {slide_id}")
                 # Create a placeholder QPixmap
                 placeholder = QPixmap(self.THUMBNAIL_SIZE)
                 placeholder.fill(Qt.GlobalColor.lightGray)
                 return placeholder
        elif role == Qt.ItemDataRole.DisplayRole: # Text below thumb? Maybe slide number?
            # Add file name or indicator to distinguish between files
            file_id = slide.file_id
            return f"File {file_id}-{slide.slide_index}" # Display file ID and slide index
        elif role == self.SlideIdRole:
            return slide_id # Return the database ID for this item
        elif role == Qt.ItemDataRole.ToolTipRole:
            # Add more detailed tooltip
            return f"File ID: {slide.file_id}, Slide {slide.slide_index}"

        return None

    def sizeHint(self, index: QModelIndex, option=None) -> QSize:
        """Provide size hint for items to ensure proper display"""
        # FIX: Add size hint method for better item sizing
        return QSize(170, 150)  # Slightly larger than thumbnail to accommodate text

    def load_slides(self, slides: List[Slide]):
        """Updates the model with slide data for the current project."""
        self.logger.info(f"Loading {len(slides)} slide thumbnails into model")
        self.beginResetModel()
        # Sort slides by their index within the file (assuming list might not be sorted)
        # TODO: Handle multiple files later - requires grouping/sorting differently
        self._slides = sorted(slides, key=lambda s: s.slide_index)
        self.endResetModel()
        self.logger.debug("Thumbnail model reset.")

    def get_slide(self, index: QModelIndex) -> Optional[Slide]:
        """Helper to get Slide object from index."""
        if index.isValid() and 0 <= index.row() < self.rowCount():
             return self._slides[index.row()]
        return None


class SlideViewPage(QWidget):
    """
    Page for viewing individual slides, thumbnails, and managing keywords.
    """
    def __init__(self, db_service, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing SlideView Page")
        
        # Use the provided database service
        self.db = db_service
        if not self.db:
            self.logger.error("Database service not provided!")

        # Initialize instance variables
        self._current_project_id = None
        self._project_files = []
        self._all_slides = []
        self._current_slide_elements = []  # Store elements for the current slide

        # --- Main Layout (Horizontal) ---
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Splitter to divide Left and Right ---
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Left Pane Widget (Canvas + Thumbs) ---
        self.left_pane_widget = QWidget()
        left_pane_layout = QVBoxLayout(self.left_pane_widget)
        left_pane_layout.setContentsMargins(5, 5, 5, 5)
        left_pane_layout.setSpacing(5)
        
        # --- File Filter Toolbar ---
        filter_toolbar = QToolBar("File Filter")
        filter_toolbar.setMovable(False)
        filter_toolbar.setFloatable(False)
        
        # Add file filter label
        filter_label = QLabel("File Filter:")
        filter_toolbar.addWidget(filter_label)
        
        # Add file filter combobox
        self.file_filter_combo = QComboBox()
        self.file_filter_combo.setMinimumWidth(150)
        self.file_filter_combo.addItem("All Files", -1)  # -1 means all files
        self.file_filter_combo.currentIndexChanged.connect(self._handle_file_filter_changed)
        filter_toolbar.addWidget(self.file_filter_combo)
        
        # Add spacer to push everything to the left
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        filter_toolbar.addWidget(spacer)
        
        left_pane_layout.addWidget(filter_toolbar)

        # Replace placeholder with actual SlideCanvas
        self.slide_canvas = SlideCanvas(self)
        size_policy_canvas = self.slide_canvas.sizePolicy()
        size_policy_canvas.setVerticalStretch(1)
        self.slide_canvas.setSizePolicy(size_policy_canvas)
        self.slide_canvas.setMinimumSize(200, 200)
        left_pane_layout.addWidget(self.slide_canvas)
        
        # Connect the elementSelected signal to our handler
        self.slide_canvas.elementSelected.connect(self.handle_element_selected)

        # --- Thumbnail Bar (Real QListView) ---
        self.thumbnail_list_view = QListView()
        self.thumbnail_list_view.setViewMode(QListView.ViewMode.IconMode)
        self.thumbnail_list_view.setFlow(QListView.Flow.LeftToRight)
        self.thumbnail_list_view.setResizeMode(QListView.ResizeMode.Adjust)
        self.thumbnail_list_view.setWrapping(False)
        
        # FIX: Increase the height to display thumbnails properly
        self.thumbnail_list_view.setMinimumHeight(150)  # Increased from 130
        self.thumbnail_list_view.setFixedHeight(180)    # Increased to show full thumbnails
        
        self.thumbnail_list_view.setSpacing(5)
        self.thumbnail_list_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Add a nice visible border for selected items
        self.thumbnail_list_view.setStyleSheet("""
            QListView::item:selected {
                border: 3px solid #3584e4;
                background-color: rgba(53, 132, 228, 0.2);
            }
        """)
        
        # Set more appropriate icon size
        self.thumbnail_list_view.setIconSize(QSize(160, 120))  # 4:3 aspect ratio, slightly larger

        # Create and set the thumbnail model
        self.thumbnail_model = SlideThumbnailModel(self) # Assumes SlideThumbnailModel class is defined above
        self.thumbnail_list_view.setModel(self.thumbnail_model)

        # Connect click signal
        self.thumbnail_list_view.clicked.connect(self.handle_thumbnail_selected) # Assumes slot exists

        left_pane_layout.addWidget(self.thumbnail_list_view) # Add the real list view
        # ---------------------------------------

        # --- Right Pane (Keywords Panel) ---
        self.right_pane_widget = QWidget()
        self.right_pane_layout = QVBoxLayout(self.right_pane_widget)
        self.right_pane_layout.setContentsMargins(10, 10, 10, 10)
        self.right_pane_layout.setSpacing(10)

        # --- Slide Keywords Section ---
        self.slide_keywords_label = QLabel("<b>Slide Keywords</b>")
        self.slide_keywords_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.right_pane_layout.addWidget(self.slide_keywords_label)
        
        # Topic Tags
        topic_layout = QVBoxLayout()
        topic_label = QLabel("Topic(s):")
        self.topic_tag_edit = TagEdit(placeholder_text="Add topic tag...")
        topic_layout.addWidget(topic_label)
        topic_layout.addWidget(self.topic_tag_edit)
        self.right_pane_layout.addLayout(topic_layout)
        
        # Title Tags
        title_layout = QVBoxLayout()
        title_label = QLabel("Title(s):")
        self.title_tag_edit = TagEdit(placeholder_text="Add title tag...")
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_tag_edit)
        self.right_pane_layout.addLayout(title_layout)
        
        # Add a spacer between sections
        self.right_pane_layout.addSpacing(20)
        
        # --- Element Keywords Section ---
        self.element_keywords_label = QLabel("<b>Element Keywords</b>")
        self.element_keywords_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.right_pane_layout.addWidget(self.element_keywords_label)
        
        # Selected Element Info
        self.selected_element_label = QLabel("Selected Element: None")
        self.right_pane_layout.addWidget(self.selected_element_label)
        
        # Name Tags
        name_layout = QVBoxLayout()
        name_label = QLabel("Name Tag(s):")
        self.name_tag_edit = TagEdit(placeholder_text="Add name tag...")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_tag_edit)
        self.right_pane_layout.addLayout(name_layout)
        
        # Tagged Elements List
        tagged_elements_label = QLabel("Tagged Elements:")
        self.right_pane_layout.addWidget(tagged_elements_label)
        
        self.tagged_elements_list = QListView()
        self.tagged_elements_list.setMaximumHeight(100)  # Limit height to keep UI compact
        self.tagged_elements_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        self.tagged_elements_model = QStandardItemModel()
        self.tagged_elements_list.setModel(self.tagged_elements_model)
        self.tagged_elements_list.clicked.connect(self._handle_tagged_element_selected)
        self.right_pane_layout.addWidget(self.tagged_elements_list)
        
        # Set the element section as always visible but indicate no selection
        # Instead of hiding it completely:
        # self.element_keywords_label.setVisible(False)
        # self.selected_element_label.setVisible(False)
        # self.name_tag_edit.setVisible(False)
        # name_label.setVisible(False)
        
        # Push everything to the top
        self.right_pane_layout.addStretch(1)
        
        # --- Add both panes to the splitter ---
        self.splitter.addWidget(self.left_pane_widget)
        self.splitter.addWidget(self.right_pane_widget)
        
        # Set default sizes (approx 70% left, 30% right)
        self.splitter.setSizes([700, 300])
        
        # Add splitter to main layout
        main_layout.addWidget(self.splitter)

        # --- Connect to AppState signals ---
        # Need 'app_state' imported from ...app_state
        app_state.projectLoaded.connect(self._load_data_for_current_project)
        app_state.projectClosed.connect(self._clear_view)
        # -----------------------------------

        # --- Load initial data if project already loaded ---
        if app_state.current_project_path:
             self._load_data_for_current_project(app_state.current_project_path)
        # -------------------------------------------------
        
        # --- Connect TagEdit signals to handlers ---
        self.topic_tag_edit.tagAdded.connect(self._handle_topic_tag_added)
        self.topic_tag_edit.tagRemoved.connect(self._handle_topic_tag_removed)
        
        self.title_tag_edit.tagAdded.connect(self._handle_title_tag_added)
        self.title_tag_edit.tagRemoved.connect(self._handle_title_tag_removed)
        
        self.name_tag_edit.tagAdded.connect(self._handle_name_tag_added)
        self.name_tag_edit.tagRemoved.connect(self._handle_name_tag_removed)
        # -----------------------------------

        self.logger.debug("SlideView Page UI __init__ finished.")

    @Slot(str) # Receives project_folder_path from AppState signal
    def _load_data_for_current_project(self, project_folder_path: str):
        """Load slide data for the current project."""
        self.logger.info(f"Loading data for project: {project_folder_path}")
        
        if not self.db:
            self.logger.error("Database service not available")
            QMessageBox.critical(self, "Error", "Database service is not available")
            return
            
        try:
            # 1. Get project from DB
            project = self.db.get_project_by_path(project_folder_path)
            if not project:
                raise ResourceNotFoundError("Project", project_folder_path)
                
            self._current_project_id = project.id
            self.logger.debug(f"Found project ID: {project.id}, name: {project.name}")
            
            # 2. Get files for this project
            files = self.db.get_files_for_project(project.id)
            if not files:
                self.logger.warning(f"No files found for project ID: {project.id}")
                self.thumbnail_model.load_slides([])
                return
                
        except ResourceNotFoundError as e:
            self.logger.error(f"Project not found: {e}", exc_info=True)
            QMessageBox.warning(self, "Project Not Found", f"The project at '{project_folder_path}' was not found in the database.")
            self.thumbnail_model.load_slides([])
            return
        except DatabaseError as e:
            self.logger.error(f"Database error loading project data: {e}", exc_info=True)
            QMessageBox.critical(self, "Database Error", f"Failed to load project data:\n{e}")
            self.thumbnail_model.load_slides([])
            return
            
        self.logger.debug(f"Found {len(files)} files for project")
        
        # Store all files for the project
        self._project_files = files
        
        # 3. Update file filter dropdown
        self._update_file_filter(files)
        
        # 4. Load slides from all files
        all_slides = []
        
        for file_obj in files:
            # Get slides for each file
            file_id = file_obj.id
            self.logger.debug(f"Getting slides for file ID: {file_id}")
            try:
                slides_for_file = self.db.get_slides_for_file(file_id)
                
                if slides_for_file:
                    self.logger.debug(f"Found {len(slides_for_file)} slides for file {file_id}")
                    # For debugging, show first slide's path
                    if slides_for_file:
                        first_slide = slides_for_file[0]
                        self.logger.debug(f"Slide {first_slide.id}: thumb_path={first_slide.thumb_rel_path}")
                    
                    # Add these slides to the combined list
                    all_slides.extend(slides_for_file)
                else:
                    self.logger.warning(f"No slides found for file ID: {file_id}")
            except DatabaseError as e:
                self.logger.error(f"Database error loading slides for file ID {file_id}: {e}", exc_info=True)
                # Continue loading other files
                continue
        
        # Store all slides for later filtering
        self._all_slides = all_slides
        
        # 5. Add all slides to model
        self.logger.info(f"Found {len(all_slides)} slides in DB for project '{project.name}'")
        self.thumbnail_model.load_slides(all_slides)
        
        # 6. Update keyword suggestions for all TagEdit components
        self._update_keyword_suggestions()
        
        # Auto-select the first thumbnail if any slides are loaded
        if self.thumbnail_model.rowCount() > 0:
            first_index = self.thumbnail_model.index(0, 0)
            self.thumbnail_list_view.setCurrentIndex(first_index)
            self.handle_thumbnail_selected(first_index)
            self.logger.debug("Auto-selected first thumbnail")

    def _update_file_filter(self, files: List[File]):
        """Update the file filter dropdown with the current project's files."""
        # Clear existing items except 'All Files'
        while self.file_filter_combo.count() > 1:
            self.file_filter_combo.removeItem(1)
            
        # Disconnect signal temporarily to avoid triggering filter changes
        try:
            self.file_filter_combo.currentIndexChanged.disconnect()
        except:
            pass
            
        # Add files to the dropdown
        for file_obj in files:
            if file_obj.id is not None:
                # Use filename as display text and file_id as data
                display_name = f"{file_obj.filename}" if file_obj.filename else f"File {file_obj.id}"
                self.file_filter_combo.addItem(display_name, file_obj.id)
                
        # Reconnect the signal
        self.file_filter_combo.currentIndexChanged.connect(self._handle_file_filter_changed)
        
        # Set to "All Files" by default
        self.file_filter_combo.setCurrentIndex(0)
        
        # Show/hide the filter based on number of files
        if len(files) <= 1:
            self.file_filter_combo.parent().setVisible(False)  # Hide the toolbar if only one file
        else:
            self.file_filter_combo.parent().setVisible(True)   # Show the toolbar if multiple files

    @Slot(int)
    def _handle_file_filter_changed(self, index: int):
        """Slot called when the file filter combobox selection changes."""
        file_id = self.file_filter_combo.itemData(index)
        if file_id == -1:  # All files
            self.thumbnail_model.load_slides(self._all_slides)
        else:
            # Filter slides by file ID
            filtered_slides = [slide for slide in self._all_slides if slide.file_id == file_id]
            self.thumbnail_model.load_slides(filtered_slides)
        
        # Auto-select the first thumbnail if any slides are loaded
        if self.thumbnail_model.rowCount() > 0:
            first_index = self.thumbnail_model.index(0, 0)
            self.thumbnail_list_view.setCurrentIndex(first_index)
            self.handle_thumbnail_selected(first_index)
            self.logger.debug("Auto-selected first thumbnail")

    @Slot()
    def _clear_view(self):
        """Clears the slide view when no project is open."""
        self.thumbnail_model.load_slides([])  # Clear the thumbnails
        # Clear the slide canvas if it exists
        self.slide_canvas.clear()
        
        # Clear the keyword panels
        self.topic_tag_edit.clear()
        self.title_tag_edit.clear()
        self.name_tag_edit.clear()
        
        # Reset element selection state
        self.selected_element_label.setText("Selected Element: None")
        self.name_tag_edit.clear()
        app_state.current_element_id = None

    @Slot(QModelIndex)
    def handle_thumbnail_selected(self, index: QModelIndex):
        """Handles a thumbnail being selected from the list view."""
        if not index.isValid():
            return
            
        # Get the slide from the model
        slide = self.thumbnail_model.get_slide(index)
        if not slide or not slide.id:
            self.logger.warning("Invalid slide or slide ID from selection.")
            return
            
        # Log the selection
        self.logger.info(f"Selected slide: ID={slide.id}, File={slide.file_id}, Index={slide.slide_index}")
        
        # Update app state with selected slide ID
        app_state.current_slide_id = slide.id
        
        # Clear the keyword panels for the new slide
        self.topic_tag_edit.clear()
        self.title_tag_edit.clear()
        
        # Reset element selection state, but leave the section visible
        self.selected_element_label.setText("Selected Element: None")
        self.name_tag_edit.clear()
        app_state.current_element_id = None
        
        try:
            # Get the image path using the database service
            image_rel_path = self.db.get_slide_image_path(slide.id)
            if not image_rel_path:
                self.logger.warning(f"No image path found for slide ID {slide.id}")
                return
                
            # Construct full path from project path and relative path
            project_path = Path(app_state.current_project_path) if app_state.current_project_path else None
            if not project_path:
                self.logger.error("No project path available in AppState")
                return
                
            # Fetch elements for this slide
            elements = self.db.get_elements_for_slide(slide.id)
            self.logger.debug(f"Fetched {len(elements)} elements for slide {slide.id}")
            self._current_slide_elements = elements  # Store elements for later reference
            
        except ResourceNotFoundError as e:
            self.logger.error(f"Slide not found: {e}", exc_info=True)
            QMessageBox.warning(self, "Slide Not Found", f"The selected slide (ID: {slide.id}) was not found in the database.")
            return
        except DatabaseError as e:
            self.logger.error(f"Database error loading slide data: {e}", exc_info=True)
            QMessageBox.critical(self, "Database Error", f"Failed to load slide data:\n{e}")
            return
        
        # Load keywords for this slide
        self._load_keywords_for_slide(slide.id)
        
        # Update tagged elements list
        self._update_tagged_elements_list(slide.id)
            
        # Check both standard and shared locations (similar to thumbnail_cache logic)
        standard_image_path = project_path / image_rel_path
        projects_root = project_path.parent
        shared_image_path = projects_root / image_rel_path
        
        # Try both locations
        if shared_image_path.exists():
            self.logger.info(f"Loading slide image from shared location: {shared_image_path}")
            self.slide_canvas.load_slide(slide.id, shared_image_path, elements)
        elif standard_image_path.exists():
            self.logger.info(f"Loading slide image from standard location: {standard_image_path}")
            self.slide_canvas.load_slide(slide.id, standard_image_path, elements)
        else:
            self.logger.warning(f"Slide image not found at any location: {image_rel_path}")
        
        # Emit the slideSelected signal
        app_state.slideSelected.emit(slide.id)

    @Slot(int)
    def handle_element_selected(self, element_id: int):
        """
        Handles an element being selected or deselected in the slide canvas.
        
        Args:
            element_id: Database ID of the selected element, or -1 if deselected
        """
        # Update AppState with selected element
        app_state.current_element_id = element_id if element_id >= 0 else None
        
        if element_id < 0:
            self.logger.info("Element deselected")
            # Update label but keep section visible
            self.selected_element_label.setText("Selected Element: None")
            self.name_tag_edit.clear()
        else:
            self.logger.info(f"Element selected: ID={element_id}")
            # Update label with element info
            self.selected_element_label.setText(f"Selected Element: ID {element_id}")
            
            # Load element keywords
            self._load_keywords_for_element(element_id)
        
        # Emit the elementSelected signal
        app_state.elementSelected.emit(element_id)

    # --- Keyword management methods ---
    
    def _update_keyword_suggestions(self):
        """Update keyword suggestions for all TagEdit components."""
        if not self.db:
            self.logger.error("Cannot update keyword suggestions: Database service not available")
            return
            
        try:
            # Get all existing keywords
            all_keywords = self.db.get_all_keyword_strings()
            self.logger.debug(f"Loaded {len(all_keywords)} keywords for suggestions")
            
            # Get topic and title keywords specifically
            topic_keywords = self.db.get_all_keyword_strings(kind='topic')
            title_keywords = self.db.get_all_keyword_strings(kind='title')
            name_keywords = self.db.get_all_keyword_strings(kind='name')
        except DatabaseError as e:
            self.logger.error(f"Database error loading keyword suggestions: {e}", exc_info=True)
            # Continue with empty suggestions rather than crashing
            all_keywords = []
            topic_keywords = []
            title_keywords = []
            name_keywords = []
        
        # Update suggestions for each TagEdit
        self.topic_tag_edit.update_suggestions(topic_keywords)
        self.title_tag_edit.update_suggestions(title_keywords)
        self.name_tag_edit.update_suggestions(name_keywords)
    
    def _load_keywords_for_slide(self, slide_id: int):
        """Load keywords for a slide and update the TagEdit widgets."""
        if not self.db:
            self.logger.error("Cannot load keywords: Database service not available")
            return
            
        try:
            # Get topic keywords
            topic_keywords = self.db.get_keywords_for_slide(slide_id, kind='topic')
            topic_texts = [kw.keyword for kw in topic_keywords]  
            self.logger.debug(f"Loaded {len(topic_texts)} topic keywords for slide ID {slide_id}")
            
            # Get title keywords
            title_keywords = self.db.get_keywords_for_slide(slide_id, kind='title')
            title_texts = [kw.keyword for kw in title_keywords]  
            self.logger.debug(f"Loaded {len(title_texts)} title keywords for slide ID {slide_id}")
            
            # Set the keywords in the TagEdit widgets
            self.topic_tag_edit.set_tags(topic_texts)
            self.title_tag_edit.set_tags(title_texts)
            
        except DatabaseError as e:
            self.logger.error(f"Database error loading keywords for slide {slide_id}: {e}", exc_info=True)
            QMessageBox.warning(self, "Database Error", f"Failed to load keywords for the slide.")
    
    def _load_keywords_for_element(self, element_id: int):
        """Load keywords for an element and update the TagEdit widget."""
        if not self.db:
            self.logger.error("Cannot load keywords: Database service not available")
            return
            
        try:
            # Get name keywords
            element_keywords = self.db.get_keywords_for_element(element_id)
            name_texts = [kw.keyword for kw in element_keywords]
        except DatabaseError as e:
            self.logger.error(f"Database error loading keywords for element {element_id}: {e}", exc_info=True)
            name_texts = []  
        self.logger.debug(f"Loaded {len(name_texts)} name keywords for element ID {element_id}")
        
        # Set the keywords in the TagEdit widget
        self.name_tag_edit.set_tags(name_texts)
    
    # --- TagEdit signal handlers ---
    
    @Slot(str)
    def _handle_topic_tag_added(self, tag_text: str):
        """Handle a topic tag being added to a slide."""
        if not app_state.current_slide_id:
            self.logger.warning("Cannot add topic tag: No slide selected")
            return
            
        slide_id = app_state.current_slide_id
        
        try:
            # Add the keyword to the database if it doesn't exist
            keyword_id = self.db.add_keyword_if_not_exists(tag_text, 'topic')
            if keyword_id is None:
                self.logger.error(f"Failed to add topic keyword '{tag_text}'")
                return
                
            # Create and execute command
            cmd = LinkSlideKeywordCmd(slide_id, keyword_id, f"Add topic '{tag_text}'")
            app_state.undo_stack.push(cmd)
            self.logger.debug(f"Added topic '{tag_text}' to slide ID {slide_id}")
            
            # Update suggestions
            self._update_keyword_suggestions()
            
        except DatabaseError as e:
            self.logger.error(f"Database error adding topic tag '{tag_text}': {e}", exc_info=True)
            QMessageBox.critical(self, "Database Error", f"Failed to add topic tag:\n{e}")
            # Reload tags to reflect actual state
            self._load_keywords_for_slide(slide_id)
    
    @Slot(str)
    def _handle_topic_tag_removed(self, tag_text: str):
        """Handle a topic tag being removed from a slide."""
        if not app_state.current_slide_id:
            self.logger.warning("Cannot remove topic tag: No slide selected")
            return
            
        slide_id = app_state.current_slide_id
        
        try:
            # Get the keyword ID
            keyword_id = self.db.get_keyword_id(tag_text, 'topic')
            if keyword_id is None:
                self.logger.error(f"Cannot find topic keyword '{tag_text}'")
                return
                
            # Create and execute command
            cmd = UnlinkSlideKeywordCmd(slide_id, keyword_id, f"Remove topic '{tag_text}'")
            app_state.undo_stack.push(cmd)
            self.logger.debug(f"Removed topic '{tag_text}' from slide ID {slide_id}")
            
        except DatabaseError as e:
            self.logger.error(f"Database error removing topic tag '{tag_text}': {e}", exc_info=True)
            QMessageBox.critical(self, "Database Error", f"Failed to remove topic tag:\n{e}")
            # Reload tags to reflect actual state
            self._load_keywords_for_slide(slide_id)
    
    @Slot(str)
    def _handle_title_tag_added(self, tag_text: str):
        """Handle a title tag being added to a slide."""
        if not app_state.current_slide_id:
            self.logger.warning("Cannot add title tag: No slide selected")
            return
            
        slide_id = app_state.current_slide_id
        
        # Add the keyword to the database if it doesn't exist
        keyword_id = self.db.add_keyword_if_not_exists(tag_text, 'title')
        if keyword_id is None:
            self.logger.error(f"Failed to add title keyword '{tag_text}'")
            return
            
        # Create and execute command
        cmd = LinkSlideKeywordCmd(slide_id, keyword_id, f"Add title '{tag_text}'")
        app_state.undo_stack.push(cmd)
        self.logger.debug(f"Added title '{tag_text}' to slide ID {slide_id}")
        
        # Update suggestions
        self._update_keyword_suggestions()
    
    @Slot(str)
    def _handle_title_tag_removed(self, tag_text: str):
        """Handle a title tag being removed from a slide."""
        if not app_state.current_slide_id:
            self.logger.warning("Cannot remove title tag: No slide selected")
            return
            
        slide_id = app_state.current_slide_id
        
        # Get the keyword ID
        keyword_id = self.db.get_keyword_id(tag_text, 'title')
        if keyword_id is None:
            self.logger.error(f"Cannot find title keyword '{tag_text}'")
            return
            
        # Create and execute command
        cmd = UnlinkSlideKeywordCmd(slide_id, keyword_id, f"Remove title '{tag_text}'")
        app_state.undo_stack.push(cmd)
        self.logger.debug(f"Removed title '{tag_text}' from slide ID {slide_id}")
    
    @Slot(str)
    def _handle_name_tag_added(self, tag_text: str):
        """Handle a name tag being added to an element."""
        if not app_state.current_element_id:
            self.logger.warning("Cannot add name tag: No element selected")
            # Show warning message to user
            QMessageBox.warning(self, "No Element Selected", 
                               "Please select an element on the slide first to add a name tag.")
            # Remove the tag that was just added since it can't be saved
            self.name_tag_edit.remove_tag(tag_text, emit_signal=False)
            return
            
        element_id = app_state.current_element_id
        
        # Add the keyword to the database if it doesn't exist
        keyword_id = self.db.add_keyword_if_not_exists(tag_text, 'name')
        if keyword_id is None:
            self.logger.error(f"Failed to add name keyword '{tag_text}'")
            return
            
        # Create and execute command
        cmd = LinkElementKeywordCmd(element_id, keyword_id, f"Add name '{tag_text}'")
        app_state.undo_stack.push(cmd)
        self.logger.debug(f"Added name '{tag_text}' to element ID {element_id}")
        
        # Update suggestions and the tagged elements list
        self._update_keyword_suggestions()
        if app_state.current_slide_id:
            self._update_tagged_elements_list(app_state.current_slide_id)
    
    @Slot(str)
    def _handle_name_tag_removed(self, tag_text: str):
        """Handle a name tag being removed from an element."""
        if not app_state.current_element_id:
            self.logger.warning("Cannot remove name tag: No element selected")
            # Show warning message to user
            QMessageBox.warning(self, "No Element Selected", 
                               "Please select an element on the slide first to remove a name tag.")
            # Add the tag back that was just removed since it can't be processed
            self.name_tag_edit.add_tag(tag_text, emit_signal=False)
            return
            
        element_id = app_state.current_element_id
        
        # Get the keyword ID
        keyword_id = self.db.get_keyword_id(tag_text, 'name')
        if keyword_id is None:
            self.logger.error(f"Cannot find name keyword '{tag_text}'")
            return
            
        # Create and execute command
        cmd = UnlinkElementKeywordCmd(element_id, keyword_id, f"Remove name '{tag_text}'")
        app_state.undo_stack.push(cmd)
        self.logger.debug(f"Removed name '{tag_text}' from element ID {element_id}")
        
        # Update the tagged elements list
        if app_state.current_slide_id:
            self._update_tagged_elements_list(app_state.current_slide_id)
            
    def _update_tagged_elements_list(self, slide_id: int):
        """
        Update the list of elements with tags.
        
        Args:
            slide_id: The ID of the current slide
        """
        self.tagged_elements_model.clear()
        
        # For each element in the current slide, check if it has tags
        for element in self._current_slide_elements:
            try:
                keywords = self.db.get_keywords_for_element(element.id)
                if keywords:
                    # Format element type and first few keywords
                    element_type = element.element_type
                    keyword_preview = ", ".join([kw.keyword for kw in keywords[:3]])
                    if len(keywords) > 3:
                        keyword_preview += "..."
                        
                    # Create list item with element ID as data
                    item = QStandardItem(f"{element_type}: {keyword_preview}")
                    item.setData(element.id, Qt.ItemDataRole.UserRole)
                    self.tagged_elements_model.appendRow(item)
            except DatabaseError as e:
                self.logger.error(f"Database error getting keywords for element {element.id}: {e}", exc_info=True)
                # Skip this element and continue with others
                continue
        
        self.logger.debug(f"Updated tagged elements list with {self.tagged_elements_model.rowCount()} items")
        
    @Slot(QModelIndex)
    def _handle_tagged_element_selected(self, index: QModelIndex):
        """
        Handle selection of an element from the tagged elements list.
        
        Args:
            index: The index of the selected item
        """
        if not index.isValid():
            return
            
        # Get the element ID from the item data
        element_id = index.data(Qt.ItemDataRole.UserRole)
        if element_id is None:
            return
            
        # Tell the slide canvas to select this element
        self.slide_canvas.select_element(element_id)
        self.logger.debug(f"Selected element ID {element_id} from tagged elements list")