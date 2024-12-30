"""Default content generator using OpenAI."""
import os
import json
import logging
from typing import Dict, Optional
from openai import OpenAI
from ...models.filesystem import FileNode, GeneratedContent
from ...config.logger import setup_logging
from ...config.settings import get_model, get_global_prompt, find_nearest_model_file, find_nearest_prompt_file
from ...core.context.context import ContextBuilder, build_context
from .base import BaseContentGenerator

def get_openai_client() -> OpenAI:
    """Initialize OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    return OpenAI()

class DefaultGenerator(BaseContentGenerator):
    """Default generator that uses OpenAI to generate file content."""
    
    def generator_name(self) -> str:
        return "default"
        
    def can_handle(self, path: str, node: FileNode) -> bool:
        """Handle any file that doesn't have a specific generator assigned."""
        return (node.xattrs is None or 
                "generator" not in node.xattrs or 
                node.xattrs.get("generator") == self.generator_name())
                
    def get_prompt(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Get the prompt that would be used for generation."""
        # Find nearest prompt file
        nearest_prompt_path = find_nearest_prompt_file(path, fs_structure)
        if nearest_prompt_path:
            nearest_node = fs_structure.get(nearest_prompt_path)
            if nearest_node and nearest_node.content:
                return nearest_node.content.strip()
        return get_global_prompt()
    
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> str:
        """Generate content using OpenAI."""
        logger = logging.getLogger("llmfs")
        logger.debug(f"""generation_start:
  path: {path}""")
        
        try:
            client = get_openai_client()
            logger.debug("status: openai_client_initialized")
            
            # Try to find nearest prompt file
            nearest_prompt_path = find_nearest_prompt_file(path, fs_structure)
            if nearest_prompt_path:
                nearest_node = fs_structure.get(nearest_prompt_path)
                if nearest_node and nearest_node.content:
                    system_prompt = nearest_node.content.strip()
                    logger.debug(f"""prompt_source:
  type: nearest_file
  path: {nearest_prompt_path}""")
                else:
                    system_prompt = get_global_prompt()
                    logger.debug("""prompt_source:
  type: global
  reason: nearest_file_empty""")
            else:
                system_prompt = get_global_prompt()
                logger.debug("""prompt_source:
  type: global
  reason: no_nearest_file""")

            # Try to find nearest model file
            nearest_model_path = find_nearest_model_file(path, fs_structure)
            if nearest_model_path:
                nearest_node = fs_structure.get(nearest_model_path)
                if nearest_node and nearest_node.content:
                    model = nearest_node.content.strip()
                    logger.debug(f"""model_source:
  type: nearest_file
  path: {nearest_model_path}""")
                else:
                    model = get_model()
                    logger.debug("""model_source:
  type: global
  reason: nearest_file_empty""")
            else:
                model = get_model()
                logger.debug("""model_source:
  type: global
  reason: no_nearest_file""")

            logger.debug(f"""api_request:
  path: {path}
  action: send""")
            # Build context using ContextBuilder
            builder = ContextBuilder()
            for file_path, node in fs_structure.items():
                if node.content:  # Only add files that have content
                    builder.add_file_content(file_path, node.content)
            
            structured_context = builder.build()
            
            # Replace {CONTEXT} in system prompt with structured context
            final_prompt = system_prompt.replace("{CONTEXT}", structured_context)
            
            # Construct messages
            messages = [
                {"role": "system", "content": final_prompt},
                {"role": "user", "content": f"Generate content for {path}"}
            ]
            
            # Log complete prompt metadata and messages in YAML format
            metadata_yaml = f"""prompt_metadata:
  type: chat_completion
  model: {model}
  temperature: 0.2
  num_messages: {len(messages)}
  response_format: GeneratedContent
  target_file: {path}"""
            logger.debug(metadata_yaml)
            
            # Format messages as YAML
            messages_yaml = "messages:"
            for msg in messages:
                messages_yaml += f"\n  - role: {msg['role']}\n    content: |\n"
                # Indent content lines for YAML block scalar
                content_lines = msg['content'].split('\n')
                messages_yaml += '\n'.join(f"      {line}" for line in content_lines)
            logger.debug(messages_yaml)
            
            try:
                completion = client.beta.chat.completions.parse(
                    model=model,
                    messages=messages,
                    response_format=GeneratedContent,
                    temperature=0.2
                )
                logger.debug("status: api_response_received")
                content = completion.choices[0].message.parsed.content
                logger.debug(f"""generation_complete:
  content_length: {len(content)}""")
                return content
            except Exception as api_error:
                logger.error(f"OpenAI API error: {str(api_error)}", exc_info=True)
                raise
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to generate content: {e}")
