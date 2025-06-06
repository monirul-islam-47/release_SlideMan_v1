# tests/services/test_export_service.py

import pytest
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
from threading import Event

from slideman.services.export_service import ExportWorker, ExportWorkerSignals
from slideman.services.database import Database

# We'll use mocks rather than launching real PowerPoint instances
# If you need to skip these tests, you can use:
# pytest -k "not test_export_service"

@pytest.fixture
def mock_com_libraries():
    """Mock win32com and related libraries."""
    with patch("slideman.services.export_service.pythoncom") as mock_pythoncom, \
         patch("slideman.services.export_service.win32com") as mock_win32com, \
         patch("slideman.services.export_service.HAS_COM", True):
        
        # Mock the PowerPoint Application
        mock_ppt_app = MagicMock()
        mock_presentations = MagicMock()
        mock_presentation = MagicMock()
        mock_slides = MagicMock()
        mock_slide = MagicMock()
        
        # Set up the mock structure
        mock_win32com.client.Dispatch.return_value = mock_ppt_app
        mock_ppt_app.Presentations = mock_presentations
        mock_presentations.Add.return_value = mock_presentation
        mock_presentations.Open.return_value = mock_presentation
        mock_presentation.Slides = mock_slides
        mock_slides.Count = 5  # Mock 5 slides in the presentation
        
        # Mock the slide operations
        mock_presentation.Slides.return_value = mock_slides
        mock_slides.Paste.return_value = None
        
        yield {
            "pythoncom": mock_pythoncom,
            "win32com": mock_win32com,
            "ppt_app": mock_ppt_app,
            "presentation": mock_presentation,
            "slides": mock_slides
        }

@pytest.fixture
def mock_db():
    """Create a mock database with test slide data."""
    mock_db = MagicMock(spec=Database)
    
    # Mock the get_slide_origin method to return valid data
    def get_slide_origin_side_effect(slide_id):
        # Return (source_file_path, slide_index) tuple
        mock_paths = {
            1: (r"C:\path\to\test1.pptx", 1),
            2: (r"C:\path\to\test1.pptx", 2),
            3: (r"C:\path\to\test2.pptx", 1),
            4: (r"C:\path\to\nonexistent.pptx", 1),  # Will cause file not found error
            5: None,  # Will cause slide origin not found error
        }
        return mock_paths.get(slide_id, None)
    
    mock_db.get_slide_origin.side_effect = get_slide_origin_side_effect
    return mock_db

@pytest.fixture
def temp_output_path(tmp_path):
    """Create a temporary output path for test exports."""
    return tmp_path / "test_export.pptx"

class TestExportWorker:
    
    def test_init_validation(self, mock_db):
        """Test constructor validation."""
        # Valid initialization
        worker = ExportWorker([1, 2, 3], 'save', Path("output.pptx"), mock_db)
        assert worker.ordered_slide_ids == [1, 2, 3]
        assert worker.output_mode == 'save'
        assert worker.output_path == Path("output.pptx")
        assert worker.db_service == mock_db
        assert worker.is_cancelled is False
        
        # Empty slide list
        with pytest.raises(ValueError) as excinfo:
            ExportWorker([], 'save', Path("output.pptx"), mock_db)
        assert "non-empty list" in str(excinfo.value)
        
        # Missing output path in save mode
        with pytest.raises(ValueError) as excinfo:
            ExportWorker([1], 'save', None, mock_db)
        assert "Output path is required" in str(excinfo.value)
    
    def test_export_open_mode(self, mock_com_libraries, mock_db, monkeypatch):
        """Test exporting in 'open' mode (PowerPoint opens without saving)."""
        # Setup
        monkeypatch.setattr("os.path.exists", lambda path: True)  # Simulate all files exist
        
        # Create signal tracking
        progress_updates = []
        finished_message = []
        error_message = []
        
        # Create worker
        worker = ExportWorker([1, 2, 3], 'open', None, mock_db)
        
        # Connect signals
        worker.signals.exportProgress.connect(lambda current, total: progress_updates.append((current, total)))
        worker.signals.exportFinished.connect(lambda msg: finished_message.append(msg))
        worker.signals.exportError.connect(lambda msg: error_message.append(msg))
        
        # Execute
        worker.run()
        
        # Assert
        assert len(progress_updates) == 3
        assert progress_updates[-1] == (3, 3)  # Final progress should be (3, 3)
        assert len(finished_message) == 1
        assert "Presentation opened in PowerPoint" in finished_message[0]
        assert len(error_message) == 0
        
        # Verify PowerPoint interactions
        mock_app = mock_com_libraries["ppt_app"]
        assert mock_app.Visible is True
        mock_app.Presentations.Add.assert_called_once()
        
        # Verify all slides were processed
        assert mock_db.get_slide_origin.call_count == 3
        assert mock_com_libraries["slides"].Paste.call_count == 3
    
    def test_export_save_mode(self, mock_com_libraries, mock_db, temp_output_path, monkeypatch):
        """Test exporting in 'save' mode (PowerPoint saves to file)."""
        # Setup
        monkeypatch.setattr("os.path.exists", lambda path: True)  # Simulate all files exist
        
        # Create signal tracking
        progress_updates = []
        finished_message = []
        error_message = []
        
        # Create worker
        worker = ExportWorker([1, 2, 3], 'save', temp_output_path, mock_db)
        
        # Connect signals
        worker.signals.exportProgress.connect(lambda current, total: progress_updates.append((current, total)))
        worker.signals.exportFinished.connect(lambda msg: finished_message.append(msg))
        worker.signals.exportError.connect(lambda msg: error_message.append(msg))
        
        # Execute
        worker.run()
        
        # Assert
        assert len(progress_updates) == 3
        assert progress_updates[-1] == (3, 3)  # Final progress should be (3, 3)
        assert len(finished_message) == 1
        assert str(temp_output_path) in finished_message[0]
        assert len(error_message) == 0
        
        # Verify PowerPoint interactions
        mock_presentation = mock_com_libraries["presentation"]
        mock_presentation.SaveAs.assert_called_once_with(str(temp_output_path))
        mock_presentation.Close.assert_called()
    
    def test_error_handling_missing_source_file(self, mock_com_libraries, mock_db, monkeypatch):
        """Test error handling when source file doesn't exist."""
        # Setup - simulate file 1 exists but file 4 doesn't
        def mock_exists(path):
            return "nonexistent" not in path
        
        monkeypatch.setattr("os.path.exists", mock_exists)
        
        # Create signal tracking
        progress_updates = []
        finished_message = []
        error_message = []
        
        # Create worker
        worker = ExportWorker([1, 4], 'open', None, mock_db)
        
        # Connect signals
        worker.signals.exportProgress.connect(lambda current, total: progress_updates.append((current, total)))
        worker.signals.exportFinished.connect(lambda msg: finished_message.append(msg))
        worker.signals.exportError.connect(lambda msg: error_message.append(msg))
        
        # Execute
        worker.run()
        
        # Assert
        # Verify we get some progress updates
        assert len(progress_updates) > 0
        
        # Verify an error message was emitted
        assert len(error_message) > 0
        
        # We can't be certain of the exact error message format in the mock environment
        # Just verify there was an error message emitted
    
    def test_error_handling_slide_origin_not_found(self, mock_com_libraries, mock_db, monkeypatch):
        """Test error handling when slide origin information is missing."""
        # Setup
        monkeypatch.setattr("os.path.exists", lambda path: True)  # Simulate all files exist
        
        # Create signal tracking
        progress_updates = []
        finished_message = []
        error_message = []
        
        # Create worker with a slide that has no origin information
        worker = ExportWorker([1, 5], 'open', None, mock_db)
        
        # Connect signals
        worker.signals.exportProgress.connect(lambda current, total: progress_updates.append((current, total)))
        worker.signals.exportFinished.connect(lambda msg: finished_message.append(msg))
        worker.signals.exportError.connect(lambda msg: error_message.append(msg))
        
        # Execute
        worker.run()
        
        # Assert
        # Verify we get some progress updates (at least for the valid slide)
        assert len(progress_updates) > 0
        
        # Verify an error message was emitted
        assert len(error_message) > 0
        
        # The error could be combined in the final error message or emitted separately
        # Just verify there was an error message emitted
    
    def test_export_cancellation(self, mock_com_libraries, mock_db, monkeypatch):
        """Test cancellation of export process."""
        # Setup
        monkeypatch.setattr("os.path.exists", lambda path: True)
        
        # Create a worker with many slides for longer processing
        worker = ExportWorker([1, 2, 3, 1, 2, 3, 1, 2, 3], 'open', None, mock_db)
        
        # Create signal tracking
        progress_updates = []
        finished_message = []
        error_message = []
        
        # Connect signals
        worker.signals.exportProgress.connect(lambda current, total: progress_updates.append((current, total)))
        worker.signals.exportFinished.connect(lambda msg: finished_message.append(msg))
        worker.signals.exportError.connect(lambda msg: error_message.append(msg))
        
        # Mock slide processing to set cancelled after 2nd slide
        original_get_slide_origin = mock_db.get_slide_origin
        processed_count = [0]
        
        def get_slide_origin_with_cancel(slide_id):
            processed_count[0] += 1
            if processed_count[0] == 2:
                worker.cancel()
            return original_get_slide_origin(slide_id)
            
        mock_db.get_slide_origin = get_slide_origin_with_cancel
        
        # Execute
        worker.run()
        
        # Assert
        assert worker.is_cancelled is True  # Cancellation flag was set
        assert len(finished_message) == 0   # No success message
        assert len(error_message) == 1      # Error message is emitted
        
        # We can't guarantee the exact text because it depends on the implementation
        # Just verify an error message was emitted when cancelled
    
    def test_critical_error_handling(self, mock_com_libraries, mock_db):
        """Test handling of critical errors during export."""
        # Setup - make PowerPoint creation fail
        mock_com_libraries["win32com"].client.Dispatch.side_effect = Exception("PowerPoint not available")
        
        # Create signal tracking
        error_message = []
        
        # Create worker
        worker = ExportWorker([1, 2, 3], 'open', None, mock_db)
        
        # Connect signals
        worker.signals.exportError.connect(lambda msg: error_message.append(msg))
        
        # Execute
        worker.run()
        
        # Assert
        assert len(error_message) == 1
        assert "Critical export error" in error_message[0]
        assert "PowerPoint not available" in error_message[0]
    
    def test_large_export(self, mock_com_libraries, mock_db, monkeypatch):
        """Test exporting a large number of slides."""
        # Setup
        monkeypatch.setattr("os.path.exists", lambda path: True)
        
        # Create a large list of slide IDs
        large_slide_list = [1, 2, 3] * 20  # 60 slides
        
        # Create signal tracking
        progress_updates = []
        finished_message = []
        
        # Create worker
        worker = ExportWorker(large_slide_list, 'open', None, mock_db)
        
        # Connect signals
        worker.signals.exportProgress.connect(lambda current, total: progress_updates.append((current, total)))
        worker.signals.exportFinished.connect(lambda msg: finished_message.append(msg))
        
        # Execute
        worker.run()
        
        # Assert
        assert len(progress_updates) == 60
        assert progress_updates[-1] == (60, 60)
        assert len(finished_message) == 1
        
        # Verify PowerPoint interactions
        assert mock_db.get_slide_origin.call_count == 60
        assert mock_com_libraries["slides"].Paste.call_count == 60

if __name__ == "__main__":
    pytest.main(["-v", "test_export_service.py"])
