"""
Unit tests for SlideConverter service.
"""
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import tempfile

import pytest

from slideman.services.slide_converter import SlideConverter, ConversionWorker
from slideman.services.exceptions import PowerPointError, ValidationError


class TestSlideConverter:
    """Test suite for SlideConverter service."""

    @pytest.fixture
    def converter(self):
        """Create SlideConverter instance."""
        return SlideConverter()

    @pytest.fixture
    def mock_powerpoint(self):
        """Create mock PowerPoint application."""
        mock_app = MagicMock()
        mock_app.Visible = False
        mock_app.Presentations = MagicMock()
        
        # Mock presentation
        mock_pres = MagicMock()
        mock_pres.Slides = MagicMock()
        mock_pres.Slides.Count = 3
        
        # Mock slides
        slides = []
        for i in range(1, 4):
            slide = MagicMock()
            slide.SlideNumber = i
            slide.Shapes = MagicMock()
            slide.Shapes.Title = f"Slide {i} Title"
            slide.NotesPage = MagicMock()
            slide.NotesPage.Shapes = MagicMock()
            slide.NotesPage.Shapes.Placeholders = MagicMock()
            
            # Mock notes
            notes_shape = MagicMock()
            notes_shape.TextFrame = MagicMock()
            notes_shape.TextFrame.TextRange = MagicMock()
            notes_shape.TextFrame.TextRange.Text = f"Notes for slide {i}"
            slide.NotesPage.Shapes.Placeholders.return_value = notes_shape
            
            slides.append(slide)
        
        mock_pres.Slides.__iter__ = Mock(return_value=iter(slides))
        mock_pres.Slides.__getitem__ = Mock(side_effect=lambda x: slides[x-1] if 1 <= x <= 3 else None)
        
        mock_app.Presentations.Open.return_value = mock_pres
        
        return mock_app, mock_pres, slides

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create temporary output directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        return output_dir

    @patch('slideman.services.slide_converter.platform.system')
    def test_initialization_windows(self, mock_platform, converter):
        """Test initialization on Windows."""
        mock_platform.return_value = 'Windows'
        assert converter._powerpoint_app is None

    @patch('slideman.services.slide_converter.platform.system')
    def test_initialization_non_windows(self, mock_platform):
        """Test initialization on non-Windows raises error."""
        mock_platform.return_value = 'Linux'
        with pytest.raises(PowerPointError) as exc_info:
            SlideConverter()
        assert "Windows" in str(exc_info.value)

    @patch('slideman.services.slide_converter.win32com.client.Dispatch')
    def test_ensure_powerpoint_started(self, mock_dispatch, converter):
        """Test PowerPoint application startup."""
        mock_app = Mock()
        mock_dispatch.return_value = mock_app
        
        converter._ensure_powerpoint_started()
        
        mock_dispatch.assert_called_once_with("PowerPoint.Application")
        assert mock_app.Visible is False
        assert converter._powerpoint_app == mock_app

    @patch('slideman.services.slide_converter.win32com.client.Dispatch')
    def test_ensure_powerpoint_com_error(self, mock_dispatch, converter):
        """Test PowerPoint startup with COM error."""
        mock_dispatch.side_effect = Exception("COM Error")
        
        with pytest.raises(PowerPointError) as exc_info:
            converter._ensure_powerpoint_started()
        assert "Failed to start PowerPoint" in str(exc_info.value)

    def test_convert_slide_to_image_success(self, converter, mock_powerpoint, temp_output_dir):
        """Test successful slide to image conversion."""
        mock_app, mock_pres, slides = mock_powerpoint
        converter._powerpoint_app = mock_app
        
        output_path = temp_output_dir / "slide_1.png"
        
        # Mock the Export method
        slides[0].Export = Mock()
        
        with patch.object(converter, '_open_presentation', return_value=mock_pres):
            result = converter.convert_slide_to_image(
                "test.pptx", 1, str(output_path), width=1920, height=1080
            )
        
        assert result == str(output_path)
        slides[0].Export.assert_called_once_with(str(output_path), "PNG", 1920, 1080)

    def test_convert_slide_invalid_number(self, converter, mock_powerpoint):
        """Test converting slide with invalid number."""
        mock_app, mock_pres, _ = mock_powerpoint
        converter._powerpoint_app = mock_app
        
        with patch.object(converter, '_open_presentation', return_value=mock_pres):
            with pytest.raises(ValidationError) as exc_info:
                converter.convert_slide_to_image("test.pptx", 5, "output.png")
            assert "Invalid slide number" in str(exc_info.value)

    def test_extract_slide_data_success(self, converter, mock_powerpoint):
        """Test extracting slide data."""
        mock_app, mock_pres, slides = mock_powerpoint
        converter._powerpoint_app = mock_app
        
        # Add shapes to first slide
        shapes = []
        
        # Title shape
        title_shape = MagicMock()
        title_shape.Type = 1  # msoTextBox
        title_shape.HasTextFrame = True
        title_shape.TextFrame = MagicMock()
        title_shape.TextFrame.HasText = True
        title_shape.TextFrame.TextRange = MagicMock()
        title_shape.TextFrame.TextRange.Text = "Main Title"
        shapes.append(title_shape)
        
        # Image shape
        image_shape = MagicMock()
        image_shape.Type = 13  # msoPicture
        image_shape.HasTextFrame = False
        shapes.append(image_shape)
        
        slides[0].Shapes.__iter__ = Mock(return_value=iter(shapes))
        slides[0].Shapes.Count = len(shapes)
        
        with patch.object(converter, '_open_presentation', return_value=mock_pres):
            result = converter.extract_slide_data("test.pptx", 1)
        
        assert result["slide_number"] == 1
        assert result["title"] == "Slide 1 Title"
        assert result["notes"] == "Notes for slide 1"
        assert len(result["shapes"]) == 2
        assert result["shapes"][0]["type"] == "text"
        assert result["shapes"][0]["content"] == "Main Title"
        assert result["shapes"][1]["type"] == "image"

    def test_convert_presentation_success(self, converter, mock_powerpoint, temp_output_dir):
        """Test converting entire presentation."""
        mock_app, mock_pres, slides = mock_powerpoint
        converter._powerpoint_app = mock_app
        
        # Mock Export for all slides
        for slide in slides:
            slide.Export = Mock()
        
        # Add shapes to slides
        for i, slide in enumerate(slides):
            shape = MagicMock()
            shape.Type = 1  # Text
            shape.HasTextFrame = True
            shape.TextFrame = MagicMock()
            shape.TextFrame.HasText = True
            shape.TextFrame.TextRange = MagicMock()
            shape.TextFrame.TextRange.Text = f"Shape on slide {i+1}"
            slide.Shapes.__iter__ = Mock(return_value=iter([shape]))
            slide.Shapes.Count = 1
        
        with patch.object(converter, '_open_presentation', return_value=mock_pres):
            results = converter.convert_presentation("test.pptx", str(temp_output_dir))
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["slide_number"] == i + 1
            assert result["title"] == f"Slide {i+1} Title"
            assert result["thumbnail_path"] == str(temp_output_dir / f"slide_{i+1}.png")
            assert len(result["shapes"]) == 1

    def test_convert_presentation_with_progress(self, converter, mock_powerpoint, temp_output_dir):
        """Test conversion with progress callback."""
        mock_app, mock_pres, slides = mock_powerpoint
        converter._powerpoint_app = mock_app
        
        progress_calls = []
        
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        for slide in slides:
            slide.Export = Mock()
            slide.Shapes.__iter__ = Mock(return_value=iter([]))
            slide.Shapes.Count = 0
        
        with patch.object(converter, '_open_presentation', return_value=mock_pres):
            converter.convert_presentation(
                "test.pptx", 
                str(temp_output_dir),
                progress_callback=progress_callback
            )
        
        # Should have 3 progress calls (one per slide)
        assert len(progress_calls) == 3
        assert progress_calls[0] == (1, 3)
        assert progress_calls[1] == (2, 3)
        assert progress_calls[2] == (3, 3)

    def test_open_presentation_success(self, converter, mock_powerpoint):
        """Test opening presentation."""
        mock_app, mock_pres, _ = mock_powerpoint
        converter._powerpoint_app = mock_app
        
        result = converter._open_presentation("test.pptx")
        
        assert result == mock_pres
        mock_app.Presentations.Open.assert_called_once()

    def test_open_presentation_file_not_found(self, converter):
        """Test opening non-existent presentation."""
        mock_app = Mock()
        mock_app.Presentations.Open.side_effect = Exception("File not found")
        converter._powerpoint_app = mock_app
        
        with pytest.raises(PowerPointError) as exc_info:
            converter._open_presentation("missing.pptx")
        assert "Failed to open presentation" in str(exc_info.value)

    def test_extract_shapes_data(self, converter):
        """Test extracting shape data from slide."""
        shapes = []
        
        # Text shape
        text_shape = MagicMock()
        text_shape.Type = 1  # msoTextBox
        text_shape.HasTextFrame = True
        text_shape.TextFrame.HasText = True
        text_shape.TextFrame.TextRange.Text = "Sample text"
        shapes.append(text_shape)
        
        # Chart shape
        chart_shape = MagicMock()
        chart_shape.Type = 3  # msoChart
        chart_shape.HasTextFrame = False
        shapes.append(chart_shape)
        
        # Table shape
        table_shape = MagicMock()
        table_shape.Type = 19  # msoTable
        table_shape.HasTextFrame = False
        shapes.append(table_shape)
        
        mock_slide = MagicMock()
        mock_slide.Shapes.__iter__ = Mock(return_value=iter(shapes))
        
        result = converter._extract_shapes_data(mock_slide)
        
        assert len(result) == 3
        assert result[0]["type"] == "text"
        assert result[0]["content"] == "Sample text"
        assert result[1]["type"] == "chart"
        assert result[2]["type"] == "table"

    def test_cleanup(self, converter):
        """Test cleanup releases PowerPoint."""
        mock_app = Mock()
        mock_app.Quit = Mock()
        converter._powerpoint_app = mock_app
        
        converter.cleanup()
        
        mock_app.Quit.assert_called_once()
        assert converter._powerpoint_app is None

    def test_cleanup_with_error(self, converter):
        """Test cleanup handles errors gracefully."""
        mock_app = Mock()
        mock_app.Quit.side_effect = Exception("COM Error")
        converter._powerpoint_app = mock_app
        
        # Should not raise exception
        converter.cleanup()
        assert converter._powerpoint_app is None

    def test_context_manager(self, converter):
        """Test using converter as context manager."""
        mock_app = Mock()
        mock_app.Quit = Mock()
        
        with patch.object(converter, '_ensure_powerpoint_started'):
            converter._powerpoint_app = mock_app
            
            with converter as conv:
                assert conv == converter
            
            mock_app.Quit.assert_called_once()


class TestConversionWorker:
    """Test suite for ConversionWorker."""

    @pytest.fixture
    def mock_converter(self):
        """Create mock slide converter."""
        converter = Mock(spec=SlideConverter)
        converter.convert_presentation.return_value = [
            {"slide_number": 1, "title": "Slide 1", "thumbnail_path": "thumb1.png"},
            {"slide_number": 2, "title": "Slide 2", "thumbnail_path": "thumb2.png"}
        ]
        return converter

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = Mock()
        db.create_slide.return_value = Mock(id=1)
        db.create_element.return_value = Mock(id=1)
        db.update_file_status.return_value = None
        return db

    def test_worker_initialization(self, mock_converter, mock_db_service):
        """Test worker initialization."""
        worker = ConversionWorker(
            file_id=1,
            file_path="test.pptx",
            output_dir="output",
            converter=mock_converter,
            db_service=mock_db_service
        )
        
        assert worker.file_id == 1
        assert worker.file_path == "test.pptx"
        assert worker.output_dir == "output"

    @patch('slideman.services.slide_converter.QThread.run')
    def test_worker_successful_conversion(self, mock_run, mock_converter, mock_db_service):
        """Test successful conversion in worker."""
        worker = ConversionWorker(
            file_id=1,
            file_path="test.pptx",
            output_dir="output",
            converter=mock_converter,
            db_service=mock_db_service
        )
        
        # Mock the run method to call our logic directly
        with patch.object(worker, 'run', wraps=worker.run):
            worker.run()
        
        # Verify conversion was called
        mock_converter.convert_presentation.assert_called_once()
        
        # Verify database updates
        assert mock_db_service.create_slide.call_count == 2
        mock_db_service.update_file_status.assert_called()

    def test_worker_conversion_error(self, mock_converter, mock_db_service):
        """Test worker handling conversion error."""
        mock_converter.convert_presentation.side_effect = PowerPointError("Conversion failed")
        
        worker = ConversionWorker(
            file_id=1,
            file_path="test.pptx",
            output_dir="output",
            converter=mock_converter,
            db_service=mock_db_service
        )
        
        with patch.object(worker.error, 'emit') as mock_error:
            worker.run()
            
            mock_error.assert_called_once()
            assert "Conversion failed" in mock_error.call_args[0][1]