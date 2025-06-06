"""
Unit tests for BasePresenter.
"""
import logging
from unittest.mock import Mock, patch

import pytest

from slideman.presenters.base_presenter import BasePresenter, IView
from slideman.services.exceptions import DatabaseError, FileOperationError


class ConcretePresenter(BasePresenter):
    """Concrete implementation for testing."""
    pass


class TestBasePresenter:
    """Test suite for BasePresenter."""

    @pytest.fixture
    def view(self):
        """Create a mock view."""
        view = Mock(spec=IView)
        return view

    @pytest.fixture
    def services(self, service_registry):
        """Create services dict."""
        return {
            'database': service_registry.get('database'),
            'file_io': service_registry.get('file_io')
        }

    @pytest.fixture
    def presenter(self, view, services):
        """Create a concrete presenter instance."""
        return ConcretePresenter(view, services)

    def test_initialization(self, presenter, view, services):
        """Test presenter initialization."""
        assert presenter.view == view
        assert presenter.services == services
        assert presenter.logger is not None
        assert isinstance(presenter.logger, logging.Logger)

    def test_get_service_existing(self, presenter, services):
        """Test getting an existing service."""
        db_service = presenter.get_service('database')
        assert db_service == services['database']

    def test_get_service_missing(self, presenter):
        """Test getting a non-existent service."""
        service = presenter.get_service('non_existent')
        assert service is None

    def test_handle_error_with_dialog(self, presenter, view):
        """Test error handling with dialog display."""
        error = DatabaseError("Test error")
        presenter.handle_error(error, "Test Title", "test operation")
        
        view.show_error.assert_called_once_with(
            "Test Title",
            "Failed to test operation: Test error"
        )
        
    def test_handle_error_without_dialog(self, presenter, view):
        """Test error handling without dialog display."""
        error = FileOperationError("Test error")
        presenter.handle_error(error, "Test Title", "test operation", show_dialog=False)
        
        view.show_error.assert_not_called()

    def test_handle_error_logs_exception(self, presenter, view):
        """Test that errors are logged properly."""
        error = Exception("Test error")
        
        with patch.object(presenter.logger, 'error') as mock_log:
            presenter.handle_error(error, "Test Title", "test operation")
            mock_log.assert_called_once()
            args = mock_log.call_args[0]
            assert "Failed to test operation" in args[0]
            assert mock_log.call_args[1]['exc_info'] == error

    def test_handle_warning(self, presenter, view):
        """Test warning handling."""
        presenter.handle_warning("Test Warning", "Warning message")
        
        view.show_warning.assert_called_once_with(
            "Test Warning",
            "Warning message"
        )

    def test_handle_warning_logs(self, presenter):
        """Test that warnings are logged."""
        with patch.object(presenter.logger, 'warning') as mock_log:
            presenter.handle_warning("Test Warning", "Warning message")
            mock_log.assert_called_once_with("Test Warning: Warning message")

    def test_handle_info(self, presenter, view):
        """Test info message handling."""
        presenter.handle_info("Test Info", "Info message")
        
        view.show_info.assert_called_once_with(
            "Test Info",
            "Info message"
        )

    def test_handle_info_logs(self, presenter):
        """Test that info messages are logged."""
        with patch.object(presenter.logger, 'info') as mock_log:
            presenter.handle_info("Test Info", "Info message")
            mock_log.assert_called_once_with("Test Info: Info message")

    def test_cleanup(self, presenter):
        """Test cleanup method (base implementation does nothing)."""
        # Should not raise any exceptions
        presenter.cleanup()

    def test_logger_name(self):
        """Test that logger uses the correct name."""
        view = Mock(spec=IView)
        presenter = ConcretePresenter(view, {})
        assert presenter.logger.name == "ConcretePresenter"

    def test_service_injection_optional(self):
        """Test that services parameter is optional."""
        view = Mock(spec=IView)
        presenter = ConcretePresenter(view)
        assert presenter.services == {}
        assert presenter.get_service('any') is None