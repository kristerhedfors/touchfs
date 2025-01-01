"""Tests for the ModelPlugin."""
import pytest
from touchfs.content.plugins.model import ModelPlugin
from touchfs.models.filesystem import FileNode
from touchfs.config.settings import get_model, set_model

def create_file_node() -> FileNode:
    """Helper to create a FileNode instance."""
    return FileNode(
        type="file",
        content=None,
        attrs={"st_mode": "33060"},  # 444 permissions (read-only)
        xattrs={}
    )

def test_model_plugin_exposes_current_model() -> None:
    """Test that model plugin correctly exposes the current model configuration."""
    plugin = ModelPlugin()
    
    # Save original model
    original_model = get_model()
    
    try:
        # Test with a different model
        test_model = "gpt-4"
        set_model(test_model)
        
        node = create_file_node()
        content = plugin.generate("/.touchfs/model_default", node, {})
        assert content == test_model
        
    finally:
        # Restore original model
        set_model(original_model)
