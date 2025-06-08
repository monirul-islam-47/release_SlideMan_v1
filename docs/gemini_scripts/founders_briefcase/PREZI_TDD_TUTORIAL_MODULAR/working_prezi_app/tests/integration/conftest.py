"""
Integration Test Configuration for PrezI
Comprehensive test setup with mocks and fixtures
Based on CONSOLIDATED_FOUNDERS_BRIEFCASE.md specifications
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator, Generator, Dict, Any

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Test Database Configuration
TEST_DATABASE_URL = "sqlite:///./test_prezi_integration.db"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine for the session."""
    # Import here to avoid circular imports
    from services.database import Base
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    yield test_engine
    
    # Drop all tables after session
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def test_db_session(test_db_engine):
    """Create a fresh database session for each test."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture
def test_client(test_db_session):
    """Create FastAPI test client with test database."""
    from main import app
    from services.database import get_db
    
    def override_get_db():
        yield test_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for AI service testing."""
    with patch('openai.AsyncOpenAI') as mock_client:
        # Mock successful content analysis response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "topic": "Financial Performance Analysis",
            "summary": "Comprehensive analysis of quarterly financial performance showing strong growth metrics",
            "key_insights": [
                "Revenue increased by 15% quarter-over-quarter",
                "Profit margins improved from 12% to 14%",
                "Customer acquisition cost decreased by 8%",
                "Market share expanded in key segments"
            ],
            "confidence_score": 0.92,
            "slide_type": "chart",
            "content_classification": "financial_data",
            "presentation_context": "executive_summary"
        })
        
        # Mock keyword suggestion response
        mock_keyword_response = MagicMock()
        mock_keyword_response.choices = [MagicMock()]
        mock_keyword_response.choices[0].message.content = json.dumps([
            {
                "keyword": "revenue growth",
                "confidence": 0.95,
                "category": "financial_metrics"
            },
            {
                "keyword": "profit margin",
                "confidence": 0.88,
                "category": "financial_metrics"
            },
            {
                "keyword": "market expansion",
                "confidence": 0.82,
                "category": "business_strategy"
            }
        ])
        
        # Mock query interpretation response
        mock_query_response = MagicMock()
        mock_query_response.choices = [MagicMock()]
        mock_query_response.choices[0].message.content = json.dumps({
            "search_intent": "find_financial_charts",
            "topics": ["revenue", "financial performance", "charts"],
            "keywords": ["revenue", "growth", "analysis", "charts"],
            "content_types": ["chart", "table"],
            "confidence": 0.89,
            "filters": {
                "slide_types": ["chart"],
                "content_categories": ["financial"]
            }
        })
        
        # Configure mock responses based on request content
        async def mock_create_completion(*args, **kwargs):
            messages = kwargs.get('messages', [])
            if not messages:
                return mock_response
            
            last_message = messages[-1]['content'].lower()
            
            if 'suggest keywords' in last_message or 'keyword suggestions' in last_message:
                return mock_keyword_response
            elif 'interpret query' in last_message or 'search intent' in last_message:
                return mock_query_response
            else:
                return mock_response
        
        mock_client.return_value.chat.completions.create = AsyncMock(
            side_effect=mock_create_completion
        )
        
        yield mock_client.return_value

@pytest.fixture
def mock_powerpoint_service():
    """Mock PowerPoint service for testing without COM dependencies."""
    with patch('services.powerpoint_service.PowerPointService') as MockPowerPointService:
        
        # Create mock instance
        mock_instance = MagicMock()
        mock_instance.is_available = True
        mock_instance.has_com_support = True
        
        # Mock successful slide extraction
        async def mock_extract_slides(file_path: str, project_id: str):
            return {
                'success': True,
                'slides_extracted': 5,
                'file_id': f'file_{hash(file_path)}',
                'processing_time_ms': 2500,
                'slides': [
                    {
                        'slide_number': 1,
                        'title': 'Executive Summary',
                        'content': 'Quarterly performance overview and key achievements',
                        'slide_type': 'title',
                        'thumbnail_path': f'/thumbnails/{project_id}_slide_1.png',
                        'full_image_path': f'/images/{project_id}_slide_1_full.png',
                        'notes': 'Speaker notes for executive summary',
                        'elements': [
                            {
                                'element_type': 'text',
                                'content': 'Executive Summary',
                                'position_x': 100,
                                'position_y': 50,
                                'width': 400,
                                'height': 60
                            }
                        ]
                    },
                    {
                        'slide_number': 2,
                        'title': 'Revenue Growth Analysis',
                        'content': 'Q3 revenue increased by 15% showing strong market performance',
                        'slide_type': 'chart',
                        'thumbnail_path': f'/thumbnails/{project_id}_slide_2.png',
                        'full_image_path': f'/images/{project_id}_slide_2_full.png',
                        'notes': 'Discuss revenue drivers and market factors',
                        'elements': [
                            {
                                'element_type': 'chart',
                                'content': 'Revenue growth chart showing Q3 performance',
                                'position_x': 50,
                                'position_y': 100,
                                'width': 600,
                                'height': 400
                            }
                        ]
                    },
                    {
                        'slide_number': 3,
                        'title': 'Market Expansion Strategy',
                        'content': 'Strategic initiatives for expanding into new markets',
                        'slide_type': 'text',
                        'thumbnail_path': f'/thumbnails/{project_id}_slide_3.png',
                        'full_image_path': f'/images/{project_id}_slide_3_full.png',
                        'notes': 'Focus on European and Asian markets',
                        'elements': [
                            {
                                'element_type': 'text',
                                'content': 'Market expansion opportunities and strategic roadmap',
                                'position_x': 75,
                                'position_y': 120,
                                'width': 550,
                                'height': 300
                            }
                        ]
                    },
                    {
                        'slide_number': 4,
                        'title': 'Customer Satisfaction Metrics',
                        'content': 'Customer satisfaction scores and feedback analysis',
                        'slide_type': 'table',
                        'thumbnail_path': f'/thumbnails/{project_id}_slide_4.png',
                        'full_image_path': f'/images/{project_id}_slide_4_full.png',
                        'notes': 'Highlight improvement in customer satisfaction',
                        'elements': [
                            {
                                'element_type': 'table',
                                'content': 'Customer satisfaction data table',
                                'position_x': 100,
                                'position_y': 150,
                                'width': 500,
                                'height': 250
                            }
                        ]
                    },
                    {
                        'slide_number': 5,
                        'title': 'Next Quarter Objectives',
                        'content': 'Strategic objectives and goals for Q4',
                        'slide_type': 'conclusion',
                        'thumbnail_path': f'/thumbnails/{project_id}_slide_5.png',
                        'full_image_path': f'/images/{project_id}_slide_5_full.png',
                        'notes': 'Emphasize key objectives and timeline',
                        'elements': [
                            {
                                'element_type': 'text',
                                'content': 'Q4 objectives and success metrics',
                                'position_x': 80,
                                'position_y': 100,
                                'width': 540,
                                'height': 350
                            }
                        ]
                    }
                ]
            }
        
        # Mock file processing status
        async def mock_get_processing_status(file_id: str):
            return {
                'status': 'completed',
                'progress': 100,
                'slides_processed': 5,
                'total_slides': 5,
                'processing_time_ms': 2500,
                'thumbnail_generation_complete': True
            }
        
        # Mock export functionality
        async def mock_export_to_powerpoint(slides: list, output_path: str, template_id: str = None):
            return {
                'success': True,
                'file_path': output_path,
                'slide_count': len(slides),
                'export_time_ms': 1200,
                'file_size_mb': 2.4
            }
        
        # Assign mock methods
        mock_instance.extract_slides_from_file = mock_extract_slides
        mock_instance.get_processing_status = mock_get_processing_status
        mock_instance.export_to_powerpoint = mock_export_to_powerpoint
        
        # Configure the mock class to return our instance
        MockPowerPointService.return_value = mock_instance
        
        yield mock_instance

@pytest.fixture
def sample_test_data():
    """Provide comprehensive sample data for testing."""
    return {
        'projects': [
            {
                'id': 'proj_001',
                'name': 'Q3 Financial Review',
                'description': 'Quarterly financial performance analysis and strategic planning',
                'created_at': '2024-01-15T10:00:00Z',
                'slide_count': 15,
                'file_count': 3
            },
            {
                'id': 'proj_002', 
                'name': 'Market Research Analysis',
                'description': 'Comprehensive market research and competitive analysis',
                'created_at': '2024-01-20T14:30:00Z',
                'slide_count': 22,
                'file_count': 2
            }
        ],
        'slides': [
            {
                'id': 'slide_001',
                'title': 'Revenue Analysis Q3',
                'content_preview': 'Quarterly revenue analysis showing 15% growth with strong performance across all segments',
                'slide_type': 'chart',
                'project_id': 'proj_001',
                'project_name': 'Q3 Financial Review',
                'keywords': ['revenue', 'growth', 'analysis', 'quarterly', 'performance'],
                'thumbnail_path': '/thumbnails/proj_001_slide_001.png',
                'full_image_path': '/images/proj_001_slide_001_full.png',
                'relevance_score': 0.92,
                'ai_analysis': {
                    'ai_topic': 'Financial Performance',
                    'ai_summary': 'Revenue growth analysis with detailed breakdown',
                    'ai_confidence_score': 0.88,
                    'key_insights': ['Strong growth', 'Market expansion', 'Cost optimization']
                }
            },
            {
                'id': 'slide_002',
                'title': 'Customer Satisfaction Survey Results',
                'content_preview': 'Customer satisfaction scores improved to 4.2/5 with significant improvements in service quality',
                'slide_type': 'table',
                'project_id': 'proj_001',
                'project_name': 'Q3 Financial Review',
                'keywords': ['customer', 'satisfaction', 'survey', 'quality', 'service'],
                'thumbnail_path': '/thumbnails/proj_001_slide_002.png',
                'full_image_path': '/images/proj_001_slide_002_full.png',
                'relevance_score': 0.85,
                'ai_analysis': {
                    'ai_topic': 'Customer Experience',
                    'ai_summary': 'Customer satisfaction metrics and improvement areas',
                    'ai_confidence_score': 0.91,
                    'key_insights': ['Satisfaction increase', 'Service improvements', 'Response rate growth']
                }
            },
            {
                'id': 'slide_003',
                'title': 'Market Expansion Strategy',
                'content_preview': 'Strategic roadmap for expanding into European and Asian markets with timeline and resources',
                'slide_type': 'text',
                'project_id': 'proj_002',
                'project_name': 'Market Research Analysis',
                'keywords': ['market', 'expansion', 'strategy', 'international', 'growth'],
                'thumbnail_path': '/thumbnails/proj_002_slide_003.png',
                'full_image_path': '/images/proj_002_slide_003_full.png',
                'relevance_score': 0.89,
                'ai_analysis': {
                    'ai_topic': 'Business Strategy',
                    'ai_summary': 'Market expansion opportunities and strategic planning',
                    'ai_confidence_score': 0.86,
                    'key_insights': ['International opportunities', 'Resource requirements', 'Timeline planning']
                }
            }
        ],
        'assemblies': [
            {
                'id': 'assembly_001',
                'name': 'Executive Summary Presentation',
                'description': 'Executive-level presentation covering key performance metrics and strategic initiatives',
                'project_id': 'proj_001',
                'ai_generated': True,
                'slides': [
                    {
                        'slide_id': 'slide_001',
                        'position': 1,
                        'title': 'Revenue Analysis Q3',
                        'ai_suggested': True,
                        'rationale': 'Strong financial performance data essential for executive overview'
                    },
                    {
                        'slide_id': 'slide_002',
                        'position': 2,
                        'title': 'Customer Satisfaction Survey Results',
                        'ai_suggested': True,
                        'rationale': 'Customer metrics complement financial performance narrative'
                    }
                ],
                'ai_plan': {
                    'intent': 'Create executive summary focusing on performance and growth',
                    'target_audience': 'Executive leadership team',
                    'estimated_duration': 15,
                    'success_metrics': ['Clear performance overview', 'Strategic alignment', 'Data-driven insights']
                }
            }
        ],
        'search_scenarios': [
            {
                'query': 'revenue growth charts',
                'expected_results': ['slide_001'],
                'search_type': 'natural'
            },
            {
                'query': 'customer satisfaction data',
                'expected_results': ['slide_002'],
                'search_type': 'natural'
            },
            {
                'query': 'strategic planning market expansion',
                'expected_results': ['slide_003'],
                'search_type': 'semantic'
            }
        ]
    }

@pytest.fixture
def temp_files():
    """Provide temporary files for testing file uploads."""
    temp_files = []
    
    def create_temp_file(content: bytes, suffix: str = '.pptx'):
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        temp_file.write(content)
        temp_file.close()
        temp_files.append(temp_file.name)
        return temp_file.name
    
    yield create_temp_file
    
    # Cleanup
    for file_path in temp_files:
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception:
            pass

@pytest.fixture
def mock_file_storage():
    """Mock file storage system for testing."""
    stored_files = {}
    
    class MockFileStorage:
        def save_file(self, file_path: str, content: bytes) -> str:
            stored_files[file_path] = content
            return file_path
        
        def get_file(self, file_path: str) -> bytes:
            return stored_files.get(file_path, b'')
        
        def delete_file(self, file_path: str) -> bool:
            return stored_files.pop(file_path, None) is not None
        
        def file_exists(self, file_path: str) -> bool:
            return file_path in stored_files
    
    yield MockFileStorage()

@pytest.fixture
def performance_monitor():
    """Monitor performance metrics during tests."""
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_times = {}
            self.metrics = {}
        
        def start_timer(self, operation: str):
            self.start_times[operation] = time.time()
        
        def end_timer(self, operation: str) -> float:
            if operation in self.start_times:
                duration = time.time() - self.start_times[operation]
                self.metrics[operation] = duration
                return duration
            return 0.0
        
        def get_metrics(self) -> Dict[str, float]:
            return self.metrics.copy()
        
        def assert_performance(self, operation: str, max_duration: float):
            actual_duration = self.metrics.get(operation, 0)
            assert actual_duration <= max_duration, \
                f"Operation '{operation}' took {actual_duration:.3f}s, expected <= {max_duration}s"
    
    yield PerformanceMonitor()

@pytest.fixture
def api_response_validator():
    """Validate API response formats and content."""
    
    class APIResponseValidator:
        def validate_search_response(self, response_data: dict):
            """Validate search API response format."""
            required_fields = ['success', 'query', 'results', 'total_results', 'search_strategy']
            for field in required_fields:
                assert field in response_data, f"Missing required field: {field}"
            
            assert isinstance(response_data['success'], bool)
            assert isinstance(response_data['results'], list)
            assert isinstance(response_data['total_results'], int)
            
            # Validate individual slide results
            for slide in response_data['results']:
                self.validate_slide_data(slide)
        
        def validate_slide_data(self, slide_data: dict):
            """Validate slide data format."""
            required_fields = ['id', 'title', 'content_preview', 'slide_type', 'project_id']
            for field in required_fields:
                assert field in slide_data, f"Missing required slide field: {field}"
            
            assert isinstance(slide_data['keywords'], list)
            if 'relevance_score' in slide_data:
                assert 0 <= slide_data['relevance_score'] <= 1
        
        def validate_assembly_data(self, assembly_data: dict):
            """Validate assembly data format."""
            required_fields = ['id', 'name', 'project_id', 'slides']
            for field in required_fields:
                assert field in assembly_data, f"Missing required assembly field: {field}"
            
            assert isinstance(assembly_data['slides'], list)
            assert isinstance(assembly_data['ai_generated'], bool)
        
        def validate_ai_analysis(self, analysis_data: dict):
            """Validate AI analysis response format."""
            if analysis_data.get('success'):
                analysis = analysis_data.get('analysis', {})
                required_fields = ['topic', 'summary', 'confidence_score']
                for field in required_fields:
                    assert field in analysis, f"Missing required analysis field: {field}"
                
                assert 0 <= analysis['confidence_score'] <= 1
    
    yield APIResponseValidator()

# Test utilities
class DatabaseTestUtils:
    """Utilities for database testing."""
    
    @staticmethod
    def create_test_project(session, project_data: dict):
        """Create a test project in the database."""
        from models.database_models import Project
        
        project = Project(
            name=project_data['name'],
            description=project_data.get('description', ''),
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        return project
    
    @staticmethod
    def create_test_slide(session, slide_data: dict):
        """Create a test slide in the database."""
        from models.database_models import Slide
        
        slide = Slide(
            title=slide_data['title'],
            content_preview=slide_data['content_preview'],
            slide_type=slide_data['slide_type'],
            project_id=slide_data['project_id'],
            slide_number=slide_data.get('slide_number', 1),
            thumbnail_path=slide_data.get('thumbnail_path'),
            full_image_path=slide_data.get('full_image_path')
        )
        session.add(slide)
        session.commit()
        session.refresh(slide)
        return slide

@pytest.fixture
def db_test_utils():
    """Provide database testing utilities."""
    return DatabaseTestUtils()

# Async test utilities
@pytest.fixture
def async_test_utils():
    """Utilities for async testing."""
    
    class AsyncTestUtils:
        @staticmethod
        async def wait_for_condition(condition_func, timeout: float = 10.0, interval: float = 0.1):
            """Wait for a condition to become true."""
            import asyncio
            
            start_time = asyncio.get_event_loop().time()
            while True:
                if await condition_func():
                    return True
                
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise TimeoutError(f"Condition not met within {timeout} seconds")
                
                await asyncio.sleep(interval)
        
        @staticmethod
        async def run_concurrent_tasks(tasks: list, max_concurrency: int = 10):
            """Run tasks with controlled concurrency."""
            import asyncio
            
            semaphore = asyncio.Semaphore(max_concurrency)
            
            async def run_with_semaphore(task):
                async with semaphore:
                    return await task
            
            return await asyncio.gather(*[run_with_semaphore(task) for task in tasks])
    
    yield AsyncTestUtils()