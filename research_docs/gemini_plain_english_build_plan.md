```markdown
# Project Power Presenter - Detailed Build Plan (Single Developer)

This plan outlines the steps for a single developer to build the "Project Power Presenter" application based on the provided `idea.md`, `project_layout.md`, `architecture.md`, and subsequent clarifications. It emphasizes an iterative approach, building core functionality first and layering features.

**Assumptions:**

*   Developer is proficient in Python and has some experience with PySide6/Qt.
*   Development environment is Windows (due to COM dependency).
*   Poetry or a similar virtual environment/package manager is used.
*   Git is used for version control from the beginning.

**Phase 1: Foundation & Core Infrastructure (Week 1-2)**

*   **Goal:** Set up the project structure, basic window, core state management, theme loading, logging, and settings persistence. No real PowerPoint logic yet.
*   **Steps:**
    1.  **Project Setup:**
        *   Create the root directory (`pptx_manager`).
        *   Initialize Git repository (`git init`).
        *   Create the full directory structure as defined in `project_layout.md` (including `src/pptx_manager`, `resources/`, `tests/`, etc.).
        *   Create initial `.gitignore`, `README.md`, `LICENSE`.
    2.  **Environment & Dependencies:**
        *   Set up Python 3.9 environment (using Poetry, venv, etc.).
        *   Initialize `pyproject.toml` (or `requirements.txt`).
        *   Install core dependency: `PySide6`. Add `pywin32` now, even if not used immediately. Add `Pillow`, `rapidfuzz`, `appdirs`. Add dev dependencies: `pytest`, `pytest-qt`.
    3.  **Resource Compilation:**
        *   Place initial icons (SVGs preferred) in `resources/icons/`.
        *   Place `dark.qss` and `light.qss` (can be placeholders initially) in `resources/qss/`.
        *   Create `resources.qrc` listing these assets.
        *   Compile `resources.qrc` to `resources_rc.py` using `pyside6-rcc` and add the command to build scripts/Makefile if desired. Ensure `resources_rc.py` is imported somewhere (e.g., `main_window.py`).
    4.  **Basic Main Window:**
        *   Implement `src/pptx_manager/ui/main_window.py`.
        *   Create `MainWindow` class inheriting `QMainWindow`.
        *   Set up the basic structure: a central `QStackedWidget` and placeholder areas for left-rail navigation buttons.
        *   Create `src/pptx_manager/__main__.py` to instantiate `QApplication`, create `MainWindow`, show it, and start the event loop. Make the app runnable.
    5.  **Theme Loading:**
        *   Implement `src/pptx_manager/theme.py`.
        *   Add functions to load QSS content from the compiled resources (`:/qss/dark.qss`).
        *   Apply a default theme (e.g., dark) to the `QApplication` in `__main__.py`.
        *   Add a placeholder menu action in `MainWindow` to toggle themes (logic can come later).
    6.  **Logging & Crash Handling:**
        *   Configure Python's `logging` module in `__main__.py` or a dedicated setup function.
        *   Set up `RotatingFileHandler` to write logs to the location determined by `appdirs`.
        *   Implement the `sys.excepthook` replacement as detailed in `idea.md` to catch unhandled exceptions, log them, and show a user-friendly `QMessageBox`.
    7.  **Core State Management:**
        *   Implement the `AppState` singleton class in `src/pptx_manager/app_state.py` (subclassing `QObject`). Include `QUndoStack` as a member.
        *   Implement the `EventBus` singleton class in `src/pptx_manager/event_bus.py` (subclassing `QObject`) with placeholder signals defined in `idea.md`.
    8.  **Persistent Settings:**
        *   Utilize `QSettings` within `AppState` or `MainWindow` (`__init__` and `closeEvent`).
        *   Store/restore window geometry (size, position).
        *   Store/restore the chosen theme (light/dark).
        *   Implement a placeholder for storing/restoring recent projects (MRU list).

**Phase 2: Data Modeling & Persistence (Week 2-3)**

*   **Goal:** Define data structures and set up the SQLite database interaction layer.
*   **Steps:**
    1.  **Data Models:**
        *   Implement the pure data classes in `src/pptx_manager/models/` (`project.py`, `slide.py`, `keyword.py`, `element.py` - defining `ElementBBox` using EMUs). Use `@dataclass` or Pydantic.
    2.  **Database Service Setup:**
        *   Implement `src/pptx_manager/services/database.py`.
        *   Create a `Database` class or module functions.
        *   Implement `connect()` function (connects to a DB file, e.g., within the project folder or a central app data location initially).
        *   Implement `create_tables()` function containing the `CREATE TABLE` SQL statements based on the schema in `idea.md`. Ensure `FOREIGN KEY` constraints and `ON DELETE CASCADE` are included.
        *   Implement basic `PRAGMA user_version` check and placeholder logic for future migrations.
    3.  **Basic CRUD Operations:**
        *   Implement core functions in `database.py` needed for the *Projects Page* first:
            *   `add_project(name, folder_path)`
            *   `get_project_by_id(id)`
            *   `get_project_by_path(path)`
            *   `get_all_projects()` -> `list[Project]`
            *   `rename_project(id, new_name)`
            *   `delete_project(id)`
            *   (Defer slide/element/keyword CRUD until needed).
    4.  **Initial Unit Tests:**
        *   Set up `pytest` structure in `src/pptx_manager/tests/`.
        *   Write basic unit tests for the `Database` service using an in-memory SQLite DB or a temporary file DB (using `pytest` fixtures like `tmp_path`). Test `create_tables` and the project CRUD functions.

**Phase 3: Projects Page & File Handling (Week 3-4)**

*   **Goal:** Implement the landing page functionality: creating projects (including file copying) and listing existing ones.
*   **Steps:**
    1.  **Projects Page UI:**
        *   Implement `src/pptx_manager/ui/pages/projects_page.py`.
        *   Build the UI layout described in `idea.md` (Toolbar, `QListView`, `QStackedWidget` for right panel).
        *   Create a custom `QAbstractListModel` to display project data (`name`, `created_at`, counts - initially hardcoded/zero). Connect it to the `QListView`.
    2.  **File I/O Service:**
        *   Implement `src/pptx_manager/services/file_io.py`.
        *   Add function `copy_files_to_project(source_paths: list[str], project_folder: str)`:
            *   Performs disk space check beforehand.
            *   Copies files. **Implement synchronously first.**
            *   Returns list of relative paths within the project folder.
            *   Handles potential errors (permissions, disk full).
    3.  **Connect "New Project" Workflow:**
        *   Wire the "New Project" toolbar button on `ProjectsPage`.
        *   Implement the wizard steps (or dialogs): Select files -> Enter project name -> Confirm.
        *   On confirmation:
            *   Call `file_io.copy_files_to_project`.
            *   Call `database.add_project` with name and the new project folder path.
            *   Call `database.add_file` for each copied file (requires adding `files` table and CRUD).
            *   Update the `ProjectListModel` to show the new project.
            *   Emit `projectCreated` signal from `EventBus` (placeholder).
            *   Update `AppState`'s MRU list and save `QSettings`.
    4.  **List Existing Projects:**
        *   On application start (`MainWindow.__init__`) or `ProjectsPage` load:
            *   Call `database.get_all_projects()`.
            *   Populate the `ProjectListModel` with the retrieved data.
    5.  **Project Actions:**
        *   Implement Rename/Delete actions (context menu on list view).
        *   Connect actions to dialogs -> call respective `database` functions -> update list model.
        *   Implement the corresponding `QUndoCommand` classes (`CreateProjectCmd`, `RenameProjectCmd`, `DeleteProjectCmd`) in `src/pptx_manager/commands/`. Push them to `AppState.undo_stack`. Wire Undo/Redo actions (Ctrl+Z/Y) in `MainWindow` to the stack.
    6.  **Basic Background Task (File Copy):**
        *   Refactor the file copying part of the "New Project" workflow.
        *   Create a `QRunnable` worker that takes source/destination paths.
        *   Use `QThreadPool.globalInstance().start(worker)`.
        *   Emit progress signals (e.g., `fileCopyProgress(int_percent)`) from the worker using `QObject` signal emission technique for threads.
        *   Connect progress signals to a `QProgressBar` on the `ProjectsPage` or `MainWindow` status bar.

**Phase 4: Core PowerPoint Integration - Slide Conversion (Week 5-6)**

*   **Goal:** Tackle the riskiest part: using COM to convert slides to images and extract basic shape info. Get *one* slide working reliably.
*   **Steps:**
    1.  **PowerPoint Check:**
        *   Implement a utility function (e.g., in `services/slide_converter.py` or a new `com_utils.py`) to check if PowerPoint is installed and can be instantiated via COM (`win32com.client.Dispatch`). Call this check early (e.g., at app start) and show a clear error message if it fails.
    2.  **Slide Converter Service:**
        *   Implement `src/pptx_manager/services/slide_converter.py`.
        *   Create `SlideConverter(QRunnable)` class.
        *   It should accept a `file_id` and the absolute path to the `.pptx` file.
        *   Inside `run()`:
            *   Initialize COM (`pythoncom.CoInitialize()`).
            *   Open the presentation using COM (`PowerPoint.Application.Presentations.Open(...)`). **Handle errors robustly.**
            *   Iterate through slides:
                *   For each slide, call `Slide.Export(output_path, 'PNG')`. **Handle errors.**
                *   Use `python-pptx` to open the *same* file (or maybe access via COM object model if easier/faster?) to get shape data: iterate `slide.shapes`, get `shape.shape_id`, `shape.name`, `shape.left`, `shape.top`, `shape.width`, `shape.height` (these are in EMUs).
                *   Add records to `slides` and `elements` tables in the database (requires adding these tables and CRUD functions to `database.py`). Store `bbox` in EMUs.
            *   Emit `conversionProgress(file_id, slide_index, total_slides)` signal via `EventBus`.
            *   Emit `conversionFinished(file_id)` or `conversionError(file_id, error_message)` on completion/failure.
            *   Uninitialize COM (`pythoncom.CoUninitialize()`).
    3.  **Thumbnail Cache Structure:**
        *   Implement `src/pptx_manager/services/thumbnail_cache.py`.
        *   Create `ThumbnailCache` class (can be a simple dictionary mapping `slide_id` to `QPixmap` initially, plus logic to save/load generated PNGs from a dedicated cache directory).
        *   Provide `get_thumbnail(slide_id)` method. If not in memory/disk cache, return a placeholder and *potentially* trigger generation later (or rely on initial conversion).
    4.  **Integrate Conversion into Project Creation:**
        *   After file copying succeeds in the "New Project" workflow:
            *   For each added file, create and start a `SlideConverter` task via `QThreadPool`.
        *   Connect `EventBus` signals (`conversionProgress`, `conversionFinished`, `conversionError`) to UI elements (e.g., update status bar, show completion message, enable navigation to SlideView once *at least one* slide is done?).
        *   Store generated PNG paths in the `slides.thumb_path` column in the database.

**Phase 5: SlideView Page & Tagging (Week 7-9)**

*   **Goal:** Implement the core slide viewing and tagging interface.
*   **Steps:**
    1.  **SlideView Page UI:**
        *   Implement `src/pptx_manager/ui/pages/slideview_page.py`.
        *   Build the layout: `QSplitter`, Left Pane (`QGraphicsView` for canvas, `QListView` for thumbnails), Right Pane (placeholders for keyword panels).
    2.  **Thumbnail Bar:**
        *   Implement a `QAbstractListModel` for thumbnails, fetching slide info (ID, thumb path) from the database for the current project.
        *   Implement a custom delegate (or use `QListView` Icon Mode) to display thumbnails loaded via `ThumbnailCache`. Use lazy loading if performance requires it.
        *   Connect `thumbnailListView.clicked` signal to load the selected slide.
    3.  **Slide Canvas (`QGraphicsView`):**
        *   Create a custom `QGraphicsView` subclass (`SlideCanvas`).
        *   On slide selection:
            *   Load the full-size slide image (PNG generated by `SlideConverter`) into a `QGraphicsPixmapItem`.
            *   Fetch `elements` data (bounding boxes in EMUs) for the current `slide_id` from the database.
            *   For each element, create a transparent `QGraphicsRectItem` with the correct position/size (convert EMUs to pixels if needed, considering view scale). Store `element_id` on the item (`item.setData`). Make items selectable/clickable.
            *   Add pixmap and rectangle items to the `QGraphicsScene`. Fit the view to the slide.
    4.  **Shape Click Detection & Highlighting:**
        *   Implement mouse press event handling in `SlideCanvas` or scene.
        *   Identify the clicked `QGraphicsRectItem`.
        *   Visually highlight the selected rectangle (e.g., change border color/style).
        *   Emit a custom signal `elementClicked(element_id)` from `SlideCanvas`.
    5.  **Reusable `TagEdit` Widget:**
        *   Implement `src/pptx_manager/ui/components/tag_edit.py`.
        *   Create a widget that displays tags like chips/pills and has an input field for adding new ones. Use `QLineEdit` with `QCompleter` for suggestions.
        *   Emit signals like `tagAdded(text)`, `tagRemoved(text)`.
    6.  **Keyword Panel UI:**
        *   Populate the right pane of `SlideViewPage` with labels and `TagEdit` widgets for Slide Topic/Title and Element Name.
    7.  **Tagging Logic:**
        *   Connect `SlideCanvas.elementClicked` to update the Element Keyword section (enable/disable, load existing tags).
        *   Connect `TagEdit` signals:
            *   When a tag is added/removed:
                *   Create/find the keyword in the `keywords` table (requires adding table and CRUD).
                *   Create/delete the link in `slide_keywords` or `element_keywords` tables (requires adding tables and CRUD). Use database service functions.
                *   Create and push `AddSlideKeywordCmd`, `RemoveSlideKeywordCmd`, `AddElementKeywordCmd`, etc. to the undo stack.
                *   Emit `keywordsChanged(slide_id or element_id)` from `EventBus`.
    8.  **Keyword Loading:**
        *   When a slide is selected, load its existing Topic/Title tags into the `TagEdit` widgets.
        *   When an element is selected, load its existing Name tags.
        *   Implement keyword suggestions using `QCompleter` connected to `database.get_all_keywords_suggestions()`.
    9.  **External Modification Handling (Refined):**
        *   Implement the chosen strategy (Warn or Detect/Reconcile) for handling external edits to project files. This might involve adding file checksums/timestamps to the `files` table and checking them when a project is loaded or a file is accessed. Add UI warnings or re-scan triggers.

**Phase 6: Supporting Pages & Features (Week 10-12)**

*   **Goal:** Implement the remaining pages and core supporting features like fuzzy matching.
*   **Steps:**
    1.  **Keyword Manager Page:**
        *   Implement `src/pptx_manager/ui/pages/keyword_manager_page.py`.
        *   Build UI: `QTableView` on left, panel for fuzzy merge on right.
        *   Implement `QAbstractTableModel` joining `slides` and aggregated keywords. Allow inline editing (optional MVP) or use separate editing widget below.
        *   Implement Fuzzy Merge Panel:
            *   Add service function `find_similar_keywords()` using `rapidfuzz`. Run this in a background thread.
            *   Display suggestions.
            *   Implement "Merge" action: calls `database.merge_keywords(old_kw_id, new_kw_id)` (updates keywords table, re-links references in `slide_keywords`/`element_keywords`).
            *   Implement `MergeKeywordsCmd` for undo.
    2.  **Assembly Manager Page:**
        *   Implement `src/pptx_manager/ui/pages/assembly_page.py`.
        *   Build three-panel UI: Keyword Search/Basket, Slide Preview, Final Set.
        *   Implement keyword search logic (calling DB FTS5 search).
        *   Implement Basket logic (list of selected `keyword_id`s).
        *   Implement Slide Preview (show thumbnails matching selected keyword).
        *   Implement Final Set (show thumbnails matching *any* keyword in basket). Use `QListView` with Icon Mode and enable drag-and-drop reordering (`setDragDropMode(QAbstractItemView.InternalMove)`).
        *   Implement `AddToSetCmd`, `RemoveFromSetCmd`, `ReorderSlideCmd` (for Final Set view).
    3.  **Delivery Page:**
        *   Implement `src/pptx_manager/ui/pages/delivery_page.py`.
        *   Build UI: Large `QListView` (Icon Mode, drag-drop reorder) showing slides from Assembly's Final Set. Toolbar with actions.
        *   Implement "Save As PPTX":
            *   Create `ExportService(QRunnable)` in `services/`.
            *   Worker uses COM to create a new presentation, iterate through the slide IDs in the final set order, and insert slides from their source presentations (`Slides.InsertFromFile`). **Handle errors.**
            *   Emit progress/completion/error signals.
        *   Implement "Open in PowerPoint": Similar logic, but doesn't save the file, just leaves the new presentation open.
    4.  **Reusable `SlideThumbnailWidget` (Refactor):**
        *   If thumbnail display/interaction logic is complex and repeated (SlideView, KeywordMgr, Assembly, Delivery), refactor it into `src/pptx_manager/ui/components/slide_thumbnail.py`. Ensure it supports drag-and-drop source/target roles where needed.

**Phase 7: Polishing, Testing & Packaging (Week 13-14)**

*   **Goal:** Refine UX, add accessibility, improve error handling, write more tests, and package the application.
*   **Steps:**
    1.  **UI/UX Polish:**
        *   Review all pages for consistency, layout issues, missing tooltips.
        *   Ensure theme switching works correctly.
        *   Refine progress indication and feedback messages.
        *   Implement the "Unified search bar" (v1.x goal, maybe defer).
    2.  **Accessibility:**
        *   Implement keyboard navigation (tab order, shortcuts Alt+1..5 for pages).
        *   Set accessible names/descriptions for controls.
        *   Test basic screen reader compatibility (Windows Narrator).
        *   Check color contrast, especially for custom Dracula theme elements.
    3.  **Error Handling:**
        *   Review error handling for edge cases (file not found, COM errors, DB errors, network errors if update check added).
        *   Provide informative user messages for common failures.
    4.  **Testing Expansion:**
        *   Write more unit tests for services (especially keyword merging, complex DB queries).
        *   Write GUI tests using `pytest-qt` for core workflows (create project, add tag, assemble basic deck, export). Mock COM interactions where feasible. Test Undo/Redo extensively.
    5.  **Documentation:**
        *   Update `README.md` with usage instructions, features, known limitations, and how to report issues.
        *   Add basic inline code documentation (docstrings).
    6.  **Packaging:**
        *   Create a PyInstaller spec file (`.spec`).
        *   Configure it to:
            *   Include necessary data files (QSS, icons via resources or `datas`).
            *   Include Qt platform plugins (`platforms/qwindows.dll`), styles, imageformats, etc.
            *   Include tricky dependencies (`pywin32` COM files, `rapidfuzz` compiled extension).
            *   Set application icon.
            *   Use `--noconsole` for the final build.
        *   Test the packaged application thoroughly on a clean machine/VM.
    7.  **Basic Update Check:**
        *   Implement a simple check (e.g., against a VERSION file on a web server or GitHub release asset list).
        *   If update found, notify user and provide download link (manual install for MVP).

**Phase 8: Release & Iteration (Ongoing)**

*   **Goal:** Release v1.0 and plan for v1.x based on feedback.
*   **Steps:**
    1.  **Final Testing & Bug Fixing.**
    2.  **Create v1.0 Release** (e.g., GitHub Release with packaged EXE).
    3.  **Gather User Feedback.**
    4.  **Prioritize v1.x features** (Unified search, CI/CD, i18n scaffolding, etc.).
    5.  **Begin next development cycle.**

This detailed plan provides a roadmap. The developer should commit code frequently, test continuously, and be prepared to adjust timelines based on unforeseen challenges, particularly with COM integration and UI polishing.
```