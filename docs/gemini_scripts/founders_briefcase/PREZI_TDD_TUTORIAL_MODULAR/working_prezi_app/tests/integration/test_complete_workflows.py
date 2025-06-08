"""
Complete Workflow Integration Tests for PrezI
Tests end-to-end user workflows from file upload to presentation assembly
Based on CONSOLIDATED_FOUNDERS_BRIEFCASE.md specifications
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch

class TestCompleteWorkflows:
    """Test complete user workflows end-to-end."""
    
    def test_complete_presentation_creation_workflow(
        self,
        test_client: TestClient,
        mock_powerpoint_service,
        mock_openai_client,
        sample_test_data,
        api_response_validator,
        performance_monitor
    ):
        """
        Test complete workflow: Create project -> Upload file -> Process slides -> 
        Analyze with AI -> Search content -> Create assembly -> Export presentation
        """
        performance_monitor.start_timer("complete_workflow")
        
        # Step 1: Create project
        performance_monitor.start_timer("create_project")
        project_response = test_client.post("/api/projects", json={
            "name": "Complete Workflow Test Project",
            "description": "End-to-end testing project for presentation creation"
        })
        performance_monitor.end_timer("create_project")
        
        assert project_response.status_code == 200
        project_data = project_response.json()
        assert project_data['success'] is True
        assert 'project' in project_data
        
        project_id = project_data['project']['id']
        assert project_id is not None
        
        # Step 2: Upload PowerPoint file
        performance_monitor.start_timer("file_upload")
        mock_pptx_content = b'Mock PowerPoint content for integration testing' * 100
        
        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as tmp_file:
            tmp_file.write(mock_pptx_content)
            tmp_file.seek(0)
            
            files = {
                "file": ("test_presentation.pptx", tmp_file, "application/vnd.openxmlformats-officedocument.presentationml.presentation")
            }
            data = {"project_id": project_id}
            
            upload_response = test_client.post("/api/files/upload", files=files, data=data)
            
        performance_monitor.end_timer("file_upload")
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data['success'] is True
        assert 'file_id' in upload_data
        assert upload_data['processing_started'] is True
        
        file_id = upload_data['file_id']
        
        # Step 3: Check processing status
        performance_monitor.start_timer("check_processing")
        status_response = test_client.get(f"/api/files/{file_id}/status")
        performance_monitor.end_timer("check_processing")
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data['status'] == 'completed'
        assert status_data['slides_processed'] == 5
        
        # Step 4: Get processed slides
        performance_monitor.start_timer("get_slides")
        slides_response = test_client.get(f"/api/projects/{project_id}/slides")
        performance_monitor.end_timer("get_slides")
        
        assert slides_response.status_code == 200
        slides_data = slides_response.json()
        assert len(slides_data) > 0
        
        # Validate slide data structure
        for slide in slides_data:
            api_response_validator.validate_slide_data(slide)
        
        slide_id = slides_data[0]['id']
        
        # Step 5: Analyze slides with AI
        performance_monitor.start_timer("ai_analysis")
        analysis_response = test_client.post(f"/api/slides/{slide_id}/analyze")
        performance_monitor.end_timer("ai_analysis")
        
        assert analysis_response.status_code == 200
        analysis_data = analysis_response.json()
        assert analysis_data['success'] is True
        
        api_response_validator.validate_ai_analysis(analysis_data)
        
        # Step 6: Search for slides with natural language
        performance_monitor.start_timer("natural_search")
        search_response = test_client.post("/api/search/natural-language", json={
            "query": "financial performance charts and revenue analysis",
            "project_id": project_id,
            "filters": {
                "content_types": ["chart"],
                "include_ai_analysis": True
            }
        })
        performance_monitor.end_timer("natural_search")
        
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data['success'] is True
        assert search_data['total_results'] > 0
        
        api_response_validator.validate_search_response(search_data)
        
        # Verify AI query interpretation
        assert 'query_interpretation' in search_data
        interpretation = search_data['query_interpretation']
        assert 'search_intent' in interpretation
        assert 'topics' in interpretation
        assert 'content_types' in interpretation
        
        # Step 7: Create manual assembly
        performance_monitor.start_timer("create_assembly")
        selected_slides = [
            {"slide_id": slide['id'], "title": slide['title']}
            for slide in search_data['results'][:3]
        ]
        
        assembly_response = test_client.post("/api/assembly/manual", json={
            "name": "Financial Performance Summary",
            "slides": selected_slides,
            "project_id": project_id,
            "optimize_order": True
        })
        performance_monitor.end_timer("create_assembly")
        
        assert assembly_response.status_code == 200
        assembly_data = assembly_response.json()
        assert assembly_data['success'] is True
        assert 'assembly' in assembly_data
        
        api_response_validator.validate_assembly_data(assembly_data['assembly'])
        
        assembly_id = assembly_data['assembly']['id']
        
        # Step 8: Optimize assembly with AI
        performance_monitor.start_timer("optimize_assembly")
        optimization_response = test_client.post(f"/api/assembly/{assembly_id}/optimize", json={
            "optimization_goals": ["logical_flow", "audience_engagement", "time_efficiency"]
        })
        performance_monitor.end_timer("optimize_assembly")
        
        assert optimization_response.status_code == 200
        optimization_data = optimization_response.json()
        assert optimization_data['success'] is True
        
        # Step 9: Export assembly to PowerPoint
        performance_monitor.start_timer("export_powerpoint")
        export_response = test_client.post(f"/api/assembly/{assembly_id}/export", json={
            "format": "pptx",
            "options": {
                "include_notes": True,
                "slide_numbering": True,
                "quality": "high"
            }
        })
        performance_monitor.end_timer("export_powerpoint")
        
        assert export_response.status_code == 200
        export_data = export_response.json()
        assert export_data['success'] is True
        assert 'file_path' in export_data
        assert export_data['slide_count'] == len(selected_slides)
        
        # Step 10: Export to PDF
        performance_monitor.start_timer("export_pdf")
        pdf_export_response = test_client.post(f"/api/assembly/{assembly_id}/export", json={
            "format": "pdf",
            "options": {
                "quality": "high",
                "include_notes": False
            }
        })
        performance_monitor.end_timer("export_pdf")
        
        assert pdf_export_response.status_code == 200
        pdf_export_data = pdf_export_response.json()
        assert pdf_export_data['success'] is True
        
        performance_monitor.end_timer("complete_workflow")
        
        # Verify performance requirements
        metrics = performance_monitor.get_metrics()
        performance_monitor.assert_performance("complete_workflow", 30.0)  # Total workflow < 30s
        performance_monitor.assert_performance("file_upload", 5.0)         # Upload < 5s
        performance_monitor.assert_performance("ai_analysis", 3.0)         # AI analysis < 3s
        performance_monitor.assert_performance("natural_search", 2.0)      # Search < 2s
        performance_monitor.assert_performance("create_assembly", 1.0)     # Assembly creation < 1s
        performance_monitor.assert_performance("export_powerpoint", 5.0)   # Export < 5s
        
        print(f"\nWorkflow Performance Metrics:")
        for operation, duration in metrics.items():
            print(f"  {operation}: {duration:.3f}s")
    
    def test_ai_automated_assembly_workflow(
        self,
        test_client: TestClient,
        mock_openai_client,
        sample_test_data,
        api_response_validator
    ):
        """Test AI-automated presentation creation workflow."""
        
        # Create project with pre-existing slides
        project_response = test_client.post("/api/projects", json={
            "name": "AI Assembly Test Project",
            "description": "Test AI-automated assembly creation"
        })
        
        project_data = project_response.json()
        project_id = project_data['project']['id']
        
        # Create sample slides using test data
        created_slides = []
        for slide_data in sample_test_data['slides']:
            slide_response = test_client.post("/api/slides", json={
                **slide_data,
                "project_id": project_id,
                "slide_number": len(created_slides) + 1
            })
            assert slide_response.status_code == 200
            created_slides.append(slide_response.json())
        
        # Test AI-automated assembly creation with comprehensive intent
        ai_assembly_response = test_client.post("/api/assembly/ai-automated", json={
            "intent": "Create a comprehensive executive presentation focusing on financial performance, customer satisfaction, and strategic growth initiatives. The presentation should tell a story that flows from current performance to future opportunities.",
            "project_id": project_id,
            "user_preferences": {
                "duration": 15,
                "style": "executive",
                "include_notes": True,
                "target_audience": "board_of_directors",
                "emphasis": "data_driven"
            }
        })
        
        assert ai_assembly_response.status_code == 200
        ai_data = ai_assembly_response.json()
        assert ai_data['success'] is True
        assert 'assembly_plan' in ai_data
        assert 'recommendations' in ai_data
        assert 'estimated_duration' in ai_data
        
        # Validate assembly plan structure
        assembly_plan = ai_data['assembly_plan']
        api_response_validator.validate_assembly_data(assembly_plan)
        
        assert assembly_plan['ai_generated'] is True
        assert len(assembly_plan['slides']) > 0
        assert 'ai_plan' in assembly_plan
        
        # Validate AI plan details
        ai_plan = assembly_plan['ai_plan']
        required_plan_fields = ['intent', 'target_audience', 'estimated_duration', 'success_metrics']
        for field in required_plan_fields:
            assert field in ai_plan, f"Missing AI plan field: {field}"
        
        # Verify recommendations are provided
        assert isinstance(ai_data['recommendations'], list)
        assert len(ai_data['recommendations']) > 0
        
        # Test that slides are ordered logically by AI
        slide_positions = [slide['position'] for slide in assembly_plan['slides']]
        assert slide_positions == sorted(slide_positions), "Slides should be ordered by position"
        
        # Verify AI rationale is provided for slide selection
        for slide in assembly_plan['slides']:
            if slide.get('ai_suggested'):
                assert 'rationale' in slide, "AI-suggested slides should have rationale"
    
    def test_cross_project_search_and_assembly_workflow(
        self,
        test_client: TestClient,
        mock_openai_client,
        sample_test_data,
        api_response_validator
    ):
        """Test cross-project search and assembly creation workflow."""
        
        # Create multiple projects with slides
        projects = []
        all_slides = []
        
        for i, project_template in enumerate(sample_test_data['projects']):
            project_response = test_client.post("/api/projects", json={
                "name": f"{project_template['name']} - Test {i+1}",
                "description": project_template['description']
            })
            
            project_data = project_response.json()
            projects.append(project_data['project'])
            
            # Add slides to each project
            project_slides = [slide for slide in sample_test_data['slides'] 
                            if slide['project_id'] == project_template['id']]
            
            for slide_template in project_slides:
                slide_response = test_client.post("/api/slides", json={
                    **slide_template,
                    "project_id": project_data['project']['id'],
                    "slide_number": len(all_slides) + 1
                })
                assert slide_response.status_code == 200
                all_slides.append(slide_response.json())
        
        # Test cross-project search
        cross_search_response = test_client.post("/api/search/cross-project", json={
            "query": "financial performance and customer satisfaction",
            "content_types": ["chart", "table"],
            "sort_by": "relevance",
            "sort_order": "desc",
            "limit": 10,
            "offset": 0,
            "include_ai_analysis": True,
            "search_scope": "all_projects"
        })
        
        assert cross_search_response.status_code == 200
        cross_search_data = cross_search_response.json()
        assert cross_search_data['success'] is True
        assert cross_search_data['total_results'] > 0
        
        api_response_validator.validate_search_response(cross_search_data)
        
        # Verify slides from multiple projects are returned
        project_ids = set(slide['project_id'] for slide in cross_search_data['results'])
        assert len(project_ids) > 1, "Cross-project search should return slides from multiple projects"
        
        # Create assembly from cross-project search results
        selected_slides = cross_search_data['results'][:4]
        
        # Use the first project as the assembly owner
        assembly_response = test_client.post("/api/assembly/manual", json={
            "name": "Cross-Project Executive Summary",
            "slides": [{"slide_id": slide['id'], "title": slide['title']} for slide in selected_slides],
            "project_id": projects[0]['id'],
            "optimize_order": True
        })
        
        assert assembly_response.status_code == 200
        assembly_data = assembly_response.json()
        assert assembly_data['success'] is True
        
        # Verify assembly contains slides from multiple projects
        assembly_slide_projects = set()
        for slide in assembly_data['assembly']['slides']:
            # Find the original slide to get its project
            original_slide = next((s for s in selected_slides if s['id'] == slide['slide_id']), None)
            if original_slide:
                assembly_slide_projects.add(original_slide['project_id'])
        
        assert len(assembly_slide_projects) > 1, "Assembly should contain slides from multiple projects"
    
    def test_collaboration_workflow(
        self,
        test_client: TestClient,
        sample_test_data
    ):
        """Test real-time collaboration workflow."""
        
        # Create project and assembly for collaboration
        project_response = test_client.post("/api/projects", json={
            "name": "Collaboration Test Project",
            "description": "Test real-time collaboration features"
        })
        
        project_data = project_response.json()
        project_id = project_data['project']['id']
        
        # Create initial assembly
        assembly_response = test_client.post("/api/assembly/manual", json={
            "name": "Collaborative Presentation",
            "slides": [],
            "project_id": project_id
        })
        
        assembly_data = assembly_response.json()
        assembly_id = assembly_data['assembly']['id']
        
        # Create collaboration session
        collab_response = test_client.post("/api/assembly/collaboration/session", json={
            "assembly_id": assembly_id,
            "owner_id": "user_001",
            "participants": ["user_002", "user_003", "user_004"]
        })
        
        assert collab_response.status_code == 200
        collab_data = collab_response.json()
        assert 'session_id' in collab_data
        assert collab_data['assembly_id'] == assembly_id
        
        session_id = collab_data['session_id']
        
        # Test multiple collaboration updates
        collaboration_scenarios = [
            {
                "user_id": "user_002",
                "action": "add_slide",
                "data": {"slide_id": "slide_001", "position": 1, "title": "Introduction"}
            },
            {
                "user_id": "user_003", 
                "action": "reorder_slides",
                "data": {"slide_moves": [{"slide_id": "slide_001", "new_position": 2}]}
            },
            {
                "user_id": "user_004",
                "action": "add_slide",
                "data": {"slide_id": "slide_002", "position": 1, "title": "Executive Summary"}
            },
            {
                "user_id": "user_002",
                "action": "update_slide_notes",
                "data": {"slide_id": "slide_001", "notes": "Focus on key metrics and performance indicators"}
            }
        ]
        
        for scenario in collaboration_scenarios:
            update_response = test_client.post("/api/assembly/collaboration/update", json={
                "session_id": session_id,
                **scenario
            })
            
            assert update_response.status_code == 200
            update_data = update_response.json()
            assert update_data['success'] is True
            assert 'version' in update_data
            
            # Verify version incrementing
            if 'changes' in update_data:
                assert len(update_data['changes']) > 0
                for change in update_data['changes']:
                    assert 'type' in change
                    assert 'user' in change
                    assert 'details' in change
        
        # Test conflict resolution
        conflict_update_1 = test_client.post("/api/assembly/collaboration/update", json={
            "session_id": session_id,
            "user_id": "user_002",
            "action": "update_slide_title",
            "data": {"slide_id": "slide_001", "title": "New Title by User 2"}
        })
        
        conflict_update_2 = test_client.post("/api/assembly/collaboration/update", json={
            "session_id": session_id,
            "user_id": "user_003",
            "action": "update_slide_title", 
            "data": {"slide_id": "slide_001", "title": "New Title by User 3"}
        })
        
        # Both should succeed, but the system should handle conflicts
        assert conflict_update_1.status_code == 200
        assert conflict_update_2.status_code == 200
        
        # One of them might indicate conflicts
        update_1_data = conflict_update_1.json()
        update_2_data = conflict_update_2.json()
        
        assert update_1_data['success'] is True
        assert update_2_data['success'] is True
    
    def test_template_application_workflow(
        self,
        test_client: TestClient,
        sample_test_data
    ):
        """Test template application workflow."""
        
        # Create project and assembly
        project_response = test_client.post("/api/projects", json={
            "name": "Template Test Project",
            "description": "Test template application features"
        })
        
        project_data = project_response.json()
        project_id = project_data['project']['id']
        
        # Create slides
        for slide_data in sample_test_data['slides'][:2]:
            test_client.post("/api/slides", json={
                **slide_data,
                "project_id": project_id
            })
        
        # Create assembly
        assembly_response = test_client.post("/api/assembly/manual", json={
            "name": "Template Test Assembly",
            "slides": [
                {"slide_id": sample_test_data['slides'][0]['id'], "title": sample_test_data['slides'][0]['title']},
                {"slide_id": sample_test_data['slides'][1]['id'], "title": sample_test_data['slides'][1]['title']}
            ],
            "project_id": project_id
        })
        
        assembly_data = assembly_response.json()
        assembly_id = assembly_data['assembly']['id']
        
        # Get available templates
        templates_response = test_client.get("/api/assembly/templates")
        assert templates_response.status_code == 200
        templates_data = templates_response.json()
        assert isinstance(templates_data, list)
        
        # If templates are available, test application
        if templates_data:
            template_id = templates_data[0]['id']
            
            # Apply template to assembly
            apply_response = test_client.post(f"/api/assembly/{assembly_id}/template", json={
                "template_id": template_id
            })
            
            assert apply_response.status_code == 200
            apply_data = apply_response.json()
            assert apply_data['success'] is True
            assert 'template_applied' in apply_data
            assert apply_data['template_applied'] == template_id
    
    @pytest.mark.asyncio
    async def test_performance_under_load(
        self,
        test_client: TestClient,
        mock_openai_client,
        performance_monitor
    ):
        """Test system performance under concurrent load."""
        
        # Create test project
        project_response = test_client.post("/api/projects", json={
            "name": "Load Test Project",
            "description": "Performance testing under load"
        })
        
        project_data = project_response.json()
        project_id = project_data['project']['id']
        
        # Create multiple slides for testing
        slide_ids = []
        for i in range(50):
            slide_response = test_client.post("/api/slides", json={
                "title": f"Load Test Slide {i}",
                "content_preview": f"Performance testing content for slide {i} with various keywords and data",
                "slide_type": "text",
                "project_id": project_id,
                "slide_number": i + 1,
                "keywords": [f"keyword_{i}", "performance", "load_test", "data"]
            })
            slide_ids.append(slide_response.json()['id'])
        
        # Test concurrent search operations
        search_queries = [
            "performance analysis data",
            "load test results",
            "keyword search functionality",
            "content analysis metrics",
            "slide performance data"
        ] * 4  # 20 total searches
        
        performance_monitor.start_timer("concurrent_searches")
        
        # Execute searches concurrently using asyncio
        async def perform_search(query: str, client: TestClient):
            import asyncio
            import time
            
            start_time = time.time()
            
            # Simulate async behavior with asyncio.sleep
            await asyncio.sleep(0.01)
            
            response = client.post("/api/search/natural-language", json={
                "query": query,
                "project_id": project_id
            })
            
            end_time = time.time()
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            
            return end_time - start_time
        
        # Run concurrent searches
        search_tasks = [perform_search(query, test_client) for query in search_queries]
        search_times = await asyncio.gather(*search_tasks)
        
        performance_monitor.end_timer("concurrent_searches")
        
        # Analyze performance results
        avg_search_time = sum(search_times) / len(search_times)
        max_search_time = max(search_times)
        min_search_time = min(search_times)
        
        # Performance assertions
        assert avg_search_time < 2.0, f"Average search time too high: {avg_search_time:.3f}s"
        assert max_search_time < 5.0, f"Maximum search time too high: {max_search_time:.3f}s"
        
        print(f"\nConcurrent Search Performance Results:")
        print(f"  Total searches: {len(search_times)}")
        print(f"  Average time: {avg_search_time:.3f}s")
        print(f"  Minimum time: {min_search_time:.3f}s")
        print(f"  Maximum time: {max_search_time:.3f}s")
        print(f"  95th percentile: {sorted(search_times)[int(len(search_times) * 0.95)]:.3f}s")
        
        # Test concurrent assembly creation
        performance_monitor.start_timer("concurrent_assemblies")
        
        async def create_assembly(name: str, slide_count: int):
            selected_slide_ids = slide_ids[:slide_count]
            response = test_client.post("/api/assembly/manual", json={
                "name": name,
                "slides": [{"slide_id": sid, "title": f"Slide {i}"} for i, sid in enumerate(selected_slide_ids)],
                "project_id": project_id,
                "optimize_order": True
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            return data['assembly']['id']
        
        # Create multiple assemblies concurrently
        assembly_tasks = [
            create_assembly(f"Concurrent Assembly {i}", min(10, len(slide_ids)))
            for i in range(5)
        ]
        
        assembly_ids = await asyncio.gather(*assembly_tasks)
        performance_monitor.end_timer("concurrent_assemblies")
        
        assert len(assembly_ids) == 5
        
        # Verify all assemblies were created successfully
        for assembly_id in assembly_ids:
            assert assembly_id is not None
        
        metrics = performance_monitor.get_metrics()
        performance_monitor.assert_performance("concurrent_searches", 10.0)  # All searches < 10s
        performance_monitor.assert_performance("concurrent_assemblies", 5.0)  # All assemblies < 5s