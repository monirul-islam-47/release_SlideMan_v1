"""
Unit tests for RenameProjectCommand.
"""
from unittest.mock import Mock, patch

import pytest

from slideman.commands.rename_project import RenameProjectCommand
from slideman.services.exceptions import DatabaseError, ValidationError


class TestRenameProjectCommand:
    """Test suite for RenameProjectCommand."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database service."""
        db = Mock()
        db.rename_project.return_value = True
        db.get_project_by_name.return_value = None  # No duplicate
        return db

    @pytest.fixture
    def command(self, mock_db):
        """Create command instance."""
        return RenameProjectCommand(1, "Old Name", "New Name", mock_db)

    def test_initialization(self, command):
        """Test command initialization."""
        assert command.text() == "Rename project 'Old Name' to 'New Name'"
        assert command._project_id == 1
        assert command._old_name == "Old Name"
        assert command._new_name == "New Name"

    def test_redo_success(self, command, mock_db):
        """Test successful project rename."""
        with patch('slideman.commands.rename_project.event_bus') as mock_bus:
            command.redo()
        
        mock_db.rename_project.assert_called_once_with(1, "New Name")
        mock_bus.project_renamed.emit.assert_called_once_with(1, "New Name")

    def test_redo_duplicate_name(self, command, mock_db):
        """Test redo with duplicate project name."""
        mock_db.get_project_by_name.return_value = Mock(id=2)  # Different project
        
        with pytest.raises(ValidationError) as exc_info:
            command.redo()
        
        assert "already exists" in str(exc_info.value)
        mock_db.rename_project.assert_not_called()

    def test_redo_same_name(self, command, mock_db):
        """Test redo when renaming to same name."""
        command._new_name = "Old Name"
        
        command.redo()
        
        # Should not attempt rename
        mock_db.rename_project.assert_not_called()

    def test_redo_rename_failed(self, command, mock_db):
        """Test redo when rename operation fails."""
        mock_db.rename_project.return_value = False
        
        with pytest.raises(DatabaseError) as exc_info:
            command.redo()
        
        assert "Failed to rename" in str(exc_info.value)

    def test_undo_success(self, command, mock_db):
        """Test successful undo of rename."""
        # First do the rename
        command.redo()
        
        # Reset mock
        mock_db.rename_project.reset_mock()
        
        # Undo
        with patch('slideman.commands.rename_project.event_bus') as mock_bus:
            command.undo()
        
        mock_db.rename_project.assert_called_once_with(1, "Old Name")
        mock_bus.project_renamed.emit.assert_called_once_with(1, "Old Name")

    def test_undo_failed(self, command, mock_db):
        """Test undo when rename back fails."""
        # First do the rename
        command.redo()
        
        # Make undo fail
        mock_db.rename_project.return_value = False
        
        with pytest.raises(DatabaseError) as exc_info:
            command.undo()
        
        assert "Failed to rename" in str(exc_info.value)

    def test_merge_with_same_project(self, command, mock_db):
        """Test merging rename commands for same project."""
        other_command = RenameProjectCommand(1, "New Name", "Final Name", mock_db)
        
        result = command.mergeWith(other_command)
        
        assert result is True
        assert command._new_name == "Final Name"
        assert command.text() == "Rename project 'Old Name' to 'Final Name'"

    def test_merge_with_different_project(self, command, mock_db):
        """Test merging rename commands for different projects."""
        other_command = RenameProjectCommand(2, "Other", "Another", mock_db)
        
        result = command.mergeWith(other_command)
        
        assert result is False
        assert command._new_name == "New Name"  # Unchanged

    def test_merge_with_different_command_type(self, command):
        """Test merging with different command type."""
        other_command = Mock()
        other_command.__class__.__name__ = "DeleteProjectCommand"
        
        result = command.mergeWith(other_command)
        
        assert result is False

    def test_validation_empty_name(self, mock_db):
        """Test validation of empty project name."""
        command = RenameProjectCommand(1, "Old Name", "", mock_db)
        
        with pytest.raises(ValidationError) as exc_info:
            command.redo()
        
        assert "cannot be empty" in str(exc_info.value)

    def test_validation_whitespace_name(self, mock_db):
        """Test validation of whitespace-only name."""
        command = RenameProjectCommand(1, "Old Name", "   ", mock_db)
        
        with pytest.raises(ValidationError) as exc_info:
            command.redo()
        
        assert "cannot be empty" in str(exc_info.value)

    def test_command_with_app_state_db(self):
        """Test command creation using app_state database."""
        with patch('slideman.commands.rename_project.app_state') as mock_state:
            mock_state.db_service = Mock()
            
            command = RenameProjectCommand(1, "Old", "New")
            
            assert command.db == mock_state.db_service