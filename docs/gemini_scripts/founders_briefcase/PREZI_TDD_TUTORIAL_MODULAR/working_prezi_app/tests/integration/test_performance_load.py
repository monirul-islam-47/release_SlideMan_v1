"""
Performance and Load Testing for PrezI
Tests system performance under various load conditions
Based on CONSOLIDATED_FOUNDERS_BRIEFCASE.md specifications
"""

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

class TestPerformanceLoad:
    """Test system performance under load conditions."""
    
    @pytest.mark.performance
    def test_database_query_performance_large_dataset(
        self,
        test_db_session,
        performance_monitor
    ):
        """Test database query performance with large datasets."""
        from services.database_service import DatabaseService
        
        db_service = DatabaseService(test_db_session)
        
        # Create large dataset
        performance_monitor.start_timer("create_large_dataset")
        
        # Create project
        project = db_service.create_project_sync(
            name="Performance Test Project",
            description="Large dataset for performance testing"
        )
        
        # Create many slides (simulate large presentation library)
        slide_count = 1000
        keyword_count = 500
        
        # Batch create slides
        slides = []
        for i in range(slide_count):
            slide = db_service.create_slide_sync(
                project_id=project['id'],
                slide_number=i + 1,
                title=f"Performance Test Slide {i:04d}",
                content=f"Content for performance testing slide {i}. This slide contains various keywords and metadata for search testing.",
                slide_type=["chart", "table", "text", "title", "conclusion"][i % 5]
            )
            slides.append(slide)
            
            # Add keywords to some slides
            if i % 10 == 0:  # Every 10th slide gets keywords
                for j in range(min(5, keyword_count)):
                    keyword_name = f"keyword_{j}"
                    keyword = db_service.create_or_get_keyword_sync(name=keyword_name)
                    db_service.add_keyword_to_slide_sync(slide['id'], keyword['id'])
        
        performance_monitor.end_timer("create_large_dataset")
        
        # Test query performance
        performance_monitor.start_timer("query_all_slides")
        all_slides = db_service.get_project_slides_sync(project['id'])
        performance_monitor.end_timer("query_all_slides")
        
        assert len(all_slides) == slide_count
        
        # Test search performance
        performance_monitor.start_timer("search_slides")
        search_results = db_service.search_slides_sync(
            project_id=project['id'],
            query="performance"
        )
        performance_monitor.end_timer("search_slides")
        
        assert len(search_results) > 0
        
        # Test keyword lookup performance
        performance_monitor.start_timer("keyword_lookup")
        slides_with_keywords = []
        for slide in slides[:100]:  # Test first 100 slides
            slide_keywords = db_service.get_slide_keywords_sync(slide['id'])
            if slide_keywords:
                slides_with_keywords.append(slide)
        performance_monitor.end_timer("keyword_lookup")
        
        # Performance assertions
        metrics = performance_monitor.get_metrics()
        performance_monitor.assert_performance("create_large_dataset", 60.0)  # Dataset creation < 60s
        performance_monitor.assert_performance("query_all_slides", 2.0)      # Query all slides < 2s
        performance_monitor.assert_performance("search_slides", 1.0)         # Search < 1s
        performance_monitor.assert_performance("keyword_lookup", 5.0)        # Keyword lookup < 5s
        
        print(f"\nDatabase Performance Results (n={slide_count}):")
        for operation, duration in metrics.items():
            if operation.startswith(('query', 'search', 'keyword')):
                print(f"  {operation}: {duration:.3f}s")
    
    @pytest.mark.performance
    def test_concurrent_search_performance(
        self,
        test_client,
        sample_test_data,
        performance_monitor
    ):
        """Test search performance under concurrent load."""
        
        # Setup test data
        project_response = test_client.post("/api/projects", json={
            "name": "Concurrent Search Test",
            "description": "Performance testing for concurrent searches"
        })
        project_id = project_response.json()['project']['id']
        
        # Create multiple slides for testing
        slide_ids = []
        for i in range(200):
            slide_response = test_client.post("/api/slides", json={
                "title": f"Concurrent Test Slide {i:03d}",
                "content_preview": f"Performance testing content for slide {i} with keywords like revenue, analysis, growth, market, customer, financial, strategic, data, metrics, performance",
                "slide_type": ["chart", "table", "text", "title", "conclusion"][i % 5],
                "project_id": project_id,
                "slide_number": i + 1,
                "keywords": [f"keyword_{i%20}", "performance", "test", "concurrent"]
            })
            slide_ids.append(slide_response.json()['id'])
        
        # Define search queries with varying complexity
        search_queries = [
            "revenue growth analysis",
            "financial performance metrics",
            "customer satisfaction data",
            "market analysis charts",
            "strategic planning overview",
            "data visualization dashboard",
            "quarterly performance review",
            "competitive analysis study",
            "operational efficiency metrics",
            "business intelligence reporting"
        ]
        
        # Test with different concurrency levels
        concurrency_levels = [5, 10, 20, 30]
        results = {}
        
        for concurrency in concurrency_levels:
            performance_monitor.start_timer(f"concurrent_search_{concurrency}")
            
            # Prepare concurrent search tasks
            queries_to_run = (search_queries * (concurrency // len(search_queries) + 1))[:concurrency]
            
            def perform_search(query: str) -> Dict[str, Any]:
                start_time = time.time()
                
                response = test_client.post("/api/search/natural-language", json={
                    "query": query,
                    "project_id": project_id,
                    "filters": {
                        "limit": 20,
                        "include_ai_analysis": True
                    }
                })
                
                end_time = time.time()
                
                assert response.status_code == 200
                data = response.json()
                assert data['success'] is True
                
                return {
                    'query': query,
                    'duration': end_time - start_time,
                    'results_count': data['total_results'],
                    'search_time_ms': data.get('search_time_ms', 0)
                }
            
            # Execute concurrent searches using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                search_results = list(executor.map(perform_search, queries_to_run))
            
            performance_monitor.end_timer(f"concurrent_search_{concurrency}")
            
            # Analyze results
            durations = [result['duration'] for result in search_results]
            
            results[concurrency] = {
                'total_searches': len(search_results),
                'avg_duration': statistics.mean(durations),
                'median_duration': statistics.median(durations),
                'max_duration': max(durations),
                'min_duration': min(durations),
                'percentile_95': sorted(durations)[int(len(durations) * 0.95)],
                'successful_searches': len([r for r in search_results if r['results_count'] > 0])
            }
            
            # Performance assertions for each concurrency level
            assert results[concurrency]['avg_duration'] < 3.0, f"Average search time too high at concurrency {concurrency}"
            assert results[concurrency]['max_duration'] < 10.0, f"Maximum search time too high at concurrency {concurrency}"
            assert results[concurrency]['successful_searches'] == concurrency, f"Not all searches successful at concurrency {concurrency}"
        
        # Print performance summary
        print(f"\nConcurrent Search Performance Results:")
        print(f"{'Concurrency':<12} {'Avg Time':<10} {'Max Time':<10} {'95th %ile':<10} {'Success Rate':<12}")
        print("-" * 60)
        
        for concurrency, metrics in results.items():
            success_rate = metrics['successful_searches'] / metrics['total_searches'] * 100
            print(f"{concurrency:<12} {metrics['avg_duration']:<10.3f} {metrics['max_duration']:<10.3f} "
                  f"{metrics['percentile_95']:<10.3f} {success_rate:<12.1f}%")
        
        # Verify performance doesn't degrade significantly with increased concurrency
        avg_times = [results[c]['avg_duration'] for c in concurrency_levels]
        performance_degradation = (max(avg_times) - min(avg_times)) / min(avg_times)
        assert performance_degradation < 1.0, f"Performance degradation too high: {performance_degradation:.2%}"
    
    @pytest.mark.performance
    def test_file_upload_processing_performance(
        self,
        test_client,
        mock_powerpoint_service,
        performance_monitor
    ):
        """Test file upload and processing performance."""
        import tempfile
        from pathlib import Path
        
        # Create test project
        project_response = test_client.post("/api/projects", json={
            "name": "File Processing Performance Test",
            "description": "Test file processing performance"
        })
        project_id = project_response.json()['project']['id']
        
        # Test different file sizes
        file_sizes = [
            (1024 * 100, "small"),      # 100KB
            (1024 * 500, "medium"),     # 500KB  
            (1024 * 1024, "large"),     # 1MB
            (1024 * 1024 * 5, "xlarge") # 5MB
        ]
        
        upload_results = {}
        
        for file_size, size_label in file_sizes:
            performance_monitor.start_timer(f"upload_{size_label}")
            
            # Create temporary file of specified size
            mock_content = b'Mock PowerPoint content for performance testing. ' * (file_size // 50)
            mock_content = mock_content[:file_size]  # Ensure exact size
            
            with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as tmp_file:
                tmp_file.write(mock_content)
                tmp_file.seek(0)
                
                files = {
                    "file": (f"performance_test_{size_label}.pptx", tmp_file, 
                            "application/vnd.openxmlformats-officedocument.presentationml.presentation")
                }
                data = {"project_id": project_id}
                
                # Upload file
                upload_start = time.time()
                upload_response = test_client.post("/api/files/upload", files=files, data=data)
                upload_end = time.time()
                
                # Clean up temp file
                Path(tmp_file.name).unlink(missing_ok=True)
            
            performance_monitor.end_timer(f"upload_{size_label}")
            
            assert upload_response.status_code == 200
            upload_data = upload_response.json()
            assert upload_data['success'] is True
            
            file_id = upload_data['file_id']
            
            # Check processing status
            performance_monitor.start_timer(f"processing_{size_label}")
            status_response = test_client.get(f"/api/files/{file_id}/status")
            performance_monitor.end_timer(f"processing_{size_label}")
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            upload_results[size_label] = {
                'file_size_bytes': file_size,
                'file_size_mb': file_size / (1024 * 1024),
                'upload_time': upload_end - upload_start,
                'processing_status': status_data['status'],
                'slides_processed': status_data.get('slides_processed', 0),
                'processing_time_ms': status_data.get('processing_time_ms', 0)
            }
        
        # Performance assertions
        for size_label, metrics in upload_results.items():
            file_size_mb = metrics['file_size_mb']
            
            # Upload time should be reasonable (< 2s per MB)
            max_upload_time = max(2.0, file_size_mb * 2.0)
            assert metrics['upload_time'] < max_upload_time, \
                f"Upload time too high for {size_label}: {metrics['upload_time']:.3f}s"
            
            # Processing should complete
            assert metrics['processing_status'] == 'completed'
            assert metrics['slides_processed'] > 0
        
        # Print upload performance summary
        print(f"\nFile Upload Performance Results:")
        print(f"{'Size':<8} {'Size (MB)':<10} {'Upload Time':<12} {'Slides':<8} {'Process Time':<14}")
        print("-" * 60)
        
        for size_label, metrics in upload_results.items():
            print(f"{size_label:<8} {metrics['file_size_mb']:<10.2f} {metrics['upload_time']:<12.3f} "
                  f"{metrics['slides_processed']:<8} {metrics['processing_time_ms']:<14}")
    
    @pytest.mark.performance 
    def test_assembly_creation_performance(
        self,
        test_client,
        mock_openai_client,
        performance_monitor
    ):
        """Test assembly creation performance with varying slide counts."""
        
        # Create test project
        project_response = test_client.post("/api/projects", json={
            "name": "Assembly Performance Test",
            "description": "Test assembly creation performance"
        })
        project_id = project_response.json()['project']['id']
        
        # Create slides for testing
        all_slides = []
        for i in range(100):
            slide_response = test_client.post("/api/slides", json={
                "title": f"Assembly Performance Slide {i:03d}",
                "content_preview": f"Content for assembly performance testing slide {i}",
                "slide_type": ["chart", "table", "text", "title", "conclusion"][i % 5],
                "project_id": project_id,
                "slide_number": i + 1
            })
            all_slides.append(slide_response.json())
        
        # Test assembly creation with different slide counts
        slide_counts = [5, 10, 25, 50, 100]
        assembly_results = {}
        
        for slide_count in slide_counts:
            performance_monitor.start_timer(f"assembly_creation_{slide_count}")
            
            selected_slides = all_slides[:slide_count]
            
            # Test manual assembly creation
            manual_start = time.time()
            manual_response = test_client.post("/api/assembly/manual", json={
                "name": f"Manual Assembly {slide_count} slides",
                "slides": [{"slide_id": slide['id'], "title": slide['title']} 
                          for slide in selected_slides],
                "project_id": project_id,
                "optimize_order": True
            })
            manual_end = time.time()
            
            assert manual_response.status_code == 200
            manual_data = manual_response.json()
            assert manual_data['success'] is True
            
            manual_assembly_id = manual_data['assembly']['id']
            
            # Test AI assembly optimization
            optimization_start = time.time()
            optimization_response = test_client.post(f"/api/assembly/{manual_assembly_id}/optimize", json={
                "optimization_goals": ["logical_flow", "audience_engagement"]
            })
            optimization_end = time.time()
            
            assert optimization_response.status_code == 200
            optimization_data = optimization_response.json()
            assert optimization_data['success'] is True
            
            # Test AI-automated assembly creation
            ai_start = time.time()
            ai_response = test_client.post("/api/assembly/ai-automated", json={
                "intent": f"Create a comprehensive presentation using {slide_count} slides covering key business metrics and strategic insights",
                "project_id": project_id,
                "user_preferences": {
                    "duration": min(30, slide_count * 2),
                    "style": "professional"
                }
            })
            ai_end = time.time()
            
            assert ai_response.status_code == 200
            ai_data = ai_response.json()
            assert ai_data['success'] is True
            
            performance_monitor.end_timer(f"assembly_creation_{slide_count}")
            
            assembly_results[slide_count] = {
                'manual_creation_time': manual_end - manual_start,
                'optimization_time': optimization_end - optimization_start,
                'ai_creation_time': ai_end - ai_start,
                'total_time': (manual_end - manual_start) + (optimization_end - optimization_start) + (ai_end - ai_start),
                'slides_count': slide_count
            }
        
        # Performance assertions
        for slide_count, metrics in assembly_results.items():
            # Manual assembly creation should be fast
            assert metrics['manual_creation_time'] < 2.0, \
                f"Manual assembly creation too slow for {slide_count} slides"
            
            # Optimization should complete reasonably quickly
            max_optimization_time = max(3.0, slide_count * 0.1)
            assert metrics['optimization_time'] < max_optimization_time, \
                f"Assembly optimization too slow for {slide_count} slides"
            
            # AI creation should scale reasonably
            max_ai_time = max(5.0, slide_count * 0.2)
            assert metrics['ai_creation_time'] < max_ai_time, \
                f"AI assembly creation too slow for {slide_count} slides"
        
        # Print assembly performance summary
        print(f"\nAssembly Creation Performance Results:")
        print(f"{'Slides':<8} {'Manual':<10} {'Optimize':<10} {'AI Create':<10} {'Total':<10}")
        print("-" * 55)
        
        for slide_count, metrics in assembly_results.items():
            print(f"{slide_count:<8} {metrics['manual_creation_time']:<10.3f} "
                  f"{metrics['optimization_time']:<10.3f} {metrics['ai_creation_time']:<10.3f} "
                  f"{metrics['total_time']:<10.3f}")
    
    @pytest.mark.performance
    def test_export_performance(
        self,
        test_client,
        mock_powerpoint_service,
        performance_monitor
    ):
        """Test export performance for different formats and assembly sizes."""
        
        # Create test project and slides
        project_response = test_client.post("/api/projects", json={
            "name": "Export Performance Test",
            "description": "Test export performance across formats"
        })
        project_id = project_response.json()['project']['id']
        
        # Create slides
        slides = []
        for i in range(50):
            slide_response = test_client.post("/api/slides", json={
                "title": f"Export Test Slide {i:03d}",
                "content_preview": f"Content for export performance testing slide {i}",
                "slide_type": "text",
                "project_id": project_id,
                "slide_number": i + 1
            })
            slides.append(slide_response.json())
        
        # Test export performance for different assembly sizes and formats
        slide_counts = [5, 15, 30, 50]
        export_formats = ['pptx', 'pdf', 'html']
        export_results = {}
        
        for slide_count in slide_counts:
            # Create assembly
            selected_slides = slides[:slide_count]
            assembly_response = test_client.post("/api/assembly/manual", json={
                "name": f"Export Test Assembly {slide_count}",
                "slides": [{"slide_id": slide['id'], "title": slide['title']} 
                          for slide in selected_slides],
                "project_id": project_id
            })
            
            assembly_id = assembly_response.json()['assembly']['id']
            export_results[slide_count] = {}
            
            for export_format in export_formats:
                performance_monitor.start_timer(f"export_{export_format}_{slide_count}")
                
                export_start = time.time()
                export_response = test_client.post(f"/api/assembly/{assembly_id}/export", json={
                    "format": export_format,
                    "options": {
                        "quality": "high",
                        "include_notes": True if export_format == 'pptx' else False,
                        "interactive": True if export_format == 'html' else False
                    }
                })
                export_end = time.time()
                
                performance_monitor.end_timer(f"export_{export_format}_{slide_count}")
                
                assert export_response.status_code == 200
                export_data = export_response.json()
                assert export_data['success'] is True
                
                export_results[slide_count][export_format] = {
                    'export_time': export_end - export_start,
                    'file_size_mb': export_data.get('file_size_mb', 0),
                    'export_time_ms': export_data.get('export_time_ms', 0)
                }
        
        # Performance assertions
        for slide_count in slide_counts:
            for export_format, metrics in export_results[slide_count].items():
                # Export time should scale reasonably with slide count
                max_export_time = max(10.0, slide_count * 0.5)  # 0.5s per slide max
                
                assert metrics['export_time'] < max_export_time, \
                    f"{export_format} export too slow for {slide_count} slides: {metrics['export_time']:.3f}s"
        
        # Print export performance summary
        print(f"\nExport Performance Results:")
        print(f"{'Slides':<8} {'Format':<6} {'Time (s)':<10} {'Size (MB)':<12}")
        print("-" * 40)
        
        for slide_count in slide_counts:
            for export_format, metrics in export_results[slide_count].items():
                print(f"{slide_count:<8} {export_format:<6} {metrics['export_time']:<10.3f} "
                      f"{metrics['file_size_mb']:<12.2f}")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(
        self,
        test_client,
        performance_monitor
    ):
        """Test memory usage under sustained load."""
        import psutil
        import os
        
        # Get current process
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create test project
        project_response = test_client.post("/api/projects", json={
            "name": "Memory Test Project",
            "description": "Test memory usage under load"
        })
        project_id = project_response.json()['project']['id']
        
        # Create many slides to simulate memory pressure
        performance_monitor.start_timer("memory_load_test")
        
        for batch in range(10):  # 10 batches of 50 slides = 500 total
            # Create batch of slides
            for i in range(50):
                slide_num = batch * 50 + i
                test_client.post("/api/slides", json={
                    "title": f"Memory Test Slide {slide_num:04d}",
                    "content_preview": f"Large content for memory testing " * 100,  # Larger content
                    "slide_type": "text",
                    "project_id": project_id,
                    "slide_number": slide_num + 1,
                    "keywords": [f"memory_{j}" for j in range(10)]  # Multiple keywords
                })
            
            # Perform search operations to exercise memory
            for query_num in range(10):
                test_client.post("/api/search/natural-language", json={
                    "query": f"memory test query {query_num}",
                    "project_id": project_id
                })
            
            # Check memory usage
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            # Memory usage shouldn't grow excessively
            max_memory_increase = 500  # 500MB max increase
            assert memory_increase < max_memory_increase, \
                f"Memory usage increased too much: {memory_increase:.1f}MB"
            
            # Brief pause to allow garbage collection
            await asyncio.sleep(0.1)
        
        performance_monitor.end_timer("memory_load_test")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_increase = final_memory - initial_memory
        
        print(f"\nMemory Usage Results:")
        print(f"  Initial memory: {initial_memory:.1f} MB")
        print(f"  Final memory: {final_memory:.1f} MB")
        print(f"  Total increase: {total_memory_increase:.1f} MB")
        print(f"  Operations completed: 500 slides created, 100 searches performed")
        
        # Final memory assertion
        assert total_memory_increase < 300, \
            f"Total memory increase too high: {total_memory_increase:.1f}MB"