# src/slideman/tests/services/test_database.py

import pytest
import sqlite3 # For catching specific errors if needed
from pathlib import Path

# Assuming your models and service are importable relative to the tests directory
# Adjust imports based on your exact project structure and how pytest discovers tests
from slideman.services.database import Database
from slideman.models.project import Project # Import the model to check return types
from slideman.models.file import File
from slideman.models.slide import Slide
from slideman.models.element import Element
from slideman.models.keyword import Keyword, KeywordKind

@pytest.fixture
def temp_db() -> Database:
    """
    Pytest fixture to create an in-memory SQLite database for testing.
    Yields a connected Database instance and ensures cleanup.
    """
    # Use :memory: for a temporary, in-memory database
    # Alternatively, use tmp_path fixture from pytest for a file-based temp DB:
    # db_path = tmp_path / "test_project_crud.db"
    # db = Database(db_path)
    db = Database(Path(":memory:")) # Using in-memory DB

    # Connect and ensure schema is created within the fixture
    connected = db.connect()
    assert connected, "Failed to connect to in-memory database for testing"

    yield db # Provide the connected Database instance to the test function

    # Teardown: Close the connection after the test runs
    db.close()

# --- Test Cases ---

def test_add_and_get_project(temp_db: Database):
    """Test adding a project and retrieving it by ID and path."""
    name = "My Test Project"
    path = "/path/to/my_test_project"

    # Add the project
    project_id = temp_db.add_project(name, path)
    assert project_id is not None
    assert isinstance(project_id, int)
    assert project_id > 0

    # Retrieve by ID
    retrieved_by_id = temp_db.get_project_by_id(project_id)
    assert retrieved_by_id is not None
    assert isinstance(retrieved_by_id, Project)
    assert retrieved_by_id.id == project_id
    assert retrieved_by_id.name == name
    assert retrieved_by_id.folder_path == path
    assert retrieved_by_id.created_at is not None # Should have a default value

    # Retrieve by Path
    retrieved_by_path = temp_db.get_project_by_path(path)
    assert retrieved_by_path is not None
    assert isinstance(retrieved_by_path, Project)
    assert retrieved_by_path.id == project_id # Check ID matches
    assert retrieved_by_path.name == name
    assert retrieved_by_path.folder_path == path

def test_get_non_existent_project(temp_db: Database):
    """Test retrieving projects that don't exist returns None."""
    assert temp_db.get_project_by_id(999) is None
    assert temp_db.get_project_by_path("/non/existent/path") is None

def test_get_all_projects_empty(temp_db: Database):
    """Test retrieving all projects when the database is empty."""
    projects = temp_db.get_all_projects()
    assert isinstance(projects, list)
    assert len(projects) == 0

def test_get_all_projects_multiple(temp_db: Database):
    """Test retrieving multiple projects, checking order."""
    id1 = temp_db.add_project("Project Zeta", "/path/zeta")
    id2 = temp_db.add_project("Project Alpha", "/path/alpha")
    id3 = temp_db.add_project("project beta", "/path/beta") # Test case insensitivity

    projects = temp_db.get_all_projects()
    assert len(projects) == 3
    assert isinstance(projects[0], Project)

    # Check sorting (case-insensitive)
    assert projects[0].name == "Project Alpha"
    assert projects[0].id == id2
    assert projects[1].name == "project beta"
    assert projects[1].id == id3
    assert projects[2].name == "Project Zeta"
    assert projects[2].id == id1

def test_add_project_duplicate_path(temp_db: Database):
    """Test that adding a project with a duplicate path fails."""
    path = "/path/duplicate"
    temp_db.add_project("Project One", path)
    # Adding again with the same path should fail due to UNIQUE constraint
    project_id_2 = temp_db.add_project("Project Two", path)
    assert project_id_2 is None

    # Verify only one project exists
    projects = temp_db.get_all_projects()
    assert len(projects) == 1
    assert projects[0].name == "Project One"

def test_rename_project(temp_db: Database):
    """Test renaming an existing project."""
    name = "Original Name"
    path = "/path/rename"
    project_id = temp_db.add_project(name, path)
    assert project_id is not None

    new_name = "Updated Name"
    renamed = temp_db.rename_project(project_id, new_name)
    assert renamed is True

    # Verify the name change
    retrieved = temp_db.get_project_by_id(project_id)
    assert retrieved is not None
    assert retrieved.name == new_name
    assert retrieved.folder_path == path # Path should be unchanged

def test_rename_non_existent_project(temp_db: Database):
    """Test that renaming a non-existent project fails gracefully."""
    renamed = temp_db.rename_project(999, "Doesn't Matter")
    assert renamed is False

def test_delete_project(temp_db: Database):
    """Test deleting an existing project."""
    project_id = temp_db.add_project("To Be Deleted", "/path/delete")
    assert temp_db.get_project_by_id(project_id) is not None # Verify it exists

    deleted = temp_db.delete_project(project_id)
    assert deleted is True

    # Verify it's gone
    assert temp_db.get_project_by_id(project_id) is None
    assert len(temp_db.get_all_projects()) == 0

def test_delete_non_existent_project(temp_db: Database):
    """Test that deleting a non-existent project fails gracefully."""
    deleted = temp_db.delete_project(999)
    assert deleted is False

# Optional: Test ON DELETE CASCADE later when File model and add_file exist
# def test_delete_project_cascades(temp_db: Database):
#     # Add project
#     # Add file linked to project
#     # Delete project
#     # Verify file is also deleted (e.g., db.get_file_by_id returns None)
#     pass

# --- File CRUD Tests ---

def test_add_and_get_file(temp_db: Database):
    """Test adding a file and retrieving it."""
    # First create a project
    project_id = temp_db.add_project("Test Project", "/path/to/project")
    assert project_id is not None
    
    # Add a file to the project
    filename = "presentation.pptx"
    rel_path = "presentations/presentation.pptx"
    checksum = "abc123hash"
    
    file_id = temp_db.add_file(project_id, filename, rel_path, checksum)
    assert file_id is not None
    assert isinstance(file_id, int)
    assert file_id > 0
    
    # Get files for the project
    files = temp_db.get_files_for_project(project_id)
    assert len(files) == 1
    assert isinstance(files[0], File)
    assert files[0].id == file_id
    assert files[0].project_id == project_id
    assert files[0].filename == filename
    assert files[0].rel_path == rel_path
    assert files[0].checksum == checksum
    assert files[0].conversion_status == "Pending"  # Default value


def test_file_conversion_status(temp_db: Database):
    """Test updating and filtering by file conversion status."""
    # Setup: Create project and file
    project_id = temp_db.add_project("Test Project", "/path/to/project")
    file_id = temp_db.add_file(project_id, "test.pptx", "test.pptx", "hash")
    assert file_id is not None
    
    # Test default status
    files = temp_db.get_files_for_project(project_id)
    assert len(files) == 1
    assert files[0].conversion_status == "Pending"
    
    # Test updating status
    updated = temp_db.update_file_conversion_status(file_id, "In Progress")
    assert updated is True
    
    # Verify status was updated
    files = temp_db.get_files_for_project(project_id)
    assert len(files) == 1
    assert files[0].conversion_status == "In Progress"
    
    # Test filtering by status
    in_progress_files = temp_db.get_files_for_project(project_id, status="In Progress")
    assert len(in_progress_files) == 1
    
    completed_files = temp_db.get_files_for_project(project_id, status="Completed")
    assert len(completed_files) == 0
    
    # Update to Completed
    temp_db.update_file_conversion_status(file_id, "Completed")
    completed_files = temp_db.get_files_for_project(project_id, status="Completed")
    assert len(completed_files) == 1


def test_add_file_duplicate_path(temp_db: Database):
    """Test that adding a file with a duplicate path fails."""
    # Setup
    project_id = temp_db.add_project("Test Project", "/path/to/project")
    rel_path = "duplicate.pptx"
    
    # Add first file
    file_id1 = temp_db.add_file(project_id, "First File", rel_path, "hash1")
    assert file_id1 is not None
    
    # Try to add second file with same relative path to same project
    file_id2 = temp_db.add_file(project_id, "Second File", rel_path, "hash2")
    assert file_id2 is None  # Should fail due to UNIQUE constraint
    
    # Verify only one file exists
    files = temp_db.get_files_for_project(project_id)
    assert len(files) == 1
    assert files[0].filename == "First File"


def test_delete_project_cascades(temp_db: Database):
    """Test that deleting a project also deletes its files."""
    # Setup: Create project and file
    project_id = temp_db.add_project("Test Project", "/path/to/project")
    file_id = temp_db.add_file(project_id, "test.pptx", "test.pptx", "hash")
    
    # Verify file exists
    files = temp_db.get_files_for_project(project_id)
    assert len(files) == 1
    
    # Delete the project
    deleted = temp_db.delete_project(project_id)
    assert deleted is True
    
    # Verify the project is gone
    assert temp_db.get_project_by_id(project_id) is None
    
    # Verify the file was also deleted (CASCADE)
    files = temp_db.get_files_for_project(project_id)
    assert len(files) == 0


# --- Slide CRUD Tests ---

def test_add_and_update_slide(temp_db: Database):
    """Test adding and updating a slide."""
    # Setup: Create project and file
    project_id = temp_db.add_project("Test Project", "/path/to/project")
    file_id = temp_db.add_file(project_id, "test.pptx", "test.pptx", "hash")
    
    # Add a slide
    slide_index = 1
    thumb_path = "thumbnails/slide1.png"
    image_path = "images/slide1.png"
    
    slide_id = temp_db.add_slide(file_id, slide_index, thumb_path, image_path)
    assert slide_id is not None
    assert isinstance(slide_id, int)
    assert slide_id > 0
    
    # Update slide with new paths
    new_thumb_path = "thumbnails/slide1_updated.png"
    new_image_path = "images/slide1_updated.png"
    
    updated_slide_id = temp_db.add_slide(file_id, slide_index, new_thumb_path, new_image_path)
    assert updated_slide_id == slide_id  # Should be the same ID (UPSERT)


# --- Element CRUD Tests ---

def test_add_element(temp_db: Database):
    """Test adding an element to a slide."""
    # Setup: Create project, file, and slide
    project_id = temp_db.add_project("Test Project", "/path/to/project")
    file_id = temp_db.add_file(project_id, "test.pptx", "test.pptx", "hash")
    slide_id = temp_db.add_slide(file_id, 1, "thumb.png", "image.png")
    
    # Add an element to the slide
    element_type = "SHAPE"
    bbox_x = 100.0
    bbox_y = 200.0
    bbox_w = 300.0
    bbox_h = 150.0
    
    element_id = temp_db.add_element(slide_id, element_type, bbox_x, bbox_y, bbox_w, bbox_h)
    assert element_id is not None
    assert isinstance(element_id, int)
    assert element_id > 0


def test_delete_elements_for_slide(temp_db: Database):
    """Test deleting elements for a slide."""
    # Setup: Create project, file, slide, and elements
    project_id = temp_db.add_project("Test Project", "/path/to/project")
    file_id = temp_db.add_file(project_id, "test.pptx", "test.pptx", "hash")
    slide_id = temp_db.add_slide(file_id, 1, "thumb.png", "image.png")
    
    # Add multiple elements
    element_id1 = temp_db.add_element(slide_id, "SHAPE", 100.0, 200.0, 300.0, 150.0)
    element_id2 = temp_db.add_element(slide_id, "PICTURE", 400.0, 300.0, 200.0, 100.0)
    
    assert element_id1 is not None
    assert element_id2 is not None
    
    # Delete all elements for the slide
    deleted = temp_db.delete_elements_for_slide(slide_id)
    assert deleted is True


# --- Keyword Tests ---

def test_add_and_get_keyword(temp_db: Database):
    """Test adding and retrieving keywords."""
    # Add keyword
    keyword_text = "Architecture"
    keyword_kind = "topic"  # Using KeywordKind
    
    keyword_id = temp_db.add_keyword_if_not_exists(keyword_text, keyword_kind)
    assert keyword_id is not None
    assert isinstance(keyword_id, int)
    assert keyword_id > 0
    
    # Add another keyword
    keyword_id2 = temp_db.add_keyword_if_not_exists("John Smith", "name")
    assert keyword_id2 is not None
    assert keyword_id2 != keyword_id
    
    # Test duplicate (case-insensitive)
    keyword_id3 = temp_db.add_keyword_if_not_exists("architecture", "topic")
    assert keyword_id3 == keyword_id  # Should return existing ID
    
    # Verify by getting the keyword ID
    retrieved_id = temp_db.get_keyword_id("Architecture", "topic")
    assert retrieved_id == keyword_id
    
    # Get all keywords
    all_keywords = temp_db.get_all_keywords()
    assert len(all_keywords) == 2  # We've added 2 unique keywords
    
    # Filter by kind
    topic_keywords = temp_db.get_all_keywords(kind="topic")
    name_keywords = temp_db.get_all_keywords(kind="name")
    assert len(topic_keywords) == 1
    assert len(name_keywords) == 1
    assert topic_keywords[0].keyword == "Architecture"
    assert name_keywords[0].keyword == "John Smith"


def test_keyword_filtering(temp_db: Database):
    """Test keyword filtering by kind."""
    # Add multiple keywords
    temp_db.add_keyword_if_not_exists("Financial Report", "title")
    temp_db.add_keyword_if_not_exists("Finances", "topic")
    temp_db.add_keyword_if_not_exists("Financial Planning", "topic")
    temp_db.add_keyword_if_not_exists("Annual Report", "title")
    temp_db.add_keyword_if_not_exists("John Smith", "name")
    temp_db.add_keyword_if_not_exists("Jane Smith", "name")
    
    # Get all keywords
    all_keywords = temp_db.get_all_keywords()
    assert len(all_keywords) == 6
    
    # Filter by kind
    topic_keywords = temp_db.get_all_keywords(kind="topic")
    title_keywords = temp_db.get_all_keywords(kind="title")
    name_keywords = temp_db.get_all_keywords(kind="name")
    
    assert len(topic_keywords) == 2
    assert len(title_keywords) == 2
    assert len(name_keywords) == 2
    
    # Check ordering (should be alphabetical)
    assert topic_keywords[0].keyword == "Financial Planning" or topic_keywords[0].keyword == "Finances"
    assert title_keywords[0].keyword == "Annual Report" or title_keywords[0].keyword == "Financial Report"
    assert name_keywords[0].keyword == "Jane Smith" or name_keywords[0].keyword == "John Smith"