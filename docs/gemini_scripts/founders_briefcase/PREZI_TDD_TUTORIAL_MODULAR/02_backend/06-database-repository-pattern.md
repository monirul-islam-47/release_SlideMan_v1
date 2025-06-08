# 🏦 Module 6: Database Layer TDD with Repository Pattern
## *Build PrezI's Memory Bank with Professional Data Access Patterns*

**Module:** 06 | **Phase:** Core Backend  
**Duration:** 6 hours | **Prerequisites:** Module 05 (Project Models TDD)  
**Learning Track:** Database Operations with Repository Pattern  

---

## 🎯 Module Objectives

By completing this module, you will:
- [ ] Master the Repository Pattern for clean data access
- [ ] Build a complete SQLite database for PrezI
- [ ] Apply TDD to database operations and integration testing
- [ ] Create thread-safe database connection management
- [ ] Implement comprehensive error handling for data operations
- [ ] Set up database migrations and schema versioning

---

## 🏦 Building PrezI's Memory Bank

Every great application needs a reliable way to store and retrieve data. PrezI needs to remember:
- **Projects and their details** (name, path, creation date)
- **Imported presentation files** (filename, slide count, metadata)
- **Individual slides and their content** (title, content, thumbnails)
- **Keywords and tags** for organization and search
- **Relationships** between all these entities

We're going to build this using the **Repository Pattern** - a professional design pattern that makes database operations testable, maintainable, and swappable.

Think of a repository like a **smart librarian** - you ask for "all projects created this month" and the librarian handles all the complex database queries behind the scenes.

---

## 🧩 The Repository Pattern Explained

Instead of scattering SQL queries throughout your code, the Repository pattern creates a clean interface:

### ❌ **Bad: SQL scattered everywhere**
```python
def get_user_projects(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE user_id = ?", (user_id,))
    return cursor.fetchall()

def create_project(name, user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO projects (name, user_id) VALUES (?, ?)", (name, user_id))
    conn.commit()
```

**Problems:**
- SQL mixed with business logic
- Connection management repeated
- Hard to test (real database required)
- No error handling standardization

### ✅ **Good: Repository pattern**
```python
class ProjectRepository:
    def find_by_user(self, user_id: str) -> List[Project]:
        """Clean, testable interface."""
        # Implementation hidden behind clean interface
        pass
    
    def save(self, project: Project) -> Project:
        """Save or update a project."""
        # Handles both insert and update logic
        pass
```

**Benefits:**
- Clean separation of concerns
- Easy to test with mock repositories
- Consistent error handling
- Swappable data stores (SQLite → PostgreSQL)

---

## 🏗️ Setting Up the Database Foundation

### Step 1: Database Schema Design

Create `backend/database/schema.sql`:

```sql
-- PrezI Database Schema
-- Built with TDD principles and designed for scalability

-- Core projects table
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    path TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Presentation files within projects
CREATE TABLE IF NOT EXISTS files (
    file_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    slide_count INTEGER DEFAULT 0,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE
);

-- Individual slides extracted from presentations
CREATE TABLE IF NOT EXISTS slides (
    slide_id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    slide_number INTEGER NOT NULL,
    title TEXT,
    content TEXT,
    notes TEXT,
    thumbnail_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files (file_id) ON DELETE CASCADE
);

-- Keywords for organization and tagging
CREATE TABLE IF NOT EXISTS keywords (
    keyword_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    color TEXT DEFAULT '#e5e7eb',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE,
    UNIQUE (project_id, name)
);

-- Many-to-many relationship between slides and keywords
CREATE TABLE IF NOT EXISTS slide_keywords (
    slide_id TEXT NOT NULL,
    keyword_id TEXT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (slide_id, keyword_id),
    FOREIGN KEY (slide_id) REFERENCES slides (slide_id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES keywords (keyword_id) ON DELETE CASCADE
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_files_project_id ON files (project_id);
CREATE INDEX IF NOT EXISTS idx_slides_file_id ON slides (file_id);
CREATE INDEX IF NOT EXISTS idx_slides_title ON slides (title);
CREATE INDEX IF NOT EXISTS idx_keywords_project_id ON keywords (project_id);
CREATE INDEX IF NOT EXISTS idx_keywords_name ON keywords (name);
CREATE INDEX IF NOT EXISTS idx_slide_keywords_slide_id ON slide_keywords (slide_id);
CREATE INDEX IF NOT EXISTS idx_slide_keywords_keyword_id ON slide_keywords (keyword_id);

-- Full-text search for slide content (SQLite FTS5)
CREATE VIRTUAL TABLE IF NOT EXISTS slides_fts USING fts5(
    slide_id UNINDEXED,
    title,
    content,
    notes,
    content='slides',
    content_rowid='rowid'
);

-- Triggers to maintain FTS index
CREATE TRIGGER IF NOT EXISTS slides_fts_insert AFTER INSERT ON slides BEGIN
    INSERT INTO slides_fts(slide_id, title, content, notes) 
    VALUES (new.slide_id, new.title, new.content, new.notes);
END;

CREATE TRIGGER IF NOT EXISTS slides_fts_update AFTER UPDATE ON slides BEGIN
    UPDATE slides_fts 
    SET title = new.title, content = new.content, notes = new.notes
    WHERE slide_id = new.slide_id;
END;

CREATE TRIGGER IF NOT EXISTS slides_fts_delete AFTER DELETE ON slides BEGIN
    DELETE FROM slides_fts WHERE slide_id = old.slide_id;
END;
```

### Step 2: Database Connection Manager

Create `backend/database/connection.py`:

```python
"""Database connection management for PrezI."""

import sqlite3
import threading
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database connections with thread safety."""
    
    def __init__(self, db_path: str = "prezi.db"):
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._ensure_database_exists()
    
    def _ensure_database_exists(self) -> None:
        """Create database and tables if they don't exist."""
        try:
            with self.get_connection() as conn:
                schema_path = Path(__file__).parent / "schema.sql"
                with open(schema_path, 'r') as f:
                    conn.executescript(f.read())
                logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup and transaction management."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0  # 30 second timeout for busy database
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable foreign keys (not enabled by default in SQLite)
            self._local.connection.execute("PRAGMA foreign_keys = ON")
        
        try:
            yield self._local.connection
        except Exception:
            self._local.connection.rollback()
            raise
        else:
            self._local.connection.commit()
    
    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            del self._local.connection
            logger.info("Database connection closed")
    
    def vacuum(self) -> None:
        """Optimize database file size and performance."""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
        logger.info("Database vacuumed")
```

---

## 🔴 RED PHASE: Writing Repository Tests

Now let's write tests for our ProjectRepository. Create `backend/tests/integration/test_project_repository.py`:

```python
"""Integration tests for ProjectRepository - TDD for database operations!"""

import pytest
import tempfile
import os
from datetime import datetime
from database.connection import DatabaseManager
from database.repositories import ProjectRepository, RepositoryError
from core.models.project import Project


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create temporary file
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Create database manager
    db_manager = DatabaseManager(path)
    
    yield db_manager
    
    # Cleanup
    db_manager.close()
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def project_repo(temp_db):
    """Create a ProjectRepository for testing."""
    return ProjectRepository(temp_db)


@pytest.fixture
def sample_project():
    """Create a sample project for testing."""
    return Project(
        name="Test Project",
        path="/test/path",
        description="A project for testing"
    )


class TestProjectRepository:
    """Test suite for ProjectRepository."""
    
    def test_save_new_project(self, project_repo, sample_project):
        """Test saving a new project to the database."""
        # Save the project
        saved_project = project_repo.save(sample_project)
        
        # Verify it was saved with all expected attributes
        assert saved_project.project_id is not None
        assert saved_project.name == "Test Project"
        assert saved_project.path == "/test/path"
        assert saved_project.description == "A project for testing"
        assert saved_project.created_at is not None
        assert isinstance(saved_project.created_at, datetime)
    
    def test_save_generates_unique_ids(self, project_repo):
        """Test that saving multiple projects generates unique IDs."""
        project1 = project_repo.save(Project(name="Project 1"))
        project2 = project_repo.save(Project(name="Project 2"))
        
        assert project1.project_id != project2.project_id
        assert len(project1.project_id) > 0
        assert len(project2.project_id) > 0
    
    def test_find_by_id(self, project_repo, sample_project):
        """Test finding a project by its ID."""
        # Save a project first
        saved_project = project_repo.save(sample_project)
        
        # Find it by ID
        found_project = project_repo.find_by_id(saved_project.project_id)
        
        # Verify we found the right one
        assert found_project is not None
        assert found_project.project_id == saved_project.project_id
        assert found_project.name == "Test Project"
        assert found_project.path == "/test/path"
        assert found_project.description == "A project for testing"
    
    def test_find_by_id_not_found(self, project_repo):
        """Test finding a project that doesn't exist."""
        result = project_repo.find_by_id("nonexistent-id")
        assert result is None
    
    def test_find_all_empty(self, project_repo):
        """Test finding all projects when database is empty."""
        all_projects = project_repo.find_all()
        assert all_projects == []
    
    def test_find_all_projects(self, project_repo):
        """Test retrieving all projects."""
        # Save multiple projects
        project1 = project_repo.save(Project(name="Project 1"))
        project2 = project_repo.save(Project(name="Project 2"))
        project3 = project_repo.save(Project(name="Project 3"))
        
        # Find all
        all_projects = project_repo.find_all()
        
        # Verify we got them all, in creation order (newest first)
        assert len(all_projects) == 3
        project_names = [p.name for p in all_projects]
        assert "Project 1" in project_names
        assert "Project 2" in project_names
        assert "Project 3" in project_names
    
    def test_update_existing_project(self, project_repo, sample_project):
        """Test updating an existing project."""
        # Save a project
        saved_project = project_repo.save(sample_project)
        original_id = saved_project.project_id
        
        # Update it
        saved_project.name = "Updated Name"
        saved_project.path = "/new/path"
        saved_project.description = "Updated description"
        
        updated_project = project_repo.save(saved_project)
        
        # Verify the update
        assert updated_project.name == "Updated Name"
        assert updated_project.path == "/new/path"
        assert updated_project.description == "Updated description"
        assert updated_project.project_id == original_id  # ID should not change
        
        # Verify it's actually updated in the database
        found_project = project_repo.find_by_id(original_id)
        assert found_project.name == "Updated Name"
    
    def test_delete_project(self, project_repo, sample_project):
        """Test deleting a project."""
        # Save a project
        saved_project = project_repo.save(sample_project)
        project_id = saved_project.project_id
        
        # Verify it exists
        assert project_repo.find_by_id(project_id) is not None
        
        # Delete it
        success = project_repo.delete(project_id)
        
        # Verify deletion
        assert success is True
        assert project_repo.find_by_id(project_id) is None
    
    def test_delete_nonexistent_project(self, project_repo):
        """Test deleting a project that doesn't exist."""
        success = project_repo.delete("nonexistent-id")
        assert success is False
    
    def test_find_by_name_pattern(self, project_repo):
        """Test finding projects by name pattern."""
        # Save projects with different names
        project_repo.save(Project(name="Client Project Alpha"))
        project_repo.save(Project(name="Client Project Beta"))
        project_repo.save(Project(name="Internal Presentation"))
        
        # Find projects matching pattern
        client_projects = project_repo.find_by_name_pattern("Client%")
        
        # Verify we found the right ones
        assert len(client_projects) == 2
        names = [p.name for p in client_projects]
        assert "Client Project Alpha" in names
        assert "Client Project Beta" in names
        assert "Internal Presentation" not in names
    
    def test_count_projects(self, project_repo):
        """Test counting total projects."""
        # Initially empty
        assert project_repo.count() == 0
        
        # Add some projects
        project_repo.save(Project(name="Project 1"))
        project_repo.save(Project(name="Project 2"))
        
        # Count should update
        assert project_repo.count() == 2
    
    @pytest.mark.integration
    def test_concurrent_access(self, project_repo):
        """Test that repository handles concurrent access safely."""
        import threading
        import time
        
        results = []
        errors = []
        
        def create_project(name):
            try:
                project = project_repo.save(Project(name=f"Concurrent {name}"))
                results.append(project)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_project, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify all succeeded
        assert len(errors) == 0
        assert len(results) == 5
        
        # Verify all have unique IDs
        ids = [p.project_id for p in results]
        assert len(set(ids)) == 5  # All unique
```

### Run the Tests (RED PHASE)

```bash
cd backend
pytest tests/integration/test_project_repository.py -v
```

**Expected output:**
```
ImportError: No module named 'database.repositories'
```

Perfect! **RED PHASE** complete. The tests fail because we haven't implemented the repository yet.

---

## 🟢 GREEN PHASE: Implementing the Repository

Now let's create the ProjectRepository. Create `backend/database/repositories.py`:

```python
"""Repository classes for PrezI database operations."""

from typing import List, Optional
from core.models.project import Project
from database.connection import DatabaseManager
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class ProjectRepository:
    """Repository for Project database operations with comprehensive error handling."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save(self, project: Project) -> Project:
        """Save a project to the database (insert or update)."""
        try:
            if self._project_exists(getattr(project, 'project_id', None)):
                return self._update(project)
            else:
                return self._insert(project)
        except Exception as e:
            logger.error(f"Error saving project {project.name}: {e}")
            raise RepositoryError(f"Failed to save project: {e}")
    
    def _project_exists(self, project_id: Optional[str]) -> bool:
        """Check if a project exists in the database."""
        if not project_id:
            return False
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM projects WHERE project_id = ?", 
                (project_id,)
            )
            return cursor.fetchone() is not None
    
    def _insert(self, project: Project) -> Project:
        """Insert a new project."""
        # Generate ID if not present
        if not hasattr(project, 'project_id') or not project.project_id:
            project.project_id = str(uuid.uuid4())
        
        with self.db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO projects (project_id, name, path, description, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                project.project_id,
                project.name,
                project.path,
                getattr(project, 'description', None),
                project.created_at.isoformat() if project.created_at else datetime.now().isoformat()
            ))
        
        logger.info(f"Created new project: {project.name} ({project.project_id})")
        return project
    
    def _update(self, project: Project) -> Project:
        """Update an existing project."""
        with self.db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE projects 
                SET name = ?, path = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE project_id = ?
            """, (
                project.name,
                project.path,
                getattr(project, 'description', None),
                project.project_id
            ))
        
        logger.info(f"Updated project: {project.name} ({project.project_id})")
        return project
    
    def find_by_id(self, project_id: str) -> Optional[Project]:
        """Find a project by its ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT project_id, name, path, description, created_at
                    FROM projects
                    WHERE project_id = ?
                """, (project_id,))
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_project(row)
                return None
        except Exception as e:
            logger.error(f"Error finding project {project_id}: {e}")
            raise RepositoryError(f"Failed to find project: {e}")
    
    def find_all(self) -> List[Project]:
        """Find all projects ordered by creation date (newest first)."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT project_id, name, path, description, created_at
                    FROM projects
                    ORDER BY created_at DESC
                """)
                
                return [self._row_to_project(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error finding all projects: {e}")
            raise RepositoryError(f"Failed to find projects: {e}")
    
    def find_by_name_pattern(self, pattern: str) -> List[Project]:
        """Find projects where name matches the SQL LIKE pattern."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT project_id, name, path, description, created_at
                    FROM projects
                    WHERE name LIKE ?
                    ORDER BY created_at DESC
                """, (pattern,))
                
                return [self._row_to_project(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error finding projects by pattern {pattern}: {e}")
            raise RepositoryError(f"Failed to find projects by pattern: {e}")
    
    def count(self) -> int:
        """Count total number of projects."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM projects")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error counting projects: {e}")
            raise RepositoryError(f"Failed to count projects: {e}")
    
    def delete(self, project_id: str) -> bool:
        """Delete a project by ID. Returns True if deleted, False if not found."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM projects WHERE project_id = ?
                """, (project_id,))
                
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Deleted project: {project_id}")
                else:
                    logger.warning(f"Attempted to delete non-existent project: {project_id}")
                
                return success
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {e}")
            raise RepositoryError(f"Failed to delete project: {e}")
    
    def _row_to_project(self, row) -> Project:
        """Convert a database row to a Project object."""
        # Parse datetime if it's a string
        created_at = row['created_at']
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        return Project(
            name=row['name'],
            path=row['path'],
            description=row['description'],
            created_at=created_at,
            project_id=row['project_id']
        )
```

### Update the Project Model

We need to update our Project model to support the description field. Update `backend/core/models/project.py`:

```python
"""Project model - built with TDD!"""

from datetime import datetime
from typing import Optional
from pathlib import Path
import uuid


class Project:
    """Represents a presentation project in PrezI.
    
    Each project manages a collection of PowerPoint presentations
    and provides organization capabilities for slides.
    """
    
    def __init__(
        self, 
        name: str, 
        path: Optional[str] = None,
        description: Optional[str] = None,
        created_at: Optional[datetime] = None,
        project_id: Optional[str] = None
    ):
        """Initialize a new project.
        
        Args:
            name: The project name (required, non-empty)
            path: File system path for project files
            description: Optional project description
            created_at: When the project was created (defaults to now)
            project_id: Unique identifier (auto-generated if not provided)
        
        Raises:
            ValueError: If name is empty or invalid
        """
        self._validate_name(name)
        
        self.name = name.strip()
        self.path = path
        self.description = description
        self.created_at = created_at or datetime.now()
        self.project_id = project_id or str(uuid.uuid4())
    
    def _validate_name(self, name: Optional[str]) -> None:
        """Validate the project name."""
        if not name or not isinstance(name, str) or not name.strip():
            raise ValueError("Project name cannot be empty")
    
    def __str__(self) -> str:
        """String representation of the project."""
        return f"Project(name='{self.name}', id='{self.project_id[:8]}...')"
    
    def __repr__(self) -> str:
        """Developer representation of the project."""
        return (f"Project(name='{self.name}', path='{self.path}', "
                f"description='{self.description}', "
                f"created_at='{self.created_at}', project_id='{self.project_id}')")
    
    def __eq__(self, other) -> bool:
        """Compare projects for equality based on project_id."""
        if not isinstance(other, Project):
            return False
        return self.project_id == other.project_id
```

### Run the Tests Again (GREEN PHASE)

```bash
pytest tests/integration/test_project_repository.py -v
```

**Expected output:**
```
====================== 12 passed in 0.15s ======================
```

🎉 **GREEN!** All tests passing!

---

## 🔵 REFACTOR PHASE: Adding Professional Features

Let's refactor to add more professional features and better error handling:

### Add Database Initialization Script

Create `backend/database/__init__.py`:
```python
"""Database package initialization."""

from .connection import DatabaseManager
from .repositories import ProjectRepository, RepositoryError

__all__ = ['DatabaseManager', 'ProjectRepository', 'RepositoryError']
```

### Add Connection Pooling (Advanced)

Update `backend/database/connection.py` to add connection pooling:

```python
"""Database connection management for PrezI with connection pooling."""

import sqlite3
import threading
import queue
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
import logging
import time

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database connections with thread safety and connection pooling."""
    
    def __init__(self, db_path: str = "prezi.db", pool_size: int = 10):
        self.db_path = Path(db_path)
        self.pool_size = pool_size
        self._pool = queue.Queue(maxsize=pool_size)
        self._pool_lock = threading.Lock()
        self._local = threading.local()
        
        self._ensure_database_exists()
        self._initialize_pool()
    
    def _ensure_database_exists(self) -> None:
        """Create database and tables if they don't exist."""
        try:
            conn = self._create_connection()
            schema_path = Path(__file__).parent / "schema.sql"
            with open(schema_path, 'r') as f:
                conn.executescript(f.read())
            conn.close()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _initialize_pool(self) -> None:
        """Initialize the connection pool."""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            self._pool.put(conn)
        logger.info(f"Database connection pool initialized with {self.pool_size} connections")
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with standard settings."""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging for better concurrency
        return conn
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup and transaction management."""
        # Try to get connection from pool
        try:
            conn = self._pool.get_nowait()
        except queue.Empty:
            # Pool exhausted, create temporary connection
            conn = self._create_connection()
            pool_connection = False
        else:
            pool_connection = True
        
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        else:
            conn.commit()
        finally:
            if pool_connection:
                # Return to pool
                try:
                    self._pool.put_nowait(conn)
                except queue.Full:
                    # Pool is full (shouldn't happen), close connection
                    conn.close()
            else:
                # Close temporary connection
                conn.close()
    
    def close(self) -> None:
        """Close all pooled connections."""
        closed_count = 0
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
                closed_count += 1
            except queue.Empty:
                break
        logger.info(f"Closed {closed_count} pooled database connections")
    
    def vacuum(self) -> None:
        """Optimize database file size and performance."""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
        logger.info("Database vacuumed")
    
    def get_stats(self) -> dict:
        """Get database statistics."""
        with self.get_connection() as conn:
            stats = {}
            
            # Get table sizes
            cursor = conn.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            
            # Get database file size
            stats['file_size_bytes'] = self.db_path.stat().st_size if self.db_path.exists() else 0
            stats['pool_size'] = self.pool_size
            stats['available_connections'] = self._pool.qsize()
            
            return stats
```

---

## 🚀 Integration with FastAPI

Now let's integrate our repository with FastAPI. Create `backend/api/v1/projects.py`:

```python
"""Project API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from core.schemas.project_schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from database.repositories import ProjectRepository, RepositoryError
from database.connection import DatabaseManager

router = APIRouter(prefix="/projects", tags=["projects"])

# Dependency injection for database
def get_db_manager():
    return DatabaseManager()

def get_project_repository(db_manager: DatabaseManager = Depends(get_db_manager)):
    return ProjectRepository(db_manager)


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    repo: ProjectRepository = Depends(get_project_repository)
):
    """Create a new project."""
    try:
        from core.models.project import Project
        project = Project(
            name=project_data.name,
            path=project_data.path,
            description=project_data.description
        )
        saved_project = repo.save(project)
        return ProjectResponse.from_project(saved_project)
    except RepositoryError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(repo: ProjectRepository = Depends(get_project_repository)):
    """Get all projects."""
    try:
        projects = repo.find_all()
        return [ProjectResponse.from_project(p) for p in projects]
    except RepositoryError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    repo: ProjectRepository = Depends(get_project_repository)
):
    """Get a specific project by ID."""
    try:
        project = repo.find_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return ProjectResponse.from_project(project)
    except RepositoryError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🎪 Your Second CI/CD Integration

Commit your database work:

```bash
# Stage changes
git add database/ tests/integration/ core/models/

# Professional commit message
git commit -m "feat(database): implement Repository pattern with SQLite

- Add comprehensive database schema with foreign keys and indexes
- Implement ProjectRepository with full CRUD operations
- Add thread-safe DatabaseManager with connection pooling
- Include FTS5 full-text search capability for slides
- Add comprehensive integration tests with 100% coverage
- Implement professional error handling and logging

Tests: 12 passing integration tests
Architecture: Clean separation with Repository pattern
Performance: Connection pooling and WAL mode enabled"

# Push to trigger CI/CD
git push origin main
```

---

## 🧠 What You Just Learned

### Repository Pattern Mastery
✅ **Clean Architecture**: Separated data access from business logic  
✅ **Testability**: Easy to test with temporary databases  
✅ **Maintainability**: Centralized database operations  
✅ **Flexibility**: Easy to swap SQLite for PostgreSQL later  

### Database Design Excellence
✅ **Relational Design**: Proper foreign keys and constraints  
✅ **Performance**: Strategic indexes for fast queries  
✅ **Search**: FTS5 full-text search for slide content  
✅ **Integrity**: Transaction safety and error handling  

### Professional Practices
✅ **Connection Management**: Thread-safe pooling  
✅ **Error Handling**: Comprehensive exception hierarchy  
✅ **Logging**: Proper debug and audit trails  
✅ **Testing**: Integration tests with real database operations  

---

## 🚀 What's Next?

In the next module, **API Layer TDD: RESTful Services with FastAPI**, you'll:
- Build the complete REST API for PrezI
- Apply TDD to HTTP endpoints and request/response handling
- Implement API authentication and validation
- Create automated API testing with TestClient
- Add OpenAPI documentation and interactive testing

### Preparation for Next Module
- [ ] All repository tests passing
- [ ] Database operations working correctly
- [ ] Understanding of Repository pattern
- [ ] Familiarity with dependency injection concepts

---

## ✅ Module 6 Completion Checklist

Before proceeding to the next module, ensure you can:
- [ ] Explain the Repository pattern and its benefits
- [ ] Create and manage SQLite databases with proper schema
- [ ] Write integration tests for database operations
- [ ] Handle database errors and edge cases appropriately
- [ ] Use connection pooling and thread safety measures
- [ ] Implement full CRUD operations with TDD
- [ ] Understand database transactions and rollbacks

**Module Status:** ⬜ Complete | **Next Module:** [07-fastapi-rest-services.md](07-fastapi-rest-services.md)

---

## 💡 Pro Tips for Database TDD

### 1. Use Temporary Databases for Tests
Always create isolated test databases:
```python
@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield DatabaseManager(path)
    os.unlink(path)
```

### 2. Test Edge Cases
Don't just test the happy path:
```python
def test_repository_handles_database_errors(mocker, project_repo):
    # Mock database to raise exception
    mocker.patch.object(project_repo.db_manager, 'get_connection', side_effect=sqlite3.Error("Database error"))
    
    with pytest.raises(RepositoryError):
        project_repo.find_all()
```

### 3. Use Transactions for Data Integrity
Ensure atomic operations:
```python
def transfer_slides(self, from_project_id: str, to_project_id: str, slide_ids: List[str]):
    with self.db_manager.get_connection() as conn:
        # All operations succeed or all fail
        for slide_id in slide_ids:
            conn.execute("UPDATE slides SET project_id = ? WHERE slide_id = ?", 
                        (to_project_id, slide_id))
```

### 4. Performance Test with Realistic Data
Test with appropriate data volumes:
```python
@pytest.mark.slow
def test_find_all_performance_with_large_dataset(project_repo):
    # Create 1000 projects
    for i in range(1000):
        project_repo.save(Project(name=f"Project {i}"))
    
    import time
    start = time.time()
    projects = project_repo.find_all()
    duration = time.time() - start
    
    assert len(projects) == 1000
    assert duration < 0.1  # Should be fast with proper indexing
```