"""TouchFS - A filesystem that generates content using LLMs."""
from .core.memory import Memory
from .core.jsonfs import JsonFS
from .models.filesystem import FileSystem, FileNode, FileAttrs
from .content.generator import generate_filesystem, generate_file_content
from .config.settings import get_prompt, get_openai_key
from .config.logger import setup_logging

__version__ = "0.1.0"

__all__ = [
    "Memory",
    "JsonFS",
    "FileSystem",
    "FileNode", 
    "FileAttrs",
    "generate_filesystem",
    "generate_file_content",
    "get_prompt",
    "get_openai_key",
    "setup_logging"
]
