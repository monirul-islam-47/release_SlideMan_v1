"""
Health check and system status API endpoints.
"""

import time
import platform
import psutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.database.database import get_db_session, db_manager

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "prezi-backend"
    }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db_session)):
    """Detailed health check with system and database status"""
    start_time = time.time()
    
    try:
        # System information
        system_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }
        
        # Resource usage
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        resources = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
        }
        
        # Database health
        db_healthy = db_manager.health_check()
        db_info = db_manager.get_database_info() if db_healthy else {"error": "Database unavailable"}
        
        # Application settings
        settings = get_settings()
        app_info = {
            "name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug,
            "ai_enabled": settings.ai_analysis_enabled,
            "com_enabled": settings.powerpoint_com_enabled,
            "platform_support": {
                "windows": settings.is_windows,
                "com_automation": settings.supports_com
            }
        }
        
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return {
            "status": "healthy" if db_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "response_time_ms": round(response_time, 2),
            "system": system_info,
            "resources": resources,
            "database": db_info,
            "application": app_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/health/database")
async def database_health():
    """Database-specific health check"""
    try:
        is_healthy = db_manager.health_check()
        db_info = db_manager.get_database_info()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database_info": db_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database health check failed: {str(e)}"
        )


@router.get("/version")
async def get_version():
    """Get application version information"""
    settings = get_settings()
    
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "api_version": "v1",
        "build_info": {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "timestamp": datetime.now().isoformat()
        }
    }


@router.get("/status")
async def get_status():
    """Get application status and feature flags"""
    settings = get_settings()
    
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "ai_analysis": settings.ai_analysis_enabled,
            "ai_suggestions": settings.enable_ai_suggestions,
            "auto_tagging": settings.enable_auto_tagging,
            "natural_language_search": settings.enable_natural_language_search,
            "export_pdf": settings.enable_export_pdf,
            "export_pptx": settings.enable_export_pptx,
            "powerpoint_com": settings.supports_com
        },
        "configuration": {
            "debug": settings.debug,
            "ai_model": settings.openai_model,
            "worker_threads": settings.worker_threads,
            "max_file_size": settings.max_file_size,
            "allowed_extensions": settings.allowed_extensions
        }
    }