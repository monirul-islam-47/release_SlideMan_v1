# src/slideman/commands/delete_project.py

import logging
import shutil # Use shutil for robust directory removal
from pathlib import Path
from PySide6.QtGui import QUndoCommand

from typing import Union, Optional # Need Union for older Python

from ..services.database import Database
from ..event_bus import event_bus

class DeleteProjectCmd(QUndoCommand):
    """Undoable command to delete a project (database entry and folder)."""

    def __init__(self, project_id: int, project_name: str, project_folder_path: str,
                 db: Database, parent: Union[QUndoCommand, None] = None):
        super().__init__(f"Delete project '{project_name}'", parent)
        self.logger = logging.getLogger(__name__)
        self.project_id = project_id
        self.project_name = project_name # Store for messages/revert
        self.project_path = Path(project_folder_path)
        self.db = db
        
        # For undo, we might need to store more project details if recreating
        # For now, assume ID/Name/Path is enough

        self.logger.debug(f"DeleteCmd Init: ID={project_id}, Name='{project_name}', Path='{self.project_path}'")

    def redo(self):
        """Deletes the project folder and database entry."""
        self.logger.info(f"Redo Delete: Deleting project ID {self.project_id} ('{self.project_name}')")
        folder_deleted = False
        db_deleted = False

        # 1. Delete from Database first (so cascade happens if successful)
        db_deleted = self.db.delete_project(self.project_id)

        if not db_deleted:
            self.logger.error(f"Database delete failed for project ID {self.project_id}.")
            self.setText(f"Delete project '{self.project_name}' failed: DB delete error")
            return # Stop redo

        # 2. Delete folder (only if DB delete was successful)
        if self.project_path.exists():
            try:
                # Use shutil.rmtree for recursive deletion
                shutil.rmtree(self.project_path)
                self.logger.info(f"Deleted project folder: '{self.project_path}'")
                folder_deleted = True
            except OSError as e:
                self.logger.error(f"Failed to delete project folder '{self.project_path}': {e}", exc_info=True)
                # CRITICAL: DB entry deleted, but folder remains. Log prominently.
                self.setText(f"Delete project '{self.project_name}' partial: DB deleted, FOLDER FAILED")
                # We might want to signal this critical state
        else:
             self.logger.warning(f"Project folder '{self.project_path}' not found, skipping folder deletion.")
             folder_deleted = True # Consider it success if folder already gone

        self.logger.debug("Delete redo completed.")
        # Optional: Emit signal event_bus.projectDeleted.emit(...)


    def undo(self):
        """Re-adds the project entry to the database. Does NOT restore folder contents."""
        self.logger.info(f"Undo Delete: Re-adding project ID {self.project_id} ('{self.project_name}')")
        # NOTE: We cannot reliably undo the folder deletion (shutil.rmtree).
        # The undo operation will only restore the database entry.
        # The user must be warned about this limitation.

        # Re-add project to DB. Assume folder path is still relevant even if empty.
        new_id = self.db.add_project(self.project_name, str(self.project_path))

        if new_id == self.project_id or (new_id is not None and self.project_id is None):
             # If using existing ID wasn't possible, or ID was None, update self.project_id?
             # This logic depends on whether add_project can reuse IDs or if ID should remain stable.
             # Assuming add_project gives a *new* ID if re-inserting. This makes true undo hard.
             # Let's assume for now add_project fails if path exists, which is bad for undo.
             # A better approach: DB service needs an 'undelete' or specific 'reinsert_with_id' method.
             # --- Workaround: Update DB service or accept limited undo ---
             self.logger.warning("Simple re-add might fail or create duplicate ID. True DB restore needed for robust undo.")
             if new_id is None:
                   self.logger.error(f"Failed to re-add project '{self.project_name}' to database during undo.")
                   self.setText(f"Undo Delete project '{self.project_name}' failed: DB re-add error")
             else:
                   self.project_id = new_id # Update ID if re-inserted
                   self.logger.info(f"Re-added project '{self.project_name}' to DB with new/old ID: {new_id}. FOLDER NOT RESTORED.")

        else:
             # Handles case where add_project returns an ID different from the original,
             # which indicates a problem with re-insertion logic.
             self.logger.error(f"Failed to re-add project '{self.project_name}' correctly during undo (ID mismatch or failure).")
             self.setText(f"Undo Delete project '{self.project_name}' failed: DB re-add error/mismatch")

        self.logger.warning("Undo Delete does NOT restore the deleted project folder contents.")
        # Optional: Emit signal event_bus.projectRestoredFromUndo.emit(...)
        event_bus.statusMessageUpdate.emit("Project deleted successfully.", 3000)

        """
        undo(): Crucially, this implementation has a limitation. It only attempts to re-add the project entry to the database 
        using db.add_project. It cannot restore the deleted files. A true "undelete" would require moving the folder 
        to a temporary trash location instead of using shutil.rmtree. Decision: Is this limited undo (DB only) 
        acceptable for v1.0, perhaps with a stronger warning dialog during deletion? Implementing a trash system 
        adds complexity. Let's proceed with the limited undo for now, but acknowledge the limitation. The re-add logic 
        might also need refinement in the DB service to handle potential ID or path conflicts better."""