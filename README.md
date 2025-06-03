# SLIDEMAN

A powerful PowerPoint slide management application that revolutionizes how you organize, search, and reuse presentation content. SLIDEMAN enables you to build a searchable library of slides from multiple PowerPoint files, tag them with keywords, and quickly assemble new presentations from your existing content.

## 🌟 Key Features

### 📁 Project Management
- **Create Projects**: Organize PowerPoint files (.pptx) into structured projects
- **Batch Import**: Add multiple PowerPoint files to a project at once
- **Smart Organization**: Automatic folder structure creation in `~/Documents/SlidemanProjects/`
- **Project Operations**: Rename, delete, and manage projects with full undo/redo support
- **Conversion Tracking**: Monitor slide conversion status for each file

### 🖼️ Slide Processing & Viewing
- **Automated Conversion**: Convert PowerPoint slides to high-quality images using COM automation
- **Thumbnail Generation**: Automatic thumbnail creation for fast browsing
- **Gallery View**: Browse all slides in a project with thumbnail previews
- **Full Resolution Display**: View slides at full resolution with zoom capabilities
- **Multi-file Support**: Filter and view slides from specific PowerPoint files

### 🏷️ Advanced Tagging System
- **Three-tier Keyword System**:
  - **Topic Tags**: High-level subject categorization
  - **Title Tags**: Specific slide titles and descriptions
  - **Name Tags**: Tag individual elements within slides
- **Element-level Tagging**: Click on shapes, images, charts, and tables to tag them individually
- **Visual Feedback**: Bounding box highlighting for selected elements
- **Auto-complete**: Smart suggestions based on existing keywords

### 🔍 Powerful Search & Assembly
- **Keyword Search**: Find slides by any combination of keywords
- **Fuzzy Matching**: Automatically detect and merge similar keywords
- **Cross-project Search**: Search across all projects or limit to current project
- **Assembly Workflow**:
  1. Search and collect keywords in a basket
  2. Preview associated slides
  3. Build final slide set with drag-and-drop ordering
  4. Export to new PowerPoint presentation

### 📤 Export & Delivery
- **PowerPoint Export Options**:
  - Open directly in PowerPoint for immediate editing
  - Save as new PPTX file to specified location
- **Format Preservation**: Maintains original slide formatting and layouts
- **Progress Tracking**: Real-time progress during export operations
- **Error Handling**: Graceful handling of missing source files

### 🎯 Keyword Management
- **Comprehensive Overview**: Table view showing all slides with their keywords
- **Bulk Editing**: Edit tags for multiple slides simultaneously
- **Usage Statistics**: View keyword usage across your library
- **CSV Export**: Export keyword data for external analysis
- **Similarity Detection**: Find and merge duplicate keywords with 80%+ similarity
- **Visual Indicators**: Highlight slides missing keywords

### 🎨 Modern User Interface
- **Dark Theme**: Eye-friendly dark mode interface
- **Left-rail Navigation**: Quick access to all major features
- **Responsive Design**: Adjustable thumbnail sizes and layouts
- **Status Feedback**: Real-time status updates and progress bars
- **Icon Library**: Comprehensive icon set from CoreUI Icons

### ⚡ Technical Features
- **Multi-threaded**: Background processing for smooth UI performance
- **Database-backed**: SQLite with full-text search (FTS5) capabilities
- **Undo/Redo System**: Full command pattern implementation
- **Thumbnail Caching**: Intelligent caching for fast performance
- **Thread-safe**: Proper handling of concurrent operations

## 🚀 Getting Started

### Prerequisites
- Windows OS (required for PowerPoint COM automation)
- Python 3.9 or higher
- Microsoft PowerPoint installed
- Poetry package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SLIDEMAN
   ```

2. **Create virtual environment**
   ```bash
   python -3.9 -m venv .venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source .venv/bin/activate
   ```

4. **Install Poetry and dependencies**
   ```bash
   pip install poetry
   poetry install
   ```

5. **Compile Qt resources** (Required before first run)
   ```bash
   pyside6-rcc resources/resources.qrc -o src/slideman/resources_rc.py
   ```

### Running the Application

```bash
python -m src.slideman
# or
python main.py
```

## 📋 Typical Workflow

1. **Create a Project**: Start by creating a new project and adding your PowerPoint files
2. **Process Slides**: Let SLIDEMAN convert your slides to searchable images
3. **Tag Content**: Add topic tags to slides and name tags to specific elements
4. **Search & Collect**: Use keywords to find relevant slides across your library
5. **Assemble**: Build custom presentations by selecting and ordering slides
6. **Export**: Generate new PowerPoint files with your assembled content

## 🏗️ Architecture

SLIDEMAN follows a clean layered architecture with Model-View-Presenter (MVP) pattern:

### Architecture Layers

1. **Model Layer** (Pure Python)
   - Domain objects as dataclasses (Project, File, Slide, Element, Keyword)
   - No framework dependencies
   - Immutable data structures

2. **Service Layer** (Business Logic)
   - **Database Service**: Thread-safe SQLite operations with connection pooling
   - **FileIO Service**: Project structure and file management
   - **SlideConverter**: PowerPoint COM automation for slide conversion
   - **ExportService**: PowerPoint generation from selected slides
   - **ThumbnailCache**: LRU cache with memory management
   - **ServiceRegistry**: Dependency injection container

3. **Presenter Layer** (MVP Pattern)
   - **ProjectsPresenter**: Project lifecycle and file conversion
   - **SlideViewPresenter**: Slide browsing and filtering
   - **AssemblyPresenter**: Slide selection and ordering
   - **DeliveryPresenter**: Export coordination
   - **KeywordManagerPresenter**: Tagging and keyword operations

4. **Command Layer** (Undo/Redo)
   - All user actions implemented as QUndoCommand
   - Full undo/redo support with command merging
   - Database transaction support

5. **UI Layer** (PySide6/Qt)
   - Pages implement view interfaces (IProjectsView, etc.)
   - Reusable components and mixins
   - Custom widgets for specialized functionality
   - Separation of concerns with no business logic

### Key Design Patterns

- **MVP (Model-View-Presenter)**: Separates UI from business logic
- **Dependency Injection**: ServiceRegistry provides loose coupling
- **Command Pattern**: All modifications are undoable
- **Singleton**: AppState and ThumbnailCache
- **Factory Pattern**: UI component creation
- **Observer Pattern**: Qt signals for event propagation

## 📁 Project Structure

```
SLIDEMAN/
├── src/slideman/
│   ├── models/          # Pure Python domain models
│   ├── services/        # Business logic services
│   │   ├── interfaces.py    # Service interfaces
│   │   ├── database.py      # Thread-safe database operations
│   │   ├── file_io.py       # File system operations
│   │   ├── slide_converter.py # PowerPoint COM automation
│   │   ├── export_service.py # Presentation generation
│   │   └── service_registry.py # Dependency injection
│   ├── presenters/      # MVP presenters
│   │   ├── base_presenter.py
│   │   ├── projects_presenter.py
│   │   ├── slideview_presenter.py
│   │   └── ...
│   ├── commands/        # Undo/redo commands
│   │   ├── base_command.py
│   │   ├── delete_project.py
│   │   └── ...
│   ├── ui/             # User interface
│   │   ├── pages/          # Main UI pages
│   │   ├── components/     # Reusable UI components
│   │   ├── utils/          # UI utilities
│   │   └── widgets/        # Custom widgets
│   ├── app_state.py    # Global application state
│   └── event_bus.py    # Application-wide events
├── resources/          # Icons and stylesheets
│   ├── icons/         # CoreUI icon set
│   └── qss/           # Qt stylesheets
├── tests/             # Comprehensive test suite
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   ├── presenters/    # Presenter tests
│   ├── services/      # Service tests
│   └── commands/      # Command tests
└── docs/              # Documentation
```

## 🧪 Testing

SLIDEMAN includes a comprehensive test suite with >80% code coverage:

### Test Categories

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test complete workflows (project creation, keyword management, export)
- **Presenter Tests**: Test MVP presenter logic
- **Service Tests**: Test business logic services
- **Command Tests**: Test undo/redo functionality

### Running Tests

```bash
# All tests with coverage report
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/presenters/

# Run with coverage report
pytest --cov=src/slideman --cov-report=html

# Run specific test file
pytest tests/services/test_database.py

# Run tests matching pattern
pytest -k "test_project"

# Run with verbose output
pytest -v
```

### Test Configuration

- Configuration: `pytest.ini` and `.coveragerc`
- Fixtures: `tests/conftest.py` provides shared test fixtures
- Markers: Use `@pytest.mark.gui` for GUI tests, `@pytest.mark.slow` for slow tests

## 📦 Building

### Create Executable
```bash
pyinstaller slideman.spec
```

### Create Windows Installer
Requires [Inno Setup](https://jrsoftware.org/isinfo.php) installed:
```bash
iscc slideman.iss
```

## 🔧 Configuration

- **Database Location**: `%APPDATA%/SlideMan/slideman.db`
- **Thumbnail Cache**: `%LOCALAPPDATA%/SlideMan/thumbnails/`
- **Project Storage**: `~/Documents/SlidemanProjects/`

## 🛠️ Development

### Development Setup

1. Install development dependencies:
   ```bash
   poetry install --with dev
   ```

2. Install pre-commit hooks (if available):
   ```bash
   pre-commit install
   ```

3. Run linting:
   ```bash
   # Python linting
   ruff check src/
   
   # Type checking
   mypy src/
   ```

### Code Style

- Follow PEP 8 for Python code
- Use type hints for all function signatures
- Write docstrings for all public methods
- Keep methods focused and under 50 lines
- Use descriptive variable names

### Adding New Features

1. **Create a presenter** for business logic (inherits from BasePresenter)
2. **Define view interface** for UI contract
3. **Implement commands** for user actions (inherits from BaseCommand)
4. **Add service methods** if needed
5. **Create UI page** implementing the view interface
6. **Write tests** for all new code

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Read the architecture documentation in `docs/`
2. Follow the existing code patterns
3. Write tests for new functionality
4. Update documentation as needed
5. Submit PR with clear description

### Areas for Contribution

- Performance optimizations
- Additional export formats
- Enhanced search capabilities
- UI/UX improvements
- Cross-platform support (Mac/Linux)

## 📄 License

[License information to be added]

## 🙏 Acknowledgments

- Built with [PySide6](https://doc.qt.io/qtforpython/) for the Qt framework
- Icons from [CoreUI Icons](https://coreui.io/icons/)
- Database powered by [SQLite](https://www.sqlite.org/) with FTS5

