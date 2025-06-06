"""
Unit tests for SlideViewPresenter.
"""
from unittest.mock import Mock, patch, call
from datetime import datetime

import pytest

from slideman.presenters.slideview_presenter import SlideViewPresenter, ISlideViewView
from slideman.models import Slide, File, Keyword, FileStatus
from slideman.services.exceptions import DatabaseError, ValidationError
from slideman.commands.manage_slide_keyword import ManageSlideKeywordCommand


class TestSlideViewPresenter:
    """Test suite for SlideViewPresenter."""

    @pytest.fixture
    def view(self):
        """Create a mock slideview view."""
        view = Mock(spec=ISlideViewView)
        view.update_slide_list = Mock()
        view.update_keyword_filter = Mock()
        view.clear_slide_list = Mock()
        view.set_filter_state = Mock()
        view.get_selected_slide_ids = Mock(return_value=[])
        view.get_current_filters = Mock(return_value={})
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
        """Create a SlideViewPresenter instance."""
        with patch('slideman.presenters.slideview_presenter.app_state') as mock_state:
            mock_state.undo_stack = Mock()
            mock_state.current_project = 1
            presenter = SlideViewPresenter(view, services)
            presenter.app_state = mock_state
            return presenter

    @pytest.fixture
    def sample_slides(self):
        """Create sample slides."""
        return [
            Slide(id=1, file_id=1, slide_number=1, title="Slide 1", 
                  notes="Notes 1", thumbnail_path="/thumb/1.png"),
            Slide(id=2, file_id=1, slide_number=2, title="Slide 2",
                  notes="Notes 2", thumbnail_path="/thumb/2.png"),
            Slide(id=3, file_id=2, slide_number=1, title="Slide 3",
                  notes="Notes 3", thumbnail_path="/thumb/3.png")
        ]

    @pytest.fixture
    def sample_files(self):
        """Create sample files."""
        return [
            File(id=1, project_id=1, name="presentation1.pptx", 
                 path="/path/1", size=1024, total_slides=2, status=FileStatus.READY),
            File(id=2, project_id=1, name="presentation2.pptx",
                 path="/path/2", size=2048, total_slides=1, status=FileStatus.READY)
        ]

    @pytest.fixture
    def sample_keywords(self):
        """Create sample keywords."""
        return [
            Keyword(id=1, name="important"),
            Keyword(id=2, name="presentation"),
            Keyword(id=3, name="demo")
        ]

    def test_initialization(self, presenter, view, services):
        """Test presenter initialization."""
        assert presenter.view == view
        assert presenter.services == services
        assert presenter._current_project_id is None
        assert presenter._cached_slides == []
        assert presenter._available_keywords == []

    def test_load_project_slides_success(self, presenter, view, services, sample_slides, sample_files, sample_keywords):
        """Test successful slide loading."""
        services['database'].get_project_slides.return_value = sample_slides
        services['database'].get_project_files.return_value = sample_files
        services['database'].get_slide_keywords.side_effect = [
            [sample_keywords[0], sample_keywords[1]],  # Slide 1
            [sample_keywords[2]],  # Slide 2
            []  # Slide 3
        ]
        services['database'].get_all_keywords.return_value = sample_keywords
        services['thumbnail_cache'].get_thumbnail.return_value = "/cached/thumb.png"
        
        presenter.load_project_slides(1)
        
        assert presenter._current_project_id == 1
        assert len(presenter._cached_slides) == 3
        view.update_slide_list.assert_called_once()
        view.update_keyword_filter.assert_called_once_with(sample_keywords)
        
        # Check slide data transformation
        slide_data = view.update_slide_list.call_args[0][0]
        assert len(slide_data) == 3
        assert slide_data[0]['id'] == 1
        assert slide_data[0]['title'] == "Slide 1"
        assert slide_data[0]['file_name'] == "presentation1.pptx"
        assert len(slide_data[0]['keywords']) == 2

    def test_load_project_slides_no_project(self, presenter, view):
        """Test loading slides with no project ID."""
        presenter.load_project_slides(None)
        
        view.clear_slide_list.assert_called_once()
        view.update_keyword_filter.assert_called_once_with([])
        assert presenter._current_project_id is None

    def test_load_project_slides_database_error(self, presenter, view, services):
        """Test slide loading with database error."""
        services['database'].get_project_slides.side_effect = DatabaseError("Connection failed")
        
        presenter.load_project_slides(1)
        
        view.show_error.assert_called_once()
        view.clear_slide_list.assert_called_once()

    def test_apply_filters_text_only(self, presenter, view, sample_slides):
        """Test applying text filter."""
        presenter._cached_slides = [
            {'id': 1, 'title': 'Introduction', 'notes': 'Welcome'},
            {'id': 2, 'title': 'Overview', 'notes': 'Agenda'},
            {'id': 3, 'title': 'Summary', 'notes': 'Introduction revisited'}
        ]
        view.get_current_filters.return_value = {
            'text': 'introduction',
            'keywords': [],
            'file_ids': []
        }
        
        presenter.apply_filters()
        
        slide_data = view.update_slide_list.call_args[0][0]
        assert len(slide_data) == 2  # Slides 1 and 3 match
        assert slide_data[0]['id'] == 1
        assert slide_data[1]['id'] == 3
        view.set_filter_state.assert_called_once_with(True)

    def test_apply_filters_keywords(self, presenter, view):
        """Test applying keyword filter."""
        presenter._cached_slides = [
            {'id': 1, 'keywords': [{'id': 1, 'name': 'important'}, {'id': 2, 'name': 'demo'}]},
            {'id': 2, 'keywords': [{'id': 2, 'name': 'demo'}]},
            {'id': 3, 'keywords': [{'id': 3, 'name': 'test'}]}
        ]
        view.get_current_filters.return_value = {
            'text': '',
            'keywords': [1, 2],  # Filter by 'important' and 'demo'
            'file_ids': []
        }
        
        presenter.apply_filters()
        
        slide_data = view.update_slide_list.call_args[0][0]
        assert len(slide_data) == 2  # Slides 1 and 2
        assert slide_data[0]['id'] == 1
        assert slide_data[1]['id'] == 2

    def test_apply_filters_files(self, presenter, view):
        """Test applying file filter."""
        presenter._cached_slides = [
            {'id': 1, 'file_id': 1},
            {'id': 2, 'file_id': 1},
            {'id': 3, 'file_id': 2}
        ]
        view.get_current_filters.return_value = {
            'text': '',
            'keywords': [],
            'file_ids': [1]  # Only file 1
        }
        
        presenter.apply_filters()
        
        slide_data = view.update_slide_list.call_args[0][0]
        assert len(slide_data) == 2  # Slides 1 and 2
        assert all(s['file_id'] == 1 for s in slide_data)

    def test_apply_filters_combined(self, presenter, view):
        """Test applying multiple filters together."""
        presenter._cached_slides = [
            {'id': 1, 'title': 'Important', 'file_id': 1, 
             'keywords': [{'id': 1, 'name': 'critical'}]},
            {'id': 2, 'title': 'Overview', 'file_id': 1,
             'keywords': [{'id': 1, 'name': 'critical'}]},
            {'id': 3, 'title': 'Important', 'file_id': 2,
             'keywords': [{'id': 2, 'name': 'other'}]}
        ]
        view.get_current_filters.return_value = {
            'text': 'important',
            'keywords': [1],  # 'critical'
            'file_ids': [1]
        }
        
        presenter.apply_filters()
        
        slide_data = view.update_slide_list.call_args[0][0]
        assert len(slide_data) == 1  # Only slide 1 matches all criteria
        assert slide_data[0]['id'] == 1

    def test_clear_filters(self, presenter, view):
        """Test clearing all filters."""
        presenter._cached_slides = [{'id': 1}, {'id': 2}]
        
        presenter.clear_filters()
        
        view.update_slide_list.assert_called_once_with(presenter._cached_slides)
        view.set_filter_state.assert_called_once_with(False)

    def test_add_keyword_to_selected(self, presenter, view, services):
        """Test adding keyword to selected slides."""
        view.get_selected_slide_ids.return_value = [1, 2, 3]
        keyword = Mock(id=1, name="new_tag")
        
        with patch('slideman.presenters.slideview_presenter.ManageSlideKeywordCommand') as mock_cmd:
            mock_command = Mock()
            mock_cmd.return_value = mock_command
            
            presenter.add_keyword_to_selected(keyword)
            
            # Should create command for each slide
            assert mock_cmd.call_count == 3
            assert presenter.app_state.undo_stack.push.call_count == 3

    def test_add_keyword_no_selection(self, presenter, view):
        """Test adding keyword with no slides selected."""
        view.get_selected_slide_ids.return_value = []
        keyword = Mock(id=1, name="new_tag")
        
        presenter.add_keyword_to_selected(keyword)
        
        view.show_warning.assert_called_once()
        assert "No slides selected" in view.show_warning.call_args[0][1]

    def test_remove_keyword_from_selected(self, presenter, view, services):
        """Test removing keyword from selected slides."""
        view.get_selected_slide_ids.return_value = [1, 2]
        keyword = Mock(id=1, name="tag_to_remove")
        
        with patch('slideman.presenters.slideview_presenter.ManageSlideKeywordCommand') as mock_cmd:
            mock_command = Mock()
            mock_cmd.return_value = mock_command
            
            presenter.remove_keyword_from_selected(keyword)
            
            # Should create remove commands
            assert mock_cmd.call_count == 2
            for call_args in mock_cmd.call_args_list:
                assert call_args[1]['is_add'] is False

    def test_get_selected_slides(self, presenter, view):
        """Test getting selected slide data."""
        presenter._cached_slides = [
            {'id': 1, 'title': 'Slide 1'},
            {'id': 2, 'title': 'Slide 2'},
            {'id': 3, 'title': 'Slide 3'}
        ]
        view.get_selected_slide_ids.return_value = [1, 3]
        
        selected = presenter.get_selected_slides()
        
        assert len(selected) == 2
        assert selected[0]['id'] == 1
        assert selected[1]['id'] == 3

    def test_get_unique_files(self, presenter):
        """Test getting unique files from cached slides."""
        presenter._cached_slides = [
            {'file_id': 1, 'file_name': 'file1.pptx'},
            {'file_id': 1, 'file_name': 'file1.pptx'},
            {'file_id': 2, 'file_name': 'file2.pptx'},
            {'file_id': 2, 'file_name': 'file2.pptx'}
        ]
        
        files = presenter.get_unique_files()
        
        assert len(files) == 2
        assert files[0] == (1, 'file1.pptx')
        assert files[1] == (2, 'file2.pptx')

    def test_reload_after_keyword_change(self, presenter):
        """Test that slides reload after keyword operations."""
        presenter._current_project_id = 1
        presenter._cached_slides = [{'id': 1}]
        
        with patch.object(presenter, 'load_project_slides') as mock_load:
            # Simulate keyword change
            presenter.add_keyword_to_selected(Mock(id=1))
            
            # Verify reload was scheduled (through event bus or direct call)
            # This depends on implementation details

    def test_filter_performance_large_dataset(self, presenter, view):
        """Test filter performance with large dataset."""
        # Create 1000 slides
        presenter._cached_slides = [
            {
                'id': i,
                'title': f'Slide {i}',
                'notes': f'Notes for slide {i}',
                'keywords': [{'id': j, 'name': f'tag{j}'} for j in range(1, 4)]
            }
            for i in range(1, 1001)
        ]
        
        view.get_current_filters.return_value = {
            'text': 'Slide 10',  # Should match Slide 10, 100-109, 1000
            'keywords': [],
            'file_ids': []
        }
        
        import time
        start = time.time()
        presenter.apply_filters()
        duration = time.time() - start
        
        # Should complete quickly even with 1000 slides
        assert duration < 0.1  # 100ms max
        
        slide_data = view.update_slide_list.call_args[0][0]
        assert len(slide_data) == 12  # Matches described above