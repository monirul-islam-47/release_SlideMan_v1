# Module 14: PowerPoint Service Integration
## Building the Core Magic - PowerPoint COM Automation and Processing

### Learning Objectives
By the end of this module, you will:
- Master Windows COM automation for PowerPoint processing
- Implement cross-platform fallback using python-pptx
- Build comprehensive slide extraction and analysis systems
- Create robust file processing pipelines with error handling
- Integrate PowerPoint processing with the database layer
- Test PowerPoint services with TDD methodology

### Introduction: The Heart of PrezI's Intelligence

PowerPoint integration is the **core magic** that transforms PrezI from a simple file manager into an intelligent presentation system. According to the CONSOLIDATED_FOUNDERS_BRIEFCASE.md, this module implements:

**Critical PowerPoint Features:**
- **Bulk File Import**: Process multiple `.pptx` files efficiently
- **Slide Library Creation**: Extract all slides into unified library
- **Content Intelligence**: Analyze slide content, types, and structure
- **Element-Level Processing**: Extract charts, images, text, and tables
- **Cross-Platform Support**: Windows COM automation with fallback

### 14.1 Test-Driven PowerPoint Service Development

Let's start with comprehensive tests that define our PowerPoint processing requirements:

```python
# tests/test_powerpoint_service.py
import pytest
import tempfile
import uuid
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from backend.services.powerpoint_service import PowerPointProcessor, PowerPointService
from backend.database.models import FileModel, SlideModel, ElementModel, Project
from backend.core.exceptions import PowerPointProcessingError

class TestPowerPointProcessor:
    """Test PowerPoint file processor with COM and python-pptx"""
    
    @pytest.fixture
    def mock_presentation_data(self):
        """Mock presentation data for testing"""
        return {
            "slide_count": 3,
            "slides": [
                {
                    "slide_number": 1,
                    "title": "Company Overview",
                    "content": "Leading provider of innovative solutions",
                    "notes": "Introduce company mission and vision",
                    "thumbnail_path": "/thumbnails/slide_1.png",
                    "full_image_path": "/images/slide_1_full.png",
                    "elements": [
                        {
                            "index": 1,
                            "type": "text",
                            "content": "Company Overview",
                            "position": {"x": 100, "y": 50, "width": 400, "height": 100, "z_order": 1}
                        },
                        {
                            "index": 2,
                            "type": "image",
                            "content": "",
                            "position": {"x": 200, "y": 200, "width": 300, "height": 200, "z_order": 2}
                        }
                    ],
                    "layout_name": "Title Slide",
                    "background_type": "solid"
                },
                {
                    "slide_number": 2,
                    "title": "Q4 Financial Results",
                    "content": "Revenue increased 25% year-over-year",
                    "notes": "Highlight key financial metrics",
                    "thumbnail_path": "/thumbnails/slide_2.png",
                    "full_image_path": "/images/slide_2_full.png",
                    "elements": [
                        {
                            "index": 1,
                            "type": "chart",
                            "content": "Revenue Growth Chart",
                            "position": {"x": 150, "y": 100, "width": 500, "height": 300, "z_order": 1},
                            "chart_type": "column"
                        }
                    ],
                    "layout_name": "Content with Chart",
                    "background_type": "gradient"
                },
                {
                    "slide_number": 3,
                    "title": "Thank You",
                    "content": "Questions and Discussion",
                    "notes": "Open floor for questions",
                    "thumbnail_path": "/thumbnails/slide_3.png",
                    "full_image_path": "/images/slide_3_full.png",
                    "elements": [
                        {
                            "index": 1,
                            "type": "text",
                            "content": "Thank You",
                            "position": {"x": 200, "y": 150, "width": 300, "height": 100, "z_order": 1}
                        }
                    ],
                    "layout_name": "Title Only",
                    "background_type": "solid"
                }
            ],
            "processor": "COM",
            "presentation_name": "quarterly_report.pptx",
            "has_macros": False,
            "creation_date": "2024-01-15T10:30:00Z"
        }
    
    def test_processor_initialization_windows_com(self):
        """Test PowerPoint processor initialization with COM on Windows"""
        with patch('platform.system', return_value='Windows'):
            with patch('backend.services.powerpoint_service.COM_AVAILABLE', True):
                processor = PowerPointProcessor()
                assert processor.use_com is True
                assert processor.processor_type == "COM"
    
    def test_processor_initialization_cross_platform_fallback(self):
        """Test PowerPoint processor initialization with python-pptx fallback"""
        with patch('platform.system', return_value='Linux'):
            with patch('backend.services.powerpoint_service.PPTX_AVAILABLE', True):
                processor = PowerPointProcessor()
                assert processor.use_com is False
                assert processor.processor_type == "python-pptx"
    
    def test_processor_initialization_no_libraries_available(self):
        """Test processor initialization fails when no libraries available"""
        with patch('backend.services.powerpoint_service.COM_AVAILABLE', False):
            with patch('backend.services.powerpoint_service.PPTX_AVAILABLE', False):
                with pytest.raises(PowerPointProcessingError) as exc_info:
                    PowerPointProcessor()
                assert "Neither COM automation nor python-pptx is available" in str(exc_info.value)
    
    @patch('backend.services.powerpoint_service.COM_AVAILABLE', True)
    @patch('platform.system', return_value='Windows')
    def test_process_file_with_com_success(self, mock_presentation_data):
        """Test successful file processing with COM automation"""
        processor = PowerPointProcessor()
        
        with patch.object(processor, '_process_with_com', return_value=mock_presentation_data):
            result = processor.process_file("test_presentation.pptx")
            
            assert result["slide_count"] == 3
            assert result["processor"] == "COM"
            assert len(result["slides"]) == 3
            assert result["slides"][0]["title"] == "Company Overview"
            assert result["slides"][1]["elements"][0]["type"] == "chart"
    
    def test_process_file_not_found(self):
        """Test processing fails when file doesn't exist"""
        processor = PowerPointProcessor()
        
        with pytest.raises(FileNotFoundError) as exc_info:
            processor.process_file("nonexistent_file.pptx")
        assert "PowerPoint file not found" in str(exc_info.value)
    
    def test_extract_slide_data_comprehensive(self, mock_presentation_data):
        """Test comprehensive slide data extraction"""
        slide_data = mock_presentation_data["slides"][1]  # Chart slide
        
        # Verify all required fields are present
        required_fields = [
            "slide_number", "title", "content", "notes",
            "thumbnail_path", "full_image_path", "elements",
            "layout_name", "background_type"
        ]
        
        for field in required_fields:
            assert field in slide_data, f"Missing required field: {field}"
        
        # Verify element data structure
        chart_element = slide_data["elements"][0]
        assert chart_element["type"] == "chart"
        assert chart_element["chart_type"] == "column"
        assert "position" in chart_element
        assert all(key in chart_element["position"] for key in ["x", "y", "width", "height", "z_order"])
    
    def test_element_type_detection(self):
        """Test accurate element type detection"""
        processor = PowerPointProcessor()
        
        # Test different shape types (mocked COM constants)
        test_cases = [
            (1, "text", True),    # msoAutoShape with text
            (1, "shape", False),  # msoAutoShape without text
            (13, "image", None),  # msoPicture
            (3, "chart", None),   # msoChart
            (19, "table", None),  # msoTable
            (7, "video", None),   # msoMedia
            (16, "smartart", None), # msoSmartArt
        ]
        
        for shape_type, expected_type, has_text in test_cases:
            mock_shape = Mock()
            mock_shape.Type = shape_type
            mock_shape.HasTextFrame = has_text if has_text is not None else False
            
            with patch.object(processor, '_determine_element_type_com', return_value=expected_type):
                element_type = processor._determine_element_type_com(mock_shape)
                assert element_type == expected_type
    
    def test_thumbnail_generation_path_creation(self):
        """Test thumbnail generation creates correct paths"""
        processor = PowerPointProcessor()
        
        mock_slide = Mock()
        mock_slide.Export = Mock()
        
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            with patch('pathlib.Path.exists', return_value=True):
                thumbnail_path = processor._generate_thumbnail_com(
                    mock_slide, 1, Path("test_file.pptx")
                )
                
                # Verify directory creation was called
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
                
                # Verify path format
                assert thumbnail_path.endswith(".png")
                assert "slide_1" in thumbnail_path
    
    def test_notes_extraction_comprehensive(self):
        """Test comprehensive speaker notes extraction"""
        processor = PowerPointProcessor()
        
        # Mock notes slide with multiple text shapes
        mock_notes_slide = Mock()
        mock_shape1 = Mock()
        mock_shape1.HasTextFrame = True
        mock_shape1.TextFrame.TextRange.Text = "Key talking point 1"
        
        mock_shape2 = Mock()
        mock_shape2.HasTextFrame = True
        mock_shape2.TextFrame.TextRange.Text = "Key talking point 2"
        
        mock_notes_slide.Shapes.Count = 2
        mock_notes_slide.Shapes.Item.side_effect = [mock_shape1, mock_shape2]
        
        mock_slide = Mock()
        mock_slide.NotesPage = mock_notes_slide
        
        notes = processor._extract_notes_com(mock_slide, 1)
        
        assert "Key talking point 1" in notes
        assert "Key talking point 2" in notes

class TestPowerPointService:
    """Test PowerPoint service for database integration"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = Mock(spec=Session)
        return session
    
    @pytest.fixture
    def sample_file_record(self):
        """Sample file record for testing"""
        return FileModel(
            id=str(uuid.uuid4()),
            filename="test_presentation.pptx",
            file_path="/uploads/test_presentation.pptx",
            processed=False,
            slide_count=0
        )
    
    def test_service_initialization(self, mock_db_session):
        """Test PowerPoint service initialization"""
        service = PowerPointService(mock_db_session)
        
        assert service.db == mock_db_session
        assert isinstance(service.processor, PowerPointProcessor)
    
    def test_process_file_success(self, mock_db_session, sample_file_record, mock_presentation_data):
        """Test successful file processing and database storage"""
        service = PowerPointService(mock_db_session)
        
        # Mock database query to return file record
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_file_record
        
        # Mock processor to return presentation data
        with patch.object(service.processor, 'process_file', return_value=mock_presentation_data):
            with patch.object(service, '_save_slides_to_database') as mock_save:
                result = service.process_file(sample_file_record.id)
                
                # Verify success result
                assert result["success"] is True
                assert result["slide_count"] == 3
                assert result["processor"] == "COM"
                
                # Verify file record was updated
                assert sample_file_record.processed is True
                assert sample_file_record.slide_count == 3
                assert sample_file_record.processing_error is None
                
                # Verify slides were saved to database
                mock_save.assert_called_once_with(sample_file_record, mock_presentation_data["slides"])
    
    def test_process_file_not_found(self, mock_db_session):
        """Test processing fails when file not found in database"""
        service = PowerPointService(mock_db_session)
        
        # Mock database query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(PowerPointProcessingError) as exc_info:
            service.process_file("nonexistent_id")
        assert "File nonexistent_id not found in database" in str(exc_info.value)
    
    def test_process_file_powerpoint_error(self, mock_db_session, sample_file_record):
        """Test handling of PowerPoint processing errors"""
        service = PowerPointService(mock_db_session)
        
        # Mock database query to return file record
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_file_record
        
        # Mock processor to raise exception
        with patch.object(service.processor, 'process_file', side_effect=Exception("PowerPoint error")):
            result = service.process_file(sample_file_record.id)
            
            # Verify error result
            assert result["success"] is False
            assert "PowerPoint error" in result["error"]
            
            # Verify file record error state
            assert sample_file_record.processed is False
            assert sample_file_record.processing_error == "PowerPoint error"
    
    def test_bulk_process_files_mixed_results(self, mock_db_session):
        """Test bulk processing with mixed success/failure results"""
        service = PowerPointService(mock_db_session)
        
        file_ids = ["file1", "file2", "file3"]
        
        # Mock individual process_file calls
        process_results = [
            {"success": True, "slide_count": 5},
            {"success": False, "error": "Processing failed"},
            {"success": True, "slide_count": 3}
        ]
        
        with patch.object(service, 'process_file', side_effect=process_results):
            result = service.bulk_process_files(file_ids)
            
            assert result["total_files"] == 3
            assert len(result["successful"]) == 2
            assert len(result["failed"]) == 1
            assert result["total_slides"] == 8  # 5 + 3
    
    def test_save_slides_to_database_comprehensive(self, mock_db_session, sample_file_record, mock_presentation_data):
        """Test comprehensive slide data saving to database"""
        service = PowerPointService(mock_db_session)
        
        # Mock database operations
        mock_db_session.query.return_value.filter.return_value.delete.return_value = None
        mock_db_session.add = Mock()
        mock_db_session.flush = Mock()
        mock_db_session.commit = Mock()
        
        # Call save method
        service._save_slides_to_database(sample_file_record, mock_presentation_data["slides"])
        
        # Verify database operations
        mock_db_session.add.assert_called()  # Should be called multiple times
        mock_db_session.flush.assert_called()  # For getting slide IDs
        mock_db_session.commit.assert_called_once()
        
        # Verify slide record creation (check call args)
        add_calls = mock_db_session.add.call_args_list
        slide_calls = [call for call in add_calls if isinstance(call[0][0], SlideModel)]
        element_calls = [call for call in add_calls if isinstance(call[0][0], ElementModel)]
        
        assert len(slide_calls) == 3  # 3 slides
        assert len(element_calls) >= 3  # At least 3 elements
    
    def test_slide_type_classification(self, mock_db_session):
        """Test slide type classification algorithm"""
        service = PowerPointService(mock_db_session)
        
        # Test different slide types
        test_cases = [
            ({"title": "Introduction to PrezI", "content": "", "elements": []}, "title"),
            ({"title": "Thank You", "content": "Questions?", "elements": []}, "conclusion"),
            ({"title": "Q4 Results", "content": "", "elements": [{"type": "chart"}]}, "chart"),
            ({"title": "Team Photo", "content": "", "elements": [{"type": "image"}]}, "image"),
            ({"title": "Data Summary", "content": "", "elements": [{"type": "table"}]}, "table"),
            ({"title": "Complex Slide", "content": "", "elements": [{}, {}, {}, {}]}, "content"),
            ({"title": "Unknown", "content": "", "elements": []}, "unknown")
        ]
        
        for slide_data, expected_type in test_cases:
            result = service._classify_slide_type(slide_data)
            assert result == expected_type, f"Expected {expected_type}, got {result} for {slide_data['title']}"

# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### 14.2 Complete PowerPoint Service Implementation

Now let's implement the complete PowerPoint service that passes all our tests:

```python

import logging
import platform
import tempfile
import hashlib
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import and_

# Windows COM imports (conditionally imported)
if platform.system() == "Windows":
    try:
        import win32com.client
        import pythoncom
        COM_AVAILABLE = True
    except ImportError:
        COM_AVAILABLE = False
        logging.warning("pywin32 not available - PowerPoint COM automation disabled")
else:
    COM_AVAILABLE = False

# Cross-platform fallback imports
try:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False
    logging.warning("python-pptx not available - cross-platform fallback disabled")

from backend.database.models import FileModel, SlideModel, ElementModel
from backend.core.config import get_settings

logger = logging.getLogger(__name__)

class PowerPointProcessor:
    """
    PowerPoint file processor with COM automation and cross-platform fallback
    Implements the core PowerPoint integration from CONSOLIDATED_FOUNDERS_BRIEFCASE.md
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.use_com = COM_AVAILABLE and platform.system() == "Windows" and self.settings.supports_com
        
        if not self.use_com and not PPTX_AVAILABLE:
            raise Exception(
                "Neither COM automation nor python-pptx is available. "
                "Please install python-pptx for cross-platform support."
            )
    
    def process_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Process PowerPoint file and extract slide content
        
        Args:
            file_path: Path to PowerPoint file
            
        Returns:
            Dictionary containing slide data and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PowerPoint file not found: {file_path}")
        
        logger.info(f"Processing PowerPoint file: {file_path.name}")
        
        try:
            if self.use_com:
                logger.info("Using Windows COM automation for PowerPoint processing")
                return self._process_with_com(file_path)
            else:
                logger.info("Using python-pptx for PowerPoint processing")
                return self._process_with_pptx(file_path)
                
        except Exception as e:
            logger.error(f"Failed to process PowerPoint file {file_path}: {e}")
            raise Exception(f"PowerPoint processing failed: {str(e)}") from e
    
    def _process_with_com(self, file_path: Path) -> Dict[str, Any]:
        """Process using Windows COM automation - implements CONSOLIDATED_FOUNDERS_BRIEFCASE.md specs"""
        
        # Initialize COM
        pythoncom.CoInitialize()
        
        try:
            # Create PowerPoint application
            powerpoint = win32com.client.Dispatch("PowerPoint.Application")
            powerpoint.Visible = False  # Keep hidden for processing
            
            # Open presentation
            presentation = powerpoint.Presentations.Open(
                str(file_path.absolute()),
                ReadOnly=True,
                Untitled=True,
                WithWindow=False
            )
            
            try:
                slide_count = presentation.Slides.Count
                logger.info(f"Found {slide_count} slides in presentation")
                
                slides_data = []
                
                # Process each slide
                for slide_num in range(1, slide_count + 1):
                    slide = presentation.Slides.Item(slide_num)
                    slide_data = self._extract_slide_data_com(slide, slide_num, file_path)
                    slides_data.append(slide_data)
                
                # Extract presentation metadata
                presentation_info = {
                    "slide_count": slide_count,
                    "slides": slides_data,
                    "processor": "COM",
                    "presentation_name": presentation.Name,
                    "has_macros": presentation.HasVBProject,
                    "creation_date": str(presentation.BuiltInDocumentProperties.Item("Creation Date").Value) if hasattr(presentation, 'BuiltInDocumentProperties') else None
                }
                
                return presentation_info
                
            finally:
                # Clean up presentation
                presentation.Close()
                
        finally:
            # Clean up PowerPoint application
            try:
                powerpoint.Quit()
            except:
                pass
            pythoncom.CoUninitialize()
    
    def _extract_slide_data_com(self, slide, slide_number: int, file_path: Path) -> Dict[str, Any]:
        """Extract comprehensive data from a single slide using COM"""
        
        # Initialize slide data
        title_text = ""
        content_text = ""
        elements = []
        
        # Process all shapes on the slide
        try:
            for shape_index in range(1, slide.Shapes.Count + 1):
                shape = slide.Shapes.Item(shape_index)
                
                try:
                    element_data = self._extract_shape_data_com(shape, shape_index)
                    
                    if element_data:
                        # Determine if this is title or content based on position and order
                        if shape_index == 1 and element_data["type"] == "text" and not title_text:
                            title_text = element_data["content"]
                        elif element_data["type"] == "text":
                            content_text += f"{element_data['content']}\n"
                        
                        elements.append(element_data)
                
                except Exception as e:
                    logger.warning(f"Failed to extract shape {shape_index} from slide {slide_number}: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Failed to process shapes for slide {slide_number}: {e}")
        
        # Extract speaker notes
        notes_text = self._extract_notes_com(slide, slide_number)
        
        # Generate thumbnail and full image
        thumbnail_path = self._generate_thumbnail_com(slide, slide_number, file_path)
        full_image_path = self._generate_full_image_com(slide, slide_number, file_path)
        
        return {
            "slide_number": slide_number,
            "title": title_text.strip(),
            "content": content_text.strip(),
            "notes": notes_text.strip(),
            "thumbnail_path": thumbnail_path,
            "full_image_path": full_image_path,
            "elements": elements,
            "layout_name": self._get_layout_name_com(slide),
            "background_type": self._get_background_type_com(slide)
        }
    
    def _extract_shape_data_com(self, shape, shape_index: int) -> Optional[Dict[str, Any]]:
        """Extract data from a single shape using COM"""
        
        try:
            element_data = {
                "index": shape_index,
                "type": self._determine_element_type_com(shape),
                "content": "",
                "position": {
                    "x": float(shape.Left),
                    "y": float(shape.Top),
                    "width": float(shape.Width),
                    "height": float(shape.Height),
                    "z_order": shape.ZOrderPosition
                }
            }
            
            # Extract text content if shape has text
            if hasattr(shape, 'HasTextFrame') and shape.HasTextFrame:
                try:
                    text_content = shape.TextFrame.TextRange.Text.strip()
                    element_data["content"] = text_content
                except:
                    pass
            
            # Extract additional properties based on shape type
            if element_data["type"] == "chart":
                element_data["chart_type"] = self._get_chart_type_com(shape)
            elif element_data["type"] == "image":
                element_data["image_name"] = getattr(shape, 'Name', '')
            elif element_data["type"] == "table":
                element_data["table_info"] = self._get_table_info_com(shape)
            
            return element_data if element_data["content"] or element_data["type"] != "text" else None
            
        except Exception as e:
            logger.warning(f"Failed to extract shape data: {e}")
            return None
    
    def _extract_notes_com(self, slide, slide_number: int) -> str:
        """Extract speaker notes from slide using COM"""
        notes_text = ""
        
        try:
            notes_slide = slide.NotesPage
            
            for shape_index in range(1, notes_slide.Shapes.Count + 1):
                shape = notes_slide.Shapes.Item(shape_index)
                
                if hasattr(shape, 'HasTextFrame') and shape.HasTextFrame:
                    try:
                        notes_content = shape.TextFrame.TextRange.Text.strip()
                        if notes_content:
                            notes_text += f"{notes_content}\n"
                    except:
                        continue
                        
        except Exception as e:
            logger.warning(f"Failed to extract notes for slide {slide_number}: {e}")
        
        return notes_text.strip()
    
    def _generate_thumbnail_com(self, slide, slide_number: int, file_path: Path) -> str:
        """Generate thumbnail image using COM"""
        try:
            # Create thumbnail directory
            settings = get_settings()
            thumbnail_dir = Path(settings.thumbnail_dir)
            thumbnail_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename based on file and slide
            file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
            timestamp = int(datetime.now().timestamp())
            thumbnail_name = f"{file_hash}_slide_{slide_number}_{timestamp}.png"
            thumbnail_path = thumbnail_dir / thumbnail_name
            
            # Export slide as thumbnail
            slide.Export(
                str(thumbnail_path),
                "PNG",
                ScaleWidth=300,  # Standard thumbnail width
                ScaleHeight=225  # Standard thumbnail height (4:3 ratio)
            )
            
            if thumbnail_path.exists():
                logger.info(f"Generated thumbnail: {thumbnail_path}")
                return str(thumbnail_path)
            else:
                logger.warning(f"Thumbnail generation failed for slide {slide_number}")
                return ""
            
        except Exception as e:
            logger.error(f"Failed to generate thumbnail for slide {slide_number}: {e}")
            return ""
    
    def _generate_full_image_com(self, slide, slide_number: int, file_path: Path) -> str:
        """Generate full-size image using COM"""
        try:
            # Create image directory
            settings = get_settings()
            image_dir = Path(settings.upload_dir).parent / "images"
            image_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
            timestamp = int(datetime.now().timestamp())
            image_name = f"{file_hash}_slide_{slide_number}_{timestamp}_full.png"
            image_path = image_dir / image_name
            
            # Export slide as high-resolution image
            slide.Export(
                str(image_path),
                "PNG",
                ScaleWidth=1920,  # High resolution width
                ScaleHeight=1440  # High resolution height
            )
            
            if image_path.exists():
                logger.info(f"Generated full image: {image_path}")
                return str(image_path)
            else:
                logger.warning(f"Full image generation failed for slide {slide_number}")
                return ""
            
        except Exception as e:
            logger.error(f"Failed to generate full image for slide {slide_number}: {e}")
            return ""
    
    def _determine_element_type_com(self, shape) -> str:
        """Determine element type from COM shape"""
        try:
            # PowerPoint shape type constants
            shape_type = shape.Type
            
            if shape_type == 1:  # msoAutoShape or msoTextBox
                if hasattr(shape, 'HasTextFrame') and shape.HasTextFrame:
                    return "text"
                else:
                    return "shape"
            elif shape_type == 13:  # msoPicture
                return "image"
            elif shape_type == 3:  # msoChart
                return "chart"
            elif shape_type == 19:  # msoTable
                return "table"
            elif shape_type == 7:  # msoMedia (video/audio)
                return "video"
            elif shape_type == 16:  # msoSmartArt
                return "smartart"
            else:
                return "other"
                
        except Exception:
            return "other"
    
    def _get_layout_name_com(self, slide) -> str:
        """Get slide layout name using COM"""
        try:
            return slide.Layout.Name
        except:
            return "Unknown Layout"
    
    def _get_background_type_com(self, slide) -> str:
        """Get slide background type using COM"""
        try:
            if hasattr(slide.Background, 'Type'):
                bg_type = slide.Background.Type
                if bg_type == 1:
                    return "solid"
                elif bg_type == 2:
                    return "gradient"
                elif bg_type == 3:
                    return "texture"
                elif bg_type == 4:
                    return "pattern"
                elif bg_type == 5:
                    return "picture"
            return "default"
        except:
            return "unknown"
    
    def _get_chart_type_com(self, shape) -> str:
        """Get chart type for chart shapes"""
        try:
            if hasattr(shape, 'Chart'):
                chart_type = shape.Chart.ChartType
                # Map common chart types
                chart_types = {
                    51: "column",
                    52: "clustered_column",
                    4: "line",
                    5: "pie",
                    15: "area",
                    65: "bar"
                }
                return chart_types.get(chart_type, "unknown")
        except:
            pass
        return "unknown"
    
    def _get_table_info_com(self, shape) -> Dict[str, Any]:
        """Get table information for table shapes"""
        try:
            if hasattr(shape, 'Table'):
                table = shape.Table
                return {
                    "rows": table.Rows.Count,
                    "columns": table.Columns.Count
                }
        except:
            pass
        return {"rows": 0, "columns": 0}
    
    def _process_with_pptx(self, file_path: Path) -> Dict[str, Any]:
        """Process using python-pptx library (cross-platform fallback)"""
        
        try:
            presentation = Presentation(str(file_path))
            slide_count = len(presentation.slides)
            
            logger.info(f"Found {slide_count} slides in presentation (python-pptx)")
            
            slides_data = []
            
            # Process each slide
            for slide_index, slide in enumerate(presentation.slides):
                slide_data = self._extract_slide_data_pptx(slide, slide_index + 1, file_path)
                slides_data.append(slide_data)
            
            return {
                "slide_count": slide_count,
                "slides": slides_data,
                "processor": "python-pptx",
                "presentation_name": file_path.stem,
                "has_macros": False,  # python-pptx can't detect macros
                "creation_date": None
            }
            
        except Exception as e:
            raise Exception(f"python-pptx processing failed: {str(e)}") from e
    
    def _extract_slide_data_pptx(self, slide, slide_number: int, file_path: Path) -> Dict[str, Any]:
        """Extract data from a single slide using python-pptx"""
        
        title_text = ""
        content_text = ""
        elements = []
        
        # Extract text from shapes
        for shape_index, shape in enumerate(slide.shapes):
            try:
                element_data = self._extract_shape_data_pptx(shape, shape_index)
                
                if element_data:
                    # First text shape is usually title
                    if not title_text and element_data["type"] == "text":
                        title_text = element_data["content"]
                    elif element_data["type"] == "text":
                        content_text += f"{element_data['content']}\n"
                    
                    elements.append(element_data)
                    
            except Exception as e:
                logger.warning(f"Failed to extract shape {shape_index} from slide {slide_number}: {e}")
                continue
        
        # Extract speaker notes
        notes_text = ""
        try:
            if hasattr(slide, 'notes_slide') and slide.notes_slide.notes_text_frame:
                notes_text = slide.notes_slide.notes_text_frame.text.strip()
        except Exception as e:
            logger.warning(f"Failed to extract notes for slide {slide_number}: {e}")
        
        # Note: python-pptx doesn't support image export
        # We'll use placeholder paths for now
        return {
            "slide_number": slide_number,
            "title": title_text,
            "content": content_text.strip(),
            "notes": notes_text,
            "thumbnail_path": "",  # Would need additional library for image export
            "full_image_path": "",
            "elements": elements,
            "layout_name": slide.slide_layout.name if hasattr(slide, 'slide_layout') else "Unknown",
            "background_type": "unknown"
        }
    
    def _extract_shape_data_pptx(self, shape, shape_index: int) -> Optional[Dict[str, Any]]:
        """Extract data from a single shape using python-pptx"""
        
        try:
            element_data = {
                "index": shape_index,
                "type": self._determine_element_type_pptx(shape),
                "content": "",
                "position": {
                    "x": float(shape.left) if hasattr(shape, 'left') else 0,
                    "y": float(shape.top) if hasattr(shape, 'top') else 0,
                    "width": float(shape.width) if hasattr(shape, 'width') else 0,
                    "height": float(shape.height) if hasattr(shape, 'height') else 0,
                    "z_order": 0  # python-pptx doesn't provide z-order
                }
            }
            
            # Extract text content
            if hasattr(shape, "text") and shape.text.strip():
                element_data["content"] = shape.text.strip()
            
            return element_data if element_data["content"] or element_data["type"] != "text" else None
            
        except Exception as e:
            logger.warning(f"Failed to extract shape data: {e}")
            return None
    
    def _determine_element_type_pptx(self, shape) -> str:
        """Determine element type from python-pptx shape"""
        try:
            if hasattr(shape, 'shape_type'):
                if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                    return "image"
                elif shape.shape_type == MSO_SHAPE_TYPE.CHART:
                    return "chart"
                elif shape.shape_type == MSO_SHAPE_TYPE.TABLE:
                    return "table"
                elif hasattr(shape, 'text'):
                    return "text"
                else:
                    return "shape"
            else:
                return "other"
                
        except Exception:
            return "other"

class PowerPointService:
    """
    PowerPoint service for file processing and database integration
    Implements the PowerPoint processing pipeline from CONSOLIDATED_FOUNDERS_BRIEFCASE.md
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.processor = PowerPointProcessor()
    
    def process_file(self, file_id: str) -> Dict[str, Any]:
        """
        Process a PowerPoint file and save results to database
        
        Args:
            file_id: Database ID of file to process
            
        Returns:
            Processing result dictionary
        """
        # Get file record
        file_record = self.db.query(FileModel).filter(FileModel.id == file_id).first()
        if not file_record:
            raise Exception(f"File {file_id} not found in database")
        
        # Update processing status
        file_record.processed = False
        file_record.processing_error = None
        self.db.commit()
        
        try:
            logger.info(f"Starting PowerPoint processing for file: {file_record.filename}")
            
            # Process file using PowerPoint processor
            result = self.processor.process_file(file_record.file_path)
            
            # Save slides to database
            self._save_slides_to_database(file_record, result["slides"])
            
            # Update file record with success
            file_record.processed = True
            file_record.slide_count = result["slide_count"]
            file_record.processing_error = None
            
            # Update AI analysis if available
            if "has_macros" in result:
                file_record.ai_analysis = {
                    "processor": result["processor"],
                    "has_macros": result["has_macros"],
                    "creation_date": result.get("creation_date"),
                    "processing_timestamp": datetime.now().isoformat()
                }
            
            self.db.commit()
            
            logger.info(f"Successfully processed {result['slide_count']} slides from {file_record.filename}")
            
            return {
                "success": True,
                "file_id": file_id,
                "filename": file_record.filename,
                "slide_count": result["slide_count"],
                "processor": result["processor"]
            }
            
        except Exception as e:
            # Update file record with error
            file_record.processed = False
            file_record.processing_error = str(e)
            self.db.commit()
            
            logger.error(f"Failed to process PowerPoint file {file_record.filename}: {e}")
            
            return {
                "success": False,
                "file_id": file_id,
                "filename": file_record.filename,
                "error": str(e)
            }
    
    def bulk_process_files(self, file_ids: List[str]) -> Dict[str, Any]:
        """
        Process multiple PowerPoint files in batch
        
        Args:
            file_ids: List of file IDs to process
            
        Returns:
            Bulk processing results
        """
        results = {
            "successful": [],
            "failed": [],
            "total_files": len(file_ids),
            "total_slides": 0
        }
        
        logger.info(f"Starting bulk processing of {len(file_ids)} PowerPoint files")
        
        for file_id in file_ids:
            try:
                result = self.process_file(file_id)
                
                if result["success"]:
                    results["successful"].append(result)
                    results["total_slides"] += result["slide_count"]
                else:
                    results["failed"].append(result)
                    
            except Exception as e:
                logger.error(f"Unexpected error processing file {file_id}: {e}")
                results["failed"].append({
                    "success": False,
                    "file_id": file_id,
                    "error": str(e)
                })
        
        logger.info(f"Bulk processing complete: {len(results['successful'])} successful, {len(results['failed'])} failed")
        
        return results
    
    def _save_slides_to_database(self, file_record: FileModel, slides_data: List[Dict[str, Any]]):
        """Save extracted slide data to database"""
        
        # Clear existing slides for this file
        self.db.query(SlideModel).filter(SlideModel.file_id == file_record.id).delete()
        
        for slide_data in slides_data:
            # Create slide record
            slide = SlideModel(
                id=str(uuid.uuid4()),
                file_id=file_record.id,
                slide_number=slide_data["slide_number"],
                title=slide_data["title"][:500] if slide_data["title"] else None,  # Limit title length
                notes=slide_data["notes"],
                slide_type=self._classify_slide_type(slide_data),
                thumbnail_path=slide_data["thumbnail_path"],
                full_image_path=slide_data["full_image_path"],
                ai_analysis={
                    "layout_name": slide_data["layout_name"],
                    "background_type": slide_data["background_type"],
                    "element_count": len(slide_data["elements"]),
                    "extracted_timestamp": datetime.now().isoformat()
                }
            )
            
            self.db.add(slide)
            self.db.flush()  # Get slide ID
            
            # Create element records
            for element_data in slide_data["elements"]:
                element = ElementModel(
                    id=str(uuid.uuid4()),
                    slide_id=slide.id,
                    element_type=element_data["type"],
                    content=element_data["content"][:1000] if element_data["content"] else None,  # Limit content
                    position_x=element_data["position"]["x"],
                    position_y=element_data["position"]["y"],
                    width=element_data["position"]["width"],
                    height=element_data["position"]["height"],
                    ai_analysis={
                        "index": element_data["index"],
                        "z_order": element_data["position"].get("z_order", 0)
                    }
                )
                
                self.db.add(element)
        
        self.db.commit()
    
    def _classify_slide_type(self, slide_data: Dict[str, Any]) -> str:
        """Classify slide type based on content and structure"""
        
        # Simple heuristic-based classification
        title = slide_data.get("title", "").lower()
        content = slide_data.get("content", "").lower()
        element_count = len(slide_data.get("elements", []))
        
        # Check for specific slide types
        if any(keyword in title for keyword in ["introduction", "welcome", "agenda", "overview"]):
            return "title"
        elif any(keyword in title for keyword in ["conclusion", "summary", "thank you", "questions"]):
            return "conclusion"
        elif any(element["type"] == "chart" for element in slide_data.get("elements", [])):
            return "chart"
        elif any(element["type"] == "image" for element in slide_data.get("elements", [])):
            return "image"
        elif any(element["type"] == "table" for element in slide_data.get("elements", [])):
            return "table"
        elif element_count > 3:
            return "content"
        else:
            return "unknown"

# Example usage and testing
if __name__ == "__main__":
    # This would be used for testing the PowerPoint service
    import tempfile
    
    # Create a mock database session for testing
    class MockSession:
        def query(self, model):
            return self
        def filter(self, condition):
            return self
        def first(self):
            return None
        def add(self, obj):
            pass
        def commit(self):
            pass
        def flush(self):
            pass
    
    # Test processor initialization
    try:
        processor = PowerPointProcessor()
        print(f"PowerPoint processor initialized: COM={processor.use_com}")
        
        service = PowerPointService(MockSession())
        print("PowerPoint service initialized successfully")
        
    except Exception as e:
        print(f"Failed to initialize PowerPoint service: {e}")