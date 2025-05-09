# PPTX Manager – Software‑Architecture Overview

## 1. High‑Level Pattern

┌────────────┐     signals     ┌────────────┐
│   UI / Qt  │ ───────────────▶│  AppState  │
└────────────┘◀─────────────── └────────────┘
        │ data / commands                ▲
        ▼                                │
┌──────────────────┐     services    ┌───────────────┐
│ QUndoCommands    │ ───────────────▶│   Services    │
└──────────────────┘◀─────────────── └───────────────┘
        │                                    ▲
        ▼ SQL / DTOs                         │ COM
┌──────────────────┐                 ┌─────────────────┐
│ SQLite Database  │                 │ PowerPoint COM  │
└──────────────────┘                 └─────────────────┘



* **Presentation** – Qt widgets & pages (left‑rail nav + `QStackedWidget`).
* **State / Orchestration** – `AppState` singleton and `EventBus` (Qt signals).
* **Business Logic** – headless `services/` modules (database, file IO, slide conversion, cache).
* **Persistence** – SQLite v3.41, schema in `/services/database.py`.
* **Integration** – COM automation via `pythoncom` to export slides to PNG.

## 2. Core Modules

| Module | Purpose | Key Classes / Functions |
|--------|---------|-------------------------|
| `ui/` | Interactive pages & reusable widgets | `MainWindow`, `ProjectsPage`, `TagEdit`, `SlideThumbnailWidget` |
| `app_state.py` | Session‑wide mutable data & QUndoStack | `AppState(QObject)` |
| `event_bus.py` | Global Qt signals | `conversionProgress(int,int)`, `keywordsChanged(int)` |
| `services/database.py` | CRUD, migrations, FTS5 search | `Database`, `create_tables()` |
| `services/slide_converter.py` | PPTX→PNG in background thread | `SlideConverter(QRunnable)` |
| `services/thumbnail_cache.py` | Lazy generation & memory/disk cache | `ThumbnailCache` |
| `commands/` | Undoable domain actions | `AddKeywordCmd`, `MergeKeywordsCmd`, `ReorderSlidesCmd` |
| `models/` | Pure dataclasses | `Project`, `Slide`, `Keyword`, `ElementBBox` |
| `resources/` | Icons, `.qss`, `.qrc` | `dark.qss`, `light.qss`, `resources_rc.py` |

## 3. Data Flow Example – “Add keyword to element”

1. **User action** – Clicks shape → types keyword in `TagEdit`.
2. `TagEdit` emits `keywordAdded(element_id, text)` to its page.
3. Page constructs `AddKeywordCmd(element_id, text)` and pushes to `AppState.undo_stack`.
4. `AddKeywordCmd.redo()` calls `services.database.add_element_keyword()`.
5. Database notifies via `EventBus.keywordsChanged(element_id)`.
6. `SlideViewPage` listens and refreshes its right‑hand keyword panel.
7. UI instantly reflects undo/redo.

## 4. Concurrency & Responsiveness

* **Slide conversion** runs in `QThreadPool` with **queued‑signal** updates:
  `conversionProgress(file_id, percent)` → progress bar per file.
* **Thumbnail generation** is demand‑driven; cache returns placeholder,
  computes async, then signals `thumbnailReady(slide_id)`.
* **DB access** is synchronous within service threads; long searches use FTS5 and emit results incrementally.

## 5. Undo / Redo Strategy

* Central `QUndoStack` lives in `AppState`.
* Each business operation has a matching `QUndoCommand` with symmetrical
  `redo()/undo()` that wrap DB transactions.
* Stack length persisted in `QSettings` on shutdown → restores on startup.

## 6. Persistence & Migration

* **Schema**: `projects`, `files`, `slides`, `elements`, `keywords`,
  link tables `slide_keywords`, `element_keywords`.
* **Migrations**: simple `PRAGMA user_version` check on startup
  → run incremental SQL scripts in `/migrations/`.
* **Back‑ups**: optional “Export Project” copies project folder + DB slice.

## 7. Packaging & Updates

* **PyInstaller** one‑folder build, Windows‑first.
* Updater checks GitHub Releases JSON; if a newer EXE appears,
  downloads to `%LOCALAPPDATA%\pptx‑manager\updates`, verifies SHA‑256,
  swaps on next launch.

## 8. Extension Hooks (v2 Roadmap)

* AI tagging service → new module `services/ai_tag_suggester.py`.
* Cloud sync via WebDAV → plug into `services/file_io.py` as strategy.
* Plug‑in API – Qt `QPluginLoader` scanning `/plugins/`.

---

*Follow the separation of concerns: UI ↔ Commands ↔ Services ↔ Data.  
This keeps tests fast and the codebase ready for upcoming v2 features.*

