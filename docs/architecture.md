# SLIDEMAN Architecture Documentation

## Overview

SLIDEMAN is built using a clean layered architecture with Model-View-Presenter (MVP) pattern, ensuring separation of concerns, testability, and maintainability. This document describes the architectural decisions, patterns, and component interactions.

## Architectural Principles

1. **Separation of Concerns**: Each layer has a specific responsibility
2. **Dependency Inversion**: High-level modules don't depend on low-level modules
3. **Single Responsibility**: Each class has one reason to change
4. **Open/Closed**: Open for extension, closed for modification
5. **Interface Segregation**: Clients shouldn't depend on interfaces they don't use

## Architecture Layers

### 1. Model Layer

The model layer contains pure Python dataclasses representing the domain entities. These are immutable data structures with no business logic or framework dependencies.

```
models/
├── project.py      # Project entity
├── file.py         # PowerPoint file entity
├── slide.py        # Slide entity
├── element.py      # Slide element entity
└── keyword.py      # Keyword/tag entity
```

**Key Characteristics:**
- Immutable dataclasses using `frozen=True`
- No Qt dependencies
- Simple data validation in `__post_init__`
- Can be easily serialized/deserialized

### 2. Service Layer

The service layer contains all business logic and external system interactions. Services are stateless and can be used independently of the UI framework.

```
services/
├── interfaces.py           # Service protocols/interfaces
├── database.py            # SQLite database operations
├── file_io.py             # File system operations
├── slide_converter.py     # PowerPoint COM automation
├── export_service.py      # Presentation generation
├── thumbnail_cache.py     # Image caching service
├── background_tasks.py    # Thread pool management
├── service_registry.py    # Dependency injection
└── exceptions.py          # Custom exceptions
```

**Key Services:**

#### Database Service
- Thread-safe SQLite access with connection pooling
- Full-text search using FTS5
- Transaction support
- Cascade delete operations

#### File I/O Service
- Project directory management
- Safe file operations
- Disk space checking
- Checksum calculation

#### Slide Converter Service
- Windows COM automation for PowerPoint
- Batch slide conversion
- Progress reporting
- Shape extraction

#### Export Service
- Assemble slides into new presentations
- Maintain formatting
- Support for notes inclusion

### 3. Presenter Layer (MVP)

Presenters implement the Model-View-Presenter pattern, coordinating between views and services. They contain no UI code but manage the presentation logic.

```
presenters/
├── base_presenter.py         # Base class with common functionality
├── projects_presenter.py     # Project management logic
├── slideview_presenter.py    # Slide browsing and filtering
├── assembly_presenter.py     # Slide selection and ordering
├── delivery_presenter.py     # Export coordination
└── keyword_manager_presenter.py  # Tagging operations
```

**Presenter Responsibilities:**
- Receive user input from views
- Call appropriate services
- Update view with results
- Handle errors consistently
- Manage background tasks

**View Interfaces:**
Each presenter works with a view interface (e.g., `IProjectsView`) that defines the contract between presenter and view. This enables:
- Easy testing with mock views
- Multiple view implementations
- Clear separation of concerns

### 4. Command Layer

All user actions that modify state are implemented as undoable commands following the Command pattern.

```
commands/
├── base_command.py           # Base class for all commands
├── delete_project.py         # Delete project command
├── rename_project.py         # Rename project command
├── manage_slide_keyword.py   # Add/remove slide keywords
├── manage_element_keyword.py # Add/remove element keywords
└── merge_keywords_cmd.py     # Merge duplicate keywords
```

**Command Features:**
- Full undo/redo support
- Command merging for efficiency
- Database transaction integration
- Consistent error handling

### 5. UI Layer

The UI layer contains all Qt-specific code, implementing the view interfaces defined by presenters.

```
ui/
├── main_window.py      # Main application window
├── pages/              # Main UI pages
│   ├── projects_page.py
│   ├── slideview_page.py
│   ├── assembly_page.py
│   ├── delivery_page.py
│   └── keyword_manager_page.py
├── components/         # Reusable UI components
│   ├── common.py          # Shared mixins and factories
│   ├── slide_canvas.py    # Slide display widget
│   └── tag_edit.py        # Tag editing widget
├── widgets/            # Custom widgets
│   ├── base_preview_widget.py
│   ├── slide_preview_widget.py
│   └── assembly_preview_widget.py
└── utils/              # UI utilities
    ├── messages.py        # Standardized dialogs
    ├── workers.py         # Background task helpers
    └── factories.py       # UI component factories
```

## Component Interactions

### Typical Request Flow

1. **User Action**: User clicks button in UI
2. **View**: UI page handles event, calls presenter method
3. **Presenter**: Validates input, calls service(s)
4. **Service**: Performs business logic, returns result
5. **Presenter**: Processes result, updates view
6. **View**: Updates UI with new data

### Example: Creating a Project

```python
# 1. User fills form and clicks "Create"
# 2. ProjectsPage (View) calls presenter
self.presenter.create_project()

# 3. ProjectsPresenter validates and coordinates
def create_project(self):
    # Get input from view
    info = self.view.get_new_project_info()
    if not info:
        return
    
    # Validate files
    if not all(self.file_io.is_valid_powerpoint(f) for f in files):
        self.view.show_error("Invalid files")
        return
    
    # Create project structure
    project_path = self.file_io.create_project_structure(name)
    
    # Create database record
    project = self.db.create_project(name, description)
    
    # Copy files (background task)
    for file in files:
        dest = self.file_io.copy_file_to_project(file, project_path)
        self.db.create_file(project.id, file.name, str(dest), ...)
    
    # Notify success
    self.view.show_info("Project created")
    event_bus.project_created.emit(project.id)
```

## Design Patterns

### 1. Model-View-Presenter (MVP)

**Problem**: Tight coupling between UI and business logic makes testing difficult and changes risky.

**Solution**: 
- **Model**: Domain entities (Project, Slide, etc.)
- **View**: UI implementation with minimal logic
- **Presenter**: Coordinates between view and model/services

**Benefits**:
- Views can be tested with mock presenters
- Presenters can be tested with mock views
- Business logic is UI-framework agnostic

### 2. Dependency Injection

**Problem**: Hard-coded dependencies make testing and configuration difficult.

**Solution**: ServiceRegistry provides all services to components that need them.

```python
# Registration
registry = ServiceRegistry()
registry.register('database', Database())
registry.register('file_io', FileIO())

# Usage in presenter
class ProjectsPresenter(BasePresenter):
    def __init__(self, view, services):
        self.db = services['database']
        self.file_io = services['file_io']
```

### 3. Command Pattern

**Problem**: Need undo/redo functionality for user actions.

**Solution**: All modifications implemented as QUndoCommand subclasses.

```python
class RenameProjectCommand(BaseCommand):
    def redo(self):
        self.db.rename_project(self.project_id, self.new_name)
        
    def undo(self):
        self.db.rename_project(self.project_id, self.old_name)
```

### 4. Factory Pattern

**Problem**: Complex UI component creation with repetitive configuration.

**Solution**: Factory functions encapsulate creation logic.

```python
def create_thumbnail_list_view(icon_size=(160, 120)):
    view = QListView()
    view.setViewMode(QListView.IconMode)
    view.setIconSize(QSize(*icon_size))
    # ... more configuration
    return view
```

### 5. Observer Pattern

**Problem**: Components need to react to changes in other components.

**Solution**: Qt signals provide decoupled event notification.

```python
# Event bus for application-wide events
class EventBus(QObject):
    project_created = Signal(int)
    project_deleted = Signal(int)
    # ...

# Usage
event_bus.project_created.connect(self.on_project_created)
```

### 6. Singleton Pattern

**Problem**: Need single instances of certain services (cache, app state).

**Solution**: Controlled instance creation.

```python
class ThumbnailCache:
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
```

## Threading Model

SLIDEMAN uses Qt's threading capabilities for responsive UI:

### Main Thread
- All UI operations
- Event handling
- View updates

### Worker Threads
- Slide conversion (SlideConverter)
- File operations (copy, checksum)
- Export operations
- Database operations (via DatabaseWorker)

### Thread Safety
- Database uses connection pooling
- Services are stateless or thread-safe
- Qt signals handle cross-thread communication

## Data Flow

### 1. Project Import Flow
```
User selects files
    → ProjectsPresenter validates
    → FileIO creates project structure
    → Database creates records
    → ConversionWorker processes slides
    → ThumbnailCache stores images
    → View updates with results
```

### 2. Search and Filter Flow
```
User enters search/selects keywords
    → SlideViewPresenter builds query
    → Database performs FTS search
    → Results filtered by criteria
    → ThumbnailCache provides images
    → View displays filtered slides
```

### 3. Assembly and Export Flow
```
User selects slides
    → AssemblyPresenter manages list
    → User orders slides
    → DeliveryPresenter coordinates
    → ExportWorker generates PowerPoint
    → Progress reported to view
    → File opened or saved
```

## Error Handling Strategy

### 1. Service Layer
- Raise specific exceptions (DatabaseError, FileOperationError, etc.)
- Log errors with context
- Clean up resources in finally blocks

### 2. Presenter Layer
- Catch service exceptions
- Show appropriate user messages
- Log for debugging
- Maintain consistent state

### 3. UI Layer
- Standardized error dialogs
- User-friendly messages
- Option to report issues

## Performance Considerations

### 1. Database
- Connection pooling reduces overhead
- FTS5 for fast text search
- Indexed foreign keys
- Prepared statements

### 2. Thumbnail Cache
- LRU eviction policy
- Memory limit (100MB default)
- Disk persistence
- Lazy loading

### 3. Background Tasks
- Thread pool for parallel operations
- Progress reporting
- Cancellation support
- Resource cleanup

## Security Considerations

### 1. Input Validation
- Sanitize file paths
- Validate project names
- Check file types
- Prevent path traversal

### 2. Database
- Parameterized queries
- Input sanitization
- Transaction isolation

### 3. File Operations
- Safe path joining
- Permission checking
- Disk space validation

## Future Extensibility

The architecture supports several extension points:

### 1. New Export Formats
- Implement new export service
- Register with ServiceRegistry
- No presenter changes needed

### 2. Additional Storage Backends
- Implement IDatabaseService
- Could support cloud storage
- Transparent to presenters

### 3. Cross-platform Support
- Abstract PowerPoint operations
- Platform-specific implementations
- Same presenter logic

### 4. Plugin System
- Services as plugins
- Dynamic registration
- Configuration-based loading

## Conclusion

SLIDEMAN's architecture provides a solid foundation for a maintainable, testable, and extensible application. The clear separation of concerns, consistent patterns, and comprehensive testing ensure the codebase can evolve while maintaining quality.