"""Plugin that provides cache control through proc-like files."""
import logging
import os
import json
from typing import Dict
from pathlib import Path
from datetime import datetime
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
                try:
                    with file.open('r') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and "response" in data:
                            total += len(json.dumps(data["response"]).encode())
                        else:
                            total += file.stat().st_size
                except Exception:
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
        """List cached request hashes with prompt segments.
        
        Returns most recent 64 entries, sorted by date (newest first).
        """
        result = []
        cache_dir = get_cache_dir()
        if cache_dir.exists():
            # Get all cache files with their timestamps
            files_with_time = []
            for file in cache_dir.glob("*.json"):
                try:
                    ctime = file.stat().st_ctime
                    files_with_time.append((file, ctime))
                except Exception as e:
                    logger.error(f"Failed to get stats for cache file {file}: {e}")
                    continue
            
            # Sort by timestamp (newest first) and take top 64
            sorted_files = [f[0] for f in sorted(files_with_time, key=lambda x: x[1], reverse=True)][:64]
            
            # Process files
            for file in sorted_files:
                try:
                    # Get hash from filename
                    hash = file.stem.split('_', 1)[0] if '_' in file.stem else file.stem[:8]
                    
                    # Get file creation time
                    ctime = file.stat().st_ctime
                    timestamp = datetime.fromtimestamp(ctime).strftime('%b %d %H:%M')
                    
                    # Read entire file content first
                    with file.open('r') as f:
                        content = f.read()
                    
                    # Parse JSON from complete content
                    data = json.loads(content)
                    if isinstance(data, dict) and "request" in data:
                        # Format request string with fixed width
                        path = data["request"].get("path", "")
                        req_str = json.dumps(data["request"])
                        if len(req_str) > 60:
                            req_str = req_str[:57] + "..."
                        
                        # Calculate response size
                        response_size = len(json.dumps(data.get("response", {})).encode())
                        
                        # Get either path or prompt from request
                        path = data["request"].get("path", "")
                        prompt = data["request"].get("prompt", "")
                        
                        # Choose what to display - prefer prompt for filesystem requests
                        display_text = ""
                        if prompt and data["request"].get("type") == "filesystem":
                            display_text = prompt
                        elif path:
                            display_text = path
                            
                        # Truncate if needed
                        if len(display_text) > 40:
                            display_text = display_text[:37] + "..."
                        
                        size_str = f"{response_size:,d}"
                        result.append(f"{hash}  {timestamp}  {display_text:<40}  {size_str:>10} bytes\n")
                    else:
                        # For legacy or invalid files, use file size
                        size = file.stat().st_size
                        size_str = f"{size:,d}"
                        result.append(f"{hash}  {timestamp}  {'<invalid>':<40}  {size_str:>10} bytes\n")
                except Exception as e:
                    logger.error(f"Failed to read cache file {file}: {e}")
                    # Get file creation time even for error cases
                    ctime = file.stat().st_ctime
                    timestamp = datetime.fromtimestamp(ctime).strftime('%b %d %H:%M')
                    result.append(f"{hash}  {timestamp}  {'<error>':<40}  {'0':>10} bytes\n")
        return "".join(result) if result else "Cache empty\n"
        
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
            content = self._list_cache()
            # Force content to be available immediately
            node.content = content
            return content

        return ""
