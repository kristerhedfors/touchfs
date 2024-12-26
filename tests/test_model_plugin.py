"""Tests for the ModelPlugin."""
import pytest
import logging
from llmfs.content.plugins.model import ModelPlugin
from llmfs.models.filesystem import FileNode
from llmfs.config.settings import get_model, set_model

def create_file_node(content=None):
    """Helper to create a FileNode instance"""
    return FileNode(
        type="file",
        content=content,
        attrs={"st_mode": "33188"},  # 644 permissions
        xattrs={}
    )

def test_model_plugin_updates_global_config(caplog):
    """Test that model plugin updates global configuration with logging"""
    plugin = ModelPlugin()
    caplog.set_level(logging.INFO)
    
    # Save original model
    original_model = get_model()
    
    try:
        # Test with raw text
        node = create_file_node(content="gpt-3.5-turbo")
        content = plugin.generate("/.llmfs/model.default", node, {})
        assert content == "gpt-3.5-turbo"
        assert get_model() == "gpt-3.5-turbo"
        assert "Setting model to: gpt-3.5-turbo" in caplog.text
        
        # Test with JSON
        node = create_file_node(content='{"model": "gpt-4"}')
        content = plugin.generate("/.llmfs/model.default", node, {})
        assert content == "gpt-4"
        assert get_model() == "gpt-4"
        assert "Setting model to: gpt-4" in caplog.text
        
        # Test default
        node = create_file_node()
        content = plugin.generate("/.llmfs/model.default", node, {})
        default_model = get_model()  # Should use current model as default
        assert content == default_model
        assert get_model() == default_model
        assert f"Setting model to: {default_model}" in caplog.text
        
    finally:
        # Restore original model
        set_model(original_model)

def test_model_plugin_debug_logging(caplog):
    """Test debug level logging in model plugin"""
    plugin = ModelPlugin()
    caplog.set_level(logging.DEBUG)
    
    # Save original model
    original_model = get_model()
    
    try:
        # Test JSON parsing log
        node = create_file_node(content='{"model": "gpt-4"}')
        plugin.generate("/.llmfs/model.default", node, {})
        assert "Parsed model from JSON: gpt-4" in caplog.text
        
        # Test raw input log
        node = create_file_node(content="gpt-3.5-turbo")
        plugin.generate("/.llmfs/model.default", node, {})
        assert "Using raw model input: gpt-3.5-turbo" in caplog.text
        
        # Test default model log
        node = create_file_node()
        plugin.generate("/.llmfs/model.default", node, {})
        assert "Using default model:" in caplog.text
        
    finally:
        # Restore original model
        set_model(original_model)
