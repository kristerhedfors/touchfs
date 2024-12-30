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
    
    Important: Files that should be generated immediately when first accessed should have an xattr "generate_content" set to "true".
    
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
       - Add "xattrs": {"generate_content": "true"} for files that should be generated on first access
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
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # Log complete prompt metadata and messages in YAML format
        logger = logging.getLogger("llmfs")
        metadata_yaml = f"""prompt_metadata:
  type: filesystem_generation
  model: {model}
  temperature: 0.7
  num_messages: {len(messages)}
  response_format: json_object"""
        logger.debug(metadata_yaml)
        
        # Format messages as YAML
        messages_yaml = "messages:"
        for msg in messages:
            messages_yaml += f"\n  - role: {msg['role']}\n    content: |\n"
            # Indent content lines for YAML block scalar
            content_lines = msg['content'].split('\n')
            messages_yaml += '\n'.join(f"      {line}" for line in content_lines)
        logger.debug(messages_yaml)
        
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        # Parse and validate the response
        fs_data = json.loads(completion.choices[0].message.content)
        FileSystem.model_validate(fs_data)
        
        # Only filter .llmfs entries if this is a user-generated filesystem
        if "data" in fs_data and prompt and not prompt.startswith("internal:"):
            filtered_data = {}
            for path, node in fs_data["data"].items():
                if not path.startswith("/.llmfs/") and path != "/.llmfs":
                    if node.get("children"):
                        filtered_children = {}
                        for child_name, child_path in node["children"].items():
                            if not child_path.startswith("/.llmfs/") and child_path != "/.llmfs":
                                filtered_children[child_name] = child_path
                        node["children"] = filtered_children
                    filtered_data[path] = node
            fs_data["data"] = filtered_data

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
    
    Content generation is triggered during size calculation (stat operations) and only occurs when:
    1. The file has the generate_content extended attribute set to true
    2. The file is empty (0 bytes)
    
    This ensures safety by never overwriting existing content. Files are typically marked for
    generation either during initial filesystem creation or via the touch command, which sets
    the necessary extended attribute under the hood.
    
    Args:
        path: Path of the file to generate content for
        fs_structure: Dict containing the entire filesystem structure
        
    Returns:
        Generated content for the file
        
    Raises:
        RuntimeError: If content generation fails
    """
    logger = logging.getLogger("llmfs")
    
    # Get registry from fs_structure
    registry = fs_structure.get('_plugin_registry')
    if not registry:
        logger.error("No plugin registry found")
        raise RuntimeError("Plugin registry not available")
    logger.debug("status: plugin_registry_found")
    
    # Create a copy of fs_structure without the registry for node conversion
    fs_structure_copy = {k: v for k, v in fs_structure.items() if k != '_plugin_registry'}
    
    # Only filter .llmfs files if we're not accessing them directly
    if not path.startswith("/.llmfs/") and path != "/.llmfs":
        # Filter out .llmfs directory and its contents from context
        filtered_structure = {}
        for p, node in fs_structure_copy.items():
            if not p.startswith("/.llmfs/") and p != "/.llmfs":
                filtered_structure[p] = node
                # If this is a directory, filter its children too
                if node.get("children"):
                    filtered_children = {}
                    for child_name, child_path in node["children"].items():
                        if not child_path.startswith("/.llmfs/") and child_path != "/.llmfs":
                            filtered_children[child_name] = child_path
                    node["children"] = filtered_children
    else:
        # Use unfiltered structure for .llmfs files
        filtered_structure = fs_structure_copy

    logger.debug(f"""structure_info:
  filtered_keys: {list(filtered_structure.keys())}
  target_path: {path}
  node_structure: {filtered_structure.get(path, 'not_found')}""")
    
    try:
        # Convert raw dictionary to FileNode model
        node_dict = filtered_structure[path]
        node = FileNode(
            type=node_dict["type"],
            content=node_dict.get("content", ""),
            children=node_dict.get("children"),
            attrs=FileAttrs(**node_dict["attrs"]),
            xattrs=node_dict.get("xattrs")
        )

        # Convert remaining fs_structure to use FileNode models
        fs_nodes = {}
        for p, n in filtered_structure.items():
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
        # Skip caching only for .llmfs proc files
        is_proc_file = path.startswith("/.llmfs/")
        
        # Check cache first if enabled and not a proc file
        if get_cache_enabled() and not is_proc_file:
            # Create minimal cache key with only stable elements
            generator = registry.get_generator(path, node)
            try:
                prompt = generator.get_prompt(path, node, fs_nodes)
            except (AttributeError, NotImplementedError):
                # Fallback if get_prompt not implemented
                prompt = get_global_prompt()
            
            request_data = {
                "type": "file_content",
                "path": path,
                "model": get_model(),
                "prompt": prompt,
                "file_type": node.type
            }
            cached = get_cached_response(request_data)
            if cached:
                logger.debug(f"""cache:
  status: hit
  path: {path}""")
                return cached

        # Generate content
        content = generator.generate(path, node, fs_nodes)

        # Cache the result if enabled and not a proc file
        # For files with generate_content, cache after first generation
        if get_cache_enabled() and not is_proc_file:
            logger.debug(f"""cache:
  status: store
  path: {path}""")
            # Use same minimal cache key for storing
            generator = registry.get_generator(path, node)
            try:
                prompt = generator.get_prompt(path, node, fs_nodes)
            except (AttributeError, NotImplementedError):
                # Fallback if get_prompt not implemented
                prompt = get_global_prompt()
            
            request_data = {
                "type": "file_content",
                "path": path,
                "model": get_model(),
                "prompt": prompt,
                "file_type": node.type
            }
            cache_response(request_data, content)

        return content
    except Exception as e:
        logger.error(f"Plugin generation failed: {str(e)}", exc_info=True)
        raise RuntimeError(f"Plugin content generation failed: {e}")
