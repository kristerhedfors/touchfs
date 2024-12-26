import pytest
from llmfs.content.plugins.config import ConfigPlugin
from llmfs.models.filesystem import FileNode

def create_file_node(content=None):
    """Helper to create a FileNode instance"""
    return FileNode(
        type="file",
        content=content,
        attrs={"st_mode": "33188"},  # 644 permissions
        xattrs={}
    )

def test_can_handle():
    plugin = ConfigPlugin()
    assert plugin.can_handle("/.llmfs/config.yaml", create_file_node())
    assert plugin.can_handle("/project/.llmfs/config.yaml", create_file_node())
    assert not plugin.can_handle("/config.yaml", create_file_node())
    assert not plugin.can_handle("/.llmfs/other.yaml", create_file_node())

def test_validate_config():
    plugin = ConfigPlugin()
    
    # Valid configurations
    assert plugin._validate_config({})
    assert plugin._validate_config({"generation": {"model": "gpt-4"}})
    
    # Invalid configurations
    assert not plugin._validate_config(None)
    assert not plugin._validate_config([])
    assert not plugin._validate_config("not a dict")

def test_load_yaml():
    plugin = ConfigPlugin()
    
    # Valid YAML
    assert plugin._load_yaml("key: value") == {"key": "value"}
    assert plugin._load_yaml("nested:\n  key: value") == {"nested": {"key": "value"}}
    
    # Invalid YAML
    assert plugin._load_yaml("invalid: : yaml") is None
    assert plugin._load_yaml("- unclosed list") is None

def test_merge_configs():
    plugin = ConfigPlugin()
    
    # Basic merge
    parent = {"a": 1, "b": 2}
    child = {"b": 3, "c": 4}
    merged = plugin._merge_configs(parent, child)
    assert merged == {"a": 1, "b": 3, "c": 4}
    
    # Nested merge
    parent = {"nested": {"x": 1, "y": 2}}
    child = {"nested": {"y": 3, "z": 4}}
    merged = plugin._merge_configs(parent, child)
    assert merged == {"nested": {"x": 1, "y": 3, "z": 4}}

def test_hierarchical_config():
    plugin = ConfigPlugin()
    fs_structure = {
        "/.llmfs/config.yaml": create_file_node("""
generation:
    model: gpt-3.5-turbo
logging:
    level: info
"""),
        "/project/.llmfs/config.yaml": create_file_node("""
generation:
    model: gpt-4
"""),
        "/project/subdir/.llmfs/config.yaml": create_file_node("""
logging:
    level: debug
""")
    }
    
    # Test root config
    root_config = plugin._get_parent_config("/.llmfs/config.yaml", fs_structure)
    assert root_config == {}
    
    # Test project config inherits from root
    project_config = plugin._get_parent_config("/project/.llmfs/config.yaml", fs_structure)
    assert project_config == {
        "generation": {"model": "gpt-3.5-turbo"},
        "logging": {"level": "info"}
    }
    
    # Test subdir config inherits from project and root
    subdir_config = plugin._get_parent_config("/project/subdir/.llmfs/config.yaml", fs_structure)
    assert subdir_config == {
        "generation": {"model": "gpt-4"},
        "logging": {"level": "info"}
    }

def test_generate_content():
    plugin = ConfigPlugin()
    fs_structure = {
        "/.llmfs/config.yaml": create_file_node("""
generation:
    model: gpt-3.5-turbo
logging:
    level: info
""")
    }
    
    # Test reading config
    node = create_file_node()
    content = plugin.generate("/project/.llmfs/config.yaml", node, fs_structure)
    assert "generation:" in content
    assert "model: gpt-3.5-turbo" in content
    
    # Test writing valid config
    node = create_file_node("""
generation:
    model: gpt-4
""")
    content = plugin.generate("/project/.llmfs/config.yaml", node, fs_structure)
    assert "model: gpt-4" in content
    assert "level: info" in content  # Inherited from parent
    
    # Test writing invalid config
    node = create_file_node("invalid: : yaml")
    content = plugin.generate("/project/.llmfs/config.yaml", node, fs_structure)
    assert "generation:" in content  # Keeps parent config
    assert "model: gpt-3.5-turbo" in content
