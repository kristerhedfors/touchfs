"""Models for filesystem list generation."""

from typing import List
from pydantic import BaseModel

class FilesystemList(BaseModel):
    """Simple model for filesystem generation that just lists files to create."""
    files: List[str]
    """List of file paths to create. Directories are implicit from the paths."""
