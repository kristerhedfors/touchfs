import pytest
from llmfs.content.plugins.generation import GenerationModelPlugin, GenerationConfig
from llmfs.models.filesystem import FileNode

def create_file_node(content=None):
    """Helper to create a FileNode instance"""
    return FileNode(
        type="file",
        content=content,
        attrs={"st_mode": "33188"},  # 644 permissions
        xattrs={}
    )

def test_proc_path():
    """Test that the plugin uses correct proc path"""
    plugin = GenerationModelPlugin()
    assert plugin.get_proc_path() == "generation.model"
    
    # Test path handling from ProcPlugin
    assert plugin.can_handle("/.llmfs/generation.model", create_file_node())
    assert not plugin.can_handle("/project/.llmfs/generation.model", create_file_node())
    assert not plugin.can_handle("/generation.model", create_file_node())

def test_default_model():
    """Test default model value"""
    plugin = GenerationModelPlugin()
    node = create_file_node()
    content = plugin.generate("/.llmfs/generation.model", node, {})
    assert content == GenerationConfig().model

def test_custom_model():
    """Test setting custom model"""
    plugin = GenerationModelPlugin()
    node = create_file_node('{"model": "gpt-3.5-turbo"}')
    content = plugin.generate("/.llmfs/generation.model", node, {})
    assert content == "gpt-3.5-turbo"

def test_invalid_model():
    """Test invalid model input"""
    plugin = GenerationModelPlugin()
    node = create_file_node('invalid json')
    with pytest.raises(Exception):
        plugin.generate("/.llmfs/generation.model", node, {})
