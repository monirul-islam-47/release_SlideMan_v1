# tests/models/test_file.py

import pytest
from slideman.models.file import File, FileStatus


def test_file_creation_with_valid_parameters():
    """Test that a File can be created with valid parameters."""
    # Test with minimum required parameters
    file = File(project_id=1, filename="presentation.pptx", rel_path="presentations/presentation.pptx")
    assert file.id is None
    assert file.project_id == 1
    assert file.filename == "presentation.pptx"
    assert file.rel_path == "presentations/presentation.pptx"
    assert file.slide_count is None
    assert file.checksum is None
    assert file.conversion_status == "Pending"  # Default value
    
    # Test with all parameters specified
    file = File(
        id=5,
        project_id=1,
        filename="presentation.pptx",
        rel_path="presentations/presentation.pptx",
        slide_count=25,
        checksum="abc123hash",
        conversion_status="Completed"
    )
    assert file.id == 5
    assert file.project_id == 1
    assert file.filename == "presentation.pptx"
    assert file.rel_path == "presentations/presentation.pptx"
    assert file.slide_count == 25
    assert file.checksum == "abc123hash"
    assert file.conversion_status == "Completed"


def test_file_property_access():
    """Test that File properties can be accessed correctly."""
    file = File(
        id=1,
        project_id=2,
        filename="test.pptx",
        rel_path="test/test.pptx",
        slide_count=10,
        checksum="hash123",
        conversion_status="In Progress"
    )
    
    # Test direct property access
    assert file.id == 1
    assert file.project_id == 2
    assert file.filename == "test.pptx"
    assert file.rel_path == "test/test.pptx"
    assert file.slide_count == 10
    assert file.checksum == "hash123"
    assert file.conversion_status == "In Progress"


def test_file_property_mutation():
    """Test that File properties can be modified with validation."""
    file = File(project_id=1, filename="test.pptx", rel_path="test/test.pptx")
    
    # Test valid property modifications
    file.filename = "updated.pptx"
    file.rel_path = "updated/updated.pptx"
    file.slide_count = 15
    file.checksum = "newhash456"
    file.conversion_status = "Completed"
    
    assert file.filename == "updated.pptx"
    assert file.rel_path == "updated/updated.pptx"
    assert file.slide_count == 15
    assert file.checksum == "newhash456"
    assert file.conversion_status == "Completed"
    
    # Test property validation during assignment
    with pytest.raises(Exception) as exc_info:
        file.filename = 123
    assert "filename must be a string" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    with pytest.raises(Exception) as exc_info:
        file.rel_path = 456
    assert "rel_path must be a string" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    with pytest.raises(Exception) as exc_info:
        file.conversion_status = "Invalid Status"
    assert "conversion_status must be one of" in str(exc_info.value) or "type" in str(exc_info.value).lower()


def test_file_string_fields_validation():
    """Test that File correctly validates string fields."""
    # Test that filename must be a string
    with pytest.raises(Exception) as exc_info:
        File(project_id=1, filename=123, rel_path="/path")
    assert "filename must be a string" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    # Test that rel_path must be a string
    with pytest.raises(Exception) as exc_info:
        File(project_id=1, filename="file.pptx", rel_path=123)
    assert "rel_path must be a string" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    # Test that filename cannot be empty
    with pytest.raises(Exception) as exc_info:
        File(project_id=1, filename="", rel_path="/path")
    assert "filename cannot be empty" in str(exc_info.value) or "blank" in str(exc_info.value).lower()
    
    # Test that filename cannot be just whitespace
    with pytest.raises(Exception) as exc_info:
        File(project_id=1, filename="   ", rel_path="/path")
    assert "filename cannot be empty" in str(exc_info.value) or "blank" in str(exc_info.value).lower()


def test_file_status_validation():
    """Test that File validates the conversion_status field."""
    # Test valid statuses
    valid_statuses = ["Pending", "In Progress", "Completed", "Failed"]
    for status in valid_statuses:
        file = File(project_id=1, filename="file.pptx", rel_path="/path", conversion_status=status)
        assert file.conversion_status == status
    
    # Test invalid status
    with pytest.raises(Exception) as exc_info:
        File(project_id=1, filename="file.pptx", rel_path="/path", conversion_status="Unknown")
    assert "conversion_status must be one of" in str(exc_info.value) or "type" in str(exc_info.value).lower()


def test_file_with_empty_optional_fields():
    """Test File behavior with unset optional fields."""
    file = File(project_id=1, filename="file.pptx", rel_path="/path")
    
    assert file.slide_count is None
    assert file.checksum is None
    assert file.conversion_status == "Pending"  # This has a default value


def test_file_project_relationship():
    """Test the relationship between File and Project through project_id."""
    # Simple test showing file belongs to a project
    file = File(project_id=5, filename="file.pptx", rel_path="/path")
    assert file.project_id == 5
    
    # Test changing project association
    file.project_id = 10
    assert file.project_id == 10
