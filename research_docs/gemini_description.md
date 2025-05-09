# Project SLIDEMAN: The Smart PowerPoint Library and Assembly Tool

## 1. Vision & Executive Summary

Project SLIDEMAN is envisioned as a powerful, desktop-based application for Windows users who work extensively with Microsoft PowerPoint presentations. It addresses the common challenges of managing, searching, and reusing slide content scattered across numerous `.pptx` files. By providing a centralized library with robust tagging capabilities and intuitive assembly tools, the application aims to dramatically streamline workflows for professionals who frequently create new presentations from existing materials (e.g., sales teams, consultants, educators, researchers).

The core value proposition lies in transforming a disorganized collection of presentations into a structured, searchable knowledge base. Users can import presentations into distinct "projects," assign meaningful keywords (tags) at both the slide and individual element level (like charts or images), and then rapidly find and assemble specific slides based on these tags to create new, tailored presentations with significantly less effort. The application prioritizes a modern user interface, performance, and data integrity, leveraging the power of Qt (via PySide6) and direct PowerPoint integration for high-fidelity results.

## 2. Core Philosophy & Approach

*   **Modern & Intuitive UI:** The application will adopt the visual style, theme (including light/dark modes), and interaction patterns inspired by the "Modern GUI PyDracula" project, ensuring a clean, professional, and user-friendly experience.
*   **Data Integrity Foremost:** Presentations are copied into managed project folders upon import, leaving original files untouched. All metadata (tags, element locations) is stored robustly in a dedicated SQLite database per project. Strategy includes detecting external modifications to *copied* project files to warn users or attempt reconciliation.
*   **Performance-Oriented:** Recognizing that dealing with potentially hundreds or thousands of slides requires speed, the application will heavily utilize background processing (`QThreadPool`/`QtConcurrent`), thumbnail caching, lazy loading of resources, and optimized database queries (including FTS5 indexing) to maintain a responsive UI.
*   **High-Fidelity PowerPoint Integration:** Leveraging Microsoft PowerPoint's COM automation capabilities is central to the strategy. This ensures pixel-perfect slide rendering for previews and thumbnails and allows for high-fidelity export when assembling new presentations or opening selections directly in PowerPoint.
*   **Windows First (MVP):** Due to the reliance on COM automation for core functionality (rendering, export), the initial release (MVP/v1.0) will target the Windows platform exclusively. Pre-flight checks will ensure PowerPoint is installed and accessible.
*   **Structured & Maintainable Code:** An MVC or MVVM architecture will separate concerns (UI, logic, data), promoting maintainability and scalability. Code will be organized into modules per feature area.

## 3. Key Features & Capabilities (Detailed by Page)

### 3.1. Projects (Landing Page)

*   **Purpose:** The central hub for managing distinct collections of presentations ("projects"). Serves as the application's entry point.
*   **Project Creation:**
    *   Initiate a new project via a dedicated toolbar action or wizard.
    *   Select one or multiple `.pptx` files using a file dialog.
    *   Specify a unique name for the project.
    *   The application **copies** the selected `.pptx` files into a dedicated, newly created subfolder within a user-configurable base directory. Originals remain untouched.
    *   Performs a disk space check before copying to prevent errors. Handles potential duplicate project names gracefully (e.g., append `(2)` or prompt).
    *   Seeds the project's SQLite database with initial file information.
*   **Background Slide Processing:** Immediately after file copying, a background pipeline initiates using PowerPoint COM automation:
    *   Opens each presentation invisibly.
    *   Renders each slide into a high-quality image (for thumbnails and previews).
    *   Extracts basic shape information (type, bounding box in EMUs) using `python-pptx` for later tagging.
    *   Stores slide images and shape data persistently (thumbnail caching).
    *   Provides real-time progress indication (e.g., status bar, spinners on project list items). Handles COM errors gracefully with logging and user feedback.
*   **Project Listing:**
    *   Displays all existing projects in a clear list view.
    *   Shows key metadata: Project Name, Date Modified/Created, Number of Files, Total Slide Count.
    *   Allows users to easily reopen existing projects.
    *   Provides context menu actions: Open, Rename, Delete (with confirmation, moves project folder to a temporary trash or deletes outright).
*   **Project Details:** Selecting a project in the list can display summary information in a dedicated panel (e.g., list/thumbnails of included decks).
*   **Recent Projects:** Utilizes `QSettings` to display a Most Recently Used (MRU) list for quick access.
*   **External Modification Handling:** Implements checks (e.g., file timestamp/checksum) on project load to detect if `.pptx` files *within the project folder* were modified externally. Warns the user and potentially offers a re-scan option to update metadata (slide counts, shape data), acknowledging that tags on significantly altered content might be lost.

### 3.2. SlideView / Keywords Page

*   **Purpose:** The primary interface for viewing slides within a selected project and assigning descriptive keywords (tags).
*   **Layout:** A two-pane view (using `QSplitter`):
    *   **Left Pane (Main View):**
        *   **Slide Canvas (`QGraphicsView`):** Displays the high-resolution, pre-rendered image of the currently selected slide. Supports zooming and panning. Critically, it overlays transparent, clickable rectangles (`QGraphicsRectItem`) corresponding to the detected shapes (text boxes, images, charts, etc.) based on their stored EMU bounding boxes. Clicking a shape highlights it visually.
        *   **Thumbnails Bar (`QListView`):** A horizontal, scrollable strip below the main canvas showing thumbnails of all slides in the current project's files. Supports lazy loading for performance. Clicking a thumbnail navigates to that slide. Displays identifying information (e.g., `FileName - Slide X`).
    *   **Right Pane (Keyword Panel):**
        *   **Slide-Level Keywords:** Dedicated input areas (`TagEdit` widgets with autocompletion) for assigning 'Topic' and 'Title' keywords that apply to the entire slide currently viewed. Multiple tags of each type are supported.
        *   **Element-Level Keywords:** When a shape is clicked and selected on the Slide Canvas, this section becomes active, allowing the user to assign 'Name' keywords specifically to that element (e.g., "Q2 Revenue Chart", "Competitor Logo"). Multiple name tags per element are supported.
*   **Interaction:**
    *   Navigate slides using Previous/Next buttons, clicking thumbnails, or potentially keyboard shortcuts.
    *   Clicking within the slide canvas detects the shape underneath the cursor (using the overlay rectangles) and selects it. Handles overlapping shapes (e.g., cycle selection on repeated clicks).
    *   Adding/removing tags in the Keyword Panel immediately updates the database via dedicated service calls and pushes corresponding Undo commands.
    *   Keyword input fields provide autocompletion suggestions based on existing keywords in the database (using `QCompleter`).

### 3.3. Keyword Manager Page

*   **Purpose:** Provides a project-wide overview of all assigned keywords and tools for maintaining consistency.
*   **Layout:** A two-pane view:
    *   **Left Pane (Keyword Overview & Editing):**
        *   **Slide-Keyword Table (`QTableView`):** Displays a comprehensive list of slides, showing their thumbnail, slide number/identifier, and associated 'Topic', 'Title', and aggregated 'Name' keywords. Supports sorting and filtering (e.g., by keyword text, keyword kind, slides with unused keywords).
        *   **Editing Widget:** Below the table, provides controls (likely similar `TagEdit` widgets) to edit the keywords for the currently selected slide(s) in the table, enabling bulk editing capabilities.
    *   **Right Pane (Fuzzy Merge Panel):**
        *   **Suggestion List:** Automatically detects potentially duplicate or similar keywords within the project (e.g., "Revenue" vs. "revenue", "Q1 Forecast" vs. "Q1 Forcast") using fuzzy matching algorithms (`rapidfuzz`, Levenshtein distance). Presents these as merge suggestions (e.g., "Merge 'revenue' into 'Revenue' impacting X slides/elements").
        *   **Actions:** Users can select suggestions and click "Merge Selected" to consolidate keywords (updating all references in the database) or "Ignore" to dismiss suggestions. Prevents merging keywords of different kinds (topic, title, name).
*   **Functionality:** Enables efficient clean-up of keyword inconsistencies, improving search accuracy and tag management. Allows exporting the keyword list (e.g., to CSV).

### 3.4. Assembly Manager Page

*   **Purpose:** Allows users to build a new slide sequence ("assembly") by searching for and selecting slides based on their assigned keywords, potentially across multiple projects.
*   **Layout:** A three-panel layout:
    *   **Left Panel (Keyword Search & Basket):**
        *   Search input field to find keywords. Filters allow specifying keyword kind (topic, title, name) and scope (current project or all projects).
        *   Displays search results (matching keywords). Users can select keywords (e.g., double-click, drag-and-drop) to add them to the "Basket".
        *   The Basket list shows currently selected keywords used for filtering slides. Supports multi-keyword selection (initially logical AND, potentially OR/NOT in v1.x).
    *   **Middle Panel (Slide Preview):**
        *   Displays thumbnails of all slides that match the *currently selected keyword* in the search results or basket.
        *   Allows quick visual confirmation. Clicking a thumbnail can open an enlarged preview dialog.
    *   **Right Panel (Final Slide Set):**
        *   Displays thumbnails of *all* slides associated with *any* keyword currently in the Basket. This forms the pool for the final presentation.
        *   Users can drag-and-drop thumbnails within this panel to reorder the sequence for the new presentation.
        *   Allows removing slides from the set. Flags duplicate slides if added from different sources.
*   **Functionality:** Provides a powerful way to dynamically construct presentations based on content themes or specific named elements, leveraging the tagging work done previously.

### 3.5. Delivery Page

*   **Purpose:** The final stage for reviewing the assembled slide set, making final adjustments, and exporting the result.
*   **Layout:** Primarily a large view area displaying the curated sequence of slide thumbnails from the Assembly Manager.
    *   **Thumbnail View (`QListView` in Icon Mode):** Shows the final ordered list of slides. Supports drag-and-drop reordering. Allows multi-selection for potential partial exports (v1.x).
    *   **Toolbar/Controls:**
        *   Adjust thumbnail size (slider or buttons).
        *   Sorting options (if needed beyond manual order).
        *   **"Open in PowerPoint":** Uses COM automation to create a *new*, temporary presentation in PowerPoint containing the selected slides in the specified order. Allows immediate editing or saving from PowerPoint itself.
        *   **"Save As PPTX":** Prompts the user for a file name and location (defaults to the project folder). Constructs a new `.pptx` file containing the selected slides in order. This likely uses PowerPoint COM automation (`Presentations.Add`, `Slides.InsertFromFile` or similar) to ensure high fidelity of copied slides, including master layouts and complex elements. Handles filename conflicts (prompt overwrite or auto-increment).
        *   Potentially export selected slides as images/PDF (v1.x).
*   **Functionality:** Provides the mechanism to output the curated slide set into a usable format. Checks for missing slides (if original project files were somehow altered/deleted after assembly) and warns the user.

## 4. Cross-Cutting Features & Capabilities

*   **Visual Style & Theming:** Consistent application-wide theme based on PyDracula QSS, supporting both Light and Dark modes via a toggle, managed centrally. Uses SVG icons for high-DPI scaling.
*   **Data Management:**
    *   Uses SQLite for robust, file-based storage of all project metadata.
    *   Schema includes tables for projects, files, slides, elements (with EMU bounding boxes), keywords, and many-to-many link tables.
    *   Uses `ON DELETE CASCADE` for maintaining relational integrity.
    *   Planned FTS5 indexes for efficient keyword searching.
*   **Performance:**
    *   Aggressive thumbnail caching (generate once, store persistently).
    *   Lazy loading of thumbnails and potentially other resources in list/table views.
    *   Background threads (`QThreadPool`) for file copying, slide conversion/rendering (via COM), database operations, and fuzzy keyword analysis, ensuring UI responsiveness.
*   **Tagging System:** Supports three distinct keyword types ('topic', 'title' for slides; 'name' for elements) stored in a normalized structure, allowing multi-tagging.
*   **Search:** Core keyword search functionality in Assembly Manager. Potential for a unified global search bar (v1.x) and optional full-text slide content search (v1.x).
*   **Undo/Redo:** Robust undo/redo capabilities implemented using `QUndoStack` and the Command pattern for actions like project creation/deletion, keyword assignment/removal, merging keywords, and reordering slides in Assembly/Delivery.
*   **Error Handling & Logging:**
    *   Graceful handling of unexpected application errors with a user-friendly dialog and detailed logging to rotating files.
    *   Specific error handling and logging for COM automation issues (PowerPoint crashes, object model errors).
    *   Checks for critical dependencies (PowerPoint installation) at startup or project creation.
*   **Accessibility:** Planned considerations include logical keyboard navigation (tab order), clear focus indicators, high-contrast theme compliance, screen reader support (accessible names/descriptions), and resizable UI elements.
*   **Packaging & Updates (MVP):** Distributed as a Windows application packaged using PyInstaller (with `--noconsole`). Includes a simple in-app mechanism to check for updates (version check against a server/file) and prompt the user to download a new installer.

## 5. Technical Architecture Highlights

*   **Language:** Python (targeting v3.9+ for stability with dependencies)
*   **GUI Framework:** PySide6 (v6.5-6.7 recommended)
*   **Core Libraries:**
    *   `python-pptx` (for reading `.pptx` structure, shape enumeration)
    *   `pywin32` / `win32com` (for PowerPoint COM automation - rendering, export)
    *   `sqlite3` (built-in Python module for database)
    *   `Pillow` (image manipulation for thumbnails if needed beyond COM export)
    *   `rapidfuzz` (for fast fuzzy string matching)
    *   `appdirs` (for standard user data/log paths)
*   **Packaging:** PyInstaller

## 6. Scope & Roadmap

*   **MVP (v1.0):** Focuses on the core workflow: Project creation (copying, background conversion), SlideView with tagging (slide/element), basic Keyword Manager (viewing, manual editing), Assembly Manager (keyword search, building set), Delivery (reorder, export to PPTX/Open in PP), Undo/Redo for key actions, Light/Dark theme, Windows packaging with simple update check. Includes Fuzzy Merge panel.
*   **Should-Have (v1.x):** Unified global keyword search, optional full-text search, internationalization support (`tr()`), basic CI/CD (testing, build), reusable `SlideThumbnailWidget`.
*   **Deferred (v2+):** OCR, database migrations, cross-platform support (major refactor away from COM), advanced CI/CD, AI features, plugin API.

## 7. Target Capacity (v1.0)

*   The application aims to comfortably manage and remain performant with projects containing up to approximately **1000 slides** in total across all included `.pptx` files. Performance beyond this scale may require further optimization in later versions.