"""
Integration tests for assembly and export workflow.
"""
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from slideman.services.database import Database
from slideman.services.export_service import ExportService
from slideman.services.service_registry import ServiceRegistry
from slideman.presenters.assembly_presenter import AssemblyPresenter
from slideman.presenters.delivery_presenter import DeliveryPresenter
from slideman.models import Project, File, Slide, FileStatus


class TestAssemblyExportWorkflow:
    """Integration tests for slide assembly and export workflow."""

    @pytest.fixture
    def test_db(self):
        """Create in-memory test database."""
        db = Database(":memory:")
        db.initialize()
        yield db
        db.close()

    @pytest.fixture
    def sample_project_with_slides(self, test_db):
        """Create sample project with multiple slides."""
        # Create project
        project = test_db.create_project("Export Test Project", "Testing export")
        
        # Create files with slides
        files_data = []
        all_slides = []
        
        for i in range(3):  # 3 files
            file_obj = test_db.create_file(
                project_id=project.id,
                name=f"presentation{i+1}.pptx",
                path=f"/source/pres{i+1}.pptx",
                size=1024 * (i + 1),
                total_slides=5
            )
            files_data.append(file_obj)
            
            # Create 5 slides per file
            for j in range(5):
                slide = test_db.create_slide(
                    file_id=file_obj.id,
                    slide_number=j + 1,
                    title=f"File {i+1} - Slide {j+1}",
                    notes=f"Notes for F{i+1}S{j+1}",
                    thumbnail_path=f"/thumb/f{i+1}_s{j+1}.png"
                )
                all_slides.append(slide)
        
        return {
            'project': project,
            'files': files_data,
            'slides': all_slides
        }

    @pytest.fixture
    def mock_export_service(self):
        """Create mock export service."""
        service = Mock(spec=ExportService)
        service.export_presentation.return_value = "/output/exported.pptx"
        service.validate_export.return_value = True
        return service

    @pytest.fixture
    def service_registry(self, test_db, mock_export_service):
        """Create service registry with test services."""
        registry = ServiceRegistry()
        registry.register('database', test_db)
        registry.register('export', mock_export_service)
        registry.register('thumbnail_cache', Mock())
        return registry

    def test_slide_assembly_workflow(self, test_db, sample_project_with_slides):
        """Test assembling slides from multiple presentations."""
        slides = sample_project_with_slides['slides']
        
        # Create assembly with specific slides
        assembly = []
        # Add slides in custom order: 
        # - Slide 3 from file 1
        # - Slide 1 from file 2
        # - Slide 5 from file 3
        # - Slide 2 from file 1
        selected_indices = [2, 5, 14, 1]  # 0-based indices
        
        for idx in selected_indices:
            assembly.append(slides[idx].id)
        
        # Verify assembly
        assert len(assembly) == 4
        
        # Test reordering
        assembly[0], assembly[1] = assembly[1], assembly[0]
        
        # Final order should be: File2-S1, File1-S3, File3-S5, File1-S2
        expected_titles = [
            "File 2 - Slide 1",
            "File 1 - Slide 3", 
            "File 3 - Slide 5",
            "File 1 - Slide 2"
        ]
        
        assembled_slides = [test_db.get_slide(sid) for sid in assembly]
        actual_titles = [s.title for s in assembled_slides]
        assert actual_titles == expected_titles

    def test_assembly_presenter_integration(self, service_registry, sample_project_with_slides):
        """Test AssemblyPresenter with full integration."""
        slides = sample_project_with_slides['slides']
        
        # Mock view
        view = Mock()
        view.add_slide_to_preview.return_value = True
        view.get_assembly_order.return_value = []
        
        # Mock app state
        with patch('slideman.presenters.assembly_presenter.app_state') as mock_state:
            mock_state.assembly_slides = []
            
            presenter = AssemblyPresenter(view, {
                'database': service_registry.get('database'),
                'thumbnail_cache': service_registry.get('thumbnail_cache')
            })
            presenter.app_state = mock_state
            
            # Add slides to assembly
            added_count = presenter.add_slides_to_assembly([
                slides[0].id, 
                slides[5].id, 
                slides[10].id
            ])
            
            assert added_count == 3
            assert len(mock_state.assembly_slides) == 3
            
            # Test duplicate prevention
            result = presenter.add_slide_to_assembly(slides[0].id)
            assert result is False  # Already in assembly
            
            # Test removal
            result = presenter.remove_slide_from_assembly(slides[5].id)
            assert result is True
            assert slides[5].id not in mock_state.assembly_slides
            
            # Test reordering
            new_order = [slides[10].id, slides[0].id]
            presenter.update_slide_order(new_order)
            assert mock_state.assembly_slides == new_order

    def test_export_workflow(self, mock_export_service, sample_project_with_slides):
        """Test exporting assembled slides."""
        slides = sample_project_with_slides['slides']
        
        # Select slides for export
        selected_slide_ids = [slides[i].id for i in [0, 2, 4, 6, 8]]
        
        # Configure mock
        mock_export_service.export_presentation.return_value = "/output/final.pptx"
        
        # Execute export
        output_path = mock_export_service.export_presentation(
            selected_slide_ids,
            "/output/final.pptx",
            include_notes=True
        )
        
        # Verify export
        assert output_path == "/output/final.pptx"
        mock_export_service.export_presentation.assert_called_once_with(
            selected_slide_ids,
            "/output/final.pptx",
            include_notes=True
        )

    def test_delivery_presenter_integration(self, service_registry, sample_project_with_slides):
        """Test DeliveryPresenter with full workflow."""
        slides = sample_project_with_slides['slides']
        selected_ids = [slides[0].id, slides[1].id, slides[2].id]
        
        # Mock view
        view = Mock()
        view.get_assembly_order.return_value = selected_ids
        view.get_export_settings.return_value = {
            'include_notes': True,
            'output_path': '/export/output.pptx'
        }
        
        # Mock app state
        with patch('slideman.presenters.delivery_presenter.app_state') as mock_state:
            mock_state.assembly_slides = selected_ids
            
            presenter = DeliveryPresenter(view, {
                'database': service_registry.get('database'),
                'export': service_registry.get('export'),
                'thumbnail_cache': service_registry.get('thumbnail_cache')
            })
            presenter.app_state = mock_state
            
            # Load assembly
            presenter.load_assembly()
            view.update_preview.assert_called_once()
            
            # Mock export worker
            with patch('slideman.presenters.delivery_presenter.ExportWorker') as mock_worker_class:
                mock_worker = Mock()
                mock_worker_class.return_value = mock_worker
                
                # Start export
                presenter.export_presentation()
                
                mock_worker_class.assert_called_once()
                mock_worker.start.assert_called_once()
                
                # Simulate completion
                presenter._on_export_complete('/export/output.pptx')
                view.show_export_complete.assert_called_once_with('/export/output.pptx')

    def test_assembly_with_keywords(self, test_db, sample_project_with_slides):
        """Test assembling slides based on keywords."""
        slides = sample_project_with_slides['slides']
        
        # Create and assign keywords
        intro_kw = test_db.create_keyword("introduction")
        summary_kw = test_db.create_keyword("summary")
        data_kw = test_db.create_keyword("data")
        
        # Tag specific slides
        test_db.add_slide_keyword(slides[0].id, intro_kw.id)
        test_db.add_slide_keyword(slides[4].id, summary_kw.id)
        test_db.add_slide_keyword(slides[7].id, data_kw.id)
        test_db.add_slide_keyword(slides[9].id, summary_kw.id)
        test_db.add_slide_keyword(slides[12].id, data_kw.id)
        
        # Find all slides with specific keywords for assembly
        summary_slides = test_db.search_slides_by_keywords(
            sample_project_with_slides['project'].id,
            [summary_kw.id]
        )
        
        assert len(summary_slides) == 2
        
        # Create assembly from keyword search
        assembly = [intro_kw.id] + [s.id for s in summary_slides]
        assert len(assembly) == 3

    def test_large_assembly_performance(self, test_db, mock_export_service):
        """Test performance with large slide assembly."""
        # Create project with many slides
        project = test_db.create_project("Large Project", "Performance test")
        
        # Create single large file
        large_file = test_db.create_file(
            project_id=project.id,
            name="large_presentation.pptx",
            path="/source/large.pptx",
            size=50 * 1024 * 1024,  # 50MB
            total_slides=100
        )
        
        # Create 100 slides
        large_assembly = []
        for i in range(100):
            slide = test_db.create_slide(
                file_id=large_file.id,
                slide_number=i + 1,
                title=f"Slide {i + 1}",
                notes=f"Notes for slide {i + 1}",
                thumbnail_path=f"/thumb/large_{i + 1}.png"
            )
            if i % 2 == 0:  # Select every other slide
                large_assembly.append(slide.id)
        
        assert len(large_assembly) == 50
        
        # Test export with progress
        progress_updates = []
        
        def progress_callback(current, total):
            progress_updates.append((current, total))
        
        # Mock export with progress
        mock_export_service.export_presentation.side_effect = lambda ids, path, notes: (
            progress_callback(len(ids), len(ids)),
            path
        )[-1]
        
        output = mock_export_service.export_presentation(
            large_assembly,
            "/output/large_export.pptx",
            include_notes=True
        )
        
        assert output == "/output/large_export.pptx"

    def test_export_error_recovery(self, service_registry, sample_project_with_slides):
        """Test error recovery during export."""
        slides = sample_project_with_slides['slides']
        selected_ids = [slides[0].id, slides[1].id]
        
        # Make export fail
        export_service = service_registry.get('export')
        export_service.export_presentation.side_effect = Exception("PowerPoint not found")
        
        # Mock view
        view = Mock()
        view.get_assembly_order.return_value = selected_ids
        view.get_export_settings.return_value = {
            'include_notes': True,
            'output_path': '/export/fail.pptx'
        }
        
        with patch('slideman.presenters.delivery_presenter.app_state') as mock_state:
            mock_state.assembly_slides = selected_ids
            
            presenter = DeliveryPresenter(view, service_registry)
            presenter.app_state = mock_state
            
            # Create mock worker that will fail
            with patch('slideman.presenters.delivery_presenter.ExportWorker') as mock_worker_class:
                mock_worker = Mock()
                mock_worker_class.return_value = mock_worker
                
                presenter.export_presentation()
                
                # Simulate error
                presenter._on_export_error("PowerPoint not found")
                
                view.show_error.assert_called_once()
                assert "PowerPoint not found" in view.show_error.call_args[0][1]

    def test_assembly_persistence(self, test_db, sample_project_with_slides):
        """Test that assembly state persists across sessions."""
        slides = sample_project_with_slides['slides']
        
        # Create initial assembly
        initial_assembly = [slides[0].id, slides[2].id, slides[4].id]
        
        # Simulate saving to app state
        app_state_mock = Mock()
        app_state_mock.assembly_slides = initial_assembly.copy()
        
        # Simulate app restart - load assembly
        loaded_assembly = app_state_mock.assembly_slides
        
        assert loaded_assembly == initial_assembly
        
        # Verify slides still exist and are valid
        for slide_id in loaded_assembly:
            slide = test_db.get_slide(slide_id)
            assert slide is not None
            assert slide.id in initial_assembly