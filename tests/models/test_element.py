# tests/models/test_element.py

import pytest
from slideman.models.element import Element


def test_element_creation_with_valid_parameters():
    """Test that an Element can be created with valid parameters."""
    # Test with minimum required parameters
    element = Element(
        slide_id=1,
        element_type="SHAPE",
        bbox_x=100.0,
        bbox_y=200.0,
        bbox_w=300.0,
        bbox_h=150.0
    )
    assert element.id is None
    assert element.slide_id == 1
    assert element.element_type == "SHAPE"
    assert element.bbox_x == 100.0
    assert element.bbox_y == 200.0
    assert element.bbox_w == 300.0
    assert element.bbox_h == 150.0
    
    # Test with all parameters specified
    element = Element(
        id=5,
        slide_id=2,
        element_type="PICTURE",
        bbox_x=50.5,
        bbox_y=75.25,
        bbox_w=200.75,
        bbox_h=100.5
    )
    assert element.id == 5
    assert element.slide_id == 2
    assert element.element_type == "PICTURE"
    assert element.bbox_x == 50.5
    assert element.bbox_y == 75.25
    assert element.bbox_w == 200.75
    assert element.bbox_h == 100.5


def test_element_property_access():
    """Test that Element properties can be accessed correctly."""
    element = Element(
        id=1,
        slide_id=2,
        element_type="CHART",
        bbox_x=10.0,
        bbox_y=20.0,
        bbox_w=30.0,
        bbox_h=40.0
    )
    
    # Test direct property access
    assert element.id == 1
    assert element.slide_id == 2
    assert element.element_type == "CHART"
    assert element.bbox_x == 10.0
    assert element.bbox_y == 20.0
    assert element.bbox_w == 30.0
    assert element.bbox_h == 40.0


def test_element_property_mutation():
    """Test that Element properties can be modified with validation."""
    element = Element(
        slide_id=1,
        element_type="SHAPE",
        bbox_x=100.0,
        bbox_y=200.0,
        bbox_w=300.0,
        bbox_h=150.0
    )
    
    # Test valid property modifications
    element.element_type = "TABLE"
    element.bbox_x = 150.0
    element.bbox_y = 250.0
    element.bbox_w = 350.0
    element.bbox_h = 200.0
    
    assert element.element_type == "TABLE"
    assert element.bbox_x == 150.0
    assert element.bbox_y == 250.0
    assert element.bbox_w == 350.0
    assert element.bbox_h == 200.0
    
    # Test property validation during assignment
    with pytest.raises(Exception) as exc_info:
        element.element_type = 123
    assert "element_type must be a string" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    with pytest.raises(Exception) as exc_info:
        element.element_type = ""
    assert "element_type cannot be empty" in str(exc_info.value)
    
    with pytest.raises(Exception) as exc_info:
        element.bbox_w = "not a number"
    assert "bbox_w must be a number" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    with pytest.raises(Exception) as exc_info:
        element.bbox_h = 0
    assert "bbox_h must be positive" in str(exc_info.value)
    
    with pytest.raises(Exception) as exc_info:
        element.bbox_w = -10
    assert "bbox_w must be positive" in str(exc_info.value)


def test_element_validation():
    """Test that Element correctly validates its fields."""
    # Test element_type must be a string
    with pytest.raises(Exception) as exc_info:
        Element(
            slide_id=1,
            element_type=123,
            bbox_x=10.0,
            bbox_y=20.0,
            bbox_w=30.0,
            bbox_h=40.0
        )
    assert "element_type must be a string" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    # Test element_type cannot be empty
    with pytest.raises(Exception) as exc_info:
        Element(
            slide_id=1,
            element_type="",
            bbox_x=10.0,
            bbox_y=20.0,
            bbox_w=30.0,
            bbox_h=40.0
        )
    assert "element_type cannot be empty" in str(exc_info.value)
    
    # Test bbox_w must be a number
    with pytest.raises(Exception) as exc_info:
        Element(
            slide_id=1,
            element_type="SHAPE",
            bbox_x=10.0,
            bbox_y=20.0,
            bbox_w="not a number",
            bbox_h=40.0
        )
    assert "bbox_w must be a number" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    # Test bbox_w must be positive
    with pytest.raises(Exception) as exc_info:
        Element(
            slide_id=1,
            element_type="SHAPE",
            bbox_x=10.0,
            bbox_y=20.0,
            bbox_w=0,
            bbox_h=40.0
        )
    assert "bbox_w must be positive" in str(exc_info.value)
    
    # Test bbox_h must be positive
    with pytest.raises(Exception) as exc_info:
        Element(
            slide_id=1,
            element_type="SHAPE",
            bbox_x=10.0,
            bbox_y=20.0,
            bbox_w=30.0,
            bbox_h=-5.0
        )
    assert "bbox_h must be positive" in str(exc_info.value)


def test_element_integer_conversion():
    """Test that Element accepts integers for float fields and converts them."""
    element = Element(
        slide_id=1,
        element_type="SHAPE",
        bbox_x=100,  # Integer
        bbox_y=200,  # Integer
        bbox_w=300,  # Integer
        bbox_h=150   # Integer
    )
    
    # Check that values were converted to floats
    assert isinstance(element.bbox_x, float)
    assert isinstance(element.bbox_y, float)
    assert isinstance(element.bbox_w, float)
    assert isinstance(element.bbox_h, float)
    
    assert element.bbox_x == 100.0
    assert element.bbox_y == 200.0
    assert element.bbox_w == 300.0
    assert element.bbox_h == 150.0


def test_element_slide_relationship():
    """Test the relationship between Element and Slide through slide_id."""
    # Simple test showing element belongs to a slide
    element = Element(
        slide_id=5,
        element_type="SHAPE",
        bbox_x=100.0,
        bbox_y=200.0,
        bbox_w=300.0,
        bbox_h=150.0
    )
    assert element.slide_id == 5
    
    # Test changing slide association
    element.slide_id = 10
    assert element.slide_id == 10


def test_element_positioning():
    """Test that Element positioning properties work correctly."""
    element = Element(
        slide_id=1,
        element_type="SHAPE",
        bbox_x=100.0,
        bbox_y=200.0,
        bbox_w=300.0,
        bbox_h=150.0
    )
    
    # Test basic positioning
    assert element.bbox_x == 100.0
    assert element.bbox_y == 200.0
    assert element.bbox_w == 300.0
    assert element.bbox_h == 150.0
    
    # Calculating right edge
    right_edge = element.bbox_x + element.bbox_w
    assert right_edge == 400.0
    
    # Calculating bottom edge
    bottom_edge = element.bbox_y + element.bbox_h
    assert bottom_edge == 350.0
    
    # Test repositioning
    element.bbox_x = 150.0
    element.bbox_y = 250.0
    
    # Verify new position
    assert element.bbox_x == 150.0
    assert element.bbox_y == 250.0
    
    # New right edge
    new_right_edge = element.bbox_x + element.bbox_w
    assert new_right_edge == 450.0
    
    # New bottom edge
    new_bottom_edge = element.bbox_y + element.bbox_h
    assert new_bottom_edge == 400.0
