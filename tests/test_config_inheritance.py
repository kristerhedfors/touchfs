"""Tests for configuration inheritance and overlay paths."""
import os
import tempfile
from pathlib import Path
import pytest
from touchfs.config.model import set_overlay_path as set_model_overlay_path, get_model
from touchfs.config.prompts import set_overlay_path as set_prompt_overlay_path, get_global_prompt

def write_config(path: Path, content: str):
    """Helper to write configuration files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

def test_model_config_inheritance(tmp_path):
    """Test model configuration inheritance with overlay paths."""
    # Create test directories
    base_dir = tmp_path / "base"
    overlay_dir = tmp_path / "overlay"
    
    # Create config files in base directory
    write_config(base_dir / ".model", "base-model")
    write_config(base_dir / ".touchfs" / "model_default", "base-touchfs-model")
    
    # Create config files in overlay directory
    write_config(overlay_dir / ".model", "overlay-model")
    write_config(overlay_dir / ".touchfs" / "model_default", "overlay-touchfs-model")
    
    # Test without overlay
    set_model_overlay_path(None)
    os.environ.pop("TOUCHFS_DEFAULT_MODEL", None)  # Clear env var
    assert get_model() == "gpt-4o-2024-08-06"  # Default model
    
    # Test with overlay
    set_model_overlay_path(str(overlay_dir))
    assert get_model() == "overlay-model"  # Should find .model in overlay
    
    # Test JSON config
    write_config(overlay_dir / ".model", '{"model": "json-model", "temperature": 0.7}')
    assert get_model() == "json-model"  # Should parse JSON config
    
    # Test environment variable override
    os.environ["TOUCHFS_DEFAULT_MODEL"] = "env-model"
    assert get_model() == "env-model"  # Env should override files
    
    # Clean up environment
    os.environ.pop("TOUCHFS_DEFAULT_MODEL", None)

def test_prompt_config_inheritance(tmp_path):
    """Test prompt configuration inheritance with overlay paths."""
    # Create test directories
    base_dir = tmp_path / "base"
    overlay_dir = tmp_path / "overlay"
    
    # Create config files in base directory
    write_config(base_dir / ".prompt", "base-prompt")
    write_config(base_dir / ".touchfs" / "prompt_default", "base-touchfs-prompt")
    
    # Create config files in overlay directory
    write_config(overlay_dir / ".prompt", "overlay-prompt")
    write_config(overlay_dir / ".touchfs" / "prompt_default", "overlay-touchfs-prompt")
    
    # Test without overlay
    set_prompt_overlay_path(None)
    os.environ.pop("TOUCHFS_GLOBAL_PROMPT", None)  # Clear env var
    assert "content generator for a virtual filesystem" in get_global_prompt()  # Default template
    
    # Test with overlay
    set_prompt_overlay_path(str(overlay_dir))
    assert get_global_prompt() == "overlay-prompt"  # Should find .prompt in overlay
    
    # Test JSON config
    write_config(overlay_dir / ".prompt", '{"prompt": "json-prompt", "style": "comprehensive"}')
    assert get_global_prompt() == "json-prompt"  # Should parse JSON config
    
    # Test environment variable override
    os.environ["TOUCHFS_GLOBAL_PROMPT"] = "env-prompt"
    assert get_global_prompt() == "env-prompt"  # Env should override files
    
    # Clean up environment
    os.environ.pop("TOUCHFS_GLOBAL_PROMPT", None)

def test_config_inheritance_order(tmp_path):
    """Test configuration inheritance order with multiple levels."""
    project = tmp_path / "project"
    src = project / "src"
    api = src / "api"
    
    # Create nested config structure
    write_config(project / ".prompt", "project-prompt")
    write_config(src / ".prompt", "src-prompt")
    write_config(api / ".prompt", "api-prompt")
    
    write_config(project / ".model", "project-model")
    write_config(src / ".model", "src-model")
    write_config(api / ".model", "api-model")
    
    # Ensure environment variables are cleared
    os.environ.pop("TOUCHFS_DEFAULT_MODEL", None)
    os.environ.pop("TOUCHFS_GLOBAL_PROMPT", None)
    
    # Test model inheritance
    set_model_overlay_path(str(project))
    assert get_model() == "project-model"
    
    set_model_overlay_path(str(src))
    assert get_model() == "src-model"
    
    set_model_overlay_path(str(api))
    assert get_model() == "api-model"
    
    # Test prompt inheritance
    set_prompt_overlay_path(str(project))
    assert get_global_prompt() == "project-prompt"
    
    set_prompt_overlay_path(str(src))
    assert get_global_prompt() == "src-prompt"
    
    set_prompt_overlay_path(str(api))
    assert get_global_prompt() == "api-prompt"

def test_config_file_precedence(tmp_path):
    """Test precedence between different config file locations."""
    project = tmp_path / "project"
    
    # Ensure environment variables are cleared
    os.environ.pop("TOUCHFS_DEFAULT_MODEL", None)
    os.environ.pop("TOUCHFS_GLOBAL_PROMPT", None)
    
    # Create both .model and .touchfs/model_default
    write_config(project / ".model", "root-model")
    write_config(project / ".touchfs" / "model_default", "touchfs-model")
    
    # Create both .prompt and .touchfs/prompt_default
    write_config(project / ".prompt", "root-prompt")
    write_config(project / ".touchfs" / "prompt_default", "touchfs-prompt")
    
    # Test model precedence
    set_model_overlay_path(str(project))
    assert get_model() == "root-model"  # .model should take precedence
    
    # Test prompt precedence
    set_prompt_overlay_path(str(project))
    assert get_global_prompt() == "root-prompt"  # .prompt should take precedence
