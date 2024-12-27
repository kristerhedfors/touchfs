"""Tests for the DefaultGenerator."""
import pytest
import logging
from llmfs.content.plugins.default import DefaultGenerator
from llmfs.models.filesystem import FileNode
from llmfs.config.settings import get_global_prompt

def create_file_node(content=None):
    """Helper to create a FileNode instance"""
    return FileNode(
        type="file",
        content=content,
        attrs={"st_mode": "33188"},  # 644 permissions
        xattrs={}
    )

def test_prompt_hierarchical_lookup(caplog):
    """Test hierarchical prompt file lookup"""
    generator = DefaultGenerator()
    caplog.set_level(logging.DEBUG)
    
    # Create filesystem structure
    fs_structure = {
        "/project/src/file.py": create_file_node(),
        "/project/src/.llmfs/prompt": create_file_node("src prompt"),
        "/project/.llmfs/prompt.default": create_file_node("project prompt.default"),
        "/project/.llmfs/prompt": create_file_node("project prompt"),
        "/.llmfs/prompt.default": create_file_node("root prompt.default"),
    }
    
    # Test finding src/prompt (closest prompt)
    content = generator._find_nearest_prompt("/project/src/file.py", fs_structure)
    assert content == "src prompt"
    assert "Found prompt at: /project/src/.llmfs/prompt" in caplog.text
    caplog.clear()
    
    # Test finding project/prompt when src has no prompt
    fs_structure.pop("/project/src/.llmfs/prompt")
    content = generator._find_nearest_prompt("/project/src/file.py", fs_structure)
    assert content == "project prompt"
    assert "Found prompt at: /project/.llmfs/prompt" in caplog.text
    caplog.clear()
    
    # Test finding project/prompt.default when no prompts exist
    fs_structure.pop("/project/.llmfs/prompt")
    content = generator._find_nearest_prompt("/project/src/file.py", fs_structure)
    assert content == "project prompt.default"
    assert "Found prompt.default at: /project/.llmfs/prompt.default" in caplog.text
    caplog.clear()
    
    # Test finding root prompt.default when no other prompts exist
    fs_structure.pop("/project/.llmfs/prompt.default")
    content = generator._find_nearest_prompt("/project/src/file.py", fs_structure)
    assert content == "root prompt.default"
    assert "Found prompt.default at: /.llmfs/prompt.default" in caplog.text
    caplog.clear()
    
    # Test falling back to global prompt when no files found
    fs_structure.pop("/.llmfs/prompt.default")
    content = generator._find_nearest_prompt("/project/src/file.py", fs_structure)
    assert content is None
    assert "No prompt files found in directory hierarchy" in caplog.text

def test_empty_prompt_files(caplog):
    """Test handling of empty prompt files"""
    generator = DefaultGenerator()
    caplog.set_level(logging.DEBUG)
    
    # Create filesystem structure with empty files
    fs_structure = {
        "/project/src/file.py": create_file_node(),
        "/project/src/.llmfs/prompt": create_file_node(""),  # Empty prompt
        "/project/.llmfs/prompt.default": create_file_node("project prompt.default"),
    }
    
    # Should skip empty prompt and find prompt.default
    content = generator._find_nearest_prompt("/project/src/file.py", fs_structure)
    assert content == "project prompt.default"
    assert "Empty prompt at:" in caplog.text
    assert "Found prompt.default at:" in caplog.text

def test_prompt_lookup_order(caplog):
    """Test that prompt is checked before prompt.default in each directory"""
    generator = DefaultGenerator()
    caplog.set_level(logging.DEBUG)
    
    # Create filesystem structure with both files at each level
    fs_structure = {
        "/project/src/file.py": create_file_node(),
        "/project/src/.llmfs/prompt": create_file_node("src prompt"),
        "/project/src/.llmfs/prompt.default": create_file_node("src prompt.default"),
        "/project/.llmfs/prompt": create_file_node("project prompt"),
        "/project/.llmfs/prompt.default": create_file_node("project prompt.default"),
        "/.llmfs/prompt": create_file_node("root prompt"),
        "/.llmfs/prompt.default": create_file_node("root prompt.default"),
    }
    
    # Should find src/prompt first
    content = generator._find_nearest_prompt("/project/src/file.py", fs_structure)
    assert content == "src prompt"
    assert "Found prompt at: /project/src/.llmfs/prompt" in caplog.text
    caplog.clear()
    
    # Remove src/prompt, should find src/prompt.default next
    fs_structure.pop("/project/src/.llmfs/prompt")
    content = generator._find_nearest_prompt("/project/src/file.py", fs_structure)
    assert content == "src prompt.default"
    assert "Found prompt.default at: /project/src/.llmfs/prompt.default" in caplog.text

def test_model_hierarchical_lookup(caplog):
    """Test hierarchical model file lookup"""
    generator = DefaultGenerator()
    caplog.set_level(logging.DEBUG)
    
    # Create filesystem structure
    fs_structure = {
        "/project/src/file.py": create_file_node(),
        "/project/src/.llmfs/model": create_file_node("gpt-4o-2024-08-06"),
        "/project/.llmfs/model.default": create_file_node("gpt-4"),
        "/project/.llmfs/model": create_file_node("gpt-3.5-turbo"),
        "/.llmfs/model.default": create_file_node("gpt-4o-2024-08-06"),
    }
    
    # Test finding src/model (closest model)
    content = generator._find_nearest_model("/project/src/file.py", fs_structure)
    assert content == "gpt-4o-2024-08-06"
    assert "Found model at: /project/src/.llmfs/model" in caplog.text
    caplog.clear()
    
    # Test finding project/model when src has no model
    fs_structure.pop("/project/src/.llmfs/model")
    content = generator._find_nearest_model("/project/src/file.py", fs_structure)
    assert content == "gpt-3.5-turbo"
    assert "Found model at: /project/.llmfs/model" in caplog.text
    caplog.clear()
    
    # Test finding project/model.default when no models exist
    fs_structure.pop("/project/.llmfs/model")
    content = generator._find_nearest_model("/project/src/file.py", fs_structure)
    assert content == "gpt-4"
    assert "Found model.default at: /project/.llmfs/model.default" in caplog.text
    caplog.clear()
    
    # Test finding root model.default when no other models exist
    fs_structure.pop("/project/.llmfs/model.default")
    content = generator._find_nearest_model("/project/src/file.py", fs_structure)
    assert content == "gpt-4o-2024-08-06"
    assert "Found model.default at: /.llmfs/model.default" in caplog.text

def test_empty_model_files(caplog):
    """Test handling of empty model files"""
    generator = DefaultGenerator()
    caplog.set_level(logging.DEBUG)
    
    # Create filesystem structure with empty files
    fs_structure = {
        "/project/src/file.py": create_file_node(),
        "/project/src/.llmfs/model": create_file_node(""),  # Empty model
        "/project/.llmfs/model.default": create_file_node("gpt-4"),
    }
    
    # Should skip empty model and find model.default
    content = generator._find_nearest_model("/project/src/file.py", fs_structure)
    assert content == "gpt-4"
    assert "Empty model at:" in caplog.text
    assert "Found model.default at:" in caplog.text
