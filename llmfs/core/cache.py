"""File-based caching system for LLM calls with comprehensive logging."""
import os
import json
import hashlib
import base64
import logging
from pathlib import Path
from typing import Optional, Any, Dict, Tuple
from . import cache_stats
from ..config.settings import get_cache_enabled

logger = logging.getLogger("llmfs")

# Initialize cache system logging
logger.info("Initializing LLMFS cache system")

def get_cache_dir() -> Path:
    """Get the cache directory path.
    
    Uses LLMFS_CACHE_FOLDER if set, otherwise defaults to ~/.llmfs.cache
    
    Returns:
        Path to cache directory
    """
    cache_dir = os.getenv("LLMFS_CACHE_FOLDER")
    if cache_dir:
        logger.debug(f"Using custom cache directory from LLMFS_CACHE_FOLDER: {cache_dir}")
        return Path(cache_dir)
    default_dir = Path.home() / ".llmfs.cache"
    logger.debug(f"Using default cache directory: {default_dir}")
    return default_dir

def compute_cache_filename(request_data: Dict[str, Any]) -> Tuple[str, str]:
    """Compute cache filename components.
    
    Args:
        request_data: Dictionary containing request parameters
        
    Returns:
        Tuple of (8-byte hash, 40-byte base64 path-safe prompt)
    """
    # Sort dictionary to ensure consistent hashing
    serialized = json.dumps(request_data, sort_keys=True)
    full_hash = hashlib.sha256(serialized.encode()).hexdigest()
    hash_prefix = full_hash[:8]  # First 8 bytes
    
    # Get content to encode in filename - use entire request for uniqueness
    content = json.dumps(request_data, sort_keys=True)
    
    # Use URL-safe base64 encoding and take first 40 bytes
    safe_prompt = base64.urlsafe_b64encode(content.encode()).decode()[:40]
    # Pad with - if shorter than 40 bytes
    safe_prompt = safe_prompt.ljust(40, '-')
    
    logger.debug(f"Generated cache filename components - Hash: {hash_prefix}, Safe prompt: {safe_prompt}")
    return hash_prefix, safe_prompt

def get_cached_response(request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get cached response for a request if available.
    
    Args:
        request_data: Dictionary containing request parameters
        
    Returns:
        Cached response if available, None otherwise
    """
    request_type = request_data.get("type", "unknown")
    logger.debug(f"Checking cache for request type: {request_type}")
    
    if not get_cache_enabled():
        logger.info("Cache disabled - recording miss")
        cache_stats.increment_misses()
        return None
        
    cache_dir = get_cache_dir()
    if not cache_dir.exists():
        logger.warning(f"Cache directory does not exist: {cache_dir}")
        cache_stats.increment_misses()
        return None
        
    hash_prefix, safe_prompt = compute_cache_filename(request_data)
    cache_file = cache_dir / f"{hash_prefix}_{safe_prompt}.json"
    
    if not cache_file.exists():
        logger.debug(f"Cache miss - File not found: {cache_file.name}")
        cache_stats.increment_misses()
        return None
        
    try:
        logger.debug(f"Reading cache file: {cache_file.name}")
        with cache_file.open('r') as f:
            cache_data = json.load(f)
            cache_stats.increment_hits()
            logger.info(f"Cache hit for {request_type} request - File: {cache_file.name}")
            return cache_data.get("response") if isinstance(cache_data, dict) else cache_data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse cache file {cache_file.name}: {e}")
        cache_stats.increment_misses()
        return None
    except Exception as e:
        logger.error(f"Failed to read cache file {cache_file.name}: {str(e)}", exc_info=True)
        cache_stats.increment_misses()
        return None

def cache_response(request_data: Dict[str, Any], response_data: Dict[str, Any]):
    """Cache a response for a request.
    
    Args:
        request_data: Dictionary containing request parameters
        response_data: Dictionary containing response data
    """
    request_type = request_data.get("type", "unknown")
    logger.debug(f"Attempting to cache response for request type: {request_type}")
    
    if not get_cache_enabled():
        logger.debug("Cache disabled - skipping cache write")
        return
        
    # Don't cache proc file requests
    if request_data.get("type") == "file_content" and request_data.get("path", "").startswith("/.llmfs/"):
        logger.debug("Skipping cache for proc file request")
        return
        
    cache_dir = get_cache_dir()
    try:
        if not cache_dir.exists():
            logger.info(f"Creating cache directory: {cache_dir}")
        cache_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create cache directory {cache_dir}: {str(e)}", exc_info=True)
        return
    
    hash_prefix, safe_prompt = compute_cache_filename(request_data)
    cache_file = cache_dir / f"{hash_prefix}_{safe_prompt}.json"
    
    try:
        cache_data = {
            "request": request_data,
            "response": response_data
        }
        logger.debug(f"Writing cache file: {cache_file.name}")
        with cache_file.open('w') as f:
            json.dump(cache_data, f, indent=2)
            f.flush()  # Ensure data is written to disk
            os.fsync(f.fileno())  # Force flush to disk
            logger.info(f"Successfully cached {request_type} response to: {cache_file.name}")
    except Exception as e:
        logger.error(f"Failed to write cache file {cache_file.name}: {str(e)}", exc_info=True)
