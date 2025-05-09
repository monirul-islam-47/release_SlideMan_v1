# tests/models/test_slide.py

import pytest
from slideman.models.slide import Slide


def test_slide_creation_with_valid_parameters():
    """Test that a Slide can be created with valid parameters."""
    # Test with minimum required parameters
    slide = Slide(file_id=1, slide_index=2)
    assert slide.id is None
    assert slide.file_id == 1
    assert slide.slide_index == 2
    assert slide.title is None
    assert slide.thumb_rel_path is None
    assert slide.image_rel_path is None
    
    # Test with all parameters specified
    slide = Slide(
        id=5,
        file_id=2,
        slide_index=3,
        title="Slide Title",
        thumb_rel_path="thumbnails/slide3.png",
        image_rel_path="images/slide3.png"
    )
    assert slide.id == 5
    assert slide.file_id == 2
    assert slide.slide_index == 3
    assert slide.title == "Slide Title"
    assert slide.thumb_rel_path == "thumbnails/slide3.png"
    assert slide.image_rel_path == "images/slide3.png"


def test_slide_property_access():
    """Test that Slide properties can be accessed correctly."""
    slide = Slide(
        id=1,
        file_id=2,
        slide_index=3,
        title="Test Slide",
        thumb_rel_path="thumb/test.png",
        image_rel_path="img/test.png"
    )
    
    # Test direct property access
    assert slide.id == 1
    assert slide.file_id == 2
    assert slide.slide_index == 3
    assert slide.title == "Test Slide"
    assert slide.thumb_rel_path == "thumb/test.png"
    assert slide.image_rel_path == "img/test.png"


def test_slide_num_property():
    """Test that the slide_num property returns the slide_index for backward compatibility."""
    slide = Slide(file_id=1, slide_index=5)
    assert slide.slide_num == 5  # Should return the slide_index value
    
    # If slide_index changes, slide_num should reflect that
    slide.slide_index = 10
    assert slide.slide_num == 10


def test_slide_property_mutation():
    """Test that Slide properties can be modified with validation."""
    slide = Slide(file_id=1, slide_index=0)
    
    # Test valid property modifications
    slide.title = "New Title"
    slide.thumb_rel_path = "new/thumb/path.png"
    slide.image_rel_path = "new/image/path.png"
    slide.slide_index = 5
    
    assert slide.title == "New Title"
    assert slide.thumb_rel_path == "new/thumb/path.png"
    assert slide.image_rel_path == "new/image/path.png"
    assert slide.slide_index == 5
    
    # Test property validation during assignment
    with pytest.raises(Exception) as exc_info:
        slide.slide_index = "not an int"
    assert "slide_index must be an integer" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    with pytest.raises(Exception) as exc_info:
        slide.slide_index = -1
    assert "slide_index must be non-negative" in str(exc_info.value)
    
    with pytest.raises(Exception) as exc_info:
        slide.title = 123
    assert "title must be a string or None" in str(exc_info.value) or "type" in str(exc_info.value).lower()


def test_slide_validation():
    """Test that Slide correctly validates its fields."""
    # Test slide_index must be an integer
    with pytest.raises(Exception) as exc_info:
        Slide(file_id=1, slide_index="not an int")
    assert "slide_index must be an integer" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    # Test slide_index must be non-negative
    with pytest.raises(Exception) as exc_info:
        Slide(file_id=1, slide_index=-1)
    assert "slide_index must be non-negative" in str(exc_info.value)
    
    # Test title must be a string or None
    with pytest.raises(Exception) as exc_info:
        Slide(file_id=1, slide_index=0, title=123)
    assert "title must be a string or None" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    # Test thumb_rel_path must be a string or None
    with pytest.raises(Exception) as exc_info:
        Slide(file_id=1, slide_index=0, thumb_rel_path=456)
    assert "thumb_rel_path must be a string or None" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    # Test image_rel_path must be a string or None
    with pytest.raises(Exception) as exc_info:
        Slide(file_id=1, slide_index=0, image_rel_path=789)
    assert "image_rel_path must be a string or None" in str(exc_info.value) or "type" in str(exc_info.value).lower()


def test_slide_path_handling():
    """Test slide path handling for thumbnails and images."""
    # Test that path can be empty string
    slide = Slide(file_id=1, slide_index=0, thumb_rel_path="", image_rel_path="")
    assert slide.thumb_rel_path == ""
    assert slide.image_rel_path == ""
    
    # Test that path can be set independently
    slide = Slide(file_id=1, slide_index=0)
    assert slide.thumb_rel_path is None
    assert slide.image_rel_path is None
    
    slide.thumb_rel_path = "thumb_only.png"
    assert slide.thumb_rel_path == "thumb_only.png"
    assert slide.image_rel_path is None
    
    slide.image_rel_path = "image_only.png"
    assert slide.thumb_rel_path == "thumb_only.png"
    assert slide.image_rel_path == "image_only.png"


def test_slide_file_relationship():
    """Test the relationship between Slide and File through file_id."""
    # Simple test showing slide belongs to a file
    slide = Slide(file_id=5, slide_index=0)
    assert slide.file_id == 5
    
    # Test changing file association
    slide.file_id = 10
    assert slide.file_id == 10


def test_slide_ordering():
    """Test slide ordering through slide_index."""
    # Create multiple slides with different indices
    slide1 = Slide(file_id=1, slide_index=0)
    slide2 = Slide(file_id=1, slide_index=1)
    slide3 = Slide(file_id=1, slide_index=2)
    
    # Verify ordering is correct
    assert slide1.slide_index < slide2.slide_index < slide3.slide_index
    
    # Test that slides with same file_id can have different indices
    slides = [slide3, slide1, slide2]  # Unordered list
    slides_ordered = sorted(slides, key=lambda s: s.slide_index)  # Order by slide_index
    assert slides_ordered[0] == slide1
    assert slides_ordered[1] == slide2
    assert slides_ordered[2] == slide3
