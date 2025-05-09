# tests/models/test_project.py

import pytest
from datetime import datetime
from pydantic import ValidationError
from slideman.models.project import Project


def test_project_creation_with_valid_parameters():
    """Test that a Project can be created with valid parameters."""
    # Test minimum valid parameters
    project = Project(name="Test Project", folder_path="/path/to/project")
    assert project.id is None  # Default value is None
    assert project.name == "Test Project"
    assert project.folder_path == "/path/to/project"
    assert project.created_at is None

    # Test with all parameters specified
    created_at = "2025-05-09T23:00:00"
    project = Project(
        id=1, 
        name="Test Project", 
        folder_path="/path/to/project",
        created_at=created_at
    )
    assert project.id == 1
    assert project.name == "Test Project"
    assert project.folder_path == "/path/to/project"
    assert project.created_at == created_at


def test_project_property_access():
    """Test that Project properties can be accessed correctly."""
    project = Project(id=1, name="Test Project", folder_path="/path/to/project", created_at="2025-05-09T23:00:00")
    
    # Test direct property access
    assert project.id == 1
    assert project.name == "Test Project"
    assert project.folder_path == "/path/to/project"
    assert project.created_at == "2025-05-09T23:00:00"


def test_project_property_mutation():
    """Test that Project properties can be modified with validation."""
    project = Project(id=1, name="Test Project", folder_path="/path/to/project")
    
    # Test property modification with valid values
    project.name = "Updated Project Name"
    project.folder_path = "/new/path"
    project.created_at = "2025-05-09T23:30:00"
    
    assert project.name == "Updated Project Name"
    assert project.folder_path == "/new/path"
    assert project.created_at == "2025-05-09T23:30:00"
    
    # Test property validation during assignment
    # Pydantic raises ValidationError with Pydantic v2
    with pytest.raises(Exception) as exc_info:  # Could be TypeError or ValidationError
        project.name = 123
    assert "name must be a string" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    with pytest.raises(Exception) as exc_info:
        project.folder_path = 456
    assert "folder_path must be a string" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    with pytest.raises(Exception) as exc_info:
        project.created_at = 789
    assert "created_at must be a string" in str(exc_info.value) or "type" in str(exc_info.value).lower()


def test_project_equality():
    """Test that Project equality works correctly."""
    project1 = Project(id=1, name="Test Project", folder_path="/path/to/project")
    project2 = Project(id=1, name="Test Project", folder_path="/path/to/project")
    project3 = Project(id=2, name="Different Project", folder_path="/path/to/other")
    
    # Test equality
    assert project1 == project2  # Dataclasses implement __eq__ based on all fields
    assert project1 != project3


def test_project_string_representation():
    """Test the string representation of a Project."""
    project = Project(id=1, name="Test Project", folder_path="/path/to/project")
    
    # Test __str__ or __repr__ (dataclasses implement __repr__ by default)
    str_repr = str(project)
    assert "Project" in str_repr
    assert "Test Project" in str_repr
    assert "/path/to/project" in str_repr


def test_project_created_at_formatting():
    """Test that created_at can be parsed as a datetime if needed."""
    created_at = "2025-05-09T23:00:00"
    project = Project(id=1, name="Test Project", folder_path="/path/to/project", created_at=created_at)
    
    # Test that created_at can be parsed as datetime
    dt = datetime.fromisoformat(project.created_at)
    assert dt.year == 2025
    assert dt.month == 5
    assert dt.day == 9
    assert dt.hour == 23
    assert dt.minute == 0


def test_project_with_empty_values():
    """Test Project behavior with empty but valid values."""
    # Test with empty name and path (still valid as they're strings)
    project = Project(name="", folder_path="")
    assert project.name == ""
    assert project.folder_path == ""


def test_project_id_flexibility():
    """Test that Project accepts different ID types."""
    # Project should accept string IDs (explicitly allowed in the model)
    project = Project(id="string_id", name="Test", folder_path="/path")
    assert project.id == "string_id"
    
    # Project should also accept None IDs
    project = Project(id=None, name="Test", folder_path="/path")
    assert project.id is None
    
    # Project should accept integer IDs
    project = Project(id=1, name="Test", folder_path="/path")
    assert project.id == 1


def test_project_string_fields_validation():
    """Test that Project correctly validates string fields."""
    # Test that name must be a string
    with pytest.raises(Exception) as exc_info:  # Either TypeError or ValidationError
        Project(id=1, name=123, folder_path="/path")
    assert "name must be a string" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    # Test that folder_path must be a string
    with pytest.raises(Exception) as exc_info:
        Project(id=1, name="Test", folder_path=123)
    assert "folder_path must be a string" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    # Test that created_at must be a string or None
    with pytest.raises(Exception) as exc_info:
        Project(id=1, name="Test", folder_path="/path", created_at=123)
    assert "created_at must be a string" in str(exc_info.value) or "type" in str(exc_info.value).lower()
