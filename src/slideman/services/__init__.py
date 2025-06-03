"""
SLIDEMAN services package.

This package contains all business logic services including database operations,
file I/O, PowerPoint operations, and background tasks.
"""

# Export custom exceptions
from .exceptions import (
    SlidemanException,
    DatabaseError,
    ConnectionError,
    TransactionError,
    FileOperationError,
    FileNotFoundError,
    InsufficientSpaceError,
    PowerPointError,
    COMInitializationError,
    PresentationAccessError,
    SlideExportError,
    ResourceNotFoundError,
    ValidationError,
    DuplicateResourceError,
    ServiceNotAvailableError,
    OperationCancelledError,
    ThreadSafetyError,
)

# Export main services
from .database import Database
from .database_worker import DatabaseWorker
from .slide_converter import SlideConverter
from .export_service import ExportWorker
from .file_io import check_disk_space, calculate_checksum, copy_files_to_project
# Avoid circular import
# from .thumbnail_cache import ThumbnailCache
from .background_tasks import WorkerSignals, FileCopyWorker
from .keyword_tasks import FindSimilarKeywordsWorker, FindSimilarKeywordsSignals
from .service_registry import service_registry, ServiceRegistry
from .interfaces import (
    IDatabaseService, IProjectService, IFileService, ISlideService,
    IElementService, IKeywordService, ISlideKeywordService,
    IElementKeywordService, IFileIOService, IThumbnailCacheService,
    IExportService, ISlideConverterService
)

__all__ = [
    # Exceptions
    "SlidemanException",
    "DatabaseError",
    "ConnectionError",
    "TransactionError",
    "FileOperationError",
    "FileNotFoundError",
    "InsufficientSpaceError",
    "PowerPointError",
    "COMInitializationError",
    "PresentationAccessError",
    "SlideExportError",
    "ResourceNotFoundError",
    "ValidationError",
    "DuplicateResourceError",
    "ServiceNotAvailableError",
    "OperationCancelledError",
    "ThreadSafetyError",
    # Services
    "Database",
    "DatabaseWorker",
    "SlideConverter",
    "ExportWorker",
    "check_disk_space",
    "calculate_checksum",
    "copy_files_to_project",
    # "ThumbnailCache", # Commented out to avoid circular import
    "WorkerSignals",
    "FileCopyWorker",
    "FindSimilarKeywordsWorker",
    "FindSimilarKeywordsSignals",
    "ServiceRegistry",
    "service_registry",
    # Interfaces
    "IDatabaseService",
    "IProjectService",
    "IFileService",
    "ISlideService",
    "IElementService",
    "IKeywordService",
    "ISlideKeywordService",
    "IElementKeywordService",
    "IFileIOService",
    "IThumbnailCacheService",
    "IExportService",
    "ISlideConverterService",
]