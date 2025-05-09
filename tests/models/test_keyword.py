# tests/models/test_keyword.py

import pytest
from slideman.models.keyword import Keyword, KeywordKind


def test_keyword_creation_with_valid_parameters():
    """Test that a Keyword can be created with valid parameters."""
    # Test with minimum required parameters
    keyword = Keyword(keyword="Architecture", kind="topic")
    assert keyword.id is None
    assert keyword.keyword == "Architecture"
    assert keyword.kind == "topic"
    
    # Test with all parameters specified
    keyword = Keyword(id=5, keyword="John Smith", kind="name")
    assert keyword.id == 5
    assert keyword.keyword == "John Smith"
    assert keyword.kind == "name"


def test_keyword_property_access():
    """Test that Keyword properties can be accessed correctly."""
    keyword = Keyword(id=1, keyword="Financial Report", kind="title")
    
    # Test direct property access
    assert keyword.id == 1
    assert keyword.keyword == "Financial Report"
    assert keyword.kind == "title"


def test_keyword_property_mutation():
    """Test that Keyword properties can be modified with validation."""
    keyword = Keyword(keyword="Original", kind="topic")
    
    # Test valid property modifications
    keyword.keyword = "Modified"
    keyword.kind = "name"
    
    assert keyword.keyword == "Modified"
    assert keyword.kind == "name"
    
    # Test property validation during assignment
    with pytest.raises(Exception) as exc_info:
        keyword.keyword = 123
    assert "keyword must be a string" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    with pytest.raises(Exception) as exc_info:
        keyword.keyword = ""
    assert "keyword cannot be empty" in str(exc_info.value)
    
    with pytest.raises(Exception) as exc_info:
        keyword.keyword = "   "  # Just whitespace
    assert "keyword cannot be empty" in str(exc_info.value)
    
    with pytest.raises(Exception) as exc_info:
        keyword.kind = "invalid_kind"
    assert "kind must be one of" in str(exc_info.value) or "type" in str(exc_info.value).lower()


def test_keyword_validation():
    """Test that Keyword correctly validates its fields."""
    # Test keyword must be a string
    with pytest.raises(Exception) as exc_info:
        Keyword(keyword=123, kind="topic")
    assert "keyword must be a string" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    # Test keyword cannot be empty
    with pytest.raises(Exception) as exc_info:
        Keyword(keyword="", kind="topic")
    assert "keyword cannot be empty" in str(exc_info.value)
    
    # Test keyword cannot be just whitespace
    with pytest.raises(Exception) as exc_info:
        Keyword(keyword="   ", kind="topic")
    assert "keyword cannot be empty" in str(exc_info.value)
    
    # Test kind must be one of the allowed values
    with pytest.raises(Exception) as exc_info:
        Keyword(keyword="Valid", kind="invalid_kind")
    assert "kind must be one of" in str(exc_info.value) or "type" in str(exc_info.value).lower()
    
    # Test all valid kinds
    valid_kinds = ["topic", "title", "name"]
    for kind in valid_kinds:
        keyword = Keyword(keyword="Test", kind=kind)
        assert keyword.kind == kind


def test_keyword_equality():
    """Test equality comparison between Keyword objects."""
    keyword1 = Keyword(id=1, keyword="Test", kind="topic")
    keyword2 = Keyword(id=1, keyword="Test", kind="topic")
    keyword3 = Keyword(id=2, keyword="Different", kind="name")
    
    # Test equality
    assert keyword1 == keyword2  # Same attributes
    assert keyword1 != keyword3  # Different attributes


def test_keyword_case_sensitivity():
    """Test that keywords can have different cases."""
    # Create keywords with different cases
    keyword1 = Keyword(keyword="test", kind="topic")
    keyword2 = Keyword(keyword="Test", kind="topic")
    keyword3 = Keyword(keyword="TEST", kind="topic")
    
    # They should be treated as different objects
    assert keyword1.keyword != keyword2.keyword
    assert keyword2.keyword != keyword3.keyword
    assert keyword1.keyword != keyword3.keyword
    
    # But a case-insensitive comparison would consider them the same
    assert keyword1.keyword.lower() == keyword2.keyword.lower() == keyword3.keyword.lower()
    
    # NOTE: Uniqueness constraints are typically enforced at the database level
    # and would need to be tested with database service tests


def test_keyword_types():
    """Test the different keyword types."""
    # Topic keyword
    topic = Keyword(keyword="Technology", kind="topic")
    assert topic.kind == "topic"
    
    # Title keyword
    title = Keyword(keyword="Quarterly Report", kind="title")
    assert title.kind == "title"
    
    # Name keyword
    name = Keyword(keyword="Jane Doe", kind="name")
    assert name.kind == "name"
