# SLIDEMAN Enhancement Report: Phase 7 - Assembly Manager Page UI Implementation

## Overview

This report details the implementation of Phase 7, Step 1 for the SLIDEMAN application: creating the basic UI skeleton for the Assembly Manager page. The Assembly Manager will enable users to search for keywords across projects, select relevant keywords, preview associated slides, and build a curated list (assembly) of desired slides.

## Files Created and Modified

### New Files Created

1. **`src/slideman/ui/pages/assembly_page.py`**
   * **Purpose**: Core implementation of the Assembly Manager UI
   * **Technical Details**:
     - Created a new `AssemblyManagerPage` class extending `QWidget`
     - Implemented `__init__` method with comprehensive UI initialization
     - Added class docstring explaining the purpose and structure
     - Configured database service connection through `app_state.db_service`
     - Added logging with proper namespaces for debugging and tracing
     - Established appropriate imports from PySide6 (QWidget, QHBoxLayout, QVBoxLayout, etc.)

### Modified Files

1. **`src/slideman/ui/main_window.py`**
   * **Purpose**: Integration of the new Assembly Manager page into the application
   * **Specific Changes**:
     - Added import statement: `from .pages.assembly_page import AssemblyManagerPage`
     - Replaced placeholder line 90: `self.stacked_widget.addWidget(QLabel("Assembly Page Placeholder"))` with functional page creation
     - Added instantiation: `self.assembly_manager_page = AssemblyManagerPage(parent=self)`
     - Added to stacked widget: `self.stacked_widget.addWidget(self.assembly_manager_page)`
   * **Why**: To integrate the new page with the existing navigation system and application structure

## Detailed Technical Implementation

### AssemblyManagerPage Structure and Components

The new Assembly Manager page (`src/slideman/ui/pages/assembly_page.py`) implements a three-panel layout using a horizontal `QSplitter` for resizable sections:

```python
# Main layout and splitter setup
main_layout = QHBoxLayout(self)
main_layout.setContentsMargins(0, 0, 0, 0)
main_layout.setSpacing(0)

# Create a splitter for resizable panels
self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
```

1. **Left Panel (Keyword Search & Basket)** - Lines 42-97
   * **Components**:
     - `QLineEdit` for search input with placeholder text
     - Two `QComboBox` widgets for filtering (Kind and Project Scope)
     - `QListView` for search results with placeholder `QStandardItemModel`
     - `QListView` for keyword basket with placeholder `QStandardItemModel`
     - `QPushButton` widgets for "Add to Basket" and "Clear Basket" actions
   * **Layout**: Vertical layout with search controls at top, results in middle, basket at bottom
   * **Technical Details**:
     ```python
     self.keyword_search_input = QLineEdit()
     self.keyword_search_input.setPlaceholderText("Enter keyword to search...")
     
     # Kind filter dropdown
     self.kind_filter = QComboBox()
     self.kind_filter.addItem("All")
     self.kind_filter.addItem("Slide")
     self.kind_filter.addItem("Element")
     self.kind_filter.addItem("Name")
     ```

2. **Middle Panel (Slide Preview)** - Lines 99-135
   * **Components**:
     - `QLabel` for displaying selected keyword context
     - `QListView` configured in IconMode with LeftToRight flow for slide thumbnails
     - `QPushButton` for adding slides to assembly
   * **Technical Details**:
     ```python
     # Slide preview view configuration
     self.slide_preview_view = QListView()
     self.slide_preview_view.setViewMode(QListView.ViewMode.IconMode)
     self.slide_preview_view.setFlow(QListView.Flow.LeftToRight)
     self.slide_preview_view.setWrapping(True)
     self.slide_preview_view.setResizeMode(QListView.ResizeMode.Adjust)
     self.slide_preview_view.setIconSize(QSize(160, 120))  # 4:3 aspect ratio
     ```

3. **Right Panel (Final Assembly Set)** - Lines 137-174
   * **Components**:
     - `QListView` in IconMode with drag-and-drop functionality enabled
     - Button row with "Remove Selected" and "Clear Assembly" actions
     - Export button for final assembly operations
   * **Technical Details**:
     ```python
     # Final assembly view with drag-drop support
     self.final_set_view = QListView()
     self.final_set_view.setViewMode(QListView.ViewMode.IconMode)
     self.final_set_view.setFlow(QListView.Flow.LeftToRight)
     self.final_set_view.setWrapping(True)
     self.final_set_view.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
     ```

### Signal Connections and Event Handling

The implementation includes a comprehensive signal connection structure (Lines 192-215):

```python
def _connect_signals(self):
    """Connect signals for the Assembly Manager Page"""
    # When a keyword is selected in the results view
    self.keyword_results_view.selectionModel().selectionChanged.connect(
        self._handle_keyword_selection_changed
    )
    
    # When the add to basket button is clicked
    self.add_to_basket_btn.clicked.connect(self._handle_add_to_basket)
    
    # Additional signal connections...
```

For each UI interaction, a corresponding placeholder slot method is defined (Lines 217-275) to be implemented in future phases:

```python
@Slot()
def _handle_keyword_selection_changed(self):
    self.logger.debug("Keyword selection changed (placeholder)")
    # Update preview label with selected keyword
    selected_indexes = self.keyword_results_view.selectedIndexes()
    if selected_indexes:
        selected_keyword = selected_indexes[0].data()
        self.preview_label.setText(f"Preview for Keyword: {selected_keyword}")
```

### MainWindow Integration

The page is integrated into the application's navigation system in `src/slideman/ui/main_window.py`:

```python
# Lines 17-19: Import statement added
from .pages.assembly_page import AssemblyManagerPage

# Lines 92-93: Page instantiation and addition to stack
self.assembly_manager_page = AssemblyManagerPage(parent=self)
self.stacked_widget.addWidget(self.assembly_manager_page)
```

The existing navigation button connection (already defined at Line 114) now correctly points to the new page:

```python
self.btn_assembly.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
```

## Technical Design Considerations

### Widget Sizing and Proportions

The implementation carefully considers UI proportions and sizing:

```python
# Set initial sizes (proportional to the ratios mentioned: 25:35:40)
self.main_splitter.setSizes([250, 350, 400])
```

These proportions reflect the recommended ratios in the technical plan, giving appropriate visual weight to each panel based on its intended content density.

### Placeholder Data Strategy

All views were populated with placeholder data to provide visual cues about their intended content:

```python
# Example of placeholder data creation
preview_model = QStandardItemModel()
for i in range(3):
    item = QStandardItem()
    placeholder = QPixmap(QSize(160, 120))
    placeholder.fill(Qt.GlobalColor.lightGray)
    item.setIcon(placeholder)
    item.setText(f"Slide {i+1}")
    preview_model.appendRow(item)
self.slide_preview_view.setModel(preview_model)
```

This approach ensures that the UI is visually comprehensible during development and testing before real data connections are implemented.

## Phase 7, Step 2: Keyword Search Reliability Improvements

### Summary of Fix
- Scoped searches correctly by replacing manual `get_projects()` loop with `get_project_id_by_path()` to retrieve the current project ID.
- Prevented duplicate and mis-mapped rows by using `SELECT DISTINCT k.id, k.keyword, k.kind` in the FTS5 query and explicit columns in the fallback `LIKE` query.

### Why previous attempts failed
- Manual project lookup never matched due to mismatched folder path comparisons, so project filters were never applied.
- Generic `SELECT *` allowed extra columns and duplicate rows from FTS triggers, causing unreliable results and inconsistent mappings.

### Outcome
Search now reliably returns the expected keywords under both scoped and unscoped conditions. Testing confirms consistent, accurate results.

### Technical Details
- **Project ID Lookup**  
  Replaced manual iteration over `db.get_projects()`:
  ```python
  if app_state.current_project_path and self.db:
      projects = self.db.get_projects()
      for p in projects:
          if p.get("folder_path") == app_state.current_project_path:
              self.current_project_id = p.get("id")
  ```
  with direct lookup:
  ```python
  project_id = self.db.get_project_id_by_path(app_state.current_project_path)
  if project_id is not None:
      self.current_project_id = project_id
  ```
- **FTS5 Query Update**  
  Changed from:
  ```sql
  SELECT k.*
    FROM keywords k
    JOIN keywords_fts fts ON k.id = fts.rowid
    WHERE fts MATCH ?
  ```
  to:
  ```sql
  SELECT DISTINCT k.id, k.keyword, k.kind
    FROM keywords k
    JOIN keywords_fts fts ON k.id = fts.rowid
    WHERE fts MATCH ?
    ORDER BY k.keyword COLLATE NOCASE
  ```
- **Fallback LIKE Query Update**  
  Changed from:
  ```sql
  SELECT * FROM keywords WHERE keyword LIKE ? COLLATE NOCASE
  ```
  to:
  ```sql
  SELECT id, keyword, kind 
    FROM keywords 
    WHERE keyword LIKE ? COLLATE NOCASE 
    ORDER BY keyword COLLATE NOCASE
  ```
- **FTS Table & Triggers Creation**  
  Added creation of the FTS virtual table and synchronization triggers:
  ```python
  cursor.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS keywords_fts USING fts5(
      keyword,
      kind,
      content='keywords',
      content_rowid='id'
  );""")
  cursor.execute("""CREATE TRIGGER IF NOT EXISTS keywords_ai AFTER INSERT ON keywords BEGIN
      INSERT INTO keywords_fts(rowid, keyword, kind) VALUES (new.id, new.keyword, new.kind);
  END;""")
  cursor.execute("""CREATE TRIGGER IF NOT EXISTS keywords_au AFTER UPDATE ON keywords BEGIN
      INSERT INTO keywords_fts(keywords_fts, rowid, keyword, kind) VALUES('delete', old.id, old.keyword, old.kind);
      INSERT INTO keywords_fts(rowid, keyword, kind) VALUES (new.id, new.keyword, new.kind);
  END;""")
  cursor.execute("""CREATE TRIGGER IF NOT EXISTS keywords_ad AFTER DELETE ON keywords BEGIN
      INSERT INTO keywords_fts(keywords_fts, rowid, keyword, kind) VALUES('delete', old.id, old.keyword, old.kind);
  END;""")
  ```
- **FTS Table Population**  
  Populated existing keywords into the FTS index on first run:
  ```python
  cursor.execute("SELECT COUNT(*) FROM keywords_fts;")
  count = cursor.fetchone()[0]
  if count == 0:
      cursor.execute(
          "INSERT INTO keywords_fts(rowid, keyword, kind) SELECT id, keyword, kind FROM keywords;"
      )
  ```

## Phase 7, Step 2: Keyword Search and Basket Functionality Implementation

This section details the implementation of keyword search functionality and the keyword basket feature for the Assembly Manager page.

### Database Enhancements for Full-Text Search

**File: `src/slideman/services/database.py`**

1. **FTS5 Virtual Table Implementation**
   * Added a virtual table for keyword text searching using SQLite's FTS5 extension:
   ```python
   # Create FTS5 virtual table for keyword searching
   cursor.execute("""
       CREATE VIRTUAL TABLE keywords_fts USING fts5(
           keyword,
           content='keywords',
           content_rowid='id'
       );
   """)
   ```

2. **Trigger Implementation for FTS Synchronization**
   * Created triggers to keep the FTS index synchronized with the main keywords table:
   ```python
   # Create triggers to keep FTS table synchronized
   cursor.execute("""
       CREATE TRIGGER keywords_ai AFTER INSERT ON keywords BEGIN
           INSERT INTO keywords_fts(rowid, keyword) VALUES (new.id, new.keyword);
       END;
   """)
   
   cursor.execute("""
       CREATE TRIGGER keywords_ad AFTER DELETE ON keywords BEGIN
           INSERT INTO keywords_fts(keywords_fts, rowid, keyword) VALUES('delete', old.id, old.keyword);
       END;
   """)
   
   cursor.execute("""
       CREATE TRIGGER keywords_au AFTER UPDATE ON keywords BEGIN
           INSERT INTO keywords_fts(keywords_fts, rowid, keyword) VALUES('delete', old.id, old.keyword);
           INSERT INTO keywords_fts(rowid, keyword) VALUES (new.id, new.keyword);
       END;
   """)
   ```

3. **Search Keywords Method**
   * Implemented a comprehensive search method that supports prefix matching and filtering by keyword kind and project scope:
   ```python
   def search_keywords(self, query_term: str, kind: Optional[KeywordKind] = None, 
                        project_id: Optional[int] = None) -> List[Keyword]:
       """Search for keywords using FTS5 with prefix matching and optional filtering"""
       if not query_term or not self._conn:
           return []
           
       # Use prefix matching by appending * to the query term
       query_term = query_term.strip() + "*"
       
       params = [query_term]
       sql = """SELECT k.* FROM keywords k 
               JOIN keywords_fts fts ON k.rowid = fts.rowid 
               WHERE keywords_fts MATCH ?"""
       
       # Add filter for keyword kind if specified
       if kind:
           sql += " AND k.kind = ?"
           params.append(kind)
       
       # Add project scope filter if specified
       if project_id is not None:
           sql += """ AND k.id IN (
               SELECT DISTINCT keyword_id FROM (
                   SELECT keyword_id FROM slide_keywords WHERE slide_id IN (
                       SELECT id FROM slides WHERE project_id = ?
                   )
                   UNION
                   SELECT keyword_id FROM element_keywords WHERE element_id IN (
                       SELECT id FROM elements WHERE slide_id IN (
                           SELECT id FROM slides WHERE project_id = ?
                       )
                   )
               )
           )"""
           params.extend([project_id, project_id])
       
       # Execute the query
       cursor = self._conn.cursor()
       cursor.execute(sql, params)
       rows = cursor.fetchall()
       
       # Convert rows to Keyword objects
       return [Keyword(id=row['id'], keyword=row['keyword'], kind=row['kind']) 
               for row in rows]
   ```

### Custom Model for Keyword Representation

**File: `src/slideman/ui/pages/assembly_page.py`**

1. **KeywordListModel Implementation**
   * Created a custom list model that inherits from `QAbstractListModel` to display keywords with visual differentiation based on keyword kind:
   ```python
   class KeywordListModel(QAbstractListModel):
       """Model for displaying keywords in a list view."""
       KeywordIdRole = Qt.ItemDataRole.UserRole + 1
       KeywordTextRole = Qt.ItemDataRole.UserRole + 2
       KeywordKindRole = Qt.ItemDataRole.UserRole + 3
       
       def __init__(self, parent=None):
           super().__init__(parent)
           self._keywords: List[Keyword] = []
   ```

   * Implemented visual cues with different background colors for different keyword types:
   ```python
   elif role == Qt.ItemDataRole.BackgroundRole:
       # Different background colors based on keyword kind
       if keyword.kind == 'topic':
           return QBrush(QColor(230, 240, 250))  # Light blue
       elif keyword.kind == 'title':
           return QBrush(QColor(230, 250, 230))  # Light green
       elif keyword.kind == 'name':
           return QBrush(QColor(250, 240, 230))  # Light orange
   ```

   * Added methods for managing keyword collections:
   ```python
   def addKeyword(self, keyword: Keyword) -> bool:
       """Add a keyword to the model if it doesn't already exist"""
       # Check if keyword already exists by ID
       if any(kw.id == keyword.id for kw in self._keywords):
           return False
           
       pos = len(self._keywords)
       self.beginInsertRows(QModelIndex(), pos, pos)
       self._keywords.append(keyword)
       self.endInsertRows()
       return True
   ```

### Search Interface Implementation

1. **UI Enhancements**
   * Added proper data connections to filter comboboxes:
   ```python
   self.kind_filter = QComboBox()
   self.kind_filter.addItem("All", None)  # None means no filter
   self.kind_filter.addItem("Topic", "topic")
   self.kind_filter.addItem("Title", "title")
   self.kind_filter.addItem("Name", "name")
   self.kind_filter.currentIndexChanged.connect(self._on_filter_changed)
   ```

2. **Debounced Search Implementation**
   * Added debouncing for search input to prevent excessive database queries:
   ```python
   # Create a timer for debouncing search input
   self.search_timer = QTimer(self)
   self.search_timer.setSingleShot(True)
   self.search_timer.setInterval(300)  # 300ms debounce delay
   self.search_timer.timeout.connect(self._update_keyword_search_results)
   ```

   * Connected search input to debounce handler:
   ```python
   @Slot(str)
   def _on_search_text_changed(self, text: str):
       """Handle search text changes with debounce"""
       # Restart the timer to debounce input
       self.search_timer.stop()
       self.search_timer.start()
   ```

3. **Search Results Update**
   * Implemented logic to query the database and update the results model:
   ```python
   @Slot()
   def _update_keyword_search_results(self):
       """Update the keyword search results based on current filters"""
       # Get the search term
       query_term = self.keyword_search_input.text().strip()
       
       # Get the kind filter
       kind = self.kind_filter.currentData()
       
       # Get project scope
       use_project_scope = self.project_scope_filter.currentData()
       project_id = self.current_project_id if use_project_scope else None
       
       # Search for keywords
       keywords = self.db.search_keywords(query_term, kind, project_id)
       
       # Update the model
       self.keyword_results_model.setKeywords(keywords)
   ```

### Keyword Basket Implementation

1. **Basket Interaction Methods**
   * Added methods to add keywords to the basket:
   ```python
   @Slot()
   def _add_selected_keyword_to_basket(self):
       """Add currently selected keyword to the basket"""
       selected_indexes = self.keyword_results_view.selectionModel().selectedIndexes()
       if not selected_indexes:
           return
           
       # Get the selected keyword
       index = selected_indexes[0]
       keyword_id = index.data(KeywordListModel.KeywordIdRole)
       
       # Check if it's already in the basket
       existing = self.keyword_basket_model.getKeywordById(keyword_id)
       if existing:
           return  # Already in basket
           
       # Get the keyword object from the results model
       keyword = self.keyword_results_model.getKeywordById(keyword_id)
       if keyword:
           # Add to basket model
           self.keyword_basket_model.addKeyword(keyword)
           self._emit_basket_updated()
   ```

2. **Context Menu Integration**
   * Added context menus for both the search results and the basket for more intuitive interaction:
   ```python
   @Slot(QPoint)
   def _show_results_context_menu(self, pos):
       """Show context menu for keyword results"""
       global_pos = self.keyword_results_view.mapToGlobal(pos)
       menu = QMenu(self)
       
       # Get the item under cursor
       index = self.keyword_results_view.indexAt(pos)
       if index.isValid():
           add_action = menu.addAction("Add to Basket")
           add_action.triggered.connect(self._add_selected_keyword_to_basket)
           
       menu.exec(global_pos)
   ```

3. **Signal Emission**
   * Implemented methods to notify observers when the basket content changes:
   ```python
   def _emit_basket_updated(self):
       """Emit the basketUpdated signal with current keywords"""
       keywords = self.keyword_basket_model.keywords()
       keyword_ids = [k.id for k in keywords]
       self.basketUpdated.emit(keyword_ids)
       self.logger.debug(f"Basket updated: {len(keyword_ids)} keywords")
   ```

## Phase 7, Step 3: Slide Preview & Enlarged Slide Functionality

### Summary of Changes
- Added `get_slide_image_path` in `Database` to fetch `image_rel_path` for a slide.
- Enhanced `ThumbnailCache` to derive the project path from the database when `app_state.current_project_path` is unset.
- Updated `_show_enlarged_slide` in `AssemblyManagerPage`:
  - Fallback to full-resolution image, then thumbnail if missing.
  - Derived project root via `get_project_folder_path_for_slide`.
  - Checked both standard and shared file paths.
  - Guarded against null `QPixmap` instances.
  - Adjusted dialog title to indicate preview vs full-res.

### Technical Implementation
1. **Database** (`database.py`)
   ```python
   def get_slide_image_path(self, slide_id: int) -> Optional[str]:
       ...
   ```
2. **ThumbnailCache** (`thumbnail_cache.py`)
   - On cache miss, attempt disk load using derived project path when `current_project_path` is `None`.
3. **AssemblyManagerPage** (`assembly_page.py`)
   - Revamped `_show_enlarged_slide` slot:
     ```python
     @Slot(QModelIndex)
     def _show_enlarged_slide(self, index: QModelIndex):
         ...
         image_rel = db.get_slide_image_path(slide_id) or db.get_slide_thumbnail_path(slide_id)
         proj_path = app_state.current_project_path or db.get_project_folder_path_for_slide(slide_id)
         ...
     ```

## Phase 7, Step 4: Final Slide Set Assembly & Reordering

### Summary of Changes
- Created `FinalSetModel` subclass of `QAbstractListModel` to display and reorder slide thumbnails.
- Configured `final_set_view` for drag-and-drop (`InternalMove`) and multi-selection.
- Connected `app_state.assemblyBasketChanged` to `_update_final_set` to populate the final set from current basket keywords.
- Implemented `_update_final_set`, `_remove_selected_slides`, and `_clear_final_set` in `AssemblyManagerPage`.
- Enabled internal move and deletion by overriding `flags`, `mimeTypes`, `mimeData`, `dropMimeData`, and `removeRows`.

### Technical Implementation
1. **AssemblyManagerPage** (`assembly_page.py`)
   - Defined `FinalSetModel`:
     ```python
     class FinalSetModel(QAbstractListModel):
         ...
         def dropMimeData(...):
             ...
     ```
   - Initialized model and view:
     ```python
     self.final_set_model = FinalSetModel([], self)
     self.final_set_view.setModel(self.final_set_model)
     self.final_set_view.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
     self.final_set_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
     ```
   - Populated final set on `app_state.assemblyBasketChanged`.
   - Wired removal and clear buttons (`remove_selected_btn`, `clear_assembly_btn`) to update model.

## Phase 7, Step 5: State Persistence & Integration

### Summary of Changes
- Extended `AppState` (`app_state.py`) with:
  - `assembly_keyword_basket: List[int]`
  - `assembly_final_slide_ids: List[int]`
  - Signals: `assemblyBasketChanged`, `assemblyOrderChanged`
  - Methods: `set_assembly_basket(ids)`, `set_assembly_order(ids)`, `clear_assembly()`
  - Persistence in `QSettings` within `load_initial_state` and save on updates.
- Modified `AssemblyManagerPage` to:
  - Call `app_state.set_assembly_basket(...)` in `_emit_basket_updated`.
  - Listen to `app_state.assemblyBasketChanged` to refresh final set.
  - Persist reorder, removal, and clear actions via `app_state.set_assembly_order(...)` and `final_set_model.layoutChanged`.

### Technical Implementation
1. **AppState** (`app_state.py`)
   ```python
   self.assembly_keyword_basket = []
   self.assembly_final_slide_ids = []
   assemblyBasketChanged = Signal(list)
   assemblyOrderChanged = Signal(list)
   def set_assembly_basket(self, ids: List[int]):
       ...
   def set_assembly_order(self, ids: List[int]):
       ...
   ```
2. **AssemblyManagerPage** (`assembly_page.py`)
   - Replaced local basket signals with `app_state` calls.
   - Connected `final_set_model.layoutChanged` to `_on_final_order_changed` to persist reorder.

## Next Steps and Technical Roadmap

With the keyword search and basket functionality now implemented, the following technical steps remain:

1. **Slide Preview Implementation** (Phase 7, Step 3):
   * Create slide thumbnail model for previews (`SlidePreviewModel`)
   * Implement loading of slide thumbnails associated with selected keywords
   * Add zoom/detail view capabilities for better slide inspection

2. **Assembly Management** (Phase 7, Step 4):
   * Develop a reorderable model for the final assembly (`AssemblyListModel`)
   * Add drag-and-drop support between preview and assembly panels
   * Implement assembly ordering functionality

3. **Export Functionality** (Phase 7, Step 5):
   * Create export options dialog
   * Implement PDF export capabilities
   * Add slide deck export formats

## Technical Issues and Solutions

### Keyword Search Functionality Issues

During implementation, we encountered several technical challenges with the keyword search functionality that deserve documentation for future reference.

#### Issue 1: FTS5 Table Creation

**Problem:**
The SQLite FTS5 (Full-Text Search) virtual table for keywords (`keywords_fts`) was not being created in existing databases, resulting in runtime errors when attempting to search:

```
sqlite3.OperationalError: no such table: keywords_fts
```

**Technical Context:**
In our original implementation, the FTS5 table creation was included in the `_create_tables()` method of the `Database` class, which only runs when initializing a new database. For existing databases, the virtual table was missing.

**Solution Approach:** 
We implemented a new method `_ensure_fts_tables_exist()` that:
1. Checks if the `keywords_fts` virtual table exists using the SQLite `sqlite_master` table
2. Creates the virtual table if it doesn't exist
3. Creates triggers to keep the FTS index in sync with the main keywords table
4. Populates the FTS table with existing keyword data

This method is called after the schema initialization to ensure the FTS table exists in all cases.

#### Issue 2: Search Reliability

**Problem:**
Even after creating the FTS5 table structure, searches for keywords that are known to exist in the database (e.g., "mama") fail to return results.

**Technical Root Causes:**
1. **FTS5 Index Synchronization:** The FTS5 table may not be fully synchronized with the main `keywords` table
2. **Feature Availability:** Some SQLite builds may have limited FTS5 capabilities
3. **Unicode Handling:** FTS5 tokenization of non-English text can vary by SQLite configuration
4. **Prefix Matching Syntax:** The prefix matching operator `*` works differently than SQL's `LIKE` operator

**Robust Solution Implementation:**  
We implemented a two-tiered search approach for maximum reliability:

1. **Primary FTS5 Search:**
```python
base_sql = """
    SELECT k.*
    FROM keywords k
    JOIN keywords_fts fts ON k.rowid = fts.rowid
    WHERE keywords_fts MATCH ?
"""
params = [query_term + '*']  # Add * for prefix matching
```

2. **Fallback SQL LIKE Search:**
```python
fallback_sql = "SELECT * FROM keywords WHERE keyword LIKE ? COLLATE NOCASE"
params = [f"{query_term}%"]  # Use LIKE with % for wildcard
```

The code first attempts the optimized FTS5 search. If this fails due to any reason (exception, empty FTS table, etc.), it automatically falls back to a traditional SQL `LIKE` search which is more robust but less performant.

**Key Insight:**  
This dual approach balances performance with reliability:
- When FTS5 is working correctly: Fast, index-based searching
- When FTS5 fails: Slower but reliable LIKE-based searching

#### Issue 3: Case Sensitivity and Partial Matching

**Problem:**  
Searching for partial terms and dealing with case sensitivity could produce inconsistent results.

**Solution:**  
- Added `COLLATE NOCASE` to all query components to ensure case-insensitivity
- Ensured consistent wildcard behavior across both search methods
- Added thorough error logging for diagnostic purposes

#### Lessons for Future Development

1. **Database Schema Migration:**  
   Virtual tables require special handling during schema migrations as they are not fully covered by standard SQLite migration approaches.

2. **Multi-Tier Search Strategy:**  
   Always provide fallback search mechanisms when relying on optional SQLite features like FTS5.

3. **Error Transparency:**  
   Log search term, parameters, and results for easier debugging.
   * Implement export file generation
   * Add progress reporting for lengthy operations

### Current Status of Keyword Search Functionality

#### Update (2025-05-07)

We have implemented the following fixes to address the keyword search functionality issues:

1. **Added `search_keywords` Method to Database Class**:
   * Implemented a robust search method in the `Database` class that supports:
     - Primary FTS5 search with proper index usage
     - Fallback to SQL LIKE search when FTS5 fails
     - Filtering by keyword kind and project scope
     - Proper error handling and logging

2. **Enhanced FTS Tables Management**:
   * Modified `_ensure_fts_tables_exist()` method to be called after schema initialization
   * Ensured FTS tables exist even for existing databases to prevent schema-related issues
   * Added proper triggers to keep the FTS index in sync with the main keywords table

3. **Improved UI Interaction**:
   * Connected the Enter/Return key press in the search input field to trigger keyword search
   * Enhanced the debounce mechanism for search input

Despite these implementations, the search functionality still shows issues with retrieving keywords. Recent logs show:

```
2025-05-07 05:10:01,579 - DEBUG - [src.slideman.services.database] - Found 0 keywords matching 'mama*' using FTS5
2025-05-07 05:10:01,581 - DEBUG - [src.slideman.ui.pages.assembly_page] - Found 0 keywords matching 'mama'
```

Even though keywords like "mama" clearly exist in the database (as visible in the UI), both the FTS5 search and the fallback LIKE search are failing to retrieve them. This suggests that there might be deeper issues that require further investigation:

#### Ongoing Investigation Areas:

1. **Data Storage and Representation**:
   * How keywords are stored in the database (encoding, normalization)
   * The relationship between displayed text in the UI and actual database entries
   * Potential whitespace or special character issues affecting matching

2. **Database Configuration**:
   * Potential issues with the SQLite build or FTS5 extension configuration
   * Database connection and transaction management

3. **Keyword Extraction Process**:
   * The exact process by which text elements from slides are extracted and stored as keywords
   * Potential inconsistencies between extraction and search processes

The UI structure is correctly implemented with all necessary components and signal connections. This provides a solid foundation for the search functionality once the underlying data retrieval issues are resolved in future development phases.

## Phase 7 Steps 3-5 sections

### Phase 7, Step 3: Slide Preview & Enlarged Slide Functionality

### Summary of Changes
- Added `get_slide_image_path` in `Database` to fetch `image_rel_path` for a slide.
- Enhanced `ThumbnailCache` to derive the project path from the database when `app_state.current_project_path` is unset.
- Updated `_show_enlarged_slide` in `AssemblyManagerPage`:
  - Fallback to full-resolution image, then thumbnail if missing.
  - Derived project root via `get_project_folder_path_for_slide`.
  - Checked both standard and shared file paths.
  - Guarded against null `QPixmap` instances.
  - Adjusted dialog title to indicate preview vs full-res.

### Technical Implementation
1. **Database** (`database.py`)
   ```python
   def get_slide_image_path(self, slide_id: int) -> Optional[str]:
       ...
   ```
2. **ThumbnailCache** (`thumbnail_cache.py`)
   - On cache miss, attempt disk load using derived project path when `current_project_path` is `None`.
3. **AssemblyManagerPage** (`assembly_page.py`)
   - Revamped `_show_enlarged_slide` slot:
     ```python
     @Slot(QModelIndex)
     def _show_enlarged_slide(self, index: QModelIndex):
         ...
         image_rel = db.get_slide_image_path(slide_id) or db.get_slide_thumbnail_path(slide_id)
         proj_path = app_state.current_project_path or db.get_project_folder_path_for_slide(slide_id)
         ...
     ```

### Phase 7, Step 4: Final Slide Set Assembly & Reordering

### Summary of Changes
- Created `FinalSetModel` subclass of `QAbstractListModel` to display and reorder slide thumbnails.
- Configured `final_set_view` for drag-and-drop (`InternalMove`) and multi-selection.
- Connected `app_state.assemblyBasketChanged` to `_update_final_set` to populate the final set from current basket keywords.
- Implemented `_update_final_set`, `_remove_selected_slides`, and `_clear_final_set` in `AssemblyManagerPage`.
- Enabled internal move and deletion by overriding `flags`, `mimeTypes`, `mimeData`, `dropMimeData`, and `removeRows`.

### Technical Implementation
1. **AssemblyManagerPage** (`assembly_page.py`)
   - Defined `FinalSetModel`:
     ```python
     class FinalSetModel(QAbstractListModel):
         ...
         def dropMimeData(...):
             ...
     ```
   - Initialized model and view:
     ```python
     self.final_set_model = FinalSetModel([], self)
     self.final_set_view.setModel(self.final_set_model)
     self.final_set_view.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
     self.final_set_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
     ```
   - Populated final set on `app_state.assemblyBasketChanged`.
   - Wired removal and clear buttons (`remove_selected_btn`, `clear_assembly_btn`) to update model.

### Phase 7, Step 5: State Persistence & Integration

### Summary of Changes
- Extended `AppState` (`app_state.py`) with:
  - `assembly_keyword_basket: List[int]`
  - `assembly_final_slide_ids: List[int]`
  - Signals: `assemblyBasketChanged`, `assemblyOrderChanged`
  - Methods: `set_assembly_basket(ids)`, `set_assembly_order(ids)`, `clear_assembly()`
  - Persistence in `QSettings` within `load_initial_state` and save on updates.
- Modified `AssemblyManagerPage` to:
  - Call `app_state.set_assembly_basket(...)` in `_emit_basket_updated`.
  - Listen to `app_state.assemblyBasketChanged` to refresh final set.
  - Persist reorder, removal, and clear actions via `app_state.set_assembly_order(...)` and `final_set_model.layoutChanged`.

### Technical Implementation
1. **AppState** (`app_state.py`)
   ```python
   self.assembly_keyword_basket = []
   self.assembly_final_slide_ids = []
   assemblyBasketChanged = Signal(list)
   assemblyOrderChanged = Signal(list)
   def set_assembly_basket(self, ids: List[int]):
       ...
   def set_assembly_order(self, ids: List[int]):
       ...
   ```
2. **AssemblyManagerPage** (`assembly_page.py`)
   - Replaced local basket signals with `app_state` calls.
   - Connected `final_set_model.layoutChanged` to `_on_final_order_changed` to persist reorder.
