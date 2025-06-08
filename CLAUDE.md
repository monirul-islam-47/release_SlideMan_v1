# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 CRITICAL ACTIVE PROJECT: PREZI TDD TUTORIAL COMPLETION

**URGENT PROJECT STATUS:** The PrezI TDD Tutorial in `docs/gemini_scripts/founders_briefcase/PREZI_TDD_TUTORIAL_MODULAR/` is INCOMPLETE and requires immediate continuation until 100% finished.

### 🚨 MANDATORY OBJECTIVES FOR ALL CLAUDE AGENTS

**AGENTS MUST CONTINUE WORKING ON THESE OBJECTIVES UNTIL COMPLETION. NO EXCEPTIONS.**

#### ☐ **OBJECTIVE 1: EXTRACT ALL EXISTING CONTENT**
- Extract ALL remaining content from `TDD_CICD_MASTERY_GUIDE.md` (currently only 6 of 40 modules extracted)
- Extract ALL knowledge from founders briefcase documents (CONSOLIDATED_FOUNDERS_BRIEFCASE.md, fnf_checklist.md, UXUID.md, SAD.md, etc.)
- Students will NOT have access to source materials - ALL knowledge must be distilled into the tutorial
- **CRITICAL:** PowerPoint COM integration and AI OpenAI content still unextracted

#### ☐ **OBJECTIVE 2: ORGANIZE INTO MODULAR STRUCTURE**
- Complete the 40-module structure in PREZI_TDD_TUTORIAL_MODULAR/
- Ensure each module is self-contained with prerequisites clearly marked
- Maintain progression: Foundations → Backend → Frontend → AI Features → Testing → CI/CD → Mastery

#### ☐ **OBJECTIVE 3: IDENTIFY AND FILL ALL GAPS**
- Students MUST be able to create the full PrezI application
- Every piece of code needed for working app must be provided
- All specifications from founders briefcase must be implemented
- **CRITICAL:** Create separate `/working_prezi_app/` folder with complete, runnable demonstration code

#### ☐ **OBJECTIVE 4: COMPLETE ALL MISSING MODULES**
- Write all 34 remaining modules (currently 6/40 complete)
- Include working code examples for every concept
- Provide step-by-step instructions that guarantee student success
- Ensure tutorial produces fully functional PrezI application as specified

### 📊 CURRENT STATUS TRACKING
- **Completed:** 6/40 modules (15%)
- **Critical Missing:** PowerPoint COM integration, AI features, Frontend (HTML/CSS/JS + Electron)
- **Risk Level:** HIGH - Students cannot build PrezI with current incomplete tutorial

### 🎯 SUCCESS CRITERIA
**The tutorial is only complete when:**
- All 40 modules are finished with working code
- Students can build complete PrezI app by following tutorial
- All features from fnf_checklist.md are implementable
- Working demonstration code exists in `/working_prezi_app/`
- Tutorial manifesto requirements are 100% satisfied

### 🚨 AGENT CONTINUATION PROTOCOL
1. **READ this CLAUDE.md first** - understand the objectives
2. **CHECK current progress** in PREZI_TDD_TUTORIAL_MODULAR/
3. **CONTINUE extraction** from TDD_CICD_MASTERY_GUIDE.md
4. **FILL GAPS** using founders briefcase specifications  
5. **CREATE missing modules** until all 40 complete
6. **BUILD working app** in demonstration folder
7. **REPEAT until 100% complete**

**NO AGENT should work on other tasks until these objectives are achieved.**

---

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

# Run with coverage and HTML report
pytest --cov=src/slideman --cov-report=html

# Run specific test categories using markers
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m gui               # GUI tests only
pytest -m "not slow"        # Skip slow tests

# Run tests matching a pattern
pytest -k "test_project"

# Run with verbose output
pytest -v
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
- **State Management**: `AppState` singleton manages global application state with thread-safe operations
- **Event System**: `EventBus` provides Qt signals for decoupled communication between components
- **Commands**: All user actions implement QUndoCommand for undo/redo support with transaction safety
- **Services**: Headless business logic layer that can be used independently of Qt
- **MVP Architecture**: Model-View-Presenter pattern separates UI from business logic
- **Dependency Injection**: `ServiceRegistry` provides loose coupling between components
- **Interface Segregation**: All services implement clear interfaces defined in `services/interfaces.py`

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
6. **Threading**: Database operations should use the thread-safe `DatabaseWorker` class
7. **Service Access**: Use `ServiceRegistry.get()` to access services rather than direct instantiation

## Development Workflow

When implementing new features:
1. **Define interfaces first** in `services/interfaces.py` for any new services
2. **Create presenter** in `presenters/` to handle business logic
3. **Implement commands** in `commands/` for undoable user actions
4. **Add view interface** and implement in UI layer
5. **Write tests** for all layers (presenter, service, command)
6. **Update service registry** to register new services

## Debugging Tips

- **Database issues**: Check `DatabaseWorker` thread safety, use transactions for multiple operations
- **UI freezing**: Ensure long operations use `BackgroundTaskService` 
- **Signal/slot issues**: Use `qWarning()` to debug signal emissions
- **Resource loading**: Verify `resources_rc.py` is compiled and up-to-date
- **COM errors**: Check PowerPoint is installed and accessible on Windows

## Known Issues (from analysis reports)
- Thread safety concerns in database access
- Some code duplication in UI components
- Inconsistent error handling patterns
- Missing comprehensive integration tests