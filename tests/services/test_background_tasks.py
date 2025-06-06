"""
Unit tests for background tasks and workers.
"""
from unittest.mock import Mock, patch, MagicMock
import time

import pytest
from PySide6.QtCore import QObject, Signal, QThread

from slideman.services.background_tasks import BackgroundTaskManager
from slideman.services.database_worker import DatabaseWorker
from slideman.services.keyword_tasks import MergeKeywordsTask


class TestBackgroundTaskManager:
    """Test suite for BackgroundTaskManager."""

    @pytest.fixture
    def manager(self, qapp):
        """Create BackgroundTaskManager instance."""
        return BackgroundTaskManager()

    def test_initialization(self, manager):
        """Test manager initialization."""
        assert manager._thread_pool is not None
        assert manager._active_workers == []
        assert hasattr(manager, 'logger')

    def test_submit_task(self, manager):
        """Test submitting a task."""
        # Create a mock task
        task = Mock()
        task.run = Mock()
        
        # Submit task
        worker = manager.submit_task(task, "Test Task")
        
        assert worker is not None
        assert worker in manager._active_workers

    def test_submit_function(self, manager):
        """Test submitting a function."""
        result_holder = []
        
        def test_function(x, y):
            result_holder.append(x + y)
            return x + y
        
        worker = manager.submit_function(test_function, "Add Numbers", 5, 3)
        
        # Give it time to execute
        worker.wait(1000)
        
        assert len(result_holder) == 1
        assert result_holder[0] == 8

    def test_worker_cleanup(self, manager):
        """Test worker cleanup after completion."""
        def quick_task():
            return "done"
        
        worker = manager.submit_function(quick_task, "Quick Task")
        
        # Wait for completion
        worker.wait(1000)
        time.sleep(0.1)  # Give cleanup time to run
        
        # Worker should be removed from active list
        assert worker not in manager._active_workers

    def test_cancel_all_tasks(self, manager):
        """Test cancelling all active tasks."""
        # Submit multiple long-running tasks
        def long_task():
            time.sleep(5)
        
        workers = []
        for i in range(3):
            worker = manager.submit_function(long_task, f"Task {i}")
            workers.append(worker)
        
        # Cancel all
        manager.cancel_all_tasks()
        
        # All workers should be terminated
        for worker in workers:
            assert not worker.isRunning()
        
        assert len(manager._active_workers) == 0

    def test_get_active_task_count(self, manager):
        """Test getting active task count."""
        assert manager.get_active_task_count() == 0
        
        # Submit tasks
        def task():
            time.sleep(0.5)
        
        for i in range(3):
            manager.submit_function(task, f"Task {i}")
        
        assert manager.get_active_task_count() == 3

    def test_wait_for_all_tasks(self, manager):
        """Test waiting for all tasks to complete."""
        completed = []
        
        def task(n):
            time.sleep(0.1)
            completed.append(n)
        
        # Submit tasks
        for i in range(3):
            manager.submit_function(task, f"Task {i}", i)
        
        # Wait for all
        all_completed = manager.wait_for_all_tasks(timeout=2000)
        
        assert all_completed is True
        assert len(completed) == 3
        assert manager.get_active_task_count() == 0

    def test_task_error_handling(self, manager):
        """Test error handling in tasks."""
        error_signal_received = []
        
        def failing_task():
            raise ValueError("Task failed!")
        
        worker = manager.submit_function(failing_task, "Failing Task")
        
        # Connect to error signal
        worker.error.connect(lambda e: error_signal_received.append(e))
        
        # Wait for completion
        worker.wait(1000)
        time.sleep(0.1)
        
        assert len(error_signal_received) == 1
        assert "Task failed!" in error_signal_received[0]

    def test_max_thread_count(self, manager):
        """Test thread pool max thread count configuration."""
        # Set max threads
        manager.set_max_thread_count(2)
        
        # Submit more tasks than max threads
        running_count = []
        
        def count_task():
            running_count.append(1)
            time.sleep(0.5)
            running_count.pop()
        
        for i in range(5):
            manager.submit_function(count_task, f"Task {i}")
        
        time.sleep(0.1)
        
        # Should not exceed max thread count
        assert len(running_count) <= 2


class TestDatabaseWorker:
    """Test suite for DatabaseWorker."""

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = Mock()
        db.get_project.return_value = Mock(id=1, name="Test Project")
        db.create_slide.return_value = Mock(id=1)
        return db

    def test_worker_initialization(self, mock_db_service):
        """Test worker initialization."""
        def task(db):
            return db.get_project(1)
        
        worker = DatabaseWorker(task, mock_db_service)
        
        assert worker._task == task
        assert worker._db_service == mock_db_service

    def test_worker_successful_execution(self, mock_db_service, qapp):
        """Test successful task execution."""
        result_received = []
        
        def task(db):
            return db.get_project(1)
        
        worker = DatabaseWorker(task, mock_db_service)
        worker.result.connect(lambda r: result_received.append(r))
        
        worker.run()
        
        assert len(result_received) == 1
        assert result_received[0].name == "Test Project"

    def test_worker_error_handling(self, mock_db_service, qapp):
        """Test error handling in worker."""
        error_received = []
        
        def failing_task(db):
            raise ValueError("Database error")
        
        worker = DatabaseWorker(failing_task, mock_db_service)
        worker.error.connect(lambda e: error_received.append(e))
        
        worker.run()
        
        assert len(error_received) == 1
        assert "Database error" in error_received[0]

    def test_worker_with_complex_task(self, mock_db_service, qapp):
        """Test worker with complex database operations."""
        def complex_task(db):
            # Simulate multiple DB operations
            project = db.get_project(1)
            slides = []
            for i in range(3):
                slide = db.create_slide(
                    file_id=1,
                    slide_number=i+1,
                    title=f"Slide {i+1}"
                )
                slides.append(slide)
            return {'project': project, 'slides': slides}
        
        worker = DatabaseWorker(complex_task, mock_db_service)
        result_received = []
        worker.result.connect(lambda r: result_received.append(r))
        
        worker.run()
        
        assert len(result_received) == 1
        assert 'project' in result_received[0]
        assert 'slides' in result_received[0]
        assert len(result_received[0]['slides']) == 3


class TestMergeKeywordsTask:
    """Test suite for MergeKeywordsTask."""

    @pytest.fixture
    def mock_db_service(self):
        """Create mock database service."""
        db = Mock()
        
        # Mock keyword operations
        db.get_keyword_by_name.side_effect = lambda name: {
            'old_tag': Mock(id=1, name='old_tag'),
            'new_tag': Mock(id=2, name='new_tag')
        }.get(name)
        
        db.get_slides_with_keyword.return_value = [1, 2, 3]
        db.get_elements_with_keyword.return_value = [4, 5]
        db.add_slide_keyword.return_value = None
        db.add_element_keyword.return_value = None
        db.remove_slide_keyword.return_value = None
        db.remove_element_keyword.return_value = None
        db.delete_keyword.return_value = None
        
        return db

    def test_merge_task_initialization(self, mock_db_service):
        """Test merge task initialization."""
        task = MergeKeywordsTask('old_tag', 'new_tag', mock_db_service)
        
        assert task.old_keyword_name == 'old_tag'
        assert task.new_keyword_name == 'new_tag'
        assert task.db == mock_db_service

    def test_merge_task_execution(self, mock_db_service, qapp):
        """Test successful keyword merge."""
        task = MergeKeywordsTask('old_tag', 'new_tag', mock_db_service)
        
        progress_updates = []
        task.progress.connect(lambda p, m: progress_updates.append((p, m)))
        
        task.run()
        
        # Verify operations
        assert mock_db_service.get_slides_with_keyword.called
        assert mock_db_service.get_elements_with_keyword.called
        assert mock_db_service.add_slide_keyword.call_count == 3  # 3 slides
        assert mock_db_service.add_element_keyword.call_count == 2  # 2 elements
        assert mock_db_service.delete_keyword.called
        
        # Check progress updates
        assert len(progress_updates) > 0
        assert progress_updates[-1][0] == 100  # Final progress should be 100%

    def test_merge_task_error_handling(self, mock_db_service, qapp):
        """Test error handling during merge."""
        mock_db_service.get_keyword_by_name.side_effect = Exception("Database error")
        
        task = MergeKeywordsTask('old_tag', 'new_tag', mock_db_service)
        
        error_received = []
        task.error.connect(lambda e: error_received.append(e))
        
        task.run()
        
        assert len(error_received) == 1
        assert "Database error" in error_received[0]

    def test_merge_task_with_conflicts(self, mock_db_service, qapp):
        """Test merging when target keyword already exists on items."""
        # Mock that some slides already have the new keyword
        mock_db_service.add_slide_keyword.side_effect = [None, Exception("Duplicate"), None]
        
        task = MergeKeywordsTask('old_tag', 'new_tag', mock_db_service)
        
        # Should handle duplicates gracefully
        task.run()
        
        # Should still complete the merge
        assert mock_db_service.delete_keyword.called