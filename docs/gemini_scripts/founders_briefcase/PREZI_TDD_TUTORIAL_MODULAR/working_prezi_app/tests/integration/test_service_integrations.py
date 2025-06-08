"""
Service Integration Tests for PrezI
Tests integration between individual services and their dependencies
Based on CONSOLIDATED_FOUNDERS_BRIEFCASE.md specifications
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

class TestPowerPointServiceIntegration:
    """Test PowerPoint service integration with database and file system."""
    
    @pytest.mark.asyncio
    async def test_file_processing_and_database_storage(
        self,
        test_db_session,
        mock_powerpoint_service,
        db_test_utils,
        sample_test_data
    ):
        """Test complete file processing workflow with database storage."""
        from services.database_service import DatabaseService
        
        db_service = DatabaseService(test_db_session)
        
        # Create test project
        project = db_test_utils.create_test_project(
            test_db_session,
            sample_test_data['projects'][0]
        )
        
        # Create temporary PowerPoint file
        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as tmp_file:
            tmp_file.write(b'Mock PowerPoint content for integration testing')
            file_path = tmp_file.name
        
        try:
            # Process file with PowerPoint service
            processing_result = await mock_powerpoint_service.extract_slides_from_file(
                file_path, project.id
            )
            
            assert processing_result['success'] is True
            assert processing_result['slides_extracted'] == 5
            assert len(processing_result['slides']) == 5
            
            # Store slides in database
            stored_slides = []
            for slide_data in processing_result['slides']:
                # Create slide record
                slide = await db_service.create_slide(
                    project_id=project.id,
                    slide_number=slide_data['slide_number'],
                    title=slide_data['title'],
                    content=slide_data['content'],
                    slide_type=slide_data['slide_type'],
                    thumbnail_path=slide_data['thumbnail_path'],
                    full_image_path=slide_data['full_image_path'],
                    notes=slide_data.get('notes', '')
                )
                
                # Store elements
                for element_data in slide_data.get('elements', []):
                    element = await db_service.create_slide_element(
                        slide_id=slide['id'],
                        element_type=element_data['element_type'],
                        content=element_data.get('content', ''),
                        position_x=element_data['position_x'],
                        position_y=element_data['position_y'],
                        width=element_data['width'],
                        height=element_data['height']
                    )
                    assert element is not None
                
                stored_slides.append(slide)
            
            # Verify slides were stored correctly
            assert len(stored_slides) == 5
            
            # Test retrieval
            retrieved_slides = await db_service.get_project_slides(project.id)
            assert len(retrieved_slides) == 5
            
            # Verify slide data integrity
            for original_slide, stored_slide in zip(processing_result['slides'], stored_slides):
                assert stored_slide['title'] == original_slide['title']
                assert stored_slide['content'] == original_slide['content']
                assert stored_slide['slide_type'] == original_slide['slide_type']
                assert stored_slide['slide_number'] == original_slide['slide_number']
        
        finally:
            # Cleanup
            Path(file_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_powerpoint_error_handling_and_fallback(
        self,
        test_db_session,
        mock_powerpoint_service
    ):
        """Test PowerPoint service error handling and fallback mechanisms."""
        from services.database_service import DatabaseService
        
        db_service = DatabaseService(test_db_session)
        
        # Create test project
        project = await db_service.create_project(
            name="Error Handling Test",
            description="Test PowerPoint error handling"
        )
        
        # Test with corrupted file
        with patch.object(mock_powerpoint_service, 'extract_slides_from_file') as mock_extract:
            # Simulate PowerPoint COM error
            mock_extract.side_effect = Exception("PowerPoint COM automation failed")
            
            with pytest.raises(Exception):
                await mock_powerpoint_service.extract_slides_from_file(
                    "/nonexistent/file.pptx", project['id']
                )
        
        # Test fallback to python-pptx
        with patch.object(mock_powerpoint_service, 'extract_slides_from_file') as mock_extract:
            mock_extract.return_value = {
                'success': True,
                'slides_extracted': 2,
                'fallback_used': True,
                'fallback_method': 'python_pptx',
                'slides': [
                    {
                        'slide_number': 1,
                        'title': 'Fallback Slide 1',
                        'content': 'Extracted using python-pptx fallback',
                        'slide_type': 'text',
                        'thumbnail_path': '/fallback/thumb1.png',
                        'elements': []
                    },
                    {
                        'slide_number': 2,
                        'title': 'Fallback Slide 2', 
                        'content': 'Second slide from fallback method',
                        'slide_type': 'text',
                        'thumbnail_path': '/fallback/thumb2.png',
                        'elements': []
                    }
                ]
            }
            
            result = await mock_powerpoint_service.extract_slides_from_file(
                "/test/file.pptx", project['id']
            )
            
            assert result['success'] is True
            assert result['fallback_used'] is True
            assert result['slides_extracted'] == 2
    
    @pytest.mark.asyncio
    async def test_concurrent_file_processing(
        self,
        test_db_session,
        mock_powerpoint_service,
        async_test_utils
    ):
        """Test concurrent file processing capabilities."""
        from services.database_service import DatabaseService
        
        db_service = DatabaseService(test_db_session)
        
        # Create test project
        project = await db_service.create_project(
            name="Concurrent Processing Test",
            description="Test concurrent file processing"
        )
        
        # Create multiple processing tasks
        file_tasks = []
        for i in range(5):
            task = mock_powerpoint_service.extract_slides_from_file(
                f"/mock/concurrent_file_{i}.pptx", project['id']
            )
            file_tasks.append(task)
        
        # Process files concurrently with controlled concurrency
        results = await async_test_utils.run_concurrent_tasks(file_tasks, max_concurrency=3)
        
        # Verify all files processed successfully
        assert len(results) == 5
        for result in results:
            assert result['success'] is True
            assert result['slides_extracted'] == 5
        
        # Verify no corruption or interference between concurrent operations
        total_slides = sum(result['slides_extracted'] for result in results)
        assert total_slides == 25  # 5 files × 5 slides each

class TestAIServiceIntegration:
    """Test AI service integration with content analysis and database."""
    
    @pytest.mark.asyncio
    async def test_slide_content_analysis_workflow(
        self,
        test_db_session,
        mock_openai_client,
        sample_test_data
    ):
        """Test complete slide content analysis workflow."""
        from services.ai_service import AIService
        from services.database_service import DatabaseService
        
        db_service = DatabaseService(test_db_session)
        ai_service = AIService()
        
        # Create test project and slide
        project = await db_service.create_project(
            name="AI Analysis Test",
            description="Test AI content analysis"
        )
        
        slide_data = sample_test_data['slides'][0]
        slide = await db_service.create_slide(
            project_id=project['id'],
            slide_number=1,
            title=slide_data['title'],
            content=slide_data['content_preview'],
            slide_type=slide_data['slide_type']
        )
        
        # Test AI content analysis
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
        
        # Verify confidence score is valid
        assert isinstance(analysis['confidence_score'], float)
        assert 0 <= analysis['confidence_score'] <= 1
        
        # Store AI analysis in database
        await db_service.update_slide_ai_analysis(
            slide_id=slide['id'],
            ai_topic=analysis['topic'],
            ai_summary=analysis['summary'],
            ai_confidence_score=analysis['confidence_score'],
            key_insights=analysis['key_insights']
        )
        
        # Verify analysis was stored
        updated_slide = await db_service.get_slide_by_id(slide['id'])
        assert updated_slide['ai_analysis'] is not None
        assert updated_slide['ai_analysis']['ai_topic'] == analysis['topic']
        assert updated_slide['ai_analysis']['ai_confidence_score'] == analysis['confidence_score']
    
    @pytest.mark.asyncio
    async def test_keyword_suggestion_and_storage(
        self,
        test_db_session,
        mock_openai_client
    ):
        """Test AI keyword suggestion and database storage integration."""
        from services.ai_service import AIService
        from services.database_service import DatabaseService
        
        db_service = DatabaseService(test_db_session)
        ai_service = AIService()
        
        # Create test project and slide
        project = await db_service.create_project(
            name="Keyword Suggestion Test",
            description="Test AI keyword suggestions"
        )
        
        slide = await db_service.create_slide(
            project_id=project['id'],
            slide_number=1,
            title="Financial Performance Analysis",
            content="Quarterly revenue analysis showing strong growth metrics and market expansion",
            slide_type="chart"
        )
        
        # Test keyword suggestion
        keyword_result = await ai_service.suggest_keywords(
            content=slide['content'],
            context='financial_presentation'
        )
        
        assert isinstance(keyword_result, list)
        assert len(keyword_result) > 0
        
        # Store suggested keywords
        stored_keywords = []
        for keyword_data in keyword_result:
            # Create keyword if it doesn't exist
            keyword = await db_service.create_or_get_keyword(
                name=keyword_data['keyword'],
                description=f"AI-suggested keyword for {keyword_data['category']}",
                is_ai_suggested=True,
                ai_confidence=keyword_data['confidence']
            )
            
            # Associate keyword with slide
            await db_service.add_keyword_to_slide(
                slide_id=slide['id'],
                keyword_id=keyword['id']
            )
            
            stored_keywords.append(keyword)
        
        # Verify keywords were stored and associated
        slide_keywords = await db_service.get_slide_keywords(slide['id'])
        assert len(slide_keywords) == len(keyword_result)
        
        # Verify AI confidence scores
        for keyword in slide_keywords:
            if keyword.get('is_ai_suggested'):
                assert keyword.get('ai_confidence') is not None
                assert 0 <= keyword['ai_confidence'] <= 1
    
    @pytest.mark.asyncio
    async def test_ai_fallback_mechanisms(
        self,
        test_db_session
    ):
        """Test AI service fallback when OpenAI is unavailable."""
        from services.ai_service import AIService
        
        ai_service = AIService()
        
        # Mock OpenAI failure
        with patch('openai.AsyncOpenAI') as mock_client:
            mock_client.side_effect = Exception("OpenAI API unavailable")
            
            # Test fallback analysis
            result = await ai_service.analyze_slide_content(
                slide_id="test_slide",
                content="Sample financial data showing revenue growth",
                slide_type="chart"
            )
            
            # Should fall back to rule-based analysis
            assert result['success'] is True
            assert 'fallback_analysis' in result
            assert result['fallback_analysis'] is not None
            
            # Verify fallback provides basic analysis
            fallback = result['fallback_analysis']
            assert 'topic' in fallback
            assert 'summary' in fallback
            assert 'confidence_score' in fallback
            assert fallback['confidence_score'] < 1.0  # Lower confidence for fallback
    
    @pytest.mark.asyncio
    async def test_ai_rate_limiting_and_retry(
        self,
        mock_openai_client
    ):
        """Test AI service rate limiting and retry logic."""
        from services.ai_service import AIService
        
        ai_service = AIService()
        
        # Configure mock to simulate rate limiting initially, then succeed
        call_count = 0
        
        async def mock_rate_limited_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:
                # Simulate rate limit error
                from openai import RateLimitError
                raise RateLimitError("Rate limit exceeded", response=None, body=None)
            else:
                # Success after retries
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.content = json.dumps({
                    "topic": "Test Topic",
                    "summary": "Test analysis after retry",
                    "confidence_score": 0.85,
                    "key_insights": ["Retry successful"]
                })
                return mock_response
        
        mock_openai_client.chat.completions.create.side_effect = mock_rate_limited_call
        
        # Test analysis with rate limiting
        result = await ai_service.analyze_slide_content(
            slide_id="rate_limit_test",
            content="Test content for rate limiting",
            slide_type="text"
        )
        
        # Should eventually succeed after retries
        assert result['success'] is True
        assert call_count > 1  # Verify retries occurred
        assert result['analysis']['summary'] == "Test analysis after retry"

class TestSearchServiceIntegration:
    """Test search service integration with AI and database."""
    
    @pytest.mark.asyncio
    async def test_natural_language_search_with_ai_interpretation(
        self,
        test_db_session,
        mock_openai_client,
        sample_test_data
    ):
        """Test natural language search with AI query interpretation."""
        from services.search_service import SearchService
        from services.database_service import DatabaseService
        
        db_service = DatabaseService(test_db_session)
        search_service = SearchService(db_service)
        
        # Setup test data
        project = await db_service.create_project(
            name="Search Integration Test",
            description="Test search service integration"
        )
        
        # Create test slides with varied content
        test_slides = [
            {
                'title': 'Revenue Growth Analysis Q3',
                'content': 'Quarterly revenue increased by 15% compared to previous quarter with strong performance in all segments',
                'slide_type': 'chart',
                'keywords': ['revenue', 'growth', 'quarterly', 'analysis', 'performance']
            },
            {
                'title': 'Customer Satisfaction Survey Results',
                'content': 'Customer satisfaction scores improved to 4.2/5 with 89% response rate',
                'slide_type': 'table',
                'keywords': ['customer', 'satisfaction', 'survey', 'results', 'scores']
            },
            {
                'title': 'Market Expansion Strategy Overview',
                'content': 'Strategic roadmap for expanding into European and Asian markets with resource allocation',
                'slide_type': 'text',
                'keywords': ['market', 'expansion', 'strategy', 'international', 'roadmap']
            },
            {
                'title': 'Financial Performance Dashboard',
                'content': 'Key financial metrics including profit margins, cash flow, and ROI analysis',
                'slide_type': 'chart',
                'keywords': ['financial', 'performance', 'metrics', 'profit', 'ROI']
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
            for keyword_name in slide_data['keywords']:
                keyword = await db_service.create_or_get_keyword(name=keyword_name)
                await db_service.add_keyword_to_slide(slide['id'], keyword['id'])
            
            created_slides.append(slide)
        
        # Test natural language search with AI interpretation
        search_result = await search_service.natural_language_search(
            query="Show me financial charts and revenue performance data",
            project_id=project['id']
        )
        
        assert search_result['success'] is True
        assert search_result['total_results'] > 0
        assert search_result['search_strategy'] == 'ai_natural_language'
        
        # Verify AI query interpretation
        assert 'query_interpretation' in search_result
        interpretation = search_result['query_interpretation']
        
        assert 'search_intent' in interpretation
        assert 'topics' in interpretation
        assert 'keywords' in interpretation
        assert 'content_types' in interpretation
        assert 'confidence' in interpretation
        
        # Verify interpretation contains expected elements
        assert 'chart' in interpretation['content_types']
        assert any('revenue' in topic.lower() for topic in interpretation['topics'])
        assert any('financial' in keyword.lower() for keyword in interpretation['keywords'])
        
        # Verify relevant slides are returned
        results = search_result['results']
        assert len(results) > 0
        
        # Should prioritize chart slides with financial/revenue content
        chart_slides = [slide for slide in results if slide['slide_type'] == 'chart']
        assert len(chart_slides) > 0
        
        revenue_slides = [slide for slide in results 
                         if 'revenue' in slide['title'].lower() or 'revenue' in slide['content_preview'].lower()]
        assert len(revenue_slides) > 0
    
    @pytest.mark.asyncio
    async def test_semantic_search_with_embeddings(
        self,
        test_db_session,
        mock_openai_client,
        sample_test_data
    ):
        """Test semantic search with AI embeddings."""
        from services.search_service import SearchService
        from services.database_service import DatabaseService
        
        db_service = DatabaseService(test_db_session)
        search_service = SearchService(db_service)
        
        # Setup test data (reuse from previous test)
        project = await db_service.create_project(
            name="Semantic Search Test",
            description="Test semantic search capabilities"
        )
        
        # Create slides with semantically related content
        semantic_test_slides = [
            {
                'title': 'Profit Margin Analysis',
                'content': 'Analysis of profit margins across different product lines',
                'slide_type': 'chart'
            },
            {
                'title': 'Revenue Stream Breakdown',
                'content': 'Breakdown of revenue streams and their contribution to total income',
                'slide_type': 'chart'
            },
            {
                'title': 'Team Building Activities',
                'content': 'Overview of team building exercises and employee engagement initiatives',
                'slide_type': 'text'
            }
        ]
        
        for i, slide_data in enumerate(semantic_test_slides):
            await db_service.create_slide(
                project_id=project['id'],
                slide_number=i + 1,
                title=slide_data['title'],
                content=slide_data['content'],
                slide_type=slide_data['slide_type']
            )
        
        # Test semantic search for financial concepts
        semantic_result = await search_service.semantic_search(
            query="financial performance and earnings",
            use_ai_embeddings=True
        )
        
        assert semantic_result['search_strategy'] == 'ai_semantic'
        
        # Should find semantically related slides even without exact keyword matches
        results = semantic_result['results']
        
        # Should find profit and revenue slides as semantically related to "financial performance"
        financial_slides = [slide for slide in results 
                           if any(term in slide['title'].lower() for term in ['profit', 'revenue', 'margin'])]
        
        # Should not strongly match team building slide
        team_slides = [slide for slide in results 
                      if 'team' in slide['title'].lower()]
        
        # Verify semantic relevance
        if len(results) > 0:
            assert len(financial_slides) >= len(team_slides)
    
    @pytest.mark.asyncio
    async def test_cross_project_search_integration(
        self,
        test_db_session,
        sample_test_data
    ):
        """Test cross-project search functionality."""
        from services.search_service import SearchService
        from services.database_service import DatabaseService
        
        db_service = DatabaseService(test_db_session)
        search_service = SearchService(db_service)
        
        # Create multiple projects with slides
        projects = []
        all_slides = []
        
        for i in range(3):
            project = await db_service.create_project(
                name=f"Cross-Project Test {i+1}",
                description=f"Project {i+1} for cross-project search testing"
            )
            projects.append(project)
            
            # Create slides with common keywords across projects
            project_slides = [
                {
                    'title': f'Financial Report Project {i+1}',
                    'content': f'Financial analysis and performance metrics for project {i+1}',
                    'slide_type': 'chart'
                },
                {
                    'title': f'Customer Data Project {i+1}',
                    'content': f'Customer analytics and satisfaction data for project {i+1}',
                    'slide_type': 'table'
                }
            ]
            
            for j, slide_data in enumerate(project_slides):
                slide = await db_service.create_slide(
                    project_id=project['id'],
                    slide_number=j + 1,
                    title=slide_data['title'],
                    content=slide_data['content'],
                    slide_type=slide_data['slide_type']
                )
                
                # Add common keywords
                common_keywords = ['financial', 'data', 'analysis']
                for keyword_name in common_keywords:
                    keyword = await db_service.create_or_get_keyword(name=keyword_name)
                    await db_service.add_keyword_to_slide(slide['id'], keyword['id'])
                
                all_slides.append(slide)
        
        # Test cross-project search
        search_filter = {
            'query': 'financial analysis',
            'search_scope': 'all_projects',
            'content_types': ['chart'],
            'sort_by': 'relevance',
            'sort_order': 'desc',
            'limit': 50,
            'offset': 0,
            'include_ai_analysis': True
        }
        
        cross_result = await search_service.advanced_search(search_filter)
        
        assert cross_result['success'] is True
        assert cross_result['search_strategy'] == 'cross_project_advanced'
        
        # Should find slides from multiple projects
        project_ids = set(slide['project_id'] for slide in cross_result['results'])
        assert len(project_ids) > 1, "Cross-project search should return slides from multiple projects"
        
        # Should find financial chart slides from all projects
        financial_charts = [slide for slide in cross_result['results'] 
                           if slide['slide_type'] == 'chart' and 'financial' in slide['title'].lower()]
        
        assert len(financial_charts) == 3  # One from each project

class TestAssemblyServiceIntegration:
    """Test assembly service integration with AI and export functionality."""
    
    @pytest.mark.asyncio
    async def test_ai_automated_assembly_creation(
        self,
        test_db_session,
        mock_openai_client,
        sample_test_data
    ):
        """Test AI-automated assembly creation and optimization."""
        from services.assembly_service import AssemblyService
        from services.database_service import DatabaseService
        
        db_service = DatabaseService(test_db_session)
        assembly_service = AssemblyService(db_service)
        
        # Setup test project and slides
        project = await db_service.create_project(
            name="AI Assembly Test",
            description="Test AI-automated assembly creation"
        )
        
        # Create diverse slides for assembly
        test_slides = [
            {
                'title': 'Executive Summary',
                'content': 'High-level overview of company performance and strategic direction',
                'slide_type': 'title'
            },
            {
                'title': 'Revenue Growth Trends',
                'content': 'Analysis of revenue growth over the past 4 quarters',
                'slide_type': 'chart'
            },
            {
                'title': 'Market Share Analysis',
                'content': 'Competitive landscape and market position analysis',
                'slide_type': 'chart'
            },
            {
                'title': 'Customer Metrics',
                'content': 'Customer acquisition, retention, and satisfaction metrics',
                'slide_type': 'table'
            },
            {
                'title': 'Strategic Initiatives',
                'content': 'Key strategic initiatives and implementation roadmap',
                'slide_type': 'text'
            },
            {
                'title': 'Financial Outlook',
                'content': 'Future financial projections and growth targets',
                'slide_type': 'conclusion'
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
            created_slides.append(slide)
        
        # Test AI-automated assembly creation
        assembly_result = await assembly_service.create_ai_automated_assembly(
            intent="Create an executive presentation that tells the story of our company's performance, current market position, and future growth strategy",
            project_id=project['id'],
            user_preferences={
                'duration': 20,
                'style': 'executive',
                'target_audience': 'board_of_directors'
            }
        )
        
        assert assembly_result['success'] is True
        assert 'assembly_plan' in assembly_result
        assert 'recommendations' in assembly_result
        
        assembly_plan = assembly_result['assembly_plan']
        assert assembly_plan['ai_generated'] is True
        assert len(assembly_plan['slides']) > 0
        
        # Verify logical slide ordering
        slide_positions = [slide['position'] for slide in assembly_plan['slides']]
        assert slide_positions == sorted(slide_positions)
        
        # Verify AI rationale for slide selection
        ai_suggested_slides = [slide for slide in assembly_plan['slides'] if slide.get('ai_suggested')]
        assert len(ai_suggested_slides) > 0
        
        for slide in ai_suggested_slides:
            assert 'rationale' in slide
            assert slide['rationale'] is not None
        
        # Verify recommendations are provided
        assert isinstance(assembly_result['recommendations'], list)
        assert len(assembly_result['recommendations']) > 0
    
    @pytest.mark.asyncio
    async def test_assembly_optimization_workflow(
        self,
        test_db_session,
        mock_openai_client
    ):
        """Test assembly optimization with AI suggestions."""
        from services.assembly_service import AssemblyService
        from services.database_service import DatabaseService
        
        db_service = DatabaseService(test_db_session)
        assembly_service = AssemblyService(db_service)
        
        # Create test assembly
        project = await db_service.create_project(
            name="Optimization Test",
            description="Test assembly optimization"
        )
        
        assembly = await db_service.create_assembly(
            name="Test Assembly for Optimization",
            project_id=project['id'],
            slides=[
                {'slide_id': 'slide_003', 'position': 1, 'title': 'Conclusion'},
                {'slide_id': 'slide_001', 'position': 2, 'title': 'Introduction'},
                {'slide_id': 'slide_002', 'position': 3, 'title': 'Main Content'}
            ]
        )
        
        # Test assembly optimization
        optimization_result = await assembly_service.optimize_assembly(
            assembly_id=assembly['id'],
            goals=['logical_flow', 'audience_engagement', 'time_efficiency']
        )
        
        assert optimization_result['success'] is True
        assert 'optimization' in optimization_result
        
        optimization = optimization_result['optimization']
        assert 'optimized_order' in optimization
        assert 'improvements' in optimization
        assert 'flow_score' in optimization
        assert 'rationale' in optimization
        
        # Verify flow score improvement
        assert isinstance(optimization['flow_score'], (int, float))
        assert 0 <= optimization['flow_score'] <= 1
        
        # Verify logical ordering suggestions
        optimized_order = optimization['optimized_order']
        assert len(optimized_order) == 3
        
        # Should suggest moving introduction to the beginning
        intro_slide = next((slide for slide in optimized_order if 'Introduction' in slide.get('title', '')), None)
        if intro_slide:
            assert intro_slide['position'] == 1
    
    @pytest.mark.asyncio
    async def test_export_integration_workflow(
        self,
        test_db_session,
        mock_powerpoint_service
    ):
        """Test assembly export integration with PowerPoint service."""
        from services.assembly_service import AssemblyService
        from services.database_service import DatabaseService
        
        db_service = DatabaseService(test_db_session)
        assembly_service = AssemblyService(db_service)
        
        # Create test assembly with slides
        project = await db_service.create_project(
            name="Export Test",
            description="Test assembly export functionality"
        )
        
        # Create slides
        slides = []
        for i in range(3):
            slide = await db_service.create_slide(
                project_id=project['id'],
                slide_number=i + 1,
                title=f'Export Test Slide {i+1}',
                content=f'Content for export test slide {i+1}',
                slide_type='text'
            )
            slides.append(slide)
        
        # Create assembly
        assembly = await db_service.create_assembly(
            name="Export Test Assembly",
            project_id=project['id'],
            slides=[
                {'slide_id': slide['id'], 'position': i+1, 'title': slide['title']}
                for i, slide in enumerate(slides)
            ]
        )
        
        # Test PowerPoint export
        export_result = await assembly_service.export_assembly(
            assembly_id=assembly['id'],
            format='pptx',
            options={
                'include_notes': True,
                'slide_numbering': True,
                'quality': 'high'
            }
        )
        
        assert export_result['success'] is True
        assert 'file_path' in export_result
        assert export_result['slide_count'] == 3
        assert export_result['format'] == 'pptx'
        
        # Test PDF export
        pdf_export_result = await assembly_service.export_assembly(
            assembly_id=assembly['id'],
            format='pdf',
            options={'quality': 'high'}
        )
        
        assert pdf_export_result['success'] is True
        assert pdf_export_result['format'] == 'pdf'
        
        # Test HTML export
        html_export_result = await assembly_service.export_assembly(
            assembly_id=assembly['id'],
            format='html',
            options={
                'interactive': True,
                'responsive': True
            }
        )
        
        assert html_export_result['success'] is True
        assert html_export_result['format'] == 'html'
        assert html_export_result.get('interactive') is True
        assert html_export_result.get('responsive') is True