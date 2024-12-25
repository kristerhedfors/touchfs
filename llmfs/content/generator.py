"""Content generation using OpenAI's API and plugins."""
import os
import json
import logging
from typing import Dict
from openai import OpenAI
from ..models.filesystem import FileSystem, GeneratedContent, FileNode, FileAttrs
from ..config.logger import setup_logging
from .plugins.registry import PluginRegistry

def get_openai_client() -> OpenAI:
    """Initialize OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    return OpenAI()

def generate_filesystem(prompt: str) -> dict:
    """Generate filesystem structure using OpenAI.
    
    Args:
        prompt: User prompt describing desired filesystem structure
        
    Returns:
        Dict containing the generated filesystem structure
        
    Raises:
        RuntimeError: If filesystem generation fails
    """
    client = get_openai_client()
    
    system_prompt = """
    You are a filesystem generator. Given a prompt, generate a JSON structure representing a filesystem.
    The filesystem must follow this exact structure:
    {
      "data": {
        "/": {
          "type": "directory",
          "children": {
            "example": "/example"
          },
          "attrs": {
            "st_mode": "16877",  # directory with 755 permissions
            "st_size": "0"
          }
        },
        "/example": {
          "type": "directory",
          "children": {},
          "attrs": {
            "st_mode": "16877",
            "st_size": "0"
          }
        }
      }
    }

    Rules:
    1. The response must have a top-level "data" field containing the filesystem structure
    2. Each node must have a "type" ("file", "directory", or "symlink")
    3. Each node must have "attrs" with st_mode and st_size
    4. For files:
       - Set content to null initially (it will be generated on first read)
       - Use st_mode "33188" for regular files (644 permissions)
    5. For directories:
       - Must have "children" mapping names to absolute paths
       - Use st_mode "16877" for directories (755 permissions)
    6. For symlinks:
       - Must have "content" with the target path
       - Use st_mode "41471" for symlinks (777 permissions)
    7. All paths must be absolute and normalized
    8. Root directory ("/") must always exist
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        # Parse and validate the response
        fs_data = json.loads(completion.choices[0].message.content)
        FileSystem.model_validate(fs_data)
        return fs_data
    except Exception as e:
        raise RuntimeError(f"Failed to generate filesystem: {e}")

def generate_file_content(path: str, fs_structure: Dict[str, FileNode]) -> str:
    """Generate content for a file using plugins or OpenAI.
    
    Args:
        path: Path of the file to generate content for
        fs_structure: Dict containing the entire filesystem structure
        
    Returns:
        Generated content for the file
        
    Raises:
        RuntimeError: If content generation fails
    """
    logger = logging.getLogger("llmfs")
    
    # Convert raw dictionary to FileNode model
    node_dict = fs_structure[path]
    node = FileNode(
        type=node_dict["type"],
        content=node_dict.get("content", ""),
        children=node_dict.get("children"),
        attrs=FileAttrs(**node_dict["attrs"]),
        xattrs=node_dict.get("xattrs")
    )
    
    # Convert fs_structure to use FileNode models
    fs_nodes = {}
    for p, n in fs_structure.items():
        fs_nodes[p] = FileNode(
            type=n["type"],
            content=n.get("content", ""),
            children=n.get("children"),
            attrs=FileAttrs(**n["attrs"]),
            xattrs=n.get("xattrs")
        )
    
    # Create JsonFS instance for plugin registry
    from ..core.jsonfs import JsonFS
    fs = JsonFS()
    fs._data = fs_structure
    
    # Check for plugin-based generation first
    registry = PluginRegistry(root=fs)
    generator = registry.get_generator(path, node)
    
    if not generator:
        logger.error(f"No generator found for path: {path}")
        raise RuntimeError(f"No content generator available for {path}")
        
    try:
        return generator.generate(path, node, fs_nodes)
    except Exception as e:
        logger.error(f"Plugin generation failed: {str(e)}", exc_info=True)
        raise RuntimeError(f"Plugin content generation failed: {e}")
