# 🚧  Final Build Plan — “PPTX Manager” (PySide 6, Python 3.9, Windows‑first)

*Changes locked for v1 (MVP):*  
* • No GitHub CI/CD or formal coverage gates  
* • Testing = basic smoke tests only  
* • Shape detection = bounding‑box hit‑test  
* • Output deck naming: `_YYYY‑MM‑DD_<projectName>_assembled.pptx`  
* • Packaging via PyInstaller one‑folder build (no auto‑update)*  

---

## Phase 0 — Prep & Tooling
1. **Install toolchain**
   * Python 3.9 (x64) + venv/Poetry  
   * Visual Studio Build Tools (for PySide 6 wheels)  
   * MS PowerPoint + `pywin32`
2. **Create repo skeleton** (see repo‑layout note).
3. *(Optional)* add local pre‑commit hooks (`ruff`, `black`) for style.

# 🤖 Hands‑On Build Instructions (Agent‑Friendly)

> **Goal:** give an AI‑powered coding agent “paint‑by‑numbers” tasks for **Phases 1‑5**.  
> Each numbered **Task** is atomic. After completing it, the agent should **run** or **import** the
> module to confirm syntax, then **commit** with the task ID in the message.

---
## 📁 Naming Conventions

* **Project root**: `pptx_manager/`
* **Source root**: `pptx_manager/src/pptx_manager/`
* **Tests root**: `pptx_manager/src/pptx_manager/tests/`
* **All code uses Python 3.9, spaces for indents (4), UTF‑8**

---

## Phase 1 — Core Infrastructure  *(8 tasks)*

| ID | Task | File(s) & Exact Content |
|----|------|-------------------------|
| **1.1** | **Create package skeleton** | Generate folders exactly:<br>`src/pptx_manager/{__init__.py,app_state.py,event_bus.py}`<br>`src/pptx_manager/services/{__init__.py,database.py,slide_converter.py,thumbnail_cache.py}` |
| **1.2** | **`app_state.py` skeleton** | Define:<br>`class AppState(QObject):`<br>• `_instance` singleton<br>• attrs: `undo_stack: QUndoStack`, `current_project: Optional[int]`, `settings: QSettings`<br>• signals: `projectLoaded(int)`, `slideSelected(int)` |
| **1.3** | **`event_bus.py`** | Create `class EventBus(QObject)` (singleton). Qt signals:<br>`conversionProgress(int,int)`, `conversionFinished(int)`, `conversionError(int,str)`, `keywordsChanged(int)` |
| **1.4** | **Logging setup** | In `__init__.py` root package, configure `logging`:<br>• RotatingFileHandler to `%APPDATA%\\pptx‑manager\\logs\\app.log` (5 MB, 3 backups). |
| **1.5** | **Database schema** | In `services/database.py`:<br>``Database = sqlite3.connect(str(path));``<br>Create tables per **ERD v0.2**. Wrap in `create_tables()` function. |
| **1.6** | **Thumbnail cache stub** | `services/thumbnail_cache.py` with `get_thumb(slide_id)` returning placeholder QPixmap. Add TODO for async load. |
| **1.7** | **Slide converter stub** | `services/slide_converter.py`:<br>``class SlideConverter(QRunnable):`` constructor takes `file_id, path`; emits `EventBus.conversionProgress`; method `run()` logs “TODO COM export”. |
| **1.8** | **Smoke import test** | In `tests/test_smoke.py` import every new module and assert `True`. Run `python -m pytest -q` – must pass. |

---

## Phase 2 — Shared UI Foundations  *(7 tasks)*

| ID | Task | Instruction |
|----|------|-------------|
| **2.1** | **Copy QSS + icons** | Place `resources/qss/dark.qss` (blank) and `resources/icons/placeholder.svg`. |
| **2.2** | **`theme.py`** | Function `apply_theme(app, theme_name)` that loads `.qss` into QApplication. |
| **2.3** | **`SlideThumbnailWidget`** | `ui/components/slide_thumbnail.py` with a `QLabel` showing a pixmap, property `slide_id`. |
| **2.4** | **`TagEdit` widget** | `ui/components/tag_edit.py` subclass `QLineEdit`; method `set_tags(list[str])`; emits `tagsChanged(list[str])` on Return. |
| **2.5** | **MainWindow shell** | `ui/main_window.py`:<br>• `QMainWindow`<br>• Left `QListWidget` nav; central `QStackedWidget`.<br>• Pages placeholder widgets for each section.<br>• Hook nav selection → `stack.setCurrentIndex()`. |
| **2.6** | **`__main__.py` launcher** | Instantiate QApplication, call `apply_theme('dark')`, show `MainWindow`. |
| **2.7** | **Run manual smoke** | `python -m pptx_manager` should launch empty window without errors. |

---

## Phase 3 — Application Pages  *(10 tasks)*

| ID | Page | Key Steps (create file in `ui/pages/`) |
|----|------|----------------------------------------|
| **3.1** | **ProjectsPage** | • UI: “New Project” & “Open Project” buttons, `QTableWidget` listing projects.<br>• On “New”: `QFileDialog.getOpenFileNames` filter `*.pptx` → copy files to chosen folder via `services.file_io` (create helper).<br>• Insert project row into DB via `services.database`. |
| **3.2** | **Hook slide conversion** | After project created, loop files → `SlideConverter` to `QThreadPool.globalInstance().start()`. |
| **3.3** | **Handle conversionProgress** | ProjectsPage connects to `EventBus.conversionProgress` → update QProgressBar per file row. |
| **3.4** | **SlideViewPage** | Layout: central QLabel for slide, bottom thumb `QScrollArea`, right Tag panel (Topic/Title TagEdit). |
| **3.5** | **Bounding‑box click** | On mousePress in central QLabel, translate to slide coords, emit `elementClicked(element_id)` (use placeholder mapping). |
| **3.6** | **Add/Remove keyword commands** | `commands/add_keyword.py` & `remove_keyword.py` implement `QUndoCommand` calling DB helpers. |
| **3.7** | **KeywordManagerPage** | `QTableWidget` listing slide thumbnails + tags; right fuzzy merge panel with `QPushButton("Merge")` (dummy). |
| **3.8** | **AssemblyPage** | 3 columns: keyword search list, preview panel, basket (`QListWidget`). Drag‑drop enabled. |
| **3.9** | **DeliveryPage** | Shows basket; drag‑reorder (`internalMove`). Two buttons: “Open in PowerPoint” and “Save Deck”. |
| **3.10** | **Export deck** | Implement `save_deck(project_name)` in `services/file_io.py` → python‑pptx copy selected slides; filename `_YYYY‑MM‑DD_<project>_assembled.pptx`. |

---

## Phase 4 — Polish & Smoke Tests  *(5 tasks)*

| ID | Task | Detail |
|----|------|--------|
| **4.1** | **Undo/Redo UI** | Add toolbar with `QAction("Undo", shortcut=Ctrl+Z)` / Redo (Ctrl+Y) wired to `AppState.undo_stack`. |
| **4.2** | **Settings dialog** | `ui/components/settings_dialog.py` with two `QSpinBox` (cache MB, thumbnail size) and theme radio select. |
| **4.3** | **Accessibility sweep** | Ensure every interactive widget has `.setAccessibleName` and is reachable via Tab order. |
| **4.4** | **Smoke scenario test** | `tests/test_end_to_end.py` launches app with `pytest‑qt`’s `qtbot`, creates temp project with 1 pptx (use a 1‑slide dummy), adds keyword, exports deck, asserts output file exists. |
| **4.5** | **Manual checklist** | Provide markdown checklist in `docs/manual_test.md` with steps user performs pre‑release. |

---

## Phase 5 — Packaging  *(3 tasks)*

| ID | Task | Instruction |
|----|------|-------------|
| **5.1** | **Create PyInstaller spec** | `pptx_manager.spec` with: `hiddenimports=['pyside6','pywin32']`, add data `resources/*`. |
| **5.2** | **Build** | Run:<br>`pyinstaller --noconsole --clean pptx_manager.spec`<br>Check `dist/pptx_manager/pptx_manager.exe` launches. |
| **5.3** | **Zip for release** | Script `scripts/make_release_zip.py` zips `dist/pptx_manager` → `releases/PPTX-Manager_v1.zip`. |

---

## What the Agent Should Report

* After **each task**:  
  * “Task X.Y complete — \<one‑line summary\> — \<stdout / pytest result\>”.  
  * If error occurs, include full traceback + next proposed fix.
* After **Phase** finishes:  
  * Summary list of generated files and manual test steps.

---

### Outstanding Questions (answer before agent starts)

1. **Icon set**: Should the agent leave placeholders, or do you have real SVGs?
2. **Dummy PPTX** for tests: provide path, or let agent generate a blank via python‑pptx?
3. **Slide element mapping**: For v1, OK to treat entire slide as one “element” (simpler click handling), or keep planned bounding‑box table though COM won’t supply shape coords?

*Answer these and the agent can proceed unambiguously.*


## Phase 6 — Documentation & Launch
1. **README** — install steps, quickstart GIF, known issues (PowerPoint COM, disk‑space).
2. **Troubleshooting FAQ** — common COM errors, how to clear thumbnail cache.
3. Tag release v1.0 and share with users for feedback.

---

### v1 Scope Locked
* **No auto‑update, CI/CD, or formal unit‑test coverage metrics.**
* Focus on end‑to‑end functionality & usability.

We’re ready to start Phase 0 whenever you are!
