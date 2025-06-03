"""
SLIDEMAN commands package.

This package contains all undoable command implementations following
the Command pattern for undo/redo support.
"""

from .base_command import BaseCommand
from .delete_project import DeleteProjectCmd
from .rename_project import RenameProjectCmd
from .manage_element_keyword import LinkElementKeywordCmd, UnlinkElementKeywordCmd
from .manage_slide_keyword import (
    LinkSlideKeywordCmd, UnlinkSlideKeywordCmd, ReplaceSlideKeywordsCmd
)
from .merge_keywords_cmd import MergeKeywordsCmd

__all__ = [
    "BaseCommand",
    "DeleteProjectCmd",
    "RenameProjectCmd",
    "LinkElementKeywordCmd",
    "UnlinkElementKeywordCmd",
    "LinkSlideKeywordCmd",
    "UnlinkSlideKeywordCmd",
    "ReplaceSlideKeywordsCmd",
    "MergeKeywordsCmd",
]