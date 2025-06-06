#!/usr/bin/env python3
"""
Migration script for Phase 1 refactoring.

This script backs up original files and replaces them with refactored versions.
Run with: python migrate_phase1.py
"""

import shutil
import os
from pathlib import Path
from datetime import datetime


def create_backup(file_path: Path) -> Path:
    """Create a backup of the original file."""
    backup_dir = file_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    backup_path = backup_dir / backup_name
    
    shutil.copy2(file_path, backup_path)
    print(f"  ✓ Backed up {file_path.name} to {backup_path}")
    return backup_path


def migrate_file(src_path: Path, dst_path: Path) -> bool:
    """Migrate a file, creating backup first."""
    if not src_path.exists():
        print(f"  ✗ Source file not found: {src_path}")
        return False
    
    if dst_path.exists():
        create_backup(dst_path)
    
    shutil.copy2(src_path, dst_path)
    print(f"  ✓ Migrated {src_path.name} -> {dst_path.name}")
    return True


def main():
    """Run the migration."""
    print("Phase 1 Refactoring Migration")
    print("=" * 50)
    
    # Define file mappings
    migrations = [
        # (new_file, original_file)
        ("src/slideman/services/database_new.py", "src/slideman/services/database.py"),
        ("src/slideman/services/slide_converter_new.py", "src/slideman/services/slide_converter.py"),
        ("src/slideman/services/export_service_new.py", "src/slideman/services/export_service.py"),
    ]
    
    # Check if we're in the right directory
    if not Path("src/slideman").exists():
        print("ERROR: Must run from project root directory")
        return 1
    
    print("\nStep 1: Creating backups and migrating files")
    print("-" * 50)
    
    success_count = 0
    for new_file, orig_file in migrations:
        new_path = Path(new_file)
        orig_path = Path(orig_file)
        
        print(f"\nMigrating {orig_file}:")
        if migrate_file(new_path, orig_path):
            success_count += 1
            # Remove the _new file after successful migration
            new_path.unlink()
            print(f"  ✓ Removed temporary file {new_path.name}")
    
    print("\nStep 2: Updating imports in affected files")
    print("-" * 50)
    
    # Files that need import updates
    files_to_update = [
        "src/slideman/ui/pages/projects_page.py",
        "src/slideman/ui/pages/slideview_page.py",
        "src/slideman/ui/pages/assembly_page.py",
        "src/slideman/ui/pages/delivery_page.py",
        "src/slideman/commands/rename_project.py",
        "src/slideman/commands/delete_project.py",
    ]
    
    # Update imports
    for file_path in files_to_update:
        path = Path(file_path)
        if path.exists():
            print(f"\nUpdating imports in {file_path}:")
            
            # Read file
            content = path.read_text(encoding='utf-8')
            original_content = content
            
            # Update database service usage in worker threads
            if "slide_converter.py" in file_path or "export_service.py" in file_path:
                # These are already updated
                continue
                
            # For UI files that create workers
            if "projects_page.py" in file_path:
                # Update SlideConverter instantiation
                content = content.replace(
                    "SlideConverter(file_id, file_path, self.db, signals)",
                    "SlideConverter(file_id, file_path, self.db.db_path, signals)"
                )
                
            if "delivery_page.py" in file_path or "assembly_page.py" in file_path:
                # Update ExportWorker instantiation
                content = content.replace(
                    "ExportWorker(ordered_slide_ids, output_mode, output_path, self.db)",
                    "ExportWorker(ordered_slide_ids, output_mode, output_path, self.db.db_path)"
                )
            
            # Write back if changed
            if content != original_content:
                create_backup(path)
                path.write_text(content, encoding='utf-8')
                print(f"  ✓ Updated imports")
            else:
                print(f"  - No changes needed")
    
    print("\nStep 3: Summary")
    print("-" * 50)
    print(f"✓ Successfully migrated {success_count}/{len(migrations)} files")
    print("\nIMPORTANT: Next steps:")
    print("1. Update src/slideman/__init__.py to import new exception classes")
    print("2. Run tests to verify the refactoring")
    print("3. Update any remaining direct database access in UI files")
    print("\nBackups are stored in: src/slideman/services/backups/")
    
    return 0


if __name__ == "__main__":
    exit(main())