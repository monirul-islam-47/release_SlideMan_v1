"""
Unit tests for BaseCommand.
"""
from unittest.mock import Mock, patch

import pytest

from slideman.commands.base_command import BaseCommand
from slideman.services.database import Database


class ConcreteCommand(BaseCommand):
    """Concrete implementation for testing."""
    
    def redo(self):
        """Test redo implementation."""
        pass
    
    def undo(self):
        """Test undo implementation."""
        pass


class TestBaseCommand:
    """Test suite for BaseCommand."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database service."""
        return Mock(spec=Database)

    @pytest.fixture
    def command(self, mock_db):
        """Create concrete command instance."""
        return ConcreteCommand("Test Command", mock_db)

    def test_initialization_with_db(self, command, mock_db):
        """Test command initialization with database."""
        assert command.text() == "Test Command"
        assert command.db == mock_db
        assert hasattr(command, 'logger')

    def test_initialization_without_db(self):
        """Test command initialization without database uses app_state."""
        with patch('slideman.commands.base_command.app_state') as mock_state:
            mock_state.db_service = Mock()
            
            command = ConcreteCommand("Test Command")
            
            assert command.db == mock_state.db_service

    def test_logger_name(self, command):
        """Test logger uses correct name."""
        assert command.logger.name == "ConcreteCommand"

    def test_text_property(self, command):
        """Test command text is accessible."""
        assert command.text() == "Test Command"

    def test_merge_with_compatible(self):
        """Test command merging with compatible command."""
        command1 = ConcreteCommand("Command 1")
        command2 = ConcreteCommand("Command 2")
        
        # Default implementation returns False
        assert command1.mergeWith(command2) is False

    def test_id_property(self, command):
        """Test command has ID."""
        # Should have some ID (implementation specific)
        assert command.id() != -1

    def test_inheritance_requirement(self):
        """Test that subclasses must implement redo/undo."""
        class IncompleteCommand(BaseCommand):
            pass
        
        # Should not be able to instantiate without redo/undo
        with pytest.raises(TypeError):
            IncompleteCommand("Test")