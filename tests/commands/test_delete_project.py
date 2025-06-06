"""
Unit tests for DeleteProjectCommand.
"""
from unittest.mock import Mock, patch, call

import pytest

from slideman.commands.delete_project import DeleteProjectCommand
from slideman.models import Project
from slideman.services.exceptions import DatabaseError


class TestDeleteProjectCommand:
    """Test suite for DeleteProjectCommand."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database service."""
        db = Mock()
        db.get_project.return_value = Project(
            id=1, 
            name="Test Project", 
            description="Test Description",
            path="/projects/test"
        )
        db.delete_project.return_value = True
        return db

    @pytest.fixture
    def mock_file_io(self):
        """Create mock file IO service."""
        file_io = Mock()
        file_io.delete_project_structure.return_value = None
        return file_io

    @pytest.fixture
    def command(self, mock_db):
        """Create command instance."""
        with patch('slideman.commands.delete_project.app_state') as mock_state:
            mock_state.service_registry.get.return_value = Mock()
            return DeleteProjectCommand(1, "Test Project", mock_db)

    def test_initialization(self, mock_db):
        """Test command initialization."""
        command = DeleteProjectCommand(1, "Test Project", mock_db)
        
        assert command.text() == "Delete project 'Test Project'"
        assert command._project_id == 1
        assert command._project_name == "Test Project"
        assert command._project_data is None
        assert command.db == mock_db

    def test_redo_success(self, command, mock_db, mock_file_io):
        """Test successful project deletion."""
        with patch('slideman.commands.delete_project.app_state') as mock_state:
            mock_state.service_registry.get.return_value = mock_file_io
            
            with patch('slideman.commands.delete_project.event_bus') as mock_bus:
                command.redo()
        
        # Verify data was saved
        assert command._project_data is not None
        assert command._project_data['id'] == 1
        assert command._project_data['name'] == "Test Project"
        
        # Verify deletion
        mock_db.delete_project.assert_called_once_with(1)
        mock_file_io.delete_project_structure.assert_called_once_with("Test Project")
        mock_bus.project_deleted.emit.assert_called_once_with(1)

    def test_redo_project_not_found(self, command, mock_db):
        """Test redo when project doesn't exist."""
        mock_db.get_project.return_value = None
        
        with pytest.raises(DatabaseError) as exc_info:
            command.redo()
        
        assert "not found" in str(exc_info.value)
        mock_db.delete_project.assert_not_called()

    def test_redo_deletion_failed(self, command, mock_db):
        """Test redo when deletion fails."""
        mock_db.delete_project.return_value = False
        
        with pytest.raises(DatabaseError) as exc_info:
            command.redo()
        
        assert "Failed to delete" in str(exc_info.value)

    def test_undo_not_implemented(self, command):
        """Test undo is not implemented."""
        # First do the deletion
        command._project_data = {
            'id': 1,
            'name': 'Test Project',
            'description': 'Test',
            'files': [],
            'keywords': []
        }
        
        # Undo should log warning but not raise
        command.undo()
        
        # No restoration should occur (not implemented)

    def test_redo_saves_complete_data(self, command, mock_db):
        """Test that redo saves all project data for potential undo."""
        # Mock complete project data
        mock_db.get_project_files.return_value = [
            Mock(id=1, name="file1.pptx", path="/path/1"),
            Mock(id=2, name="file2.pptx", path="/path/2")
        ]
        mock_db.get_project_keywords.return_value = [
            Mock(id=1, name="keyword1"),
            Mock(id=2, name="keyword2")
        ]
        
        with patch('slideman.commands.delete_project.app_state'):
            with patch('slideman.commands.delete_project.event_bus'):
                command.redo()
        
        # Verify complete data saved
        assert len(command._project_data['files']) == 2
        assert len(command._project_data['keywords']) == 2
        assert command._project_data['files'][0]['name'] == "file1.pptx"

    def test_redo_handles_file_deletion_error(self, command, mock_db, mock_file_io):
        """Test redo continues even if file deletion fails."""
        mock_file_io.delete_project_structure.side_effect = Exception("Permission denied")
        
        with patch('slideman.commands.delete_project.app_state') as mock_state:
            mock_state.service_registry.get.return_value = mock_file_io
            
            with patch('slideman.commands.delete_project.event_bus') as mock_bus:
                # Should not raise exception
                command.redo()
        
        # Database deletion should still occur
        mock_db.delete_project.assert_called_once_with(1)
        mock_bus.project_deleted.emit.assert_called_once()

    def test_merge_with_returns_false(self, command):
        """Test that delete commands don't merge."""
        other_command = DeleteProjectCommand(2, "Other Project", Mock())
        
        assert command.mergeWith(other_command) is False

    def test_command_with_app_state_db(self):
        """Test command creation using app_state database."""
        with patch('slideman.commands.delete_project.app_state') as mock_state:
            mock_state.db_service = Mock()
            
            command = DeleteProjectCommand(1, "Test Project")
            
            assert command.db == mock_state.db_service