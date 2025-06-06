# Phase 1: Architecture & Foundation Implementation Guide

## Overview
This phase establishes the foundational architecture patterns that all subsequent phases will build upon. The goal is to implement proper MVP/MVVM patterns, dependency injection, and decouple from global state without breaking existing functionality.

## Duration: 2-3 weeks

## Prerequisites
- Understanding of the existing codebase structure
- Familiarity with Qt signals/slots mechanism
- Knowledge of Python Protocol types and dependency injection patterns

## Step-by-Step Implementation

### Step 1: Create View Interfaces (Day 1-2)

#### 1.1 Create the interfaces package
```bash
mkdir -p src/slideman/ui/interfaces
touch src/slideman/ui/interfaces/__init__.py
touch src/slideman/ui/interfaces/view_interfaces.py
```

#### 1.2 Define view interfaces
Create `src/slideman/ui/interfaces/view_interfaces.py`:

```python
from typing import Protocol, List, Optional, Any
from PySide6.QtCore import QModelIndex

class IProjectsView(Protocol):
    """Interface for ProjectsPage"""
    
    def show_projects(self, projects: List[Any]) -> None:
        """Display list of projects"""
        ...
        
    def show_loading(self, loading: bool) -> None:
        """Show/hide loading indicator"""
        ...
        
    def show_error(self, message: str, details: Optional[str] = None) -> None:
        """Display error message"""
        ...
        
    def get_selected_project(self) -> Optional[Any]:
        """Get currently selected project"""
        ...
        
    def clear_selection(self) -> None:
        """Clear current selection"""
        ...
        
    def refresh_view(self) -> None:
        """Request view refresh"""
        ...

class ISlideViewView(Protocol):
    """Interface for SlideViewPage"""
    
    def show_slides(self, slides: List[Any]) -> None:
        """Display slides in grid/list"""
        ...
        
    def show_loading(self, loading: bool) -> None:
        """Show/hide loading state"""
        ...
        
    def update_slide_keywords(self, slide_id: int, keywords: List[str]) -> None:
        """Update keywords for specific slide"""
        ...
        
    def set_view_mode(self, mode: str) -> None:
        """Switch between grid/list view"""
        ...
        
    def get_selected_slides(self) -> List[Any]:
        """Get all selected slides"""
        ...

class IAssemblyView(Protocol):
    """Interface for AssemblyPage"""
    
    def add_slides_to_assembly(self, slides: List[Any]) -> None:
        """Add slides to assembly area"""
        ...
        
    def remove_slide_from_assembly(self, index: int) -> None:
        """Remove slide at index"""
        ...
        
    def reorder_slides(self, from_index: int, to_index: int) -> None:
        """Reorder slides in assembly"""
        ...
        
    def clear_assembly(self) -> None:
        """Clear all slides from assembly"""
        ...
        
    def show_export_dialog(self) -> Optional[str]:
        """Show export dialog and return path"""
        ...

class IKeywordManagerView(Protocol):
    """Interface for KeywordManagerPage"""
    
    def show_keywords(self, keywords: List[Any]) -> None:
        """Display keyword list with counts"""
        ...
        
    def show_merge_dialog(self, source: str, target: str) -> bool:
        """Show merge confirmation dialog"""
        ...
        
    def refresh_keyword_list(self) -> None:
        """Refresh the keyword display"""
        ...
```

### Step 2: Create ViewModels (Day 3-4)

#### 2.1 Create viewmodels package
```bash
mkdir -p src/slideman/ui/viewmodels
touch src/slideman/ui/viewmodels/__init__.py
touch src/slideman/ui/viewmodels/base_viewmodel.py
touch src/slideman/ui/viewmodels/project_viewmodel.py
```

#### 2.2 Create base ViewModel
Create `src/slideman/ui/viewmodels/base_viewmodel.py`:

```python
from PySide6.QtCore import QObject, Signal
from typing import TypeVar, Generic, Optional

T = TypeVar('T')

class ObservableProperty(QObject, Generic[T]):
    """Observable property that emits signals on change"""
    
    valueChanged = Signal(object)
    
    def __init__(self, initial_value: T):
        super().__init__()
        self._value = initial_value
        
    def get(self) -> T:
        return self._value
        
    def set(self, value: T) -> None:
        if self._value != value:
            old_value = self._value
            self._value = value
            self.valueChanged.emit(value)
            
    value = property(get, set)

class BaseViewModel(QObject):
    """Base class for all ViewModels"""
    
    loadingChanged = Signal(bool)
    errorOccurred = Signal(str, str)  # message, details
    
    def __init__(self):
        super().__init__()
        self._loading = ObservableProperty(False)
        self._loading.valueChanged.connect(self.loadingChanged.emit)
        
    @property
    def is_loading(self) -> bool:
        return self._loading.get()
        
    def set_loading(self, loading: bool) -> None:
        self._loading.set(loading)
        
    def show_error(self, message: str, details: str = "") -> None:
        self.errorOccurred.emit(message, details)
```

#### 2.3 Create ProjectViewModel
Create `src/slideman/ui/viewmodels/project_viewmodel.py`:

```python
from PySide6.QtCore import Signal
from typing import List, Optional
from .base_viewmodel import BaseViewModel, ObservableProperty
from ...models import Project

class ProjectViewModel(BaseViewModel):
    """ViewModel for project data"""
    
    projectsChanged = Signal(list)
    selectionChanged = Signal(object)  # Optional[Project]
    
    def __init__(self):
        super().__init__()
        self._projects = ObservableProperty[List[Project]]([])
        self._selected_project = ObservableProperty[Optional[Project]](None)
        
        self._projects.valueChanged.connect(self.projectsChanged.emit)
        self._selected_project.valueChanged.connect(self.selectionChanged.emit)
        
    @property
    def projects(self) -> List[Project]:
        return self._projects.get()
        
    def set_projects(self, projects: List[Project]) -> None:
        self._projects.set(projects)
        
    @property
    def selected_project(self) -> Optional[Project]:
        return self._selected_project.get()
        
    def select_project(self, project: Optional[Project]) -> None:
        self._selected_project.set(project)
        
    def add_project(self, project: Project) -> None:
        projects = self.projects.copy()
        projects.append(project)
        self.set_projects(projects)
        
    def remove_project(self, project: Project) -> None:
        projects = self.projects.copy()
        if project in projects:
            projects.remove(project)
            self.set_projects(projects)
            
            # Clear selection if removed project was selected
            if self.selected_project == project:
                self.select_project(None)
```

### Step 3: Create Dependency Injection Container (Day 5)

#### 3.1 Create DI container
Create `src/slideman/ui/container.py`:

```python
from typing import Dict, Any, Callable, TypeVar, Type
from PySide6.QtCore import QObject
import logging

T = TypeVar('T')

class ServiceLifetime:
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"

class DIContainer:
    """Dependency injection container for managing services and presenters"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._lifetime: Dict[str, str] = {}
        self.logger = logging.getLogger(__name__)
        
    def register_singleton(self, name: str, factory: Callable[[], T]) -> None:
        """Register a singleton service"""
        self._factories[name] = factory
        self._lifetime[name] = ServiceLifetime.SINGLETON
        
    def register_transient(self, name: str, factory: Callable[[], T]) -> None:
        """Register a transient service (new instance each time)"""
        self._factories[name] = factory
        self._lifetime[name] = ServiceLifetime.TRANSIENT
        
    def register_factory(self, name: str, factory: Callable[[], T]) -> None:
        """Alias for register_transient"""
        self.register_transient(name, factory)
        
    def get(self, name: str) -> Any:
        """Get a service by name"""
        if name not in self._factories:
            raise KeyError(f"Service '{name}' not registered")
            
        lifetime = self._lifetime.get(name, ServiceLifetime.TRANSIENT)
        
        if lifetime == ServiceLifetime.SINGLETON:
            if name not in self._singletons:
                self._singletons[name] = self._factories[name]()
                self.logger.debug(f"Created singleton: {name}")
            return self._singletons[name]
        else:
            instance = self._factories[name]()
            self.logger.debug(f"Created transient: {name}")
            return instance
            
    def get_typed(self, name: str, expected_type: Type[T]) -> T:
        """Get a service with type checking"""
        service = self.get(name)
        if not isinstance(service, expected_type):
            raise TypeError(f"Service '{name}' is not of type {expected_type}")
        return service

def create_container() -> DIContainer:
    """Factory function to create and configure the DI container"""
    container = DIContainer()
    
    # Register services (singletons)
    from ..services import DatabaseService, FileIOService, SlideConverterService
    from ..services import ExportService, ThumbnailCache
    from ..theme import ThemeManager
    from ..event_bus import EventBus
    
    container.register_singleton('event_bus', lambda: EventBus())
    container.register_singleton('database', lambda: DatabaseService())
    container.register_singleton('file_io', lambda: FileIOService())
    container.register_singleton('slide_converter', lambda: SlideConverterService())
    container.register_singleton('export_service', lambda: ExportService())
    container.register_singleton('thumbnail_cache', lambda: ThumbnailCache())
    container.register_singleton('theme_manager', lambda: ThemeManager())
    
    # Register presenters (transient - new instance per view)
    from ..presenters import (
        ProjectsPresenter, SlideViewPresenter, AssemblyPresenter,
        KeywordManagerPresenter, DeliveryPresenter
    )
    
    container.register_factory('projects_presenter', 
        lambda: ProjectsPresenter(
            container.get('database'),
            container.get('file_io'),
            container.get('event_bus')
        ))
        
    container.register_factory('slideview_presenter',
        lambda: SlideViewPresenter(
            container.get('database'),
            container.get('slide_converter'),
            container.get('event_bus')
        ))
        
    container.register_factory('assembly_presenter',
        lambda: AssemblyPresenter(
            container.get('export_service'),
            container.get('event_bus')
        ))
        
    container.register_factory('keyword_presenter',
        lambda: KeywordManagerPresenter(
            container.get('database'),
            container.get('event_bus')
        ))
        
    return container
```

### Step 4: Create Application Context (Day 6)

#### 4.1 Create state management utilities
Create `src/slideman/ui/state/application_context.py`:

```python
from PySide6.QtCore import QObject, Signal
from typing import Optional
from ..viewmodels.base_viewmodel import ObservableProperty
from ...models import Project, File, Slide
from ...theme import Theme

class ApplicationContext(QObject):
    """Application-wide state container to replace AppState singleton"""
    
    # Signals for state changes
    currentProjectChanged = Signal(object)  # Optional[Project]
    currentFileChanged = Signal(object)     # Optional[File]
    currentSlideChanged = Signal(object)    # Optional[Slide]
    themeChanged = Signal(Theme)
    
    def __init__(self):
        super().__init__()
        
        # Observable properties
        self._current_project = ObservableProperty[Optional[Project]](None)
        self._current_file = ObservableProperty[Optional[File]](None)
        self._current_slide = ObservableProperty[Optional[Slide]](None)
        self._theme = ObservableProperty[Theme](Theme.DARK)
        
        # Connect observables to signals
        self._current_project.valueChanged.connect(self.currentProjectChanged.emit)
        self._current_file.valueChanged.connect(self.currentFileChanged.emit)
        self._current_slide.valueChanged.connect(self.currentSlideChanged.emit)
        self._theme.valueChanged.connect(self.themeChanged.emit)
        
    @property
    def current_project(self) -> Optional[Project]:
        return self._current_project.get()
        
    def set_current_project(self, project: Optional[Project]) -> None:
        self._current_project.set(project)
        # Clear dependent state
        if project is None:
            self.set_current_file(None)
            self.set_current_slide(None)
            
    @property
    def current_file(self) -> Optional[File]:
        return self._current_file.get()
        
    def set_current_file(self, file: Optional[File]) -> None:
        self._current_file.set(file)
        # Clear dependent state
        if file is None:
            self.set_current_slide(None)
            
    @property
    def current_slide(self) -> Optional[Slide]:
        return self._current_slide.get()
        
    def set_current_slide(self, slide: Optional[Slide]) -> None:
        self._current_slide.set(slide)
        
    @property
    def theme(self) -> Theme:
        return self._theme.get()
        
    def set_theme(self, theme: Theme) -> None:
        self._theme.set(theme)
```

### Step 5: Refactor Presenters (Day 7-10)

#### 5.1 Update base presenter
Modify `src/slideman/presenters/base_presenter.py`:

```python
from abc import ABC, abstractmethod
from typing import Optional, Any
from PySide6.QtCore import QObject
import logging

class BasePresenter(ABC):
    """Base presenter with view lifecycle management"""
    
    def __init__(self):
        self._view: Optional[Any] = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def set_view(self, view: Any) -> None:
        """Bind view to presenter"""
        self._view = view
        self.on_view_attached()
        
    def get_view(self) -> Optional[Any]:
        """Get bound view"""
        return self._view
        
    @abstractmethod
    def on_view_attached(self) -> None:
        """Called when view is attached"""
        pass
        
    @abstractmethod
    def on_view_shown(self) -> None:
        """Called when view becomes visible"""
        pass
        
    @abstractmethod
    def on_view_hidden(self) -> None:
        """Called when view is hidden"""
        pass
        
    def cleanup(self) -> None:
        """Cleanup presenter resources"""
        self._view = None
```

#### 5.2 Refactor ProjectsPresenter
Update `src/slideman/presenters/projects_presenter.py`:

```python
from PySide6.QtCore import QObject, QThreadPool, Signal, Slot
from typing import Optional, List
from .base_presenter import BasePresenter
from ..ui.interfaces.view_interfaces import IProjectsView
from ..ui.viewmodels.project_viewmodel import ProjectViewModel
from ..services import DatabaseService, FileIOService
from ..event_bus import EventBus
from ..models import Project
from ..ui.utils.workers import DatabaseWorker
import logging

class ProjectsPresenter(BasePresenter, QObject):
    """Presenter for projects page - handles all business logic"""
    
    # Signals for async operations
    projectsLoaded = Signal(list)
    projectCreated = Signal(object)
    projectDeleted = Signal(object)
    
    def __init__(self, database: DatabaseService, file_io: FileIOService, event_bus: EventBus):
        BasePresenter.__init__(self)
        QObject.__init__(self)
        
        self._database = database
        self._file_io = file_io
        self._event_bus = event_bus
        self._viewmodel = ProjectViewModel()
        self._thread_pool = QThreadPool()
        
        # Connect viewmodel to internal handlers
        self._viewmodel.projectsChanged.connect(self._on_projects_changed)
        self._viewmodel.errorOccurred.connect(self._on_error)
        
    def on_view_attached(self) -> None:
        """Initialize when view is attached"""
        if self._view:
            # Connect view to viewmodel
            self._viewmodel.projectsChanged.connect(self._view.show_projects)
            self._viewmodel.loadingChanged.connect(self._view.show_loading)
            self._viewmodel.errorOccurred.connect(self._view.show_error)
            
    def on_view_shown(self) -> None:
        """Load data when view is shown"""
        self.load_projects()
        
    def on_view_hidden(self) -> None:
        """Cleanup when view is hidden"""
        # Cancel any pending operations
        self._thread_pool.clear()
        
    def load_projects(self) -> None:
        """Load projects asynchronously"""
        self._viewmodel.set_loading(True)
        
        def load_task():
            try:
                return self._database.get_all_projects()
            except Exception as e:
                self.logger.error(f"Failed to load projects: {e}")
                return None
                
        def on_loaded(result):
            self._viewmodel.set_loading(False)
            if result is not None:
                self._viewmodel.set_projects(result)
            else:
                self._viewmodel.show_error("Failed to load projects", 
                                         "Check database connection")
                
        worker = DatabaseWorker(load_task)
        worker.finished.connect(on_loaded)
        self._thread_pool.start(worker)
        
    def create_project(self, name: str, description: str = "") -> None:
        """Create new project"""
        self._viewmodel.set_loading(True)
        
        def create_task():
            try:
                # Create project in database
                project = self._database.create_project(name, description)
                # Create project directory
                self._file_io.create_project_directory(project.id)
                return project
            except Exception as e:
                self.logger.error(f"Failed to create project: {e}")
                return None
                
        def on_created(result):
            self._viewmodel.set_loading(False)
            if result:
                self._viewmodel.add_project(result)
                self.projectCreated.emit(result)
                self._event_bus.project_created.emit(result)
            else:
                self._viewmodel.show_error("Failed to create project",
                                         "Check permissions and try again")
                
        worker = DatabaseWorker(create_task)
        worker.finished.connect(on_created)
        self._thread_pool.start(worker)
        
    def delete_project(self, project: Project) -> None:
        """Delete project with confirmation"""
        if not self._view:
            return
            
        # This would typically show a confirmation dialog
        # For now, proceed with deletion
        self._viewmodel.set_loading(True)
        
        def delete_task():
            try:
                # Delete from database
                self._database.delete_project(project.id)
                # Delete project directory
                self._file_io.delete_project_directory(project.id)
                return True
            except Exception as e:
                self.logger.error(f"Failed to delete project: {e}")
                return False
                
        def on_deleted(success):
            self._viewmodel.set_loading(False)
            if success:
                self._viewmodel.remove_project(project)
                self.projectDeleted.emit(project)
                self._event_bus.project_deleted.emit(project.id)
            else:
                self._viewmodel.show_error("Failed to delete project",
                                         "Project may be in use")
                
        worker = DatabaseWorker(delete_task)
        worker.finished.connect(on_deleted)
        self._thread_pool.start(worker)
        
    def select_project(self, project: Optional[Project]) -> None:
        """Handle project selection"""
        self._viewmodel.select_project(project)
        if project:
            self._event_bus.project_selected.emit(project)
            
    @Slot(list)
    def _on_projects_changed(self, projects: List[Project]) -> None:
        """Handle projects list change"""
        self.projectsLoaded.emit(projects)
        
    @Slot(str, str)
    def _on_error(self, message: str, details: str) -> None:
        """Handle errors from viewmodel"""
        self.logger.error(f"{message}: {details}")
```

### Step 6: Refactor Pages to Use Presenters (Day 11-14)

#### 6.1 Update ProjectsPage
Modify `src/slideman/ui/pages/projects_page.py` to implement the interface:

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtWidgets import QTableView, QMessageBox, QProgressBar
from PySide6.QtCore import Qt, Slot
from typing import List, Optional
from ..interfaces.view_interfaces import IProjectsView
from ...presenters import ProjectsPresenter
from ...models import Project

class ProjectsPage(QWidget):
    """Projects page implementing IProjectsView interface"""
    
    def __init__(self, presenter: ProjectsPresenter):
        super().__init__()
        self.presenter = presenter
        self.presenter.set_view(self)
        
        # UI elements
        self.table_view = QTableView()
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.new_button = QPushButton("New Project")
        self.delete_button = QPushButton("Delete")
        self.refresh_button = QPushButton("Refresh")
        
        toolbar.addWidget(self.new_button)
        toolbar.addWidget(self.delete_button)
        toolbar.addStretch()
        toolbar.addWidget(self.refresh_button)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.table_view)
        
        self.setLayout(layout)
        
    def _connect_signals(self):
        """Connect UI signals to presenter"""
        self.new_button.clicked.connect(self._on_new_project)
        self.delete_button.clicked.connect(self._on_delete_project)
        self.refresh_button.clicked.connect(self.presenter.load_projects)
        self.table_view.selectionModel().currentRowChanged.connect(
            self._on_selection_changed
        )
        
    # Implement IProjectsView interface
    
    def show_projects(self, projects: List[Project]) -> None:
        """Display projects in table"""
        # Update table model with projects
        # This is simplified - you'd use a proper QAbstractTableModel
        pass
        
    def show_loading(self, loading: bool) -> None:
        """Show/hide loading indicator"""
        self.progress_bar.setVisible(loading)
        self.table_view.setEnabled(not loading)
        self.new_button.setEnabled(not loading)
        self.delete_button.setEnabled(not loading)
        
    def show_error(self, message: str, details: Optional[str] = None) -> None:
        """Show error dialog"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        if details:
            msg_box.setDetailedText(details)
        msg_box.exec()
        
    def get_selected_project(self) -> Optional[Project]:
        """Get currently selected project"""
        # Get from table selection
        return None
        
    def clear_selection(self) -> None:
        """Clear table selection"""
        self.table_view.clearSelection()
        
    def refresh_view(self) -> None:
        """Refresh the view"""
        self.presenter.load_projects()
        
    # View lifecycle methods
    
    def showEvent(self, event):
        """Called when page is shown"""
        super().showEvent(event)
        self.presenter.on_view_shown()
        
    def hideEvent(self, event):
        """Called when page is hidden"""
        super().hideEvent(event)
        self.presenter.on_view_hidden()
        
    # Private slots
    
    @Slot()
    def _on_new_project(self):
        """Handle new project button"""
        # Show dialog to get project details
        # For now, use dummy data
        self.presenter.create_project("New Project", "Description")
        
    @Slot()
    def _on_delete_project(self):
        """Handle delete project button"""
        project = self.get_selected_project()
        if project:
            self.presenter.delete_project(project)
            
    @Slot()
    def _on_selection_changed(self):
        """Handle table selection change"""
        project = self.get_selected_project()
        self.presenter.select_project(project)
```

### Step 7: Update Main Window (Day 15)

#### 7.1 Modify MainWindow to use DI container
Update `src/slideman/ui/main_window.py`:

```python
from PySide6.QtWidgets import QMainWindow, QStackedWidget
from PySide6.QtCore import Qt
from .container import DIContainer, create_container
from .state.application_context import ApplicationContext
from .pages import ProjectsPage, SlideViewPage, AssemblyPage
from .pages import DeliveryPage, KeywordManagerPage

class MainWindow(QMainWindow):
    """Main application window with dependency injection"""
    
    def __init__(self):
        super().__init__()
        
        # Create DI container and application context
        self.container = create_container()
        self.context = ApplicationContext()
        
        # Store in container for access by presenters
        self.container.register_singleton('app_context', lambda: self.context)
        
        self._setup_ui()
        self._setup_pages()
        self._connect_signals()
        
    def _setup_ui(self):
        """Setup main window UI"""
        self.setWindowTitle("SLIDEMAN")
        self.setMinimumSize(1200, 800)
        
        # Create stacked widget for pages
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Setup navigation, toolbar, etc.
        # ... existing code ...
        
    def _setup_pages(self):
        """Create and add pages with presenters"""
        # Create pages with injected presenters
        self.projects_page = ProjectsPage(
            self.container.get('projects_presenter')
        )
        self.slideview_page = SlideViewPage(
            self.container.get('slideview_presenter')
        )
        self.assembly_page = AssemblyPage(
            self.container.get('assembly_presenter')
        )
        self.delivery_page = DeliveryPage(
            self.container.get('delivery_presenter')
        )
        self.keyword_page = KeywordManagerPage(
            self.container.get('keyword_presenter')
        )
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.projects_page)
        self.stacked_widget.addWidget(self.slideview_page)
        self.stacked_widget.addWidget(self.assembly_page)
        self.stacked_widget.addWidget(self.delivery_page)
        self.stacked_widget.addWidget(self.keyword_page)
        
    def _connect_signals(self):
        """Connect application-wide signals"""
        # Connect context changes to UI updates
        self.context.currentProjectChanged.connect(self._on_project_changed)
        self.context.themeChanged.connect(self._on_theme_changed)
        
        # Connect event bus signals
        event_bus = self.container.get('event_bus')
        event_bus.project_selected.connect(self._on_project_selected)
        
    def _on_project_changed(self, project):
        """Handle project change in context"""
        # Update window title, enable/disable actions, etc.
        if project:
            self.setWindowTitle(f"SLIDEMAN - {project.name}")
        else:
            self.setWindowTitle("SLIDEMAN")
            
    def _on_theme_changed(self, theme):
        """Handle theme change"""
        theme_manager = self.container.get('theme_manager')
        stylesheet = theme_manager.load_theme(theme)
        self.setStyleSheet(stylesheet)
        
    def _on_project_selected(self, project):
        """Handle project selection from event bus"""
        self.context.set_current_project(project)
        # Switch to slideview page
        self.stacked_widget.setCurrentWidget(self.slideview_page)
```

### Step 8: Create Database Worker Utility (Day 16)

Create `src/slideman/ui/utils/workers.py`:

```python
from PySide6.QtCore import QObject, QRunnable, Signal, Slot
from typing import Callable, Any, Optional
import traceback
import logging

class WorkerSignals(QObject):
    """Signals for worker threads"""
    finished = Signal(object)  # Result
    error = Signal(str, str)   # Error message, traceback
    progress = Signal(int)     # Progress percentage

class DatabaseWorker(QRunnable):
    """Worker for database operations"""
    
    def __init__(self, fn: Callable[[], Any], *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.logger = logging.getLogger(__name__)
        
    @Slot()
    def run(self):
        """Execute the function"""
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            self.logger.error(f"Worker error: {e}")
            tb = traceback.format_exc()
            self.signals.error.emit(str(e), tb)
            self.signals.finished.emit(None)

class AsyncTaskRunner:
    """Helper for running async tasks with proper error handling"""
    
    def __init__(self, thread_pool):
        self.thread_pool = thread_pool
        self.logger = logging.getLogger(__name__)
        
    def run_async(self, 
                  task: Callable[[], Any],
                  on_success: Optional[Callable[[Any], None]] = None,
                  on_error: Optional[Callable[[str, str], None]] = None,
                  on_progress: Optional[Callable[[int], None]] = None) -> DatabaseWorker:
        """Run task asynchronously with callbacks"""
        
        worker = DatabaseWorker(task)
        
        if on_success:
            worker.signals.finished.connect(on_success)
        if on_error:
            worker.signals.error.connect(on_error)
        if on_progress:
            worker.signals.progress.connect(on_progress)
            
        self.thread_pool.start(worker)
        return worker
```

## Testing Strategy

### Unit Tests
Create tests for each new component:

```python
# tests/ui/test_viewmodels.py
import pytest
from src.slideman.ui.viewmodels import ProjectViewModel
from src.slideman.models import Project

def test_project_viewmodel_signals():
    """Test that viewmodel emits correct signals"""
    vm = ProjectViewModel()
    
    # Track signal emissions
    projects_changed = []
    vm.projectsChanged.connect(lambda p: projects_changed.append(p))
    
    # Add project
    project = Project(id=1, name="Test")
    vm.add_project(project)
    
    assert len(projects_changed) == 1
    assert project in vm.projects

# tests/ui/test_container.py
def test_di_container_singleton():
    """Test singleton registration"""
    container = DIContainer()
    
    call_count = 0
    def factory():
        nonlocal call_count
        call_count += 1
        return object()
        
    container.register_singleton('test', factory)
    
    obj1 = container.get('test')
    obj2 = container.get('test')
    
    assert obj1 is obj2
    assert call_count == 1
```

### Integration Tests
```python
# tests/integration/test_mvp_integration.py
def test_projects_page_presenter_integration(qtbot):
    """Test page and presenter work together"""
    container = create_test_container()
    presenter = container.get('projects_presenter')
    page = ProjectsPage(presenter)
    
    qtbot.addWidget(page)
    
    # Verify presenter is connected
    assert presenter.get_view() is page
    
    # Test loading projects
    with qtbot.waitSignal(presenter.projectsLoaded, timeout=1000):
        presenter.load_projects()
```

## Migration Checklist

- [ ] Create view interfaces for all pages
- [ ] Create ViewModels for data binding
- [ ] Set up DI container with service registration
- [ ] Create ApplicationContext to replace AppState
- [ ] Refactor each presenter to handle business logic
- [ ] Update each page to implement view interface
- [ ] Remove direct database access from UI components
- [ ] Add async operations with loading states
- [ ] Update MainWindow to use DI container
- [ ] Write comprehensive tests
- [ ] Update documentation

## Common Pitfalls and Solutions

### 1. Circular Dependencies
**Problem**: Presenter depends on view, view depends on presenter
**Solution**: Use interfaces and setter injection

### 2. Memory Leaks
**Problem**: Signal connections not cleaned up
**Solution**: Always disconnect in cleanup methods

### 3. Thread Safety
**Problem**: UI updates from worker threads
**Solution**: Use Qt's signal/slot mechanism with queued connections

### 4. State Synchronization
**Problem**: Multiple components need same state
**Solution**: Use ApplicationContext with signals

## Validation Criteria

1. **No direct database access in UI layer**
   - Search for `DatabaseService` imports in `ui/pages/`
   - Should only exist in presenters

2. **All async operations show loading state**
   - Check that every database call uses workers
   - Verify loading indicators appear

3. **Proper separation of concerns**
   - Views only handle display logic
   - Presenters contain all business logic
   - Services handle data access

4. **Tests pass**
   - All existing tests still pass
   - New components have test coverage

## Next Steps

After completing Phase 1:
1. Monitor application performance
2. Gather feedback on responsiveness
3. Identify any remaining coupling issues
4. Proceed to Phase 2 (Performance Optimization)