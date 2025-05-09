# Project Slideman - Detailed Technical Build Plan (with File Structure Integration)

This plan provides technical specifics for implementing the Slideman application, explicitly mentioning target files based on `project_layout.md`.

**Phase 1: Foundation & Core Infrastructure (Est. Week 1-2)**

*   **Goal:** Establish the project skeleton, core Qt application, dependencies, resource handling, basic state management, logging, and settings.
*   **Technical Steps:**
    1.  **Project Setup:**
        *   **Files:** Create root folder `pptx_manager/`, run `git init`. Create `.gitignore`, `README.md`, `LICENSE`. Create `pyproject.toml` using `poetry init`. Create directory structure: `src/pptx_manager/`, `resources/icons/`, `resources/qss/`, `tests/unit/`, `tests/gui/`, `src/pptx_manager/services/`, `src/pptx_manager/models/`, `src/pptx_manager/ui/components/`, `src/pptx_manager/ui/pages/`, `src/pptx_manager/commands/`.
        *   **Content (`pyproject.toml`):** Define dependencies (Python ~3.9, PySide6, pywin32, Pillow, rapidfuzz, appdirs) and dev dependencies (pytest, pytest-qt) as previously detailed.
    2.  **Environment:** Run `poetry install`.
    3.  **Resource Compilation:**
        *   **Files:** Create `resources/resources.qrc`. Populate `resources/icons/`, `resources/qss/` with initial assets (SVGs, `dark.qss`, `light.qss`).
        *   **Content (`resources/resources.qrc`):** Define resource paths as XML (see previous example).
        *   **Action:** Run `pyside6-rcc resources/resources.qrc -o src/pptx_manager/resources_rc.py`.
        *   **File Modification (`src/pptx_manager/__main__.py` or `src/pptx_manager/ui/main_window.py`):** Add `from . import resources_rc` near the top to ensure resources are loaded.
    4.  **Basic Main Window:**
        *   **File:** Create `src/pptx_manager/ui/main_window.py`.
        *   **Content (`main_window.py`):**
            ```python
            from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget, QMenuBar, QStatusBar
            from PySide6.QtGui import QAction, QIcon, QKeySequence
            from PySide6.QtCore import Slot, QSettings, Qt
            # Import theme and app_state later
            # from .. import theme
            # from ..app_state import app_state # Access singleton instance

            class MainWindow(QMainWindow):
                def __init__(self):
                    super().__init__()
                    self.setWindowTitle("Power Presenter")
                    # self.setWindowIcon(QIcon(":/icons/app_icon.svg"))

                    # Core layout
                    self.stacked_widget = QStackedWidget()
                    # TODO: Add page widgets later
                    # self.projects_page = ProjectsPage() # Example placeholder
                    # self.stacked_widget.addWidget(self.projects_page)

                    # Example: Simple central widget structure
                    main_widget = QWidget()
                    # TODO: Replace with layout containing left nav buttons and stacked_widget
                    layout = QVBoxLayout(main_widget)
                    layout.addWidget(self.stacked_widget)
                    self.setCentralWidget(main_widget)

                    self.status_bar = QStatusBar()
                    self.setStatusBar(self.status_bar)

                    self._create_actions()
                    self._create_menus()
                    # self._create_toolbar() # Optional toolbar
                    self._load_settings()

                def _create_actions(self):
                    # File Menu Actions
                    self.quit_action = QAction(QIcon(":/icons/exit.svg"), "&Quit", self, shortcut=QKeySequence.Quit, statusTip="Exit application", triggered=self.close)
                    # Edit Menu Actions
                    # self.undo_action = app_state.undo_stack.createUndoAction(self, "&Undo")
                    # self.undo_action.setShortcut(QKeySequence.Undo)
                    # self.redo_action = app_state.undo_stack.createRedoAction(self, "&Redo")
                    # self.redo_action.setShortcut(QKeySequence.Redo)
                    # View Menu Actions
                    self.toggle_theme_action = QAction("Toggle &Theme", self, statusTip="Switch between light and dark themes", triggered=self.toggle_theme)
                    # Help Menu Actions
                    self.about_action = QAction("&About", self, statusTip="Show About box", triggered=self.show_about_dialog)

                def _create_menus(self):
                    menu_bar = self.menuBar()
                    file_menu = menu_bar.addMenu("&File")
                    file_menu.addAction(self.quit_action)

                    edit_menu = menu_bar.addMenu("&Edit")
                    # edit_menu.addAction(self.undo_action) # Add when app_state is ready
                    # edit_menu.addAction(self.redo_action)

                    view_menu = menu_bar.addMenu("&View")
                    view_menu.addAction(self.toggle_theme_action)

                    help_menu = menu_bar.addMenu("&Help")
                    help_menu.addAction(self.about_action)

                @Slot()
                def toggle_theme(self):
                    # Assuming theme module is imported
                    # current = theme.get_current_theme()
                    # new = "light" if current == "dark" else "dark"
                    # theme.apply_theme(QApplication.instance(), new)
                    # QSettings().setValue("theme", new) # Persist
                    self.status_bar.showMessage(f"Theme changed to {new}", 2000)

                @Slot()
                def show_about_dialog(self):
                    # QMessageBox.about(self, "About Power Presenter", "...")
                    pass

                def closeEvent(self, event):
                    self._save_settings()
                    event.accept()

                def _load_settings(self):
                    settings = QSettings("YourCompany", "PPTXManager")
                    geom = settings.value("mainWindowGeometry")
                    if geom: self.restoreGeometry(geom)
                    # initial_theme = settings.value("theme", "dark") # Theme applied in __main__

                def _save_settings(self):
                    settings = QSettings("YourCompany", "PPTXManager")
                    settings.setValue("mainWindowGeometry", self.saveGeometry())
                    # Theme already saved on toggle
            ```
        *   **File:** Create `src/pptx_manager/__main__.py`.
        *   **Content (`__main__.py`):** Structure as shown previously, including `QApplication` setup, `setup_logging`, `global_exception_hook`, theme application, singleton instantiation (commented out initially), `MainWindow` creation, and `app.exec()`.
    5.  **Theme Loading:**
        *   **File:** Create `src/pptx_manager/theme.py`.
        *   **Content (`theme.py`):** Implement `load_stylesheet`, `apply_theme`, `get_current_theme` functions using `QFile` to read from `:/qss/...` resources, as shown previously.
    6.  **Logging & Crash Handling:**
        *   **File Modification (`src/pptx_manager/__main__.py`):** Add `setup_logging()` and `global_exception_hook()` implementations as per `idea.md` and previous example.
    7.  **Core State Management:**
        *   **File:** Create `src/pptx_manager/app_state.py`.
        *   **Content (`app_state.py`):**
            ```python
            from PySide6.QtCore import QObject, Signal, QSettings
            from PySide6.QtWidgets import QUndoStack
            from typing import Optional
            # from .models import Project # Import later

            class AppState(QObject):
                _instance = None
                # Define Signals
                projectLoaded = Signal(str) # project_folder_path
                # Add other signals like keywordsChanged, slideSelected etc.

                def __new__(cls):
                    if cls._instance is None:
                        cls._instance = super().__new__(cls)
                        # Initialize state ONLY once
                        cls._instance._initialized = False
                    return cls._instance

                def __init__(self):
                    if self._initialized:
                        return
                    super().__init__()
                    self.settings = QSettings("YourCompany", "PPTXManager")
                    self.undo_stack = QUndoStack(self)
                    self.current_project: Optional['Project'] = None # Use forward ref or import
                    # Add other state variables: keyword_cache, slide_thumbs etc. later
                    self._initialized = True

                def load_initial_state(self):
                     # Load MRU, maybe last project path?
                     pass

                def reset_for_tests(self): # Helper for testing
                    self.undo_stack.clear()
                    self.current_project = None
                    # Reset other state

            # Global instance for easy access
            app_state = AppState()
            ```
        *   **File:** Create `src/pptx_manager/event_bus.py`.
        *   **Content (`event_bus.py`):**
            ```python
            from PySide6.QtCore import QObject, Signal

            class EventBus(QObject):
                _instance = None
                # Define ALL global signals as class attributes
                conversionProgress = Signal(int, int, int) # file_id, current, total
                conversionFinished = Signal(int) # file_id
                conversionError = Signal(int, str) # file_id, error_msg
                keywordsChanged = Signal(int) # slide_id or element_id depending on context
                # ... other signals ...

                def __new__(cls):
                    if cls._instance is None:
                        cls._instance = super().__new__(cls)
                    return cls._instance

            # Global instance
            event_bus = EventBus()
            ```
    8.  **Persistent Settings:** Code using `QSettings` goes primarily into `MainWindow._load_settings`, `MainWindow._save_settings`, `MainWindow.closeEvent`, and potentially `AppState` for app-wide settings not tied to the window itself.

**Phase 2: Data Modeling & Persistence (Est. Week 2-3)**

*   **Goal:** Implement data classes and SQLite service layer.
*   **Technical Steps:**
    1.  **Data Models:**
        *   **Files:** Create `src/pptx_manager/models/project.py`, `file.py`, `slide.py`, `keyword.py`, `element.py`.
        *   **Content (Example `element.py`):**
            ```python
            from dataclasses import dataclass

            @dataclass
            class Element:
                id: int
                slide_id: int
                element_type: str
                bbox_x: float # EMU
                bbox_y: float # EMU
                bbox_w: float # EMU
                bbox_h: float # EMU
            ```
            *(Define other dataclasses similarly)*
    2.  **Database Service Setup:**
        *   **File:** Create `src/pptx_manager/services/database.py`.
        *   **Content (`database.py`):** Implement `Database` class with `connect`, `close`, `_initialize_schema`, `_create_tables` (containing SQL from `idea.md` + indices), `__enter__`, `__exit__` as shown previously.
    3.  **Basic CRUD Operations:**
        *   **File Modification (`src/pptx_manager/services/database.py`):** Add methods to the `Database` class: `add_project(name, path) -> int`, `get_project_by_id(id) -> Optional[Project]`, `get_all_projects() -> list[Project]`, `rename_project(id, name)`, `delete_project(id)`. Implement the necessary SQL `INSERT`, `SELECT`, `UPDATE`, `DELETE` statements. Map `sqlite3.Row` results to your dataclasses. Add `add_file(...)`, `update_file_slide_count(...)` etc. as needed.
    4.  **Initial Unit Tests:**
        *   **File:** Create `src/pptx_manager/tests/services/test_database.py`.
        *   **Content (`test_database.py`):** Use `pytest` fixtures (`tmp_path`) and write test functions (`test_add_and_get_project`, etc.) asserting the behavior of the `Database` class methods, as shown previously.

**Phase 3: Projects Page & File Handling (Est. Week 3-4)**

*   **Goal:** Implement project creation, listing, file copying, basic undo.
*   **Technical Steps:**
    1.  **Projects Page UI:**
        *   **File:** Create `src/pptx_manager/ui/pages/projects_page.py`.
        *   **Content (`projects_page.py`):**
            ```python
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QListView, QToolBar, QStackedWidget, QAbstractItemView
            from PySide6.QtGui import QStandardItemModel, QStandardItem # Or QAbstractListModel
            from PySide6.QtCore import Qt, Slot
            # from ...services.database import Database # Import later
            # from ...app_state import app_state # Import later
            # from ...commands.create_project import CreateProjectCmd # Import later

            class ProjectsPage(QWidget):
                def __init__(self, db: 'Database', parent=None): # Pass DB or access via service locator/DI
                    super().__init__(parent)
                    self.db = db # Store reference
                    layout = QVBoxLayout(self)

                    self.toolbar = QToolBar()
                    # new_action = self.toolbar.addAction("New Project")
                    # new_action.triggered.connect(self.handle_new_project)
                    layout.addWidget(self.toolbar)

                    self.project_list_view = QListView()
                    self.project_model = QStandardItemModel() # Or custom model
                    self.project_list_view.setModel(self.project_model)
                    # self.project_list_view.setContextMenuPolicy(Qt.ActionsContextMenu)
                    # Add Open, Rename, Delete actions to context menu later
                    layout.addWidget(self.project_list_view)

                    # self.right_panel = QStackedWidget() # For welcome/details
                    # layout.addWidget(self.right_panel) # Add if needed

                    self.load_projects()

                def load_projects(self):
                    self.project_model.clear()
                    projects = self.db.get_all_projects() # Fetch data
                    for proj in projects:
                        item = QStandardItem(f"{proj.name} ({proj.created_at})")
                        item.setData(proj.id, Qt.UserRole + 1) # Store ID
                        self.project_model.appendRow(item)

                @Slot()
                def handle_new_project(self):
                    # 1. Show File Dialog (QFileDialog)
                    # 2. Show Name Input (QInputDialog)
                    # 3. Determine project path
                    # 4. Create CreateProjectCmd(name, file_paths, project_path, self.db) # Pass dependencies
                    # 5. app_state.undo_stack.push(cmd)
                    # 6. self.load_projects() # Refresh list
                    pass # Implement logic
            ```
    2.  **File I/O Service:**
        *   **File:** Create `src/pptx_manager/services/file_io.py`.
        *   **Content (`file_io.py`):** Implement `copy_files_to_project(src_list, dest_folder) -> dict`, `calculate_checksum(path) -> str`, `check_disk_space(path, required_bytes) -> bool` using `shutil`, `os`, `hashlib`.
    3.  **Connect "New Project" Workflow:** Logic goes inside `ProjectsPage.handle_new_project` slot, calling `file_io` and `database` methods. Instantiate and push `CreateProjectCmd`.
    4.  **List Existing Projects:** Implemented in `ProjectsPage.load_projects()`. Call this when the page is shown or app starts.
    5.  **Project Actions & Undo:**
        *   **Files:** Create `src/pptx_manager/commands/create_project.py`, `rename_project.py`, `delete_project.py`.
        *   **Content (Example `create_project.py`):**
            ```python
            from PySide6.QtWidgets import QUndoCommand
            # from ..services.database import Database
            # from ..services import file_io
            # from ..models import Project # Or just pass primitive types

            class CreateProjectCmd(QUndoCommand):
                def __init__(self, name, source_files, proj_path, db, parent=None):
                    super().__init__("Create project '{name}'", parent)
                    self.name = name
                    self.source_files = source_files
                    self.proj_path = proj_path
                    self.db = db
                    self.project_id = -1
                    self.copied_files_info = {} # Store rel_path: checksum

                def redo(self):
                    # Ensure proj_path directory exists
                    # self.copied_files_info = file_io.copy_files_to_project(...) # Run copy
                    # self.project_id = self.db.add_project(self.name, self.proj_path)
                    # for rel_path, checksum in self.copied_files_info.items():
                    #    self.db.add_file(self.project_id, Path(rel_path).name, rel_path, checksum)
                    # TODO: Trigger background conversion here!

                def undo(self):
                    # if self.project_id != -1:
                    #    self.db.delete_project(self.project_id) # Uses ON DELETE CASCADE for files
                    #    # shutil.rmtree(self.proj_path) # Delete copied files/folder
            ```
        *   Implement `RenameProjectCmd` (using `db.rename_project`, `os.rename` folder) and `DeleteProjectCmd` (opposite of `CreateProjectCmd.redo`).
        *   Connect context menu actions on `ProjectsPage.project_list_view` to slots that create and push these commands.
    6.  **Basic Background Task (File Copy):**
        *   **File:** Create `src/pptx_manager/services/background_tasks.py` (or similar).
        *   **Content (`background_tasks.py`):** Define `WorkerSignals(QObject)` and `FileCopyWorker(QRunnable)` as shown before.
        *   **File Modification (`src/pptx_manager/commands/create_project.py`):** The `redo` method should *trigger* this worker instead of calling `file_io` directly. Handle the `finished`/`error` signals from the worker to proceed with DB updates *after* copying is done. This makes the command itself synchronous but initiates async work.

**Phase 4: Core PowerPoint Integration - Slide Conversion (Est. Week 5-6)**

*   **Goal:** Implement COM-based slide-to-PNG conversion and shape extraction.
*   **Technical Steps:**
    1.  **PowerPoint Check:**
        *   **File Modification (`src/pptx_manager/services/slide_converter.py` or new `com_utils.py`):** Add `check_powerpoint_available()` function.
        *   **File Modification (`src/pptx_manager/__main__.py`):** Call check function early.
    2.  **Slide Converter Service:**
        *   **File:** Create `src/pptx_manager/services/slide_converter.py`.
        *   **Content (`slide_converter.py`):** Implement `SlideConversionSignals(QObject)` and `SlideConverter(QRunnable)` class as detailed in the previous technical plan, including `CoInitialize`/`CoUninitialize`, COM calls (`Presentations.Open`, `Slide.Export`), `python-pptx` for shape data, DB calls (`add_slide`, `add_element`), and signal emission. Ensure robust `try...finally` blocks.
    3.  **Thumbnail Cache Structure:**
        *   **File:** Create `src/pptx_manager/services/thumbnail_cache.py`.
        *   **Content (`thumbnail_cache.py`):**
            ```python
            from PySide6.QtGui import QPixmap
            from pathlib import Path
            import logging

            class ThumbnailCache:
                def __init__(self, cache_dir: Path):
                    self.cache_dir = cache_dir
                    self.cache_dir.mkdir(parents=True, exist_ok=True)
                    self._memory_cache = {} # slide_id -> QPixmap

                def get_thumbnail(self, slide_id: int, thumb_path_str: Optional[str]) -> Optional[QPixmap]:
                    if slide_id in self._memory_cache:
                        return self._memory_cache[slide_id]
                    if thumb_path_str:
                        thumb_path = Path(thumb_path_str) # Should be absolute or relative to cache_dir? Decide.
                        if thumb_path.exists():
                            pixmap = QPixmap(str(thumb_path))
                            if not pixmap.isNull():
                                self._memory_cache[slide_id] = pixmap
                                return pixmap
                            else:
                                logging.warning(f"Failed to load thumbnail from disk: {thumb_path}")
                    # Return placeholder?
                    return None # Or return a default placeholder QPixmap

                def store_thumbnail(self, slide_id: int, pixmap: QPixmap, thumb_path: Path):
                     # Save pixmap to thumb_path
                     # if pixmap.save(str(thumb_path), "PNG"):
                     #    self._memory_cache[slide_id] = pixmap
                     # else:
                     #    logging.error(f"Failed to save thumbnail: {thumb_path}")
                    pass # Implement saving logic based on where slide_converter saves images

                def clear_memory(self):
                    self._memory_cache.clear()
            ```
    4.  **Integrate Conversion:**
        *   **File Modification (`src/pptx_manager/commands/create_project.py` or logic handling worker completion):** After file copy AND `db.add_file` is done, iterate through added `file_id`s. Get file path from DB. Create `SlideConverter(file_id, file_path, db, cache_instance)` task. Connect its signals (via `EventBus` or direct connection if appropriate) to update UI/status bar. `QThreadPool.globalInstance().start(task)`.

**Phase 5: SlideView Page & Tagging (Est. Week 7-9)**

*   **Goal:** View slides, highlight shapes, implement tagging.
*   **Technical Steps:**
    1.  **SlideView Page UI:**
        *   **File:** Create `src/pptx_manager/ui/pages/slideview_page.py`.
        *   **Content (`slideview_page.py`):** `SlideViewPage(QWidget)` with `QSplitter`, containing `SlideCanvas` (custom `QGraphicsView`), `ThumbnailListView` (standard `QListView`), and a right `QWidget` (`keyword_panel`) with `QFormLayout`.
    2.  **Thumbnail Bar:** Use `QListView`. Create `ThumbnailListModel(QAbstractListModel)` fetching `slides` for current project. Use `QStyledItemDelegate` to draw `QPixmap` from `ThumbnailCache`. Connect `view.clicked` to `SlideViewPage.load_slide_data` slot.
    3.  **Slide Canvas:**
        *   **File:** Create `src/pptx_manager/ui/components/slide_canvas.py`.
        *   **Content (`slide_canvas.py`):** `SlideCanvas(QGraphicsView)`. Implement `load_slide(slide_id, db, cache)` method as described before (clear scene, add pixmap, add selectable `QGraphicsRectItem`s for elements, convert EMU -> scene coords).
    4.  **Shape Click Detection:** In `SlideCanvas`, connect `self.scene().selectionChanged`. Get selected items, extract `element_id`, visually style (`setPen`), emit `elementClicked = Signal(int)`.
    5.  **Reusable `TagEdit` Widget:**
        *   **File:** Create `src/pptx_manager/ui/components/tag_edit.py`.
        *   **Content (`tag_edit.py`):** `TagEdit(QWidget)`. Layout with `QLineEdit` (with `QCompleter`) and a flow layout/area to display tag 'pills' (e.g., `QPushButton`s). Implement `add_tag`, `remove_tag`, `set_tags`, `get_tags` methods. Emit `tagAdded = Signal(str)`, `tagRemoved = Signal(str)`.
    6.  **Keyword Panel UI:**
        *   **File Modification (`src/pptx_manager/ui/pages/slideview_page.py`):** Instantiate `TagEdit` widgets inside the `keyword_panel` layout.
    7.  **Tagging Logic:**
        *   **Files:** Create `commands/add_keyword.py`, `remove_keyword.py`.
        *   **Content (Example `add_keyword.py`):** `AddKeywordCmd(QUndoCommand)` takes `target_id` (slide or element), `kind`, `keyword_text`, `db`. `redo()` calls `db.add_keyword_if_not_exists`, `db.link_slide/element_keyword`. `undo()` calls `db.unlink_slide/element_keyword` (careful not to delete keyword if used elsewhere).
        *   **File Modification (`slideview_page.py`):** Connect `SlideCanvas.elementClicked` to update state. Connect `TagEdit` signals to slots that create and push the `AddKeywordCmd`/`RemoveKeywordCmd`. Fetch suggestions for `QCompleter` from `db.get_all_keyword_strings()`.
    8.  **Keyword Loading:** Implement slots in `SlideViewPage` (`load_slide_data`, `load_element_data`) to fetch keywords from DB and call `tag_edit.set_tags()`.
    9.  **External Modification:** Add checksum logic to `database.py` (`files` table) and checks in project loading / slide access paths.

**Phase 6: Supporting Pages & Features (Est. Week 10-12)**

*   **Goal:** Implement remaining pages and fuzzy matching.
*   **Technical Steps:**
    1.  **Keyword Manager Page:**
        *   **File:** Create `src/pptx_manager/ui/pages/keyword_manager_page.py`. Use `QTableView` + custom `KeywordTableModel`. Background thread (`QRunnable`) in `services/` uses `rapidfuzz` to find suggestions. Merge action calls `db.merge_keywords`.
        *   **File:** Create `src/pptx_manager/commands/merge_keywords.py` (`MergeKeywordsCmd`).
    2.  **Assembly Manager Page:**
        *   **File:** Create `src/pptx_manager/ui/pages/assembly_page.py`. Implement 3-panel UI. Use `db.search_keywords_fts` (requires setting up FTS5 table and triggers in `database.py`). Use draggable `QListView` for Final Set.
        *   **Files:** Create `commands/add_to_set.py`, `remove_from_set.py`, `reorder_slides.py`. Implement commands manipulating the state representing the final slide set (likely stored in `AppState` or the page itself).
    3.  **Delivery Page:**
        *   **File:** Create `src/pptx_manager/ui/pages/delivery_page.py`. Use draggable `QListView`.
        *   **File Modification (`src/pptx_manager/services/background_tasks.py`? Or new `export_service.py`):** Implement `ExportWorker(QRunnable)` using COM (`InsertFromFile`, `SaveAs`). Trigger from Delivery Page buttons.
    4.  **Reusable `SlideThumbnailWidget`:**
        *   **File:** Create `src/pptx_manager/ui/components/slide_thumbnail.py` (if needed). Refactor thumbnail display/interaction logic here. Use this widget or a delegate in the list views across pages.

**Phase 7: Polishing, Testing & Packaging (Est. Week 13-14)**

*   **Goal:** Refine, test thoroughly, package.
*   **Technical Steps:**
    1.  **UI/UX Polish:** Review all `.py` files in `ui/pages/` and `ui/components/`. Add tooltips, refine layouts.
    2.  **Accessibility:** Modify UI elements in `.py` files (pages/components) using `setTabOrder`, `setAccessibleName`. Add `QShortcut`s in `main_window.py`.
    3.  **Error Handling:** Add `try...except` blocks around service calls in UI slots and command `redo`/`undo` methods. Log errors using `logging`. Show `QMessageBox`.
    4.  **Testing Expansion:** Add more test files in `tests/services/`, `tests/commands/`, `tests/gui/`. Use `pytest-qt`'s `qtbot` and mocking (`unittest.mock.patch`).
    5.  **Documentation:** Update `README.md`. Add docstrings to major classes/functions in all `.py` files.
    6.  **Packaging:** Create `pptx_manager.spec` file. Configure `Analysis`, `COLLECT`, `EXE` sections carefully, paying attention to `hiddenimports`, `datas`, `binaries` for Qt plugins, pywin32, rapidfuzz.
    7.  **Basic Update Check:** Add logic (e.g., in `main_window.py` or a helper function) using `urllib.request` and `QDesktopServices`.

**Phase 8: Release & Iteration (Ongoing)**

*   **Goal:** Release, feedback, plan v1.x.
*   **Technical Steps:** Use Git tags. Create GitHub Release. Monitor issues/feedback. Update `README.md` / `docs/` based on roadmap.

This file-integrated plan provides a much more concrete guide for implementation. Remember that code structure might evolve slightly during development.