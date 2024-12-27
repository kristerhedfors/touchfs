"""Plugin that provides cache control through proc-like files."""
import logging
import os
import json
from typing import Dict
from pathlib import Path
from .multiproc import MultiProcPlugin
from ...models.filesystem import FileNode
from ...config.settings import get_cache_enabled, set_cache_enabled
from ...core.cache import get_cache_dir
from ...core import cache_stats

logger = logging.getLogger("llmfs")

class CacheControlPlugin(MultiProcPlugin):
    """Plugin that provides cache control through proc-like files.
    
    Creates the following control files:
    - .llmfs/cache_enabled: Write 0/1 to disable/enable caching
    - .llmfs/cache_stats: Read-only cache statistics
    - .llmfs/cache_clear: Write 1 to clear the cache
    - .llmfs/cache_list: Read-only list of cached request hashes
    """
    
    def generator_name(self) -> str:
        return "cache_control"
    
    def get_proc_paths(self) -> list[str]:
        """Return paths for cache control files."""
        return ["cache_enabled", "cache_stats", "cache_clear", "cache_list"]

    def _get_cache_size(self) -> int:
        """Get total size of cache files in bytes."""
        total = 0
        cache_dir = get_cache_dir()
        if cache_dir.exists():
            for file in cache_dir.glob("*.json"):
                total += file.stat().st_size
        return total

    def _clear_cache(self):
        """Clear all cached files."""
        cache_dir = get_cache_dir()
        if cache_dir.exists():
            for file in cache_dir.glob("*.json"):
                try:
                    file.unlink()
                except Exception as e:
                    logger.error(f"Failed to delete cache file {file}: {e}")
            logger.info("Cache cleared")

    def _list_cache(self) -> str:
        """List all cached request hashes."""
        result = []
        cache_dir = get_cache_dir()
        if cache_dir.exists():
            for file in sorted(cache_dir.glob("*.json")):
                hash = file.stem
                size = file.stat().st_size
                result.append(f"{hash} ({size} bytes)")
        return "\n".join(result) + "\n" if result else "Cache empty\n"
        
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Handle reads/writes to cache control files."""
        # Strip /.llmfs/ prefix to get proc path
        proc_path = path.replace("/.llmfs/", "")
        
        if proc_path == "cache_enabled":
            if node.content:
                try:
                    value = node.content.strip()
                    if value == "1":
                        set_cache_enabled(True)
                        logger.info("Cache enabled")
                    elif value == "0":
                        set_cache_enabled(False)
                        logger.info("Cache disabled")
                    else:
                        logger.warning(f"Invalid cache control value: {value}")
                except Exception as e:
                    logger.error(f"Failed to update cache state: {e}")
            return "1\n" if get_cache_enabled() else "0\n"

        elif proc_path == "cache_stats":
            stats = cache_stats.get_stats()
            cache_size = self._get_cache_size()
            return (
                f"Hits: {stats['hits']}\n"
                f"Misses: {stats['misses']}\n"
                f"Size: {cache_size} bytes\n"
                f"Enabled: {get_cache_enabled()}\n"
            )

        elif proc_path == "cache_clear":
            if node.content and node.content.strip() == "1":
                self._clear_cache()
            return "Write 1 to clear cache\n"

        elif proc_path == "cache_list":
            return self._list_cache()

        return ""
