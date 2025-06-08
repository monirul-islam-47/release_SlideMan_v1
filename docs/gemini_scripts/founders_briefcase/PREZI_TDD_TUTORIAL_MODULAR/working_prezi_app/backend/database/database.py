"""
Database setup and session management for the PrezI application.
Uses SQLAlchemy with SQLite for local storage and full-text search capabilities.
"""

import logging
from typing import Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.core.config import get_settings, get_database_url

logger = logging.getLogger(__name__)

# SQLAlchemy base class
Base = declarative_base()

# Database engine
engine = None
SessionLocal = None


def configure_sqlite_connection(dbapi_connection, connection_record):
    """Configure SQLite connection with optimizations and FTS5 support"""
    cursor = dbapi_connection.cursor()
    
    # Enable WAL mode for better concurrency
    cursor.execute("PRAGMA journal_mode=WAL")
    
    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys=ON")
    
    # Optimize SQLite performance
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=10000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
    
    cursor.close()


def init_database():
    """Initialize database connection and session factory"""
    global engine, SessionLocal
    
    settings = get_settings()
    database_url = get_database_url()
    
    logger.info(f"Initializing database: {database_url}")
    
    # Create engine with appropriate configuration
    if database_url.startswith("sqlite"):
        engine = create_engine(
            database_url,
            connect_args={
                "check_same_thread": False,
                "timeout": 30
            },
            poolclass=StaticPool,
            pool_pre_ping=True,
            echo=settings.debug
        )
        
        # Configure SQLite connection
        event.listen(engine, "connect", configure_sqlite_connection)
    else:
        # For other databases (PostgreSQL, MySQL, etc.)
        engine = create_engine(
            database_url,
            pool_size=settings.database_pool_size,
            pool_overflow=settings.database_pool_overflow,
            pool_pre_ping=True,
            echo=settings.debug
        )
    
    # Create session factory
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    logger.info("Database initialization completed")


def create_tables():
    """Create all database tables"""
    if engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Create FTS5 virtual tables for full-text search
    with get_db_session() as db:
        try:
            # Slides FTS table
            db.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS slides_fts USING fts5(
                    slide_id UNINDEXED,
                    title,
                    notes,
                    content='slides',
                    content_rowid='id'
                )
            """))
            
            # Elements FTS table  
            db.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS elements_fts USING fts5(
                    element_id UNINDEXED,
                    content,
                    content='elements',
                    content_rowid='id'
                )
            """))
            
            # Files FTS table
            db.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
                    file_id UNINDEXED,
                    filename,
                    content='files',
                    content_rowid='id'
                )
            """))
            
            db.commit()
            logger.info("FTS5 virtual tables created successfully")
            
        except Exception as e:
            logger.warning(f"Could not create FTS5 tables (FTS5 may not be available): {e}")
            db.rollback()
    
    logger.info("Database tables creation completed")


def get_db_session() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup"""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db() -> Session:
    """Get database session (for dependency injection)"""
    return next(get_db_session())


class DatabaseManager:
    """Database manager for handling database operations"""
    
    def __init__(self):
        self.engine = engine
        self.session_factory = SessionLocal
    
    def get_session(self) -> Session:
        """Get a new database session"""
        if self.session_factory is None:
            raise RuntimeError("Database not initialized")
        return self.session_factory()
    
    def execute_raw_sql(self, sql: str, params: dict = None) -> list:
        """Execute raw SQL query"""
        with self.get_session() as session:
            result = session.execute(text(sql), params or {})
            return result.fetchall()
    
    def health_check(self) -> bool:
        """Check database connection health"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_database_info(self) -> dict:
        """Get database information"""
        try:
            with self.get_session() as session:
                # Get SQLite version
                version_result = session.execute(text("SELECT sqlite_version()")).fetchone()
                version = version_result[0] if version_result else "Unknown"
                
                # Get database size
                size_result = session.execute(text("PRAGMA page_count")).fetchone()
                page_count = size_result[0] if size_result else 0
                
                page_size_result = session.execute(text("PRAGMA page_size")).fetchone()
                page_size = page_size_result[0] if page_size_result else 0
                
                database_size = page_count * page_size
                
                # Get table count
                tables_result = session.execute(text("""
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)).fetchone()
                table_count = tables_result[0] if tables_result else 0
                
                return {
                    "type": "SQLite",
                    "version": version,
                    "size_bytes": database_size,
                    "table_count": table_count,
                    "fts_enabled": self._check_fts_support(),
                    "wal_mode": self._check_wal_mode()
                }
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}
    
    def _check_fts_support(self) -> bool:
        """Check if FTS5 is supported"""
        try:
            with self.get_session() as session:
                result = session.execute(text("PRAGMA compile_options")).fetchall()
                options = [row[0] for row in result]
                return any("FTS5" in option for option in options)
        except Exception:
            return False
    
    def _check_wal_mode(self) -> bool:
        """Check if WAL mode is enabled"""
        try:
            with self.get_session() as session:
                result = session.execute(text("PRAGMA journal_mode")).fetchone()
                return result[0].upper() == "WAL" if result else False
        except Exception:
            return False
    
    def vacuum_database(self):
        """Vacuum the database to reclaim space"""
        try:
            with self.get_session() as session:
                session.execute(text("VACUUM"))
                session.commit()
                logger.info("Database vacuum completed")
        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")
            raise
    
    def analyze_database(self):
        """Analyze the database to update statistics"""
        try:
            with self.get_session() as session:
                session.execute(text("ANALYZE"))
                session.commit()
                logger.info("Database analysis completed")
        except Exception as e:
            logger.error(f"Database analysis failed: {e}")
            raise


# Global database manager instance
db_manager = DatabaseManager()


def init_app_database():
    """Initialize the application database"""
    init_database()
    create_tables()
    return db_manager


# Cleanup function
def close_database():
    """Close database connections"""
    global engine, SessionLocal
    if engine:
        engine.dispose()
        engine = None
        SessionLocal = None
        logger.info("Database connections closed")