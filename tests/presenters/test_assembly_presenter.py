"""
Unit tests for AssemblyPresenter.
"""
from unittest.mock import Mock, patch, call
from datetime import datetime

import pytest

from slideman.presenters.assembly_presenter import AssemblyPresenter, IAssemblyView
from slideman.models import Slide
from slideman.services.exceptions import ValidationError


class TestAssemblyPresenter:
    """Test suite for AssemblyPresenter."""

    @pytest.fixture
    def view(self):
        """Create a mock assembly view."""
        view = Mock(spec=IAssemblyView)
        view.add_slide_to_preview = Mock(return_value=True)
        view.remove_slide_from_preview = Mock(return_value=True)
        view.clear_preview = Mock()
        view.get_assembly_order = Mock(return_value=[])
        view.update_slide_count = Mock()
        view.set_assembly_order = Mock()
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
            'thumbnail_cache': service_registry.get('thumbnail_cache')
        }

    @pytest.fixture
    def presenter(self, view, services):
        """Create an AssemblyPresenter instance."""
        with patch('slideman.presenters.assembly_presenter.app_state') as mock_state:
            mock_state.assembly_slides = []
            presenter = AssemblyPresenter(view, services)
            presenter.app_state = mock_state
            return presenter

    @pytest.fixture
    def sample_slide(self):
        """Create a sample slide."""
        return Slide(
            id=1,
            file_id=1,
            slide_number=1,
            title="Test Slide",
            notes="Test notes",
            thumbnail_path="/thumb/1.png"
        )

    def test_initialization(self, presenter, view, services):
        """Test presenter initialization."""
        assert presenter.view == view
        assert presenter.services == services

    def test_add_slide_to_assembly_success(self, presenter, view, services, sample_slide):
        """Test successfully adding a slide to assembly."""
        services['database'].get_slide.return_value = sample_slide
        services['database'].get_file.return_value = Mock(name="presentation.pptx")
        services['thumbnail_cache'].get_thumbnail.return_value = "/cached/thumb.png"
        
        with patch('slideman.presenters.assembly_presenter.event_bus') as mock_bus:
            result = presenter.add_slide_to_assembly(1)
        
        assert result is True
        services['database'].get_slide.assert_called_once_with(1)
        view.add_slide_to_preview.assert_called_once()
        
        # Check metadata passed to view
        call_args = view.add_slide_to_preview.call_args[0]
        assert call_args[0] == 1  # slide_id
        metadata = call_args[2]
        assert metadata['title'] == "Test Slide"
        assert metadata['file_name'] == "presentation.pptx"
        
        # Check app_state update
        presenter.app_state.assembly_slides.append.assert_called_once_with(1)
        mock_bus.assembly_updated.emit.assert_called_once()

    def test_add_slide_duplicate(self, presenter, view):
        """Test adding duplicate slide to assembly."""
        presenter.app_state.assembly_slides = [1, 2, 3]
        
        result = presenter.add_slide_to_assembly(2)
        
        assert result is False
        view.show_warning.assert_called_once()
        assert "already in assembly" in view.show_warning.call_args[0][1]

    def test_add_slide_not_found(self, presenter, view, services):
        """Test adding non-existent slide."""
        services['database'].get_slide.return_value = None
        
        result = presenter.add_slide_to_assembly(999)
        
        assert result is False
        view.show_error.assert_called_once()

    def test_add_slides_to_assembly_batch(self, presenter, view, services):
        """Test adding multiple slides at once."""
        slides = [
            Slide(id=i, file_id=1, slide_number=i, title=f"Slide {i}", 
                  notes="", thumbnail_path=f"/thumb/{i}.png")
            for i in range(1, 4)
        ]
        services['database'].get_slide.side_effect = slides
        services['database'].get_file.return_value = Mock(name="presentation.pptx")
        services['thumbnail_cache'].get_thumbnail.return_value = "/cached/thumb.png"
        
        added = presenter.add_slides_to_assembly([1, 2, 3])
        
        assert added == 3
        assert view.add_slide_to_preview.call_count == 3
        view.update_slide_count.assert_called_with(3)

    def test_remove_slide_from_assembly(self, presenter, view):
        """Test removing slide from assembly."""
        presenter.app_state.assembly_slides = [1, 2, 3]
        
        with patch('slideman.presenters.assembly_presenter.event_bus') as mock_bus:
            result = presenter.remove_slide_from_assembly(2)
        
        assert result is True
        view.remove_slide_from_preview.assert_called_once_with(2)
        assert presenter.app_state.assembly_slides == [1, 3]
        mock_bus.assembly_updated.emit.assert_called_once()

    def test_remove_slide_not_in_assembly(self, presenter, view):
        """Test removing slide not in assembly."""
        presenter.app_state.assembly_slides = [1, 2, 3]
        
        result = presenter.remove_slide_from_assembly(5)
        
        assert result is False
        view.remove_slide_from_preview.assert_not_called()

    def test_clear_assembly_confirmed(self, presenter, view):
        """Test clearing assembly with confirmation."""
        presenter.app_state.assembly_slides = [1, 2, 3]
        
        with patch('slideman.presenters.assembly_presenter.QMessageBox') as mock_msgbox:
            mock_msgbox.question.return_value = mock_msgbox.Yes
            
            with patch('slideman.presenters.assembly_presenter.event_bus') as mock_bus:
                presenter.clear_assembly()
        
        view.clear_preview.assert_called_once()
        assert presenter.app_state.assembly_slides == []
        view.update_slide_count.assert_called_with(0)
        mock_bus.assembly_updated.emit.assert_called_once()

    def test_clear_assembly_cancelled(self, presenter, view):
        """Test clearing assembly when cancelled."""
        presenter.app_state.assembly_slides = [1, 2, 3]
        
        with patch('slideman.presenters.assembly_presenter.QMessageBox') as mock_msgbox:
            mock_msgbox.question.return_value = mock_msgbox.No
            
            presenter.clear_assembly()
        
        view.clear_preview.assert_not_called()
        assert presenter.app_state.assembly_slides == [1, 2, 3]

    def test_update_slide_order(self, presenter, view):
        """Test updating slide order."""
        new_order = [3, 1, 2]
        presenter.app_state.assembly_slides = [1, 2, 3]
        
        with patch('slideman.presenters.assembly_presenter.event_bus') as mock_bus:
            presenter.update_slide_order(new_order)
        
        assert presenter.app_state.assembly_slides == new_order
        mock_bus.assembly_updated.emit.assert_called_once()

    def test_move_slide_up(self, presenter, view):
        """Test moving slide up in order."""
        presenter.app_state.assembly_slides = [1, 2, 3, 4]
        view.get_assembly_order.return_value = [1, 2, 3, 4]
        
        presenter.move_slide_up(2)  # Move slide 2 up
        
        view.set_assembly_order.assert_called_once_with([2, 1, 3, 4])
        assert presenter.app_state.assembly_slides == [2, 1, 3, 4]

    def test_move_slide_up_at_top(self, presenter, view):
        """Test moving slide up when already at top."""
        presenter.app_state.assembly_slides = [1, 2, 3]
        view.get_assembly_order.return_value = [1, 2, 3]
        
        presenter.move_slide_up(1)  # Try to move first slide up
        
        view.set_assembly_order.assert_not_called()

    def test_move_slide_down(self, presenter, view):
        """Test moving slide down in order."""
        presenter.app_state.assembly_slides = [1, 2, 3, 4]
        view.get_assembly_order.return_value = [1, 2, 3, 4]
        
        presenter.move_slide_down(2)  # Move slide 2 down
        
        view.set_assembly_order.assert_called_once_with([1, 3, 2, 4])
        assert presenter.app_state.assembly_slides == [1, 3, 2, 4]

    def test_move_slide_down_at_bottom(self, presenter, view):
        """Test moving slide down when already at bottom."""
        presenter.app_state.assembly_slides = [1, 2, 3]
        view.get_assembly_order.return_value = [1, 2, 3]
        
        presenter.move_slide_down(3)  # Try to move last slide down
        
        view.set_assembly_order.assert_not_called()

    def test_get_assembly_slides(self, presenter, services):
        """Test getting assembly slide data."""
        presenter.app_state.assembly_slides = [1, 2]
        slides = [
            Slide(id=1, file_id=1, slide_number=1, title="Slide 1", notes="", thumbnail_path=""),
            Slide(id=2, file_id=1, slide_number=2, title="Slide 2", notes="", thumbnail_path="")
        ]
        services['database'].get_slide.side_effect = slides
        services['database'].get_file.return_value = Mock(name="test.pptx", project_id=1)
        
        result = presenter.get_assembly_slides()
        
        assert len(result) == 2
        assert result[0]['slide'].id == 1
        assert result[1]['slide'].id == 2
        assert all(r['file_name'] == "test.pptx" for r in result)

    def test_load_initial_state(self, presenter, view, services):
        """Test loading initial assembly state."""
        presenter.app_state.assembly_slides = [1, 2]
        slides = [
            Slide(id=1, file_id=1, slide_number=1, title="Slide 1", notes="", thumbnail_path=""),
            Slide(id=2, file_id=1, slide_number=2, title="Slide 2", notes="", thumbnail_path="")
        ]
        services['database'].get_slide.side_effect = slides
        services['database'].get_file.return_value = Mock(name="test.pptx")
        services['thumbnail_cache'].get_thumbnail.return_value = "/thumb.png"
        
        presenter.load_initial_state()
        
        assert view.add_slide_to_preview.call_count == 2
        view.update_slide_count.assert_called_with(2)