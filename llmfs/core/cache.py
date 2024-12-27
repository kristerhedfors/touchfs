"""File-based caching system for LLM calls."""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Any, Dict
from . import cache_stats
from ..config.settings import get_cache_enabled

logger = logging.getLogger("llmfs")

def get_cache_dir() -> Path:
    """Get the cache directory path.
    
    Uses LLMFS_CACHE_FOLDER if set, otherwise defaults to ~/.llmfs.cache
    
    Returns:
        Path to cache directory
    """
    cache_dir = os.getenv("LLMFS_CACHE_FOLDER")
    if cache_dir:
        return Path(cache_dir)
    return Path.home() / ".llmfs.cache"

def compute_request_hash(request_data: Dict[str, Any]) -> str:
    """Compute a hash for the request data.
    
    Args:
        request_data: Dictionary containing request parameters
        
    Returns:
        Hash string for the request
    """
    # Sort dictionary to ensure consistent hashing
    serialized = json.dumps(request_data, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()

def get_cached_response(request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get cached response for a request if available.
    
    Args:
        request_data: Dictionary containing request parameters
        
    Returns:
        Cached response if available, None otherwise
    """
    if not get_cache_enabled():
        cache_stats.increment_misses()
        return None
        
    cache_dir = get_cache_dir()
    if not cache_dir.exists():
        cache_stats.increment_misses()
        return None
        
    request_hash = compute_request_hash(request_data)
    cache_file = cache_dir / f"{request_hash}.json"
    
    if not cache_file.exists():
        cache_stats.increment_misses()
        return None
        
    try:
        with cache_file.open('r') as f:
            cache_stats.increment_hits()
            logger.debug(f"Cache hit for request hash: {request_hash}")
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read cache file: {e}")
        cache_stats.increment_misses()
        return None

def cache_response(request_data: Dict[str, Any], response_data: Dict[str, Any]):
    """Cache a response for a request.
    
    Args:
        request_data: Dictionary containing request parameters
        response_data: Dictionary containing response data
    """
    if not get_cache_enabled():
        return
        
    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    request_hash = compute_request_hash(request_data)
    cache_file = cache_dir / f"{request_hash}.json"
    
    try:
        with cache_file.open('w') as f:
            json.dump(response_data, f, indent=2)
            logger.debug(f"Cached response for request hash: {request_hash}")
    except Exception as e:
        logger.error(f"Failed to write cache file: {e}")
