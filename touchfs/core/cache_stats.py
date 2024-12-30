"""Cache statistics tracking with detailed logging."""
import logging
from typing import Dict

logger = logging.getLogger("touchfs")

# Cache hit/miss counters
cache_hits = 0
cache_misses = 0

def increment_hits():
    """Increment cache hits counter."""
    global cache_hits
    cache_hits += 1
    if cache_hits % 100 == 0:  # Log every 100 hits
        logger.info(f"Cache hits milestone reached: {cache_hits}")
    logger.debug(f"Cache hit recorded (total: {cache_hits})")

def increment_misses():
    """Increment cache misses counter."""
    global cache_misses
    cache_misses += 1
    if cache_misses % 100 == 0:  # Log every 100 misses
        logger.info(f"Cache misses milestone reached: {cache_misses}")
    logger.debug(f"Cache miss recorded (total: {cache_misses})")

def get_stats() -> Dict[str, int]:
    """Get current cache statistics."""
    stats = {
        'hits': cache_hits,
        'misses': cache_misses
    }
    total = cache_hits + cache_misses
    hit_rate = (cache_hits / total * 100) if total > 0 else 0
    logger.info(f"Cache stats - Hits: {cache_hits}, Misses: {cache_misses}, Hit Rate: {hit_rate:.1f}%")
    return stats

def reset_stats():
    """Reset cache statistics."""
    global cache_hits, cache_misses
    logger.warning("Resetting cache statistics")
    logger.info(f"Final stats before reset - Hits: {cache_hits}, Misses: {cache_misses}")
    cache_hits = cache_misses = 0
    logger.debug("Cache statistics reset complete")
