# PySide6 App – Session Notes (May 2 2025)

*This document captures key points mentioned during the session. I will update it as you share new information. Feel free to ask me to elaborate or reference any item.*

---

* my app should have the visual look, theme and style of the app in this repo: [https://github.com/Wanderson-Magalhaes/Modern\_GUI\_PyDracula\_PySide6\_or\_PyQt6](https://github.com/Wanderson-Magalhaes/Modern_GUI_PyDracula_PySide6_or_PyQt6)
* the app is basically a library/manager for PowerPoint files
* the app should have **pages** (left‑side navigation built on a `QStackedWidget` controlled by custom buttons):

  * \*\* Projects (landing page)\*\* – the user can start a project by selecting one or multiple .pptx files (copying them into a user‑named project folder to keep originals untouched). The page also lists existing projects (or shows an empty list if none) so a user can reopen and continue work.
  * \*\* SlideView/keywords\*\* – once a project is selected, this page shows slides from its files. Layout: left side main slide view with a horizontal, scrollable thumbnail strip underneath; right side keyword panel. Users can add two kinds of slide‑level tags (topic, title) and one kind of element‑level tag (name). Clicking inside the slide view should detect the shape clicked (bounding box via python‑pptx or a better method) and highlight it so tags can be attached. All metadata is stored in a database (e.g. sqlite3).
  * \*\* Keyword manager\*\* – left: scrollable table listing each slide thumbnail alongside its keywords; below the table: widget to edit/update those keywords. Right: panel to detect similar/conflicting keywords and suggest merges.
  * \*\* Assembly manager\*\* – left: widget to search/select keywords within the current project or across all projects and build a list. Middle: widget to search and preview slides by keyword (thumbnails with click‑to‑enlarge). Right: populated with thumbnails of all slides associated with the selected keywords.
  * \*\* Delivery\*\* – shows thumbnails of slides from the previous step; user can reorder via drag‑and‑drop, change thumbnail size, open the ordered set in PowerPoint, or save them to a new .pptx in the project folder.

## Recommendations (added May 2 2025)

### 1. Architecture & File Layout

* **Maintainability**: Adopt an MVVM or MVC structure separating UI, data models, and controllers.
* **Scalability**: Organize each tab in its own module (e.g., `projects_view.py`, `slideview.py`) with shared services (`database.py`, `file_io.py`).

### 2. Data & Performance

* **SQLite schema**: Separate tables for `projects`, `slides`, `elements`, and `keywords` with many‑to‑many junctions; add FTS5 indexes for fast keyword search.
* **Thumbnail caching**: Generate and store thumbnails once per slide to keep navigation snappy.
* **Lazy loading**: Use `QThreadPool`/`QtConcurrent` to load slides in the background so the UI never blocks.

### 3. Tagging Mechanics

* **Clickable shapes**: Pre‑compute shape bounding boxes with `python‑pptx` and overlay `QGraphicsRectItem` for reliable detection and highlighting.
* **Keyword consistency**: Combine fuzzy matching (`rapidfuzz`) with user‑confirmed merges in the Keyword Manager.

### 4. UX Polish

* **Unified search bar**: Add a global keyword search in the toolbar that routes to the Assembly Manager tab.
* **Drag‑and‑drop reuse**: Implement a reusable `SlideThumbnailWidget` so drag behavior is consistent across tabs.
* **Theme abstraction**: Centralize color values in `theme.py`.

### 5. Future‑Proofing & Testing

* **Plugin hooks**: Emit signals such as `slide_set_exported` or `keywords_updated` for extensibility.
* **Unit tests**: Mock `python-pptx` objects to test keyword‑assignment logic independently of the GUI.

## Decisions & Prioritization (added May 2 2025)

### Confirmed for MVP (v1.0)

* **Workflow**: Project versioning with undo‑redo; single‑user, full‑permission model (no multi‑user sync needed).

* **Data**: Element‑geometry stored in slide coordinates for resolution‑independent hit‑testing.

* **UX**: Keyboard‑first navigation; light ⇄ dark theme toggle driven by provided `.qss` + `resources.qrc`.

* **Performance**: Thumbnail caching & lazy loading.

* **Resilience**: Disk‑space check before project copy.

* **Packaging**: Windows‑only build via PyInstaller with a simple in‑app auto‑update (version check + installer download).

* **Keyword management**: Fuzzy keyword merge panel.

### Should‑Have (post‑launch v1.x)

* Unified keyword search bar.
* Optional full‑text slide search (feature‑flagged).
* Internationalization scaffolding—wrap UI strings in `tr()` (see note below).
* Minimal GitHub Actions workflow to run tests and build the installer.
* Unit tests using `pytest‑qt`; drag‑and‑drop `SlideThumbnailWidget` reuse.

### Deferred to v2

* OCR for embedded images.
* Formal DB migration strategy.
* Cross‑platform packaging (macOS/Linux).
* Advanced CI/CD (signed artifacts, release channels).
* AI‑assisted tagging, template‑aware export, plugin API, additional analytics.

### Note on Qt Translation (`tr()`)

Every `QObject` subclass inherits `tr()`, which marks strings for translation extraction. For static contexts use `QtCore.QCoreApplication.translate("context", "text")`. Run `pylupdate6` to generate `.ts` files, translate them with Qt Linguist, compile to `.qm`, and load via `QTranslator` at runtime.

## Pre‑Workflow Checklist (added May 2 2025)

Before detailing each page, make sure these cross‑cutting pieces are designed:

1. **Central AppState** – a singleton or service object that exposes current project, selected slide, keyword list, and undo stack so every widget reads from one source of truth.
2. **Signals & Event Bus** – formalize Qt signals (or a lightweight pub/sub) early—e.g., `project_loaded`, `keywords_changed`—to decouple widgets.
3. **Persistent Settings** – store recent projects, theme choice, window geometry via `QSettings`.
4. **Logging & Crash Handling** – configure Python `logging` to write a rotating file; wrap main loop in a try/except that shows a friendly crash dialog.
5. **Accessibility Checks** – define keyboard focus order and shortcuts now to avoid retrofitting.
6. **Unit‑Test Hooks** – expose pure‑Python functions for DB I/O, keyword merges, etc., so they’re testable without the GUI.
7. **Third‑Party Dependencies** – list required DLLs (Office COM) and Qt plugins; script their copy into the PyInstaller spec.

### Central AppState – Detailed Design (added May 2 2025)

* **Purpose**: Hold all session‑level mutable data in one place—current project path, selected slide ID, keyword cache, undo stack, active theme—so every widget has a single source of truth.
* **Pattern**: Implement as a lightweight singleton (or Borg) subclassing `QObject`:

  ```python
  class AppState(QtCore.QObject):
      _instance = None
      def __new__(cls):
          if cls._instance is None:
              cls._instance = super().__new__(cls)
          return cls._instance
  ```
* **Signals**: `projectLoaded(str)`, `slideSelected(int)`, `keywordsChanged(int)`, `undoStackChanged()`, `thumbnailReady(int)`.
* **Core Data Members**:

  ```python
  current_project: ProjectModel      # @dataclass holding meta & paths
  undo_stack:      QtWidgets.QUndoStack
  settings:        QtCore.QSettings  # persistent app prefs
  slide_thumbs:    dict[int, QtGui.QPixmap]
  keyword_cache:   dict[int, list[str]]
  ```
* **Thread Safety**: Long‑running workers (thumbnail generation, slide parsing) emit results via `thumbnailReady` so updates happen on the GUI thread.
* **Access Pattern**: Any widget imports `app_state` and reads/writes attributes or connects to signals—no circular deps.
* **Persistence Hooks**: `saveSession()` writes recent projects & window geometry (called on app close); `loadSession()` restores them on start.
* **Unit Testing**: Provide a `reset()` helper so tests can instantiate a fresh AppState and verify state changes without the GUI.

### Signals & Event Bus – Detailed Design (added May 2 2025)

* **Goal**: Decouple widgets/modules by routing all cross‑component communication through well‑defined Qt signals (or a thin pub/sub wrapper) so UI elements never directly call each other.
* **Strategy**: Re‑use Qt’s native signal/slot system but formalize an *event namespace* inside `AppState` (or a dedicated `EventBus` object) to keep signals discoverable and unit‑testable.

```python
class EventBus(QtCore.QObject):
    # Project‑level events
    projectLoaded      = QtCore.Signal(str)          # emit project path
    projectSaved       = QtCore.Signal(str)
    projectClosed      = QtCore.Signal()

    # Slide navigation
    slideSelected      = QtCore.Signal(int)          # emit slide_id
    thumbnailReady     = QtCore.Signal(int)          # background thread → GUI
    # Slide conversion (PowerPoint COM export)
    conversionProgress  = QtCore.Signal(int, int, int)  # file_id, slide_idx, total
    conversionFinished  = QtCore.Signal(int)            # project_id
    conversionError     = QtCore.Signal(str)            # error message

    # Keyword actions
    keywordsChanged    = QtCore.Signal(int)          # slide_id whose tags changed
    keywordMerged      = QtCore.Signal(str, str)     # old, new

    # Undo / redo
    undoStackChanged   = QtCore.Signal()

    # UI & misc
    themeChanged       = QtCore.Signal(str)          # "light" / "dark"
```

* **Singleton Access**: `event_bus = EventBus()` created once in `core/event_bus.py`; every widget imports and connects/ emits.
* **Queued Connections**: When emitting from worker threads, force queued delivery.
* **Payload Style**: Keep payloads primitive (IDs, paths) so receivers fetch fresh data from `AppState`.
* **Naming Convention**: Verb‑noun (`slideSelected`) for state change, noun‑verb (`keywordMerged`) for action performed.
* **Testing Hooks**: Monkey‑patch a temporary `EventBus` in unit tests.
* **Error Isolation**: Keep slots short; heavy work goes to workers.
* **Documentation**: Generate an *Event Reference* via Sphinx autodoc.

### Persistent Settings – Detailed Design (added May 2 2025)

* **Objective**: Remember user preferences and last session state without polluting the project database.
* ... (rest unchanged) ...
* **Unit Tests**: Use `QSettings.setPath()` to redirect I/O to a temp dir during tests.

### Logging & Crash Handling – Detailed Design (added May 2 2025)

* **Purpose**: Capture diagnostic information for debugging while providing a graceful experience when unexpected errors occur.
* **Logging Setup**:

  ```python
  import logging, pathlib, appdirs
  LOG_DIR = pathlib.Path(appdirs.user_data_dir("pptx‑manager", "mama‑ai")) / "logs"
  LOG_DIR.mkdir(parents=True, exist_ok=True)

  logging.basicConfig(
      level=logging.INFO,
      handlers=[
          logging.handlers.RotatingFileHandler(
              LOG_DIR / "app.log", maxBytes=2*1024*1024, backupCount=5
          ),
          logging.StreamHandler()  # console (removed in packaged build)
      ],
      format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
  )
  ```

  * **Levels**: Default `INFO`; enable `DEBUG` via `--verbose` CLI flag or a hidden setting.
  * **Module Hierarchy**: Use `logger = logging.getLogger(__name__)` in each module so output can be filtered per subsystem.
  * **Log Rotation**: 5 backups of 2 MB each (\~10 MB total). Older files auto‑purged.
* **Crash Handler**:

  ```python
  import sys, traceback
  from PySide6.QtWidgets import QMessageBox

  def excepthook(exc_type, exc_value, exc_tb):
      logging.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
      err_txt = "
  ```

".join(traceback.format\_exception(exc\_type, exc\_value, exc\_tb)) QMessageBox.critical(None, "Unexpected Error", "An unexpected error occurred. The application will exit.

"+ f"A log file was written to: {LOG\_DIR / 'app.log'}") sys.exit(1)

sys.excepthook = excepthook

````
- Shows a friendly dialog; writes full traceback to `app.log`.
- **Recovery**: Optionally offer a “Restart App” button that calls `QProcess.startDetached(sys.executable, sys.argv)`.
- **Thread Exceptions**: Worker threads should wrap tasks and emit `errorOccurred(str)` back to the GUI; main thread shows a non‑modal toast.
- **External Reporting (Optional)**: Hook into Sentry or Bugsnag via DSN read from environment; send anonymized stack traces.
- **Testing**: Use `caplog` in `pytest` to assert specific warnings are logged; simulate an unhandled exception and verify dialog suppression under `pytest‑qt`.
- **User Support**: Add a “Show Logs” menu item that opens the log directory in Explorer so users can attach logs to bug reports.
py`; every widget imports and connects/ emits.
- **Queued Connections**: When emitting from worker threads, force queued delivery:
```python
event_bus.thumbnailReady.emit(slide_id)            # auto‑queued
````

* **Payload Style**: Prefer *primitive* payloads (IDs, paths) so receivers can fetch fresh data from `AppState`, avoiding stale copies.
* **Naming Convention**: Verb‑noun (`slideSelected`) for “state change”, noun‑verb (`keywordMerged`) for “action performed”.
* **Testing Hooks**: In unit tests, create a temporary `EventBus()` instance and monkey‑patch it in modules under test to assert emissions without GUI.
* **Error Isolation**: Slots should be short; heavy work belongs in separate workers to prevent one faulty handler from blocking the bus.
* **Documentation**: Auto‑generate an *Event Reference* table in your README via Sphinx autodoc so new contributors see available signals.

### Accessibility Checks – Detailed Design (added May 2 2025)

* **Keyboard‑First Navigation**

  * Ensure a logical `tab` order: set `setTabOrder()` after UI creation or override `focusNextPrevChild()` in custom widgets.
  * Provide dedicated shortcuts for core actions (Ctrl + N New Project, Ctrl + O Open, Ctrl + S Save, Ctrl + Z Undo, Ctrl + Y Redo, Ctrl + F Search, Alt + 1…5 to jump between pages).
  * Display shortcuts in tooltips and menu texts (e.g., “Save 	Ctrl+S”).
* **Focus Indicators**

  * Style `:focus` in QSS with a clear outline (min 2 px) that meets WCAG‑AA contrast vs. background.
* **High‑DPI & Scaling**

  * Enable `Qt.AA_EnableHighDpiScaling` and `Qt.AA_UseHighDpiPixmaps` in `QApplication.setAttribute()` before construction.
  * Vector icons (SVG) via the `.qrc`; avoid baked‑in @2x PNGs.
* **Color Contrast & Themes**

  * Verify both light/dark palettes with a contrast checker (≥ 4.5:1 for text). Adjust Dracula purples if needed.
  * Allow a per‑widget override in QSS for “accessible highlight” color.
* **Screen Reader Support**

  * Set `setAccessibleName()` and `setAccessibleDescription()` on custom buttons and panels.
  * Provide meaningful `accessibleText` for slide thumbnails (“Slide 3: Market Share Pie Chart”).
* **Resizable Text & UI**

  * Base fonts on `QApplication.font()` and respond to `fontChanged` to rescale.
  * Expose a “UI Scale” slider (90 % – 125 %) that multiplies `QFont.pointSizeF()`.
* **Error & Status Feedback**

  * Use `QStatusBar` or non‑modal toasts for transient messages; ensure they are also logged.
  * Provide color‑blind‑safe icons (dual encoding: icon + label).
* **Testing Toolkit**

  * Use automated a11y checks with `axe‑core` via `qt‑accessibility‑inspector` (if available) or manual NVDA/Windows Narrator passes.
  * Add a CI job that runs headless `pytest‑qt` to walk the tab order and assert no widget is skipped.

### Unit‑Test Hooks – Detailed Design (added May 2 2025)

* **Objectives**

  * Validate core logic (DB I/O, keyword merge, geometry math, versioning) without spinning up the full GUI.
  * Provide smoke/UI tests to catch broken signal routing or regressions in drag‑and‑drop.
* **Testing Stack**

  | Layer                | Tooling                                      |
  | -------------------- | -------------------------------------------- |
  | Pure‑Python logic    | `pytest`, `pytest‑cov`                       |
  | Qt widgets & signals | `pytest‑qt` (`qtbot`)                        |
  | CLI / end‑to‑end     | `subprocess` + packaged EXE in CI (optional) |
* **Project Layout**

  ```text
  project_root/
  ├─ src/
  ├─ tests/
  │   ├─ unit/
  │   ├─ gui/
  │   └─ data/  # sample pptx, sqlite fixtures
  └─ pyproject.toml  # [tool.pytest.ini_options]
  ```
* **Key Fixtures**

  | Fixture       | Scope    | Purpose                                                                              |
  | ------------- | -------- | ------------------------------------------------------------------------------------ |
  | `tmp_db`      | function | Creates a fresh SQLite in `tmp_path` and injects into `database.py` via monkeypatch. |
  | `app_state`   | function | Calls `AppState.reset()` before each test.                                           |
  | `bus`         | function | Instantiates a fresh `EventBus`; monkey‑patches global import sites.                 |
  | `qtbot`       | function | Provided by `pytest‑qt` for simulating clicks/keys.                                  |
  | `sample_pptx` | session  | Copies a small deck from `tests/data` for slide parsing tests.                       |
* **Mocking External Libs**

  * Use `unittest.mock` to stub `python-pptx` objects (e.g., `Shape`, `Slide`) so keyword logic tests don’t need actual files.
  * Mock `win32com.client.Dispatch("PowerPoint.Application")` in modules that export slides.
* **Testing Asynchronous Logic**

  * Replace `QThreadPool.start` with a synchronous lambda in unit tests; verify signal emission with `QtTest.QSignalSpy`.
* **Coverage Targets**

  * ≥ 85 % on `core/` (keyword merge, DB helper, undo commands).
  * Smoke tests open each main page, trigger a sample action, and assert no exceptions.
* **Continuous Integration (minimal MVP)**

  * GitHub Actions workflow `python-tests.yml` on `push`/`PR`:

    ```yaml
    jobs:
      test:
        runs-on: windows-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
            with: {python-version: '3.9'}
          - name: Install deps
            run: pip install -r requirements_dev.txt
          - name: Run tests
            run: pytest -v --cov=src --cov-report=xml
          - uses: codecov/codecov-action@v4
    ```
  * Later, append a second job `build` that runs the PyInstaller spec *after* tests pass.
* **Developer Ergonomics**

  * `pre-commit` hook runs `pytest -q` on staged files touching `src/`.
  * `make test` shortcut in a `Makefile` or `tasks.py` (Invoke).

### Third‑Party Dependencies – Detailed Inventory (added May 2 2025)

* **Runtime Libraries**

  | Package                         | Version / Wheel   | Notes                                                                                                                                 |
  | ------------------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
  | Python                          | **3.9.x**         | Chosen for stability with PySide6 and Win32 COM; ensure 64‑bit installer to match Office.                                             |
  | PySide6                         | 6.5–6.7           | MIT‑licensed; brings Qt DLLs. Copy `platforms/`, `styles/`, `svg/`, and `imageformats/` plugins into the PyInstaller `collect` phase. |
  | python‑pptx                     | latest (≥ 0.6.23) | Pure‑Python; handles slide XML. Requires `lxml`, `Pillow`.                                                                            |
  | win32com / pywin32              | 305+              | Needed for PowerPoint automation; auto‑included wheel has `pyd` compiled for cp39‑win\_amd64. Office 2016+ must be present.           |
  | Pillow                          | 10.x              | For thumbnail generation.                                                                                                             |
  | rapidfuzz                       | 3.x cp39 wheel    | C++ extension; ensure the compiled `.pyd` is collected.                                                                               |
  | appdirs                         | 1.4               | For cross‑platform log & cache paths.                                                                                                 |
  | pytest / pytest‑qt / pytest‑cov | dev‑only          | Excluded by PyInstaller via `--exclude-module`.                                                                                       |
  | PyInstaller                     | 6.x               | Build spec sets `--noconsole` in release, collects DLLs.                                                                              |

* **DLL / External Requirements**

  * **Microsoft Visual C++ Redistributable 2015–2022 (x64)** – bundled by Office and many systems; add installer link in README.
  * **MS Office PowerPoint (Desktop)** – user must have it for COM automation; detect via registry and show a setup wizard step.

* **PyInstaller Spec Highlights**

  ```python
  a = Analysis(…
      binaries=[('C:/Windows/System32/WindowsCodecs.dll', 'dlls')],
      datas=[('assets/qss/*', 'assets/qss'), ('resources.qrc', '.')],
      hiddenimports=['win32com', 'win32com.client', 'rapidfuzz.fuzz'],
  )
  coll = COLLECT(a, …)
  ```

  * Use `pyi-hooks/hook-rapidfuzz.py` to include the `.pyd`.
  * Run `--add-binary` for `platforms/qwindows.dll`, etc.

* **License Compliance**

  * All listed packages are BSD/MIT or PSF‑licensed; include `THIRD_PARTY_LICENSES.txt` generated via `pip‑licenses`.

* **Upgrade Strategy**

  * Add `dependabot` config for `requirements.txt` but lock major versions in the CI matrix.
  * Pin exact versions in `requirements_dev.txt`; rely on PyInstaller build log to confirm collected modules.

## Initial SQLite Schema – Draft (v0.1, May 2 2025)

(See ERD diagram below for relationships.)

```sql
-- PROJECT‑LEVEL METADATA
CREATE TABLE projects (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    folder_path   TEXT    NOT NULL UNIQUE,
    created_at    TEXT    DEFAULT (datetime('now')),
    updated_at    TEXT    DEFAULT (datetime('now') ON UPDATE CURRENT_TIMESTAMP)
);

-- ORIGINAL FILES ADDED TO EACH PROJECT
CREATE TABLE files (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id    INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename      TEXT    NOT NULL,
    rel_path      TEXT    NOT NULL,
    slide_count   INTEGER,
    checksum      TEXT,
    UNIQUE(project_id, rel_path)
);

-- SLIDES (one row per slide); slide‑level tags stored via slide_keywords table
CREATE TABLE slides (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id       INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    slide_index   INTEGER NOT NULL,
    thumb_path    TEXT,
    UNIQUE(file_id, slide_index)
);

-- ELEMENTS inside a slide; element‑level tags stored via element_keywords table
CREATE TABLE elements (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    slide_id      INTEGER NOT NULL REFERENCES slides(id) ON DELETE CASCADE,
    element_type  TEXT    NOT NULL,
    bbox_x        REAL    NOT NULL,
    bbox_y        REAL    NOT NULL,
    bbox_w        REAL    NOT NULL,
    bbox_h        REAL    NOT NULL
);

-- KEYWORD CANONICAL LIST (deduped)
CREATE TABLE keywords (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword       TEXT    NOT NULL COLLATE NOCASE UNIQUE,
    kind          TEXT    NOT NULL CHECK (kind IN ('topic','title','name'))
);

-- MANY‑TO‑MANY LINK TABLES
CREATE TABLE slide_keywords (
    slide_id      INTEGER NOT NULL REFERENCES slides(id)    ON DELETE CASCADE,
    keyword_id    INTEGER NOT NULL REFERENCES keywords(id)  ON DELETE CASCADE,
    PRIMARY KEY (slide_id, keyword_id)
);

CREATE TABLE element_keywords (
    element_id    INTEGER NOT NULL REFERENCES elements(id)  ON DELETE CASCADE,
    keyword_id    INTEGER NOT NULL REFERENCES keywords(id)  ON DELETE CASCADE,
    PRIMARY KEY (element_id, keyword_id)
);
```

*Update (May 2 2025):* single‑value columns `topic_tag`, `title_tag`, and `name_tag` have been **removed** in favor of storing **multiple** tags exclusively through the many‑to‑many tables above.

### Entity‑Relationship Diagram (ERD v0.1)

A PNG diagram has been generated. [Download the ERD](sandbox:/mnt/data/erd_v0_1.png)

```
projects 1───N files 1───N slides 1───N elements
      │                     │                │
      │                     └───N slide_keywords N───1 keywords
      │                                      │
      └─────────────────────────────N element_keywords N───┘
```

### Notes & Next Steps

1. **Indices** – Add ... (unchanged)

---

## Page Design – Projects (Landing) Page (added May 2 2025)

### 1. Purpose & Responsibilities

* Entry point of the application.
* Create a **new project** (copy selected .pptx files into a project folder and seed the DB).
* List **existing projects** with quick metadata and open/rename/delete actions.
* Surface **recent projects** from `QSettings` MRU list.
* Validate disk space, check duplicate names, and emit `projectLoaded` on success.

### 2. Layout & Widgets (desktop view)

```
┌───────────────────────────────────── Projects Page ─────────────────────────────────────┐
│ Toolbar:  New (Ctrl+N)  |  Open (Ctrl+O)  |  Refresh  |  Disk Space: 120 GB free        │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ [QListView] Existing Projects (left 35 %)     │  [QStackedWidget] Right‑side panel      │
│  • Q2_Pitch_Deck   2025‑04‑15  3 files  72 slides │  ◦ Welcome placeholder (no project)   │
│  • Investor_Update 2025‑03‑08  1 file   18 slides │  ◦ New‑Project wizard (step 1/2)      │
│  • …                                            │  ◦ Project summary card                │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ StatusBar: "Ready"  |  ProgressBar (file copy)                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

* **Toolbar**: `QToolButton`s with SVG icons; wired to `NewProjectAction`, `OpenProjectAction`, `RefreshAction`.
* **Project List** (`QListView` + `QAbstractListModel`): shows project name, last modified, slide count. Context menu: Open, Rename, Delete.
* **Right Panel** (`QStackedWidget` inside page):

  * *Welcome card* when no selection.
  * *New‑Project Wizard* (Step 1: select files → Step 2: choose project name & folder).
  * *Summary card* for the currently highlighted project (thumbnail grid of included decks).
* **StatusBar**: shows copy progress, free‑space warning, undo/redo tips.

### 3. Key Signals & Event Flow

| Emitter           | Signal           | Payload          | Listener(s)            | Outcome                                                         |
| ----------------- | ---------------- | ---------------- | ---------------------- | --------------------------------------------------------------- |
| NewProjectWizard  | `projectCreated` | `project_path`   | AppState → EventBus    | Inserts DB rows; sets `current_project`; emits `projectLoaded`. |
| ProjectList model | `rowsInserted`   | QModelIndex      | StatusBar              | "Project added" toast.                                          |
| Rename dialog     | `projectRenamed` | `(id, new_name)` | DB service, List model | Updates DB & view; pushes `RenameProjectCmd`.                   |
| Delete action     | `projectDeleted` | `id`             | DB service             | Removes folder & DB rows; pushes `DeleteProjectCmd`.            |

### 4. Undo / Redo Commands (examples)

| Command            | redo()                                    | undo()                            |
| ------------------ | ----------------------------------------- | --------------------------------- |
| `CreateProjectCmd` | insert project row, copy files            | delete project row, remove folder |
| `RenameProjectCmd` | update name in DB & folder                | revert name                       |
| `DeleteProjectCmd` | move folder to temp trash, delete DB rows | restore folder, reinsert rows     |

### 5. Services & Helpers

* `ProjectService.create(name, file_paths)` → returns `ProjectModel`, runs copy in background thread; emits progress (%) to StatusBar.
* `DiskUtil.ensure_space(required_bytes)` – raises if < 2 × required.
* \`\` – runs PowerPoint‑COM export in a dedicated worker (STA thread or external process); streams per‑slide progress to EventBus; can be cancelled/resumed.
* `FileWatcher` (optional) – monitors project folder for external changes (v1.x).

### 6. Edge‑Case Handling

* **Duplicate Names**: auto‑append `(2)` or prompt user.
* **Long File Paths** (> 255 chars on Windows): warn and shorten folder name.
* **Interrupted Copy/Conversion**: file copy and slide conversion run in a temp dir; only when both succeed does the folder get renamed to final project path.
* **Cancel / Resume**: if the user cancels the conversion, partial PNGs are removed and DB rows rolled back.

### 7. Slide Conversion Pipeline (new)

1. **Trigger** – Immediately after file copy in `CreateProjectCmd`, `ProjectService` schedules `SlideConverter`.
2. **Worker** – `SlideConverter` starts a single background task using `pythoncom.CoInitialize()` inside a dedicated `QThread` (STA) *or* spawns an external helper process to avoid COM issues.
3. **Progress Reporting** – Emits `conversionProgress(file_id, slide_idx, total)` every slide. StatusBar shows a determinate progress bar; the Project List item also displays a small spinner and percentage.
4. **Incremental Availability** – Thumbnails are written slide‑by‑slide; the user may proceed to the SlideView page as soon as the first few slides are ready (lazy loading continues in background).
5. **Completion** – On 100 %, `SlideConverter` emits `conversionFinished(project_id)`. AppState flips `project.ready = True`; navigation buttons to SlideView unlock.
6. **Error Handling** – If PowerPoint crashes or COM errors occur, the worker emits `conversionError(msg)`; UI shows retry/cancel; logs capture `ppt_err_###.log`.

### 8. Extension Points

* Hook to import ZIP of decks in bulk.
* Right‑click “Export Project Bundle” for shareability (v1.x). . Extension Points
* Hook to import ZIP of decks in bulk.
* Right‑click “Export Project Bundle” for shareability (v1.x).

---

## Page Design – SlideView/Keywords Page (added May 2 2025)

### 1. Purpose & Responsibilities

* Display slides of the current project and let the user navigate them.
* Let the user assign **topic/title** tags to whole slides and **name** tags to individual elements (images, charts, tables, text blocks).
* Provide visual feedback (thumbnail strip, element highlight rectangles) and store all tags in the DB.

### 2. Layout & Widgets (desktop view)

```
┌──────────────────────────────────── SlideView / Keywords ────────────────────────────────┐
│ Toolbar:  ◀ Prev  |  ▶ Next  |  Zoom 100 % ▼  |  Fit  |  Find (Ctrl+F)                  │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ QSplitter ───────────────────────────────────────────────────────────────────────────────│
│ │ Left pane (70 %)                                     │  Right pane (30 %)             │
│ │ ┌────────────── SlideCanvas (QGraphicsView) ─────────┐│  ┌──── Keyword Panel ────┐   │
│ │ │                                                    ││  │ Slide Keywords        │   │
│ │ │  [rendered slide image, selectable shapes]         ││  │  • **Topic(s)**:  [TagEdit]  │   │
│ │ │                                                    ││  │  • **Title(s)**:  [TagEdit]  │   │
│ │ └─────────────────────────────────────────────────────┘│  ├───────────┬──────────┤   │
│ │ ┌── ThumbnailsBar (QListView horizontal) ────────────┐│  │ Element Keywords      │   │
│ │ │ [thumb][thumb][thumb] …                            ││  │  • Selected element:  │   │
│ │ └─────────────────────────────────────────────────────┘│  │    • **Name tag(s)**  [TagEdit]  │   │
│ └───────────────────────────────────────────────────────┘│  └────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

* **SlideCanvas**: custom `QGraphicsView` that draws the slide pixmap plus an overlay `QGraphicsRectItem` for each detected shape; clicking fires `elementClicked(element_id)`.
* **ThumbnailsBar**: `QListView` with `QHBoxLayout` delegate; infinite‑scroll with lazy fetch.
* **Keyword Panel**: two subsections: *Slide* and *Element*; each uses a `TagEdit` (chips‑style) widget powered by `QCompleter` from the keywords table.

### 3. Key Signals & Event Flow

| Emitter       | Signal                    | Payload            | Listener(s)               | Outcome                                                                              |
| ------------- | ------------------------- | ------------------ | ------------------------- | ------------------------------------------------------------------------------------ |
| ThumbnailsBar | `slideSelected`           | `slide_id`         | SlideCanvas, KeywordPanel | Loads pixmap & tags; updates UI.                                                     |
| SlideCanvas   | `elementClicked`          | `element_id`       | KeywordPanel              | Highlights shape; loads element tags.                                                |
| KeywordPanel  | `addSlideKeyword(topic)`  | `(slide_id, kw)`   | DB service                | Inserts into `slide_keywords`; pushes `AddSlideKeywordCmd`; emits `keywordsChanged`. |
| KeywordPanel  | `addElementKeyword(name)` | `(element_id, kw)` | DB service                | Inserts into `element_keywords`; pushes `AddElementKeywordCmd`.                      |
| EventBus      | `keywordsChanged`         | `slide_id`         | ThumbnailsBar             | Refresh keyword badges on thumbs.                                                    |

### 4. Undo / Redo Commands

| Command                    | redo()                             | undo()        |
| -------------------------- | ---------------------------------- | ------------- |
| `AddSlideKeywordCmd`       | insert row into `slide_keywords`   | delete row    |
| `RemoveSlideKeywordCmd`    | delete row                         | re‑insert row |
| `AddElementKeywordCmd`     | insert row into `element_keywords` | delete row    |
| `RenameKeywordCmd` (merge) | update `keywords.keyword`          | revert text   |

### 5. Services & Helpers

* **SlideRenderer**: caches rendered slide pixmaps at multiple zoom levels (via Pillow); runs in `QThreadPool`.
* **ShapeDetector**: uses `python-pptx` to enumerate shapes, returns list of bounding boxes and `element_id`s.
* **KeywordService**: high‑level CRUD wrapper around keyword tables; provides fuzzy‑match suggestions.

### 6. Edge‑Case Handling

* **Overlapping shapes**: cycle selection on repeated clicks; show info tip “Tab to cycle elements under cursor”.
* **Multiple files**: prepend file alias to slide number in thumbnail tooltip (e.g., `Marketing_v2.pptx – Slide 7`).
* **Long keyword text**: elide chips visually; full text in tooltip.

### 7. Extension Points

* Live **fuzzy‑merge suggestions** banner when user types a near‑duplicate keyword.
* **Annotation layer**: allow drawing rectangles/freehand to mark regions (v1.x).
* **Slide notes panel**: show PowerPoint speaker notes (v1.x).

---

## Page Design – Keyword Manager Page (added May 2 2025)

### 1. Purpose & Responsibilities

* Provide an overview of all slide‑level and element‑level keywords in the current project.
* Enable bulk editing, renaming, and **fuzzy merge** of near‑duplicate keywords.

### 2. Layout & Widgets

```
┌───────────────────────────────────────── Keyword Manager ───────────────────────────────┐
│ Filter 🔍 [text]  |  Kind ⌄  (topic/title/name)  |  Unused ☐  |  Export CSV            │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ QSplitter ───────────────────────────────────────────────────────────────────────────────│
│ │ Left pane (60 %)                                  │  Right pane (40 %)               │
│ │ ┌── Slide‑Keyword Table (QTableView) ────────────┐│  ┌── Fuzzy Merge Panel ───────┐ │
│ │ │ Thumb | Slide # | Topic(s) | Title(s) | …      ││  │ Suggestion List            │ │
│ │ │ ----- | ------- | -------- | -------- |        ││  │  • "Revenue"  ↦ "Revenue"  │ │
│ │ └─────────────────────────────────────────────────┘│  │  • "revenue"  ↦ "Revenue"  │ │
│ │ Editing Widget (below table): TagEdit rows         │  │  [Merge Selected] [Ignore] │ │
│ └────────────────────────────────────────────────────┘│  └────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

* **Slide‑Keyword Table**: custom model joining `slides` + aggregated keywords; inline editing triggers `EditSlideKeywordsCmd`.
* **Fuzzy Merge Panel**: background job computes Levenshtein < 80 %; user selects rows to merge.

### 3. Key Signals & Event Flow

| Emitter    | Signal              | Payload                     | Listener(s)    | Outcome                                                                   |
| ---------- | ------------------- | --------------------------- | -------------- | ------------------------------------------------------------------------- |
| Table      | `keywordCellEdited` | `(slide_id, kind, new_set)` | DB service     | Updates link tables; pushes `EditSlideKeywordsCmd`.                       |
| FuzzyPanel | `mergeRequested`    | `(old_kw_id, new_kw_id)`    | KeywordService | Updates `keywords` row; pushes `RenameKeywordCmd`; emits `keywordMerged`. |
| Filter bar | `filterChanged`     | text                        | Table model    | Re‑query; refresh view.                                                   |

### 4. Undo / Redo Commands

`EditSlideKeywordsCmd`, `RenameKeywordCmd`, `MergeKeywordsCmd` (batch).

### 5. Edge‑Case Handling

* Prevent merging keywords of different **kind**.
* Show count of slides impacted before merge confirmation.

### 6. Extension Points

* Export full keyword list to CSV / Excel.
* Heat‑map column: how often a keyword appears.

---

## Page Design – Assembly Manager Page (added May 2 2025)

### 1. Purpose & Responsibilities

* Let users build a slide set by searching/selecting keywords and previewing matching slides.
* Support multi‑keyword queries (AND/OR), cross‑project mode, and curated ordering.

### 2. Layout & Widgets

```
┌──────────────────────────────────────────── Assembly Manager ────────────────────────────┐
│ Left Panel (25 %): Keyword Search & Basket          │  Middle Preview (35 %) │ Right (40 %) │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  Keyword Search 🔍 [text]      [Kind ⌄] [Project ⌄]                                     │
│  Results ListView  (double‑click → add)                                                │
│  Basket List (selected keywords)   [Clear]                                             │
│                                                                                        │
│ │ Slide Preview: QListView grid                                                       │
│ │  • thumb • thumb • thumb … (matches current keyword)                               │
│ │ Click → enlarge QDialog                                                             │
│                                                                                        │
│ │ Final Slide Set ListView (thumbnails)                                               │
│ │  Drag to re‑order or Delete                                                         │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3. Key Signals & Event Flow

| Emitter       | Signal            | Payload              | Listener(s)   | Outcome                       |
| ------------- | ----------------- | -------------------- | ------------- | ----------------------------- |
| KeywordSearch | `keywordSelected` | `(kw_id)`            | PreviewModel  | Runs query; loads thumbnails. |
| Basket        | `basketUpdated`   | list\[kw\_id]        | FinalSetModel | Re‑build slide pool union.    |
| FinalSetView  | `slideReordered`  | `(old_idx, new_idx)` | UndoStack     | Push `ReorderSlideCmd`.       |
| FinalSetView  | `slideRemoved`    | `slide_id`           | Model         | Push `RemoveFromSetCmd`.      |

### 4. Undo / Redo Commands

`AddToSetCmd`, `RemoveFromSetCmd`, `ReorderSlideCmd`.

### 5. Edge‑Case Handling

* Duplicate slides from different files → flag duplicates with badge.
* Keyword basket empty → disable middle preview.

### 6. Extension Points

* Boolean query builder (AND/OR/NOT) for keywords.
* Weighting: rank slides by number of matched keywords.

---

## Page Design – Delivery Page (added May 2 2025)

### 1. Purpose & Responsibilities

* Review the curated slide set, adjust order & size, then export.
* Export options: open in PowerPoint, save as new .pptx, or export selected slides as images/PDF.

### 2. Layout & Widgets

```
┌────────────────────────────────────────────── Delivery ──────────────────────────────────┐
│ Toolbar:  Thumbnail Size ▲▼  |  Sort ⌄  |  Open in PowerPoint  |  Save As PPTX          │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ Final Slide List (QListView horizontal, icon mode); supports drag‑reorder, multiselect. │
│ Zoom slider bottom‑right; status shows "15 slides • 24 MB"                               │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3. Key Signals & Event Flow

| Emitter       | Signal            | Payload                    | Listener(s)   | Outcome                                        |
| ------------- | ----------------- | -------------------------- | ------------- | ---------------------------------------------- |
| ListView      | `orderChanged`    | list\[slide\_id] new order | Model         | Push `ReorderSlideCmd`; update counter.        |
| Toolbar Save  | `exportRequested` | format (`pptx`/`pdf`)      | ExportService | Runs background export; progress in StatusBar. |
| ExportService | `exportFinished`  | path                       | EventBus      | Show "Open Folder" toast.                      |

### 4. Undo / Redo Commands

`ReorderSlideCmd`, `RemoveSlideCmd`.

### 5. Services & Helpers

* **ExportService**: uses `python-pptx` or PowerPoint COM to assemble new deck; supports PDF export via `ExportAsFixedFormat`.

### 6. Edge‑Case Handling

* Slides deleted in original project after assembly → warn & offer to remove missing slides.
* Export to existing filename → prompt overwrite or auto‑increment.

### 7. Extension Points

* Export to Google Slides via Slides API.
* One‑click email draft with exported deck attached.
