"""Cache statistics tracking."""

# Cache hit/miss counters
cache_hits = 0
cache_misses = 0

def increment_hits():
    """Increment cache hits counter."""
    global cache_hits
    cache_hits += 1

def increment_misses():
    """Increment cache misses counter."""
    global cache_misses
    cache_misses += 1

def get_stats():
    """Get current cache statistics."""
    return {
        'hits': cache_hits,
        'misses': cache_misses
    }

def reset_stats():
    """Reset cache statistics."""
    global cache_hits, cache_misses
    cache_hits = cache_misses = 0
