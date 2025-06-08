"""
Configuration management for the PrezI application.
Handles environment variables, settings, and application configuration.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field, validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Information
    app_name: str = Field(default="PrezI Working App", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # API Configuration
    host: str = Field(default="127.0.0.1", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=False, env="RELOAD")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./prezi_app.db", env="DATABASE_URL")
    database_pool_size: int = Field(default=5, env="DATABASE_POOL_SIZE")
    database_pool_overflow: int = Field(default=10, env="DATABASE_POOL_OVERFLOW")
    
    # AI Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.3, env="OPENAI_TEMPERATURE")
    ai_analysis_enabled: bool = Field(default=True, env="AI_ANALYSIS_ENABLED")
    
    # PowerPoint Configuration
    powerpoint_com_enabled: bool = Field(default=True, env="POWERPOINT_COM_ENABLED")
    powerpoint_timeout: int = Field(default=30, env="POWERPOINT_TIMEOUT")
    slides_per_batch: int = Field(default=10, env="SLIDES_PER_BATCH")
    
    # File Storage Configuration
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    thumbnail_dir: str = Field(default="./thumbnails", env="THUMBNAIL_DIR")
    export_dir: str = Field(default="./exports", env="EXPORT_DIR")
    max_file_size: int = Field(default=100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB
    allowed_extensions: list = Field(default=[".pptx", ".ppt"], env="ALLOWED_EXTENSIONS")
    
    # Security Configuration
    secret_key: str = Field(default="prezi-dev-secret-key-change-in-production", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    cors_origins: list = Field(default=["http://localhost:3000", "http://127.0.0.1:3000"], env="CORS_ORIGINS")
    
    # Performance Configuration
    worker_threads: int = Field(default=4, env="WORKER_THREADS")
    cache_size: int = Field(default=1000, env="CACHE_SIZE")
    thumbnail_cache_size: int = Field(default=500, env="THUMBNAIL_CACHE_SIZE")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
        env="LOG_FORMAT"
    )
    
    # Feature Flags
    enable_ai_suggestions: bool = Field(default=True, env="ENABLE_AI_SUGGESTIONS")
    enable_auto_tagging: bool = Field(default=True, env="ENABLE_AUTO_TAGGING")
    enable_natural_language_search: bool = Field(default=True, env="ENABLE_NL_SEARCH")
    enable_export_pdf: bool = Field(default=True, env="ENABLE_EXPORT_PDF")
    enable_export_pptx: bool = Field(default=True, env="ENABLE_EXPORT_PPTX")
    
    @validator("openai_api_key")
    def validate_openai_key(cls, v, values):
        """Validate OpenAI API key if AI features are enabled"""
        if values.get("ai_analysis_enabled", True) and not v:
            # Don't require API key in development/testing
            if not values.get("debug", False):
                raise ValueError("OpenAI API key is required when AI analysis is enabled")
        return v
    
    @validator("powerpoint_com_enabled")
    def validate_com_support(cls, v):
        """Validate COM support on Windows"""
        if v and sys.platform != "win32":
            # Allow disabling COM on non-Windows platforms
            return False
        return v
    
    @validator("upload_dir", "thumbnail_dir", "export_dir")
    def validate_directories(cls, v):
        """Ensure directories exist"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path.absolute())
    
    @property
    def is_windows(self) -> bool:
        """Check if running on Windows"""
        return sys.platform == "win32"
    
    @property
    def supports_com(self) -> bool:
        """Check if COM automation is supported"""
        return self.is_windows and self.powerpoint_com_enabled
    
    @property
    def database_path(self) -> Path:
        """Get database file path for SQLite"""
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url[10:]  # Remove 'sqlite:///'
            return Path(db_path).absolute()
        return Path("prezi_app.db")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()


def get_data_dir() -> Path:
    """Get application data directory"""
    if sys.platform == "win32":
        # Windows: Use AppData
        base_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        # macOS: Use Application Support
        base_dir = Path.home() / "Library" / "Application Support"
    else:
        # Linux: Use XDG data home
        base_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    
    app_dir = base_dir / "PrezI"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_cache_dir() -> Path:
    """Get application cache directory"""
    if sys.platform == "win32":
        # Windows: Use Local AppData
        base_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        # macOS: Use Caches
        base_dir = Path.home() / "Library" / "Caches"
    else:
        # Linux: Use XDG cache home
        base_dir = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    
    cache_dir = base_dir / "PrezI"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_config_dir() -> Path:
    """Get application configuration directory"""
    if sys.platform == "win32":
        # Windows: Use AppData
        base_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        # macOS: Use Application Support
        base_dir = Path.home() / "Library" / "Application Support"
    else:
        # Linux: Use XDG config home
        base_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    
    config_dir = base_dir / "PrezI"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


class PlatformConfig:
    """Platform-specific configuration"""
    
    def __init__(self):
        self.is_windows = sys.platform == "win32"
        self.is_macos = sys.platform == "darwin"
        self.is_linux = sys.platform.startswith("linux")
        
        self.data_dir = get_data_dir()
        self.cache_dir = get_cache_dir()
        self.config_dir = get_config_dir()
        
        # Platform-specific paths
        self.database_path = self.data_dir / "prezi_app.db"
        self.thumbnails_path = self.cache_dir / "thumbnails"
        self.uploads_path = self.data_dir / "uploads"
        self.exports_path = self.data_dir / "exports"
        
        # Ensure directories exist
        for path in [self.thumbnails_path, self.uploads_path, self.exports_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    @property
    def supports_com(self) -> bool:
        """Check if COM automation is supported"""
        return self.is_windows
    
    def get_temp_dir(self) -> Path:
        """Get temporary directory for processing"""
        import tempfile
        temp_dir = Path(tempfile.gettempdir()) / "prezi_processing"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir


# Global platform configuration instance
platform_config = PlatformConfig()


# Environment configuration helpers
def is_development() -> bool:
    """Check if running in development mode"""
    return get_settings().debug


def is_production() -> bool:
    """Check if running in production mode"""
    return not is_development()


def get_cors_origins() -> list:
    """Get CORS origins for the application"""
    settings = get_settings()
    if is_development():
        # Allow common development origins
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            *settings.cors_origins
        ]
    return settings.cors_origins


def get_database_url() -> str:
    """Get database URL with platform-specific path"""
    settings = get_settings()
    if settings.database_url.startswith("sqlite:///"):
        # Use platform-specific database path
        return f"sqlite:///{platform_config.database_path}"
    return settings.database_url