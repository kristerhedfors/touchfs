"""Tests for the PromptPlugin."""
import pytest
import logging
import os
from llmfs.content.plugins.prompt import PromptPlugin
from llmfs.models.filesystem import FileNode
from llmfs.config.settings import get_global_prompt, set_global_prompt

def create_file_node(content=None):
    """Helper to create a FileNode instance"""
    return FileNode(
        type="file",
        content=content,
        attrs={"st_mode": "33188"},  # 644 permissions
        xattrs={}
    )

def test_prompt_plugin_updates_global_config(caplog):
    """Test that prompt plugin updates global configuration with logging"""
    plugin = PromptPlugin()
    caplog.set_level(logging.DEBUG)
    
    # Save original prompt
    original_prompt = get_global_prompt()
    
    try:
        # Test with raw text
        test_prompt = "Generate {path} as a Python script"
        node = create_file_node(content=test_prompt)
        content = plugin.generate("/.llmfs/prompt.default", node, {})
        assert content.strip() == test_prompt
        assert get_global_prompt() == test_prompt
        assert "Using raw prompt input" in caplog.text
        
        # Test with JSON
        test_prompt = "Create {path} with these rules"
        node = create_file_node(content=f'{{"prompt": "{test_prompt}"}}')
        content = plugin.generate("/.llmfs/prompt.default", node, {})
        assert content.strip() == test_prompt
        assert get_global_prompt() == test_prompt
        assert "Parsed prompt from JSON" in caplog.text
        
        # Test default
        node = create_file_node()
        content = plugin.generate("/.llmfs/prompt.default", node, {})
        default_prompt = get_global_prompt()
        assert content.strip() == default_prompt
        assert "Using default prompt template" in caplog.text
        
    finally:
        # Restore original prompt
        set_global_prompt(original_prompt)

def test_nearest_prompt_lookup():
    """Test that prompt plugin correctly uses nearest prompt file"""
    plugin = PromptPlugin()
    
    # Save original prompt
    original_prompt = get_global_prompt()
    
    try:
        # Create filesystem structure with multiple prompt files
        fs_structure = {
            "/project/.llmfs/prompt": create_file_node(
                content='{"prompt": "Project level prompt"}'
            ),
            "/project/subdir/.llmfs/prompt": create_file_node(
                content='{"prompt": "Subdir level prompt"}'
            ),
            "/project/subdir/file.py": create_file_node(),
            "/project/other/file.txt": create_file_node(),
        }
        
        # Test subdir file uses nearest prompt
        content = plugin.generate(
            "/project/subdir/file.py", 
            fs_structure["/project/subdir/file.py"],
            fs_structure
        )
        assert content.strip() == "Subdir level prompt"
        
        # Test other file falls back to project prompt
        content = plugin.generate(
            "/project/other/file.txt",
            fs_structure["/project/other/file.txt"],
            fs_structure
        )
        assert content.strip() == "Project level prompt"
        
        # Test prompt file doesn't reference itself
        content = plugin.generate(
            "/project/subdir/.llmfs/prompt",
            fs_structure["/project/subdir/.llmfs/prompt"],
            fs_structure
        )
        assert content.strip() == "Subdir level prompt"
        
    finally:
        # Restore original prompt
        set_global_prompt(original_prompt)

def test_prompt_format_variables():
    """Test that prompt templates preserve format variables"""
    plugin = PromptPlugin()
    
    # Save original prompt
    original_prompt = get_global_prompt()
    
    try:
        # Test path variable
        test_prompt = "Generate {path} with specific requirements"
        node = create_file_node(content=test_prompt)
        content = plugin.generate("/.llmfs/prompt.default", node, {})
        assert "{path}" in content
        assert get_global_prompt() == test_prompt
        
        # Test filesystem structure variable
        test_prompt = "Structure: {json.dumps({p: n.model_dump() for p, n in fs_structure.items()}, indent=2)}"
        node = create_file_node(content=test_prompt)
        content = plugin.generate("/.llmfs/prompt.default", node, {})
        assert "{json.dumps" in content
        assert "fs_structure" in content
        assert get_global_prompt() == test_prompt
        
    finally:
        # Restore original prompt
        set_global_prompt(original_prompt)
