"""Tests for the PromptPlugin."""
import pytest
from unittest.mock import patch
from touchfs.content.plugins.prompt import PromptPlugin
from touchfs.models.filesystem import FileNode

def create_file_node() -> FileNode:
    """Helper to create a FileNode instance."""
    return FileNode(
        type="file",
        content=None,
        attrs={"st_mode": "33060"},  # 444 permissions (read-only)
        xattrs={}
    )

def test_prompt_plugin_exposes_current_prompt() -> None:
    """Test that prompt plugin correctly exposes the current prompt configuration."""
    plugin = PromptPlugin()
    
    # Mock the template read to return a known value
    test_prompt = "Test prompt template"
    with patch('touchfs.config.settings._read_template', return_value=test_prompt):
        node = create_file_node()
        content = plugin.generate("/.touchfs/prompt_default", node, {})
        assert content.strip() == test_prompt
