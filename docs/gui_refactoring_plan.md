# SLIDEMAN GUI Refactoring Plan

## Overview
This document outlines a comprehensive refactoring plan to address the GUI issues identified in the SLIDEMAN application. The refactoring is organized into 6 phases, prioritized by impact and dependencies.

## Phase 1: Architecture & Foundation (2-3 weeks)

### 1.1 Implement Proper MVP/MVVM Pattern

#### Current Issues:
- Presenters exist but aren't properly utilized
- UI components directly access database and services
- Business logic mixed with presentation code
- Tight coupling to global app state

#### Refactoring Steps:

1. **Create View Interfaces**
   ```python
   # src/slideman/ui/interfaces/view_interfaces.py
   class IProjectsView(Protocol):
       def show_projects(self, projects: List[Project]) -> None: ...
       def show_error(self, message: str) -> None: ...
       def show_loading(self, loading: bool) -> None: ...
       def get_selected_project(self) -> Optional[Project]: ...
   ```

2. **Refactor Presenters to Handle All Business Logic**
   ```python
   # Example: Refactored ProjectsPresenter
   class ProjectsPresenter:
       def __init__(self, view: IProjectsView, service_registry: ServiceRegistry):
           self._view = view
           self._db_service = service_registry.get_database_service()
           self._file_service = service_registry.get_file_service()
           
       def load_projects(self):
           self._view.show_loading(True)
           # Move to background thread
           self._load_projects_async()
   ```

3. **Create ViewModels for Data Binding**
   ```python
   # src/slideman/ui/viewmodels/project_viewmodel.py
   class ProjectViewModel(QObject):
       projectsChanged = Signal(list)
       loadingChanged = Signal(bool)
       errorOccurred = Signal(str)
       
       def __init__(self, database_service):
           self._projects = []
           self._loading = False
   ```

4. **Dependency Injection Container**
   ```python
   # src/slideman/ui/container.py
   class DIContainer:
       def __init__(self):
           self._services = {}
           self._presenters = {}
           
       def register_service(self, name: str, factory: Callable):
           self._services[name] = factory
   ```

### 1.2 Decouple from Global State

1. **Replace AppState Singleton Usage**
   - Pass required state through constructors
   - Use signals for state changes
   - Implement proper state management pattern

2. **Create Application Context**
   ```python
   class ApplicationContext:
       def __init__(self):
           self.current_project = Observable[Optional[Project]]()
           self.current_file = Observable[Optional[File]]()
           self.theme = Observable[Theme]()
   ```

## Phase 2: Performance Optimization (2 weeks)

### 2.1 Background Database Operations

1. **Create Database Task Queue**
   ```python
   class DatabaseTaskQueue(QObject):
       def __init__(self, db_service):
           self._queue = Queue()
           self._worker = DatabaseWorker(db_service)
           
       def query_async(self, query_func, callback):
           task = DatabaseTask(query_func, callback)
           self._queue.put(task)
   ```

2. **Implement Async Presenters**
   ```python
   class AsyncProjectsPresenter(ProjectsPresenter):
       def load_projects(self):
           self._view.show_loading(True)
           
           def on_projects_loaded(projects):
               self._view.show_loading(False)
               self._view.show_projects(projects)
               
           self._db_queue.query_async(
               lambda: self._db_service.get_all_projects(),
               on_projects_loaded
           )
   ```

### 2.2 Virtual Scrolling for Large Collections

1. **Implement Virtual List Model**
   ```python
   class VirtualSlideListModel(QAbstractListModel):
       def __init__(self, page_size=50):
           self._page_size = page_size
           self._cache = LRUCache(maxsize=200)
           self._total_count = 0
           
       def data(self, index, role):
           if not index.isValid():
               return None
               
           row = index.row()
           if row not in self._cache:
               self._load_page(row // self._page_size)
   ```

2. **Create Virtual Table View**
   ```python
   class VirtualSlideTableView(QTableView):
       def __init__(self):
           super().__init__()
           self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
           self._model = VirtualSlideListModel()
   ```

### 2.3 Optimize Thumbnail Loading

1. **Async Thumbnail Provider**
   ```python
   class AsyncThumbnailProvider(QObject):
       thumbnailReady = Signal(str, QPixmap)
       
       def request_thumbnail(self, slide_id: str, size: QSize):
           task = ThumbnailTask(slide_id, size)
           QThreadPool.globalInstance().start(task)
   ```

2. **Implement Progressive Loading**
   - Load visible thumbnails first
   - Use placeholder images
   - Cancel pending requests on scroll

## Phase 3: UI Component Consolidation (1.5 weeks)

### 3.1 Create Unified Base Classes

1. **Base Preview Widget**
   ```python
   class BasePreviewWidget(QWidget):
       itemActivated = Signal(object)
       selectionChanged = Signal(list)
       
       def __init__(self, item_delegate_class):
           self._delegate_class = item_delegate_class
           self._setup_ui()
           
       @abstractmethod
       def get_item_size(self) -> QSize: ...
       
       @abstractmethod
       def create_context_menu(self, item) -> QMenu: ...
   ```

2. **Consolidate Preview Implementations**
   - Merge `SlidePreviewWidget`, `AssemblyPreviewWidget`, `DeliveryPreviewWidget`
   - Extract common functionality
   - Use composition for specific behaviors

### 3.2 Fix Theme System

1. **Implement Theme Manager**
   ```python
   class ThemeManager(QObject):
       themeChanged = Signal(Theme)
       
       def __init__(self):
           self._current_theme = Theme.DARK
           self._stylesheets = {}
           
       def load_theme(self, theme: Theme):
           if theme not in self._stylesheets:
               self._stylesheets[theme] = self._load_stylesheet(theme)
           return self._stylesheets[theme]
   ```

2. **Fix Resource Loading**
   ```python
   # Add to main_window.py
   def setup_theme(self):
       theme_manager = self.container.get_service('theme_manager')
       theme_manager.themeChanged.connect(self._apply_theme)
       
       # Load user preference
       settings = QSettings()
       theme = Theme(settings.value('theme', Theme.DARK))
       theme_manager.set_theme(theme)
   ```

3. **Enable Icons**
   - Verify resource compilation
   - Update icon paths in navigation
   - Add fallback text for missing icons

### 3.3 Responsive Layouts

1. **Create Responsive Navigation**
   ```python
   class ResponsiveNavigation(QWidget):
       def __init__(self):
           self._collapsed = False
           self._min_width = 50
           self._max_width = 200
           
       def resizeEvent(self, event):
           if event.size().width() < 800:
               self.collapse()
           else:
               self.expand()
   ```

2. **Implement Breakpoint System**
   ```python
   class BreakpointManager:
       MOBILE = 480
       TABLET = 768
       DESKTOP = 1024
       
       def get_breakpoint(self, width):
           if width < self.MOBILE:
               return Breakpoint.MOBILE
           # ...
   ```

## Phase 4: User Experience Enhancements (1.5 weeks)

### 4.1 Keyboard Shortcuts

1. **Create Shortcut Manager**
   ```python
   class ShortcutManager:
       def __init__(self, main_window):
           self._shortcuts = {}
           self._setup_default_shortcuts()
           
       def _setup_default_shortcuts(self):
           self.register('Ctrl+1', 'navigate.projects')
           self.register('Ctrl+2', 'navigate.slideview')
           self.register('Ctrl+Z', 'edit.undo')
           # ...
   ```

2. **Add Navigation Shortcuts**
   - Ctrl+1-5 for page navigation
   - Tab/Shift+Tab for focus navigation
   - Arrow keys for list navigation

### 4.2 Enhanced Tooltips

1. **Create Rich Tooltip System**
   ```python
   class RichTooltip(QToolTip):
       @staticmethod
       def show_slide_info(slide, pos):
           html = f'''
           <h3>{slide.title}</h3>
           <p>Keywords: {', '.join(slide.keywords)}</p>
           <p>Created: {slide.created_at}</p>
           '''
           QToolTip.showText(pos, html)
   ```

2. **Add Contextual Help**
   - Tooltip on hover for all toolbar actions
   - Extended tooltips with keyboard shortcuts
   - Status bar hints for current action

### 4.3 Loading States

1. **Create Loading Overlay**
   ```python
   class LoadingOverlay(QWidget):
       def __init__(self, parent):
           super().__init__(parent)
           self.setAttribute(Qt.WA_TransparentForMouseEvents)
           self._setup_ui()
           
       def show_with_message(self, message):
           self._label.setText(message)
           self.show()
           self.raise_()
   ```

2. **Implement Skeleton Screens**
   ```python
   class SkeletonLoader(QWidget):
       def __init__(self, item_count=10):
           self._create_skeleton_items(item_count)
           
       def _create_skeleton_items(self, count):
           # Create placeholder items with animation
   ```

### 4.4 Undo/Redo Visualization

1. **Create Undo History Widget**
   ```python
   class UndoHistoryWidget(QListWidget):
       def __init__(self, undo_stack):
           self._undo_stack = undo_stack
           undo_stack.indexChanged.connect(self._update_display)
           
       def _update_display(self):
           # Show command history with current position
   ```

2. **Add Visual Feedback**
   - Toast notifications for actions
   - Highlight changed elements
   - Show undo/redo in status bar

## Phase 5: Accessibility (1 week)

### 5.1 Screen Reader Support

1. **Add Accessible Names**
   ```python
   def make_accessible(widget, name, description=None):
       widget.setAccessibleName(name)
       if description:
           widget.setAccessibleDescription(description)
   ```

2. **Implement Accessible Actions**
   ```python
   class AccessibleSlideWidget(QWidget):
       def __init__(self):
           self.setFocusPolicy(Qt.StrongFocus)
           
       def keyPressEvent(self, event):
           if event.key() == Qt.Key_Space:
               self.activate()
   ```

### 5.2 Keyboard Navigation

1. **Focus Chain Management**
   ```python
   class FocusManager:
       def setup_focus_chain(self, widgets):
           for i in range(len(widgets) - 1):
               widgets[i].setTabOrder(widgets[i], widgets[i + 1])
   ```

2. **Implement Focus Indicators**
   ```css
   QWidget:focus {
       outline: 2px solid #007acc;
       outline-offset: 2px;
   }
   ```

### 5.3 High Contrast Mode

1. **Create High Contrast Theme**
   ```python
   class HighContrastTheme:
       BACKGROUND = "#000000"
       FOREGROUND = "#FFFFFF"
       ACCENT = "#FFFF00"
       BORDER = "#FFFFFF"
   ```

2. **Adjust Color Contrast**
   - Ensure WCAG AA compliance
   - Test with contrast analyzers
   - Provide contrast adjustment settings

## Phase 6: Testing & Documentation (1 week)

### 6.1 UI Testing Framework

1. **Setup pytest-qt**
   ```python
   # tests/ui/test_main_window.py
   def test_navigation(qtbot):
       window = MainWindow()
       qtbot.addWidget(window)
       
       # Test page switching
       qtbot.mouseClick(window.nav_buttons[1], Qt.LeftButton)
       assert window.stacked_widget.currentIndex() == 1
   ```

2. **Create UI Test Utilities**
   ```python
   class UITestHelper:
       @staticmethod
       def wait_for_signal(qtbot, signal, timeout=1000):
           with qtbot.waitSignal(signal, timeout=timeout):
               pass
   ```

### 6.2 Integration Tests

1. **Test User Workflows**
   ```python
   def test_slide_tagging_workflow(qtbot, mock_db):
       # Test complete workflow from selection to save
   ```

2. **Performance Tests**
   ```python
   def test_large_dataset_performance(qtbot, benchmark):
       # Test with 10,000 slides
       benchmark(load_slides, 10000)
   ```

### 6.3 Documentation

1. **Update Architecture Docs**
   - Document new MVP pattern
   - Add sequence diagrams
   - Update component relationships

2. **Create UI Guidelines**
   - Design patterns
   - Component usage
   - Styling conventions

## Implementation Timeline

| Phase | Duration | Dependencies | Priority |
|-------|----------|--------------|----------|
| 1. Architecture | 2-3 weeks | None | High |
| 2. Performance | 2 weeks | Phase 1 | High |
| 3. UI Components | 1.5 weeks | Phase 1 | Medium |
| 4. UX Enhancements | 1.5 weeks | Phase 3 | Medium |
| 5. Accessibility | 1 week | Phase 4 | Low |
| 6. Testing | 1 week | All phases | Low |

**Total Duration: 9-10 weeks**

## Risk Mitigation

1. **Backward Compatibility**
   - Maintain existing public APIs
   - Deprecate gradually
   - Provide migration guides

2. **Feature Flags**
   ```python
   class FeatureFlags:
       USE_VIRTUAL_SCROLLING = True
       USE_ASYNC_DATABASE = True
       USE_NEW_THEME_SYSTEM = False
   ```

3. **Incremental Rollout**
   - Test each phase thoroughly
   - Get user feedback early
   - Maintain rollback capability

## Success Metrics

1. **Performance**
   - UI response time < 100ms
   - Smooth scrolling at 60fps
   - Memory usage < 500MB for 10k slides

2. **User Experience**
   - All actions accessible via keyboard
   - No blocking UI operations
   - Clear loading feedback

3. **Code Quality**
   - 80%+ test coverage for UI
   - No direct database access in views
   - Clear separation of concerns

## Conclusion

This refactoring plan addresses all major issues identified in the GUI critique while maintaining functionality and improving maintainability. The phased approach allows for incremental improvements and reduces risk.

## Detailed Architecture Specification

### Architecture Overview

The refactored architecture follows a layered approach with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                        View Layer                            │
│  (Qt Widgets, Pages, Custom Components)                      │
├─────────────────────────────────────────────────────────────┤
│                     Presenter Layer                          │
│  (Business Logic, View Coordination)                         │
├─────────────────────────────────────────────────────────────┤
│                    ViewModel Layer                           │
│  (Data Binding, State Management)                            │
├─────────────────────────────────────────────────────────────┤
│                     Service Layer                            │
│  (Database, File I/O, Export, Background Tasks)              │
├─────────────────────────────────────────────────────────────┤
│                      Model Layer                             │
│  (Pure Data Classes: Project, Slide, Keyword)                │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

#### 1. **View Layer**
- **Purpose**: Handle UI rendering and user input
- **Responsibilities**:
  - Display data provided by presenters
  - Capture user interactions
  - NO business logic
  - NO direct service access
- **Key Classes**:
  - `ProjectsPage`, `SlideViewPage`, etc. (implement view interfaces)
  - Custom widgets like `SlideCanvas`, `TagEdit`
  - `MainWindow` (application shell)

#### 2. **Presenter Layer**
- **Purpose**: Orchestrate business logic and view updates
- **Responsibilities**:
  - Handle user actions from views
  - Coordinate service calls
  - Update views with results
  - Manage view state transitions
- **Key Classes**:
  - `ProjectsPresenter`, `SlideViewPresenter`, etc.
  - Command pattern implementations
  - Error handling and validation

#### 3. **ViewModel Layer**
- **Purpose**: Provide reactive data binding between presenters and views
- **Responsibilities**:
  - Hold view-specific state
  - Emit signals on data changes
  - Transform model data for view consumption
  - Cache computed properties
- **Key Classes**:
  - `ProjectViewModel`, `SlideViewModel`
  - `ObservableList`, `ObservableProperty`
  - Filter and sort state management

#### 4. **Service Layer**
- **Purpose**: Encapsulate business operations and external interactions
- **Responsibilities**:
  - Database operations
  - File system interactions
  - PowerPoint COM automation
  - Background task execution
- **Key Classes**:
  - `DatabaseService`, `FileIOService`
  - `SlideConverterService`, `ExportService`
  - `ThumbnailCache`, `BackgroundTaskManager`

#### 5. **Model Layer**
- **Purpose**: Define core data structures
- **Responsibilities**:
  - Pure data representation
  - NO Qt dependencies
  - NO business logic
  - Serialization/deserialization
- **Key Classes**:
  - `Project`, `File`, `Slide`, `Element`, `Keyword`
  - Value objects and enums

### Key Architectural Patterns

#### 1. **Dependency Injection**
```python
# src/slideman/ui/container.py
class DIContainer:
    def __init__(self):
        self._register_services()
        self._register_presenters()
        
    def _register_services(self):
        # Services are singletons
        self.register_singleton('database', DatabaseService)
        self.register_singleton('file_io', FileIOService)
        self.register_singleton('theme_manager', ThemeManager)
        
    def _register_presenters(self):
        # Presenters are created per view
        self.register_factory('projects_presenter', 
            lambda: ProjectsPresenter(
                self.get('database'),
                self.get('file_io')
            ))
```

#### 2. **View Interfaces (Protocol)**
```python
# src/slideman/ui/interfaces/view_interfaces.py
from typing import Protocol, List, Optional

class IProjectsView(Protocol):
    """Interface that ProjectsPage must implement"""
    
    def show_projects(self, projects: List[ProjectViewModel]) -> None:
        """Display list of projects"""
        ...
        
    def show_loading(self, loading: bool) -> None:
        """Show/hide loading indicator"""
        ...
        
    def show_error(self, message: str, details: Optional[str] = None) -> None:
        """Display error to user"""
        ...
        
    def get_selected_projects(self) -> List[ProjectViewModel]:
        """Return currently selected projects"""
        ...
```

#### 3. **Observable Pattern for State**
```python
# src/slideman/ui/state/observable.py
class Observable(Generic[T]):
    def __init__(self, initial_value: T):
        self._value = initial_value
        self._observers = []
        
    def get(self) -> T:
        return self._value
        
    def set(self, value: T) -> None:
        if self._value != value:
            self._value = value
            self._notify_observers()
            
    def subscribe(self, callback: Callable[[T], None]) -> Disposable:
        self._observers.append(callback)
        return Disposable(lambda: self._observers.remove(callback))
```

#### 4. **Command Pattern with Undo/Redo**
```python
# src/slideman/commands/base_command.py
class Command(QUndoCommand):
    def __init__(self, presenter, description: str):
        super().__init__(description)
        self.presenter = presenter
        
    def execute_async(self) -> None:
        """Override for async execution"""
        pass
```

### Implementation Notes for Other Agents

#### 1. **File Organization**
```
src/slideman/
├── ui/
│   ├── interfaces/          # View interfaces (Protocols)
│   │   ├── __init__.py
│   │   └── view_interfaces.py
│   ├── viewmodels/         # ViewModels for data binding
│   │   ├── __init__.py
│   │   └── project_viewmodel.py
│   ├── state/              # State management utilities
│   │   ├── __init__.py
│   │   ├── observable.py
│   │   └── application_context.py
│   ├── container.py        # DI container
│   └── pages/              # Existing pages (refactored)
├── presenters/             # Already exists, needs refactoring
└── services/               # Already exists, needs async wrappers
```

#### 2. **Migration Strategy**

**Step 1: Create Interfaces First**
- Don't modify existing code initially
- Create view interfaces that match current page APIs
- This allows gradual migration

**Step 2: Refactor One Page at a Time**
- Start with `ProjectsPage` as it's the entry point
- Extract all database calls to presenter
- Keep the same UI behavior

**Step 3: Add Async Gradually**
- Wrap existing synchronous services with async facades
- Use `QThreadPool` for database operations
- Add loading states to views

#### 3. **Critical Implementation Details**

**Thread Safety**:
```python
# WRONG - Direct database access from UI thread
def refresh_projects(self):
    projects = self.db_service.get_all_projects()  # Blocks UI!
    self.display_projects(projects)

# RIGHT - Async with callback
def refresh_projects(self):
    self.show_loading(True)
    self.presenter.load_projects_async(
        callback=lambda projects: self.display_projects(projects)
    )
```

**Signal Connections**:
```python
# Use Qt's queued connections for thread safety
signal.connect(slot, Qt.QueuedConnection)

# Disconnect signals in cleanup to prevent crashes
def cleanup(self):
    try:
        self.signal.disconnect()
    except TypeError:
        pass  # Already disconnected
```

**View Lifecycle**:
```python
class RefactoredPage(QWidget):
    def __init__(self, presenter: IPresenter):
        super().__init__()
        self.presenter = presenter
        self.presenter.set_view(self)  # Two-way binding
        
    def showEvent(self, event):
        super().showEvent(event)
        self.presenter.on_view_shown()  # Let presenter initialize
        
    def hideEvent(self, event):
        super().hideEvent(event)
        self.presenter.on_view_hidden()  # Let presenter cleanup
```

#### 4. **Testing Approach**

**Unit Tests**:
```python
# Test presenter without Qt
def test_projects_presenter_load():
    mock_view = Mock(spec=IProjectsView)
    mock_db = Mock(spec=DatabaseService)
    
    presenter = ProjectsPresenter(mock_view, mock_db)
    presenter.load_projects()
    
    mock_view.show_loading.assert_called_with(True)
    mock_db.get_all_projects.assert_called_once()
```

**Integration Tests**:
```python
# Test with real Qt widgets
def test_projects_page_integration(qtbot):
    container = create_test_container()
    page = ProjectsPage(container.get('projects_presenter'))
    qtbot.addWidget(page)
    
    # Simulate user action
    qtbot.mouseClick(page.refresh_button, Qt.LeftButton)
    
    # Wait for async operation
    qtbot.waitUntil(lambda: page.loading_overlay.isHidden())
```

#### 5. **Common Pitfalls to Avoid**

1. **Don't Access Global State**:
   ```python
   # WRONG
   from slideman.app_state import app_state
   current_project = app_state.current_project
   
   # RIGHT
   current_project = self.context.current_project.get()
   ```

2. **Don't Mix Concerns**:
   ```python
   # WRONG - View doing business logic
   class ProjectsPage:
       def delete_project(self):
           if self.db_service.has_slides(project):
               # Complex business logic here
   
   # RIGHT - Presenter handles logic
   class ProjectsPresenter:
       def delete_project(self, project):
           if self._can_delete_project(project):
               # Business logic here
   ```

3. **Don't Block the UI Thread**:
   ```python
   # WRONG
   slides = self.converter.convert_file(file_path)  # Takes 30 seconds!
   
   # RIGHT
   self.converter.convert_file_async(
       file_path,
       progress_callback=self.update_progress,
       completion_callback=self.on_conversion_complete
   )
   ```

#### 6. **Incremental Refactoring Checklist**

For each page/component:

- [ ] Create view interface
- [ ] Move all service calls to presenter
- [ ] Replace direct state access with context/observables
- [ ] Add loading states for async operations
- [ ] Implement proper error handling
- [ ] Add keyboard shortcuts
- [ ] Add accessibility attributes
- [ ] Write unit tests for presenter
- [ ] Write integration tests for view
- [ ] Update documentation

#### 7. **Code Review Guidelines**

When reviewing refactored code, check for:

1. **No database imports in UI files**
2. **All service calls go through presenters**
3. **Views only import from `ui/` package**
4. **Presenters don't import Qt widgets**
5. **ViewModels emit signals for all changes**
6. **Async operations show loading state**
7. **Errors are handled gracefully**
8. **Memory leaks prevented (disconnected signals)**
9. **Thread safety maintained**
10. **Tests cover both success and error paths**

### Final Notes

This architecture is designed to be implemented incrementally. You don't need to refactor everything at once. Start with one page, prove the pattern works, then apply it to others. The existing code can coexist with the refactored code during the transition period.

The key principle is **separation of concerns**: Views display, Presenters orchestrate, Services execute, Models represent. When in doubt, ask: "Does this code belong in this layer?" If you're doing database queries in a view or creating widgets in a presenter, you're in the wrong layer.