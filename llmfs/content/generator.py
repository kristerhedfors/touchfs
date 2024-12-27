"""Content generation using OpenAI's API and plugins."""
import os
import json
import logging
from typing import Dict
from openai import OpenAI
from ..models.filesystem import FileSystem, GeneratedContent, FileNode, FileAttrs
from ..config.logger import setup_logging
from ..config.settings import get_model, get_cache_enabled
from .plugins.registry import PluginRegistry
from ..core.cache import get_cached_response, cache_response

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
            "st_mode": "16877"  # directory with 755 permissions
          }
        },
        "/example": {
          "type": "directory",
          "children": {},
          "attrs": {
            "st_mode": "16877"
          }
        }
      }
    }

    Rules:
    1. The response must have a top-level "data" field containing the filesystem structure
    2. Each node must have a "type" ("file", "directory", or "symlink")
    3. Each node must have "attrs" with st_mode
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
        # Check cache first if enabled
        if get_cache_enabled():
            request_data = {
                "type": "filesystem",
                "prompt": prompt,
                "model": get_model(),
                "system_prompt": system_prompt
            }
            cached = get_cached_response(request_data)
            if cached:
                return cached

        # Generate if not cached
        model = get_model()
        completion = client.chat.completions.create(
            model=model,
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

        # Cache the result if enabled
        if get_cache_enabled():
            request_data = {
                "type": "filesystem",
                "prompt": prompt,
                "model": get_model(),
                "system_prompt": system_prompt
            }
            cache_response(request_data, fs_data)

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
    
    # Get and remove registry first before any conversions
    registry = None
    if '_plugin_registry' in fs_structure:
        registry = fs_structure.pop('_plugin_registry')
        logger.debug("Found and removed plugin registry from fs_structure")
        logger.debug(f"Structure keys after registry removal: {list(fs_structure.keys())}")
        if path in fs_structure:
            logger.debug(f"Node structure for {path}: {fs_structure[path]}")
    
    try:
        # Convert raw dictionary to FileNode model
        node_dict = fs_structure[path]
        node = FileNode(
            type=node_dict["type"],
            content=node_dict.get("content", ""),
            children=node_dict.get("children"),
            attrs=FileAttrs(**node_dict["attrs"]),
            xattrs=node_dict.get("xattrs")
        )

        # Convert remaining fs_structure to use FileNode models
        fs_nodes = {}
        for p, n in fs_structure.items():
            fs_nodes[p] = FileNode(
                type=n["type"],
                content=n.get("content", ""),
                children=n.get("children"),
                attrs=FileAttrs(**n["attrs"]),
                xattrs=n.get("xattrs")
            )
    except Exception as e:
        logger.error(f"Error converting to FileNode models: {e}", exc_info=True)
        raise RuntimeError(f"Failed to convert filesystem structure: {e}")
    
    if not registry:
        logger.error("No plugin registry found")
        raise RuntimeError("Plugin registry not available")
        
    generator = registry.get_generator(path, node)
    
    if not generator:
        logger.error(f"No generator found for path: {path}")
        raise RuntimeError(f"No content generator available for {path}")
        
    try:
        # Check cache first if enabled
        if get_cache_enabled():
            request_data = {
                "type": "file_content",
                "path": path,
                "node": node.model_dump(),
                "fs_structure": {k: v.model_dump() for k, v in fs_nodes.items()}
            }
            cached = get_cached_response(request_data)
            if cached:
                    # Update node content when using cached content
                    node.content = cached
                    # Update the original fs_structure node
                    fs_structure[path]["content"] = cached
                    return cached

        # Generate if not cached
        content = generator.generate(path, node, fs_nodes)

        # Cache the result if enabled
        if get_cache_enabled():
            request_data = {
                "type": "file_content",
                "path": path,
                "node": node.model_dump(),
                "fs_structure": {k: v.model_dump() for k, v in fs_nodes.items()}
            }
            cache_response(request_data, content)

        return content
    except Exception as e:
        logger.error(f"Plugin generation failed: {str(e)}", exc_info=True)
        raise RuntimeError(f"Plugin content generation failed: {e}")
