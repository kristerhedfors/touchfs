"""Feature flag configuration and management."""
import logging

logger = logging.getLogger("touchfs")

# Global feature flags
_cache_enabled = True

def get_cache_enabled() -> bool:
    """Get current cache enabled state.
    
    Returns:
        bool: Whether caching is enabled
    """
    return _cache_enabled

def set_cache_enabled(enabled: bool):
    """Update cache enabled state.
    
    Args:
        enabled: Whether to enable caching
    """
    global _cache_enabled
    logger.info(f"Setting cache enabled to: {enabled}")
    _cache_enabled = enabled
