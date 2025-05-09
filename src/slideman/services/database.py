# src/slideman/services/database.py

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Any, Tuple

# Import models to potentially use for return types later
from ..models.project import Project
from ..models.file import File
from ..models.slide import Slide
from ..models.element import Element
from ..models.keyword import Keyword, KeywordKind

# Import thread-safety related classes
from PySide6.QtCore import QMutex, QMutexLocker

# Define the current schema version. Increment this when schema changes.
DB_SCHEMA_VERSION = 2

class Database:
    """
    Handles all interactions with the application's SQLite database.
    Manages connection, schema creation, and CRUD operations.
    """
    def __init__(self, db_path: Path):
        """
        Initializes the Database service.

        Args:
            db_path: The path to the SQLite database file.
        """
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Database service initialized for path: {self.db_path}")
        
        # Initialize mutex for thread safety during write operations
        self._write_mutex = QMutex()

    def connect(self) -> bool:
        """
        Establishes a connection to the SQLite database file.
        Initializes the schema if the database is new or needs migration.

        Returns:
            True if connection is successful, False otherwise.
        """
        if self._conn:
            self.logger.warning("Database connection already established.")
            return True # Already connected

        try:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            # Connect to the database. Creates the file if it doesn't exist.
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False) # check_same_thread=False needed for QThreadPool potentially? Revisit if issues arise.
            # Use Row factory for dictionary-like access to columns
            self._conn.row_factory = sqlite3.Row
            # Enable foreign key constraint enforcement (off by default in sqlite3)
            self._conn.execute("PRAGMA foreign_keys = ON;")
            self.logger.info(f"Successfully connected to database at: {self.db_path}")
            # Initialize or migrate the schema
            self._initialize_schema()
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error connecting to database at {self.db_path}: {e}", exc_info=True)
            self._conn = None # Ensure connection is None on failure
            return False
        except OSError as e:
            self.logger.error(f"OS Error, likely permissions, accessing database path {self.db_path}: {e}", exc_info=True)
            self._conn = None
            return False


    def close(self):
        """Closes the database connection if it's open."""
        if self._conn:
            self.logger.info("Closing database connection.")
            self._conn.close()
            self._conn = None
        else:
            self.logger.debug("Attempted to close an already closed database connection.")

    def _get_db_version(self) -> int:
        """Retrieves the current user_version pragma from the database."""
        if not self._conn: return -1
        try:
            cursor = self._conn.cursor()
            cursor.execute("PRAGMA user_version;")
            result = cursor.fetchone()
            return result[0] if result else 0
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get database version: {e}", exc_info=True)
            return -1 # Indicate error

    def _set_db_version(self, version: int):
        """Sets the user_version pragma."""
        if not self._conn: return
        try:
            self._conn.execute(f"PRAGMA user_version = {version};")
            self.logger.info(f"Database user_version set to {version}")
        except sqlite3.Error as e:
            self.logger.error(f"Failed to set database version to {version}: {e}", exc_info=True)


    def _ensure_fts_tables_exist(self):
        """Checks if the FTS5 tables exist and creates them if they don't."""
        if not self._conn:
            self.logger.error("Cannot check FTS tables, no database connection.")
            return False

        try:
            cursor = self._conn.cursor()
            # Create virtual table if not exists
            cursor.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS keywords_fts USING fts5(
                keyword,
                kind,
                content='keywords',
                content_rowid='id'
            );""")
            # Create triggers if not exist
            cursor.execute("""CREATE TRIGGER IF NOT EXISTS keywords_ai AFTER INSERT ON keywords BEGIN
                INSERT INTO keywords_fts(rowid, keyword, kind) VALUES (new.id, new.keyword, new.kind);
            END;""")
            cursor.execute("""CREATE TRIGGER IF NOT EXISTS keywords_au AFTER UPDATE ON keywords BEGIN
                INSERT INTO keywords_fts(keywords_fts, rowid, keyword, kind) VALUES('delete', old.id, old.keyword, old.kind);
                INSERT INTO keywords_fts(rowid, keyword, kind) VALUES (new.id, new.keyword, new.kind);
            END;""")
            cursor.execute("""CREATE TRIGGER IF NOT EXISTS keywords_ad AFTER DELETE ON keywords BEGIN
                INSERT INTO keywords_fts(keywords_fts, rowid, keyword, kind) VALUES('delete', old.id, old.keyword, old.kind);
            END;""")
            # Populate FTS table if empty
            cursor.execute("SELECT COUNT(*) FROM keywords_fts;")
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute("INSERT INTO keywords_fts(rowid, keyword, kind) SELECT id, keyword, kind FROM keywords;")
            self._conn.commit()
            self.logger.debug("FTS5 table and triggers ensured and populated if needed.")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error ensuring FTS tables exist: {e}", exc_info=True)
            self._conn.rollback()
            return False

    def get_slide_origin(self, slide_id: int) -> Optional[Tuple[str, int]]:
        """
        Retrieves the original file path and slide index for a given slide ID.
        
        Args:
            slide_id: The ID of the slide to look up
            
        Returns:
            Tuple containing (full_path_to_source_file, original_slide_index) or None if not found
        """
        if not self._conn:
            self.logger.error(f"Cannot get slide origin, no database connection for slide ID: {slide_id}")
            return None
        
        try:
            cursor = self._conn.cursor()
            query = """
                SELECT p.folder_path, f.rel_path, s.slide_index 
                FROM slides s 
                JOIN files f ON s.file_id = f.id 
                JOIN projects p ON f.project_id = p.id 
                WHERE s.id = ?
            """
            cursor.execute(query, (slide_id,))
            result = cursor.fetchone()
            
            if not result:
                self.logger.warning(f"No slide origin found for slide ID: {slide_id}")
                return None
                
            folder_path, rel_path, slide_index = result
            
            # Combine folder_path and rel_path to get full path
            full_path = Path(folder_path) / rel_path
            
            self.logger.debug(f"Found origin for slide ID {slide_id}: {full_path}, index {slide_index}")
            return (str(full_path), slide_index)
            
        except sqlite3.Error as e:
            self.logger.error(f"SQL error retrieving slide origin for slide ID {slide_id}: {e}", exc_info=True)
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving slide origin for slide ID {slide_id}: {e}", exc_info=True)
            return None
            
    def search_keywords(self, query_term: str, kind: Optional[KeywordKind] = None, project_id: Optional[int] = None) -> List[Keyword]:
        """
        Searches for keywords matching the given query term, optionally filtered by kind and project.
        Uses FTS5 for efficient full-text search with prefix matching.
        """
        keywords = []
        if not self._conn or not query_term:
            return keywords
            
        query_term = query_term.strip() + '*'  # Add * for prefix matching
        
        # First, try using FTS5 for efficient search
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM keywords_fts")
            fts_count = cursor.fetchone()[0]
            
            if fts_count > 0:
                # FTS5 search is available, use it
                base_sql = """
                    SELECT DISTINCT k.id, k.keyword, k.kind
                    FROM keywords k
                    JOIN keywords_fts fts ON k.id = fts.rowid
                    WHERE fts MATCH ?
                """
                params = [query_term]
                
                # Apply kind filter if provided
                if kind:
                    base_sql += " AND k.kind = ?"
                    params.append(kind)
                    
                # Filter by project if project_id is provided
                if project_id is not None:
                    base_sql += """
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
                    """
                    params.extend([project_id, project_id])
                    
                base_sql += " ORDER BY k.keyword COLLATE NOCASE"
                
                cursor.execute(base_sql, params)
                for row in cursor.fetchall():
                    keywords.append(Keyword(**dict(row)))
                self.logger.debug(f"Found {len(keywords)} keywords matching '{query_term}' using FTS5")
                return keywords
            else:
                self.logger.warning("FTS5 table exists but is empty. Will try fallback search.")
                # Fall through to fallback search
                
        except sqlite3.Error as e:
            self.logger.warning(f"Error searching with FTS5 (will fallback to direct search): {e}")
            # Fall through to fallback search

        # Fallback: Use LIKE search directly on the keywords table
        try:
            fallback_sql = "SELECT id, keyword, kind FROM keywords WHERE keyword LIKE ? COLLATE NOCASE"
            params = [f"{query_term.rstrip('*')}%"]  # Use LIKE with % for wildcard
            
            # Apply kind filter if provided
            if kind:
                fallback_sql += " AND kind = ?"
                params.append(kind)
            
            # Add project filter if needed
            if project_id is not None:
                fallback_sql += """
                    AND id IN (
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
                """
                params.extend([project_id, project_id])
            
            fallback_sql += " ORDER BY keyword COLLATE NOCASE"
            
            cursor = self._conn.cursor()
            cursor.execute(fallback_sql, params)
            for row in cursor.fetchall():
                keywords.append(Keyword(**dict(row)))
            self.logger.debug(f"Found {len(keywords)} keywords matching '{query_term}' using fallback search")
        except sqlite3.Error as e:
            self.logger.error(f"Database error during fallback search for '{query_term}': {e}", exc_info=True)
        
        return keywords
        
    def _initialize_schema(self):
        """Checks the database version and creates/migrates the schema."""
        if not self._conn:
            self.logger.error("Cannot initialize schema, no database connection.")
            return

        current_version = self._get_db_version()
        self.logger.info(f"Current DB version: {current_version}. Required version: {DB_SCHEMA_VERSION}")

        if current_version < DB_SCHEMA_VERSION:
            self.logger.info("Database schema needs initialization or migration.")
            # --- Migration Logic ---
            # Simple case: If version 0, create everything
            if current_version == 0:
                self.logger.info("Creating initial database schema...")
                try:
                    self._create_tables()
                    self._create_indices() # Separate step for clarity
                    # Set version AFTER successful creation
                    self._set_db_version(DB_SCHEMA_VERSION)
                    self._conn.commit() # Commit schema changes
                    self.logger.info("Initial schema created successfully.")
                except sqlite3.Error as e:
                    self.logger.error(f"Failed to create initial schema: {e}", exc_info=True)
                    self._conn.rollback() # Rollback partial changes on error
                    raise # Re-raise the exception to signal failure
            else:
                # Placeholder for future migrations
                # if current_version < 2:
                #     self._apply_migration_to_v2()
                # if current_version < 3:
                #     self._apply_migration_to_v3()
                # self._set_db_version(DB_SCHEMA_VERSION) # Set final version after all migrations
                # self._conn.commit()
                self.logger.warning(f"Migration from version {current_version} to {DB_SCHEMA_VERSION} not yet implemented.")
                # For now, we might treat this as an error or just proceed
                # raise NotImplementedError(f"Migration from {current_version} needed.")

        elif current_version == DB_SCHEMA_VERSION:
            # Always ensure FTS tables exist, even for existing databases
            self._ensure_fts_tables_exist()
            self.logger.debug("Database schema is up to date.")
        else:
            # This case should ideally not happen if versions only increase
            self.logger.error(f"Database version {current_version} is newer than expected application version {DB_SCHEMA_VERSION}. Application might be outdated.")
            # Handle this case - maybe raise an error?
            
        # Always ensure FTS tables exist, even for existing databases
        self._ensure_fts_tables_exist()

    def _create_tables(self):
        """Executes the SQL statements to create all necessary tables."""
        if not self._conn: return
        cursor = self._conn.cursor()
        self.logger.debug("Executing CREATE TABLE statements...")

        # --- PROJECTS Table ---
        cursor.execute("""
            CREATE TABLE projects (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                folder_path   TEXT    NOT NULL UNIQUE,
                created_at    TEXT    DEFAULT (datetime('now', 'localtime'))
            );
        """) # Used 'localtime' for default timestamp

        # --- FILES Table (Add conversion_status) ---
        cursor.execute("""
            CREATE TABLE files (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id    INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                filename      TEXT    NOT NULL,
                rel_path      TEXT    NOT NULL,
                slide_count   INTEGER,
                checksum      TEXT,
                conversion_status TEXT DEFAULT 'Pending' CHECK(conversion_status IN ('Pending', 'In Progress', 'Completed', 'Failed')),
                UNIQUE(project_id, rel_path)
            );
        """)
        self.logger.debug("FILES table schema updated.")

        # --- SLIDES Table (Change path columns) ---
        cursor.execute("""
            CREATE TABLE slides (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id       INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
                slide_index   INTEGER NOT NULL, -- 1-based index within file
                thumb_rel_path TEXT, -- Relative to project folder
                image_rel_path TEXT, -- Relative to project folder
                UNIQUE(file_id, slide_index)
            );
        """)
        self.logger.debug("SLIDES table schema updated.")

        # --- ELEMENTS Table ---
        cursor.execute("""
            CREATE TABLE elements (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                slide_id      INTEGER NOT NULL REFERENCES slides(id) ON DELETE CASCADE,
                element_type  TEXT    NOT NULL, -- E.g., SHAPE, PICTURE, CHART
                bbox_x        REAL    NOT NULL, -- EMU units
                bbox_y        REAL    NOT NULL, -- EMU units
                bbox_w        REAL    NOT NULL, -- EMU units
                bbox_h        REAL    NOT NULL  -- EMU units
            );
        """)

        # --- KEYWORDS Table ---
        cursor.execute("""
            CREATE TABLE keywords (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword       TEXT    NOT NULL COLLATE NOCASE UNIQUE, -- Case-insensitive uniqueness
                kind          TEXT    NOT NULL CHECK (kind IN ('topic','title','name'))
            );
        """)
        
        # --- KEYWORDS_FTS Virtual Table (for full-text search) ---
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS keywords_fts USING fts5(
                keyword,
                kind,
                content='keywords',
                content_rowid='id'
            );
        """)
        
        # --- Triggers to keep FTS in sync with keywords table ---
        # Insert trigger
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS keywords_ai AFTER INSERT ON keywords BEGIN
                INSERT INTO keywords_fts(rowid, keyword, kind) VALUES (new.id, new.keyword, new.kind);
            END;
        """)
        
        # Update trigger
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS keywords_au AFTER UPDATE ON keywords BEGIN
                INSERT INTO keywords_fts(keywords_fts, rowid, keyword, kind) VALUES('delete', old.id, old.keyword, old.kind);
                INSERT INTO keywords_fts(rowid, keyword, kind) VALUES (new.id, new.keyword, new.kind);
            END;
        """)
        
        # Delete trigger
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS keywords_ad AFTER DELETE ON keywords BEGIN
                INSERT INTO keywords_fts(keywords_fts, rowid, keyword, kind) VALUES('delete', old.id, old.keyword, old.kind);
            END;
        """)
        
        # --- SLIDE_KEYWORDS Link Table ---
        cursor.execute("""
            CREATE TABLE slide_keywords (
                slide_id      INTEGER NOT NULL REFERENCES slides(id)    ON DELETE CASCADE,
                keyword_id    INTEGER NOT NULL REFERENCES keywords(id)  ON DELETE CASCADE,
                PRIMARY KEY (slide_id, keyword_id)
            ) WITHOUT ROWID; -- Optimization for link tables
        """) # Added WITHOUT ROWID

        # --- ELEMENT_KEYWORDS Link Table ---
        cursor.execute("""
            CREATE TABLE element_keywords (
                element_id    INTEGER NOT NULL REFERENCES elements(id)  ON DELETE CASCADE,
                keyword_id    INTEGER NOT NULL REFERENCES keywords(id)  ON DELETE CASCADE,
                PRIMARY KEY (element_id, keyword_id)
            ) WITHOUT ROWID; -- Optimization for link tables
        """) # Added WITHOUT ROWID

        self.logger.debug("Finished executing CREATE TABLE statements for Schema v2.")

    def _create_indices(self):
        """Executes SQL statements to create recommended indices."""
        if not self._conn: return
        cursor = self._conn.cursor()
        self.logger.debug("Executing CREATE INDEX statements...")

        # Indices for foreign keys often queried
        cursor.execute("CREATE INDEX idx_files_project_id ON files(project_id);")
        cursor.execute("CREATE INDEX idx_slides_file_id ON slides(file_id);")
        cursor.execute("CREATE INDEX idx_elements_slide_id ON elements(slide_id);")

        # Indices for link tables (reverse lookup)
        cursor.execute("CREATE INDEX idx_slide_keywords_keyword_id ON slide_keywords(keyword_id);")
        cursor.execute("CREATE INDEX idx_element_keywords_keyword_id ON element_keywords(keyword_id);")

        # Index on keyword text for faster lookups (though FTS5 will be better for search)
        cursor.execute("CREATE INDEX idx_keywords_keyword ON keywords(keyword COLLATE NOCASE);")

        self.logger.debug("Finished executing CREATE INDEX statements.")

    def get_slide_thumbnail_path(self, slide_id: int) -> Optional[str]:
        """Retrieves the relative path to the thumbnail image for a slide."""
        if not self._conn: return None
        sql = "SELECT thumb_rel_path FROM slides WHERE id = ?"
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, (slide_id,))
            result = cursor.fetchone()
            return result['thumb_rel_path'] if result and result['thumb_rel_path'] else None
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting thumbnail path for SlideID {slide_id}: {e}")
            return None

    def get_slide_image_path(self, slide_id: int) -> Optional[str]:
        """Retrieve the relative image path for a given slide ID."""
        if not self._conn:
            return None
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT image_rel_path FROM slides WHERE id = ?", (slide_id,))
            row = cursor.fetchone()
            # Return the relative image path if found
            if row and row[0]:
                return row[0]
        except sqlite3.Error as e:
            self.logger.error(f"Error getting image path for slide {slide_id}: {e}", exc_info=True)
        return None
            
    def get_slides_for_file(self, file_id: int) -> List[Slide]:
         """Retrieves all slide records for a given file_id, ordered by index."""
         slides = []
         if not self._conn: return slides
         
         sql = """SELECT id, file_id, slide_index, thumb_rel_path, image_rel_path
                  FROM slides
                  WHERE file_id = ?
                  ORDER BY slide_index ASC;"""
         try:
              cursor = self._conn.cursor()
              cursor.execute(sql, (file_id,))
              for row in cursor.fetchall():
                   # Map row to Slide dataclass - matching the actual fields in the Slide model
                   slides.append(Slide(
                       id=row[0],
                       file_id=row[1],
                       slide_index=row[2],
                       title="",  # Not in schema yet
                       thumb_rel_path=row[3],
                       image_rel_path=row[4]
                   ))
              self.logger.debug(f"Retrieved {len(slides)} slides for file ID {file_id}.")
         except sqlite3.Error as e:
              self.logger.error(f"Database error fetching slides for file ID {file_id}: {e}", exc_info=True)
         return slides

    def get_elements_for_slide(self, slide_id: int) -> List[Element]:
        """Retrieves all element records for a given slide_id."""
        elements = []
        if not self._conn: return elements
        sql = """SELECT id, slide_id, element_type, bbox_x, bbox_y, bbox_w, bbox_h
                 FROM elements
                 WHERE slide_id = ?;"""
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, (slide_id,))
            for row in cursor.fetchall():
                # Convert row dictionary to kwargs for Element constructor
                element_data = dict(row)
                elements.append(Element(**element_data))
            self.logger.debug(f"Retrieved {len(elements)} elements for slide ID {slide_id}.")
        except sqlite3.Error as e:
            self.logger.error(f"Database error fetching elements for slide ID {slide_id}: {e}", exc_info=True)
        return elements
            
    # --- CRUD Methods for Projects ---

    def add_project(self, name: str, folder_path: str) -> Optional[int]:
        """
        Adds a new project entry to the database.

        Args:
            name: The name of the project.
            folder_path: The absolute path to the project's folder.

        Returns:
            The integer ID of the newly inserted project, or None on failure.
        """
        if not self._conn:
            self.logger.error("Cannot add project, no database connection.")
            return None
        sql = "INSERT INTO projects (name, folder_path) VALUES (?, ?)"
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, (name, folder_path))
            self._conn.commit()
            new_id = cursor.lastrowid
            self.logger.info(f"Added project '{name}' with ID: {new_id} at path: {folder_path}")
            return new_id
        except sqlite3.IntegrityError as e:
            # Likely UNIQUE constraint violation on folder_path
            self.logger.error(f"Failed to add project '{name}'. IntegrityError (duplicate path?): {e}")
            self._conn.rollback()
            return None
        except sqlite3.Error as e:
            self.logger.error(f"Database error adding project '{name}': {e}", exc_info=True)
            self._conn.rollback()
            return None

    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """Retrieves a single project by its primary key ID."""
        if not self._conn: return None
        sql = "SELECT id, name, folder_path, created_at FROM projects WHERE id = ?"
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, (project_id,))
            row = cursor.fetchone()
            if row:
                # Map the sqlite3.Row object to the Project dataclass
                return Project(id=row['id'], name=row['name'], folder_path=row['folder_path'], created_at=row['created_at'])
            else:
                return None # Not found
        except sqlite3.Error as e:
            self.logger.error(f"Database error fetching project ID {project_id}: {e}", exc_info=True)
            return None

    def get_project_by_path(self, folder_path: str) -> Optional[Project]:
         """Retrieves a single project by its unique folder path."""
         if not self._conn: return None
         sql = "SELECT id, name, folder_path, created_at FROM projects WHERE folder_path = ?"
         try:
             cursor = self._conn.cursor()
             cursor.execute(sql, (folder_path,))
             row = cursor.fetchone()
             return Project(**row) if row else None # Alternate mapping using **row
         except sqlite3.Error as e:
             self.logger.error(f"Database error fetching project path {folder_path}: {e}", exc_info=True)
             return None

    def get_project_id_by_path(self, project_path: str) -> Optional[int]:
        """
        Retrieves a project ID by its folder path.
        
        Args:
            project_path: The folder path of the project
            
        Returns:
            The project ID if found, None otherwise
        """
        if not self._conn:
            self.logger.error("No database connection")
            return None
            
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT id FROM projects WHERE folder_path = ?",
                (project_path,)
            )
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving project ID by path: {e}")
            return None

    def get_all_projects(self) -> List[Project]:
        """Retrieves all projects, ordered by name."""
        projects = []
        if not self._conn: return projects
        sql = "SELECT id, name, folder_path, created_at FROM projects ORDER BY name COLLATE NOCASE;"
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql)
            for row in cursor.fetchall():
                projects.append(Project(**row)) # Map rows to Project objects
            self.logger.debug(f"Retrieved {len(projects)} projects.")
        except sqlite3.Error as e:
            self.logger.error(f"Database error fetching all projects: {e}", exc_info=True)
        return projects

    def rename_project(self, project_id: int, new_name: str) -> bool:
        """Updates the name of an existing project."""
        if not self._conn: return False
        sql = "UPDATE projects SET name = ? WHERE id = ?"
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, (new_name, project_id))
            updated_rows = cursor.rowcount
            self._conn.commit()
            if updated_rows > 0:
                self.logger.info(f"Renamed project ID {project_id} to '{new_name}'.")
                return True
            else:
                self.logger.warning(f"Attempted to rename project ID {project_id}, but project not found.")
                return False
        except sqlite3.Error as e:
            self.logger.error(f"Database error renaming project ID {project_id}: {e}", exc_info=True)
            self._conn.rollback()
            return False

    def update_project_details(self, project_id: int, new_name: str, new_folder_path: str) -> bool:
        """Updates the name and folder path of an existing project."""
        if not self._conn: return False
        sql = "UPDATE projects SET name = ?, folder_path = ? WHERE id = ?"
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, (new_name, new_folder_path, project_id))
            updated_rows = cursor.rowcount
            self._conn.commit()
            if updated_rows > 0:
                self.logger.info(f"Updated details for project ID {project_id} to Name='{new_name}', Path='{new_folder_path}'.")
                return True
            else:
                self.logger.warning(f"Attempted to update project ID {project_id}, but project not found.")
                return False
        except sqlite3.IntegrityError as e:
             self.logger.error(f"Failed to update project {project_id}. IntegrityError (duplicate path?): {e}")
             self._conn.rollback()
             return False
        except sqlite3.Error as e:
            self.logger.error(f"Database error updating project ID {project_id}: {e}", exc_info=True)
            self._conn.rollback()
            return False

    def delete_project(self, project_id: int) -> bool:
        """
        Deletes a project entry (and associated files, slides, etc.,
        due to ON DELETE CASCADE).
        """
        if not self._conn: return False
        sql = "DELETE FROM projects WHERE id = ?"
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, (project_id,))
            deleted_rows = cursor.rowcount
            self._conn.commit()
            if deleted_rows > 0:
                self.logger.info(f"Deleted project ID {project_id} (and cascaded related data).")
                return True
            else:
                self.logger.warning(f"Attempted to delete project ID {project_id}, but project not found.")
                return False
        except sqlite3.Error as e:
            self.logger.error(f"Database error deleting project ID {project_id}: {e}", exc_info=True)
            self._conn.rollback()
            return False

    # --- CRUD Methods for Files ---

    def add_file(self, project_id: int, filename: str, rel_path: str, checksum: Optional[str]) -> Optional[int]:
        """Adds a file record linked to a project."""
        if not self._conn: return None
        sql = """
            INSERT INTO files (project_id, filename, rel_path, checksum)
            VALUES (?, ?, ?, ?)
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, (project_id, filename, rel_path, checksum))
            self._conn.commit()
            new_id = cursor.lastrowid
            self.logger.info(f"Added file '{filename}' (RelPath: {rel_path}) with ID: {new_id} to project ID: {project_id}")
            return new_id
        except sqlite3.IntegrityError as e:
            # Likely UNIQUE constraint (project_id, rel_path)
            self.logger.error(f"Failed to add file '{filename}' to project {project_id}. IntegrityError (duplicate rel_path?): {e}")
            self._conn.rollback()
            return None
        except sqlite3.Error as e:
            self.logger.error(f"Database error adding file '{filename}' to project {project_id}: {e}", exc_info=True)
            self._conn.rollback()
            return None
    # --- CRUD Methods for SLIDEs ---
    def add_slide(self, file_id: int, slide_index: int,
                  thumb_rel_path: Optional[str], image_rel_path: Optional[str]) -> Optional[int]:
         """Adds or updates a slide record linked to a file, including image paths."""
         if not self._conn: return None
         # SQL updated to match new column names and ON CONFLICT clause
         sql = """
             INSERT INTO slides (file_id, slide_index, thumb_rel_path, image_rel_path)
             VALUES (?, ?, ?, ?)
             ON CONFLICT(file_id, slide_index) DO UPDATE SET
                 thumb_rel_path=excluded.thumb_rel_path,
                 image_rel_path=excluded.image_rel_path;
         """
         try:
             cursor = self._conn.cursor()
             # Pass the correct parameters in order
             cursor.execute(sql, (file_id, slide_index, thumb_rel_path, image_rel_path))
             self._conn.commit()
             # Get ID (logic remains same)
             cursor.execute("SELECT id FROM slides WHERE file_id = ? AND slide_index = ?", (file_id, slide_index))
             result = cursor.fetchone()
             new_id = result['id'] if result else None
             if new_id:
                  self.logger.debug(f"Added/Updated slide record for FileID {file_id}, Index {slide_index}. SlideID: {new_id}")
             else:
                  self.logger.error(f"Failed to get ID after adding/updating slide for FileID {file_id}, Index {slide_index}")
             return new_id
         except sqlite3.Error as e:
             self.logger.error(f"Database error adding/updating slide for FileID {file_id}, Index {slide_index}: {e}", exc_info=True)
             self._conn.rollback()
             return None
    def update_file_conversion_status(self, file_id: int, status: str) -> bool:
         """Updates the conversion_status for a given file_id."""
         allowed_statuses = ('Pending', 'In Progress', 'Completed', 'Failed')
         if status not in allowed_statuses:
             self.logger.error(f"Invalid conversion status provided: {status}")
             return False
         if not self._conn: return False
         sql = "UPDATE files SET conversion_status = ? WHERE id = ?"
         try:
             cursor = self._conn.cursor()
             cursor.execute(sql, (status, file_id))
             updated_rows = cursor.rowcount
             self._conn.commit()
             if updated_rows > 0:
                 self.logger.info(f"Updated conversion status for file ID {file_id} to '{status}'.")
                 return True
             else:
                 self.logger.warning(f"Attempted to update status for file ID {file_id}, but file not found.")
                 return False
         except sqlite3.Error as e:
             self.logger.error(f"Database error updating conversion status for file ID {file_id}: {e}", exc_info=True)
             self._conn.rollback()
             return False

    def get_files_for_project(self, project_id: int, status: Optional[str] = None) -> List[File]:
         """
         Retrieves file records for a given project_id, optionally filtering by status.
         """
         files = []
         if not self._conn: return files
         
         sql = "SELECT id, project_id, filename, rel_path, slide_count, checksum, conversion_status FROM files WHERE project_id = ?"
         params: List[Any] = [project_id]
         if status:
              sql += " AND conversion_status = ?"
              params.append(status)
         sql += " ORDER BY filename COLLATE NOCASE;"

         try:
              cursor = self._conn.cursor()
              cursor.execute(sql, params)
              for row in cursor.fetchall():
                   # Map row to File dataclass, ensure File dataclass has conversion_status field
                   files.append(File(**row))
              self.logger.debug(f"Retrieved {len(files)} files for project ID {project_id} (status filter: {status}).")
         except sqlite3.Error as e:
              self.logger.error(f"Database error fetching files for project ID {project_id}: {e}", exc_info=True)
         return files

    # Make sure add_element and delete_elements_for_slide are also present
    def add_element(self, slide_id: int, element_type: str,
                     bbox_x: float, bbox_y: float, bbox_w: float, bbox_h: float) -> Optional[int]:
         # ... (Implementation from previous phase review) ...
         if not self._conn: return None
         sql = """
             INSERT INTO elements (slide_id, element_type, bbox_x, bbox_y, bbox_w, bbox_h)
             VALUES (?, ?, ?, ?, ?, ?)
         """
         try:
             cursor = self._conn.cursor()
             cursor.execute(sql, (slide_id, element_type, bbox_x, bbox_y, bbox_w, bbox_h))
             self._conn.commit()
             new_id = cursor.lastrowid
             self.logger.debug(f"Added element record for SlideID {slide_id}. ElementID: {new_id}")
             return new_id
         except sqlite3.Error as e:
             self.logger.error(f"Database error adding element for SlideID {slide_id}: {e}", exc_info=True)
             self._conn.rollback()
             return None


    def delete_elements_for_slide(self, slide_id: int) -> bool:
         # ... (Implementation from previous phase review) ...
         if not self._conn: return False
         sql = "DELETE FROM elements WHERE slide_id = ?"
         try:
             cursor = self._conn.cursor()
             cursor.execute(sql, (slide_id,))
             deleted_count = cursor.rowcount
             self._conn.commit()
             self.logger.info(f"Deleted {deleted_count} elements for SlideID {slide_id}.")
             return True
         except sqlite3.Error as e:
             self.logger.error(f"Database error deleting elements for SlideID {slide_id}: {e}", exc_info=True)
             self._conn.rollback()
             return False

    # --- CRUD Methods for keywords and link tables ---
    
    def add_keyword_if_not_exists(self, keyword_text: str, kind: KeywordKind) -> Optional[int]:
        """
        Adds a new keyword if it doesn't already exist.
        
        Args:
            keyword_text: The text of the keyword
            kind: The type of keyword ('topic', 'title', or 'name')
            
        Returns:
            The ID of the existing or newly created keyword, or None on failure
        """
        keyword_text = keyword_text.strip()
        if not keyword_text: return None

        with QMutexLocker(self._write_mutex): # Lock for potential INSERT
            self.logger.debug(f"Write lock acquired for add_keyword_if_not_exists ('{keyword_text}')")
            if not self._conn: return None
            # First, try to find existing keyword (case-insensitive)
            find_sql = "SELECT id FROM keywords WHERE keyword = ? COLLATE NOCASE AND kind = ?"
            insert_sql = "INSERT INTO keywords (keyword, kind) VALUES (?, ?)"
            try:
                cursor = self._conn.cursor()
                cursor.execute(find_sql, (keyword_text, kind))
                result = cursor.fetchone()
                if result:
                    keyword_id = result['id']
                    self.logger.debug(f"Keyword '{keyword_text}' already exists with ID: {keyword_id}")
                    return keyword_id
                else:
                    # Keyword doesn't exist, insert it
                    cursor.execute(insert_sql, (keyword_text, kind))
                    self._conn.commit()
                    new_id = cursor.lastrowid
                    self.logger.info(f"Added new keyword '{keyword_text}' (Kind: {kind}) with ID: {new_id}")
                    return new_id
            except sqlite3.Error as e:
                # Note: UNIQUE constraint might fire here too if simultaneous adds happened,
                # but the initial SELECT mitigates most cases. Rollback just in case.
                self.logger.error(f"Database error adding/finding keyword '{keyword_text}': {e}", exc_info=True)
                self._conn.rollback()
                return None
        # Lock released
    
    def get_keyword_id(self, keyword_text: str, kind: KeywordKind) -> Optional[int]:
        """
        Gets the ID for a keyword with the specified text and kind.
        
        Args:
            keyword_text: The text of the keyword
            kind: The type of keyword ('topic', 'title', or 'name')
            
        Returns:
            The ID of the keyword if found, or None otherwise
        """
        # READ operation - no lock needed
        keyword_text = keyword_text.strip()
        if not keyword_text or not self._conn: return None
            
        sql = "SELECT id FROM keywords WHERE keyword = ? COLLATE NOCASE AND kind = ?"
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, (keyword_text, kind))
            result = cursor.fetchone()
            return result['id'] if result else None
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting keyword ID for '{keyword_text}' (Kind: {kind}): {e}", exc_info=True)
            return None
    
    def get_all_keywords(self, kind: Optional[KeywordKind] = None) -> List[Keyword]:
        """
        Gets all keywords, optionally filtered by kind.
        
        Args:
            kind: Optional filter for keyword kind ('topic', 'title', or 'name')
            
        Returns:
            List of all Keyword objects
        """
        keywords = []
        if not self._conn:
            return keywords
            
        sql = "SELECT id, keyword, kind FROM keywords"
        params = []
        
        if kind:
            sql += " WHERE kind = ?"
            params.append(kind)
            
        sql += " ORDER BY keyword COLLATE NOCASE"
        
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, params)
            for row in cursor.fetchall():
                keywords.append(Keyword(**dict(row)))
            self.logger.debug(f"Retrieved {len(keywords)} keywords{' with kind ' + kind if kind else ''}")
        except sqlite3.Error as e:
            self.logger.error(f"Database error fetching all keywords: {e}", exc_info=True)
            
        return keywords
    
    def link_slide_keyword(self, slide_id: int, keyword_id: int) -> bool:
        """
        Links a slide to a keyword.
        
        Args:
            slide_id: The ID of the slide
            keyword_id: The ID of the keyword
            
        Returns:
            True if the link was created or already exists, False otherwise
        """
        with QMutexLocker(self._write_mutex): # Lock for writing
            self.logger.debug(f"Write lock acquired for link_slide_keyword (S:{slide_id}, K:{keyword_id})")
            if not self._conn: return False
            sql = "INSERT OR IGNORE INTO slide_keywords (slide_id, keyword_id) VALUES (?, ?)"
            try:
                cursor = self._conn.cursor()
                cursor.execute(sql, (slide_id, keyword_id))
                self._conn.commit()
                # Check if row was actually inserted or ignored
                was_inserted = cursor.rowcount > 0
                if was_inserted: 
                    self.logger.info(f"Linked Slide {slide_id} to Keyword {keyword_id}")
                else: 
                    self.logger.debug(f"Link Slide {slide_id} to Keyword {keyword_id} already exists or failed silently.")
                return True  # Return True even if ignored, as the desired state (link exists) is achieved
            except sqlite3.Error as e:
                self.logger.error(f"Database error linking slide {slide_id} to keyword {keyword_id}: {e}", exc_info=True)
                self._conn.rollback()
                return False
        # Lock released
    
    def unlink_slide_keyword(self, slide_id: int, keyword_id: int) -> bool:
        """
        Removes a link between a slide and a keyword.
        
        Args:
            slide_id: The ID of the slide
            keyword_id: The ID of the keyword
            
        Returns:
            True if the operation was successful, False on error
        """
        with QMutexLocker(self._write_mutex): # Lock for writing
            self.logger.debug(f"Write lock acquired for unlink_slide_keyword (S:{slide_id}, K:{keyword_id})")
            if not self._conn: return False
            sql = "DELETE FROM slide_keywords WHERE slide_id = ? AND keyword_id = ?"
            try:
                cursor = self._conn.cursor()
                cursor.execute(sql, (slide_id, keyword_id))
                deleted_rows = cursor.rowcount
                self._conn.commit()
                if deleted_rows > 0:
                    self.logger.info(f"Unlinked Slide {slide_id} from Keyword {keyword_id}")
                else:
                    self.logger.debug(f"No link found to delete for Slide {slide_id} and Keyword {keyword_id}")
                return True # Return True even if no rows deleted (idempotent operation)
            except sqlite3.Error as e:
                self.logger.error(f"Database error unlinking slide {slide_id} from keyword {keyword_id}: {e}", exc_info=True)
                self._conn.rollback()
                return False
        # Lock released
    
    def link_element_keyword(self, element_id: int, keyword_id: int) -> bool:
        """
        Links an element to a keyword.
        
        Args:
            element_id: The ID of the element
            keyword_id: The ID of the keyword
            
        Returns:
            True if the link was created or already exists, False otherwise
        """
        with QMutexLocker(self._write_mutex): # Lock for writing
            self.logger.debug(f"Write lock acquired for link_element_keyword (E:{element_id}, K:{keyword_id})")
            if not self._conn: return False
            sql = "INSERT OR IGNORE INTO element_keywords (element_id, keyword_id) VALUES (?, ?)"
            try:
                cursor = self._conn.cursor()
                cursor.execute(sql, (element_id, keyword_id))
                self._conn.commit()
                was_inserted = cursor.rowcount > 0
                if was_inserted: 
                    self.logger.info(f"Linked Element {element_id} to Keyword {keyword_id}")
                else: 
                    self.logger.debug(f"Link Element {element_id} to Keyword {keyword_id} already exists or failed silently.")
                return True  # Return True even if ignored, as the desired state (link exists) is achieved
            except sqlite3.Error as e:
                self.logger.error(f"Database error linking element {element_id} to keyword {keyword_id}: {e}", exc_info=True)
                self._conn.rollback()
                return False
        # Lock released
    
    def unlink_element_keyword(self, element_id: int, keyword_id: int) -> bool:
        """
        Removes a link between an element and a keyword.
        
        Args:
            element_id: The ID of the element
            keyword_id: The ID of the keyword
            
        Returns:
            True if the operation was successful, False on error
        """
        with QMutexLocker(self._write_mutex): # Lock for writing
            self.logger.debug(f"Write lock acquired for unlink_element_keyword (E:{element_id}, K:{keyword_id})")
            if not self._conn: return False
            sql = "DELETE FROM element_keywords WHERE element_id = ? AND keyword_id = ?"
            try:
                cursor = self._conn.cursor()
                cursor.execute(sql, (element_id, keyword_id))
                deleted_rows = cursor.rowcount
                self._conn.commit()
                if deleted_rows > 0:
                    self.logger.info(f"Unlinked Element {element_id} from Keyword {keyword_id}")
                else:
                    self.logger.debug(f"No link found to delete for Element {element_id} and Keyword {keyword_id}")
                return True # Return True even if no rows deleted (idempotent operation)
            except sqlite3.Error as e:
                self.logger.error(f"Database error unlinking element {element_id} from keyword {keyword_id}: {e}", exc_info=True)
                self._conn.rollback()
                return False
        # Lock released
    
    def get_keywords_for_slide(self, slide_id: int, kind: Optional[KeywordKind] = None) -> List[Keyword]:
        """
        Gets all keywords for a specific slide, optionally filtered by kind.
        
        Args:
            slide_id: The ID of the slide
            kind: Optional filter for keyword kind ('topic', 'title', or 'name')
            
        Returns:
            List of keyword objects (with id, keyword, kind attributes)
        """
        # READ operation - no lock needed
        keywords = []
        if not self._conn: return keywords
        
        sql = """
            SELECT k.id, k.keyword, k.kind
            FROM keywords k
            JOIN slide_keywords sk ON k.id = sk.keyword_id
            WHERE sk.slide_id = ?
        """
        params = [slide_id]
        
        if kind:
            sql += " AND k.kind = ?"
            params.append(kind)
            
        sql += " ORDER BY k.keyword COLLATE NOCASE"
        
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, params)
            for row in cursor.fetchall():
                keywords.append(Keyword(**dict(row)))
            self.logger.debug(f"Retrieved {len(keywords)} keywords for slide ID {slide_id}"
                             f"{' with kind '+kind if kind else ''}")
            return keywords
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting keywords for slide {slide_id}: {e}", exc_info=True)
            return keywords
    
    def get_keywords_for_element(self, element_id: int) -> List[Keyword]:
        """
        Gets all keywords for a specific element.
        
        Args:
            element_id: The ID of the element
            
        Returns:
            List of keyword objects (with id, keyword, kind attributes)
        """
        # READ operation - no lock needed
        keywords = []
        if not self._conn: return keywords
        
        sql = """
            SELECT k.id, k.keyword, k.kind
            FROM keywords k
            JOIN element_keywords ek ON k.id = ek.keyword_id
            WHERE ek.element_id = ?
            ORDER BY k.keyword COLLATE NOCASE
        """
        
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, (element_id,))
            for row in cursor.fetchall():
                keywords.append(Keyword(**dict(row)))
            self.logger.debug(f"Retrieved {len(keywords)} keywords for element ID {element_id}")
            return keywords
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting keywords for element {element_id}: {e}", exc_info=True)
            return keywords
    
    def get_all_keyword_strings(self, kind: Optional[KeywordKind] = None) -> List[str]:
        """
        Gets all keyword strings, optionally filtered by kind.
        
        Args:
            kind: Optional filter for keyword kind ('topic', 'title', or 'name')
            
        Returns:
            List of keyword strings
        """
        # READ operation - no lock needed
        keywords = []
        if not self._conn: return keywords
        
        sql = "SELECT DISTINCT keyword FROM keywords"
        params = []
        
        if kind:
            sql += " WHERE kind = ?"
            params.append(kind)
            
        sql += " ORDER BY keyword COLLATE NOCASE"
        
        try:
            cursor = self._conn.cursor()
            cursor.execute(sql, params)
            keywords = [row['keyword'] for row in cursor.fetchall()]
            self.logger.debug(f"Retrieved {len(keywords)} unique keyword strings"
                             f"{' with kind '+kind if kind else ''}")
            return keywords
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting all keyword strings: {e}", exc_info=True)
            return keywords

    def get_project_id_by_path(self, project_path: str) -> Optional[int]:
        """
        Retrieves a project ID by its folder path.
        
        Args:
            project_path: The folder path of the project
            
        Returns:
            The project ID if found, None otherwise
        """
        if not self._conn:
            self.logger.error("No database connection")
            return None
            
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT id FROM projects WHERE folder_path = ?",
                (project_path,)
            )
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving project ID by path: {e}")
            return None
            
    def replace_slide_keywords(self, slide_id: int, kind: KeywordKind, new_keyword_texts: List[str]) -> bool:
        """
        Replaces all keywords of a specific kind for a slide with a new set of keywords.
        
        Args:
            slide_id: The ID of the slide
            kind: The kind of keywords ('topic', 'title', 'name')
            new_keyword_texts: List of new keyword texts to set
            
        Returns:
            True if successful, False otherwise
        """
        if not self._conn:
            self.logger.error("No database connection")
            return False
            
        # Use mutex for thread safety during write operations
        with QMutexLocker(self._write_mutex):
            try:
                # Start a transaction
                self._conn.execute("BEGIN TRANSACTION")
                
                # Get the IDs of the new keywords, creating them if they don't exist
                new_keyword_ids = []
                for text in new_keyword_texts:
                    keyword_id = self.add_keyword_if_not_exists(text, kind)
                    if keyword_id is None:
                        raise Exception(f"Failed to add keyword '{text}' of kind '{kind}'")
                    new_keyword_ids.append(keyword_id)
                
                # Find all existing keyword IDs linked to this slide of the given kind
                cursor = self._conn.cursor()
                cursor.execute(
                    """
                    SELECT k.id
                    FROM keywords k
                    JOIN slide_keywords sk ON k.id = sk.keyword_id
                    WHERE sk.slide_id = ? AND k.kind = ?
                    """,
                    (slide_id, kind)
                )
                existing_keyword_ids = [row[0] for row in cursor.fetchall()]
                
                # Calculate differences
                to_remove = [kid for kid in existing_keyword_ids if kid not in new_keyword_ids]
                to_add = [kid for kid in new_keyword_ids if kid not in existing_keyword_ids]
                
                # Remove keywords that are not in the new set
                for keyword_id in to_remove:
                    success = self.unlink_slide_keyword(slide_id, keyword_id)
                    if not success:
                        raise Exception(f"Failed to unlink keyword ID {keyword_id} from slide ID {slide_id}")
                
                # Add new keywords that aren't already linked
                for keyword_id in to_add:
                    success = self.link_slide_keyword(slide_id, keyword_id)
                    if not success:
                        raise Exception(f"Failed to link keyword ID {keyword_id} to slide ID {slide_id}")
                
                # Commit the transaction
                self._conn.execute("COMMIT")
                self.logger.debug(f"Successfully replaced {kind} keywords for slide ID {slide_id}")
                return True
                
            except Exception as e:
                # Rollback on error
                self._conn.execute("ROLLBACK")
                self.logger.error(f"Error replacing keywords for slide ID {slide_id}: {str(e)}")
                return False

    def get_all_keyword_objects(self) -> List[Keyword]:
        """
        Gets all keywords as Keyword objects from the database.
        
        Returns:
            List of Keyword objects
        """
        keywords = []
        
        try:
            # Get all keywords
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT id, keyword, kind FROM keywords ORDER BY keyword COLLATE NOCASE"
            )
                
            for row in cursor.fetchall():
                keywords.append(Keyword(
                    id=row[0],
                    keyword=row[1],
                    kind=row[2]
                ))
                
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting all keyword objects: {e}", exc_info=True)
            
        return keywords
        
    def merge_keywords(self, from_keyword_id: int, to_keyword_id: int) -> bool:
        """
        Merges one keyword into another, updating all references.
        The 'from' keyword will be removed and all its references updated to point to the 'to' keyword.
        
        Args:
            from_keyword_id: ID of the keyword to merge from (will be removed)
            to_keyword_id: ID of the keyword to merge into (will be kept)
            
        Returns:
            True if successful, False otherwise
        """
        if not self._conn:
            self.logger.error("No database connection")
            return False
            
        # Use mutex for thread safety during write operations
        with QMutexLocker(self._write_mutex):
            try:
                # Start a transaction
                self._conn.execute("BEGIN TRANSACTION")
                
                # Get information about both keywords for logging
                cursor = self._conn.cursor()
                cursor.execute(
                    "SELECT keyword, kind FROM keywords WHERE id = ?",
                    (from_keyword_id,)
                )
                from_row = cursor.fetchone()
                if not from_row:
                    raise ValueError(f"Source keyword ID {from_keyword_id} not found")
                
                cursor.execute(
                    "SELECT keyword, kind FROM keywords WHERE id = ?",
                    (to_keyword_id,)
                )
                to_row = cursor.fetchone()
                if not to_row:
                    raise ValueError(f"Target keyword ID {to_keyword_id} not found")
                
                from_text, from_kind = from_row
                to_text, to_kind = to_row
                
                if from_kind != to_kind:
                    raise ValueError(f"Cannot merge keywords of different kinds: {from_kind} vs {to_kind}")
                
                self.logger.info(f"Merging keyword '{from_text}' (ID: {from_keyword_id}) into '{to_text}' (ID: {to_keyword_id})")
                
                # Update slide_keywords references
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO slide_keywords (slide_id, keyword_id)
                    SELECT slide_id, ? FROM slide_keywords WHERE keyword_id = ?
                    """,
                    (to_keyword_id, from_keyword_id)
                )
                slide_updates = cursor.rowcount
                
                # Remove old slide_keywords entries
                cursor.execute(
                    "DELETE FROM slide_keywords WHERE keyword_id = ?",
                    (from_keyword_id,)
                )
                
                # Update element_keywords references
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO element_keywords (element_id, keyword_id)
                    SELECT element_id, ? FROM element_keywords WHERE keyword_id = ?
                    """,
                    (to_keyword_id, from_keyword_id)
                )
                element_updates = cursor.rowcount
                
                # Remove old element_keywords entries
                cursor.execute(
                    "DELETE FROM element_keywords WHERE keyword_id = ?",
                    (from_keyword_id,)
                )
                
                # Delete the 'from' keyword
                cursor.execute(
                    "DELETE FROM keywords WHERE id = ?",
                    (from_keyword_id,)
                )
                
                # Commit the transaction
                self._conn.execute("COMMIT")
                self.logger.debug(f"Merged keyword {from_keyword_id} into {to_keyword_id}. Updated {slide_updates} slide links and {element_updates} element links")
                return True
                
            except Exception as e:
                # Rollback on error
                self._conn.execute("ROLLBACK")
                self.logger.error(f"Error merging keywords {from_keyword_id} into {to_keyword_id}: {str(e)}")
                return False
        # Lock released
    
    # Add context manager to enable with statement
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_slides_for_project(self, project_id):
        """
        Get all slides for a project.
        
        Args:
            project_id: The ID of the project to get slides for.
            
        Returns:
            List of slide dictionaries with all slide information.
        """
        slides = []
        
        try:
            # First get all files for the project
            files = self.get_files_for_project(project_id)
            
            # For each file, get all slides
            for file in files:
                file_slides = self.get_slides_for_file(file.id)
                
                # For each slide, add file information and build slide data
                for slide in file_slides:
                    # Get thumbnail path
                    thumbnail_path = self.get_slide_thumbnail_path(slide.id)
                    
                    # Build slide dictionary with data from both slide and file
                    slide_data = {
                        'id': slide.id,
                        'file_id': file.id,
                        'file_name': file.filename,
                        'slide_index': slide.slide_index,
                        'thumbnail_path': thumbnail_path
                    }
                    
                    slides.append(slide_data)
            
            self.logger.debug(f"Retrieved {len(slides)} slides for project ID {project_id}")
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error getting slides for project: {e}", exc_info=True)
        
        return slides

    def get_slides_for_keyword(self, keyword_id: int, project_id: Optional[int] = None) -> List[Slide]:
        """Retrieve slides linked to a keyword, optionally filtered by project."""
        if not self._conn:
            return []
        try:
            cursor = self._conn.cursor()
            if project_id is not None:
                sql = """
                    SELECT DISTINCT s.id, s.file_id, s.slide_index, s.thumb_rel_path, s.image_rel_path
                      FROM slides s
                      JOIN files f ON s.file_id = f.id
                      JOIN slide_keywords sk ON s.id = sk.slide_id
                     WHERE sk.keyword_id = ? AND f.project_id = ?
                    UNION
                    SELECT DISTINCT s.id, s.file_id, s.slide_index, s.thumb_rel_path, s.image_rel_path
                      FROM slides s
                      JOIN files f ON s.file_id = f.id
                      JOIN elements e ON s.id = e.slide_id
                      JOIN element_keywords ek ON e.id = ek.element_id
                     WHERE ek.keyword_id = ? AND f.project_id = ?
                    ORDER BY slide_index;
                """
                params = (keyword_id, project_id, keyword_id, project_id)
            else:
                sql = """
                    SELECT DISTINCT s.id, s.file_id, s.slide_index, s.thumb_rel_path, s.image_rel_path
                      FROM slides s
                      JOIN slide_keywords sk ON s.id = sk.slide_id
                     WHERE sk.keyword_id = ?
                    UNION
                    SELECT DISTINCT s.id, s.file_id, s.slide_index, s.thumb_rel_path, s.image_rel_path
                      FROM slides s
                      JOIN elements e ON s.id = e.slide_id
                      JOIN element_keywords ek ON e.id = ek.element_id
                     WHERE ek.keyword_id = ?
                    ORDER BY slide_index;
                """
                params = (keyword_id, keyword_id)
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            slides: List[Slide] = []
            for row in rows:
                slides.append(Slide(
                    id=row["id"],
                    file_id=row["file_id"],
                    slide_index=row["slide_index"],
                    thumb_rel_path=row["thumb_rel_path"],
                    image_rel_path=row["image_rel_path"]
                ))
            return slides
        except sqlite3.Error as e:
            self.logger.error(f"Error getting slides for keyword {keyword_id}: {e}", exc_info=True)
            return []

    def get_project_folder_path_for_slide(self, slide_id: int) -> Optional[str]:
        """Retrieve project folder path containing the given slide."""
        if not self._conn:
            return None
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT p.folder_path FROM projects p "
                "JOIN files f ON f.project_id = p.id "
                "JOIN slides s ON s.file_id = f.id WHERE s.id = ?;",
                (slide_id,)
            )
            row = cursor.fetchone()
            if row and row[0]:
                return row[0]
            return None
        except sqlite3.Error as e:
            self.logger.error(f"Error getting project path for slide {slide_id}: {e}", exc_info=True)
            return None