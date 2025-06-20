# src/slideman/app_state.py

from PySide6.QtCore import QObject, Signal, QSettings, Slot, QMutex, QMutexLocker
from PySide6.QtGui import QUndoStack
from typing import Optional, List # For type hinting
import logging
import threading

from .services.database import Database # Import Database type hint

# Import models later when they exist and are needed
# from .models.project import Project

class AppState(QObject):
    """
    Thread-safe singleton class holding the application's shared state.
    Includes the central undo stack.
    """
    _instance = None
    _lock = threading.Lock()  # Thread lock for singleton creation

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
        # Double-checked locking pattern for thread safety
        if cls._instance is None:
            with cls._lock:
                # Check again inside the lock
                if cls._instance is None:
                    logging.debug("Creating AppState instance")
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False # Initialize flag before __init__ call
                    cls._instance._state_mutex = QMutex()  # Mutex for state modifications
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

        # --- Add DB Service Reference ---
        # This will be set from outside after initialization
        self.db_service: Optional[Database] = None
        
        # --- UX Enhancement State ---
        self.user_level = self._get_user_level()
        
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
        try:
            # self.recent_projects = self.settings.value("recentProjects", [], type=list)
            # Load persisted assembly state
            basket = self.settings.value("assemblyKeywordBasket", [], type=list)
            slide_ids = self.settings.value("assemblyFinalSlideIds", [], type=list)
            
            # Handle None values
            if basket is None:
                basket = []
            if slide_ids is None:
                slide_ids = []
            
            # Ensure all IDs are integers
            self.assembly_keyword_basket = [int(kid) if isinstance(kid, str) else kid for kid in basket if kid is not None]
            self.assembly_final_slide_ids = [int(sid) if isinstance(sid, str) else sid for sid in slide_ids if sid is not None]
            self.logger.debug(f"Loaded assembly basket: {self.assembly_keyword_basket}")
            self.logger.debug(f"Loaded assembly slide IDs: {self.assembly_final_slide_ids}")
            # Load last project? Optional.
        except Exception as e:
            self.logger.error(f"Error loading initial state: {e}", exc_info=True)
            # Reset to defaults on error
            self.assembly_keyword_basket = []
            self.assembly_final_slide_ids = []

    def set_current_project(self, project_path: str): #, project_model: Project):
        """Sets the currently active project (thread-safe)."""
        project_changed = False
        with QMutexLocker(self._state_mutex):
            self.logger.info(f"Setting current project: {project_path}")
            
            # Only emit changed signal if actually changing projects
            if self.current_project_path != project_path:
                old_path = self.current_project_path
                self.current_project_path = project_path
                project_changed = True
                self.logger.debug(f"Project changed from {old_path} to {project_path}")
            else:
                self.current_project_path = project_path
                
            # self.current_project_model = project_model
            self.undo_stack.clear() # Clear undo stack for new project context
            self.undo_stack.setClean()
            # Add to recent projects (implement MRU logic)
            # self._add_to_recent_projects(project_path)
        
        # Emit signals outside the mutex lock
        if project_changed:
            self.currentProjectChanged.emit(project_path)
        self.projectLoaded.emit(project_path)

    def close_project(self):
        """Closes the current project, resetting relevant state (thread-safe)."""
        with QMutexLocker(self._state_mutex):
            self.logger.info("Closing current project")
            self.current_project_path = None
            # self.current_project_model = None
            self.current_slide_id = None
            self.current_element_id = None
            self.undo_stack.clear()
            self.undo_stack.setClean()
            # Store basket state to clear after mutex release
            self.assembly_keyword_basket = []
            self.assembly_final_slide_ids = []
        
        # Emit signals outside the mutex lock
        self.assemblyBasketChanged.emit([])
        self.assemblyOrderChanged.emit([])
        self.projectClosed.emit()

    def clear_assembly(self):
        """Clears the assembly state."""
        with QMutexLocker(self._state_mutex):
            self.assembly_keyword_basket = []
            self.assembly_final_slide_ids = []
        
        # Emit signals outside the mutex lock
        self.assemblyBasketChanged.emit([])
        self.assemblyOrderChanged.emit([])

    def set_assembly_basket(self, ids: List[int]):
        """Set and persist the keyword basket in AppState (thread-safe)."""
        # Ensure all IDs are integers
        ids_int = [int(kid) if isinstance(kid, str) else kid for kid in ids]
        
        with QMutexLocker(self._state_mutex):
            self.assembly_keyword_basket = ids_int
            self.settings.setValue("assemblyKeywordBasket", ids_int)
        self.assemblyBasketChanged.emit(ids_int)

    def set_assembly_order(self, ids: List[int]):
        """Set and persist the final slide order in AppState (thread-safe)."""
        # Ensure all IDs are integers
        ids_int = [int(sid) if isinstance(sid, str) else sid for sid in ids]
        
        with QMutexLocker(self._state_mutex):
            self.assembly_final_slide_ids = ids_int
            self.settings.setValue("assemblyFinalSlideIds", ids_int)
        self.assemblyOrderChanged.emit(ids_int)

    # --- UX Enhancement Methods ---
    def is_first_run(self) -> bool:
        """Check if this is the user's first time running the application."""
        return not self.settings.value("first_run_completed", False, bool)
    
    def complete_first_run(self):
        """Mark the first run as completed."""
        self.settings.setValue("first_run_completed", True)
        self.logger.info("First run completed")
    
    def reset_first_run(self):
        """Reset first run status to show welcome dialog again (for testing/demo)."""
        self.settings.setValue("first_run_completed", False)
        self.logger.info("First run status reset - welcome dialog will show again")
    
    def _get_user_level(self) -> str:
        """Determine user experience level based on completed actions."""
        completed_actions = self.settings.value("completed_actions", 0, int)
        if completed_actions < 5:
            return "beginner"
        elif completed_actions < 20:
            return "intermediate"
        else:
            return "expert"
    
    def increment_completed_actions(self):
        """Increment the count of completed actions."""
        current = self.settings.value("completed_actions", 0, int)
        self.settings.setValue("completed_actions", current + 1)
        old_level = self.user_level
        self.user_level = self._get_user_level()
        if old_level != self.user_level:
            self.logger.info(f"User level upgraded from {old_level} to {self.user_level}")
    
    def should_show_feature(self, feature_name: str) -> bool:
        """Determine if a feature should be visible based on user level."""
        feature_visibility = {
            'beginner': {
                'basic_search': True,
                'simple_tags': True,
                'export': True,
                'advanced_search': False,
                'bulk_operations': False,
                'keyword_similarity': False
            },
            'intermediate': {
                'basic_search': True,
                'simple_tags': True,
                'export': True,
                'advanced_search': True,
                'multi_select': True,
                'custom_tags': True,
                'bulk_operations': False,
                'keyword_similarity': False
            },
            'expert': {
                'basic_search': True,
                'simple_tags': True,
                'export': True,
                'advanced_search': True,
                'multi_select': True,
                'custom_tags': True,
                'bulk_operations': True,
                'keyword_similarity': True
            }
        }
        
        level_features = feature_visibility.get(self.user_level, feature_visibility['expert'])
        return level_features.get(feature_name, True)

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