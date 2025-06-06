# src/slideman/ui/pages/projects_page.py

import logging
from pathlib import Path
from functools import partial
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListView,
                             QToolBar, QStackedWidget, QLabel, QAbstractItemView,
                             QSizePolicy, QStatusBar, QFileDialog, QInputDialog, QMessageBox, QApplication,
                             QMenu, QProgressBar, QFrame, QGridLayout, QPushButton)
from PySide6.QtGui import QAction, QIcon, QStandardItemModel, QStandardItem, QKeySequence, QFont
from PySide6.QtCore import Qt, Slot, QAbstractListModel, QModelIndex, QObject, QItemSelectionModel, QThreadPool, QItemSelection
from typing import List, Any, Optional, Dict, Union # Added Union

# Import necessary components from other layers
from ...services.background_tasks import FileCopyWorker, WorkerSignals# Import the worker
from ...services.database import Database # Import Database type hint
from ...services import file_io # Import our file_io service module
from ...services.exceptions import (
    DatabaseError, ResourceNotFoundError, DuplicateResourceError,
    ValidationError, FileOperationError
)
from ...models.project import Project
from ...models.file import File # Import File model for type hints
from ...event_bus import event_bus
from ...services.slide_converter import SlideConverter, SlideConverterSignals # Import the converter
# --- Command Imports ---
from ...commands.rename_project import RenameProjectCmd
from ...commands.delete_project import DeleteProjectCmd
from ...app_state import app_state # Need access to undo_stack
from ..components.empty_states import NoProjectsEmptyState, LoadingState
from ..components.progress_dialog import ProjectCopyProgressDialog, FileConversionProgressDialog


# --- Project List Model ---
class ProjectListModel(QAbstractListModel):
    """
    A Qt model to manage and display a list of Project objects
    in a QListView.
    """
    ProjectIdRole = Qt.UserRole + 1
    FolderPathRole = Qt.UserRole + 2

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._projects: List[Project] = []
        self.logger = logging.getLogger(__name__)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._projects) if not parent.isValid() else 0

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None
        project = self._projects[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return project.name
        elif role == self.ProjectIdRole:
            return project.id
        elif role == self.FolderPathRole:
            return project.folder_path
        return None

    def load_projects(self, projects: List[Project]):
        self.logger.info(f"Loading {len(projects)} projects into model")
        self.beginResetModel()
        self._projects = sorted(projects, key=lambda p: p.name.lower())
        self.endResetModel()
        self.logger.debug("Model reset with new project data.")

    def get_project(self, index: QModelIndex) -> Optional[Project]:
         if index.isValid() and 0 <= index.row() < self.rowCount():
              return self._projects[index.row()]
         return None

    def get_project_by_id(self, project_id: int) -> Optional[Project]:
         for project in self._projects:
             if project.id == project_id:
                 return project
         return None

# --- Projects Page Widget ---
class ProjectsPage(QWidget):
    """
    The main landing page for managing projects.
    """
    def __init__(self, db_service: Database, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Projects Page")
        self.db = db_service

        # --- SOPHISTICATED layout with proper breathing room ---
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # No margins - clean edge-to-edge
        main_layout.setSpacing(0)  # No spacing for seamless look

        # --- ELEGANT left panel with clean white background ---
        left_panel_widget = QWidget()
        left_panel_widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-right: 1px solid #e5e7eb;
                margin: 0px;
            }
        """)
        left_layout = QVBoxLayout(left_panel_widget)
        left_layout.setContentsMargins(24, 24, 24, 24)  # Professional spacing
        left_layout.setSpacing(20)  # Clean spacing hierarchy

        # SOPHISTICATED toolbar - clean and professional
        self.toolbar = QToolBar("Projects Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: transparent;
                border: none;
                spacing: 12px;
                padding: 0px;
            }
            QToolBar QToolButton {
                background-color: #667eea;
                border: 1px solid #667eea;
                border-radius: 8px;
                padding: 12px 20px;
                color: white;
                font-size: 14px;
                font-weight: 600;
                margin: 3px;
                min-width: 120px;
            }
            QToolBar QToolButton:hover {
                background-color: #5a67d8;
                border-color: #5a67d8;
                transform: translateY(-1px);
            }
            QToolBar QToolButton:pressed {
                background-color: #4c51bf;
                transform: translateY(0px);
            }
            QToolBar QToolButton:disabled {
                background-color: #e5e7eb;
                color: #9ca3af;
                border-color: #e5e7eb;
            }
            QToolBar::separator {
                background-color: #e5e7eb;
                width: 1px;
                margin: 8px 4px;
            }
        """)
        self._setup_toolbar_actions() # Helper for toolbar actions
        left_layout.addWidget(self.toolbar)

        # SOPHISTICATED project list with clean card design
        self.project_list_view = QListView()
        self.project_list_view.setAlternatingRowColors(False)
        self.project_list_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.project_list_view.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.project_list_view.setStyleSheet("""
            QListView {
                background-color: transparent;
                border: none;
                outline: none;
                selection-background-color: transparent;
                font-size: 15px;
                padding: 0px;
            }
            QListView::item {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                margin: 8px 0px;
                padding: 20px 24px;
                color: #374151;
                font-weight: 500;
                min-height: 24px;
            }
            QListView::item:hover {
                background-color: #f8fafc;
                border-color: #cbd5e1;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            }
            QListView::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border: 2px solid #667eea;
                color: white;
                font-weight: 600;
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.25);
            }
            QListView::item:selected:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5a67d8, stop:1 #6b73ff);
                box-shadow: 0 12px 30px rgba(102, 126, 234, 0.35);
            }
        """)
        self._setup_context_menu_actions() # Helper for context actions

        self.project_model = ProjectListModel(self)
        self.project_list_view.setModel(self.project_model)

        # Connect selection signal
        selection_model = self.project_list_view.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self.handle_project_selection_changed)
            self.logger.debug("Connected project list selectionChanged signal.")
        else:
            self.logger.error("Could not get selection model from project_list_view.")

        left_layout.addWidget(self.project_list_view)

        # Progress Bar
        self.task_progress_bar = QProgressBar() # Renamed for clarity
        self.task_progress_bar.setRange(0, 100)
        self.task_progress_bar.setValue(0)
        self.task_progress_bar.setVisible(False)
        self.task_progress_bar.setTextVisible(True)
        self.task_progress_bar.setFormat("Processing... %p%") # Generic format
        left_layout.addWidget(self.task_progress_bar)
        
        # --- Attributes for tracking conversion progress ---
        self._conversion_total_files = 0
        # Instead of tracking percentages, track the actual slide counts
        self._conversion_progress_map: Dict[int, Dict[str, int]] = {} # file_id -> {"current": current_slide, "total": total_slides}
        self._conversion_total_slides = 0
        self._conversion_processed_slides = 0
        # -----------------------------------------------

        # --- ELEGANT right panel with sophisticated styling ---
        self.right_panel = QStackedWidget()
        self.right_panel.setStyleSheet("""
            QStackedWidget {
                background-color: #f8fafc;
                border: none;
                margin: 0px;
            }
        """)
        
        # Empty state for no projects
        self.no_projects_empty_state = NoProjectsEmptyState()
        self.no_projects_empty_state.createProjectRequested.connect(self.handle_new_project)
        self.no_projects_empty_state.importDemoRequested.connect(self._handle_demo_project)
        self.right_panel.addWidget(self.no_projects_empty_state) # Index 0
        
        # Beautiful welcome widget following design system
        self.welcome_widget = self._create_beautiful_welcome_widget()
        self.right_panel.addWidget(self.welcome_widget) # Index 1
        
        # Beautiful project details widget following design system
        self.project_details_widget = self._create_project_details_widget()
        self.right_panel.addWidget(self.project_details_widget) # Index 2

        # --- Assemble Main Layout with OPTIMAL proportions ---
        main_layout.addWidget(left_panel_widget, 40)  # Better proportion for content density
        main_layout.addWidget(self.right_panel, 60)   # More balanced layout

        # --- Load initial data ---
        self.load_projects_from_db()
        self.logger.debug("Projects Page UI initialized.")

    def _setup_toolbar_actions(self):
        """Creates and adds actions to the toolbar with intuitive organization and beautiful styling."""
        # Primary action - most important
        self.new_project_action = QAction("➕ New Project", self)
        self.new_project_action.setToolTip("Create a new project and import PowerPoint files")
        self.new_project_action.triggered.connect(self.handle_new_project)
        self.toolbar.addAction(self.new_project_action)
        
        # Add separator for visual grouping
        self.toolbar.addSeparator()
        
        # Secondary actions - project management
        self.convert_action = QAction("⚡ Convert Slides", self)
        self.convert_action.setToolTip("Process slides for viewing and tagging (requires PowerPoint)")
        self.convert_action.triggered.connect(self.handle_start_conversion)
        self.toolbar.addAction(self.convert_action)
        self.convert_action.setEnabled(False) # Disabled initially
        
        # Add spacer to push refresh to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)
        
        # Utility action - least important, placed at the end
        self.refresh_action = QAction("🔄 Refresh", self)
        self.refresh_action.setToolTip("Refresh the projects list")
        self.refresh_action.triggered.connect(self.handle_refresh_projects)
        self.toolbar.addAction(self.refresh_action)

    def _setup_context_menu_actions(self):
        """Creates and adds actions to the list view's context menu."""
        self.rename_action = QAction("Rename Project...", self) # No icon needed for context menu?
        self.rename_action.triggered.connect(self.handle_rename_project)
        self.project_list_view.addAction(self.rename_action)

        self.delete_action = QAction(QIcon(":/icons/cil-remove.png"), "Delete Project", self)
        self.delete_action.triggered.connect(self.handle_delete_project)
        self.project_list_view.addAction(self.delete_action)

        # Initially disable context actions
        self.rename_action.setEnabled(False)
        self.delete_action.setEnabled(False)

    def _determine_unique_project_path(self, project_name: str) -> Path:
        """r\r
        Determines a unique path for a new project folder based on the name.
        Handles potential duplicates by appending counters.

        Args:
            project_name: The desired base name for the project.

        Returns:
            A Path object representing the unique folder path.

        Raises:
            OSError: If the base documents/project directory cannot be accessed/created.
            Exception: For other unexpected errors during path generation.
        """
        try:
            documents_path = Path.home() / "Documents"
            base_project_dir = documents_path / "SlidemanProjects"
            base_project_dir.mkdir(parents=True, exist_ok=True)

            safe_folder_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in project_name).rstrip()
            if not safe_folder_name: # Handle empty name after sanitization
                safe_folder_name = "Untitled Project"

            project_folder_path = base_project_dir / safe_folder_name

            counter = 1
            while project_folder_path.exists():
                counter += 1
                project_folder_path = base_project_dir / f"{safe_folder_name} ({counter})"

            return project_folder_path
        except OSError as e:
            self.logger.error(f"OS Error determining project path (permissions?): {e}", exc_info=True)
            raise # Re-raise OSError to be caught by caller
        except Exception as e:
            self.logger.error(f"Unexpected error determining project path: {e}", exc_info=True)
            raise # Re-raise other exceptions



    # --- Slots ---
    @Slot()
    def handle_new_project(self):
        """Handles the 'New Project' action workflow."""
        self.logger.info("New Project action triggered")
        if self.task_progress_bar.isVisible():
            self.logger.warning("Task already in progress. Ignoring New Project request.")
            QMessageBox.warning(self, "Operation in Progress", "An operation (copy/convert) is already running.")
            return

        # 1. Select Files
        selected_files, _ = QFileDialog.getOpenFileNames(self, "Select PowerPoint Files", "", "PowerPoint Files (*.pptx);;All Files (*)")
        if not selected_files: return
        source_paths = [Path(f) for f in selected_files]
        self.logger.info(f"Selected {len(source_paths)} files.")

        # 2. Get Name
        project_name, ok = QInputDialog.getText(self, "New Project Name", "Enter a name:")
        if not ok or not project_name.strip(): return
        project_name = project_name.strip()

        # 3. Determine Path
        try:
            project_folder_path = self._determine_unique_project_path(project_name)
            self.logger.info(f"Determined project folder path: {project_folder_path}")
        except Exception as e:
             self.logger.error(f"Failed to determine project path: {e}", exc_info=True)
             QMessageBox.critical(self, "Error", f"Could not determine project directory:\n{e}")
             return

        # 4. Start Background Worker with Progress Dialog
        try:
            self.logger.info("Setting up background file copy worker.")
            
            # Create progress dialog
            self.copy_progress_dialog = ProjectCopyProgressDialog(project_name, self)
            self.copy_progress_dialog.set_total_items(len(source_paths))
            self.copy_progress_dialog.show()
            
            copy_worker_signals = WorkerSignals() # Create signals object in main thread
            worker = FileCopyWorker(source_paths, project_folder_path, signals=copy_worker_signals)

            # Connect signals
            self.logger.debug("Connecting worker signals...") # Log before connect
            copy_worker_signals.progress.connect(self.update_copy_progress)
            # Use partial to pass current project_name and path to the slot
            on_finish_partial = partial(self.handle_copy_finished, project_name, project_folder_path)
            copy_worker_signals.finished.connect(on_finish_partial)
            copy_worker_signals.error.connect(self.handle_copy_error)   

            
            self.logger.debug("Worker signals connected.") # Log after connect

            # --- Update UI to Busy State ---
            self._set_ui_busy(True, f"Copying files for '{project_name}'...")

            QThreadPool.globalInstance().start(worker)
            self.logger.info("FileCopyWorker submitted to thread pool.")

        except Exception as e:
             self.logger.error(f"Failed to set up project creation background task for '{project_name}': {e}", exc_info=True)
             QMessageBox.critical(self, "Project Creation Failed", f"Could not start project creation task:\n{e}")
             self._set_ui_busy(False) # Reset UI if setup failed

    # --- Slots to handle worker signals ---

    @Slot(int)
    def update_task_progress(self, percent: int):
        """
        Slot to update the shared progress bar based on signals
        from either FileCopyWorker or SlideConverter.
        """
        # We could add logic here later if we want different text formats
        # for copy vs. convert, but for now just update the value.
        self.task_progress_bar.setValue(percent)
        
    @Slot(str, int)
    def update_copy_progress(self, file_name: str, files_copied: int):
        """Update the copy progress dialog."""
        if hasattr(self, 'copy_progress_dialog') and self.copy_progress_dialog:
            self.copy_progress_dialog.update_file_copy(file_name, files_copied)

        # --- Replace your entire handle_copy_finished function with this ---
    @Slot(str, Path, dict)
    def handle_copy_finished(self, project_name: str, project_folder_path: Path, copied_files_info: Dict[str, Optional[str]]):
        """Handles successful completion of the file copy worker."""
        self.logger.info(f"File copy finished successfully for project '{project_name}'. Copied {len(copied_files_info)} files.")

        # Immediately reset UI state from Copying (before DB operations)
        # This ensures UI is responsive even if DB operations take a moment or fail
        self._set_ui_busy(False, "Copy complete. Adding project details to database...", is_error=False)
        QApplication.processEvents() # Help ensure UI updates

        if not copied_files_info:
             self.logger.warning("File copy finished, but no files were reported as copied.")
             QMessageBox.warning(self, "Copy Result", "File copying completed, but no files seem to have been copied successfully.")
             # UI is already reset by _set_ui_busy above
             return

        newly_added_file_ids: List[int] = [] # Keep track of file IDs just added
        project_id: Optional[int] = None
        db_success = False # Flag to track outcome

        # --- Perform Database Operations ---
        self.logger.info(f"Adding project '{project_name}' to database.")
        try:
            project_id = self.db.add_project(project_name, str(project_folder_path))
            if project_id is None:
                # Use specific project name in error
                raise RuntimeError(f"Failed to add project '{project_name}' to database (returned None).")

            files_added_to_db = 0
            for rel_path_str, checksum in copied_files_info.items():
                filename = Path(rel_path_str).name
                file_id = self.db.add_file(project_id, filename, rel_path_str, checksum)
                if file_id is None:
                    self.logger.error(f"Failed to add file record to DB for: {rel_path_str} in project ID {project_id}")
                else:
                    files_added_to_db += 1
                    newly_added_file_ids.append(file_id) # Store successfully added ID

            self.logger.info(f"Successfully added project '{project_name}' (ID: {project_id}) with {files_added_to_db} file records.")
            db_success = True # Mark success

        except DuplicateResourceError as e:
            self.logger.error(f"Project '{project_name}' already exists in database: {e}", exc_info=True)
            QMessageBox.warning(self,
                                "Project Already Exists",
                                f"A project named '{project_name}' already exists in the database.")
            event_bus.statusMessageUpdate.emit("Project already exists.", 5000)
            # db_success remains False
        except DatabaseError as e:
            self.logger.error(f"Database error while adding project '{project_name}': {e}", exc_info=True)
            QMessageBox.critical(self,
                                 "Database Error",
                                 f"Files copied successfully for '{project_name}', but failed to add project details to the database.\n\nError: {e}")
            event_bus.statusMessageUpdate.emit("Database error occurred.", 5000)
            # db_success remains False
        except Exception as e:
            self.logger.error(f"Unexpected error adding project/files to database for project '{project_name}': {e}", exc_info=True)
            QMessageBox.critical(self,
                                 "Unexpected Error",
                                 f"An unexpected error occurred while adding project '{project_name}' to the database.\n\nError: {e}")
            event_bus.statusMessageUpdate.emit("Error adding project to database.", 5000)
            # db_success remains False

        # --- Refresh List View AFTER DB operations are done ---
        # Always refresh to reflect current DB state, even if errors occurred during add_file
        self.load_projects_from_db()

        # --- Close Progress Dialog ---
        if hasattr(self, 'copy_progress_dialog') and self.copy_progress_dialog:
            if db_success:
                self.copy_progress_dialog.finish_copy_operation(len(copied_files_info))
            else:
                self.copy_progress_dialog.finish_with_error("Database error occurred")
            
        # --- Final Status Update Based on DB Success ---
        if db_success:
            event_bus.statusMessageUpdate.emit(f"Project '{project_name}' created.", 3000)
            # Track onboarding progress
            app_state.increment_completed_actions()
            event_bus.onboardingProgressUpdate.emit("project_created")
        # No automatic triggering of conversion here anymore

        # --- NOTE: UI state was already reset by _set_ui_busy at the start ---
        # No further UI reset needed here unless subsequent steps require it.
        # Ensure _set_ui_busy correctly re-enables buttons based on current selection.
        self.handle_project_selection_changed(QItemSelection(), QItemSelection()) # Trigger selection update to potentially re-enable convert button if needed

    @Slot(str)
    def handle_copy_error(self, error_message: str):
        """Handles errors reported by the file copy worker."""
        self.logger.error(f"File copy worker failed: {error_message}")
        
        # Close progress dialog with error
        if hasattr(self, 'copy_progress_dialog') and self.copy_progress_dialog:
            self.copy_progress_dialog.finish_with_error(error_message)
            
        self._set_ui_busy(False, f"File copy failed: {error_message}", is_error=True) # Reset UI
        QMessageBox.critical(self, "File Copy Failed", f"Could not copy project files:\n{error_message}")


    @Slot()
    def handle_start_conversion(self):
        """
        Slot for the 'Convert Slides' action. Finds pending/failed files
        for the selected project and starts the conversion process.
        """
        self.logger.info("Convert Slides action triggered by user.")

        selected_project = self._get_selected_project()
        if not selected_project or selected_project.id is None:
            QMessageBox.warning(self, "No Project Selected", "Please select a project from the list first.")
            return

        if self.task_progress_bar.isVisible():
            self.logger.warning("Task already in progress. Ignoring Convert request.")
            QMessageBox.warning(self, "Operation in Progress", "An operation (copy/convert) is already running.")
            return

        project_id = selected_project.id
        project_name = selected_project.name
        project_folder_path = Path(selected_project.folder_path)

        # Call the shared logic to start conversion
        self.start_conversion_for_project(project_id, project_name, project_folder_path)


    def start_conversion_for_project(self, project_id: int, project_name: str, project_folder_path: Path, files_to_convert_ids: Optional[List[int]] = None):
        """
        Shared logic to find files and trigger conversion workers for a project.
        If files_to_convert_ids is provided, converts only those. Otherwise, fetches Pending/Failed.
        """
        self.logger.info(f"Starting conversion process for project: '{project_name}' (ID: {project_id})")

        files_to_convert: List[File] = []
        try:
            if files_to_convert_ids:
                # Convert specific file IDs (e.g., after project creation)
                all_project_files = self.db.get_files_for_project(project_id)
                id_map = {f.id: f for f in all_project_files if f.id is not None}
                files_to_convert = [id_map[fid] for fid in files_to_convert_ids if fid in id_map]
                self.logger.info(f"Converting {len(files_to_convert)} specific files provided.")
            else:
                # Fetch Pending/Failed files if specific IDs not provided
                pending_files = self.db.get_files_for_project(project_id, status='Pending')
                failed_files = self.db.get_files_for_project(project_id, status='Failed')
                files_to_convert = pending_files + failed_files
                self.logger.info(f"Found {len(files_to_convert)} Pending/Failed files to convert.")

            if not files_to_convert:
                self.logger.info(f"No files require conversion for project '{project_name}'.")
                QMessageBox.information(self, "Conversion Not Needed", f"No files require conversion in project '{project_name}'.")
                return # Important to return if nothing to do

        except ResourceNotFoundError as e:
            self.logger.error(f"Project not found (ID {project_id}): {e}", exc_info=True)
            QMessageBox.warning(self, "Project Not Found", f"The project '{project_name}' was not found in the database.")
            return
        except DatabaseError as e:
            self.logger.error(f"Database error fetching files for conversion (Project ID {project_id}): {e}", exc_info=True)
            QMessageBox.critical(self, "Database Error", f"Could not retrieve file list for conversion:\n{e}")
            return
        except Exception as e:
            self.logger.error(f"Unexpected error fetching files for conversion (Project ID {project_id}): {e}", exc_info=True)
            QMessageBox.critical(self, "Unexpected Error", f"An unexpected error occurred:\n{e}")
            return

        # --- Set UI to Conversion Busy State ---
        self._set_ui_busy(True, f"Starting slide conversion for '{project_name}'...")
        self.task_progress_bar.setFormat("Converting slides... %p%") # Set format for conversion
        
        # --- Reset and store conversion tracking info ---
        self._conversion_total_files = len(files_to_convert)
        # Initialize with empty progress data - we'll update when we get the first progress signal with actual slide counts
        self._conversion_progress_map = {file_obj.id: {"current": 0, "total": 0} for file_obj in files_to_convert if file_obj.id}
        self._conversion_total_slides = 0
        self._conversion_processed_slides = 0
        self.task_progress_bar.setValue(0) # Ensure bar starts at 0
        # ---------------------------------------------
        
        # --- Trigger Workers ---
        self._conversion_workers_active = len(files_to_convert) # Initialize counter
        all_workers_failed_to_start = True

        for file_obj in files_to_convert:
            try:
                if file_obj.id is None:
                    self.logger.warning(f"Skipping file with no ID: {file_obj.filename}")
                    self._conversion_workers_active -= 1; continue

                try:
                    self.db.update_file_conversion_status(file_obj.id, 'In Progress')
                except DatabaseError as e:
                    self.logger.error(f"Failed to update file status to 'In Progress' for FileID {file_obj.id}: {e}", exc_info=True)
                    self._conversion_workers_active -= 1
                    continue
                    
                full_file_path = project_folder_path / file_obj.rel_path

                if not full_file_path.exists():
                    self.logger.error(f"File path does not exist: {full_file_path}. Marking as failed.")
                    try:
                        self.db.update_file_conversion_status(file_obj.id, 'Failed')
                    except DatabaseError as e:
                        self.logger.error(f"Failed to update file status to 'Failed' for FileID {file_obj.id}: {e}", exc_info=True)
                    self._conversion_workers_active -= 1; continue

                self.trigger_slide_conversion(file_obj.id, full_file_path)
                all_workers_failed_to_start = False # Mark that at least one started

            except Exception as trigger_e:
                 self.logger.error(f"Error preparing conversion trigger for FileID {file_obj.id}: {trigger_e}", exc_info=True)
                 if file_obj.id:
                     try:
                         self.db.update_file_conversion_status(file_obj.id, 'Failed')
                     except DatabaseError as e:
                         self.logger.error(f"Failed to update file status to 'Failed' for FileID {file_obj.id}: {e}", exc_info=True)
                 self._conversion_workers_active -= 1

        if self._conversion_workers_active <= 0: # Check if counter dropped to zero during setup
            self.logger.warning("No valid conversion workers were started.")
            self._set_ui_busy(False, "Conversion failed to start.", is_error=True)


    def trigger_slide_conversion(self, file_id: int, file_path: Path):
         """Creates and starts a SlideConverter worker."""
         self.logger.info(f"Submitting SlideConverter task for FileID: {file_id}, Path: {file_path}")
         try:
             # --- Get DB PATH from the service instance we have ---
             # db_path = self.db.db_path # Assumes db_path is stored in Database instance
            #  if not db_path:
            #      raise ValueError("Could not retrieve database path from DB service.")
             # --- Pass DB PATH to worker ---
             worker_signals = SlideConverterSignals() # Create signals object LOCALLY
             converter_worker = SlideConverter(file_id=file_id,
                                  file_path=file_path,
                                  db_service=self.db,     # Pass db_service
                                  signals=worker_signals) # Pass signals object

             # ... (Connect signals remains same) ...
             worker_signals.progress.connect(self.handle_conversion_progress)
             worker_signals.finished.connect(self.handle_conversion_finished)
             worker_signals.error.connect(self.handle_conversion_error)
             QThreadPool.globalInstance().start(converter_worker)
         except Exception as e:
             # ... (Error handling remains same, maybe update DB status via self.db) ...
             self.logger.error(f"Failed to create or start SlideConverter for FileID {file_id}: {e}", exc_info=True)
             self.db.update_file_conversion_status(file_id, 'Failed') # Use self.db here
             self._check_conversion_completion(had_error=True)


    # --- Slots to handle conversion signals ---
    @Slot(int, int, int)
    def handle_conversion_progress(self, file_id, current_slide, total_slides):
        """Handles progress updates from a SlideConverter worker, calculates and displays overall progress."""
        if total_slides <= 0: # Avoid division by zero
            return

        # Update the progress for this specific file
        if file_id in self._conversion_progress_map:
            # Get the previous values
            prev_data = self._conversion_progress_map[file_id]
            prev_total = prev_data["total"]
            prev_current = prev_data["current"]
            
            # Update with new values
            self._conversion_progress_map[file_id] = {"current": current_slide, "total": total_slides}
            
            # If this is the first time we're getting data for this file or total has changed,
            # update our total slide count
            if prev_total != total_slides:
                self._conversion_total_slides = self._conversion_total_slides - prev_total + total_slides
                
            # Update our processed slide count
            self._conversion_processed_slides = self._conversion_processed_slides - prev_current + current_slide
            
        else:
            # Should not happen if initialized correctly, but log if it does
            self.logger.warning(f"Received progress for unexpected file ID: {file_id}")
            return

        # Calculate overall progress based on total slides processed
        if self._conversion_total_slides > 0:
            overall_percent = int((self._conversion_processed_slides / self._conversion_total_slides) * 100)
            self.task_progress_bar.setValue(overall_percent)
            # Update status bar with detailed info
            status_msg = f"Converting File ID {file_id}: Slide {current_slide}/{total_slides}... Overall: {self._conversion_processed_slides}/{self._conversion_total_slides} slides ({overall_percent}%)"
            event_bus.statusMessageUpdate.emit(status_msg, 0)
        else:
            self.task_progress_bar.setValue(0)


    @Slot(int)
    def handle_conversion_finished(self, file_id: int):
        """Handles successful completion of a single file conversion."""
        self.logger.info(f"Conversion finished successfully for File ID: {file_id}")
        self._check_conversion_completion(had_error=False) # Check if all done

    @Slot(int, str)
    def handle_conversion_error(self, file_id: int, error_msg: str):
        """Handles error completion of a single file conversion."""
        self.logger.error(f"Conversion failed for File ID: {file_id}. Error: {error_msg}")
        # TODO: Store specific errors per file?
        self._check_conversion_completion(had_error=True) # Check if all done, mark overall error


    def _check_conversion_completion(self, had_error: bool = False):
         """Checks if all active conversion workers have finished."""
         if not hasattr(self, '_conversion_workers_active'):
             # This can happen if the signal arrives after UI reset somehow
             self.logger.warning("_check_conversion_completion called without active counter.")
             return

         self._conversion_workers_active -= 1
         # Store overall error state
         if had_error:
             self._conversion_had_errors = True # Use an instance flag

         self.logger.debug(f"Conversion worker finished/errored. Active count: {self._conversion_workers_active}")

         if self._conversion_workers_active <= 0:
              self.logger.info("All conversion workers finished.")
              overall_error = getattr(self, '_conversion_had_errors', False)
              final_message = "Slide conversion completed with errors." if overall_error else "Slide conversion completed."
              self._set_ui_busy(False, final_message, is_error=overall_error)
              
              # --- Clear tracking variables ---
              self._conversion_total_files = 0
              self._conversion_progress_map = {}
              self._conversion_total_slides = 0
              self._conversion_processed_slides = 0
              # ------------------------------
              
              # Clean up flag
              if hasattr(self, '_conversion_had_errors'):
                   delattr(self, '_conversion_had_errors')
              # Refresh list to show potentially updated 'Completed'/'Failed' statuses
              self.load_projects_from_db()


    # --- SHARED UI State Functions ---
    def _set_ui_busy(self, busy: bool, status_message: str = "", is_error: bool = False):
         """Sets the UI to a busy or idle state."""
         self.logger.debug(f"Setting UI Busy: {busy}, Message: '{status_message}'")
         self.task_progress_bar.setVisible(busy)
         if busy:
             self.task_progress_bar.setValue(0) # Reset progress
         else:
             # Reset progress bar format when idle
             self.task_progress_bar.setFormat("Processing... %p%")

         # Determine selection state *after* potentially finishing task
         selection_model = self.project_list_view.selectionModel()
         has_selection = bool(selection_model and selection_model.hasSelection())

         # Enable/disable controls based on busy state
         self.new_project_action.setEnabled(not busy)
         self.refresh_action.setEnabled(not busy)
         self.project_list_view.setEnabled(not busy)
         self.toolbar.setEnabled(not busy) # Disable whole toolbar might be too much? Maybe just specific actions
         # Only enable context/convert actions if not busy AND something is selected
         self.convert_action.setEnabled(not busy and has_selection)
         self.rename_action.setEnabled(not busy and has_selection)
         self.delete_action.setEnabled(not busy and has_selection)

         if busy:
             QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
         else:
             QApplication.restoreOverrideCursor()

         if status_message:
              timeout = 5000 if is_error else 3000
              if not busy and not is_error: timeout = 3000 # Standard timeout for success
              if busy: timeout = 0 # Show busy message permanently
              event_bus.statusMessageUpdate.emit(status_message, timeout)

         # Clean up counter if finishing
         if not busy and hasattr(self, '_conversion_workers_active'):
              delattr(self, '_conversion_workers_active')

         QApplication.processEvents() # DEBUG: Force UI update


    # --- Helper to get selected project ---
    def _get_selected_project(self) -> Optional[Project]:
        """Gets the currently selected Project object from the list view."""
        selection_model = self.project_list_view.selectionModel()
        if selection_model and selection_model.hasSelection():
            current_index = selection_model.selectedIndexes()[0]
            project = self.project_model.get_project(current_index)
            return project
        return None


    # --- Other Slots (Refresh, Selection Changed, Rename, Delete) ---
    @Slot()
    def handle_refresh_projects(self):
         if self.task_progress_bar.isVisible(): return # Don't refresh during task
         self.logger.info("Refresh Projects action triggered")
         self.load_projects_from_db()

    @Slot(QItemSelection, QItemSelection)
    def handle_project_selection_changed(self, selected: QItemSelection, deselected: QItemSelection):
        """Handles selection changes in the project list view."""
        selected_indexes = selected.indexes()
        have_selection = len(selected_indexes) > 0
        
        # Enable/disable context menu actions based on selection
        self.rename_action.setEnabled(have_selection)
        self.delete_action.setEnabled(have_selection)
        # Enable/disable convert action based on selection
        self.convert_action.setEnabled(have_selection)
        
        # Update right panel based on selection
        if have_selection:
            # Get the selected project (first index in the list)
            index = selected_indexes[0]
            project = self.project_model.get_project(index)
            if project:
                # Show project details and update with actual data
                self._update_project_details(project)
                self.right_panel.setCurrentIndex(2) # Show project details
                
                # IMPORTANT: Set current project in AppState so other pages can access it
                app_state.set_current_project(project.folder_path)
                self.logger.info(f"Project selected: {project.name}")
        else:
            # No selection, show welcome panel  
            self.right_panel.setCurrentIndex(1) # Show welcome widget
            
            # Clear current project in AppState
            app_state.close_project()
            self.logger.info("Project selection cleared")
            
    @Slot()
    def handle_rename_project(self):
        if self.task_progress_bar.isVisible(): return # Don't allow during task
        project = self._get_selected_project()
        if not project: return
        # ... (Rest of rename logic using QInputDialog and pushing RenameProjectCmd) ...
        new_name, ok = QInputDialog.getText(self,"Rename Project","Enter new name:",text=project.name)
        if ok and new_name and new_name.strip() != project.name:
             cmd = RenameProjectCmd(project.id, project.name, project.folder_path, new_name.strip(), self.db)
             app_state.undo_stack.push(cmd)
             self.load_projects_from_db() # Simple refresh


    @Slot()
    def handle_delete_project(self):
        if self.task_progress_bar.isVisible(): return # Don't allow during task
        project = self._get_selected_project()
        if not project: return
        # ... (Rest of delete logic using QMessageBox and pushing DeleteProjectCmd) ...
        reply = QMessageBox.question(self,"Confirm Deletion", f"Delete '{project.name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Yes:
             cmd = DeleteProjectCmd(project.id, project.name, project.folder_path, self.db)
             app_state.undo_stack.push(cmd)
             self.load_projects_from_db() # Simple refresh

    # --- Data Loading ---
    def load_projects_from_db(self):
         self.logger.info("Loading projects from DB...")
         try:
             if self.db: projects = self.db.get_all_projects()
             else: projects = []; self.logger.error("DB service unavailable.")
             self.logger.info(f"Fetched {len(projects)} projects from database.")
             self.project_model.load_projects(projects)
             
             # Update UI based on whether projects exist
             self._update_empty_state(len(projects) == 0)
             
             event_bus.statusMessageUpdate.emit(f"Loaded {len(projects)} projects.", 3000)
         except DatabaseError as e:
             self.logger.error(f"Database error loading projects: {e}", exc_info=True)
             QMessageBox.critical(self, "Database Error", f"Could not load projects from the database:\n{e}")
             event_bus.statusMessageUpdate.emit("Database error loading projects.", 5000)
         except Exception as e:
             self.logger.error(f"Unexpected error loading projects: {e}", exc_info=True)
             QMessageBox.critical(self, "Unexpected Error", f"An unexpected error occurred while loading projects:\n{e}")
             event_bus.statusMessageUpdate.emit("Error loading projects.", 5000)
    
    def _update_empty_state(self, is_empty: bool):
        """Update the right panel to show appropriate state."""
        if is_empty:
            # Show empty state for no projects
            self.right_panel.setCurrentIndex(0)
        else:
            # Show default selection message
            self.right_panel.setCurrentIndex(1)
    
    def _handle_demo_project(self):
        """Handle demo project request from empty state."""
        self.logger.info("Demo project requested from empty state")
        
        try:
            from ...services.demo_content import DemoContentService
            demo_service = DemoContentService(self.db)
            
            # Check if demo project already exists
            if demo_service.has_demo_project():
                QMessageBox.information(
                    self, 
                    "Demo Project", 
                    "Demo project already exists!\n\n"
                    "Look for '🎯 SlideMan Demo Project' in your projects list."
                )
            else:
                # Create demo project
                project_id = demo_service.create_demo_project()
                if project_id:
                    # Also populate sample keywords
                    demo_service.populate_sample_keywords()
                    
                    QMessageBox.information(
                        self, 
                        "Demo Project Created", 
                        "Demo project created successfully!\n\n"
                        "The demo includes 10 sample slides with keywords.\n"
                        "Explore the SlideView and Keywords pages to see how SlideMan works."
                    )
                    
                    # Refresh projects list
                    self.load_projects_from_db()
                    app_state.increment_completed_actions()
                else:
                    QMessageBox.warning(
                        self, 
                        "Demo Project Failed", 
                        "Failed to create demo project.\n\n"
                        "Please try creating a regular project instead."
                    )
                    
        except Exception as e:
            self.logger.error(f"Failed to handle demo project request: {e}", exc_info=True)
            QMessageBox.critical(
                self, 
                "Error", 
                f"Error creating demo project:\n{e}\n\n"
                "Please try creating a regular project instead."
            )
    
    def _create_beautiful_welcome_widget(self):
        """Create a sophisticated welcome widget with elegant design."""
        from PySide6.QtWidgets import QFrame, QGridLayout
        
        welcome_container = QFrame()
        welcome_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 0px;
                margin: 0px;
            }
        """)
        
        layout = QVBoxLayout(welcome_container)
        layout.setContentsMargins(48, 48, 48, 48)  # Generous professional spacing
        layout.setSpacing(32)  # Sophisticated spacing hierarchy
        
        # SOPHISTICATED welcome message
        welcome_label = QLabel("🎯 Ready to Organize")
        welcome_font = QFont()
        welcome_font.setPointSize(28)
        welcome_font.setWeight(QFont.Weight.DemiBold)
        welcome_label.setFont(welcome_font)
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("color: #1f2937; margin-bottom: 16px;")
        
        # ELEGANT subtitle
        subtitle_label = QLabel("Select a project from the left to start managing your slides")
        subtitle_font = QFont()
        subtitle_font.setPointSize(16)
        subtitle_font.setWeight(QFont.Weight.Normal)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet("color: #6b7280; margin-bottom: 24px; line-height: 1.5;")
        
        layout.addWidget(welcome_label)
        layout.addWidget(subtitle_label)
        
        # SOPHISTICATED action cards with elegant spacing
        actions_layout = QGridLayout()
        actions_layout.setSpacing(24)  # Professional spacing for clean visual hierarchy
        
        actions = [
            ("📁", "Create Project", "Start a new project with your PowerPoint files"),
            ("🔍", "Search Slides", "Find any slide across all your projects"),
            ("🏷️", "Tag Content", "Organize slides with keywords for quick access"),
            ("🎯", "Build Presentation", "Assemble new presentations from existing slides")
        ]
        
        for i, (icon, title, desc) in enumerate(actions):
            card = self._create_action_card(icon, title, desc)
            row = i // 2
            col = i % 2
            actions_layout.addWidget(card, row, col)
            
        layout.addLayout(actions_layout)
        layout.addStretch()
        
        return welcome_container
    
    def _create_action_card(self, icon, title, description):
        """Create a sophisticated action card with elegant design."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 16px;
                padding: 24px;
                min-height: 120px;
            }
            QFrame:hover {
                background-color: #f8fafc;
                border-color: #667eea;
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
            }
        """)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(12)  # Professional spacing
        
        # ELEGANT icon
        icon_label = QLabel(icon)
        icon_font = QFont()
        icon_font.setPointSize(24)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("color: #667eea;")
        
        # SOPHISTICATED title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: #1f2937;")
        
        # CLEAN description
        desc_label = QLabel(description)
        desc_font = QFont()
        desc_font.setPointSize(11)
        desc_label.setFont(desc_font)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #6b7280; line-height: 1.4;")
        
        card_layout.addWidget(icon_label)
        card_layout.addWidget(title_label)
        card_layout.addWidget(desc_label)
        
        return card
    
    def _create_project_details_widget(self):
        """Create a sophisticated project details widget."""
        details_container = QFrame()
        details_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 0px;
                margin: 0px;
            }
        """)
        
        layout = QVBoxLayout(details_container)
        layout.setContentsMargins(48, 48, 48, 48)  # Professional spacing
        layout.setSpacing(32)  # Sophisticated spacing hierarchy
        
        # SOPHISTICATED project title (will be updated dynamically)
        self.project_title_label = QLabel("Project Overview")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setWeight(QFont.Weight.DemiBold)
        self.project_title_label.setFont(title_font)
        self.project_title_label.setStyleSheet("color: #1f2937;")
        
        # ELEGANT project stats cards container
        stats_container = QFrame()
        stats_container.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 16px;
                padding: 24px;
            }
        """)
        
        stats_layout = QGridLayout(stats_container)
        stats_layout.setSpacing(20)
        
        # Create stat cards
        self.files_stat = self._create_stat_card("📁", "0", "Files")
        self.slides_stat = self._create_stat_card("🎞️", "0", "Slides") 
        self.keywords_stat = self._create_stat_card("🏷️", "0", "Keywords")
        self.status_stat = self._create_stat_card("⚡", "Ready", "Status")
        
        stats_layout.addWidget(self.files_stat, 0, 0)
        stats_layout.addWidget(self.slides_stat, 0, 1)
        stats_layout.addWidget(self.keywords_stat, 1, 0)
        stats_layout.addWidget(self.status_stat, 1, 1)
        
        # Action buttons
        actions_container = QFrame()
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setSpacing(10)
        
        self.convert_btn = QPushButton("🔄 Convert Slides")
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #667eea;
                color: white;
                padding: 14px 24px;
                font-size: 14px;
                font-weight: 600;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #5a67d8;
            }
            QPushButton:disabled {
                background-color: #e5e7eb;
                color: #9ca3af;
            }
        """)
        self.convert_btn.clicked.connect(self.handle_start_conversion)
        
        self.view_slides_btn = QPushButton("👁️ View Slides")
        self.view_slides_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #374151;
                padding: 14px 24px;
                font-size: 14px;
                font-weight: 600;
                border: 1px solid #d1d5db;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
                border-color: #9ca3af;
            }
        """)
        # TODO: Connect to switch to SlideView page
        
        actions_layout.addWidget(self.convert_btn)
        actions_layout.addWidget(self.view_slides_btn)
        actions_layout.addStretch()
        
        layout.addWidget(self.project_title_label)
        layout.addWidget(stats_container)
        layout.addWidget(actions_container)
        layout.addStretch()
        
        return details_container
    
    def _create_stat_card(self, icon, value, label):
        """Create a sophisticated stat card widget."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel(icon)
        icon_font = QFont()
        icon_font.setPointSize(20)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("color: #667eea;")
        
        # Value
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setWeight(QFont.Weight.Bold)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("color: #1f2937;")
        
        # Label
        label_label = QLabel(label)
        label_font = QFont()
        label_font.setPointSize(12)
        label_font.setWeight(QFont.Weight.Medium)
        label_label.setFont(label_font)
        label_label.setAlignment(Qt.AlignCenter)
        label_label.setStyleSheet("color: #6b7280;")
        
        layout.addWidget(icon_label)
        layout.addWidget(value_label)
        layout.addWidget(label_label)
        
        # Store references for updating
        card.value_label = value_label
        
        return card
    
    def _update_project_details(self, project):
        """Update the project details widget with real project data."""
        try:
            # Update project title
            self.project_title_label.setText(f"📁 {project.name}")
            
            # Get project statistics from database
            files = self.db.get_files_for_project(project.id)
            file_count = len(files)
            
            # Count slides across all files
            slide_count = 0
            completed_files = 0
            for file in files:
                if file.conversion_status == "Completed":
                    slides = self.db.get_slides_for_file(file.id)
                    slide_count += len(slides)
                    completed_files += 1
            
            # Count unique keywords for this project
            keyword_count = 0
            try:
                # Get all keywords used in this project
                all_keywords = set()
                for file in files:
                    if file.conversion_status == "Completed":
                        slides = self.db.get_slides_for_file(file.id)
                        for slide in slides:
                            slide_keywords = self.db.get_keywords_for_slide(slide.id)
                            all_keywords.update(kw.name for kw in slide_keywords)
                keyword_count = len(all_keywords)
            except Exception as e:
                self.logger.warning(f"Could not count keywords for project {project.id}: {e}")
            
            # Determine status
            if file_count == 0:
                status = "Empty"
            elif completed_files == 0:
                status = "Pending"
            elif completed_files == file_count:
                status = "Ready"
            else:
                status = f"{completed_files}/{file_count} Ready"
            
            # Update stat cards
            self.files_stat.value_label.setText(str(file_count))
            self.slides_stat.value_label.setText(str(slide_count))
            self.keywords_stat.value_label.setText(str(keyword_count))
            self.status_stat.value_label.setText(status)
            
            # Update button states
            has_unconverted = any(f.conversion_status in ["Pending", "Failed"] for f in files)
            self.convert_btn.setEnabled(has_unconverted)
            if not has_unconverted:
                self.convert_btn.setText("✅ All Converted")
            else:
                pending_count = sum(1 for f in files if f.conversion_status in ["Pending", "Failed"])
                self.convert_btn.setText(f"🔄 Convert {pending_count} Files")
                
        except Exception as e:
            self.logger.error(f"Error updating project details: {e}", exc_info=True)
            # Set default values on error
            self.project_title_label.setText(f"📁 {project.name}")
            self.files_stat.value_label.setText("?")
            self.slides_stat.value_label.setText("?")
            self.keywords_stat.value_label.setText("?")
            self.status_stat.value_label.setText("Error")