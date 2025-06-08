"""
FastAPI main application for the PrezI backend.
This is the entry point for the backend API server.
"""

import logging
import sys
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from backend.core.config import get_settings, get_cors_origins, is_development
from backend.database.database import init_app_database, close_database
from backend.api.routes import (
    projects, files, slides, elements, keywords, 
    assemblies, search, ai, export, health
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting PrezI application...")
    
    try:
        # Initialize database
        db_manager = init_app_database()
        app.state.db_manager = db_manager
        logger.info("Database initialized successfully")
        
        # Check database health
        if not db_manager.health_check():
            logger.error("Database health check failed")
            raise Exception("Database connection failed")
        
        # Log application info
        settings = get_settings()
        logger.info(f"PrezI {settings.app_version} started successfully")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"API available at: http://{settings.host}:{settings.port}")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down PrezI application...")
        close_database()
        logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-powered PowerPoint slide management application",
        docs_url="/docs" if is_development() else None,
        redoc_url="/redoc" if is_development() else None,
        openapi_url="/openapi.json" if is_development() else None,
        lifespan=lifespan
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add routes
    setup_routes(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    return app


def setup_middleware(app: FastAPI):
    """Configure application middleware"""
    settings = get_settings()
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware (in production)
    if not is_development():
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", settings.host]
        )
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all incoming requests"""
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url}")
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(f"Response: {response.status_code} ({process_time:.3f}s)")
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(f"Request failed: {str(e)} ({process_time:.3f}s)")
            raise


def setup_routes(app: FastAPI):
    """Configure application routes"""
    
    # API routes
    api_prefix = "/api/v1"
    
    app.include_router(health.router, prefix=api_prefix, tags=["health"])
    app.include_router(projects.router, prefix=api_prefix, tags=["projects"])
    app.include_router(files.router, prefix=api_prefix, tags=["files"])
    app.include_router(slides.router, prefix=api_prefix, tags=["slides"])
    app.include_router(elements.router, prefix=api_prefix, tags=["elements"])
    app.include_router(keywords.router, prefix=api_prefix, tags=["keywords"])
    app.include_router(assemblies.router, prefix=api_prefix, tags=["assemblies"])
    app.include_router(search.router, prefix=api_prefix, tags=["search"])
    app.include_router(ai.router, prefix=api_prefix, tags=["ai"])
    app.include_router(export.router, prefix=api_prefix, tags=["export"])
    
    # Serve static files in development
    if is_development():
        try:
            app.mount("/static", StaticFiles(directory="frontend/assets"), name="static")
            app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
        except Exception as e:
            logger.warning(f"Could not mount static files: {e}")
    
    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        """Root endpoint"""
        settings = get_settings()
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs_url": "/docs" if is_development() else None
        }


def setup_exception_handlers(app: FastAPI):
    """Configure global exception handlers"""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions"""
        logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "type": "http_error"
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions"""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        
        if is_development():
            # Return detailed error in development
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": 500,
                        "message": str(exc),
                        "type": "internal_error",
                        "traceback": str(exc.__traceback__) if hasattr(exc, '__traceback__') else None
                    }
                }
            )
        else:
            # Return generic error in production
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": 500,
                        "message": "Internal server error",
                        "type": "internal_error"
                    }
                }
            )


# Create the application instance
app = create_app()


if __name__ == "__main__":
    """Run the application directly"""
    import time
    
    settings = get_settings()
    
    # Configure uvicorn logging
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_config["formatters"]["access"]["fmt"] = '%(asctime)s - %(name)s - %(levelname)s - %(client_addr)s - "%(request_line)s" %(status_code)s'
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload and is_development(),
        log_config=log_config,
        access_log=True
    )