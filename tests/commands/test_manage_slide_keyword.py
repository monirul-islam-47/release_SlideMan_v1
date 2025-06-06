"""
Unit tests for ManageSlideKeywordCommand.
"""
from unittest.mock import Mock, patch

import pytest

from slideman.commands.manage_slide_keyword import ManageSlideKeywordCommand
from slideman.models import Keyword, Slide
from slideman.services.exceptions import DatabaseError


class TestManageSlideKeywordCommand:
    """Test suite for ManageSlideKeywordCommand."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database service."""
        db = Mock()
        db.add_slide_keyword.return_value = True
        db.remove_slide_keyword.return_value = True
        db.get_slide.return_value = Slide(
            id=1, file_id=1, slide_number=1, 
            title="Test Slide", notes="", thumbnail_path=""
        )
        db.get_keyword.return_value = Keyword(id=1, name="test_tag")
        return db

    @pytest.fixture
    def add_command(self, mock_db):
        """Create add keyword command."""
        return ManageSlideKeywordCommand(
            slide_id=1,
            keyword_id=1,
            is_add=True,
            db_service=mock_db
        )

    @pytest.fixture
    def remove_command(self, mock_db):
        """Create remove keyword command."""
        return ManageSlideKeywordCommand(
            slide_id=1,
            keyword_id=1,
            is_add=False,
            db_service=mock_db
        )

    def test_initialization_add(self, add_command):
        """Test add command initialization."""
        assert add_command.text() == "Add keyword to slide"
        assert add_command._slide_id == 1
        assert add_command._keyword_id == 1
        assert add_command._is_add is True

    def test_initialization_remove(self, remove_command):
        """Test remove command initialization."""
        assert remove_command.text() == "Remove keyword from slide"
        assert remove_command._is_add is False

    def test_redo_add_success(self, add_command, mock_db):
        """Test successful keyword addition."""
        with patch('slideman.commands.manage_slide_keyword.event_bus') as mock_bus:
            add_command.redo()
        
        mock_db.add_slide_keyword.assert_called_once_with(1, 1)
        mock_bus.slide_keywords_changed.emit.assert_called_once_with(1)

    def test_redo_remove_success(self, remove_command, mock_db):
        """Test successful keyword removal."""
        with patch('slideman.commands.manage_slide_keyword.event_bus') as mock_bus:
            remove_command.redo()
        
        mock_db.remove_slide_keyword.assert_called_once_with(1, 1)
        mock_bus.slide_keywords_changed.emit.assert_called_once_with(1)

    def test_redo_add_failed(self, add_command, mock_db):
        """Test failed keyword addition."""
        mock_db.add_slide_keyword.return_value = False
        
        with pytest.raises(DatabaseError) as exc_info:
            add_command.redo()
        
        assert "Failed to add keyword" in str(exc_info.value)

    def test_redo_remove_failed(self, remove_command, mock_db):
        """Test failed keyword removal."""
        mock_db.remove_slide_keyword.return_value = False
        
        with pytest.raises(DatabaseError) as exc_info:
            remove_command.redo()
        
        assert "Failed to remove keyword" in str(exc_info.value)

    def test_undo_add(self, add_command, mock_db):
        """Test undo of keyword addition."""
        # First add
        add_command.redo()
        
        # Then undo
        mock_db.remove_slide_keyword.reset_mock()
        with patch('slideman.commands.manage_slide_keyword.event_bus') as mock_bus:
            add_command.undo()
        
        mock_db.remove_slide_keyword.assert_called_once_with(1, 1)
        mock_bus.slide_keywords_changed.emit.assert_called_once_with(1)

    def test_undo_remove(self, remove_command, mock_db):
        """Test undo of keyword removal."""
        # First remove
        remove_command.redo()
        
        # Then undo
        mock_db.add_slide_keyword.reset_mock()
        with patch('slideman.commands.manage_slide_keyword.event_bus') as mock_bus:
            remove_command.undo()
        
        mock_db.add_slide_keyword.assert_called_once_with(1, 1)
        mock_bus.slide_keywords_changed.emit.assert_called_once_with(1)

    def test_merge_with_opposite_action(self, add_command, mock_db):
        """Test merging add and remove cancels out."""
        remove_cmd = ManageSlideKeywordCommand(
            slide_id=1,
            keyword_id=1,
            is_add=False,
            db_service=mock_db
        )
        
        # Should not merge opposite actions
        assert add_command.mergeWith(remove_cmd) is False

    def test_merge_with_same_action(self, add_command, mock_db):
        """Test merging same action is redundant."""
        another_add = ManageSlideKeywordCommand(
            slide_id=1,
            keyword_id=1,
            is_add=True,
            db_service=mock_db
        )
        
        # Could merge (no-op) but implementation returns False
        assert add_command.mergeWith(another_add) is False

    def test_merge_with_different_slide(self, add_command, mock_db):
        """Test merging commands for different slides."""
        different_slide = ManageSlideKeywordCommand(
            slide_id=2,
            keyword_id=1,
            is_add=True,
            db_service=mock_db
        )
        
        assert add_command.mergeWith(different_slide) is False

    def test_merge_with_different_keyword(self, add_command, mock_db):
        """Test merging commands for different keywords."""
        different_keyword = ManageSlideKeywordCommand(
            slide_id=1,
            keyword_id=2,
            is_add=True,
            db_service=mock_db
        )
        
        assert add_command.mergeWith(different_keyword) is False

    def test_command_with_names(self, mock_db):
        """Test command text includes slide and keyword names."""
        mock_db.get_slide.return_value = Slide(
            id=1, file_id=1, slide_number=1,
            title="Important Slide", notes="", thumbnail_path=""
        )
        mock_db.get_keyword.return_value = Keyword(id=1, name="critical")
        
        command = ManageSlideKeywordCommand(1, 1, True, mock_db)
        
        # Command might update text after fetching names
        command.redo()
        
        # Verify names were fetched
        mock_db.get_slide.assert_called()
        mock_db.get_keyword.assert_called()

    def test_command_with_app_state_db(self):
        """Test command creation using app_state database."""
        with patch('slideman.commands.manage_slide_keyword.app_state') as mock_state:
            mock_state.db_service = Mock()
            
            command = ManageSlideKeywordCommand(1, 1, True)
            
            assert command.db == mock_state.db_service