"""Filesystem generation and dialogue handling for TouchFS mount command.

This module provides functionality for generating filesystem structures and handling
interactive dialogue with users during filesystem generation.
"""

import os
import sys
from typing import Dict, Any, Optional
from ...content.generator import generate_filesystem

def format_simple_tree(data: Dict[str, Any], path: str = "/", indent: str = "") -> str:
    """Format a directory tree in a clean, standardized way.
    
    Args:
        data: The filesystem data structure
        path: Current path being processed
        indent: Current indentation level
        
    Returns:
        A string representation of the tree
    """
    lines = []
    
    # Get children for current path
    children = {}
    for p in data:
        if p != path and os.path.dirname(p) == path:
            name = os.path.basename(p)
            children[name] = p
    
    # Sort children for consistent output
    names = sorted(children.keys())
    
    for i, name in enumerate(names):
        child_path = children[name]
        is_last = i == len(names) - 1
        
        # Add directory indicator
        if data[child_path].get("type") == "directory":
            name = name + "/"
        
        # Choose prefix based on whether this is the last item
        prefix = "└── " if is_last else "├── "
        
        # Build the line as a single string
        line = indent + prefix + name
        lines.append(line)
        
        # Recursively process directories
        if data[child_path].get("type") == "directory":
            next_indent = indent + ("    " if is_last else "│   ")
            child_lines = format_simple_tree(data, child_path, next_indent)
            if child_lines:  # Only add if there are child lines
                lines.extend(child_lines.split('\n'))
    
    # Filter out empty lines and join with newlines
    return '\n'.join(line for line in lines if line.strip())

def handle_filesystem_dialogue(initial_prompt: str, yes: bool = False) -> Optional[dict]:
    """Handle the interactive dialogue for filesystem generation.
    
    Args:
        initial_prompt: Initial filesystem generation prompt
        yes: Whether to auto-confirm without prompting
        
    Returns:
        Generated filesystem data if successful, None if cancelled
    """
    dialogue_history = []
    current_prompt = initial_prompt
    
    while True:
        try:
            print(f"\nGenerating filesystem from prompt: {current_prompt[:50]}...", file=sys.stdout)
            sys.stdout.flush()
            
            result = generate_filesystem(current_prompt)
            tree_visualization = format_simple_tree(result["data"])
            
            if tree_visualization:
                print("\nGenerated Filesystem Structure:")
                print(tree_visualization)
                
                if yes:
                    return result["data"]
                    
                print("\nAccept this structure? Type 'y' to accept, 'n' to reject, or enter new instructions: ", end='')
                sys.stdout.flush()
                response = sys.stdin.readline().strip()
                
                dialogue_history.append({
                    "prompt": current_prompt,
                    "result": tree_visualization,
                    "response": response
                })
                
                if response.lower() == 'y':
                    return result["data"]
                elif response.lower() == 'n':
                    print("\nPlease enter new instructions to try again, or press Ctrl+C to cancel")
                    return None
                else:
                    # Update prompt with new instructions while preserving history
                    print(f"\nRefining structure with new instructions: '{response}'")
                    print("You can keep refining until the structure is what you want.")
                    current_prompt = f"""Previous attempts:
{chr(10).join(f'Prompt: {h["prompt"]}{chr(10)}Result:{chr(10)}{h["result"]}{chr(10)}Response: {h["response"]}{chr(10)}' for h in dialogue_history)}

New instructions: {response}"""
            else:
                print("Error: No filesystem structure was generated")
                return None
                
        except Exception as e:
            print(f"Error generating filesystem: {e}", file=sys.stderr)
            return None
