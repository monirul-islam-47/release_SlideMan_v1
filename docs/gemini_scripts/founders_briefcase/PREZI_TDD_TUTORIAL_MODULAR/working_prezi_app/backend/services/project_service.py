"""
Project service for managing project operations.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc

from backend.core.models import Project, ProjectStatus
from backend.database.models import ProjectModel, FileModel, SlideModel

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for project operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_projects(
        self, 
        status: Optional[ProjectStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Project]:
        """Get list of projects with filtering"""
        try:
            query = self.db.query(ProjectModel).options(
                joinedload(ProjectModel.files).joinedload(FileModel.slides)
            )
            
            if status:
                query = query.filter(ProjectModel.status == status.value)
            
            query = query.order_by(desc(ProjectModel.updated_at))
            query = query.limit(limit).offset(offset)
            
            project_models = query.all()
            return [self._model_to_pydantic(model) for model in project_models]
            
        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            raise
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a specific project by ID"""
        try:
            project_model = self.db.query(ProjectModel).options(
                joinedload(ProjectModel.files).joinedload(FileModel.slides)
            ).filter(ProjectModel.id == project_id).first()
            
            if not project_model:
                return None
            
            return self._model_to_pydantic(project_model)
            
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            raise
    
    def create_project(self, project: Project) -> Project:
        """Create a new project"""
        try:
            project_model = ProjectModel(
                id=project.id,
                name=project.name,
                description=project.description,
                status=project.status.value,
                ai_analysis=project.ai_analysis
            )
            
            self.db.add(project_model)
            self.db.commit()
            self.db.refresh(project_model)
            
            logger.info(f"Created project: {project.name} ({project.id})")
            return self._model_to_pydantic(project_model)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create project: {e}")
            raise
    
    def update_project(self, project: Project) -> Project:
        """Update an existing project"""
        try:
            project_model = self.db.query(ProjectModel).filter(
                ProjectModel.id == project.id
            ).first()
            
            if not project_model:
                raise ValueError(f"Project not found: {project.id}")
            
            project_model.name = project.name
            project_model.description = project.description
            project_model.status = project.status.value
            project_model.ai_analysis = project.ai_analysis
            project_model.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(project_model)
            
            logger.info(f"Updated project: {project.name} ({project.id})")
            return self._model_to_pydantic(project_model)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update project: {e}")
            raise
    
    def delete_project_permanent(self, project_id: str):
        """Permanently delete a project and all its data"""
        try:
            project_model = self.db.query(ProjectModel).filter(
                ProjectModel.id == project_id
            ).first()
            
            if not project_model:
                raise ValueError(f"Project not found: {project_id}")
            
            # Delete project (cascades to files, slides, elements)
            self.db.delete(project_model)
            self.db.commit()
            
            logger.info(f"Permanently deleted project: {project_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete project: {e}")
            raise
    
    def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """Get project statistics"""
        try:
            project_model = self.db.query(ProjectModel).options(
                joinedload(ProjectModel.files).joinedload(FileModel.slides)
            ).filter(ProjectModel.id == project_id).first()
            
            if not project_model:
                raise ValueError(f"Project not found: {project_id}")
            
            # Calculate statistics
            total_files = len(project_model.files)
            total_slides = sum(file.slide_count for file in project_model.files)
            processed_files = sum(1 for file in project_model.files if file.processed)
            
            # Get file types
            file_extensions = {}
            for file in project_model.files:
                ext = file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown'
                file_extensions[ext] = file_extensions.get(ext, 0) + 1
            
            # Get total file size
            total_size = sum(file.file_size for file in project_model.files)
            
            return {
                "project_id": project_id,
                "total_files": total_files,
                "total_slides": total_slides,
                "processed_files": processed_files,
                "processing_progress": (processed_files / total_files * 100) if total_files > 0 else 0,
                "total_size_bytes": total_size,
                "file_extensions": file_extensions,
                "created_at": project_model.created_at.isoformat(),
                "updated_at": project_model.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get project stats: {e}")
            raise
    
    def get_recent_activity(self, project_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activity for a project"""
        try:
            # Get recently updated files and slides
            files = self.db.query(FileModel).filter(
                FileModel.project_id == project_id
            ).order_by(desc(FileModel.updated_at)).limit(limit).all()
            
            activities = []
            for file in files:
                activities.append({
                    "type": "file_updated",
                    "timestamp": file.updated_at.isoformat(),
                    "file_id": file.id,
                    "filename": file.filename,
                    "processed": file.processed
                })
            
            # Sort by timestamp
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return activities[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get project activity: {e}")
            raise
    
    def _model_to_pydantic(self, model: ProjectModel) -> Project:
        """Convert SQLAlchemy model to Pydantic model"""
        from backend.core.models import File, Slide, Element
        
        # Convert files
        files = []
        for file_model in model.files:
            slides = []
            for slide_model in file_model.slides:
                elements = []
                for element_model in slide_model.elements:
                    element = Element(
                        id=element_model.id,
                        slide_id=element_model.slide_id,
                        element_type=element_model.element_type,
                        content=element_model.content,
                        position_x=element_model.position_x,
                        position_y=element_model.position_y,
                        width=element_model.width,
                        height=element_model.height,
                        keywords=[],  # Will be populated by keyword service
                        ai_analysis=element_model.ai_analysis or {},
                        created_at=element_model.created_at,
                        updated_at=element_model.updated_at
                    )
                    elements.append(element)
                
                slide = Slide(
                    id=slide_model.id,
                    file_id=slide_model.file_id,
                    slide_number=slide_model.slide_number,
                    title=slide_model.title,
                    notes=slide_model.notes,
                    slide_type=slide_model.slide_type,
                    thumbnail_path=slide_model.thumbnail_path,
                    full_image_path=slide_model.full_image_path,
                    elements=elements,
                    keywords=[],  # Will be populated by keyword service
                    ai_analysis=slide_model.ai_analysis or {},
                    created_at=slide_model.created_at,
                    updated_at=slide_model.updated_at
                )
                slides.append(slide)
            
            file = File(
                id=file_model.id,
                project_id=file_model.project_id,
                filename=file_model.filename,
                file_path=file_model.file_path,
                file_size=file_model.file_size,
                slide_count=file_model.slide_count,
                slides=slides,
                keywords=[],  # Will be populated by keyword service
                ai_analysis=file_model.ai_analysis or {},
                processed=file_model.processed,
                processing_error=file_model.processing_error,
                created_at=file_model.created_at,
                updated_at=file_model.updated_at
            )
            files.append(file)
        
        return Project(
            id=model.id,
            name=model.name,
            description=model.description,
            status=ProjectStatus(model.status),
            files=files,
            keywords=[],  # Will be populated by keyword service
            ai_analysis=model.ai_analysis or {},
            created_at=model.created_at,
            updated_at=model.updated_at
        )