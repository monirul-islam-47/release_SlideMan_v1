# src/slideman/services/database.py

import sqlite3
import logging
import threading
from pathlib import Path
from typing import Optional, List, Any, Tuple, Dict
from queue import Queue, Empty, Full
from contextlib import contextmanager
import time

# Import models to potentially use for return types later
from ..models.project import Project
from ..models.file import File
from ..models.slide import Slide
from ..models.element import Element
from ..models.keyword import Keyword, KeywordKind

# Import thread-safety related classes
from PySide6.QtCore import QMutex, QMutexLocker

# Import custom exceptions
from .exceptions import (
    DatabaseError, ConnectionError, TransactionError,
    ResourceNotFoundError, ValidationError, DuplicateResourceError
)

# Define the current schema version. Increment this when schema changes.
DB_SCHEMA_VERSION = 3

class Database:
    """
    Thread-safe database service with connection pooling.
    Handles all interactions with the application's SQLite database.
    """
    
    def __init__(self, db_path: Path, pool_size: int = 5, pool_timeout: int = 30):
        """
        Initializes the Database service with connection pooling.

        Args:
            db_path: The path to the SQLite database file.
            pool_size: Maximum number of connections in the pool.
            pool_timeout: Timeout in seconds when waiting for a connection.
        """
        self.db_path = db_path
        self._pool_size = pool_size
        self._pool_timeout = pool_timeout
        self._connection_pool: Queue[sqlite3.Connection] = Queue(maxsize=pool_size)
        self._pool_lock = threading.RLock()
        self._schema_lock = threading.Lock()
        self._initialized = False
        self.logger = logging.getLogger(__name__)
        
        # Initialize mutex for thread safety during write operations
        self._write_mutex = QMutex()
        
        # Track active connections for cleanup
        self._active_connections: List[sqlite3.Connection] = []
        self._active_lock = threading.Lock()
        
        self.logger.info(f"Database service initialized for path: {self.db_path} with pool size: {pool_size}")

    def connect(self) -> bool:
        """
        Initializes the connection pool and database schema.
        
        Returns:
            bool: True if successful, False otherwise.
            
        Raises:
            ConnectionError: If unable to establish database connections.
            DatabaseError: If schema initialization fails.
        """
        if self._initialized:
            self.logger.warning("Database already initialized.")
            return True
            
        try:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize the connection pool
            self._initialize_pool()
            
            # Initialize or migrate the schema
            self._initialize_schema()
            
            self._initialized = True
            self.logger.info(f"Successfully initialized database at: {self.db_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}", exc_info=True)
            self._cleanup_pool()
            raise ConnectionError(f"Failed to initialize database: {e}") from e

    def _initialize_pool(self) -> None:
        """Initialize the connection pool with configured number of connections."""
        for i in range(self._pool_size):
            try:
                conn = self._create_connection()
                self._connection_pool.put(conn)
                with self._active_lock:
                    self._active_connections.append(conn)
            except Exception as e:
                self.logger.error(f"Failed to create connection {i+1}/{self._pool_size}: {e}")
                # Clean up any connections we've created so far
                self._cleanup_pool()
                raise ConnectionError(f"Failed to initialize connection pool: {e}") from e

    def _create_connection(self) -> sqlite3.Connection:
        """
        Create a new database connection with proper settings.
        
        Returns:
            A configured SQLite connection.
            
        Raises:
            ConnectionError: If unable to create connection.
        """
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            
            # Configure connection for better concurrency
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")  # Write-Ahead Logging for better concurrency
            conn.execute("PRAGMA synchronous = NORMAL;")  # Balance between safety and performance
            conn.execute("PRAGMA busy_timeout = 5000;")  # 5 second timeout for locked database
            conn.execute("PRAGMA temp_store = MEMORY;")  # Use memory for temporary tables
            
            return conn
            
        except sqlite3.Error as e:
            raise ConnectionError(f"Failed to create database connection: {e}") from e

    @contextmanager
    def get_connection(self):
        """
        Context manager for getting a connection from the pool.
        
        Yields:
            sqlite3.Connection: A database connection from the pool.
            
        Raises:
            ConnectionError: If unable to get a connection from the pool.
        """
        if not self._initialized:
            raise ConnectionError("Database not initialized. Call connect() first.")
            
        conn = None
        start_time = time.time()
        
        try:
            # Try to get a connection from the pool
            while True:
                try:
                    conn = self._connection_pool.get(timeout=1)
                    break
                except Empty:
                    elapsed = time.time() - start_time
                    if elapsed >= self._pool_timeout:
                        raise ConnectionError(
                            f"Timeout waiting for database connection after {self._pool_timeout}s"
                        )
                    # Check if we can create a new connection
                    with self._pool_lock:
                        if len(self._active_connections) < self._pool_size:
                            try:
                                conn = self._create_connection()
                                with self._active_lock:
                                    self._active_connections.append(conn)
                                break
                            except Exception as e:
                                self.logger.error(f"Failed to create additional connection: {e}")
                                continue
            
            # Verify connection is still valid
            try:
                conn.execute("SELECT 1")
            except sqlite3.Error:
                # Connection is dead, create a new one
                self.logger.warning("Dead connection detected, creating new one")
                with self._active_lock:
                    if conn in self._active_connections:
                        self._active_connections.remove(conn)
                conn = self._create_connection()
                with self._active_lock:
                    self._active_connections.append(conn)
            
            yield conn
            
        finally:
            # Return connection to pool
            if conn is not None:
                try:
                    self._connection_pool.put(conn, block=False)
                except Full:
                    # Pool is full, close the connection
                    self.logger.warning("Connection pool full, closing connection")
                    conn.close()
                    with self._active_lock:
                        if conn in self._active_connections:
                            self._active_connections.remove(conn)

    def _cleanup_pool(self) -> None:
        """Clean up all connections in the pool."""
        # Empty the pool
        while not self._connection_pool.empty():
            try:
                conn = self._connection_pool.get_nowait()
                conn.close()
            except Empty:
                break
        
        # Close all tracked connections
        with self._active_lock:
            for conn in self._active_connections:
                try:
                    conn.close()
                except Exception as e:
                    self.logger.error(f"Error closing connection: {e}")
            self._active_connections.clear()

    def close(self) -> None:
        """Close all database connections and clean up resources."""
        self.logger.info("Closing database connections...")
        self._cleanup_pool()
        self._initialized = False
        self.logger.info("Database connections closed.")

    def _execute_read(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        Execute a read query with proper error handling.
        
        Args:
            query: SQL query to execute.
            params: Query parameters.
            
        Returns:
            List of result rows.
            
        Raises:
            DatabaseError: If query execution fails.
        """
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
            except sqlite3.Error as e:
                self.logger.error(f"Database read error: {e}", exc_info=True)
                raise DatabaseError(f"Failed to execute read query: {e}") from e

    def _execute_write(self, query: str, params: tuple = (), return_lastrowid: bool = True) -> Optional[int]:
        """
        Execute a write query with proper locking and error handling.
        
        Args:
            query: SQL query to execute.
            params: Query parameters.
            return_lastrowid: Whether to return the last inserted row ID.
            
        Returns:
            Last inserted row ID if return_lastrowid is True, None otherwise.
            
        Raises:
            DatabaseError: If query execution fails.
        """
        with QMutexLocker(self._write_mutex):
            with self.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.lastrowid if return_lastrowid else None
                except sqlite3.IntegrityError as e:
                    conn.rollback()
                    if "UNIQUE constraint failed" in str(e):
                        raise DuplicateResourceError("Resource", str(params)) from e
                    raise ValidationError(f"Data integrity error: {e}") from e
                except sqlite3.Error as e:
                    conn.rollback()
                    self.logger.error(f"Database write error: {e}", exc_info=True)
                    raise DatabaseError(f"Failed to execute write query: {e}") from e

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.
        
        Yields:
            Connection object for the transaction.
            
        Raises:
            TransactionError: If transaction fails.
        """
        with self.get_connection() as conn:
            try:
                # Disable autocommit
                conn.isolation_level = 'DEFERRED'
                cursor = conn.cursor()
                cursor.execute("BEGIN")
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                self.logger.error(f"Transaction failed: {e}", exc_info=True)
                raise TransactionError(f"Transaction failed: {e}") from e
            finally:
                # Re-enable autocommit
                conn.isolation_level = None

    # Schema management methods

    def _get_db_version(self) -> int:
        """
        Retrieves the current schema version from the database.
        
        Returns:
            The schema version number, or 0 if not set.
            
        Raises:
            DatabaseError: If unable to retrieve version.
        """
        try:
            # During initialization, use a direct connection instead of get_connection()
            # This avoids the circular dependency where get_connection() checks _initialized
            if not self._initialized:
                # Create a temporary direct connection
                direct_conn = sqlite3.connect(str(self.db_path))
                try:
                    cursor = direct_conn.cursor()
                    cursor.execute("PRAGMA user_version;")
                    result = cursor.fetchone()
                    return result[0] if result else 0
                finally:
                    direct_conn.close()
            else:
                # Normal operation when already initialized
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA user_version;")
                    result = cursor.fetchone()
                    return result[0] if result else 0
        except Exception as e:
            raise DatabaseError(f"Failed to get database version: {e}") from e

    def _set_db_version(self, version: int) -> None:
        """
        Sets the schema version in the database.
        
        Args:
            version: The version number to set.
            
        Raises:
            DatabaseError: If unable to set version.
        """
        try:
            with self.get_connection() as conn:
                conn.execute(f"PRAGMA user_version = {version};")
                conn.commit()
        except Exception as e:
            raise DatabaseError(f"Failed to set database version: {e}") from e

    def _set_db_version_direct(self, conn: sqlite3.Connection, version: int) -> None:
        """
        Sets the schema version using a direct connection (for use during initialization).
        
        Args:
            conn: Direct database connection.
            version: The version number to set.
            
        Raises:
            DatabaseError: If unable to set version.
        """
        try:
            conn.execute(f"PRAGMA user_version = {version};")
        except Exception as e:
            raise DatabaseError(f"Failed to set database version: {e}") from e

    def _check_db_integrity(self) -> bool:
        """
        Check database integrity.
        
        Returns:
            True if database passes integrity check.
            
        Raises:
            DatabaseError: If integrity check fails.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                if result and result[0] == "ok":
                    return True
                else:
                    raise DatabaseError(f"Database integrity check failed: {result}")
        except Exception as e:
            raise DatabaseError(f"Failed to check database integrity: {e}") from e

    def _initialize_schema(self):
        """Checks the database version and creates/migrates the schema."""
        with self._schema_lock:
            try:
                current_version = self._get_db_version()
                self.logger.info(f"Current DB version: {current_version}. Required version: {DB_SCHEMA_VERSION}")

                if current_version < DB_SCHEMA_VERSION:
                    self.logger.info("Database schema needs initialization or migration.")
                    
                    # Use a direct connection during initialization
                    conn = self._create_connection()
                    try:
                        conn.execute("BEGIN TRANSACTION")
                        
                        if current_version == 0:
                            self.logger.info("Creating initial database schema...")
                            self._create_tables(conn)
                            self._create_indices(conn)
                            self._set_db_version_direct(conn, DB_SCHEMA_VERSION)
                            self.logger.info("Initial schema created successfully.")
                        else:
                            # Handle migrations
                            self.logger.info(f"Migrating database from version {current_version} to {DB_SCHEMA_VERSION}")
                            self._migrate_schema(conn, current_version, DB_SCHEMA_VERSION)
                            self._set_db_version_direct(conn, DB_SCHEMA_VERSION)
                            self.logger.info("Database migration completed successfully.")
                        
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        raise
                    finally:
                        conn.close()
                            
                elif current_version == DB_SCHEMA_VERSION:
                    self._ensure_fts_tables_exist()
                    self.logger.debug("Database schema is up to date.")
                else:
                    raise DatabaseError(
                        f"Database version {current_version} is newer than expected {DB_SCHEMA_VERSION}. "
                        "Application might be outdated."
                    )
                    
                # Always ensure FTS tables exist
                self._ensure_fts_tables_exist()
                
            except Exception as e:
                self.logger.error(f"Schema initialization failed: {e}", exc_info=True)
                raise DatabaseError(f"Failed to initialize schema: {e}") from e

    def _migrate_schema(self, conn: sqlite3.Connection, from_version: int, to_version: int) -> None:
        """
        Migrates the database schema from one version to another.
        
        Args:
            conn: Database connection.
            from_version: Current schema version.
            to_version: Target schema version.
            
        Raises:
            DatabaseError: If migration fails.
        """
        cursor = conn.cursor()
        
        try:
            # Migration from version 2 to 3
            if from_version == 2 and to_version >= 3:
                self.logger.info("Applying migration from version 2 to 3...")
                
                # Add created_at column to files table if it doesn't exist
                cursor.execute("""
                    SELECT COUNT(*) FROM pragma_table_info('files') 
                    WHERE name='created_at'
                """)
                if cursor.fetchone()[0] == 0:
                    # SQLite doesn't allow non-constant defaults in ALTER TABLE
                    # So we add the column without a default first
                    cursor.execute("""
                        ALTER TABLE files 
                        ADD COLUMN created_at TEXT
                    """)
                    # Then update existing rows with the current timestamp
                    cursor.execute("""
                        UPDATE files 
                        SET created_at = datetime('now', 'localtime')
                        WHERE created_at IS NULL
                    """)
                    self.logger.debug("Added created_at column to files table")
                
                # Add title column to slides table if it doesn't exist
                cursor.execute("""
                    SELECT COUNT(*) FROM pragma_table_info('slides') 
                    WHERE name='title'
                """)
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        ALTER TABLE slides 
                        ADD COLUMN title TEXT
                    """)
                    self.logger.debug("Added title column to slides table")
                
                from_version = 3
            
            # Add more migration blocks here for future versions
            
            if from_version != to_version:
                raise DatabaseError(
                    f"No migration path from version {from_version} to {to_version}"
                )
                
        except Exception as e:
            self.logger.error(f"Migration failed: {e}", exc_info=True)
            raise DatabaseError(f"Database migration failed: {e}") from e

    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """Create all necessary database tables."""
        cursor = conn.cursor()
        
        # Projects table
        cursor.execute("""
            CREATE TABLE projects (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                folder_path   TEXT    NOT NULL UNIQUE,
                created_at    TEXT    DEFAULT (datetime('now', 'localtime'))
            );
        """)
        
        # Files table
        cursor.execute("""
            CREATE TABLE files (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id    INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                filename      TEXT    NOT NULL,
                rel_path      TEXT    NOT NULL,
                slide_count   INTEGER,
                checksum      TEXT,
                conversion_status TEXT DEFAULT 'Pending' CHECK(conversion_status IN ('Pending', 'In Progress', 'Completed', 'Failed')),
                created_at    TEXT    DEFAULT (datetime('now', 'localtime')),
                UNIQUE(project_id, rel_path)
            );
        """)
        
        # Slides table
        cursor.execute("""
            CREATE TABLE slides (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id       INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
                slide_index   INTEGER NOT NULL,
                title         TEXT,
                thumb_rel_path TEXT,
                image_rel_path TEXT,
                UNIQUE(file_id, slide_index)
            );
        """)
        
        # Elements table
        cursor.execute("""
            CREATE TABLE elements (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                slide_id      INTEGER NOT NULL REFERENCES slides(id) ON DELETE CASCADE,
                element_type  TEXT    NOT NULL,
                bbox_x        REAL    NOT NULL,
                bbox_y        REAL    NOT NULL,
                bbox_w        REAL    NOT NULL,
                bbox_h        REAL    NOT NULL
            );
        """)
        
        # Keywords table
        cursor.execute("""
            CREATE TABLE keywords (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT    NOT NULL,
                kind    TEXT    NOT NULL CHECK(kind IN ('topic', 'title', 'name')),
                UNIQUE(keyword, kind)
            );
        """)
        
        # Junction tables
        cursor.execute("""
            CREATE TABLE slide_keywords (
                slide_id   INTEGER NOT NULL REFERENCES slides(id) ON DELETE CASCADE,
                keyword_id INTEGER NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
                PRIMARY KEY (slide_id, keyword_id)
            );
        """)
        
        cursor.execute("""
            CREATE TABLE element_keywords (
                element_id INTEGER NOT NULL REFERENCES elements(id) ON DELETE CASCADE,
                keyword_id INTEGER NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
                PRIMARY KEY (element_id, keyword_id)
            );
        """)
        
        self.logger.debug("All tables created successfully.")

    def _create_indices(self, conn: sqlite3.Connection) -> None:
        """Create database indices for performance."""
        cursor = conn.cursor()
        
        # Index on files for faster project queries
        cursor.execute("CREATE INDEX idx_files_project_id ON files(project_id);")
        
        # Index on slides for faster file queries
        cursor.execute("CREATE INDEX idx_slides_file_id ON slides(file_id);")
        
        # Index on elements for faster slide queries
        cursor.execute("CREATE INDEX idx_elements_slide_id ON elements(slide_id);")
        
        # Indices on junction tables
        cursor.execute("CREATE INDEX idx_slide_keywords_keyword_id ON slide_keywords(keyword_id);")
        cursor.execute("CREATE INDEX idx_element_keywords_keyword_id ON element_keywords(keyword_id);")
        
        # Index on keywords for faster lookups by kind
        cursor.execute("CREATE INDEX idx_keywords_kind ON keywords(kind);")
        
        self.logger.debug("All indices created successfully.")

    def _ensure_fts_tables_exist(self) -> None:
        """Ensure FTS5 virtual tables exist for full-text search."""
        try:
            # During initialization, use a direct connection instead of get_connection()
            if not self._initialized:
                # Create a temporary direct connection
                direct_conn = sqlite3.connect(str(self.db_path))
                try:
                    cursor = direct_conn.cursor()
                    
                    # Check if FTS tables already exist
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='slides_fts';"
                    )
                    if cursor.fetchone():
                        return  # Tables already exist
                    
                    # Create FTS5 virtual table for slides
                    cursor.execute("""
                        CREATE VIRTUAL TABLE IF NOT EXISTS slides_fts USING fts5(
                            slide_id UNINDEXED,
                            title,
                            notes,
                            content='slides',
                            content_rowid='id'
                        );
                    """)
                    
                    # Create triggers to keep FTS table in sync
                    cursor.execute("""
                        CREATE TRIGGER IF NOT EXISTS slides_fts_insert AFTER INSERT ON slides BEGIN
                            INSERT INTO slides_fts(slide_id, title, notes) VALUES (new.id, '', '');
                        END;
                    """)
                    
                    cursor.execute("""
                        CREATE TRIGGER IF NOT EXISTS slides_fts_delete AFTER DELETE ON slides BEGIN
                            DELETE FROM slides_fts WHERE slide_id = old.id;
                        END;
                    """)
                    
                    direct_conn.commit()
                    self.logger.debug("FTS tables created successfully.")
                finally:
                    direct_conn.close()
            else:
                # Normal operation when already initialized
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Check if FTS tables already exist
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='slides_fts';"
                    )
                    if cursor.fetchone():
                        return  # Tables already exist
                    
                    # Create FTS5 virtual table for slides
                    cursor.execute("""
                        CREATE VIRTUAL TABLE IF NOT EXISTS slides_fts USING fts5(
                            slide_id UNINDEXED,
                            title,
                            notes,
                            content='slides',
                            content_rowid='id'
                        );
                    """)
                    
                    # Create triggers to keep FTS table in sync
                    cursor.execute("""
                        CREATE TRIGGER IF NOT EXISTS slides_fts_insert AFTER INSERT ON slides BEGIN
                            INSERT INTO slides_fts(slide_id, title, notes) VALUES (new.id, '', '');
                        END;
                    """)
                    
                    cursor.execute("""
                        CREATE TRIGGER IF NOT EXISTS slides_fts_delete AFTER DELETE ON slides BEGIN
                            DELETE FROM slides_fts WHERE slide_id = old.id;
                        END;
                    """)
                    
                    conn.commit()
                    self.logger.debug("FTS tables created successfully.")
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to create FTS tables: {e}", exc_info=True)
            # Non-critical error, don't raise

    # Project management methods

    def add_project(self, name: str, folder_path: str) -> int:
        """
        Adds a new project to the database.
        
        Args:
            name: The project name.
            folder_path: The absolute path to the project folder.
            
        Returns:
            The ID of the newly created project.
            
        Raises:
            DuplicateResourceError: If a project with this folder path already exists.
            ValidationError: If input validation fails.
            DatabaseError: If the operation fails.
        """
        if not name or not name.strip():
            raise ValidationError("Project name cannot be empty")
            
        if not folder_path:
            raise ValidationError("Project folder path cannot be empty")
            
        query = "INSERT INTO projects (name, folder_path) VALUES (?, ?)"
        params = (name.strip(), folder_path)
        
        try:
            project_id = self._execute_write(query, params)
            self.logger.info(f"Added project '{name}' with ID {project_id}")
            return project_id
        except DuplicateResourceError:
            raise DuplicateResourceError("Project", folder_path)

    def get_project(self, project_id: int) -> Project:
        """
        Retrieves a project by ID.
        
        Args:
            project_id: The project ID.
            
        Returns:
            The Project object.
            
        Raises:
            ResourceNotFoundError: If the project is not found.
            DatabaseError: If the operation fails.
        """
        query = "SELECT * FROM projects WHERE id = ?"
        results = self._execute_read(query, (project_id,))
        
        if not results:
            raise ResourceNotFoundError("Project", project_id)
            
        row = results[0]
        return Project(
            id=row['id'],
            name=row['name'],
            folder_path=row['folder_path'],
            created_at=row['created_at']
        )

    def get_all_projects(self) -> List[Project]:
        """
        Retrieves all projects from the database.
        
        Returns:
            List of Project objects.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = "SELECT * FROM projects ORDER BY created_at DESC"
        results = self._execute_read(query)
        
        projects = []
        for row in results:
            projects.append(Project(
                id=row['id'],
                name=row['name'],
                folder_path=row['folder_path'],
                created_at=row['created_at']
            ))
            
        return projects

    def get_project_by_path(self, folder_path: str) -> Optional[Project]:
        """
        Retrieves a single project by its unique folder path.
        
        Args:
            folder_path: The folder path of the project.
            
        Returns:
            Project object if found, None otherwise.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = "SELECT id, name, folder_path, created_at FROM projects WHERE folder_path = ?"
        results = self._execute_read(query, (folder_path,))
        
        if not results:
            return None
            
        row = results[0]
        return Project(
            id=row['id'],
            name=row['name'],
            folder_path=row['folder_path'],
            created_at=row['created_at']
        )

    def update_project_details(self, project_id: int, name: str, folder_path: str) -> None:
        """
        Updates project name and folder path.
        
        Args:
            project_id: The project ID to update.
            name: New project name.
            folder_path: New folder path.
            
        Raises:
            ResourceNotFoundError: If the project is not found.
            ValidationError: If input validation fails.
            DatabaseError: If the operation fails.
        """
        if not name or not name.strip():
            raise ValidationError("Project name cannot be empty")
            
        # Verify project exists
        self.get_project(project_id)  # Will raise ResourceNotFoundError if not found
        
        query = "UPDATE projects SET name = ?, folder_path = ? WHERE id = ?"
        params = (name.strip(), folder_path, project_id)
        
        self._execute_write(query, params, return_lastrowid=False)
        self.logger.info(f"Updated project {project_id}: name='{name}', path='{folder_path}'")

    def delete_project(self, project_id: int) -> None:
        """
        Deletes a project and all associated data.
        
        Args:
            project_id: The project ID to delete.
            
        Raises:
            ResourceNotFoundError: If the project is not found.
            DatabaseError: If the operation fails.
        """
        # Verify project exists
        self.get_project(project_id)  # Will raise ResourceNotFoundError if not found
        
        query = "DELETE FROM projects WHERE id = ?"
        self._execute_write(query, (project_id,), return_lastrowid=False)
        self.logger.info(f"Deleted project {project_id} and all associated data")

    # File management methods

    def add_file(self, project_id: int, filename: str, rel_path: str, checksum: str) -> int:
        """
        Adds a file record to the database.
        
        Args:
            project_id: The project this file belongs to.
            filename: The file name.
            rel_path: Path relative to project folder.
            checksum: File checksum for integrity checking.
            
        Returns:
            The ID of the newly created file record.
            
        Raises:
            ValidationError: If input validation fails.
            DatabaseError: If the operation fails.
        """
        query = """
            INSERT INTO files (project_id, filename, rel_path, checksum) 
            VALUES (?, ?, ?, ?)
        """
        params = (project_id, filename, rel_path, checksum)
        
        file_id = self._execute_write(query, params)
        self.logger.debug(f"Added file '{filename}' with ID {file_id} to project {project_id}")
        return file_id

    def get_slide(self, slide_id: int) -> Optional[Slide]:
        """
        Retrieves a single slide by its ID.
        
        Args:
            slide_id: The slide ID.
            
        Returns:
            Slide object if found, None otherwise.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = """
            SELECT id, file_id, slide_index, title, thumb_rel_path, image_rel_path
            FROM slides
            WHERE id = ?
        """
        results = self._execute_read(query, (slide_id,))
        
        if not results:
            return None
            
        row = results[0]
        return Slide(
            id=row['id'],
            file_id=row['file_id'],
            slide_index=row['slide_index'],
            title=row['title'],
            thumb_rel_path=row['thumb_rel_path'],
            image_rel_path=row['image_rel_path']
        )

    def get_slide_origin(self, slide_id: int) -> Tuple[str, int]:
        """
        Retrieves the original file path and slide index for a given slide ID.
        
        Args:
            slide_id: The slide ID.
            
        Returns:
            Tuple of (full_file_path, slide_index).
            
        Raises:
            ResourceNotFoundError: If the slide is not found.
            DatabaseError: If the operation fails.
        """
        query = """
            SELECT p.folder_path, f.rel_path, s.slide_index 
            FROM slides s 
            JOIN files f ON s.file_id = f.id 
            JOIN projects p ON f.project_id = p.id 
            WHERE s.id = ?
        """
        results = self._execute_read(query, (slide_id,))
        
        if not results:
            raise ResourceNotFoundError("Slide", slide_id)
            
        row = results[0]
        full_path = Path(row['folder_path']) / row['rel_path']
        return (str(full_path), row['slide_index'])

    def delete_elements_for_slide(self, slide_id: int) -> None:
        """
        Deletes all elements associated with a slide.
        
        Args:
            slide_id: The slide ID.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = "DELETE FROM elements WHERE slide_id = ?"
        self._execute_write(query, (slide_id,))
        self.logger.debug(f"Deleted all elements for slide {slide_id}")

    def add_element(self, slide_id: int, element_type: str,
                    bbox_x: float, bbox_y: float, bbox_w: float, bbox_h: float) -> int:
        """
        Adds an element to a slide.
        
        Args:
            slide_id: The slide ID.
            element_type: Type of element (SHAPE, PICTURE, CHART, etc).
            bbox_x: X-coordinate of bounding box in EMU.
            bbox_y: Y-coordinate of bounding box in EMU.
            bbox_w: Width of bounding box in EMU.
            bbox_h: Height of bounding box in EMU.
            
        Returns:
            The element ID.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = """
            INSERT INTO elements (slide_id, element_type, bbox_x, bbox_y, bbox_w, bbox_h)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        element_id = self._execute_write(query, (slide_id, element_type, bbox_x, bbox_y, bbox_w, bbox_h))
        self.logger.debug(f"Added element {element_id} to slide {slide_id}")
        return element_id

    def add_slide(self, file_id: int, slide_index: int, thumb_rel_path: str = None, 
                  image_rel_path: str = None, title: str = None) -> int:
        """
        Adds a slide to the database.
        
        Args:
            file_id: The file ID.
            slide_index: Index of the slide in the file.
            thumb_rel_path: Relative path to thumbnail.
            image_rel_path: Relative path to full image.
            title: Optional slide title.
            
        Returns:
            The slide ID.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = """
            INSERT INTO slides (file_id, slide_index, title, thumb_rel_path, image_rel_path)
            VALUES (?, ?, ?, ?, ?)
        """
        slide_id = self._execute_write(query, (file_id, slide_index, title, thumb_rel_path, image_rel_path))
        self.logger.debug(f"Added slide {slide_id} with index {slide_index} to file {file_id}")
        return slide_id

    def get_slides_for_file(self, file_id: int) -> List[Slide]:
        """
        Retrieves all slides for a given file.
        
        Args:
            file_id: The file ID.
            
        Returns:
            List of Slide objects.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = """
            SELECT id, file_id, slide_index, title, thumb_rel_path, image_rel_path
            FROM slides
            WHERE file_id = ?
            ORDER BY slide_index
        """
        results = self._execute_read(query, (file_id,))
        
        slides = []
        for row in results:
            slides.append(Slide(
                id=row['id'],
                file_id=row['file_id'],
                slide_index=row['slide_index'],
                title=row['title'],
                thumb_rel_path=row['thumb_rel_path'],
                image_rel_path=row['image_rel_path']
            ))
        return slides

    def update_file_conversion_status(self, file_id: int, status: str) -> None:
        """
        Updates the conversion status of a file.
        
        Args:
            file_id: The file ID.
            status: The conversion status.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = "UPDATE files SET conversion_status = ? WHERE id = ?"
        self._execute_write(query, (status, file_id))
        self.logger.debug(f"Updated file {file_id} conversion status to {status}")

    def get_files_for_project(self, project_id: int) -> List[File]:
        """
        Retrieves all files for a project.
        
        Args:
            project_id: The project ID.
            
        Returns:
            List of File objects.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = """
            SELECT id, project_id, filename, rel_path, checksum,
                   conversion_status, created_at
            FROM files
            WHERE project_id = ?
            ORDER BY filename
        """
        results = self._execute_read(query, (project_id,))
        
        files = []
        for row in results:
            files.append(File(
                id=row['id'],
                project_id=row['project_id'],
                filename=row['filename'],
                rel_path=row['rel_path'],
                checksum=row['checksum'],
                conversion_status=row['conversion_status'],
                created_at=row['created_at']
            ))
        return files

    def get_project_id_by_path(self, project_path: str) -> Optional[int]:
        """
        Retrieves a project ID by its folder path.
        
        Args:
            project_path: The folder path of the project.
            
        Returns:
            The project ID if found, None otherwise.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = "SELECT id FROM projects WHERE folder_path = ?"
        results = self._execute_read(query, (project_path,))
        
        if results:
            return results[0]['id']
        return None

    def rename_project(self, project_id: int, new_name: str) -> bool:
        """
        Renames a project.
        
        Args:
            project_id: The project ID.
            new_name: The new project name.
            
        Returns:
            True if successful.
            
        Raises:
            ValidationError: If the new name is invalid.
            DatabaseError: If the operation fails.
        """
        if not new_name or not new_name.strip():
            raise ValidationError("Project name cannot be empty")
            
        query = "UPDATE projects SET name = ? WHERE id = ?"
        self._execute_write(query, (new_name.strip(), project_id))
        self.logger.info(f"Renamed project {project_id} to '{new_name}'")
        return True

    def get_slides_for_project(self, project_id: int) -> List[Dict]:
        """
        Retrieves all slides for a project with file information.
        
        Args:
            project_id: The project ID.
            
        Returns:
            List of dictionaries containing slide and file information.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = """
            SELECT s.id, s.file_id, s.slide_index, s.title, 
                   s.thumb_rel_path, s.image_rel_path,
                   f.filename, f.rel_path
            FROM slides s
            JOIN files f ON s.file_id = f.id
            WHERE f.project_id = ?
            ORDER BY f.filename, s.slide_index
        """
        results = self._execute_read(query, (project_id,))
        
        slides = []
        for row in results:
            slides.append({
                'id': row['id'],
                'file_id': row['file_id'],
                'slide_index': row['slide_index'],
                'title': row['title'],
                'thumb_rel_path': row['thumb_rel_path'],
                'image_rel_path': row['image_rel_path'],
                'filename': row['filename'],
                'file_rel_path': row['rel_path']
            })
        return slides

    def get_slide_thumbnail_path(self, slide_id: int) -> Optional[str]:
        """
        Retrieves the thumbnail path for a slide.
        
        Args:
            slide_id: The slide ID.
            
        Returns:
            The thumbnail path if found, None otherwise.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = "SELECT thumb_rel_path FROM slides WHERE id = ?"
        results = self._execute_read(query, (slide_id,))
        
        if results and results[0]['thumb_rel_path']:
            return results[0]['thumb_rel_path']
        return None

    def get_slide_image_path(self, slide_id: int) -> Optional[str]:
        """
        Retrieves the full image path for a slide.
        
        Args:
            slide_id: The slide ID.
            
        Returns:
            The image path if found, None otherwise.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = "SELECT image_rel_path FROM slides WHERE id = ?"
        results = self._execute_read(query, (slide_id,))
        
        if results and results[0]['image_rel_path']:
            return results[0]['image_rel_path']
        return None

    def get_project_folder_path_for_slide(self, slide_id: int) -> str:
        """
        Retrieves the project folder path for a given slide.
        
        Args:
            slide_id: The slide ID.
            
        Returns:
            The project folder path.
            
        Raises:
            ResourceNotFoundError: If the slide is not found.
            DatabaseError: If the operation fails.
        """
        query = """
            SELECT p.folder_path
            FROM slides s
            JOIN files f ON s.file_id = f.id
            JOIN projects p ON f.project_id = p.id
            WHERE s.id = ?
        """
        results = self._execute_read(query, (slide_id,))
        
        if not results:
            raise ResourceNotFoundError("Slide", slide_id)
            
        return results[0]['folder_path']

    def get_elements_for_slide(self, slide_id: int) -> List[Element]:
        """
        Retrieves all elements for a slide.
        
        Args:
            slide_id: The slide ID.
            
        Returns:
            List of Element objects.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = """
            SELECT id, slide_id, element_type, bbox_x, bbox_y, bbox_w, bbox_h
            FROM elements
            WHERE slide_id = ?
            ORDER BY id
        """
        results = self._execute_read(query, (slide_id,))
        
        elements = []
        for row in results:
            elements.append(Element(
                id=row['id'],
                slide_id=row['slide_id'],
                element_type=row['element_type'],
                bbox_x=row['bbox_x'],
                bbox_y=row['bbox_y'],
                bbox_w=row['bbox_w'],
                bbox_h=row['bbox_h']
            ))
        return elements

    # Keyword management methods
    
    def add_keyword_if_not_exists(self, keyword: str, kind: str = 'generic') -> int:
        """
        Adds a keyword if it doesn't already exist.
        
        Args:
            keyword: The keyword text.
            kind: The keyword type.
            
        Returns:
            The keyword ID (existing or new).
            
        Raises:
            ValidationError: If keyword is invalid.
            DatabaseError: If the operation fails.
        """
        if not keyword or not keyword.strip():
            raise ValidationError("Keyword cannot be empty")
            
        keyword = keyword.strip()
        
        # Check if keyword exists
        query = "SELECT id FROM keywords WHERE keyword = ? AND kind = ?"
        results = self._execute_read(query, (keyword, kind))
        
        if results:
            return results[0]['id']
        
        # Add new keyword
        insert_query = "INSERT INTO keywords (keyword, kind) VALUES (?, ?)"
        keyword_id = self._execute_write(insert_query, (keyword, kind))
        self.logger.debug(f"Added new keyword '{keyword}' of kind '{kind}' with ID {keyword_id}")
        return keyword_id

    def get_keyword_id(self, keyword: str, kind: str = 'generic') -> Optional[int]:
        """
        Gets the ID of a keyword.
        
        Args:
            keyword: The keyword text.
            kind: The keyword type.
            
        Returns:
            The keyword ID if found, None otherwise.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = "SELECT id FROM keywords WHERE keyword = ? AND kind = ?"
        results = self._execute_read(query, (keyword, kind))
        
        if results:
            return results[0]['id']
        return None

    def get_all_keywords_by_kind(self, kind: str) -> List[Keyword]:
        """
        Retrieves all keywords of a specific kind.
        
        Args:
            kind: The keyword type.
            
        Returns:
            List of Keyword objects.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = """
            SELECT id, keyword, kind
            FROM keywords
            WHERE kind = ?
            ORDER BY keyword COLLATE NOCASE
        """
        results = self._execute_read(query, (kind,))
        
        keywords = []
        for row in results:
            keywords.append(Keyword(
                id=row['id'],
                keyword=row['keyword'],
                kind=row['kind']
            ))
        return keywords

    def get_all_keyword_objects(self) -> List[Keyword]:
        """
        Retrieves all keywords as Keyword objects.
        
        Returns:
            List of Keyword objects.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = """
            SELECT id, keyword, kind
            FROM keywords
            ORDER BY kind, keyword COLLATE NOCASE
        """
        results = self._execute_read(query)
        
        keywords = []
        for row in results:
            keywords.append(Keyword(
                id=row['id'],
                keyword=row['keyword'],
                kind=row['kind']
            ))
        return keywords

    def get_all_keyword_strings(self, kind: str = None) -> List[str]:
        """
        Retrieves all keyword strings, optionally filtered by kind.
        
        Args:
            kind: Optional keyword type filter.
            
        Returns:
            List of keyword strings.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        if kind:
            query = "SELECT DISTINCT keyword FROM keywords WHERE kind = ? ORDER BY keyword COLLATE NOCASE"
            results = self._execute_read(query, (kind,))
        else:
            query = "SELECT DISTINCT keyword FROM keywords ORDER BY keyword COLLATE NOCASE"
            results = self._execute_read(query)
        
        return [row['keyword'] for row in results]

    def search_keywords(self, query: str, project_id: int = None) -> List[Keyword]:
        """
        Searches for keywords matching the query.
        
        Args:
            query: The search query.
            project_id: Optional project ID to filter by.
            
        Returns:
            List of matching Keyword objects.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        if not query:
            return []
            
        # Use LIKE for simple pattern matching
        search_pattern = f"%{query}%"
        
        if project_id is not None:
            sql = """
                SELECT DISTINCT k.id, k.keyword, k.kind
                FROM keywords k
                WHERE k.keyword LIKE ?
                AND k.id IN (
                    SELECT keyword_id FROM slide_keywords sk
                    JOIN slides s ON sk.slide_id = s.id
                    JOIN files f ON s.file_id = f.id
                    WHERE f.project_id = ?
                    UNION
                    SELECT keyword_id FROM element_keywords ek
                    JOIN elements e ON ek.element_id = e.id
                    JOIN slides s ON e.slide_id = s.id
                    JOIN files f ON s.file_id = f.id
                    WHERE f.project_id = ?
                )
                ORDER BY k.keyword COLLATE NOCASE
            """
            results = self._execute_read(sql, (search_pattern, project_id, project_id))
        else:
            sql = """
                SELECT id, keyword, kind
                FROM keywords
                WHERE keyword LIKE ?
                ORDER BY keyword COLLATE NOCASE
            """
            results = self._execute_read(sql, (search_pattern,))
        
        keywords = []
        for row in results:
            keywords.append(Keyword(
                id=row['id'],
                keyword=row['keyword'],
                kind=row['kind']
            ))
        return keywords

    def merge_keywords(self, source_id: int, target_id: int) -> bool:
        """
        Merges two keywords by moving all associations from source to target.
        
        Args:
            source_id: The source keyword ID to merge from.
            target_id: The target keyword ID to merge into.
            
        Returns:
            True if successful.
            
        Raises:
            ValidationError: If source and target are the same.
            ResourceNotFoundError: If either keyword is not found.
            DatabaseError: If the operation fails.
        """
        if source_id == target_id:
            raise ValidationError("Cannot merge keyword with itself")
        
        # Verify both keywords exist
        source_query = "SELECT keyword FROM keywords WHERE id = ?"
        target_query = "SELECT keyword FROM keywords WHERE id = ?"
        
        source_results = self._execute_read(source_query, (source_id,))
        if not source_results:
            raise ResourceNotFoundError("Source keyword", source_id)
            
        target_results = self._execute_read(target_query, (target_id,))
        if not target_results:
            raise ResourceNotFoundError("Target keyword", target_id)
        
        # Update slide keywords
        update_slide_keywords = """
            UPDATE OR REPLACE slide_keywords 
            SET keyword_id = ? 
            WHERE keyword_id = ?
        """
        self._execute_write(update_slide_keywords, (target_id, source_id))
        
        # Update element keywords
        update_element_keywords = """
            UPDATE OR REPLACE element_keywords 
            SET keyword_id = ? 
            WHERE keyword_id = ?
        """
        self._execute_write(update_element_keywords, (target_id, source_id))
        
        # Delete source keyword
        delete_query = "DELETE FROM keywords WHERE id = ?"
        self._execute_write(delete_query, (source_id,))
        
        self.logger.info(f"Merged keyword {source_id} into {target_id}")
        return True

    # Slide-keyword linking methods
    
    def link_slide_keyword(self, slide_id: int, keyword_id: int) -> bool:
        """
        Links a keyword to a slide.
        
        Args:
            slide_id: The slide ID.
            keyword_id: The keyword ID.
            
        Returns:
            True if successful (or already exists).
            
        Raises:
            DatabaseError: If the operation fails.
        """
        # Check if link already exists
        check_query = "SELECT 1 FROM slide_keywords WHERE slide_id = ? AND keyword_id = ?"
        results = self._execute_read(check_query, (slide_id, keyword_id))
        
        if results:
            self.logger.debug(f"Link between slide {slide_id} and keyword {keyword_id} already exists")
            return True
        
        # Create new link
        insert_query = "INSERT INTO slide_keywords (slide_id, keyword_id) VALUES (?, ?)"
        self._execute_write(insert_query, (slide_id, keyword_id))
        self.logger.debug(f"Linked keyword {keyword_id} to slide {slide_id}")
        return True

    def unlink_slide_keyword(self, slide_id: int, keyword_id: int) -> bool:
        """
        Unlinks a keyword from a slide.
        
        Args:
            slide_id: The slide ID.
            keyword_id: The keyword ID.
            
        Returns:
            True if successful.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = "DELETE FROM slide_keywords WHERE slide_id = ? AND keyword_id = ?"
        self._execute_write(query, (slide_id, keyword_id))
        self.logger.debug(f"Unlinked keyword {keyword_id} from slide {slide_id}")
        return True

    def get_keywords_for_slide(self, slide_id: int, kind: str = None) -> List[Keyword]:
        """
        Retrieves all keywords for a slide.
        
        Args:
            slide_id: The slide ID.
            kind: Optional keyword type filter.
            
        Returns:
            List of Keyword objects.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        if kind:
            query = """
                SELECT k.id, k.keyword, k.kind
                FROM keywords k
                JOIN slide_keywords sk ON k.id = sk.keyword_id
                WHERE sk.slide_id = ? AND k.kind = ?
                ORDER BY k.keyword COLLATE NOCASE
            """
            results = self._execute_read(query, (slide_id, kind))
        else:
            query = """
                SELECT k.id, k.keyword, k.kind
                FROM keywords k
                JOIN slide_keywords sk ON k.id = sk.keyword_id
                WHERE sk.slide_id = ?
                ORDER BY k.kind, k.keyword COLLATE NOCASE
            """
            results = self._execute_read(query, (slide_id,))
        
        keywords = []
        for row in results:
            keywords.append(Keyword(
                id=row['id'],
                keyword=row['keyword'],
                kind=row['kind']
            ))
        return keywords

    def replace_slide_keywords(self, slide_id: int, kind: str, keyword_texts: List[str]) -> bool:
        """
        Replaces all keywords of a specific kind for a slide.
        
        Args:
            slide_id: The slide ID.
            kind: The keyword type.
            keyword_texts: List of keyword texts to set.
            
        Returns:
            True if successful.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        # Remove existing keywords of this kind
        delete_query = """
            DELETE FROM slide_keywords
            WHERE slide_id = ? AND keyword_id IN (
                SELECT id FROM keywords WHERE kind = ?
            )
        """
        self._execute_write(delete_query, (slide_id, kind))
        
        # Add new keywords
        for keyword_text in keyword_texts:
            if keyword_text and keyword_text.strip():
                keyword_id = self.add_keyword_if_not_exists(keyword_text.strip(), kind)
                self.link_slide_keyword(slide_id, keyword_id)
        
        self.logger.debug(f"Replaced {kind} keywords for slide {slide_id}")
        return True

    def get_slide_count_for_project(self, project_id: int) -> int:
        """Get the total number of slides for a project."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(DISTINCT s.id)
                    FROM slides s
                    JOIN files f ON s.file_id = f.id
                    WHERE f.project_id = ?
                """, (project_id,))
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"Failed to get slide count for project {project_id}: {e}")
            return 0
            
    def get_file_count_for_project(self, project_id: int) -> int:
        """Get the total number of files for a project."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM files WHERE project_id = ?", (project_id,))
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"Failed to get file count for project {project_id}: {e}")
            return 0
            
    def get_keywords_for_project(self, project_id: int) -> List[Keyword]:
        """Get all keywords used in a project."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT k.id, k.text, k.kind, COUNT(*) as usage_count
                    FROM keywords k
                    JOIN slide_keywords sk ON k.id = sk.keyword_id
                    JOIN slides s ON sk.slide_id = s.id
                    JOIN files f ON s.file_id = f.id
                    WHERE f.project_id = ?
                    GROUP BY k.id, k.text, k.kind
                    ORDER BY k.text
                """, (project_id,))
                
                keywords = []
                for row in cursor.fetchall():
                    keyword = Keyword(
                        id=row[0],
                        text=row[1],
                        kind=KeywordKind(row[2]) if row[2] else KeywordKind.GENERIC
                    )
                    # Add usage_count as an attribute
                    keyword.usage_count = row[3]
                    keywords.append(keyword)
                    
                return keywords
        except Exception as e:
            self.logger.error(f"Failed to get keywords for project {project_id}: {e}")
            return []
            
    def get_slide_by_id(self, slide_id: int) -> Optional[Slide]:
        """Get a slide by its ID. Alias for get_slide method."""
        return self.get_slide(slide_id)

    def get_slides_for_keyword(self, keyword_id: int) -> List[Slide]:
        """
        Retrieves all slides associated with a keyword.
        
        Args:
            keyword_id: The keyword ID.
            
        Returns:
            List of Slide objects.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = """
            SELECT s.id, s.file_id, s.slide_index, s.title, 
                   s.thumb_rel_path, s.image_rel_path
            FROM slides s
            JOIN slide_keywords sk ON s.id = sk.slide_id
            WHERE sk.keyword_id = ?
            ORDER BY s.file_id, s.slide_index
        """
        results = self._execute_read(query, (keyword_id,))
        
        slides = []
        for row in results:
            slides.append(Slide(
                id=row['id'],
                file_id=row['file_id'],
                slide_index=row['slide_index'],
                title=row['title'],
                thumb_rel_path=row['thumb_rel_path'],
                image_rel_path=row['image_rel_path']
            ))
        return slides

    # Element-keyword linking methods
    
    def link_element_keyword(self, element_id: int, keyword_id: int) -> bool:
        """
        Links a keyword to an element.
        
        Args:
            element_id: The element ID.
            keyword_id: The keyword ID.
            
        Returns:
            True if successful (or already exists).
            
        Raises:
            DatabaseError: If the operation fails.
        """
        # Check if link already exists
        check_query = "SELECT 1 FROM element_keywords WHERE element_id = ? AND keyword_id = ?"
        results = self._execute_read(check_query, (element_id, keyword_id))
        
        if results:
            self.logger.debug(f"Link between element {element_id} and keyword {keyword_id} already exists")
            return True
        
        # Create new link
        insert_query = "INSERT INTO element_keywords (element_id, keyword_id) VALUES (?, ?)"
        self._execute_write(insert_query, (element_id, keyword_id))
        self.logger.debug(f"Linked keyword {keyword_id} to element {element_id}")
        return True

    def unlink_element_keyword(self, element_id: int, keyword_id: int) -> bool:
        """
        Unlinks a keyword from an element.
        
        Args:
            element_id: The element ID.
            keyword_id: The keyword ID.
            
        Returns:
            True if successful.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = "DELETE FROM element_keywords WHERE element_id = ? AND keyword_id = ?"
        self._execute_write(query, (element_id, keyword_id))
        self.logger.debug(f"Unlinked keyword {keyword_id} from element {element_id}")
        return True

    def get_keywords_for_element(self, element_id: int) -> List[Keyword]:
        """
        Retrieves all keywords for an element.
        
        Args:
            element_id: The element ID.
            
        Returns:
            List of Keyword objects.
            
        Raises:
            DatabaseError: If the operation fails.
        """
        query = """
            SELECT k.id, k.keyword, k.kind
            FROM keywords k
            JOIN element_keywords ek ON k.id = ek.keyword_id
            WHERE ek.element_id = ?
            ORDER BY k.kind, k.keyword COLLATE NOCASE
        """
        results = self._execute_read(query, (element_id,))
        
        keywords = []
        for row in results:
            keywords.append(Keyword(
                id=row['id'],
                keyword=row['keyword'],
                kind=row['kind']
            ))
        return keywords