pptx_manager/                # repo root
├─ .gitignore
├─ README.md
├─ LICENSE
├─ pyproject.toml            # Poetry / pip‑tools – pins Python 3.9 + deps
├─ resources/
│   ├─ icons/                # SVG / PNG assets
│   ├─ qss/                  # dark.qss, light.qss
│   └─ resources.qrc         # compiled into resources_rc.py
├─ src/
│   └─ pptx_manager/         # import root (add to PYTHONPATH)
│      ├─ __main__.py        # starts MainWindow
│      ├─ app_state.py       # singleton state + QUndoStack
│      ├─ event_bus.py       # global Qt signals (conversionProgress, etc.)
│      ├─ theme.py           # loads .qss, exposes palette helpers
│      │
│      ├─ services/          # **logic with no Qt widgets**
│      │   ├─ database.py           # SQLite + migrations
│      │   ├─ file_io.py            # copy / checksum helpers
│      │   ├─ slide_converter.py    # COM: PowerPoint → PNG
│      │   └─ thumbnail_cache.py
│      │
│      ├─ models/            # pure dataclass / pydantic value objects
│      │   ├─ project.py
│      │   ├─ slide.py
│      │   └─ keyword.py
│      │
│      ├─ ui/
│      │   ├─ components/    # TagEdit, SlideThumbnailWidget, etc.
│      │   ├─ pages/         # QStackedWidget pages
│      │   │   ├─ projects_page.py
│      │   │   ├─ slideview_page.py
│      │   │   ├─ keyword_manager_page.py
│      │   │   ├─ assembly_page.py
│      │   │   └─ delivery_page.py
│      │   └─ main_window.py # left‑rail nav + stacked pages
│      │
│      ├─ commands/          # QUndoCommand subclasses
│      │   ├─ add_keyword.py
│      │   ├─ merge_keywords.py
│      │   └─ reorder_slides.py
│      │
│      └─ tests/             # pytest‑qt + unit tests
│          ├─ ui/
│          ├─ services/
│          └─ integration/
│
├─ build/                    # PyInstaller outputs (git‑ignored)
└─ .github/
   └─ workflows/
      └─ ci.yml              # lint → tests → PyInstaller (Windows, Python 3.9)


| Layer                    | Folder                         | Responsibility                         | Depends on                   |
| ------------------------ | ------------------------------ | -------------------------------------- | ---------------------------- |
| **Presentation / Pages** | `ui/pages/`, `main_window.py`  | Screens, navigation wiring             | services, models             |
| **Reusable Widgets**     | `ui/components/`               | Thumbnail, Tag editor, etc.            | QtWidgets, QtGui             |
| **Business Logic**       | `services/`                    | DB, COM slide export, caching          | *(never imports Qt widgets)* |
| **Shared State**         | `app_state.py`, `event_bus.py` | Single source of truth, global signals | QtCore                       |
| **Data Models**          | `models/`                      | Light dataclasses (no Qt)              | —                            |
| **Undo Commands**        | `commands/`                    | Encapsulate reversible operations      | services, models             |
| **Tests**                | `tests/`                       | Unit + GUI coverage (`pytest‑qt`)      | everything                   |



