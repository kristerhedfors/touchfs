"""Cache handling for the image generation plugin."""
import hashlib
import logging
from typing import Dict, Optional, Tuple
from ....models.filesystem import FileNode
from ....models.cache_keys import ImageCacheKey
from ....core.cache import get_cached_response, cache_response
from ....config.settings import get_cache_enabled
from .types import ImageValidationResult
from .constants import IMAGE_HEADERS

logger = logging.getLogger("touchfs")

def calculate_filesystem_hash(fs_structure: Dict[str, FileNode], target_path: str) -> str:
    """Calculate a deterministic hash of the filesystem state.
    
    Args:
        fs_structure: Dictionary mapping paths to FileNode objects
        target_path: Path of the image being generated (excluded from hash)
        
    Returns:
        str: SHA256 hash of filesystem state
    """
    hasher = hashlib.sha256()
    
    # Sort files for deterministic hashing
    for file_path in sorted(fs_structure.keys()):
        # Skip the target image file
        if file_path == target_path:
            continue
            
        node = fs_structure[file_path]
        # Handle both FileNode objects and dicts
        content = None
        if isinstance(node, dict):
            content = node.get('content')
        else:
            content = getattr(node, 'content', None)
            
        if content:
            # Add path and content to hash
            hasher.update(file_path.encode())
            hasher.update(content if isinstance(content, bytes) else content.encode())
    
    return hasher.hexdigest()

def validate_image_data(content: bytes) -> ImageValidationResult:
    """Validate that content is valid image data.
    
    Args:
        content: Binary content to validate
        
    Returns:
        ImageValidationResult: Validation result with format if valid
    """
    try:
        # Check for common image format headers
        for fmt, header in IMAGE_HEADERS.items():
            if content.startswith(header):
                return ImageValidationResult(
                    is_valid=True,
                    format=fmt
                )
        
        return ImageValidationResult(
            is_valid=False,
            error="Content does not match any known image format headers"
        )
    except Exception as e:
        return ImageValidationResult(
            is_valid=False,
            error=f"Failed to validate image data: {str(e)}"
        )

def get_cached_image(path: str, fs_structure: Dict[str, FileNode]) -> Optional[bytes]:
    """Try to get a cached image for the given path and filesystem state.
    
    Args:
        path: Path of the image being generated
        fs_structure: Current filesystem structure
        
    Returns:
        Optional[bytes]: Cached image data if found and valid, None otherwise
    """
    if not get_cache_enabled():
        return None
        
    try:
        # Calculate filesystem hash
        fs_hash = calculate_filesystem_hash(fs_structure, path)
        
        # Create cache key
        cache_key = ImageCacheKey(
            filepath=path,
            fs_hash=fs_hash
        )
        
        # Try to get cached response
        cached = get_cached_response(cache_key.to_cache_dict())
        if cached:
            # Validate cached content
            validation = validate_image_data(cached)
            if validation.is_valid:
                logger.debug(f"""cache_operation:
  status: hit
  path: {path}
  format: {validation.format}
  size: {len(cached)} bytes""")
                return cached
            else:
                logger.warning(f"""cache_operation:
  status: invalid
  path: {path}
  error: {validation.error}""")
                
        return None
    except Exception as e:
        logger.error(f"""cache_operation:
  status: error
  path: {path}
  operation: check
  error: {str(e)}""")
        return None

def cache_image(path: str, fs_structure: Dict[str, FileNode], image_data: bytes) -> None:
    """Cache generated image data.
    
    Args:
        path: Path of the image being generated
        fs_structure: Current filesystem structure
        image_data: Generated image data to cache
    """
    if not get_cache_enabled():
        return
        
    try:
        # Calculate filesystem hash
        fs_hash = calculate_filesystem_hash(fs_structure, path)
        
        # Create cache key
        cache_key = ImageCacheKey(
            filepath=path,
            fs_hash=fs_hash
        )
        
        # Cache the image data
        cache_response(cache_key.to_cache_dict(), image_data)
        logger.debug(f"""cache_operation:
  status: stored
  path: {path}
  size: {len(image_data)} bytes""")
    except Exception as e:
        logger.error(f"""cache_operation:
  status: error
  path: {path}
  operation: store
  error: {str(e)}""")
