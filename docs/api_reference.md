# SLIDEMAN API Reference

This document provides a comprehensive API reference for SLIDEMAN's core services and components.

## Table of Contents

1. [Services](#services)
2. [Presenters](#presenters)
3. [Commands](#commands)
4. [Models](#models)
5. [Events](#events)

## Services

### DatabaseService

The main database service providing thread-safe access to SQLite with FTS5 support.

```python
class IDatabaseService(Protocol):
    """Database service interface for data persistence."""
```

#### Key Methods

##### Project Operations

```python
def create_project(self, name: str, description: str = "") -> Project:
    """Create a new project.
    
    Args:
        name: Project name (must be unique)
        description: Optional project description
        
    Returns:
        Created Project object with assigned ID
        
    Raises:
        ValidationError: If name is empty or already exists
        DatabaseError: If creation fails
    """

def get_project(self, project_id: int) -> Optional[Project]:
    """Get project by ID.
    
    Args:
        project_id: Project ID
        
    Returns:
        Project object or None if not found
    """

def rename_project(self, project_id: int, new_name: str) -> bool:
    """Rename a project.
    
    Args:
        project_id: Project ID
        new_name: New project name
        
    Returns:
        True if successful
        
    Raises:
        ValidationError: If new name is invalid or duplicate
    """

def delete_project(self, project_id: int) -> bool:
    """Delete a project and all associated data.
    
    Args:
        project_id: Project ID
        
    Returns:
        True if successful
        
    Note:
        Cascades to delete all files, slides, elements, and keywords
    """
```

##### File Operations

```python
def create_file(
    self, 
    project_id: int, 
    name: str, 
    path: str, 
    size: int,
    total_slides: int = 0
) -> File:
    """Register a PowerPoint file in the database.
    
    Args:
        project_id: Parent project ID
        name: File name
        path: Full file path
        size: File size in bytes
        total_slides: Number of slides (updated after conversion)
        
    Returns:
        Created File object
    """

def update_file_status(
    self, 
    file_id: int, 
    status: FileStatus, 
    total_slides: Optional[int] = None
) -> None:
    """Update file processing status.
    
    Args:
        file_id: File ID
        status: New status (PENDING, CONVERTING, READY, ERROR)
        total_slides: Update slide count if provided
    """
```

##### Slide Operations

```python
def create_slide(
    self,
    file_id: int,
    slide_number: int,
    title: str,
    notes: str,
    thumbnail_path: str
) -> Slide:
    """Create a slide record.
    
    Args:
        file_id: Parent file ID
        slide_number: Slide number in presentation
        title: Slide title
        notes: Speaker notes
        thumbnail_path: Path to thumbnail image
        
    Returns:
        Created Slide object
    """

def search_slides(
    self,
    project_id: int,
    query: str,
    file_ids: Optional[List[int]] = None,
    keyword_ids: Optional[List[int]] = None
) -> List[Slide]:
    """Search slides with full-text search and filters.
    
    Args:
        project_id: Limit to project
        query: Search query for title/notes
        file_ids: Filter by specific files
        keyword_ids: Filter by keywords (AND condition)
        
    Returns:
        List of matching slides
    """
```

##### Keyword Operations

```python
def create_keyword(self, name: str) -> Keyword:
    """Create a new keyword.
    
    Args:
        name: Keyword name (case-insensitive unique)
        
    Returns:
        Created Keyword object
        
    Raises:
        ValidationError: If name is empty or duplicate
    """

def add_slide_keyword(self, slide_id: int, keyword_id: int) -> bool:
    """Associate keyword with slide.
    
    Args:
        slide_id: Slide ID
        keyword_id: Keyword ID
        
    Returns:
        True if successful (False if already exists)
    """

def get_keyword_usage_count(self, keyword_id: int) -> int:
    """Get total usage count for keyword.
    
    Args:
        keyword_id: Keyword ID
        
    Returns:
        Count of slides + elements using this keyword
    """
```

### FileIOService

Handles file system operations for projects.

```python
class IFileIOService(Protocol):
    """File I/O service interface."""
```

#### Key Methods

```python
def create_project_structure(self, project_name: str) -> Path:
    """Create project directory structure.
    
    Args:
        project_name: Project name
        
    Returns:
        Path to created project directory
        
    Raises:
        ValidationError: If project already exists
        FileOperationError: If creation fails
    """

def copy_file_to_project(self, source: Path, project_path: Path) -> Path:
    """Copy PowerPoint file to project.
    
    Args:
        source: Source file path
        project_path: Project directory
        
    Returns:
        Path to copied file in project/sources/
        
    Note:
        Handles duplicate names by adding suffix (_1, _2, etc.)
    """

def check_disk_space(self, path: Path, required_bytes: int) -> bool:
    """Check if sufficient disk space available.
    
    Args:
        path: Path to check
        required_bytes: Space needed
        
    Returns:
        True if sufficient space available
    """
```

### SlideConverterService

Converts PowerPoint slides to images using COM automation.

```python
class ISlideConverterService(Protocol):
    """Slide conversion service interface."""
```

#### Key Methods

```python
def convert_presentation(
    self,
    pptx_path: str,
    output_dir: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[Dict[str, Any]]:
    """Convert all slides in presentation to images.
    
    Args:
        pptx_path: Path to PowerPoint file
        output_dir: Directory for output images
        progress_callback: Called with (current, total)
        
    Returns:
        List of slide data dictionaries:
        {
            'slide_number': int,
            'title': str,
            'notes': str,
            'thumbnail_path': str,
            'shapes': List[Dict]  # Shape data
        }
        
    Raises:
        PowerPointError: If conversion fails
        ValidationError: If file not found
    """

def extract_slide_data(self, pptx_path: str, slide_number: int) -> Dict:
    """Extract detailed data from specific slide.
    
    Args:
        pptx_path: Path to PowerPoint file
        slide_number: 1-based slide number
        
    Returns:
        Slide data including shapes
    """
```

### ExportService

Exports selected slides to new PowerPoint presentations.

```python
class IExportService(Protocol):
    """Export service interface."""
```

#### Key Methods

```python
def export_presentation(
    self,
    slide_ids: List[int],
    output_path: str,
    include_notes: bool = True
) -> str:
    """Export slides to new presentation.
    
    Args:
        slide_ids: Ordered list of slide IDs
        output_path: Output file path
        include_notes: Include speaker notes
        
    Returns:
        Path to created presentation
        
    Raises:
        ExportError: If export fails
        ValidationError: If inputs invalid
    """

def validate_export(self, file_path: str) -> bool:
    """Validate exported presentation.
    
    Args:
        file_path: Path to presentation
        
    Returns:
        True if valid PowerPoint file
    """
```

## Presenters

### BasePresenter

Base class for all presenters in the MVP pattern.

```python
class BasePresenter:
    """Base presenter providing common functionality."""
    
    def __init__(self, view: IView, services: Optional[Dict[str, Any]] = None):
        """Initialize presenter.
        
        Args:
            view: View interface implementation
            services: Service instances (uses app_state if None)
        """
    
    def get_service(self, name: str) -> Optional[Any]:
        """Get service by name from registry."""
    
    def handle_error(
        self, 
        error: Exception, 
        title: str, 
        operation: str,
        show_dialog: bool = True
    ) -> None:
        """Handle and log errors consistently."""
```

### ProjectsPresenter

Manages project operations and file conversion.

```python
class ProjectsPresenter(BasePresenter):
    """Presenter for project management."""
    
    def load_projects(self) -> None:
        """Load and display all projects."""
    
    def create_project(self) -> None:
        """Create new project with PowerPoint files."""
    
    def delete_selected_project(self) -> None:
        """Delete currently selected project."""
    
    def rename_selected_project(self) -> None:
        """Rename currently selected project."""
    
    def convert_project_slides(self) -> None:
        """Start slide conversion for pending files."""
```

### SlideViewPresenter

Handles slide browsing and filtering.

```python
class SlideViewPresenter(BasePresenter):
    """Presenter for slide viewing and filtering."""
    
    def load_project_slides(self, project_id: Optional[int]) -> None:
        """Load slides for project."""
    
    def apply_filters(self) -> None:
        """Apply current filter criteria."""
    
    def add_keyword_to_selected(self, keyword: Keyword) -> None:
        """Add keyword to selected slides."""
    
    def get_selected_slides(self) -> List[Dict[str, Any]]:
        """Get currently selected slide data."""
```

## Commands

### BaseCommand

Base class for all undoable commands.

```python
class BaseCommand(QUndoCommand):
    """Base class for undoable commands."""
    
    def __init__(self, description: str, db_service: Optional[Database] = None):
        """Initialize command.
        
        Args:
            description: Command description for undo stack
            db_service: Database service (uses app_state if None)
        """
```

### Command Examples

```python
class RenameProjectCommand(BaseCommand):
    """Rename project with undo support."""
    
    def __init__(
        self,
        project_id: int,
        old_name: str,
        new_name: str,
        db_service: Optional[Database] = None
    ):
        """Initialize rename command."""
    
    def redo(self) -> None:
        """Execute rename operation."""
    
    def undo(self) -> None:
        """Revert to original name."""
    
    def mergeWith(self, other: QUndoCommand) -> bool:
        """Merge consecutive renames of same project."""
```

## Models

### Project

```python
@dataclass(frozen=True)
class Project:
    """Project containing PowerPoint files."""
    id: int
    name: str
    description: str
    path: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### File

```python
@dataclass(frozen=True)
class File:
    """PowerPoint file in a project."""
    id: int
    project_id: int
    name: str
    path: str
    size: int
    total_slides: int
    status: FileStatus
    created_at: Optional[datetime] = None
```

### Slide

```python
@dataclass(frozen=True)
class Slide:
    """Individual slide from a PowerPoint file."""
    id: int
    file_id: int
    slide_number: int
    title: str
    notes: str
    thumbnail_path: str
    created_at: Optional[datetime] = None
```

### Keyword

```python
@dataclass(frozen=True)
class Keyword:
    """Tag for categorizing slides and elements."""
    id: int
    name: str
    created_at: Optional[datetime] = None
```

## Events

SLIDEMAN uses Qt signals for decoupled communication between components.

### EventBus Signals

```python
class EventBus(QObject):
    """Application-wide event bus."""
    
    # Project events
    project_created = Signal(int)  # project_id
    project_deleted = Signal(int)  # project_id
    project_renamed = Signal(int, str)  # project_id, new_name
    
    # File events
    file_imported = Signal(int)  # file_id
    file_converted = Signal(int)  # file_id
    
    # Keyword events
    keyword_created = Signal(int)  # keyword_id
    keywords_merged = Signal(str, str)  # old_name, new_name
    
    # Slide events
    slide_keywords_changed = Signal(int)  # slide_id
    
    # Assembly events
    assembly_updated = Signal()  # Assembly changed
```

### Usage Example

```python
# Connect to event
event_bus.project_created.connect(self.on_project_created)

# Emit event
event_bus.project_created.emit(project_id)

# Disconnect
event_bus.project_created.disconnect(self.on_project_created)
```