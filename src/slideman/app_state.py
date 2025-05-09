# src/slideman/app_state.py

from PySide6.QtCore import QObject, Signal, QSettings, Slot
from PySide6.QtGui import QUndoStack
from typing import Optional, List # For type hinting
import logging

from .services.database import Database # Import Database type hint

# Import models later when they exist and are needed
# from .models.project import Project

class AppState(QObject):
    """
    Singleton class holding the application's shared state.
    Includes the central undo stack.
    """
    _instance = None

    # --- Define Signals ---
    # Signals related to state changes often originate here or are proxied
    projectLoaded = Signal(str) # Emits project_folder_path when a project is loaded
    projectClosed = Signal()    # Emitted when a project is closed
    currentProjectChanged = Signal(str) # Emits project_folder_path when the current project changes
    undoStackChanged = Signal() # Emitted by QUndoStack itself, can be connected to

    # Add signals for slide and element selection
    slideSelected = Signal(int) # slide_id
    elementSelected = Signal(int) # element_id

    # Assembly Manager signals
    assemblyBasketChanged = Signal(list)  # Emits list of keyword IDs
    assemblyOrderChanged = Signal(list)   # Emits ordered list of slide IDs

    def __new__(cls):
        if cls._instance is None:
            logging.debug("Creating AppState instance")
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False # Initialize flag before __init__ call
        return cls._instance

    def __init__(self):
        """Initializes the AppState singleton."""
        if self._initialized:
            return
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # --- Core State Variables ---
        self.settings = QSettings("SlidemanDev", "Slideman") # Company, AppName
        self.undo_stack = QUndoStack(self)
        self.current_project_path: Optional[str] = None
        # self.current_project_model: Optional[Project] = None # Link to loaded project data model

        # Add current slide and element IDs
        self.current_slide_id: Optional[int] = None
        self.current_element_id: Optional[int] = None

        # --- Assembly Manager State ---
        # List of keyword IDs in the basket
        self.assembly_keyword_basket: List[int] = []
        # Ordered list of slide IDs for final assembly
        self.assembly_final_slide_ids: List[int] = []

        # --- Connect internal signals CORRECTLY ---
        # Make sure ALL these lines connect to the SLOT, not the SIGNAL's emit
        self.undo_stack.indexChanged.connect(self._emit_undo_stack_changed)
        self.undo_stack.cleanChanged.connect(self._emit_undo_stack_changed)
        self.undo_stack.canUndoChanged.connect(self._emit_undo_stack_changed)
        self.undo_stack.canRedoChanged.connect(self._emit_undo_stack_changed)

        self.current_project_path: Optional[str] = None
        # --- Add DB Service Reference ---
        # This will be set from outside after initialization
        self.db_service: Optional[Database] = None
        # -----------------------------

        self._initialized = True
        self.logger.info("AppState initialized")

    def set_db_service(self, db_instance: Database):
         """Sets the database service instance for AppState and potentially others to use."""
         self.logger.info("Database service instance set in AppState.")
         self.db_service = db_instance

         
    # --- Intermediate slot ---
    @Slot()
    def _emit_undo_stack_changed(self, *args):
        """Slot to capture various undo stack signals and emit our single notification."""
        self.logger.debug(f"Captured undo stack signal with args: {args}. Emitting undoStackChanged.") # Add logging
        self.undoStackChanged.emit() # Emit our signal with no arguments

    def load_initial_state(self):
        """Loads persistent state like recent projects."""
        self.logger.debug("Loading initial state")
        # self.recent_projects = self.settings.value("recentProjects", [], type=list)
        # Load persisted assembly state
        self.assembly_keyword_basket = self.settings.value("assemblyKeywordBasket", [], type=list)
        self.assembly_final_slide_ids = self.settings.value("assemblyFinalSlideIds", [], type=list)
        # Load last project? Optional.

    def set_current_project(self, project_path: str): #, project_model: Project):
         """Sets the currently active project."""
         self.logger.info(f"Setting current project: {project_path}")
         
         # Only emit changed signal if actually changing projects
         if self.current_project_path != project_path:
             old_path = self.current_project_path
             self.current_project_path = project_path
             # Emit the currentProjectChanged signal
             self.currentProjectChanged.emit(project_path)
             self.logger.debug(f"Project changed from {old_path} to {project_path}")
         else:
             self.current_project_path = project_path
             
         # self.current_project_model = project_model
         self.undo_stack.clear() # Clear undo stack for new project context
         self.undo_stack.setClean()
         # Add to recent projects (implement MRU logic)
         # self._add_to_recent_projects(project_path)
         self.projectLoaded.emit(project_path) # Emit signal

    def close_project(self):
        """Closes the current project, resetting relevant state."""
        self.logger.info("Closing current project")
        self.current_project_path = None
        # self.current_project_model = None
        self.current_slide_id = None
        self.current_element_id = None
        self.undo_stack.clear()
        self.undo_stack.setClean()
        # Clear caches related to the project?
        self.clear_assembly()
        self.projectClosed.emit() # Emit signal

    def clear_assembly(self):
        """Clears the assembly state."""
        self.assembly_keyword_basket = []
        self.assembly_final_slide_ids = []
        self.assemblyBasketChanged.emit(self.assembly_keyword_basket)
        self.assemblyOrderChanged.emit(self.assembly_final_slide_ids)

    def set_assembly_basket(self, ids: List[int]):
        """Set and persist the keyword basket in AppState."""
        self.assembly_keyword_basket = ids
        self.settings.setValue("assemblyKeywordBasket", ids)
        self.assemblyBasketChanged.emit(ids)

    def set_assembly_order(self, ids: List[int]):
        """Set and persist the final slide order in AppState."""
        self.assembly_final_slide_ids = ids
        self.settings.setValue("assemblyFinalSlideIds", ids)
        self.assemblyOrderChanged.emit(ids)

    # --- Add methods to manage recent projects, caches etc. as needed ---

    # --- Testing Helper ---
    def reset_for_tests(self):
        """Resets state for isolated testing."""
        self.logger.debug("Resetting AppState for tests")
        self.undo_stack.clear()
        self.current_project_path = None
        self.current_slide_id = None
        self.current_element_id = None
        # self.current_project_model = None
        # self.recent_projects = []
        # Clear other caches/state
        self.assembly_keyword_basket = []
        self.assembly_final_slide_ids = []


# --- Global Singleton Instance ---
# This line ensures the instance is created when the module is imported.
app_state = AppState()