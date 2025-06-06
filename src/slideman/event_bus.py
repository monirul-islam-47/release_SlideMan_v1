# src/slideman/event_bus.py

from PySide6.QtCore import QObject, Signal
import logging

class EventBus(QObject):
    """
    Singleton class acting as a central hub for application-wide signals.
    Helps decouple components.
    """
    _instance = None

    # --- Define ALL global signals ---

    # Project Lifecycle Events
    projectCreated = Signal(str)       # project_folder_path
    projectOpened = Signal(str)        # project_folder_path (may overlap with AppState.projectLoaded)
    projectSaved = Signal(str)         # project_folder_path (if explicit save needed)
    projectClosed = Signal(str)        # project_folder_path
    # projectClosed signal exists in AppState, maybe reuse or proxy?

    # File/Slide Processing (from background tasks)
    fileCopyProgress = Signal(int)     # percent complete
    fileCopyFinished = Signal(list)    # list of copied file paths/info
    fileCopyError = Signal(str)        # error message
    conversionProgress = Signal(int, int, int) # file_id, current_slide_idx, total_slides
    conversionFinished = Signal(int)   # file_id
    conversionError = Signal(int, str) # file_id, error_message
    thumbnailReady = Signal(int)       # slide_id (when its thumbnail is loaded/generated)

    # Data Change Events (often triggered after DB update)
    keywordsChanged = Signal(int)      # slide_id or element_id whose keywords changed
    keywordMerged = Signal(str, str)   # old_keyword_text, new_keyword_text

    # UI Interaction Events (can be useful for cross-page communication)
    navigateToSlide = Signal(int)      # slide_id
    navigateToPage = Signal(str)       # page name/index

    # Status/Notification Events
    statusMessageUpdate = Signal(str, int) # message, timeout_ms
    errorMessageOccurred = Signal(str, str) # title, message (for dialogs/notifications)

    # UX Enhancement Events
    onboardingProgressUpdate = Signal(str) # action type for progress tracking

    # Theme change could also be here if preferred over direct call
    # themeChanged = Signal(str) # "light" / "dark"

    def __new__(cls):
        if cls._instance is None:
            logging.debug("Creating EventBus instance")
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # QObject.__init__(self) # Not needed if __new__ handles instance correctly
        # This check prevents re-initialization on subsequent imports
        if hasattr(self, '_initialized') and self._initialized:
             return
        super().__init__() # Call QObject's init
        self.logger = logging.getLogger(__name__)
        self._initialized = True
        self.logger.info("EventBus initialized")


# --- Global Singleton Instance ---
event_bus = EventBus()