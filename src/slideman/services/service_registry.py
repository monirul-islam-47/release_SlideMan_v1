"""
Service Registry for dependency injection.

This module provides a centralized registry for managing service instances
and their dependencies throughout the application. It replaces the singleton
pattern with proper dependency injection.
"""

import logging
from typing import Any, Dict, Optional, Type, Callable
from pathlib import Path

from .database import Database
# Import specific functions from file_io instead of non-existent FileIO class
from .file_io import check_disk_space, calculate_checksum, copy_files_to_project
# Avoid circular import with thumbnail_cache
# from .thumbnail_cache import ThumbnailCache
# Import actual classes from background_tasks
from .background_tasks import WorkerSignals, FileCopyWorker
from .slide_converter import SlideConverter
# ExportService doesn't exist, only ExportWorker
from .export_service import ExportWorker


class ServiceRegistry:
    """
    Central registry for managing service instances.
    
    This class provides:
    - Service registration and retrieval
    - Lazy initialization of services
    - Dependency resolution
    - Service lifecycle management
    """
    
    def __init__(self):
        """Initialize the service registry."""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._initializing: set = set()  # Track services being initialized to prevent circular deps
        self.logger = logging.getLogger(__name__)
        
    def register_service(self, name: str, service: Any) -> None:
        """
        Register a service instance.
        
        Args:
            name: Unique name for the service
            service: The service instance
        """
        self._services[name] = service
        self.logger.debug(f"Registered service: {name}")
        
    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        """
        Register a factory function for lazy service creation.
        
        Args:
            name: Unique name for the service
            factory: Callable that creates the service instance
        """
        self._factories[name] = factory
        self.logger.debug(f"Registered factory for service: {name}")
        
    def get(self, name: str) -> Optional[Any]:
        """
        Get a service by name, creating it if necessary.
        
        Args:
            name: Name of the service to retrieve
            
        Returns:
            The service instance or None if not found
        """
        # Return existing service
        if name in self._services:
            return self._services[name]
            
        # Check for circular dependency
        if name in self._initializing:
            self.logger.error(f"Circular dependency detected for service: {name}")
            return None
            
        # Try to create from factory
        if name in self._factories:
            self.logger.debug(f"Creating service from factory: {name}")
            self._initializing.add(name)
            try:
                service = self._factories[name]()
                self._services[name] = service
                return service
            except Exception as e:
                self.logger.error(f"Error creating service {name}: {e}", exc_info=True)
                return None
            finally:
                self._initializing.discard(name)
                
        self.logger.warning(f"Service not found: {name}")
        return None
        
    def get_required(self, name: str) -> Any:
        """
        Get a required service by name.
        
        Args:
            name: Name of the service to retrieve
            
        Returns:
            The service instance
            
        Raises:
            ValueError: If the service is not found
        """
        service = self.get(name)
        if service is None:
            raise ValueError(f"Required service not found: {name}")
        return service
        
    def has_service(self, name: str) -> bool:
        """
        Check if a service is registered.
        
        Args:
            name: Name of the service
            
        Returns:
            True if the service is registered
        """
        return name in self._services or name in self._factories
        
    def remove_service(self, name: str) -> None:
        """
        Remove a service from the registry.
        
        Args:
            name: Name of the service to remove
        """
        self._services.pop(name, None)
        self._factories.pop(name, None)
        self.logger.debug(f"Removed service: {name}")
        
    def clear(self) -> None:
        """Clear all services from the registry."""
        # Clean up services that have cleanup methods
        for name, service in self._services.items():
            if hasattr(service, 'cleanup'):
                try:
                    service.cleanup()
                    self.logger.debug(f"Cleaned up service: {name}")
                except Exception as e:
                    self.logger.error(f"Error cleaning up service {name}: {e}", exc_info=True)
                    
        self._services.clear()
        self._factories.clear()
        self._initializing.clear()
        self.logger.info("Service registry cleared")
        
    def create_default_services(self, db_path: Path, app_data_dir: Path) -> None:
        """
        Create and register default services.
        
        Args:
            db_path: Path to the database file
            app_data_dir: Path to the application data directory
        """
        # Register core services
        self.register_factory("database", lambda: Database(db_path))
        
        # Register file_io functions directly
        self.register_service("check_disk_space", check_disk_space)
        self.register_service("calculate_checksum", calculate_checksum)
        self.register_service("copy_files_to_project", copy_files_to_project)
        
        # Avoid ThumbnailCache circular import - will be handled elsewhere
        # Try to get the thumbnail_cache from module-level instance
        try:
            from .thumbnail_cache import thumbnail_cache
            self.register_service("thumbnail_cache", thumbnail_cache)
        except ImportError as e:
            self.logger.warning(f"Could not import thumbnail_cache: {e}")
        
        # Register worker classes
        self.register_service("worker_signals", WorkerSignals)
        self.register_factory("file_copy_worker", lambda: FileCopyWorker)
        
        # Register service classes (not instances)
        self.register_service("slide_converter", SlideConverter)
        self.register_service("export_worker", ExportWorker)
        
        self.logger.info("Default services registered")
        
    def get_services_for_presenter(self, presenter_name: str) -> Dict[str, Any]:
        """
        Get services required by a specific presenter.
        
        Args:
            presenter_name: Name of the presenter
            
        Returns:
            Dictionary of services needed by the presenter
        """
        # Define service requirements for each presenter
        requirements = {
            "ProjectsPresenter": [
                "database", "file_io", "background_tasks", 
                "slide_converter", "app_state", "undo_stack",
                "thread_pool", "delete_project_cmd", "rename_project_cmd"
            ],
            "SlideViewPresenter": [
                "database", "thumbnail_cache", "app_state", 
                "undo_stack"
            ],
            "AssemblyPresenter": [
                "database", "thumbnail_cache", "app_state"
            ],
            "DeliveryPresenter": [
                "database", "export_service", "app_state",
                "thread_pool"
            ],
            "KeywordManagerPresenter": [
                "database", "app_state", "undo_stack"
            ]
        }
        
        required_services = requirements.get(presenter_name, [])
        services = {}
        
        for service_name in required_services:
            service = self.get(service_name)
            if service:
                services[service_name] = service
            else:
                self.logger.warning(f"Service {service_name} not available for {presenter_name}")
                
        return services


# Global service registry instance
service_registry = ServiceRegistry()