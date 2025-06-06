"""Base worker classes and utilities for consistent threading patterns."""

import logging
from typing import Optional, Any, Callable, Dict
from PySide6.QtCore import QRunnable, Signal, QObject, Slot

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    """Standard signals for worker threads."""
    
    started = Signal()
    finished = Signal()
    error = Signal(Exception)
    result = Signal(object)
    progress = Signal(int)  # Progress percentage 0-100
    message = Signal(str)   # Status message


class BaseWorker(QRunnable):
    """Base class for all worker threads with standard signal support.
    
    Provides:
    - Standard signals for communication
    - Error handling
    - Progress reporting
    - Result emission
    """
    
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self._is_cancelled = False
        
    def cancel(self):
        """Request cancellation of the worker."""
        self._is_cancelled = True
        
    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        return self._is_cancelled
    
    @Slot()
    def run(self):
        """Execute the worker task."""
        try:
            self.signals.started.emit()
            result = self.execute()
            if not self._is_cancelled:
                self.signals.result.emit(result)
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            self.signals.error.emit(e)
        finally:
            self.signals.finished.emit()
    
    def execute(self) -> Any:
        """Override this method to implement worker logic.
        
        Returns:
            Result of the operation
            
        Raises:
            Any exception will be caught and emitted via error signal
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def report_progress(self, value: int):
        """Report progress to listeners.
        
        Args:
            value: Progress percentage (0-100)
        """
        if 0 <= value <= 100:
            self.signals.progress.emit(value)
            
    def report_message(self, message: str):
        """Report status message to listeners.
        
        Args:
            message: Status message
        """
        self.signals.message.emit(message)


class FunctionWorker(BaseWorker):
    """Worker that executes a callable with arguments.
    
    Useful for quickly wrapping functions in a worker thread.
    """
    
    def __init__(
        self, 
        func: Callable,
        *args,
        **kwargs
    ):
        """Initialize the function worker.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        """
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
    def execute(self) -> Any:
        """Execute the stored function with its arguments."""
        return self.func(*self.args, **self.kwargs)


class BatchWorker(BaseWorker):
    """Worker for processing items in batches with progress reporting."""
    
    def __init__(
        self,
        items: list,
        process_func: Callable[[Any], Any],
        batch_size: int = 10
    ):
        """Initialize the batch worker.
        
        Args:
            items: List of items to process
            process_func: Function to process each item
            batch_size: Number of items to process before reporting progress
        """
        super().__init__()
        self.items = items
        self.process_func = process_func
        self.batch_size = batch_size
        
    def execute(self) -> list:
        """Process all items in batches."""
        results = []
        total = len(self.items)
        
        for i, item in enumerate(self.items):
            if self.is_cancelled:
                break
                
            result = self.process_func(item)
            results.append(result)
            
            # Report progress
            if (i + 1) % self.batch_size == 0 or i == total - 1:
                progress = int(((i + 1) / total) * 100)
                self.report_progress(progress)
                self.report_message(f"Processed {i + 1} of {total} items")
                
        return results


def create_worker(
    func: Callable,
    *args,
    on_success: Optional[Callable[[Any], None]] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
    on_finished: Optional[Callable[[], None]] = None,
    on_progress: Optional[Callable[[int], None]] = None,
    **kwargs
) -> FunctionWorker:
    """Create a worker with connected callbacks.
    
    Args:
        func: Function to execute in worker thread
        *args: Positional arguments for function
        on_success: Callback for successful completion
        on_error: Callback for errors
        on_finished: Callback when worker finishes (success or error)
        on_progress: Callback for progress updates
        **kwargs: Keyword arguments for function
        
    Returns:
        Configured worker ready to be added to thread pool
    """
    worker = FunctionWorker(func, *args, **kwargs)
    
    if on_success:
        worker.signals.result.connect(on_success)
    if on_error:
        worker.signals.error.connect(on_error)
    if on_finished:
        worker.signals.finished.connect(on_finished)
    if on_progress:
        worker.signals.progress.connect(on_progress)
        
    return worker


class WorkerManager:
    """Manager for tracking and cancelling active workers."""
    
    def __init__(self):
        self._workers: Dict[str, BaseWorker] = {}
        
    def add_worker(self, key: str, worker: BaseWorker):
        """Add a worker to track.
        
        Args:
            key: Unique identifier for the worker
            worker: Worker instance to track
        """
        # Cancel existing worker with same key
        if key in self._workers:
            self.cancel_worker(key)
            
        self._workers[key] = worker
        
        # Remove from tracking when finished
        worker.signals.finished.connect(lambda: self._remove_worker(key))
        
    def cancel_worker(self, key: str) -> bool:
        """Cancel a specific worker.
        
        Args:
            key: Identifier of worker to cancel
            
        Returns:
            True if worker was found and cancelled
        """
        if key in self._workers:
            self._workers[key].cancel()
            return True
        return False
        
    def cancel_all(self):
        """Cancel all active workers."""
        for worker in self._workers.values():
            worker.cancel()
            
    def _remove_worker(self, key: str):
        """Remove worker from tracking."""
        self._workers.pop(key, None)
        
    def is_active(self, key: str) -> bool:
        """Check if a worker is active.
        
        Args:
            key: Worker identifier
            
        Returns:
            True if worker exists and hasn't finished
        """
        return key in self._workers