"""Tests for the PromptPlugin."""
import pytest
from unittest.mock import patch
from touchfs.content.plugins.prompt import PromptPlugin
from touchfs.models.filesystem import FileNode
from touchfs.content.plugins.base import OverlayFile

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

def test_prompt_plugin_exposes_last_final_prompt() -> None:
    """Test that prompt plugin correctly exposes the last final prompt."""
    plugin = PromptPlugin()
    node = create_file_node()
    
    # Initially should indicate no prompts generated
    content = plugin.generate("/.touchfs/prompt_last_final", node, {})
    assert content.strip() == "No prompts generated yet"
    
    # Set a last final prompt
    test_final_prompt = "This is the final prompt that was sent to LLM"
    with patch('touchfs.content.plugins.prompt.get_last_final_prompt', return_value=test_final_prompt):
        content = plugin.generate("/.touchfs/prompt_last_final", node, {})
        assert content.strip() == test_final_prompt

def test_prompt_plugin_overlay_files() -> None:
    """Test that prompt plugin provides correct overlay files."""
    plugin = PromptPlugin()
    overlays = plugin.get_overlay_files()
    
    # Should provide two overlay files
    assert len(overlays) == 2
    
    # Verify overlay file properties
    for overlay in overlays:
        assert isinstance(overlay, OverlayFile)
        assert overlay.path.startswith("/.touchfs/")
        assert overlay.path.endswith(("prompt_default", "prompt_last_final"))
        assert overlay.attrs["st_mode"] == "33188"  # 644 permissions
        assert overlay.xattrs["generate_content"] == b"true"
        assert overlay.xattrs["generator"] == "prompt"

def test_prompt_plugin_proc_paths() -> None:
    """Test that prompt plugin exposes correct proc paths."""
    plugin = PromptPlugin()
    paths = plugin.get_proc_paths()
    assert "prompt_default" in paths
    assert "prompt_last_final" in paths
    assert len(paths) == 2
