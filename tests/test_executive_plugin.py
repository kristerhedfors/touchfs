"""Tests for the executive summary generator plugin."""
import pytest
from llmfs.models.filesystem import FileNode
from llmfs.content.plugins.executive import ExecutiveGenerator

def create_file_node(content=None, xattrs=None):
    """Helper to create a FileNode instance"""
    return FileNode(
        type="file",
        content=content,
        attrs={"st_mode": "33188"},  # 644 permissions
        xattrs=xattrs or {}
    )

def test_generator_name():
    """Test generator returns correct name."""
    generator = ExecutiveGenerator()
    assert generator.generator_name() == "executive"

def test_proc_path():
    """Test proc path is correct."""
    generator = ExecutiveGenerator()
    assert generator.get_proc_path() == "executive"

def test_overlay_file_creation():
    """Test overlay file is created in .llmfs directory."""
    generator = ExecutiveGenerator()
    overlays = generator.get_overlay_files()
    assert len(overlays) == 1
    assert overlays[0].path == "/.llmfs/executive"
    assert overlays[0].xattrs["generator"] == "executive"

def test_summary_generation():
    """Test executive summary generation with mock filesystem."""
    # Create mock filesystem structure
    structure = {
        "/": FileNode(
            type="directory",
            children={
                "test.py": "/test.py",
                "README.md": "/README.md",
                "src": "/src",
                ".llmfs": "/.llmfs",
                "requirements.txt": "/requirements.txt"
            },
            attrs={"st_mode": "16877"}
        ),
        "/test.py": create_file_node(),
        "/README.md": create_file_node(),
        "/requirements.txt": create_file_node(),
        "/src": FileNode(
            type="directory",
            children={
                "main.py": "/src/main.py",
                "utils.py": "/src/utils.py"
            },
            attrs={"st_mode": "16877"}
        ),
        "/src/main.py": create_file_node(xattrs={"generator": "test_gen"}),
        "/src/utils.py": create_file_node(xattrs={"touched": "true"}),
        "/.llmfs": FileNode(
            type="directory",
            children={
                "tree": "/.llmfs/tree",
                "prompt.default": "/.llmfs/prompt.default"
            },
            attrs={"st_mode": "16877"}
        ),
        "/.llmfs/tree": create_file_node(xattrs={"generator": "tree"}),
        "/.llmfs/prompt.default": create_file_node(
            content="test prompt",
            xattrs={"generator": "prompt"}
        )
    }
    
    generator = ExecutiveGenerator()
    summary = generator.generate("/.llmfs/executive", create_file_node(), structure)
    
    # Verify basic content presence in filesystem summary
    assert "files" in summary.lower()
    assert "directories" in summary.lower()
    assert "python" in summary.lower()
    assert "readme" in summary.lower()
    assert "requirements.txt" in summary.lower()
    assert "generated" in summary.lower()
    assert "test_gen" in summary.lower()
    
    # Verify basic content presence in .llmfs summary
    assert ".llmfs" in summary.lower()
    assert len(summary.split()) >= 50  # Ensure reasonable length

def test_can_handle():
    """Test can_handle correctly identifies executive files."""
    generator = ExecutiveGenerator()
    
    # Should handle .llmfs/executive
    assert generator.can_handle(
        "/.llmfs/executive",
        create_file_node(xattrs={"generator": "executive"})
    )
    
    # Should not handle other files
    assert not generator.can_handle(
        "/other/file",
        create_file_node()
    )
    assert not generator.can_handle(
        "/.llmfs/other",
        create_file_node(xattrs={"generator": "other"})
    )
