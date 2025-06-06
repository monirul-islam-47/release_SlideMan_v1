# SLIDEMAN Architecture Analysis - Complete Report

Based on my thorough analysis of the codebase, here's a comprehensive understanding of SLIDEMAN's architecture:

## Core Architecture Patterns

1. **Model-View-Presenter (MVP)**: 
   - Views handle UI only
   - Presenters contain all business logic
   - Models are pure data structures (Pydantic)
   - Clean separation of concerns

2. **Service Layer**:
   - All business logic in stateless services
   - Thread-safe database with connection pooling
   - Services handle file I/O, slide conversion, exports

3. **Command Pattern**:
   - All user actions are QUndoCommand subclasses
   - Full undo/redo support
   - Commands use services, not direct DB access

4. **Dependency Injection**:
   - ServiceRegistry manages service lifecycle
   - Services injected into presenters and commands
   - Avoids singleton anti-pattern (except AppState/EventBus)

5. **Event-Driven Communication**:
   - EventBus for decoupled component communication
   - Qt signals for UI updates
   - AppState manages global application state

## Key Architectural Components

### 1. Application Bootstrap (`__main__.py`)
- Sets up logging infrastructure
- Initializes Qt application
- Creates database connection
- Loads theme
- Creates main window

### 2. State Management
- `AppState`: Thread-safe singleton for global state
- `EventBus`: Central signal hub for events
- Both use proper thread locking

### 3. Data Layer
- SQLite with FTS5 for search
- Thread-safe with connection pooling
- Models: Project → File → Slide → Element
- Keywords linked via junction tables
- Clean Pydantic models with validation

### 4. Service Layer
- `Database`: All data operations
- `SlideConverter`: PowerPoint → images (COM)
- `ExportService`: Assembly → PowerPoint
- `ThumbnailCache`: LRU cache for performance
- `FileIO`: Project structure management

### 5. Presenter Layer
- One presenter per UI page
- Handles all business logic
- Coordinates services
- Updates views through interfaces

### 6. UI Layer
- Qt/PySide6 widgets
- Five main pages in stacked widget
- Custom widgets for slide preview
- Dark theme with consistent styling

## Data Flow Architecture

```
User Action → View → Presenter → Command → Service → Database
                ↓                    ↓         ↓
            EventBus ← AppState ← Signal ← Response
```

## Threading Model

1. **Main Thread**: Qt UI only
2. **Worker Threads**: 
   - File copying (QRunnable)
   - Slide conversion (QRunnable)
   - Export operations (QRunnable)
3. **Database**: Thread-safe connection pool

## Key Design Decisions

1. **Windows-Only**: Uses COM for PowerPoint integration
2. **Local First**: SQLite database, file-based projects
3. **Immutable Models**: Pydantic for data validation
4. **Three-Tier Keywords**: Topic/Title/Name hierarchy
5. **Presenter Pattern**: Business logic separated from UI

## Project Structure

```
src/slideman/
├── __main__.py          # Entry point
├── app_state.py         # Global state
├── event_bus.py         # Event system
├── models/              # Data models
├── services/            # Business logic
├── presenters/          # MVP presenters
├── commands/            # Undo/redo commands
├── ui/                  # Qt widgets
│   ├── pages/          # Main UI pages
│   ├── widgets/        # Reusable widgets
│   └── components/     # UI components
└── theme.py            # Theming system
```

## Database Schema

### Tables
1. **projects**: id, name, folder_path, created_at
2. **files**: id, project_id, filename, rel_path, slide_count, checksum, conversion_status
3. **slides**: id, file_id, slide_index, thumb_rel_path, image_rel_path
4. **elements**: id, slide_id, element_type, content
5. **keywords**: id, keyword, kind (topic/title/name)
6. **slide_keywords**: slide_id, keyword_id (junction)
7. **element_keywords**: element_id, keyword_id (junction)

### Relationships
- Projects contain Files (1:N)
- Files contain Slides (1:N)
- Slides contain Elements (1:N)
- Keywords linked to Slides and Elements (M:N)

## Service Details

### Database Service
- Thread-safe with connection pooling (5 connections)
- WAL mode for concurrent access
- FTS5 virtual tables for search
- Comprehensive error handling with custom exceptions

### SlideConverter Service
- Uses COM automation (Windows PowerPoint)
- Converts slides to PNG images
- Extracts shape/element data
- Runs in background thread

### ExportService
- Assembles slides into new PowerPoint
- Supports custom ordering
- Progress tracking
- Background execution

### ThumbnailCache
- LRU cache with 100MB limit
- Lazy loading from disk
- Thread-safe access
- Preloading support

## UI Architecture

### Main Window
- Left navigation rail
- Stacked widget for pages
- Status bar for messages
- Toolbar for actions

### Pages
1. **Projects Page**: Create, list, delete projects
2. **SlideView Page**: Browse slides, add keywords
3. **Assembly Page**: Collect slides by keywords
4. **Delivery Page**: Export assembled presentations
5. **Keyword Manager**: Manage keyword hierarchy

### Custom Widgets
- SlidePreviewWidget: Thumbnail with keywords
- TagEdit: Keyword input with autocomplete
- SortableHeaderView: Sortable table headers

## Plan to Recreate From Scratch

To recreate SLIDEMAN from scratch while understanding each component:

### Phase 1: Core Foundation
1. Set up project structure with Poetry
2. Create basic Qt application skeleton
3. Implement AppState and EventBus patterns
4. Design and implement data models

### Phase 2: Data Layer
1. Create SQLite database schema
2. Implement thread-safe database service
3. Add connection pooling
4. Implement FTS5 search

### Phase 3: Service Layer
1. Create ServiceRegistry for DI
2. Implement file I/O operations
3. Add PowerPoint conversion service
4. Create thumbnail caching

### Phase 4: UI Foundation
1. Create main window with navigation
2. Implement base presenter pattern
3. Create base command class
4. Set up theming system

### Phase 5: Feature Implementation
1. Projects page (create/list/delete)
2. SlideView page (browse/tag)
3. Assembly page (collect slides)
4. Delivery page (export)
5. Keyword manager

### Phase 6: Polish
1. Error handling
2. Progress indicators
3. Keyboard shortcuts
4. Testing

## Key Learnings

1. **MVP Pattern Benefits**: Clear separation makes testing easier
2. **Service Layer**: Decouples business logic from UI
3. **Command Pattern**: Elegant undo/redo implementation
4. **Thread Safety**: Critical for database operations
5. **Event Bus**: Enables loose coupling between components

This architecture is well-designed with clear separation of concerns, making it maintainable and testable. The refactoring has created a solid foundation for future development.