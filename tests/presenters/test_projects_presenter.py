"""
Unit tests for ProjectsPresenter.
"""
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

import pytest

from slideman.presenters.projects_presenter import ProjectsPresenter, IProjectsView
from slideman.models import Project, File, FileStatus
from slideman.services.exceptions import DatabaseError, FileOperationError, ValidationError
from slideman.commands.delete_project import DeleteProjectCommand
from slideman.commands.rename_project import RenameProjectCommand


class TestProjectsPresenter:
    """Test suite for ProjectsPresenter."""

    @pytest.fixture
    def view(self):
        """Create a mock projects view."""
        view = Mock(spec=IProjectsView)
        view.show_project_list = Mock()
        view.show_project_details = Mock()
        view.update_conversion_progress = Mock()
        view.clear_project_selection = Mock()
        view.get_new_project_info = Mock()
        view.get_rename_input = Mock()
        view.confirm_delete = Mock()
        view.show_error = Mock()
        view.show_warning = Mock()
        view.show_info = Mock()
        view.set_busy = Mock()
        return view

    @pytest.fixture
    def services(self, service_registry):
        """Create services dict with mocks."""
        return {
            'database': service_registry.get('database'),
            'file_io': service_registry.get('file_io'),
            'slide_converter': service_registry.get('slide_converter')
        }

    @pytest.fixture
    def presenter(self, view, services):
        """Create a ProjectsPresenter instance."""
        with patch('slideman.presenters.projects_presenter.app_state') as mock_state:
            mock_state.undo_stack = Mock()
            presenter = ProjectsPresenter(view, services)
            presenter.app_state = mock_state
            return presenter

    @pytest.fixture
    def sample_projects(self):
        """Create sample projects."""
        return [
            Project(id=1, name="Project 1", description="Desc 1", path="/path/1"),
            Project(id=2, name="Project 2", description="Desc 2", path="/path/2")
        ]

    def test_initialization(self, presenter, view, services):
        """Test presenter initialization."""
        assert presenter.view == view
        assert presenter.services == services
        assert presenter._selected_project_id is None
        assert presenter._conversion_workers == {}

    def test_load_projects_success(self, presenter, view, services, sample_projects):
        """Test successful project loading."""
        services['database'].get_all_projects.return_value = sample_projects
        
        presenter.load_projects()
        
        services['database'].get_all_projects.assert_called_once()
        view.show_project_list.assert_called_once_with(sample_projects)
        view.clear_project_selection.assert_called_once()
        assert presenter._selected_project_id is None

    def test_load_projects_database_error(self, presenter, view, services):
        """Test project loading with database error."""
        services['database'].get_all_projects.side_effect = DatabaseError("Connection failed")
        
        presenter.load_projects()
        
        view.show_error.assert_called_once()
        assert "Load Projects" in view.show_error.call_args[0][0]
        view.show_project_list.assert_called_once_with([])

    def test_select_project(self, presenter, view, services, sample_projects):
        """Test project selection."""
        project = sample_projects[0]
        services['database'].get_project.return_value = project
        services['database'].get_project_stats.return_value = {
            'total_files': 5,
            'total_slides': 50,
            'total_keywords': 10
        }
        
        presenter.select_project(1)
        
        assert presenter._selected_project_id == 1
        services['database'].get_project.assert_called_once_with(1)
        view.show_project_details.assert_called_once_with(project)

    def test_select_project_not_found(self, presenter, view, services):
        """Test selecting non-existent project."""
        services['database'].get_project.return_value = None
        
        presenter.select_project(999)
        
        assert presenter._selected_project_id is None
        view.show_warning.assert_called_once()

    def test_create_project_success(self, presenter, view, services):
        """Test successful project creation."""
        view.get_new_project_info.return_value = ("New Project", [Path("file1.pptx"), Path("file2.pptx")])
        services['file_io'].is_valid_powerpoint.return_value = True
        services['file_io'].get_file_size.return_value = 1024
        services['file_io'].create_project_structure.return_value = True
        services['file_io'].copy_file_to_project.return_value = Path("/project/sources/file.pptx")
        
        new_project = Project(id=3, name="New Project", description="", path="/project")
        services['database'].create_project.return_value = new_project
        services['database'].create_file.return_value = File(
            id=1, project_id=3, name="file1.pptx", path="/project/sources/file1.pptx",
            size=1024, total_slides=0, status=FileStatus.PENDING
        )
        
        with patch('slideman.presenters.projects_presenter.event_bus') as mock_bus:
            presenter.create_project()
        
        services['database'].create_project.assert_called_once()
        assert services['file_io'].copy_file_to_project.call_count == 2
        mock_bus.project_created.emit.assert_called_once_with(3)
        view.show_info.assert_called_once()

    def test_create_project_cancelled(self, presenter, view):
        """Test project creation when user cancels."""
        view.get_new_project_info.return_value = None
        
        presenter.create_project()
        
        view.show_error.assert_not_called()
        view.show_info.assert_not_called()

    def test_create_project_invalid_files(self, presenter, view, services):
        """Test project creation with invalid PowerPoint files."""
        view.get_new_project_info.return_value = ("New Project", [Path("invalid.txt")])
        services['file_io'].is_valid_powerpoint.return_value = False
        
        presenter.create_project()
        
        view.show_error.assert_called_once()
        assert "Invalid Files" in view.show_error.call_args[0][0]

    def test_delete_selected_project_confirmed(self, presenter, view, services, sample_projects):
        """Test deleting selected project with confirmation."""
        presenter._selected_project_id = 1
        project = sample_projects[0]
        services['database'].get_project.return_value = project
        view.confirm_delete.return_value = True
        
        with patch('slideman.presenters.projects_presenter.DeleteProjectCommand') as mock_cmd:
            mock_command = Mock()
            mock_cmd.return_value = mock_command
            
            presenter.delete_selected_project()
            
            mock_cmd.assert_called_once_with(1, "Project 1", services['database'])
            presenter.app_state.undo_stack.push.assert_called_once_with(mock_command)

    def test_delete_selected_project_cancelled(self, presenter, view, services, sample_projects):
        """Test deleting project when user cancels."""
        presenter._selected_project_id = 1
        services['database'].get_project.return_value = sample_projects[0]
        view.confirm_delete.return_value = False
        
        presenter.delete_selected_project()
        
        # Should not execute any deletion
        presenter.app_state.undo_stack.push.assert_not_called()

    def test_rename_selected_project_success(self, presenter, view, services, sample_projects):
        """Test renaming selected project."""
        presenter._selected_project_id = 1
        project = sample_projects[0]
        services['database'].get_project.return_value = project
        view.get_rename_input.return_value = "Renamed Project"
        
        with patch('slideman.presenters.projects_presenter.RenameProjectCommand') as mock_cmd:
            mock_command = Mock()
            mock_cmd.return_value = mock_command
            
            presenter.rename_selected_project()
            
            mock_cmd.assert_called_once_with(
                1, "Project 1", "Renamed Project", services['database']
            )
            presenter.app_state.undo_stack.push.assert_called_once_with(mock_command)

    def test_convert_project_slides(self, presenter, view, services):
        """Test starting slide conversion for a project."""
        presenter._selected_project_id = 1
        files = [
            File(id=1, project_id=1, name="file1.pptx", path="/path/1", 
                 size=1024, total_slides=0, status=FileStatus.PENDING),
            File(id=2, project_id=1, name="file2.pptx", path="/path/2",
                 size=2048, total_slides=0, status=FileStatus.READY)
        ]
        services['database'].get_project_files.return_value = files
        
        with patch('slideman.presenters.projects_presenter.ConversionWorker') as mock_worker:
            worker_instance = Mock()
            mock_worker.return_value = worker_instance
            
            presenter.convert_project_slides()
            
            # Should only convert PENDING files
            mock_worker.assert_called_once()
            worker_instance.start.assert_called_once()
            assert 1 in presenter._conversion_workers

    def test_cleanup_stops_workers(self, presenter):
        """Test that cleanup stops all conversion workers."""
        # Add some mock workers
        worker1 = Mock()
        worker2 = Mock()
        worker1.isRunning.return_value = True
        worker2.isRunning.return_value = False
        
        presenter._conversion_workers = {1: worker1, 2: worker2}
        
        presenter.cleanup()
        
        worker1.quit.assert_called_once()
        worker1.wait.assert_called_once_with(5000)
        worker2.quit.assert_not_called()  # Already stopped

    def test_handle_conversion_progress(self, presenter, view):
        """Test handling conversion progress updates."""
        presenter._on_conversion_progress(1, 5, 10)
        
        view.update_conversion_progress.assert_called_once_with(1, 5, 10)

    def test_handle_conversion_complete(self, presenter, view):
        """Test handling conversion completion."""
        presenter._conversion_workers[1] = Mock()
        
        with patch('slideman.presenters.projects_presenter.event_bus') as mock_bus:
            presenter._on_conversion_complete(1)
        
        assert 1 not in presenter._conversion_workers
        mock_bus.file_converted.emit.assert_called_once_with(1)
        view.show_info.assert_called_once()

    def test_handle_conversion_error(self, presenter, view):
        """Test handling conversion errors."""
        presenter._conversion_workers[1] = Mock()
        
        presenter._on_conversion_error(1, "Conversion failed")
        
        assert 1 not in presenter._conversion_workers
        view.show_error.assert_called_once()
        assert "Conversion failed" in view.show_error.call_args[0][1]

    def test_concurrent_conversions(self, presenter, services):
        """Test handling multiple concurrent conversions."""
        files = [
            File(id=i, project_id=1, name=f"file{i}.pptx", path=f"/path/{i}",
                 size=1024, total_slides=0, status=FileStatus.PENDING)
            for i in range(1, 4)
        ]
        services['database'].get_project_files.return_value = files
        presenter._selected_project_id = 1
        
        with patch('slideman.presenters.projects_presenter.ConversionWorker') as mock_worker:
            workers = [Mock() for _ in range(3)]
            mock_worker.side_effect = workers
            
            presenter.convert_project_slides()
            
            assert len(presenter._conversion_workers) == 3
            for worker in workers:
                worker.start.assert_called_once()