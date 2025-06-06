"""
Unit tests for MergeKeywordsCommand.
"""
from unittest.mock import Mock, patch, call

import pytest

from slideman.commands.merge_keywords_cmd import MergeKeywordsCommand
from slideman.models import Keyword
from slideman.services.exceptions import DatabaseError, ValidationError


class TestMergeKeywordsCommand:
    """Test suite for MergeKeywordsCommand."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database service."""
        db = Mock()
        db.get_keyword_by_name.side_effect = lambda name: {
            'old_tag': Mock(id=1, name='old_tag'),
            'new_tag': Mock(id=2, name='new_tag')
        }.get(name)
        db.get_slides_with_keyword.return_value = [10, 11, 12]
        db.get_elements_with_keyword.return_value = [20, 21]
        db.add_slide_keyword.return_value = True
        db.add_element_keyword.return_value = True
        db.remove_slide_keyword.return_value = True
        db.remove_element_keyword.return_value = True
        db.delete_keyword.return_value = True
        return db

    @pytest.fixture
    def command(self, mock_db):
        """Create command instance."""
        return MergeKeywordsCommand('old_tag', 'new_tag', mock_db)

    def test_initialization(self, command):
        """Test command initialization."""
        assert command.text() == "Merge keyword 'old_tag' into 'new_tag'"
        assert command._old_keyword_name == 'old_tag'
        assert command._new_keyword_name == 'new_tag'
        assert command._merged_data is None

    def test_redo_success(self, command, mock_db):
        """Test successful keyword merge."""
        with patch('slideman.commands.merge_keywords_cmd.event_bus') as mock_bus:
            command.redo()
        
        # Verify data collection
        mock_db.get_slides_with_keyword.assert_called_once_with(1)
        mock_db.get_elements_with_keyword.assert_called_once_with(1)
        
        # Verify merge operations
        assert mock_db.add_slide_keyword.call_count == 3  # 3 slides
        assert mock_db.add_element_keyword.call_count == 2  # 2 elements
        
        # Verify deletion
        mock_db.delete_keyword.assert_called_once_with(1)
        
        # Verify event
        mock_bus.keywords_merged.emit.assert_called_once_with('old_tag', 'new_tag')
        
        # Verify data saved for undo
        assert command._merged_data is not None
        assert command._merged_data['slide_ids'] == [10, 11, 12]
        assert command._merged_data['element_ids'] == [20, 21]

    def test_redo_keywords_not_found(self, command, mock_db):
        """Test merge when keywords don't exist."""
        mock_db.get_keyword_by_name.return_value = None
        
        with pytest.raises(ValidationError) as exc_info:
            command.redo()
        
        assert "not found" in str(exc_info.value)

    def test_redo_same_keyword(self, command, mock_db):
        """Test merge when both keywords are the same."""
        command._new_keyword_name = 'old_tag'
        
        with pytest.raises(ValidationError) as exc_info:
            command.redo()
        
        assert "Cannot merge" in str(exc_info.value)

    def test_redo_transaction_handling(self, command, mock_db):
        """Test that merge uses database transaction."""
        with patch('slideman.commands.merge_keywords_cmd.event_bus'):
            command.redo()
        
        # Should begin and commit transaction
        mock_db.begin_transaction.assert_called_once()
        mock_db.commit_transaction.assert_called_once()

    def test_redo_rollback_on_error(self, command, mock_db):
        """Test transaction rollback on error."""
        mock_db.add_slide_keyword.side_effect = DatabaseError("Failed")
        
        with pytest.raises(DatabaseError):
            command.redo()
        
        # Should rollback transaction
        mock_db.rollback_transaction.assert_called_once()

    def test_redo_handles_duplicate_associations(self, command, mock_db):
        """Test merge handles existing keyword associations."""
        # Some additions might fail due to duplicates
        mock_db.add_slide_keyword.side_effect = [True, False, True]  # Second fails
        
        with patch('slideman.commands.merge_keywords_cmd.event_bus'):
            # Should not raise - duplicates are expected
            command.redo()
        
        # Should still complete the merge
        mock_db.delete_keyword.assert_called_once()

    def test_undo_success(self, command, mock_db):
        """Test successful undo of merge."""
        # First do the merge
        with patch('slideman.commands.merge_keywords_cmd.event_bus'):
            command.redo()
        
        # Reset mocks
        mock_db.reset_mock()
        
        # Create the old keyword for undo
        mock_db.create_keyword.return_value = Keyword(id=1, name='old_tag')
        
        # Undo
        with patch('slideman.commands.merge_keywords_cmd.event_bus') as mock_bus:
            command.undo()
        
        # Should recreate old keyword
        mock_db.create_keyword.assert_called_once_with('old_tag')
        
        # Should restore associations
        assert mock_db.add_slide_keyword.call_count == 3
        assert mock_db.add_element_keyword.call_count == 2
        
        # Should remove from new keyword
        assert mock_db.remove_slide_keyword.call_count == 3
        assert mock_db.remove_element_keyword.call_count == 2
        
        # Should emit event
        mock_bus.keywords_unmerged.emit.assert_called_once()

    def test_undo_without_merge_data(self, command):
        """Test undo without having done merge first."""
        with pytest.raises(DatabaseError) as exc_info:
            command.undo()
        
        assert "No merge data" in str(exc_info.value)

    def test_undo_transaction_handling(self, command, mock_db):
        """Test undo uses transaction."""
        # Setup merge data
        command._merged_data = {
            'old_keyword_id': 1,
            'new_keyword_id': 2,
            'slide_ids': [10],
            'element_ids': [20]
        }
        mock_db.create_keyword.return_value = Keyword(id=1, name='old_tag')
        
        with patch('slideman.commands.merge_keywords_cmd.event_bus'):
            command.undo()
        
        mock_db.begin_transaction.assert_called_once()
        mock_db.commit_transaction.assert_called_once()

    def test_merge_with_incompatible_command(self, command):
        """Test merge with different command type."""
        other_command = Mock()
        
        assert command.mergeWith(other_command) is False

    def test_command_description_formatting(self):
        """Test command description with various keyword names."""
        test_cases = [
            ('tag1', 'tag2', "Merge keyword 'tag1' into 'tag2'"),
            ('old-tag', 'new-tag', "Merge keyword 'old-tag' into 'new-tag'"),
            ('Tag_1', 'Tag_2', "Merge keyword 'Tag_1' into 'Tag_2'")
        ]
        
        for old, new, expected in test_cases:
            cmd = MergeKeywordsCommand(old, new, Mock())
            assert cmd.text() == expected

    def test_command_with_app_state_db(self):
        """Test command creation using app_state database."""
        with patch('slideman.commands.merge_keywords_cmd.app_state') as mock_state:
            mock_state.db_service = Mock()
            
            command = MergeKeywordsCommand('old', 'new')
            
            assert command.db == mock_state.db_service