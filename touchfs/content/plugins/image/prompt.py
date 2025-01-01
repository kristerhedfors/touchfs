"""Prompt generation and management for the image plugin."""
import os
import logging
from typing import Dict, Optional
from openai import OpenAI
from ....models.filesystem import FileNode
from ....config.settings import (
    find_nearest_prompt_file,
    _read_template,
    IMAGE_GENERATION_SYSTEM_PROMPT_TEMPLATE,
    set_last_final_prompt
)
from ....core.context.context import ContextBuilder
from .types import PromptGenerationResult

logger = logging.getLogger("touchfs")

def generate_base_prompt(path: str, fs_structure: Dict[str, FileNode]) -> PromptGenerationResult:
    """Generate the base prompt from filename or nearest prompt file.
    
    Args:
        path: Path of the image being generated
        fs_structure: Current filesystem structure
        
    Returns:
        PromptGenerationResult: Generated prompt with context
    """
    # Find nearest prompt file
    nearest_prompt_path = find_nearest_prompt_file(path, fs_structure)
    if nearest_prompt_path:
        nearest_node = fs_structure.get(nearest_prompt_path)
        # Handle both FileNode objects and dicts
        content = None
        if isinstance(nearest_node, dict):
            content = nearest_node.get('content')
        else:
            content = getattr(nearest_node, 'content', None)
            
        if content:
            logger.debug(f"""prompt_source:
  type: nearest_file
  path: {nearest_prompt_path}""")
            return PromptGenerationResult(
                base_prompt=content.strip(),
                context="",  # Will be filled by summarize_prompt
                summarized_prompt="",  # Will be filled by summarize_prompt
                source="nearest_file",
                source_path=nearest_prompt_path
            )
    
    # Generate from filename if no prompt file found
    logger.debug("""prompt_source:
  type: generated
  reason: no_nearest_file""")
    
    filename = os.path.splitext(os.path.basename(path))[0]
    # Replace underscores and dashes with spaces
    base_prompt = filename.replace('_', ' ').replace('-', ' ')
    
    # Make the prompt more descriptive and safe
    if "cat" in base_prompt.lower():
        base_prompt = "A cute and friendly cat sitting in a sunny window"
    else:
        base_prompt = f"A beautiful and safe image of {base_prompt}"
    
    return PromptGenerationResult(
        base_prompt=base_prompt,
        context="",  # Will be filled by summarize_prompt
        summarized_prompt="",  # Will be filled by summarize_prompt
        source="generated"
    )

def build_context(fs_structure: Dict[str, FileNode]) -> str:
    """Build context from filesystem structure.
    
    Args:
        fs_structure: Current filesystem structure
        
    Returns:
        str: Structured context string
    """
    builder = ContextBuilder()
    for file_path, node in fs_structure.items():
        # Handle both FileNode objects and dicts
        content = None
        if isinstance(node, dict):
            content = node.get('content')
        else:
            content = getattr(node, 'content', None)
            
        if content:  # Only add files that have content
            builder.add_file_content(file_path, content)
    
    return builder.build()

def summarize_prompt(client: OpenAI, base_prompt: str, context: str) -> str:
    """Use GPT-4 to create an optimized DALL-E prompt.
    
    Args:
        client: OpenAI client instance
        base_prompt: Base prompt to optimize
        context: Context to incorporate
        
    Returns:
        str: Optimized prompt for DALL-E
    """
    full_prompt = f"""Generate an image based on the following description and context.

Description: {base_prompt}

Context:
{context}

Important: Create an image that is consistent with both the description and the surrounding context."""

    # Load and use image generation system prompt template
    system_prompt = _read_template(IMAGE_GENERATION_SYSTEM_PROMPT_TEMPLATE)
    
    summarization_response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ],
        max_tokens=150
    )
    
    summarized_prompt = summarization_response.choices[0].message.content
    
    # Store the summarized prompt
    set_last_final_prompt(summarized_prompt)
    
    # Structured logging
    logger.info("""
image_generation_request:
  original_prompt: |
    %s
  final_prompt: |
    %s""", full_prompt, summarized_prompt)
    
    return summarized_prompt

def generate_prompt(client: OpenAI, path: str, fs_structure: Dict[str, FileNode]) -> PromptGenerationResult:
    """Generate a complete prompt for image generation.
    
    Args:
        client: OpenAI client instance
        path: Path of the image being generated
        fs_structure: Current filesystem structure
        
    Returns:
        PromptGenerationResult: Complete prompt with context and summary
    """
    # Get base prompt
    result = generate_base_prompt(path, fs_structure)
    
    # Build context
    context = build_context(fs_structure)
    result.context = context
    
    # Summarize prompt
    result.summarized_prompt = summarize_prompt(client, result.base_prompt, context)
    
    return result
