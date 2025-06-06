"""
Unit tests for DeliveryPresenter.
"""
from unittest.mock import Mock, patch, call, MagicMock
from pathlib import Path
import platform

import pytest

from slideman.presenters.delivery_presenter import DeliveryPresenter, IDeliveryView
from slideman.models import Slide
from slideman.services.exceptions import ExportError, ValidationError


class TestDeliveryPresenter:
    """Test suite for DeliveryPresenter."""

    @pytest.fixture
    def view(self):
        """Create a mock delivery view."""
        view = Mock(spec=IDeliveryView)
        view.update_preview = Mock()
        view.clear_preview = Mock()
        view.update_export_progress = Mock()
        view.show_export_complete = Mock()
        view.get_export_settings = Mock(return_value={
            'include_notes': True,
            'output_path': '/output/presentation.pptx'
        })
        view.set_export_enabled = Mock()
        view.get_assembly_order = Mock(return_value=[])
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
            'export': service_registry.get('export_service'),
            'thumbnail_cache': service_registry.get('thumbnail_cache')
        }

    @pytest.fixture
    def presenter(self, view, services):
        """Create a DeliveryPresenter instance."""
        with patch('slideman.presenters.delivery_presenter.app_state') as mock_state:
            mock_state.assembly_slides = []
            presenter = DeliveryPresenter(view, services)
            presenter.app_state = mock_state
            return presenter

    def test_initialization(self, presenter, view, services):
        """Test presenter initialization."""
        assert presenter.view == view
        assert presenter.services == services
        assert presenter._export_worker is None

    def test_load_assembly_success(self, presenter, view, services):
        """Test loading assembly slides."""
        presenter.app_state.assembly_slides = [1, 2]
        slides = [
            Slide(id=1, file_id=1, slide_number=1, title="Slide 1", notes="Notes 1", thumbnail_path="/t1.png"),
            Slide(id=2, file_id=1, slide_number=2, title="Slide 2", notes="Notes 2", thumbnail_path="/t2.png")
        ]
        services['database'].get_slide.side_effect = slides
        services['database'].get_file.return_value = Mock(name="test.pptx", path="/path/test.pptx")
        services['thumbnail_cache'].get_thumbnail.return_value = "/cached.png"
        
        presenter.load_assembly()
        
        view.update_preview.assert_called_once()
        preview_data = view.update_preview.call_args[0][0]
        assert len(preview_data) == 2
        assert preview_data[0]['slide_id'] == 1
        assert preview_data[0]['title'] == "Slide 1"
        view.set_export_enabled.assert_called_with(True)

    def test_load_assembly_empty(self, presenter, view):
        """Test loading empty assembly."""
        presenter.app_state.assembly_slides = []
        
        presenter.load_assembly()
        
        view.clear_preview.assert_called_once()
        view.set_export_enabled.assert_called_with(False)
        view.show_info.assert_called_once()

    def test_export_presentation_success(self, presenter, view, services):
        """Test successful presentation export."""
        presenter.app_state.assembly_slides = [1, 2, 3]
        view.get_assembly_order.return_value = [1, 2, 3]
        view.get_export_settings.return_value = {
            'include_notes': True,
            'output_path': '/output/final.pptx'
        }
        
        with patch('slideman.presenters.delivery_presenter.ExportWorker') as mock_worker_class:
            mock_worker = Mock()
            mock_worker_class.return_value = mock_worker
            
            presenter.export_presentation()
            
            mock_worker_class.assert_called_once_with(
                [1, 2, 3],
                '/output/final.pptx',
                True,
                services['export']
            )
            mock_worker.progress.connect.assert_called()
            mock_worker.result.connect.assert_called()
            mock_worker.error.connect.assert_called()
            mock_worker.start.assert_called_once()
            view.set_busy.assert_called_with(True, "Preparing export...")

    def test_export_presentation_no_slides(self, presenter, view):
        """Test export with no slides."""
        presenter.app_state.assembly_slides = []
        
        presenter.export_presentation()
        
        view.show_warning.assert_called_once()
        assert "No slides" in view.show_warning.call_args[0][1]

    def test_export_presentation_already_running(self, presenter, view):
        """Test export when already exporting."""
        presenter._export_worker = Mock()
        presenter._export_worker.isRunning.return_value = True
        
        presenter.export_presentation()
        
        view.show_warning.assert_called_once()
        assert "already in progress" in view.show_warning.call_args[0][1]

    def test_cancel_export(self, presenter, view):
        """Test cancelling export."""
        mock_worker = Mock()
        mock_worker.isRunning.return_value = True
        presenter._export_worker = mock_worker
        
        presenter.cancel_export()
        
        mock_worker.terminate.assert_called_once()
        view.set_busy.assert_called_with(False)
        view.show_info.assert_called_once()

    def test_export_progress_update(self, presenter, view):
        """Test handling export progress updates."""
        presenter._on_export_progress(50, "Processing slide 25 of 50")
        
        view.update_export_progress.assert_called_once_with(50, "Processing slide 25 of 50")

    def test_export_complete_success(self, presenter, view):
        """Test handling successful export completion."""
        output_path = '/output/final.pptx'
        presenter._export_worker = Mock()
        
        with patch('slideman.presenters.delivery_presenter.QMessageBox') as mock_msgbox:
            mock_msgbox.question.return_value = mock_msgbox.Yes
            
            with patch.object(presenter, '_open_file') as mock_open:
                presenter._on_export_complete(output_path)
        
        view.show_export_complete.assert_called_once_with(output_path)
        view.set_busy.assert_called_with(False)
        mock_open.assert_called_once_with(output_path)
        assert presenter._export_worker is None

    def test_export_complete_no_open(self, presenter, view):
        """Test export completion without opening file."""
        output_path = '/output/final.pptx'
        presenter._export_worker = Mock()
        
        with patch('slideman.presenters.delivery_presenter.QMessageBox') as mock_msgbox:
            mock_msgbox.question.return_value = mock_msgbox.No
            
            presenter._on_export_complete(output_path)
        
        view.show_export_complete.assert_called_once_with(output_path)
        # Should not attempt to open file

    def test_export_error_handling(self, presenter, view):
        """Test handling export errors."""
        presenter._export_worker = Mock()
        error_msg = "PowerPoint application not found"
        
        presenter._on_export_error(error_msg)
        
        view.show_error.assert_called_once()
        assert error_msg in view.show_error.call_args[0][1]
        view.set_busy.assert_called_with(False)
        assert presenter._export_worker is None

    def test_update_slide_order(self, presenter):
        """Test updating slide order."""
        new_order = [3, 1, 2]
        presenter.app_state.assembly_slides = [1, 2, 3]
        
        presenter.update_slide_order(new_order)
        
        assert presenter.app_state.assembly_slides == new_order

    def test_get_export_preview_data(self, presenter):
        """Test getting export preview statistics."""
        presenter.app_state.assembly_slides = [1, 2, 3, 4, 5]
        
        data = presenter.get_export_preview_data()
        
        assert data['total_slides'] == 5
        assert data['estimated_size'] == '~5-15 MB'  # Based on slide count

    @patch('platform.system')
    @patch('os.startfile')
    def test_open_file_windows(self, mock_startfile, mock_platform, presenter):
        """Test opening file on Windows."""
        mock_platform.return_value = 'Windows'
        
        presenter._open_file('C:\\output\\file.pptx')
        
        mock_startfile.assert_called_once_with('C:\\output\\file.pptx')

    @patch('platform.system')
    @patch('subprocess.run')
    def test_open_file_macos(self, mock_run, mock_platform, presenter):
        """Test opening file on macOS."""
        mock_platform.return_value = 'Darwin'
        
        presenter._open_file('/output/file.pptx')
        
        mock_run.assert_called_once_with(['open', '/output/file.pptx'], check=True)

    @patch('platform.system')
    @patch('subprocess.run')
    def test_open_file_linux(self, mock_run, mock_platform, presenter):
        """Test opening file on Linux."""
        mock_platform.return_value = 'Linux'
        
        presenter._open_file('/output/file.pptx')
        
        mock_run.assert_called_once_with(['xdg-open', '/output/file.pptx'], check=True)

    def test_open_file_error_handling(self, presenter, view):
        """Test error handling when opening file fails."""
        with patch('platform.system', return_value='Windows'):
            with patch('os.startfile', side_effect=Exception("Access denied")):
                presenter._open_file('C:\\output\\file.pptx')
        
        view.show_error.assert_called_once()
        assert "open the file" in view.show_error.call_args[0][1]

    def test_cleanup_stops_worker(self, presenter):
        """Test that cleanup stops export worker."""
        mock_worker = Mock()
        mock_worker.isRunning.return_value = True
        presenter._export_worker = mock_worker
        
        presenter.cleanup()
        
        mock_worker.terminate.assert_called_once()
        mock_worker.wait.assert_called_once_with(5000)