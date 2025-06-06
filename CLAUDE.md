# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SLIDEMAN is a PowerPoint slide management application built with Python and Qt. It allows users to organize PowerPoint files into projects, tag slides with keywords, and assemble new presentations from existing slides.

## Essential Commands

### Development Setup
```bash
# Install dependencies
pip install poetry
poetry install

# Compile Qt resources (required before running)
pyside6-rcc resources/resources.qrc -o src/slideman/resources_rc.py

# Run the application
python -m src.slideman
# or
python main.py
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/services/test_database.py

# Run with coverage
pytest --cov=src/slideman
```

### Building
```bash
# Create executable
pyinstaller slideman.spec

# Create Windows installer (requires Inno Setup)
iscc slideman.iss
```

## Architecture Overview

The application follows a layered architecture with clear separation of concerns:

### Core Patterns
- **State Management**: `AppState` singleton manages global application state
- **Event System**: `EventBus` provides Qt signals for decoupled communication
- **Commands**: All user actions implement QUndoCommand for undo/redo support
- **Services**: Headless business logic layer that can be used independently of Qt

### Key Components

1. **UI Layer** (`src/slideman/ui/`)
   - Main window with left-rail navigation
   - Pages: Projects, SlideView, Assembly, Delivery, KeywordManager
   - Custom widgets for slide preview and tagging

2. **Service Layer** (`src/slideman/services/`)
   - `database.py`: SQLite persistence with FTS5 search
   - `slide_converter.py`: PowerPoint to image conversion via COM automation
   - `file_io.py`: File operations and project structure management
   - `export_service.py`: PowerPoint assembly and export
   - `background_tasks.py`: Qt thread pool for async operations

3. **Command Layer** (`src/slideman/commands/`)
   - Undoable operations: rename_project, delete_project, manage keywords
   - Commands interact with services and emit signals

4. **Models** (`src/slideman/models/`)
   - Pure Python dataclasses: Project, File, Slide, Element, Keyword
   - No Qt dependencies in models

### Database Schema
- Projects contain Files
- Files contain Slides  
- Slides contain Elements
- Keywords can be associated with Slides, Elements, and Projects
- Full-text search enabled on slide titles and notes

### Threading Model
- Main thread: Qt UI
- Worker threads: Slide conversion, file operations
- Database operations: Currently synchronous (potential optimization area)

## Important Considerations

1. **PowerPoint COM**: Slide conversion requires Windows with PowerPoint installed
2. **Resource Compilation**: Must run `pyside6-rcc` before first run
3. **Database**: Uses SQLite with WAL mode, stored in user's AppData
4. **Thumbnails**: Cached in AppData/Local/SlideMan/thumbnails
5. **Qt Signals**: Used extensively - always check signal connections when debugging

## Known Issues (from analysis reports)
- Thread safety concerns in database access
- Some code duplication in UI components
- Inconsistent error handling patterns
- Missing comprehensive integration tests