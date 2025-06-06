"""
Presenter for the Projects page following the MVP pattern.

This presenter handles all business logic for project management, including:
- Creating new projects
- Loading existing projects
- Converting PowerPoint files
- Managing project operations
"""

from abc import abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Any
from PySide6.QtCore import Signal

from .base_presenter import BasePresenter, IView
from ..models.project import Project
from ..models.file import File
from ..services.exceptions import (
    DatabaseError, ResourceNotFoundError, DuplicateResourceError,
    ValidationError, FileOperationError
)


class IProjectsView(IView):
    """
    Interface for the Projects view.
    
    This interface extends IView with specific methods needed by the Projects page.
    """
    
    @abstractmethod
    def show_project_list(self, projects: List[Project]) -> None:
        """Display the list of projects."""
        pass
    
    @abstractmethod
    def show_project_details(self, project: Project) -> None:
        """Display details for a specific project."""
        pass
    
    @abstractmethod
    def update_conversion_progress(self, file_id: int, current: int, total: int) -> None:
        """Update the progress of slide conversion for a file."""
        pass
    
    @abstractmethod
    def clear_project_selection(self) -> None:
        """Clear the current project selection."""
        pass
    
    @abstractmethod
    def get_new_project_info(self) -> Optional[tuple[str, List[Path]]]:
        """
        Get information for creating a new project from the user.
        
        Returns:
            Tuple of (project_name, selected_files) or None if cancelled
        """
        pass
    
    @abstractmethod
    def get_rename_input(self, current_name: str) -> Optional[str]:
        """
        Get a new name for renaming a project.
        
        Args:
            current_name: The current project name
            
        Returns:
            The new name or None if cancelled
        """
        pass
    
    @abstractmethod
    def confirm_delete(self, project_name: str) -> bool:
        """
        Confirm project deletion with the user.
        
        Args:
            project_name: Name of the project to delete
            
        Returns:
            True if user confirms deletion
        """
        pass


class ProjectsPresenter(BasePresenter):
    """
    Presenter for managing projects in the SLIDEMAN application.
    
    This presenter coordinates between the Projects view and the various services
    needed for project management operations.
    """
    
    # Signals for async operations
    project_created = Signal(int)  # project_id
    project_deleted = Signal(int)  # project_id
    project_renamed = Signal(int, str)  # project_id, new_name
    conversion_completed = Signal(int)  # file_id
    
    def __init__(self, view: IProjectsView, services: Dict[str, Any]):
        """
        Initialize the projects presenter.
        
        Args:
            view: The projects view
            services: Dictionary containing required services:
                - database: Database service
                - file_io: File I/O service
                - background_tasks: Background task service
                - undo_stack: Undo/redo stack
        """
        super().__init__(view, services)
        self._current_project_id: Optional[int] = None
        self._conversion_workers = {}
        
    @property
    def projects_view(self) -> IProjectsView:
        """Get the view as IProjectsView."""
        return self._view  # type: ignore
        
    def initialize(self) -> None:
        """Initialize the presenter and load initial data."""
        self.load_projects()
        
    def load_projects(self) -> None:
        """Load all projects from the database."""
        try:
            self.logger.info("Loading projects from database")
            db = self.get_service("database")
            if not db:
                raise ValidationError("Database service not available")
                
            projects = db.get_all_projects()
            self.projects_view.show_project_list(projects)
            self.logger.info(f"Loaded {len(projects)} projects")
            
        except DatabaseError as e:
            self.handle_error(e, "Database Error")
        except Exception as e:
            self.handle_error(e, "Unexpected Error")
            
    def create_project(self) -> None:
        """Create a new project."""
        # Get project info from view
        project_info = self.projects_view.get_new_project_info()
        if not project_info:
            return
            
        project_name, selected_files = project_info
        
        if not project_name or not selected_files:
            self.handle_warning("Please provide a project name and select files")
            return
            
        try:
            self.projects_view.set_busy(True, f"Creating project '{project_name}'...")
            
            # Get services
            db = self.get_service("database")
            file_io = self.get_service("file_io")
            bg_tasks = self.get_service("background_tasks")
            
            if not all([db, file_io, bg_tasks]):
                raise ValidationError("Required services not available")
                
            # Start the file copy operation
            worker = bg_tasks.copy_files_async(
                selected_files,
                project_name,
                on_complete=lambda info: self._handle_copy_complete(project_name, info),
                on_error=self._handle_copy_error
            )
            
        except Exception as e:
            self.projects_view.set_busy(False)
            self.handle_error(e, "Project Creation Error")
            
    def _handle_copy_complete(self, project_name: str, copied_files_info: Dict[str, str]) -> None:
        """
        Handle completion of file copy operation.
        
        Args:
            project_name: Name of the project
            copied_files_info: Dictionary mapping relative paths to checksums
        """
        try:
            db = self.get_service("database")
            file_io = self.get_service("file_io")
            
            # Create project folder path
            project_folder_path = file_io.get_project_folder(project_name)
            
            # Add project to database
            project_id = db.add_project(project_name, str(project_folder_path))
            if not project_id:
                raise DatabaseError("Failed to create project in database")
                
            # Add files to database
            file_ids = []
            for rel_path, checksum in copied_files_info.items():
                filename = Path(rel_path).name
                file_id = db.add_file(project_id, filename, rel_path, checksum)
                if file_id:
                    file_ids.append(file_id)
                    
            self.logger.info(f"Project '{project_name}' created with {len(file_ids)} files")
            
            # Reload projects
            self.load_projects()
            
            # Start conversion for the new files
            if file_ids:
                self._start_conversion_for_files(project_id, project_name, project_folder_path, file_ids)
                
            # Emit signal
            self.project_created.emit(project_id)
            
        except DuplicateResourceError:
            self.handle_warning(f"A project named '{project_name}' already exists")
        except DatabaseError as e:
            self.handle_error(e, "Database Error")
        except Exception as e:
            self.handle_error(e, "Project Creation Error")
        finally:
            self.projects_view.set_busy(False)
            
    def _handle_copy_error(self, error: str) -> None:
        """Handle error during file copy operation."""
        self.projects_view.set_busy(False)
        self.handle_error(FileOperationError(error), "File Copy Error")
        
    def delete_selected_project(self, project: Project) -> None:
        """
        Delete the selected project.
        
        Args:
            project: The project to delete
        """
        if not self.projects_view.confirm_delete(project.name):
            return
            
        try:
            # Use command for undo support
            cmd_class = self.get_service("delete_project_cmd")
            db = self.get_service("database")
            undo_stack = self.get_service("undo_stack")
            
            if not all([cmd_class, db, undo_stack]):
                raise ValidationError("Required services not available")
                
            cmd = cmd_class(project.id, project.name, project.folder_path, db)
            undo_stack.push(cmd)
            
            # Reload projects
            self.load_projects()
            
            # Emit signal
            self.project_deleted.emit(project.id)
            
        except Exception as e:
            self.handle_error(e, "Delete Error")
            
    def rename_selected_project(self, project: Project) -> None:
        """
        Rename the selected project.
        
        Args:
            project: The project to rename
        """
        new_name = self.projects_view.get_rename_input(project.name)
        if not new_name or new_name == project.name:
            return
            
        try:
            # Use command for undo support
            cmd_class = self.get_service("rename_project_cmd")
            db = self.get_service("database")
            undo_stack = self.get_service("undo_stack")
            
            if not all([cmd_class, db, undo_stack]):
                raise ValidationError("Required services not available")
                
            cmd = cmd_class(project.id, project.name, project.folder_path, new_name.strip(), db)
            undo_stack.push(cmd)
            
            # Reload projects
            self.load_projects()
            
            # Emit signal
            self.project_renamed.emit(project.id, new_name)
            
        except Exception as e:
            self.handle_error(e, "Rename Error")
            
    def convert_project_slides(self, project: Project) -> None:
        """
        Start slide conversion for a project.
        
        Args:
            project: The project to convert slides for
        """
        try:
            db = self.get_service("database")
            if not db:
                raise ValidationError("Database service not available")
                
            # Get pending/failed files
            pending_files = db.get_files_for_project(project.id, status='Pending')
            failed_files = db.get_files_for_project(project.id, status='Failed')
            files_to_convert = pending_files + failed_files
            
            if not files_to_convert:
                self.handle_info("No files require conversion", "Conversion Not Needed")
                return
                
            self._start_conversion_for_files(
                project.id, 
                project.name, 
                Path(project.folder_path),
                [f.id for f in files_to_convert if f.id]
            )
            
        except Exception as e:
            self.handle_error(e, "Conversion Error")
            
    def _start_conversion_for_files(self, project_id: int, project_name: str, 
                                   project_path: Path, file_ids: List[int]) -> None:
        """
        Start slide conversion for specific files.
        
        Args:
            project_id: ID of the project
            project_name: Name of the project
            project_path: Path to the project folder
            file_ids: List of file IDs to convert
        """
        try:
            self.projects_view.set_busy(True, f"Starting conversion for '{project_name}'...")
            
            db = self.get_service("database")
            converter_class = self.get_service("slide_converter")
            
            if not all([db, converter_class]):
                raise ValidationError("Required services not available")
                
            # Get file objects
            all_files = db.get_files_for_project(project_id)
            file_map = {f.id: f for f in all_files if f.id}
            
            # Start conversion for each file
            for file_id in file_ids:
                if file_id not in file_map:
                    continue
                    
                file_obj = file_map[file_id]
                file_path = project_path / file_obj.rel_path
                
                if not file_path.exists():
                    self.logger.error(f"File not found: {file_path}")
                    db.update_file_conversion_status(file_id, 'Failed')
                    continue
                    
                # Create converter worker
                worker = converter_class(file_id, file_path, db.db_path)
                worker.signals.progress.connect(
                    lambda fid, curr, total: self.projects_view.update_conversion_progress(fid, curr, total)
                )
                worker.signals.finished.connect(self._handle_conversion_finished)
                worker.signals.error.connect(self._handle_conversion_error)
                
                # Track worker
                self._conversion_workers[file_id] = worker
                
                # Start conversion
                thread_pool = self.get_service("thread_pool")
                if thread_pool:
                    thread_pool.start(worker)
                    
        except Exception as e:
            self.projects_view.set_busy(False)
            self.handle_error(e, "Conversion Error")
            
    def _handle_conversion_finished(self, file_id: int) -> None:
        """Handle successful conversion completion."""
        self.logger.info(f"Conversion completed for file {file_id}")
        
        # Remove from tracking
        self._conversion_workers.pop(file_id, None)
        
        # Check if all conversions are done
        if not self._conversion_workers:
            self.projects_view.set_busy(False)
            
        # Emit signal
        self.conversion_completed.emit(file_id)
        
    def _handle_conversion_error(self, file_id: int, error: str) -> None:
        """Handle conversion error."""
        self.logger.error(f"Conversion error for file {file_id}: {error}")
        
        # Remove from tracking
        self._conversion_workers.pop(file_id, None)
        
        # Check if all conversions are done
        if not self._conversion_workers:
            self.projects_view.set_busy(False)
            
    def select_project(self, project: Optional[Project]) -> None:
        """
        Handle project selection.
        
        Args:
            project: The selected project or None to clear selection
        """
        if project:
            self._current_project_id = project.id
            self.projects_view.show_project_details(project)
            
            # Update app state
            app_state = self.get_service("app_state")
            if app_state:
                app_state.set_current_project(project.folder_path)
        else:
            self._current_project_id = None
            self.projects_view.clear_project_selection()
            
            # Update app state
            app_state = self.get_service("app_state")
            if app_state:
                app_state.close_project()
                
    def cleanup(self) -> None:
        """Clean up presenter resources."""
        # Cancel any running conversions
        for worker in self._conversion_workers.values():
            worker.cancel()
        self._conversion_workers.clear()
        
        super().cleanup()