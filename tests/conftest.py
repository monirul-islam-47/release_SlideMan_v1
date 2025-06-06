"""
Pytest configuration and shared fixtures for SLIDEMAN tests.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Generator, Any

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, QObject

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from slideman.models import Project, File, Slide, Element, Keyword, FileStatus
from slideman.services.database import Database
from slideman.services.service_registry import ServiceRegistry
from slideman.services.interfaces import (
    IDatabaseService, IFileIOService, IExportService, 
    IThumbnailCacheService, ISlideConverterService
)
from slideman.app_state import AppState


# Qt Application fixture
@pytest.fixture(scope='session')
def qapp():
    """Provide Qt Application for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()


# Temporary directory fixtures
@pytest.fixture
def temp_dir():
    """Provide a temporary directory that's cleaned up after test."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_project_dir(temp_dir):
    """Provide a temporary project directory structure."""
    project_dir = temp_dir / "test_project"
    project_dir.mkdir()
    (project_dir / "sources").mkdir()
    (project_dir / "thumbnails").mkdir()
    return project_dir


# Database fixtures
@pytest.fixture
def in_memory_db():
    """Provide an in-memory SQLite database."""
    db = Database(":memory:")
    db.initialize()
    yield db
    db.close()


@pytest.fixture
def populated_db(in_memory_db):
    """Provide a database populated with test data."""
    db = in_memory_db
    
    # Create test project
    project = db.create_project("Test Project", "Test Description")
    
    # Create test file
    file = db.create_file(
        project_id=project.id,
        name="test_presentation.pptx",
        path="/test/path/test_presentation.pptx",
        size=1024,
        total_slides=5
    )
    
    # Create test slides
    slides = []
    for i in range(5):
        slide = db.create_slide(
            file_id=file.id,
            slide_number=i + 1,
            title=f"Slide {i + 1}",
            notes=f"Notes for slide {i + 1}",
            thumbnail_path=f"/thumbnails/slide_{i + 1}.png"
        )
        slides.append(slide)
    
    # Create test keywords
    keywords = []
    for tag in ["important", "presentation", "demo"]:
        keyword = db.create_keyword(tag)
        keywords.append(keyword)
    
    # Associate keywords with slides
    db.add_slide_keyword(slides[0].id, keywords[0].id)
    db.add_slide_keyword(slides[0].id, keywords[1].id)
    db.add_slide_keyword(slides[1].id, keywords[2].id)
    
    yield db


# Mock service fixtures
@pytest.fixture
def mock_database_service():
    """Provide a mock database service."""
    mock = Mock(spec=IDatabaseService)
    
    # Setup default return values
    mock.get_all_projects.return_value = [
        Project(id=1, name="Test Project", description="Test", path="/test")
    ]
    mock.get_project.return_value = Project(
        id=1, name="Test Project", description="Test", path="/test"
    )
    mock.create_project.return_value = Project(
        id=2, name="New Project", description="New", path="/new"
    )
    
    return mock


@pytest.fixture
def mock_file_io_service():
    """Provide a mock file I/O service."""
    mock = Mock(spec=IFileIOService)
    
    mock.get_project_path.return_value = Path("/test/project")
    mock.create_project_structure.return_value = True
    mock.is_valid_powerpoint.return_value = True
    mock.copy_file_to_project.return_value = Path("/test/project/sources/file.pptx")
    
    return mock


@pytest.fixture
def mock_export_service():
    """Provide a mock export service."""
    mock = Mock(spec=IExportService)
    
    mock.export_presentation.return_value = "/output/presentation.pptx"
    mock.validate_export.return_value = True
    
    return mock


@pytest.fixture
def mock_thumbnail_cache():
    """Provide a mock thumbnail cache service."""
    mock = Mock(spec=IThumbnailCacheService)
    
    mock.get_thumbnail.return_value = "/path/to/thumbnail.png"
    mock.has_thumbnail.return_value = True
    mock.clear_cache.return_value = None
    
    return mock


@pytest.fixture
def mock_slide_converter():
    """Provide a mock slide converter service."""
    mock = Mock(spec=ISlideConverterService)
    
    mock.convert_presentation.return_value = [
        {"slide_number": 1, "title": "Slide 1", "notes": "Notes 1"},
        {"slide_number": 2, "title": "Slide 2", "notes": "Notes 2"}
    ]
    
    return mock


# Service registry fixture
@pytest.fixture
def service_registry(
    mock_database_service,
    mock_file_io_service,
    mock_export_service,
    mock_thumbnail_cache,
    mock_slide_converter
):
    """Provide a service registry with mock services."""
    registry = ServiceRegistry()
    
    registry.register('database', mock_database_service)
    registry.register('file_io', mock_file_io_service)
    registry.register('export', mock_export_service)
    registry.register('thumbnail_cache', mock_thumbnail_cache)
    registry.register('slide_converter', mock_slide_converter)
    
    return registry


# App state fixture
@pytest.fixture
def mock_app_state(service_registry):
    """Provide a mock app state."""
    state = Mock(spec=AppState)
    
    state.service_registry = service_registry
    state.db_service = service_registry.get('database')
    state.current_project = None
    state.assembly_slides = []
    
    return state


# Sample data fixtures
@pytest.fixture
def sample_project():
    """Provide a sample project."""
    return Project(
        id=1,
        name="Sample Project",
        description="A sample project for testing",
        path="/projects/sample"
    )


@pytest.fixture
def sample_file():
    """Provide a sample file."""
    return File(
        id=1,
        project_id=1,
        name="presentation.pptx",
        path="/projects/sample/sources/presentation.pptx",
        size=2048,
        total_slides=10,
        status=FileStatus.READY
    )


@pytest.fixture
def sample_slides():
    """Provide sample slides."""
    return [
        Slide(
            id=i,
            file_id=1,
            slide_number=i,
            title=f"Slide {i}",
            notes=f"Notes for slide {i}",
            thumbnail_path=f"/thumbnails/slide_{i}.png"
        )
        for i in range(1, 6)
    ]


@pytest.fixture
def sample_keywords():
    """Provide sample keywords."""
    return [
        Keyword(id=1, name="important"),
        Keyword(id=2, name="presentation"),
        Keyword(id=3, name="demo"),
        Keyword(id=4, name="sales")
    ]


# Mock view fixtures for presenter tests
@pytest.fixture
def mock_view():
    """Provide a generic mock view."""
    view = Mock()
    view.show_error = Mock()
    view.show_info = Mock()
    view.show_warning = Mock()
    view.update_ui = Mock()
    return view


# Worker thread fixture
@pytest.fixture
def mock_worker():
    """Provide a mock worker for background tasks."""
    worker = Mock(spec=QThread)
    worker.start = Mock()
    worker.quit = Mock()
    worker.wait = Mock()
    worker.isRunning = Mock(return_value=False)
    return worker


# PowerPoint COM mock
@pytest.fixture
def mock_powerpoint():
    """Provide a mock PowerPoint application (for Windows COM testing)."""
    mock_app = MagicMock()
    mock_app.Visible = False
    mock_app.Presentations = MagicMock()
    
    mock_presentation = MagicMock()
    mock_presentation.Slides = MagicMock()
    mock_presentation.Slides.Count = 5
    
    mock_app.Presentations.Open.return_value = mock_presentation
    
    return mock_app


# Event bus fixture
@pytest.fixture
def mock_event_bus():
    """Provide a mock event bus."""
    bus = Mock()
    bus.project_created = Mock()
    bus.project_deleted = Mock()
    bus.project_renamed = Mock()
    bus.file_imported = Mock()
    bus.keyword_created = Mock()
    bus.keyword_merged = Mock()
    return bus


# Utility fixtures
@pytest.fixture
def sample_pptx_file(temp_dir):
    """Create a sample PPTX file for testing."""
    # This would create an actual PPTX file if needed
    # For now, just create a dummy file
    pptx_path = temp_dir / "sample.pptx"
    pptx_path.write_bytes(b"DUMMY_PPTX_CONTENT")
    return pptx_path


@pytest.fixture
def mock_settings():
    """Provide mock application settings."""
    settings = Mock()
    settings.value = Mock(return_value=None)
    settings.setValue = Mock()
    return settings