"""
Unit tests for KeywordManagerPresenter.
"""
from unittest.mock import Mock, patch, call, mock_open
from datetime import datetime
import csv

import pytest

from slideman.presenters.keyword_manager_presenter import KeywordManagerPresenter, IKeywordManagerView
from slideman.models import Slide, Element, Keyword
from slideman.services.exceptions import DatabaseError, ValidationError
from slideman.commands.merge_keywords_cmd import MergeKeywordsCommand
from slideman.commands.manage_slide_keyword import ManageSlideKeywordCommand
from slideman.commands.manage_element_keyword import ManageElementKeywordCommand


class TestKeywordManagerPresenter:
    """Test suite for KeywordManagerPresenter."""

    @pytest.fixture
    def view(self):
        """Create a mock keyword manager view."""
        view = Mock(spec=IKeywordManagerView)
        view.update_keyword_table = Mock()
        view.update_suggestions = Mock()
        view.update_element_list = Mock()
        view.update_slide_preview = Mock()
        view.clear_editing_panels = Mock()
        view.show_editing_panels = Mock()
        view.get_selected_slide_id = Mock(return_value=None)
        view.get_selected_element_id = Mock(return_value=None)
        view.get_slide_tag_edits = Mock(return_value=([], []))
        view.get_element_tag_edits = Mock(return_value=[])
        view.update_status = Mock()
        view.update_statistics = Mock()
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
        """Create a KeywordManagerPresenter instance."""
        with patch('slideman.presenters.keyword_manager_presenter.app_state') as mock_state:
            mock_state.undo_stack = Mock()
            mock_state.current_project = 1
            presenter = KeywordManagerPresenter(view, services)
            presenter.app_state = mock_state
            return presenter

    @pytest.fixture
    def sample_slides_data(self):
        """Create sample slides with keywords."""
        return [
            {
                'slide_id': 1,
                'slide_title': 'Slide 1',
                'file_name': 'test.pptx',
                'keywords': ['important', 'intro'],
                'keyword_ids': [1, 2]
            },
            {
                'slide_id': 2,
                'slide_title': 'Slide 2',
                'file_name': 'test.pptx',
                'keywords': ['demo', 'important'],
                'keyword_ids': [3, 1]
            }
        ]

    def test_initialization(self, presenter, view, services):
        """Test presenter initialization."""
        assert presenter.view == view
        assert presenter.services == services
        assert presenter._current_project_id is None
        assert presenter._similarity_worker is None
        assert presenter._ignored_pairs == set()

    def test_load_project_data_success(self, presenter, view, services, sample_slides_data):
        """Test loading project keyword data."""
        slides = [
            Slide(id=1, file_id=1, slide_number=1, title="Slide 1", notes="", thumbnail_path=""),
            Slide(id=2, file_id=1, slide_number=2, title="Slide 2", notes="", thumbnail_path="")
        ]
        keywords_map = {
            1: [Keyword(id=1, name="important"), Keyword(id=2, name="intro")],
            2: [Keyword(id=3, name="demo"), Keyword(id=1, name="important")]
        }
        
        services['database'].get_project_slides.return_value = slides
        services['database'].get_file.return_value = Mock(name="test.pptx")
        services['database'].get_slide_keywords.side_effect = lambda sid: keywords_map.get(sid, [])
        services['database'].get_all_keywords.return_value = [
            Keyword(id=1, name="important"),
            Keyword(id=2, name="intro"),
            Keyword(id=3, name="demo"),
            Keyword(id=4, name="unused")
        ]
        services['database'].get_keyword_usage_count.side_effect = lambda kid: {1: 2, 2: 1, 3: 1, 4: 0}[kid]
        
        presenter.load_project_data(1)
        
        assert presenter._current_project_id == 1
        view.update_keyword_table.assert_called_once()
        view.update_statistics.assert_called_once_with(4, 1)  # 4 total, 1 unused
        
        # Check similarity detection started
        assert presenter._similarity_worker is not None

    def test_load_project_data_no_project(self, presenter, view):
        """Test loading with no project."""
        presenter.load_project_data(None)
        
        view.update_keyword_table.assert_called_once_with([])
        view.update_suggestions.assert_called_once_with([])
        view.clear_editing_panels.assert_called_once()

    def test_apply_slide_tag_changes(self, presenter, view, services):
        """Test applying slide tag changes."""
        view.get_selected_slide_id.return_value = 1
        view.get_slide_tag_edits.return_value = (['new_tag'], ['old_tag'])
        
        services['database'].get_keyword_by_name.side_effect = lambda name: {
            'new_tag': Keyword(id=5, name='new_tag'),
            'old_tag': Keyword(id=6, name='old_tag')
        }.get(name)
        
        with patch('slideman.presenters.keyword_manager_presenter.ManageSlideKeywordCommand') as mock_cmd:
            mock_command = Mock()
            mock_cmd.return_value = mock_command
            
            presenter.apply_slide_tag_changes()
            
            # Should create 2 commands (1 add, 1 remove)
            assert mock_cmd.call_count == 2
            assert presenter.app_state.undo_stack.push.call_count == 2

    def test_find_similar_keywords(self, presenter, services):
        """Test finding similar keywords."""
        keywords = [
            Keyword(id=1, name="presentation"),
            Keyword(id=2, name="presentations"),
            Keyword(id=3, name="demo"),
            Keyword(id=4, name="demos"),
            Keyword(id=5, name="test")
        ]
        
        # Mock similarity calculation
        with patch('slideman.presenters.keyword_manager_presenter.KeywordSimilarityWorker') as mock_worker_class:
            mock_worker = Mock()
            mock_worker_class.return_value = mock_worker
            
            # Simulate worker emitting results
            def simulate_work():
                # Call the connected slot with similarity results
                for handler in mock_worker.result.connect.call_args_list:
                    handler[0][0]([
                        {'keyword1': 'presentation', 'keyword2': 'presentations', 
                         'similarity': 0.95, 'usage1': 5, 'usage2': 3},
                        {'keyword1': 'demo', 'keyword2': 'demos',
                         'similarity': 0.88, 'usage1': 10, 'usage2': 2}
                    ])
            
            mock_worker.start.side_effect = simulate_work
            
            presenter.find_similar_keywords(keywords)
            
            view.update_suggestions.assert_called()
            suggestions = view.update_suggestions.call_args[0][0]
            assert len(suggestions) == 2

    def test_merge_selected_keywords(self, presenter, view, services):
        """Test merging selected keywords."""
        view.get_selected_slide_id.return_value = None  # No specific slide selected
        services['database'].get_keyword_by_name.side_effect = lambda name: {
            'important': Keyword(id=1, name='important'),
            'critical': Keyword(id=2, name='critical')
        }.get(name)
        
        with patch('slideman.presenters.keyword_manager_presenter.MergeKeywordsCommand') as mock_cmd:
            mock_command = Mock()
            mock_cmd.return_value = mock_command
            
            presenter.merge_selected_keywords('important', 'critical')
            
            mock_cmd.assert_called_once()
            presenter.app_state.undo_stack.push.assert_called_once_with(mock_command)
            
            # Should add to ignored pairs
            assert ('critical', 'important') in presenter._ignored_pairs

    def test_load_slide_elements(self, presenter, view, services):
        """Test loading slide elements for tagging."""
        slide = Slide(id=1, file_id=1, slide_number=1, title="Test", notes="", thumbnail_path="")
        elements = [
            Element(id=1, slide_id=1, type="shape", content="Shape 1"),
            Element(id=2, slide_id=1, type="text", content="Text box"),
            Element(id=3, slide_id=1, type="image", content="image.png")
        ]
        
        services['database'].get_slide.return_value = slide
        services['database'].get_slide_elements.return_value = elements
        
        presenter.load_slide_elements(1)
        
        view.show_editing_panels.assert_called_once()
        view.update_slide_preview.assert_called_once_with(1, elements)
        
        # Check element list formatting
        element_list = view.update_element_list.call_args[0][0]
        assert len(element_list) == 3
        assert element_list[0]['id'] == 1
        assert element_list[0]['display'] == 'Shape: Shape 1'

    def test_update_element_tags(self, presenter, view, services):
        """Test updating element tags."""
        view.get_selected_element_id.return_value = 1
        view.get_element_tag_edits.return_value = ['tag1', 'tag2']
        
        services['database'].get_keyword_by_name.side_effect = lambda name: {
            'tag1': Keyword(id=1, name='tag1'),
            'tag2': Keyword(id=2, name='tag2')
        }.get(name)
        services['database'].get_element_keywords.return_value = []  # No existing tags
        
        with patch('slideman.presenters.keyword_manager_presenter.ManageElementKeywordCommand') as mock_cmd:
            presenter.update_element_tags()
            
            # Should create 2 add commands
            assert mock_cmd.call_count == 2

    def test_export_keywords_to_csv(self, presenter, view, services):
        """Test exporting keywords to CSV."""
        keywords = [
            Keyword(id=1, name="important"),
            Keyword(id=2, name="demo"),
            Keyword(id=3, name="unused")
        ]
        services['database'].get_all_keywords.return_value = keywords
        services['database'].get_keyword_usage_count.side_effect = lambda kid: {1: 5, 2: 3, 3: 0}[kid]
        
        with patch('slideman.presenters.keyword_manager_presenter.QFileDialog') as mock_dialog:
            mock_dialog.getSaveFileName.return_value = ('/output/keywords.csv', '')
            
            with patch('builtins.open', mock_open()) as mock_file:
                presenter.export_keywords_to_csv()
                
                # Verify CSV writing
                mock_file.assert_called_once_with('/output/keywords.csv', 'w', newline='', encoding='utf-8')
                handle = mock_file()
                
                # Check that data was written (exact format may vary)
                write_calls = handle.write.call_args_list
                assert any('Keyword' in str(call) for call in write_calls)
                assert any('important' in str(call) for call in write_calls)

    def test_export_keywords_cancelled(self, presenter, view):
        """Test export when user cancels file dialog."""
        with patch('slideman.presenters.keyword_manager_presenter.QFileDialog') as mock_dialog:
            mock_dialog.getSaveFileName.return_value = ('', '')  # Cancelled
            
            presenter.export_keywords_to_csv()
            
            view.show_info.assert_not_called()
            view.show_error.assert_not_called()

    def test_ignore_suggestion_pair(self, presenter, view):
        """Test ignoring a suggestion pair."""
        initial_suggestions = [
            {'keyword1': 'test', 'keyword2': 'tests', 'similarity': 0.9},
            {'keyword1': 'demo', 'keyword2': 'demos', 'similarity': 0.85}
        ]
        
        # Set up initial state
        presenter._last_suggestions = initial_suggestions.copy()
        
        presenter.ignore_suggestion_pair('test', 'tests')
        
        assert ('test', 'tests') in presenter._ignored_pairs
        
        # Should update suggestions to exclude ignored pair
        view.update_suggestions.assert_called()
        updated = view.update_suggestions.call_args[0][0]
        assert len(updated) == 1
        assert updated[0]['keyword1'] == 'demo'

    def test_cleanup_stops_worker(self, presenter):
        """Test that cleanup stops similarity worker."""
        mock_worker = Mock()
        mock_worker.isRunning.return_value = True
        presenter._similarity_worker = mock_worker
        
        presenter.cleanup()
        
        mock_worker.quit.assert_called_once()
        mock_worker.wait.assert_called_once_with(5000)

    def test_error_handling_database_error(self, presenter, view, services):
        """Test handling database errors gracefully."""
        services['database'].get_project_slides.side_effect = DatabaseError("Connection lost")
        
        presenter.load_project_data(1)
        
        view.show_error.assert_called_once()
        view.update_keyword_table.assert_called_with([])

    def test_statistics_calculation(self, presenter, services):
        """Test keyword statistics calculation."""
        keywords = [
            Keyword(id=i, name=f"keyword{i}")
            for i in range(1, 11)
        ]
        services['database'].get_all_keywords.return_value = keywords
        
        # 7 used, 3 unused
        usage_counts = {i: (10-i if i <= 7 else 0) for i in range(1, 11)}
        services['database'].get_keyword_usage_count.side_effect = lambda kid: usage_counts[kid]
        
        # Load project to trigger statistics
        services['database'].get_project_slides.return_value = []
        presenter.load_project_data(1)
        
        # Should report 10 total, 3 unused
        presenter.view.update_statistics.assert_called_with(10, 3)