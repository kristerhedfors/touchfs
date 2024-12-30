"""Executive summary generator that provides high-level filesystem overviews."""
import hashlib
import json
import logging
from typing import Dict, List, Set, Tuple
from pathlib import Path
from pydantic import BaseModel
from openai import OpenAI
from functools import lru_cache
from .proc import ProcPlugin
from ...models.filesystem import FileNode
from ...config.settings import find_nearest_prompt_file, get_model

class ExecutiveSummary(BaseModel):
    """Model for structured executive summary output."""
    title: str
    summary: str

class ExecutiveGenerator(ProcPlugin):
    """Generator that creates executive summaries of filesystem content."""
    
    def generator_name(self) -> str:
        return "executive"
    
    def get_proc_path(self) -> str:
        return "executive"

    def _get_structure_hash(self, structure: Dict[str, FileNode], is_touchfs: bool) -> str:
        """Generate a stable hash of the filesystem structure."""
        def get_node_signature(path: str, node: FileNode) -> Tuple:
            # Only include path components after .touchfs for touchfs analysis
            if is_touchfs and not path.startswith("/.touchfs/"):
                return None
            # Skip .touchfs directory for main filesystem analysis
            if not is_touchfs and path.startswith("/.touchfs/"):
                return None
                
            if node.type == "file":
                return (
                    "file",
                    Path(path).suffix.lower(),
                    node.xattrs.get("generator", None),  # Include actual generator name
                    bool(node.xattrs.get("generate_content")),
                    Path(path).name.lower() in {
                        "readme.md", "requirements.txt", "setup.py", 
                        "pyproject.toml", "package.json", "dockerfile", 
                        "makefile", ".gitignore"
                    }
                )
            elif node.type == "directory":
                child_sigs = []
                if node.children:
                    for child_path in sorted(node.children.values()):
                        child_sig = get_node_signature(child_path, structure[child_path])
                        if child_sig:
                            child_sigs.append(child_sig)
                return ("directory", tuple(child_sigs))
            elif node.type == "symlink":
                return ("symlink", node.target if hasattr(node, 'target') else None)
            return None

        # Get root signature
        root_sig = get_node_signature("/", structure["/"])
        
        # Create stable string representation and hash it
        sig_str = json.dumps(root_sig, sort_keys=True)
        return hashlib.sha256(sig_str.encode()).hexdigest()

    def _analyze_directory(self, path: str, structure: Dict[str, FileNode], is_touchfs: bool = False) -> Dict:
        """Analyze a directory structure to gather statistics and key information."""
        stats = {
            "total_files": 0,
            "total_dirs": 0,
            "total_symlinks": 0,
            "generated_files": 0,
            "file_types": {},
            "generators": set(),
            "key_files": []
        }

        def should_include(p: str) -> bool:
            """Determine if path should be included based on context."""
            if is_touchfs:
                return p.startswith("/.touchfs/")
            return not p.startswith("/.touchfs/")

        def process_node(node_path: str, node: FileNode):
            if not should_include(node_path):
                return

            rel_path = node_path[7:] if is_touchfs and node_path.startswith("/.touchfs/") else node_path
            
            if node.type == "file":
                stats["total_files"] += 1
                
                # Track file extensions
                ext = Path(node_path).suffix.lower()
                if ext:
                    stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1

                # Track generated files and generators
                if node.xattrs:
                    if "generator" in node.xattrs:
                        stats["generated_files"] += 1
                        stats["generators"].add(node.xattrs["generator"])
                    elif node.xattrs.get("generate_content") == "true":
                        stats["generated_files"] += 1
                        prompt_path = find_nearest_prompt_file(node_path, structure)
                        if prompt_path:
                            stats["generators"].add(f"default:{Path(prompt_path).name}")
                        else:
                            stats["generators"].add("default")

                # Track important files using relative paths
                name = Path(node_path).name.lower()
                if name in {"readme.md", "requirements.txt", "setup.py", "pyproject.toml", 
                           "package.json", "dockerfile", "makefile", ".gitignore"}:
                    stats["key_files"].append(rel_path)

            elif node.type == "directory":
                if not (not is_touchfs and node_path == "/.touchfs"):
                    stats["total_dirs"] += 1
            elif node.type == "symlink":
                stats["total_symlinks"] += 1

            # Process children recursively
            if node.children:
                for child_name, child_path in node.children.items():
                    process_node(child_path, structure[child_path])

        # Start processing from root
        process_node(path, structure[path])
        
        # Convert generators set to sorted list for stable output
        stats["generators"] = sorted(stats["generators"])
        # Sort key files for stable output
        stats["key_files"].sort()
        
        return stats

    def _format_info_block(self, stats: Dict) -> str:
        """Format analysis results into a structured information block for LLM context."""
        lines = []
        
        # Basic statistics
        lines.append("STATISTICS:")
        lines.append(f"Files: {stats['total_files']}")
        lines.append(f"Directories: {stats['total_dirs']}")
        lines.append(f"Symlinks: {stats['total_symlinks']}")
        if stats['generated_files'] > 0:
            lines.append(f"Generated Files: {stats['generated_files']}")
        
        # File types
        if stats['file_types']:
            lines.append("\nFILE TYPES:")
            sorted_types = sorted(stats['file_types'].items(), key=lambda x: x[1], reverse=True)
            for ext, count in sorted_types[:5]:
                lines.append(f"{ext}: {count}")
        
        # Generators
        if stats['generators']:
            lines.append("\nACTIVE GENERATORS:")
            for gen in sorted(stats['generators']):
                lines.append(gen)
        
        # Key files
        if stats['key_files']:
            lines.append("\nKEY FILES:")
            for file in sorted(stats['key_files']):
                lines.append(file)
            
        return "\n".join(lines)

    def _generate_summary(self, info_block: str, is_touchfs: bool = False) -> str:
        """Generate a human-friendly summary using LLM."""
        client = OpenAI()
        
        system_prompt = """You are an expert at analyzing filesystem information and providing clear, concise summaries.
        Generate a brief executive summary (50-80 tokens) that explains the key aspects of the filesystem in a human-friendly way.
        Focus on what would be most relevant to a user trying to understand their project or system state."""
        
        user_prompt = f"""Here is the filesystem information to summarize:

{info_block}

{'This is information about the systems internal .touchfs directory.' if is_touchfs else 'This is information about the main project filesystem.'}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Log complete prompt metadata and messages in YAML format
        logger = logging.getLogger("touchfs")
        
        # Format metadata as YAML
        metadata_yaml = f"""prompt_metadata:
  type: executive_summary
  model: {get_model()}
  num_messages: {len(messages)}
  response_format: ExecutiveSummary
  is_touchfs_summary: {is_touchfs}"""
        logger.debug(metadata_yaml)
        
        # Format messages as YAML
        messages_yaml = "messages:"
        for msg in messages:
            messages_yaml += f"\n  - role: {msg['role']}\n    content: |\n"
            # Indent content lines for YAML block scalar
            content_lines = msg['content'].split('\n')
            messages_yaml += '\n'.join(f"      {line}" for line in content_lines)
        logger.debug(messages_yaml)
        
        completion = client.beta.chat.completions.parse(
            model=get_model(),
            messages=messages,
            response_format=ExecutiveSummary,
        )
        
        summary = completion.choices[0].message.parsed
        return f"# {summary.title}\n\n{summary.summary}"

    def _format_summary(self, stats: Dict, is_touchfs: bool = False) -> str:
        """Format analysis results into a human-friendly summary."""
        info_block = self._format_info_block(stats)
        return self._generate_summary(info_block, is_touchfs)

    def _get_cache_key(self, fs_structure: Dict[str, FileNode]) -> str:
        """Generate a cache key from the filesystem structure."""
        fs_hash = self._get_structure_hash(fs_structure, is_touchfs=False)
        touchfs_hash = self._get_structure_hash(fs_structure, is_touchfs=True)
        return f"{fs_hash}:{touchfs_hash}"

    def _stats_to_hashable(self, stats: Dict) -> str:
        """Convert stats dictionary to a hashable string representation."""
        # Create a stable string representation of the stats
        return json.dumps(stats, sort_keys=True)

    @lru_cache(maxsize=128)
    def _generate_cached(self, structure_key: str, fs_stats_key: str, touchfs_stats_key: str) -> str:
        """Generate cached summary from analyzed stats."""
        # Convert back to dictionaries
        fs_stats = json.loads(fs_stats_key)
        touchfs_stats = json.loads(touchfs_stats_key)
        
        # Generate summaries
        fs_summary = self._format_summary(fs_stats, is_touchfs=False)
        touchfs_summary = self._format_summary(touchfs_stats, is_touchfs=True)
        return f"{fs_summary}\n{touchfs_summary}"

    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Generate executive summaries of both filesystem and .touchfs directory."""
        # Get structure hash
        structure_key = self._get_cache_key(fs_structure)
        
        # Analyze structures and convert to hashable format
        fs_stats = self._analyze_directory("/", fs_structure, is_touchfs=False)
        touchfs_stats = self._analyze_directory("/", fs_structure, is_touchfs=True)
        fs_stats_key = self._stats_to_hashable(fs_stats)
        touchfs_stats_key = self._stats_to_hashable(touchfs_stats)
        
        # Generate cached summary
        return self._generate_cached(structure_key, fs_stats_key, touchfs_stats_key)
