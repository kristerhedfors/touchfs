"""Models for filesystem structures and content generation."""
from typing import Dict, Optional, Literal, Union
from pydantic import BaseModel, Field

class FileAttrs(BaseModel):
    """File attributes model."""
    st_mode: str
    st_uid: Optional[str] = None
    st_gid: Optional[str] = None

class FileNode(BaseModel):
    """File node model representing a file, directory, or symlink."""
    type: Literal["file", "directory", "symlink"]
    content: Optional[Union[str, bytes]] = Field(default="")
    children: Optional[Dict[str, str]] = None
    attrs: FileAttrs
    xattrs: Optional[Dict[str, str]] = None

class FileSystem(BaseModel):
    """Complete filesystem structure model."""
    data: Dict[str, FileNode]

class ContentMetadata(BaseModel):
    """Model for generated content metadata."""
    file_type: str
    dependencies: list[str] = Field(default_factory=list)
    imports: list[str] = Field(default_factory=list)

class GeneratedContent(BaseModel):
    """Model for generated file content with metadata."""
    content: str
    metadata: ContentMetadata
