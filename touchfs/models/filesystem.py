"""Models for filesystem structures and content generation."""
from typing import Dict, Optional, Literal
from pydantic import BaseModel

class FileAttrs(BaseModel):
    """File attributes model."""
    st_mode: str
    st_uid: Optional[str] = None
    st_gid: Optional[str] = None

class FileNode(BaseModel):
    """File node model representing a file, directory, or symlink."""
    type: Literal["file", "directory", "symlink"]
    content: Optional[str] = ""
    children: Optional[Dict[str, str]] = None
    attrs: FileAttrs
    xattrs: Optional[Dict[str, str]] = None

class FileSystem(BaseModel):
    """Complete filesystem structure model."""
    data: Dict[str, FileNode]

class GeneratedContent(BaseModel):
    """Model for generated file content."""
    content: str
