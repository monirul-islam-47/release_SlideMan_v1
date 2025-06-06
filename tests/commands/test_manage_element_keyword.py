"""
Unit tests for ManageElementKeywordCommand.
"""
from unittest.mock import Mock, patch

import pytest

from slideman.commands.manage_element_keyword import ManageElementKeywordCommand
from slideman.models import Element, Keyword
from slideman.services.exceptions import DatabaseError


class TestManageElementKeywordCommand:
    """Test suite for ManageElementKeywordCommand."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database service."""
        db = Mock()
        db.add_element_keyword.return_value = True
        db.remove_element_keyword.return_value = True
        db.get_element.return_value = Element(
            id=1, slide_id=1, type="text", content="Test Element"
        )
        db.get_keyword.return_value = Keyword(id=1, name="test_tag")
        return db

    @pytest.fixture
    def add_command(self, mock_db):
        """Create add keyword command."""
        return ManageElementKeywordCommand(
            element_id=1,
            keyword_id=1,
            is_add=True,
            db_service=mock_db
        )

    @pytest.fixture
    def remove_command(self, mock_db):
        """Create remove keyword command."""
        return ManageElementKeywordCommand(
            element_id=1,
            keyword_id=1,
            is_add=False,
            db_service=mock_db
        )

    def test_initialization_add(self, add_command):
        """Test add command initialization."""
        assert add_command.text() == "Add keyword to element"
        assert add_command._element_id == 1
        assert add_command._keyword_id == 1
        assert add_command._is_add is True

    def test_initialization_remove(self, remove_command):
        """Test remove command initialization."""
        assert remove_command.text() == "Remove keyword from element"
        assert remove_command._is_add is False

    def test_redo_add_success(self, add_command, mock_db):
        """Test successful keyword addition."""
        with patch('slideman.commands.manage_element_keyword.event_bus') as mock_bus:
            add_command.redo()
        
        mock_db.add_element_keyword.assert_called_once_with(1, 1)
        mock_bus.element_keywords_changed.emit.assert_called_once_with(1)

    def test_redo_remove_success(self, remove_command, mock_db):
        """Test successful keyword removal."""
        with patch('slideman.commands.manage_element_keyword.event_bus') as mock_bus:
            remove_command.redo()
        
        mock_db.remove_element_keyword.assert_called_once_with(1, 1)
        mock_bus.element_keywords_changed.emit.assert_called_once_with(1)

    def test_redo_add_failed(self, add_command, mock_db):
        """Test failed keyword addition."""
        mock_db.add_element_keyword.return_value = False
        
        with pytest.raises(DatabaseError) as exc_info:
            add_command.redo()
        
        assert "Failed to add keyword" in str(exc_info.value)

    def test_redo_remove_failed(self, remove_command, mock_db):
        """Test failed keyword removal."""
        mock_db.remove_element_keyword.return_value = False
        
        with pytest.raises(DatabaseError) as exc_info:
            remove_command.redo()
        
        assert "Failed to remove keyword" in str(exc_info.value)

    def test_undo_add(self, add_command, mock_db):
        """Test undo of keyword addition."""
        # First add
        add_command.redo()
        
        # Then undo
        mock_db.remove_element_keyword.reset_mock()
        with patch('slideman.commands.manage_element_keyword.event_bus') as mock_bus:
            add_command.undo()
        
        mock_db.remove_element_keyword.assert_called_once_with(1, 1)
        mock_bus.element_keywords_changed.emit.assert_called_once_with(1)

    def test_undo_remove(self, remove_command, mock_db):
        """Test undo of keyword removal."""
        # First remove
        remove_command.redo()
        
        # Then undo
        mock_db.add_element_keyword.reset_mock()
        with patch('slideman.commands.manage_element_keyword.event_bus') as mock_bus:
            remove_command.undo()
        
        mock_db.add_element_keyword.assert_called_once_with(1, 1)
        mock_bus.element_keywords_changed.emit.assert_called_once_with(1)

    def test_merge_with_opposite_action(self, add_command, mock_db):
        """Test merging add and remove cancels out."""
        remove_cmd = ManageElementKeywordCommand(
            element_id=1,
            keyword_id=1,
            is_add=False,
            db_service=mock_db
        )
        
        assert add_command.mergeWith(remove_cmd) is False

    def test_merge_with_different_element(self, add_command, mock_db):
        """Test merging commands for different elements."""
        different_element = ManageElementKeywordCommand(
            element_id=2,
            keyword_id=1,
            is_add=True,
            db_service=mock_db
        )
        
        assert add_command.mergeWith(different_element) is False

    def test_merge_with_different_keyword(self, add_command, mock_db):
        """Test merging commands for different keywords."""
        different_keyword = ManageElementKeywordCommand(
            element_id=1,
            keyword_id=2,
            is_add=True,
            db_service=mock_db
        )
        
        assert add_command.mergeWith(different_keyword) is False

    def test_command_with_names(self, mock_db):
        """Test command fetches element and keyword details."""
        mock_db.get_element.return_value = Element(
            id=1, slide_id=1, type="chart", content="Sales Chart"
        )
        mock_db.get_keyword.return_value = Keyword(id=1, name="financial")
        
        command = ManageElementKeywordCommand(1, 1, True, mock_db)
        
        # Execute to potentially update text
        command.redo()
        
        # Verify details were fetched
        mock_db.get_element.assert_called()
        mock_db.get_keyword.assert_called()

    def test_element_type_variations(self, mock_db):
        """Test command with different element types."""
        element_types = [
            ("text", "Text content"),
            ("image", "image.png"),
            ("chart", "Chart data"),
            ("table", "Table data"),
            ("shape", "Shape info")
        ]
        
        for elem_type, content in element_types:
            mock_db.get_element.return_value = Element(
                id=1, slide_id=1, type=elem_type, content=content
            )
            
            command = ManageElementKeywordCommand(1, 1, True, mock_db)
            command.redo()
            
            # Should handle all element types
            mock_db.add_element_keyword.assert_called()
            mock_db.add_element_keyword.reset_mock()

    def test_command_with_app_state_db(self):
        """Test command creation using app_state database."""
        with patch('slideman.commands.manage_element_keyword.app_state') as mock_state:
            mock_state.db_service = Mock()
            
            command = ManageElementKeywordCommand(1, 1, True)
            
            assert command.db == mock_state.db_service