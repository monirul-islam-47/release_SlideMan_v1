"""
Project management API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import uuid4

from backend.core.models import (
    Project, CreateProjectRequest, UpdateProjectRequest, ProjectStatus
)
from backend.database.database import get_db_session
from backend.database.models import ProjectModel
from backend.services.project_service import ProjectService

router = APIRouter()


def get_project_service(db: Session = Depends(get_db_session)) -> ProjectService:
    """Dependency to get project service"""
    return ProjectService(db)


@router.get("/projects", response_model=List[Project])
async def list_projects(
    status: Optional[ProjectStatus] = Query(None, description="Filter by project status"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of projects to return"),
    offset: int = Query(0, ge=0, description="Number of projects to skip"),
    project_service: ProjectService = Depends(get_project_service)
):
    """Get list of projects with optional filtering"""
    try:
        projects = project_service.get_projects(
            status=status,
            limit=limit,
            offset=offset
        )
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve projects: {str(e)}")


@router.post("/projects", response_model=Project, status_code=201)
async def create_project(
    project_data: CreateProjectRequest,
    project_service: ProjectService = Depends(get_project_service)
):
    """Create a new project"""
    try:
        project = Project(
            id=str(uuid4()),
            name=project_data.name,
            description=project_data.description,
            status=ProjectStatus.ACTIVE
        )
        
        created_project = project_service.create_project(project)
        return created_project
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("/projects/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service)
):
    """Get a specific project by ID"""
    try:
        project = project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve project: {str(e)}")


@router.put("/projects/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_data: UpdateProjectRequest,
    project_service: ProjectService = Depends(get_project_service)
):
    """Update an existing project"""
    try:
        # Get existing project
        existing_project = project_service.get_project(project_id)
        if not existing_project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update fields
        update_data = project_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing_project, field, value)
        
        updated_project = project_service.update_project(existing_project)
        return updated_project
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    permanent: bool = Query(False, description="Permanently delete project (cannot be undone)"),
    project_service: ProjectService = Depends(get_project_service)
):
    """Delete or archive a project"""
    try:
        project = project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if permanent:
            project_service.delete_project_permanent(project_id)
            return {"message": "Project permanently deleted"}
        else:
            # Archive project instead of permanent deletion
            project.status = ProjectStatus.DELETED
            project_service.update_project(project)
            return {"message": "Project archived"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")


@router.post("/projects/{project_id}/restore")
async def restore_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service)
):
    """Restore an archived project"""
    try:
        project = project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if project.status != ProjectStatus.DELETED:
            raise HTTPException(status_code=400, detail="Project is not archived")
        
        project.status = ProjectStatus.ACTIVE
        updated_project = project_service.update_project(project)
        return updated_project
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore project: {str(e)}")


@router.get("/projects/{project_id}/stats")
async def get_project_stats(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service)
):
    """Get project statistics"""
    try:
        project = project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        stats = project_service.get_project_stats(project_id)
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project stats: {str(e)}")


@router.get("/projects/{project_id}/recent-activity")
async def get_project_recent_activity(
    project_id: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of activities to return"),
    project_service: ProjectService = Depends(get_project_service)
):
    """Get recent activity for a project"""
    try:
        project = project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # This would typically fetch from an activity log table
        # For now, return basic info about files and slides
        activity = project_service.get_recent_activity(project_id, limit)
        return activity
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project activity: {str(e)}")