from typing import Dict, Optional
import yaml
import os
from pathlib import Path
import logging
from ..plugins.base import BaseContentGenerator
from ...models.filesystem import FileNode

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when configuration validation fails"""
    pass

class ConfigPlugin(BaseContentGenerator):
    def generator_name(self) -> str:
        return "config"
        
    def can_handle(self, path: str, node: FileNode) -> bool:
        """
        Check if this generator should handle the given file.
        Returns True for .llmfs/config.yaml files and /config/config.yaml.
        """
        return path.endswith("/.llmfs/config.yaml") or path == "/config/config.yaml"

    def _validate_config(self, config: Dict) -> bool:
        """
        Validate configuration structure and types.
        """
        try:
            if not isinstance(config, dict):
                logger.error("Configuration must be a dictionary")
                return False
            
            # Validate required sections
            required_sections = ["generation", "logging", "plugins"]
            for section in required_sections:
                if section in config and not isinstance(config[section], dict):
                    logger.error(f"'{section}' must be a dictionary")
                    return False
            
            # Validate generation section if present
            if "generation" in config:
                gen = config["generation"]
                if "model" in gen and not isinstance(gen["model"], str):
                    logger.error("'model' must be a string")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            return False

    def _load_yaml(self, content: str) -> Optional[Dict]:
        """
        Load and parse YAML content with error handling
        """
        if not content:
            return {}
            
        try:
            result = yaml.safe_load(content)
            if not isinstance(result, dict):
                logger.error("YAML content must be a dictionary")
                return None
            return result
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML: {str(e)}")
            return None

    def _get_parent_config(self, path: str, fs_structure: Dict[str, FileNode]) -> Dict:
        """
        Get configuration by walking up the directory tree
        """
        # For root config, return empty dict
        if path == "/.llmfs/config.yaml":
            return {}
            
        # Build path list from root to target directory
        paths = []
        current_path = str(Path(path).parent.parent)  # Start from parent of .llmfs
        while True:
            paths.append(current_path)
            if current_path == "/":
                break
            current_path = str(Path(current_path).parent)
            
        # Process paths from root down
        final_config = {}
        for current_path in reversed(paths):
            config_path = os.path.join(current_path, ".llmfs/config.yaml")
            if config_path != path and config_path in fs_structure:  # Skip current file
                node = fs_structure[config_path]
                if node.content:
                    current_config = self._load_yaml(node.content)
                    if current_config:
                        final_config = self._merge_configs(final_config, current_config)
            
        return final_config

    def _merge_configs(self, parent: Dict, child: Dict) -> Dict:
        """
        Merge configurations with child overriding parent
        """
        merged = parent.copy()
        for key, value in child.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged

    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """
        Handle configuration file operations
        """
        # Get parent configuration first
        parent_config = self._get_parent_config(path, fs_structure)
        
        if node.content:
            # Attempting to write new configuration
            new_config = self._load_yaml(node.content)
            if not new_config or not self._validate_config(new_config):
                logger.error("Invalid configuration provided, keeping existing configuration")
                return yaml.dump(parent_config, default_flow_style=False)
            
            # Configuration is valid, merge with parent
            merged_config = self._merge_configs(parent_config, new_config)
            return yaml.dump(merged_config, default_flow_style=False)
        else:
            # For reading, return parent config if it exists, otherwise empty dict
            return yaml.dump(parent_config, default_flow_style=False)
