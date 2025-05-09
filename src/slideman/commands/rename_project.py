# src/slideman/commands/rename_project.py

import logging
import os
from pathlib import Path
from PySide6.QtGui import QUndoCommand

from typing import Union, Optional # Need Union for older Python

# Assuming Database service is importable
from ..services.database import Database
# Assuming EventBus is importable for potential signals
from ..event_bus import event_bus

class RenameProjectCmd(QUndoCommand):
    """Undoable command to rename a project (database entry and folder)."""

    def __init__(self, project_id: int, old_name: str, old_folder_path: str,
                 new_name: str, db: Database, parent: Union[QUndoCommand, None] = None):
        super().__init__(f"Rename project '{old_name}' to '{new_name}'", parent)
        self.logger = logging.getLogger(__name__)
        self.project_id = project_id
        self.old_name = old_name
        self.old_path = Path(old_folder_path)
        self.new_name = new_name
        self.db = db

        # Determine new path based on new name (consistent logic needed)
        # This assumes the same sanitization/checking logic as in handle_new_project
        # TODO: Refactor path generation/checking logic into a shared utility?
        safe_folder_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in new_name).rstrip()
        base_project_dir = self.old_path.parent
        self.new_path = base_project_dir / safe_folder_name
        # Simple check, might need counter logic if robust renaming is needed
        if self.new_path.exists() and self.new_path != self.old_path:
             # Handle case where target folder name already exists
             self.logger.warning(f"Target rename folder '{self.new_path}' already exists. Rename might fail or overwrite.")
             # For simplicity, we proceed, but a real app might prevent/warn more actively or add counters.
             # Setting new_path to old_path will effectively prevent folder rename if target exists
             # self.new_path = self.old_path # Option to prevent folder rename

        self.logger.debug(f"RenameCmd Init: ID={project_id}, Old='{old_name}'@{old_folder_path}, New='{new_name}'@{self.new_path}")


    def redo(self):
        """Renames the project folder and updates the database."""
        self.logger.info(f"Redo Rename: Renaming project ID {self.project_id} to '{self.new_name}'")
        folder_renamed = False
        db_updated = False

        # 1. Rename folder (if path changes and new path doesn't exist or IS the old path)
        if self.old_path != self.new_path: # and not self.new_path.exists(): # Add existence check?
            try:
                os.rename(self.old_path, self.new_path)
                self.logger.info(f"Renamed folder from '{self.old_path}' to '{self.new_path}'")
                folder_renamed = True
            except OSError as e:
                self.logger.error(f"Failed to rename project folder: {e}", exc_info=True)
                # Critical decision: If folder rename fails, should DB rename proceed?
                # Let's rollback folder rename if possible (though os.rename isn't transactional)
                # For now, we stop if folder rename fails.
                self.setText(f"Rename project '{self.old_name}' failed: Folder rename error") # Update command text
                return # Stop redo

        else:
             self.logger.debug("Folder path unchanged or target exists, skipping folder rename.")
             folder_renamed = True # Treat as success if no rename needed/possible

        # 2. Rename in Database
        # Use new path if folder rename was successful or skipped, else use old path
        path_to_update = str(self.new_path) if folder_renamed else str(self.old_path)
        # TODO: Need method in DB service: update_project(id, name=new_name, folder_path=path_to_update)
        # Using rename_project for now, assuming it only updates name
        # db_updated = self.db.rename_project(self.project_id, self.new_name)
        # Let's assume a more complete update method is better:
        db_updated = self.db.update_project_details(self.project_id, self.new_name, path_to_update)


        if not db_updated:
            self.logger.error(f"Database update failed for renaming project ID {self.project_id}.")
            # Rollback folder rename if we did one
            if self.old_path != self.new_path and folder_renamed:
                 try:
                      os.rename(self.new_path, self.old_path) # Attempt rollback
                      self.logger.warning("Rolled back folder rename due to DB update failure.")
                 except OSError as rb_e:
                      self.logger.error(f"CRITICAL: Failed to rollback folder rename: {rb_e}")
            self.setText(f"Rename project '{self.old_name}' failed: DB update error")
            return # Stop redo

        self.logger.debug("Rename redo completed successfully.")
        # Optional: Emit signal via EventBus? event_bus.projectRenamed.emit(...)

    def undo(self):
        """Reverts the project name and folder name."""
        self.logger.info(f"Undo Rename: Reverting project ID {self.project_id} to '{self.old_name}'")
        folder_reverted = False
        db_reverted = False

        # 1. Rename folder back (if it was changed)
        current_path = self.new_path if self.old_path != self.new_path else self.old_path
        if current_path.exists() and self.old_path != current_path:
            try:
                os.rename(current_path, self.old_path)
                self.logger.info(f"Reverted folder name from '{current_path}' to '{self.old_path}'")
                folder_reverted = True
            except OSError as e:
                self.logger.error(f"Failed to revert project folder name: {e}", exc_info=True)
                # Log critical error, proceed with DB revert attempt?
        else:
             self.logger.debug("Folder path wasn't changed or doesn't exist, skipping folder revert.")
             folder_reverted = True # Allow DB revert attempt

        # 2. Rename in Database back to old name and old path
        # db_reverted = self.db.rename_project(self.project_id, self.old_name) # If only name was changed
        db_reverted = self.db.update_project_details(self.project_id, self.old_name, str(self.old_path))


        if not db_reverted:
            self.logger.error(f"Database update failed for reverting rename of project ID {self.project_id}.")
            # Potentially try to rename folder back again? Complex recovery.
            self.setText(f"Undo Rename project '{self.old_name}' failed: DB revert error")
        else:
            self.logger.debug("Rename undo completed successfully.")
        # Optional: Emit signal via EventBus?
        event_bus.statusMessageUpdate.emit("Project renamed successfully.", 3000)