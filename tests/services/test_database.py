# src/slideman/tests/services/test_database.py

import pytest
import sqlite3 # For catching specific errors if needed
from pathlib import Path

# Assuming your models and service are importable relative to the tests directory
# Adjust imports based on your exact project structure and how pytest discovers tests
from slideman.services.database import Database
from slideman.models.project import Project # Import the model to check return types

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