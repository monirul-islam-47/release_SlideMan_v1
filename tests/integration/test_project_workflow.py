"""
Integration tests for project creation and management workflow.
"""
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from slideman.services.database import Database
from slideman.services.file_io import FileIO
from slideman.services.slide_converter import SlideConverter
from slideman.services.service_registry import ServiceRegistry
from slideman.presenters.projects_presenter import ProjectsPresenter
from slideman.commands.rename_project import RenameProjectCommand
from slideman.commands.delete_project import DeleteProjectCommand
from slideman.models import FileStatus


class TestProjectWorkflow:
    """Integration tests for complete project workflow."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for tests."""
        workspace = tempfile.mkdtemp()
        yield Path(workspace)
        shutil.rmtree(workspace, ignore_errors=True)

    @pytest.fixture
    def test_db(self, temp_workspace):
        """Create test database."""
        db_path = temp_workspace / "test.db"
        db = Database(str(db_path))
        db.initialize()
        yield db
        db.close()

    @pytest.fixture
    def file_io(self, temp_workspace):
        """Create FileIO service with temp workspace."""
        service = FileIO()
        with patch.object(service, 'get_user_data_directory', return_value=temp_workspace):
            yield service

    @pytest.fixture
    def service_registry(self, test_db, file_io):
        """Create service registry with real services."""
        registry = ServiceRegistry()
        registry.register('database', test_db)
        registry.register('file_io', file_io)
        
        # Mock services that require external dependencies
        mock_converter = Mock(spec=SlideConverter)
        mock_converter.convert_presentation.return_value = [
            {
                'slide_number': 1,
                'title': 'Slide 1',
                'notes': 'Notes 1',
                'thumbnail_path': 'thumb1.png',
                'shapes': []
            }
        ]
        registry.register('slide_converter', mock_converter)
        
        return registry

    @pytest.fixture
    def sample_pptx_files(self, temp_workspace):
        """Create sample PowerPoint files."""
        files = []
        for i in range(2):
            file_path = temp_workspace / f"presentation{i+1}.pptx"
            file_path.write_bytes(b"PPTX_CONTENT_%d" % i)
            files.append(file_path)
        return files

    def test_complete_project_lifecycle(self, test_db, file_io, service_registry, sample_pptx_files, temp_workspace):
        """Test complete project lifecycle: create, import, convert, rename, delete."""
        
        # 1. Create project
        project_name = "Integration Test Project"
        project_path = file_io.create_project_structure(project_name)
        project = test_db.create_project(project_name, "Test project for integration")
        
        assert project is not None
        assert project.id > 0
        assert project_path.exists()
        assert (project_path / "sources").exists()
        assert (project_path / "thumbnails").exists()
        
        # 2. Import PowerPoint files
        copied_files = []
        for pptx_file in sample_pptx_files:
            dest = file_io.copy_file_to_project(pptx_file, project_path)
            copied_files.append(dest)
            
            # Register in database
            db_file = test_db.create_file(
                project_id=project.id,
                name=pptx_file.name,
                path=str(dest),
                size=file_io.get_file_size(pptx_file),
                total_slides=0
            )
            assert db_file is not None
        
        # Verify files imported
        project_files = test_db.get_project_files(project.id)
        assert len(project_files) == 2
        assert all(f.status == FileStatus.PENDING for f in project_files)
        
        # 3. Convert slides (mocked)
        converter = service_registry.get('slide_converter')
        for db_file in project_files:
            # Simulate conversion
            slides_data = converter.convert_presentation(db_file.path, str(project_path / "thumbnails"))
            
            # Save slides to database
            for slide_data in slides_data:
                slide = test_db.create_slide(
                    file_id=db_file.id,
                    slide_number=slide_data['slide_number'],
                    title=slide_data['title'],
                    notes=slide_data['notes'],
                    thumbnail_path=slide_data['thumbnail_path']
                )
                assert slide is not None
            
            # Update file status
            test_db.update_file_status(db_file.id, FileStatus.READY, len(slides_data))
        
        # Verify conversion
        all_slides = test_db.get_project_slides(project.id)
        assert len(all_slides) == 2  # 1 slide per file
        
        # 4. Add keywords to slides
        keyword1 = test_db.create_keyword("important")
        keyword2 = test_db.create_keyword("demo")
        
        test_db.add_slide_keyword(all_slides[0].id, keyword1.id)
        test_db.add_slide_keyword(all_slides[0].id, keyword2.id)
        test_db.add_slide_keyword(all_slides[1].id, keyword2.id)
        
        # Verify keywords
        slide1_keywords = test_db.get_slide_keywords(all_slides[0].id)
        assert len(slide1_keywords) == 2
        
        # 5. Rename project
        new_name = "Renamed Integration Project"
        rename_cmd = RenameProjectCommand(project.id, project_name, new_name, test_db)
        rename_cmd.redo()
        
        # Verify rename
        renamed_project = test_db.get_project(project.id)
        assert renamed_project.name == new_name
        
        # 6. Test undo rename
        rename_cmd.undo()
        restored_project = test_db.get_project(project.id)
        assert restored_project.name == project_name
        
        # 7. Delete project
        delete_cmd = DeleteProjectCommand(project.id, project_name, test_db)
        with patch.object(file_io, 'delete_project_structure') as mock_delete:
            delete_cmd.redo()
            mock_delete.assert_called_once_with(project_name)
        
        # Verify deletion (cascade)
        assert test_db.get_project(project.id) is None
        assert len(test_db.get_project_files(project.id)) == 0
        assert len(test_db.get_project_slides(project.id)) == 0

    def test_project_presenter_integration(self, service_registry, sample_pptx_files):
        """Test ProjectsPresenter integration with services."""
        # Create mock view
        view = Mock()
        view.get_new_project_info.return_value = ("Presenter Test", sample_pptx_files)
        view.confirm_delete.return_value = True
        
        # Create presenter
        presenter = ProjectsPresenter(view, {
            'database': service_registry.get('database'),
            'file_io': service_registry.get('file_io'),
            'slide_converter': service_registry.get('slide_converter')
        })
        
        # Test project creation through presenter
        with patch('slideman.presenters.projects_presenter.event_bus') as mock_bus:
            presenter.create_project()
        
        # Verify project created
        view.show_info.assert_called()
        mock_bus.project_created.emit.assert_called()
        
        # Load projects
        presenter.load_projects()
        view.show_project_list.assert_called()
        projects = view.show_project_list.call_args[0][0]
        assert len(projects) == 1
        assert projects[0].name == "Presenter Test"

    def test_error_recovery_workflow(self, test_db, file_io, temp_workspace):
        """Test error recovery in project workflow."""
        # Create project
        project = test_db.create_project("Error Test", "Testing error handling")
        project_path = file_io.create_project_structure("Error Test")
        
        # Simulate file copy failure
        bad_file = temp_workspace / "bad.pptx"
        bad_file.touch()
        
        with patch('shutil.copy2', side_effect=IOError("Disk full")):
            with pytest.raises(Exception):
                file_io.copy_file_to_project(bad_file, project_path)
        
        # Project should still be usable
        assert test_db.get_project(project.id) is not None
        
        # Try to add a good file
        good_file = temp_workspace / "good.pptx"
        good_file.write_bytes(b"GOOD_CONTENT")
        
        dest = file_io.copy_file_to_project(good_file, project_path)
        db_file = test_db.create_file(
            project_id=project.id,
            name="good.pptx",
            path=str(dest),
            size=len(b"GOOD_CONTENT"),
            total_slides=0
        )
        
        # Verify recovery
        files = test_db.get_project_files(project.id)
        assert len(files) == 1
        assert files[0].name == "good.pptx"

    def test_concurrent_project_operations(self, test_db, file_io):
        """Test concurrent project operations."""
        from concurrent.futures import ThreadPoolExecutor
        
        def create_project(name):
            project = test_db.create_project(name, f"Description for {name}")
            project_path = file_io.create_project_structure(name)
            return project, project_path
        
        # Create multiple projects concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for i in range(5):
                future = executor.submit(create_project, f"Concurrent Project {i}")
                futures.append(future)
            
            results = [f.result() for f in futures]
        
        # Verify all projects created
        assert len(results) == 5
        all_projects = test_db.get_all_projects()
        assert len(all_projects) == 5
        
        # Verify unique IDs
        project_ids = [p.id for p in all_projects]
        assert len(set(project_ids)) == 5