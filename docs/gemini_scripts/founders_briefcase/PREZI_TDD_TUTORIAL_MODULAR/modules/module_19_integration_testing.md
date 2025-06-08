# Module 19: Integration & Testing

## Learning Objectives
In this module, you'll learn how to:
- Design comprehensive integration tests for the complete PrezI system
- Test end-to-end workflows from file upload to presentation assembly
- Validate AI service integrations and error handling
- Implement performance testing for critical operations
- Create automated testing pipelines that ensure system reliability

## Prerequisites
- Completed Modules 14-18 (PowerPoint, AI, Search, Assembly, Frontend services)
- Understanding of pytest, FastAPI testing, and React Testing Library
- Knowledge of async testing patterns and mocking strategies
- Basic understanding of system integration concepts

## Introduction to Integration Testing

Integration testing validates that different components of our system work together correctly. Unlike unit tests that test individual functions, integration tests verify entire workflows and service interactions.

### Why Integration Testing Matters for PrezI

Our AI-powered presentation system has complex dependencies:
- PowerPoint file processing with COM automation
- OpenAI API integration for content analysis
- Database operations with full-text search
- Frontend-backend communication
- File upload and export workflows

Integration tests ensure these components work together seamlessly, catching issues that unit tests might miss.

## Test Architecture Design

### Testing Pyramid for PrezI

```python
# test_architecture.py
"""
PrezI Testing Strategy

1. Unit Tests (60%): Individual functions and classes
2. Integration Tests (30%): Service interactions and workflows  
3. End-to-End Tests (10%): Complete user journeys

Integration Test Categories:
- Service Integration: API endpoints with database
- External Service Integration: OpenAI, PowerPoint COM
- Frontend Integration: React components with API
- Workflow Integration: Complete user workflows
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test Database Setup
TEST_DATABASE_URL = "sqlite:///./test_prezi.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine for the session."""
    from services.database import Base
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def test_db_session(test_db_engine):
    """Create a database session for each test."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    
    yield session
    
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
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()
```

### Mock Strategy for External Services

```python
# conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import openai
from services.powerpoint_service import PowerPointService
from services.ai_service import AIService

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for AI service testing."""
    with patch('openai.AsyncOpenAI') as mock_client:
        # Mock successful content analysis
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """{
            "topic": "Financial Analysis",
            "summary": "Quarterly revenue analysis showing 15% growth",
            "key_insights": ["Revenue increased", "Profit margins improved"],
            "confidence_score": 0.85,
            "slide_type": "chart"
        }"""
        
        mock_client.return_value.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        yield mock_client.return_value

@pytest.fixture
def mock_powerpoint_service():
    """Mock PowerPoint service for testing without COM."""
    with patch.object(PowerPointService, '_initialize_powerpoint') as mock_init:
        mock_init.return_value = True
        
        service = PowerPointService()
        service.is_available = True
        service.application = MagicMock()
        
        # Mock successful slide extraction
        async def mock_extract_slides(file_path, project_id):
            return {
                'success': True,
                'slides_extracted': 5,
                'slides': [
                    {
                        'slide_number': 1,
                        'title': 'Test Slide 1',
                        'content': 'Sample content',
                        'slide_type': 'title',
                        'thumbnail_path': '/mock/thumb1.png'
                    }
                ]
            }
        
        service.extract_slides_from_file = mock_extract_slides
        yield service

@pytest.fixture
def sample_test_data():
    """Provide sample data for testing."""
    return {
        'projects': [
            {
                'id': 'proj_001',
                'name': 'Test Project',
                'description': 'Integration test project'
            }
        ],
        'slides': [
            {
                'id': 'slide_001',
                'title': 'Revenue Analysis Q3',
                'content_preview': 'Quarterly revenue showing strong growth',
                'slide_type': 'chart',
                'project_id': 'proj_001',
                'keywords': ['revenue', 'growth', 'analysis']
            }
        ],
        'assemblies': [
            {
                'id': 'assembly_001',
                'name': 'Executive Summary',
                'project_id': 'proj_001',
                'slides': [
                    {
                        'slide_id': 'slide_001',
                        'position': 1,
                        'title': 'Revenue Analysis Q3'
                    }
                ]
            }
        ]
    }
```

## Service Integration Tests

### PowerPoint Service Integration

```python
# tests/integration/test_powerpoint_integration.py
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from services.powerpoint_service import PowerPointService
from services.database_service import DatabaseService

class TestPowerPointIntegration:
    """Test PowerPoint service integration with database."""
    
    @pytest.mark.asyncio
    async def test_file_upload_and_processing_workflow(
        self, 
        test_db_session, 
        mock_powerpoint_service,
        sample_test_data
    ):
        """Test complete file upload and processing workflow."""
        # Create test project
        db_service = DatabaseService(test_db_session)
        project = await db_service.create_project(
            name="Integration Test Project",
            description="Test project for integration testing"
        )
        
        # Create temporary PowerPoint file (mock)
        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as tmp_file:
            tmp_file.write(b'Mock PowerPoint content')
            file_path = tmp_file.name
        
        try:
            # Test file processing
            result = await mock_powerpoint_service.extract_slides_from_file(
                file_path, project['id']
            )
            
            assert result['success'] is True
            assert result['slides_extracted'] == 5
            assert len(result['slides']) == 1
            
            # Verify slide data structure
            slide = result['slides'][0]
            assert 'slide_number' in slide
            assert 'title' in slide
            assert 'content' in slide
            assert 'slide_type' in slide
            assert 'thumbnail_path' in slide
            
            # Test database storage
            for slide_data in result['slides']:
                db_slide = await db_service.create_slide(
                    project_id=project['id'],
                    slide_number=slide_data['slide_number'],
                    title=slide_data['title'],
                    content=slide_data['content'],
                    slide_type=slide_data['slide_type'],
                    thumbnail_path=slide_data['thumbnail_path']
                )
                
                assert db_slide is not None
                assert db_slide['title'] == slide_data['title']
        
        finally:
            Path(file_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_powerpoint_error_handling(
        self, 
        mock_powerpoint_service
    ):
        """Test PowerPoint service error handling."""
        # Test with non-existent file
        result = await mock_powerpoint_service.extract_slides_from_file(
            "/nonexistent/file.pptx", "proj_001"
        )
        
        # Should use fallback processing
        assert 'error' in result or result.get('fallback_used') is True
    
    @pytest.mark.asyncio
    async def test_concurrent_file_processing(
        self,
        mock_powerpoint_service,
        sample_test_data
    ):
        """Test concurrent file processing capabilities."""
        # Create multiple mock files
        tasks = []
        for i in range(3):
            task = mock_powerpoint_service.extract_slides_from_file(
                f"/mock/file_{i}.pptx", "proj_001"
            )
            tasks.append(task)
        
        # Process concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all processed successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert result['success'] is True
```

### AI Service Integration

```python
# tests/integration/test_ai_integration.py
import pytest
from services.ai_service import AIService
from services.database_service import DatabaseService

class TestAIIntegration:
    """Test AI service integration with content analysis."""
    
    @pytest.mark.asyncio
    async def test_content_analysis_workflow(
        self,
        test_db_session,
        mock_openai_client,
        sample_test_data
    ):
        """Test complete content analysis workflow."""
        db_service = DatabaseService(test_db_session)
        ai_service = AIService()
        
        # Create test slide
        slide_data = sample_test_data['slides'][0]
        slide = await db_service.create_slide(
            project_id=slide_data['project_id'],
            slide_number=1,
            title=slide_data['title'],
            content=slide_data['content_preview'],
            slide_type=slide_data['slide_type']
        )
        
        # Test AI analysis
        analysis_result = await ai_service.analyze_slide_content(
            slide_id=slide['id'],
            content=slide['content'],
            slide_type=slide['slide_type']
        )
        
        assert analysis_result['success'] is True
        assert 'analysis' in analysis_result
        
        analysis = analysis_result['analysis']
        assert 'topic' in analysis
        assert 'summary' in analysis
        assert 'key_insights' in analysis
        assert 'confidence_score' in analysis
        assert isinstance(analysis['confidence_score'], float)
        assert 0 <= analysis['confidence_score'] <= 1
        
        # Test keyword suggestion integration
        keyword_result = await ai_service.suggest_keywords(
            content=slide['content'],
            context='presentation'
        )
        
        assert isinstance(keyword_result, list)
        for keyword in keyword_result:
            assert 'keyword' in keyword
            assert 'confidence' in keyword
            assert 'category' in keyword
    
    @pytest.mark.asyncio
    async def test_ai_fallback_mechanisms(
        self,
        test_db_session
    ):
        """Test AI service fallback when OpenAI is unavailable."""
        ai_service = AIService()
        
        # Mock OpenAI failure
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_client.side_effect = Exception("OpenAI API unavailable")
            
            result = await ai_service.analyze_slide_content(
                slide_id="test_slide",
                content="Sample slide content",
                slide_type="text"
            )
            
            # Should fall back to rule-based analysis
            assert result['success'] is True
            assert result.get('fallback_analysis') is not None
            assert 'error' not in result
    
    @pytest.mark.asyncio
    async def test_ai_rate_limiting(
        self,
        mock_openai_client
    ):
        """Test AI service rate limiting and retry logic."""
        ai_service = AIService()
        
        # Test multiple rapid requests
        tasks = []
        for i in range(10):
            task = ai_service.analyze_slide_content(
                slide_id=f"slide_{i}",
                content=f"Test content {i}",
                slide_type="text"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed (with rate limiting handled internally)
        for result in results:
            assert not isinstance(result, Exception)
            assert result['success'] is True
```

### Search Service Integration

```python
# tests/integration/test_search_integration.py
import pytest
from services.search_service import SearchService
from services.database_service import DatabaseService

class TestSearchIntegration:
    """Test search service integration with database and AI."""
    
    @pytest.mark.asyncio
    async def test_natural_language_search_workflow(
        self,
        test_db_session,
        mock_openai_client,
        sample_test_data
    ):
        """Test complete natural language search workflow."""
        db_service = DatabaseService(test_db_session)
        search_service = SearchService(db_service)
        
        # Setup test data
        project = await db_service.create_project(
            name="Search Test Project",
            description="Project for search testing"
        )
        
        # Create test slides with varied content
        test_slides = [
            {
                'title': 'Revenue Growth Analysis',
                'content': 'Q3 revenue increased by 15% compared to previous quarter',
                'slide_type': 'chart',
                'keywords': ['revenue', 'growth', 'analysis']
            },
            {
                'title': 'Customer Satisfaction Survey',
                'content': 'Customer satisfaction scores improved to 4.2/5',
                'slide_type': 'table',
                'keywords': ['customer', 'satisfaction', 'survey']
            },
            {
                'title': 'Market Expansion Strategy',
                'content': 'Plans for expanding into European markets',
                'slide_type': 'text',
                'keywords': ['market', 'expansion', 'strategy']
            }
        ]
        
        created_slides = []
        for i, slide_data in enumerate(test_slides):
            slide = await db_service.create_slide(
                project_id=project['id'],
                slide_number=i + 1,
                title=slide_data['title'],
                content=slide_data['content'],
                slide_type=slide_data['slide_type']
            )
            
            # Add keywords
            for keyword in slide_data['keywords']:
                await db_service.add_keyword_to_slide(slide['id'], keyword)
            
            created_slides.append(slide)
        
        # Test natural language search
        search_result = await search_service.natural_language_search(
            query="Show me charts about revenue performance",
            project_id=project['id']
        )
        
        assert search_result['success'] is True
        assert search_result['total_results'] > 0
        assert 'query_interpretation' in search_result
        
        # Verify AI interpretation
        interpretation = search_result['query_interpretation']
        assert 'search_intent' in interpretation
        assert 'topics' in interpretation
        assert 'content_types' in interpretation
        assert 'chart' in interpretation['content_types']
        
        # Verify search results relevance
        results = search_result['results']
        revenue_slide_found = any(
            'revenue' in slide['title'].lower() or 'revenue' in slide['content_preview'].lower()
            for slide in results
        )
        assert revenue_slide_found
    
    @pytest.mark.asyncio
    async def test_cross_project_search(
        self,
        test_db_session,
        sample_test_data
    ):
        """Test cross-project search functionality."""
        db_service = DatabaseService(test_db_session)
        search_service = SearchService(db_service)
        
        # Create multiple projects with slides
        projects = []
        for i in range(2):
            project = await db_service.create_project(
                name=f"Project {i+1}",
                description=f"Test project {i+1}"
            )
            projects.append(project)
            
            # Add slides to each project
            slide = await db_service.create_slide(
                project_id=project['id'],
                slide_number=1,
                title=f"Financial Report Project {i+1}",
                content=f"Financial data for project {i+1}",
                slide_type='chart'
            )
            await db_service.add_keyword_to_slide(slide['id'], 'financial')
        
        # Test cross-project search
        search_filter = {
            'query': 'financial',
            'search_scope': 'all_projects',
            'content_types': ['chart'],
            'sort_by': 'relevance',
            'sort_order': 'desc',
            'limit': 50,
            'offset': 0
        }
        
        result = await search_service.advanced_search(search_filter)
        
        assert result['success'] is True
        assert result['total_results'] == 2  # Should find slides from both projects
        
        # Verify slides from different projects are returned
        project_ids = set(slide['project_id'] for slide in result['results'])
        assert len(project_ids) == 2
    
    @pytest.mark.asyncio
    async def test_semantic_search_integration(
        self,
        test_db_session,
        mock_openai_client
    ):
        """Test semantic search with AI embeddings."""
        db_service = DatabaseService(test_db_session)
        search_service = SearchService(db_service)
        
        # Test semantic search
        result = await search_service.semantic_search(
            query="revenue performance metrics",
            use_ai_embeddings=True
        )
        
        assert result['search_strategy'] == 'ai_semantic'
        # With mock data, we expect the search to handle gracefully
        assert 'error' not in result or result['success'] is True
```

## End-to-End Workflow Tests

### Complete User Journey Tests

```python
# tests/integration/test_e2e_workflows.py
import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

class TestEndToEndWorkflows:
    """Test complete user workflows from start to finish."""
    
    def test_complete_presentation_creation_workflow(
        self,
        test_client,
        mock_powerpoint_service,
        mock_openai_client,
        sample_test_data
    ):
        """Test complete workflow: upload file -> analyze -> search -> assemble -> export."""
        
        # Step 1: Create project
        project_response = test_client.post("/api/projects", json={
            "name": "E2E Test Project",
            "description": "End-to-end testing project"
        })
        assert project_response.status_code == 200
        project_data = project_response.json()
        project_id = project_data['project']['id']
        
        # Step 2: Upload PowerPoint file
        with tempfile.NamedTemporaryFile(suffix='.pptx') as tmp_file:
            tmp_file.write(b'Mock PowerPoint content')
            tmp_file.seek(0)
            
            upload_response = test_client.post(
                "/api/files/upload",
                files={"file": ("test.pptx", tmp_file, "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
                data={"project_id": project_id}
            )
            assert upload_response.status_code == 200
            upload_data = upload_response.json()
            assert upload_data['success'] is True
        
        # Step 3: Wait for processing and get slides
        slides_response = test_client.get(f"/api/projects/{project_id}/slides")
        assert slides_response.status_code == 200
        slides_data = slides_response.json()
        assert len(slides_data) > 0
        
        slide_id = slides_data[0]['id']
        
        # Step 4: Analyze slides with AI
        analysis_response = test_client.post(f"/api/slides/{slide_id}/analyze")
        assert analysis_response.status_code == 200
        analysis_data = analysis_response.json()
        assert analysis_data['success'] is True
        
        # Step 5: Search for slides
        search_response = test_client.post("/api/search/natural-language", json={
            "query": "revenue analysis charts",
            "project_id": project_id
        })
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data['success'] is True
        
        # Step 6: Create assembly
        assembly_response = test_client.post("/api/assembly/manual", json={
            "name": "Test Assembly",
            "slides": [{"slide_id": slide_id, "title": "Test Slide"}],
            "project_id": project_id,
            "optimize_order": True
        })
        assert assembly_response.status_code == 200
        assembly_data = assembly_response.json()
        assert assembly_data['success'] is True
        assembly_id = assembly_data['assembly']['id']
        
        # Step 7: Export assembly
        export_response = test_client.post(f"/api/assembly/{assembly_id}/export", json={
            "format": "pptx",
            "options": {"include_notes": True}
        })
        assert export_response.status_code == 200
        export_data = export_response.json()
        assert export_data['success'] is True
        assert 'file_path' in export_data
    
    def test_ai_automated_assembly_workflow(
        self,
        test_client,
        mock_openai_client,
        sample_test_data
    ):
        """Test AI-automated presentation creation workflow."""
        
        # Create project with slides
        project_response = test_client.post("/api/projects", json={
            "name": "AI Assembly Test",
            "description": "Test AI-automated assembly"
        })
        project_data = project_response.json()
        project_id = project_data['project']['id']
        
        # Create sample slides
        for slide_data in sample_test_data['slides']:
            slide_response = test_client.post("/api/slides", json={
                **slide_data,
                "project_id": project_id
            })
            assert slide_response.status_code == 200
        
        # Test AI-automated assembly creation
        ai_assembly_response = test_client.post("/api/assembly/ai-automated", json={
            "intent": "Create an executive summary presentation focusing on financial performance and growth metrics",
            "project_id": project_id,
            "user_preferences": {
                "duration": 10,
                "style": "professional",
                "include_notes": True
            }
        })
        
        assert ai_assembly_response.status_code == 200
        ai_data = ai_assembly_response.json()
        assert ai_data['success'] is True
        assert 'assembly_plan' in ai_data
        assert 'recommendations' in ai_data
        
        assembly_plan = ai_data['assembly_plan']
        assert assembly_plan['ai_generated'] is True
        assert len(assembly_plan['slides']) > 0
    
    def test_collaboration_workflow(
        self,
        test_client,
        sample_test_data
    ):
        """Test real-time collaboration workflow."""
        
        # Create assembly for collaboration
        project_response = test_client.post("/api/projects", json={
            "name": "Collaboration Test",
            "description": "Test collaboration features"
        })
        project_data = project_response.json()
        project_id = project_data['project']['id']
        
        assembly_response = test_client.post("/api/assembly/manual", json={
            "name": "Collaborative Assembly",
            "slides": [],
            "project_id": project_id
        })
        assembly_data = assembly_response.json()
        assembly_id = assembly_data['assembly']['id']
        
        # Create collaboration session
        collab_response = test_client.post("/api/assembly/collaboration/session", json={
            "assembly_id": assembly_id,
            "owner_id": "user_001",
            "participants": ["user_002", "user_003"]
        })
        
        assert collab_response.status_code == 200
        collab_data = collab_response.json()
        session_id = collab_data['session_id']
        
        # Test collaboration update
        update_response = test_client.post("/api/assembly/collaboration/update", json={
            "session_id": session_id,
            "user_id": "user_002",
            "action": "add_slide",
            "data": {"slide_id": "slide_001", "position": 1}
        })
        
        assert update_response.status_code == 200
        update_data = update_response.json()
        assert update_data['success'] is True
        assert 'version' in update_data
```

## Performance Integration Tests

### Load Testing

```python
# tests/integration/test_performance.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class TestPerformanceIntegration:
    """Test system performance under load."""
    
    @pytest.mark.asyncio
    async def test_concurrent_search_performance(
        self,
        test_client,
        sample_test_data
    ):
        """Test search performance under concurrent load."""
        
        # Setup test data
        project_response = test_client.post("/api/projects", json={
            "name": "Performance Test Project",
            "description": "Performance testing"
        })
        project_id = project_response.json()['project']['id']
        
        # Create multiple slides for testing
        for i in range(100):
            test_client.post("/api/slides", json={
                "title": f"Performance Test Slide {i}",
                "content_preview": f"Content for slide {i} with various keywords",
                "slide_type": "text",
                "project_id": project_id,
                "keywords": [f"keyword_{i}", "performance", "test"]
            })
        
        # Test concurrent searches
        search_queries = [
            "performance analysis",
            "test results",
            "keyword search",
            "content analysis",
            "slide performance"
        ]
        
        async def perform_search(query):
            start_time = time.time()
            response = test_client.post("/api/search/natural-language", json={
                "query": query,
                "project_id": project_id
            })
            end_time = time.time()
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            
            return end_time - start_time
        
        # Execute concurrent searches
        tasks = [perform_search(query) for query in search_queries * 4]  # 20 concurrent searches
        search_times = await asyncio.gather(*tasks)
        
        # Verify performance requirements
        avg_search_time = sum(search_times) / len(search_times)
        max_search_time = max(search_times)
        
        assert avg_search_time < 2.0, f"Average search time too high: {avg_search_time}s"
        assert max_search_time < 5.0, f"Maximum search time too high: {max_search_time}s"
        
        print(f"Search Performance Results:")
        print(f"  Average time: {avg_search_time:.3f}s")
        print(f"  Maximum time: {max_search_time:.3f}s")
        print(f"  Total searches: {len(search_times)}")
    
    @pytest.mark.asyncio
    async def test_file_processing_performance(
        self,
        test_client,
        mock_powerpoint_service
    ):
        """Test file processing performance."""
        
        # Create project
        project_response = test_client.post("/api/projects", json={
            "name": "File Processing Test",
            "description": "Test file processing performance"
        })
        project_id = project_response.json()['project']['id']
        
        # Test multiple file uploads
        upload_times = []
        
        for i in range(5):
            with tempfile.NamedTemporaryFile(suffix='.pptx') as tmp_file:
                # Create larger mock file
                tmp_file.write(b'Mock PowerPoint content' * 1000)
                tmp_file.seek(0)
                
                start_time = time.time()
                response = test_client.post(
                    "/api/files/upload",
                    files={"file": (f"test_{i}.pptx", tmp_file, "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
                    data={"project_id": project_id}
                )
                end_time = time.time()
                
                assert response.status_code == 200
                upload_times.append(end_time - start_time)
        
        avg_upload_time = sum(upload_times) / len(upload_times)
        assert avg_upload_time < 10.0, f"Average upload time too high: {avg_upload_time}s"
    
    def test_database_query_performance(
        self,
        test_db_session,
        sample_test_data
    ):
        """Test database query performance with large datasets."""
        from services.database_service import DatabaseService
        
        db_service = DatabaseService(test_db_session)
        
        # Create large dataset
        project = db_service.create_project_sync(
            name="Performance DB Test",
            description="Database performance testing"
        )
        
        # Insert many slides
        start_time = time.time()
        for i in range(1000):
            db_service.create_slide_sync(
                project_id=project['id'],
                slide_number=i + 1,
                title=f"Performance Slide {i}",
                content=f"Content for performance testing slide {i}",
                slide_type="text"
            )
        insert_time = time.time() - start_time
        
        # Test query performance
        start_time = time.time()
        slides = db_service.search_slides_sync(
            project_id=project['id'],
            query="performance"
        )
        query_time = time.time() - start_time
        
        assert len(slides) > 0
        assert insert_time < 30.0, f"Insert time too high: {insert_time}s"
        assert query_time < 1.0, f"Query time too high: {query_time}s"
        
        print(f"Database Performance Results:")
        print(f"  Insert 1000 records: {insert_time:.3f}s")
        print(f"  Search query: {query_time:.3f}s")
        print(f"  Records found: {len(slides)}")
```

## Test Automation and CI/CD

### Pytest Configuration

```python
# pytest.ini
[tool:pytest]
minversion = 6.0
addopts = 
    -ra 
    -q 
    --tb=short
    --strict-markers
    --cov=services
    --cov=api
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=80
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    slow: Slow running tests
    requires_openai: Tests requiring OpenAI API
    requires_powerpoint: Tests requiring PowerPoint COM
asyncio_mode = auto
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

### GitHub Actions Workflow

```yaml
# .github/workflows/integration_tests.yml
name: Integration Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: prezi_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python 3.9
      uses: actions/setup-python@v3
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest-cov pytest-asyncio
    
    - name: Set up test environment
      run: |
        cp .env.test .env
        python -m pytest --version
    
    - name: Run integration tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/prezi_test
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        ENVIRONMENT: test
      run: |
        python -m pytest tests/integration/ -v --cov=services --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: integration
        name: integration-tests
    
    - name: Run performance tests
      if: github.event_name == 'push' && github.ref == 'refs/heads/main'
      run: |
        python -m pytest tests/integration/test_performance.py -v -m performance
```

### Test Data Management

```python
# tests/fixtures/test_data_manager.py
import json
import pytest
from pathlib import Path
from typing import Dict, Any

class TestDataManager:
    """Manage test data for integration tests."""
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)
    
    def load_test_data(self, dataset_name: str) -> Dict[str, Any]:
        """Load test data from JSON file."""
        data_file = self.data_dir / f"{dataset_name}.json"
        if data_file.exists():
            return json.loads(data_file.read_text())
        return {}
    
    def save_test_data(self, dataset_name: str, data: Dict[str, Any]) -> None:
        """Save test data to JSON file."""
        data_file = self.data_dir / f"{dataset_name}.json"
        data_file.write_text(json.dumps(data, indent=2))
    
    def create_sample_powerpoint_data(self) -> Dict[str, Any]:
        """Create sample PowerPoint processing data."""
        return {
            "files": [
                {
                    "name": "quarterly_report.pptx",
                    "size": 2048000,
                    "slides": [
                        {
                            "slide_number": 1,
                            "title": "Quarterly Financial Report",
                            "content": "Q3 financial performance overview",
                            "slide_type": "title",
                            "elements": [
                                {
                                    "type": "text",
                                    "content": "Q3 Financial Report",
                                    "position": {"x": 100, "y": 50, "width": 400, "height": 50}
                                }
                            ]
                        },
                        {
                            "slide_number": 2,
                            "title": "Revenue Analysis",
                            "content": "Revenue growth charts and analysis",
                            "slide_type": "chart",
                            "elements": [
                                {
                                    "type": "chart",
                                    "content": "Revenue growth chart",
                                    "position": {"x": 50, "y": 100, "width": 500, "height": 300}
                                }
                            ]
                        }
                    ]
                }
            ]
        }

@pytest.fixture
def test_data_manager():
    """Provide test data manager for tests."""
    return TestDataManager()

@pytest.fixture
def sample_powerpoint_data(test_data_manager):
    """Provide sample PowerPoint data."""
    return test_data_manager.create_sample_powerpoint_data()
```

## Best Practices and Tips

### Integration Test Design Principles

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Realistic Data**: Use realistic test data that represents actual use cases
3. **Error Scenarios**: Test both success and failure scenarios
4. **Performance Awareness**: Include performance assertions where appropriate
5. **Clear Assertions**: Make test assertions specific and meaningful

### Debugging Integration Tests

```python
# tests/utils/debugging.py
import logging
import json
from typing import Any

def setup_test_logging():
    """Setup detailed logging for integration tests."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('integration_tests.log'),
            logging.StreamHandler()
        ]
    )

def log_test_data(test_name: str, data: Any):
    """Log test data for debugging."""
    logger = logging.getLogger(f"test.{test_name}")
    logger.debug(f"Test data: {json.dumps(data, indent=2, default=str)}")

def assert_with_details(condition: bool, message: str, actual: Any = None, expected: Any = None):
    """Enhanced assertion with detailed error information."""
    if not condition:
        error_msg = f"Assertion failed: {message}"
        if actual is not None:
            error_msg += f"\nActual: {actual}"
        if expected is not None:
            error_msg += f"\nExpected: {expected}"
        raise AssertionError(error_msg)
```

## Testing Checklist

### Pre-Integration Test Checklist
- [ ] All unit tests passing
- [ ] Test database configured and accessible
- [ ] Mock services properly configured
- [ ] Test data fixtures created
- [ ] Environment variables set for testing

### Integration Test Coverage Checklist
- [ ] Service-to-service communication
- [ ] Database operations and transactions
- [ ] External API integrations (mocked)
- [ ] File upload and processing workflows
- [ ] Search and AI analysis workflows
- [ ] Assembly creation and export
- [ ] Error handling and fallback mechanisms
- [ ] Performance under load
- [ ] Concurrent operation handling

### Post-Integration Test Checklist
- [ ] All tests passing consistently
- [ ] Performance metrics within acceptable ranges
- [ ] Test coverage above 80%
- [ ] Integration test documentation updated
- [ ] CI/CD pipeline configured
- [ ] Test data cleanup verified

## Conclusion

Integration testing is crucial for ensuring that all components of the PrezI system work together correctly. By following the patterns and practices outlined in this module, you can build confidence that your AI-powered presentation system will perform reliably in production.

Key takeaways:
- Design tests that mirror real user workflows
- Use proper mocking for external dependencies
- Include performance testing for critical operations
- Automate tests in your CI/CD pipeline
- Test both success and failure scenarios thoroughly

In the next module, we'll explore advanced features including real-time collaboration, advanced AI capabilities, and system optimization techniques.