"""Plugin that provides the prompt.default file in .llmfs."""
from typing import List
from pydantic import BaseModel
from .proc import ProcPlugin
from .base import OverlayFile
from ...models.filesystem import FileNode

DEFAULT_PROMPT = """Generate appropriate content for the file {path}.
The file exists within this filesystem structure:
{json.dumps({p: n.model_dump() for p, n in fs_structure.items()}, indent=2)}

Consider:
1. The file's location and name to determine its purpose
2. Its relationship to other files and directories
3. Follow appropriate best practices for the file type
4. Generate complete, working code that would make sense in this context

For Python files:
- If it's a module's main implementation file (like operations.py), include relevant classes and functions
- If it's a test file, include proper test cases using pytest
- If it's __init__.py, include appropriate imports and exports
- Include docstrings and type hints
- Ensure the code is complete and properly structured

For shell scripts:
- Include proper shebang line
- Add error handling and logging
- Make the script robust and reusable

Keep the content focused and production-ready."""

class PromptConfig(BaseModel):
    prompt: str = DEFAULT_PROMPT

class PromptPlugin(ProcPlugin):
    """Plugin that provides the prompt.default file in .llmfs."""
    
    def generator_name(self) -> str:
        return "prompt"
    
    def get_proc_path(self) -> str:
        """Return path for prompt.default file."""
        return "prompt.default"
        
    def generate(self, path: str, node: FileNode, fs_structure: dict) -> str:
        """Return the prompt content, either from input or default."""
        if node.content:
            # Parse and validate input
            try:
                # First try parsing as JSON
                config = PromptConfig.model_validate_json(node.content)
                return config.prompt + "\n"
            except:
                # If not JSON, treat as raw prompt text
                return node.content.strip() + "\n"
        return DEFAULT_PROMPT + "\n"
