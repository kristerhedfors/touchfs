import pytest
from llmfs.content.plugins.model import ModelPlugin, ModelConfig
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
    plugin = ModelPlugin()
    assert plugin.get_proc_path() == "model.default"
    
    # Test path handling from ProcPlugin
    assert plugin.can_handle("/.llmfs/model.default", create_file_node())
    assert not plugin.can_handle("/project/.llmfs/model.default", create_file_node())
    assert not plugin.can_handle("/model.default", create_file_node())

def test_default_model():
    """Test default model value"""
    plugin = ModelPlugin()
    node = create_file_node()
    content = plugin.generate("/.llmfs/model.default", node, {})
    assert content == ModelConfig().model

def test_custom_model_json():
    """Test setting custom model using JSON"""
    plugin = ModelPlugin()
    node = create_file_node('{"model": "gpt-3.5-turbo"}')
    content = plugin.generate("/.llmfs/model.default", node, {})
    assert content == "gpt-3.5-turbo"

def test_custom_model_raw():
    """Test setting custom model using raw text"""
    plugin = ModelPlugin()
    node = create_file_node('gpt-3.5-turbo')
    content = plugin.generate("/.llmfs/model.default", node, {})
    assert content == "gpt-3.5-turbo"

def test_invalid_json():
    """Test invalid JSON input is treated as raw model name"""
    plugin = ModelPlugin()
    node = create_file_node('{"model": invalid json')
    content = plugin.generate("/.llmfs/model.default", node, {})
    assert content == '{"model": invalid json'
