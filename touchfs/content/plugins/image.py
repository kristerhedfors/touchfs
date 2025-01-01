"""Image generator plugin that creates images using OpenAI's DALL-E API."""
import os
import base64
import logging
from typing import Dict, Optional
from ...models.cache_keys import ImageCacheKey
import requests
from openai import OpenAI
from openai.types import ImagesResponse
from ...models.filesystem import FileNode
from ...config.settings import find_nearest_prompt_file, find_nearest_model_file, get_model, get_cache_enabled
from ...core.context.context import ContextBuilder
from ...core.cache import get_cached_response, cache_response
from .base import BaseContentGenerator, OverlayFile

class ImageGenerator(BaseContentGenerator):
    """Generator that creates images using OpenAI's DALL-E API."""
    
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
    DEFAULT_SIZE = "1024x1024"  # Square images are fastest to generate
    DEFAULT_MODEL = "dall-e-3"
    DEFAULT_QUALITY = "standard"
    
    def __init__(self):
        """Initialize the image generator."""
        self.logger = logging.getLogger("touchfs")
        try:
            self.client = OpenAI()  # Uses OPENAI_API_KEY environment variable
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            self.client = None
    
    def generator_name(self) -> str:
        return "image"
    
    def can_handle(self, path: str, node: FileNode) -> bool:
        """Check if this generator should handle the given file."""
        ext = os.path.splitext(path)[1].lower()
        return ext in self.SUPPORTED_EXTENSIONS
    
    def get_overlay_files(self):
        """No overlay files needed for image generation."""
        return []
    
    def _download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL and return as bytes."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            self.logger.error(f"Failed to download image: {str(e)}")
            return None
    
    def _generate_prompt(self, path: str, fs_structure: Dict[str, FileNode]) -> str:
        """Generate a prompt based on the file path and context."""
        # Find nearest prompt file
        nearest_prompt_path = find_nearest_prompt_file(path, fs_structure)
        if nearest_prompt_path:
            nearest_node = fs_structure.get(nearest_prompt_path)
            if nearest_node and nearest_node.content:
                return nearest_node.content.strip()
        
        # If no prompt file found, generate from filename
        filename = os.path.splitext(os.path.basename(path))[0]
        # Replace underscores and dashes with spaces
        base_prompt = filename.replace('_', ' ').replace('-', ' ')
        
        # Make the prompt more descriptive and safe
        if "cat" in base_prompt.lower():
            prompt = "A cute and friendly cat sitting in a sunny window"
        else:
            prompt = f"A beautiful and safe image of {base_prompt}"
        
        # Build context using ContextBuilder
        builder = ContextBuilder()
        for file_path, node in fs_structure.items():
            if node.content:  # Only add files that have content
                builder.add_file_content(file_path, node.content)
        
        structured_context = builder.build()
        
        # Create a detailed prompt that includes context
        return f"""Generate an image based on the following description and context.

Description: {prompt}

Context:
{structured_context}

Important: Create an image that is consistent with both the description and the surrounding context."""
    
    def generate(self, path: str, node: FileNode, fs_structure: Dict[str, FileNode]) -> Optional[bytes]:
        """Generate an image using OpenAI's DALL-E API."""
        # Return existing content if present
        if node and node.content:
            return node.content

        # Don't check cache until after prompt generation and summarization
        # so context from text files can influence the cache key
        try:
            self.logger.debug(f"""generation_start:
  path: {path}""")

            if not self.client:
                self.logger.error("OpenAI client not initialized")
                return None

            # Build context from all files
            builder = ContextBuilder()
            for file_path, node in fs_structure.items():
                if node.content:  # Only add files that have content
                    builder.add_file_content(file_path, node.content)
            structured_context = builder.build()

            # Calculate SHA256 hash of all relevant files
            import hashlib
            hasher = hashlib.sha256()
            
            # Sort files for deterministic hashing
            for file_path in sorted(fs_structure.keys()):
                # Skip the target image file
                if file_path == path:
                    continue
                    
                node = fs_structure[file_path]
                if node.content:
                    # Add path and content to hash
                    hasher.update(file_path.encode())
                    hasher.update(node.content if isinstance(node.content, bytes) else node.content.encode())
            
            fs_hash = hasher.hexdigest()
            
            # Check cache using filesystem hash and complete path
            if get_cache_enabled():
                cache_key = ImageCacheKey(
                    filepath=path,  # Complete relative path within filesystem
                    fs_hash=fs_hash
                )
                cached = get_cached_response(cache_key.to_cache_dict())
                if cached:
                    return cached

            # If cache miss, proceed with generation
            # Generate base prompt from filename
            base_name = os.path.splitext(os.path.basename(path))[0]
            base_prompt = base_name.replace('_', ' ').replace('-', ' ')
            
            # Find nearest prompt file
            nearest_prompt_path = find_nearest_prompt_file(path, fs_structure)
            if nearest_prompt_path:
                nearest_node = fs_structure.get(nearest_prompt_path)
                if nearest_node and nearest_node.content:
                    base_prompt = nearest_node.content.strip()
                    self.logger.debug(f"""prompt_source:
  type: nearest_file
  path: {nearest_prompt_path}""")
            else:
                self.logger.debug("""prompt_source:
  type: generated
  reason: no_nearest_file""")

            # Create full prompt with context
            full_prompt = f"""Generate an image based on the following description and context.

Description: {base_prompt}

Context:
{structured_context}

Important: Create an image that is consistent with both the description and the surrounding context."""

            # Use GPT to summarize the prompt, with emphasis on image references in context
            summarization_response = self.client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": """You are an expert at creating image generation prompts. Your task is to create a clear, descriptive prompt for DALL-E 3 to generate an image.

For hero.jpg, create a prompt that describes:
- A heroic figure in a dynamic pose
- Modern or futuristic armor/clothing
- Dramatic lighting and atmosphere
- Any weapons or special effects
- Environmental details that enhance the heroic theme

Rules:
1. Write in clear, descriptive language that DALL-E can understand
2. Focus on visual details and composition
3. Include specific colors, lighting, and atmosphere
4. Keep the tone epic and heroic
5. Stay within 150 tokens
6. Output the prompt directly, no meta-commentary"""},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=150
            )
            
            summarized_prompt = summarization_response.choices[0].message.content

            # Store the summarized prompt as last_final_prompt
            from ...config.settings import set_last_final_prompt
            set_last_final_prompt(summarized_prompt)

            # Log prompts with clear highlighting
            self.logger.info("================================================================")
            self.logger.info("                    IMAGE GENERATION REQUEST                     ")
            self.logger.info("================================================================")
            self.logger.info(f"Path: {path}")
            self.logger.info("Model: dall-e-3")
            self.logger.info("Original Prompt:")
            self.logger.info("-----------------")
            self.logger.info(full_prompt)
            self.logger.info("\nSummarized Prompt (150 tokens):")
            self.logger.info("-----------------------------")
            self.logger.info(summarized_prompt)
            self.logger.info("================================================================")
            
            # Log the full prompt and summary for debugging
            self.logger.info("================================================================")
            self.logger.info("                    CONTEXT AND SUMMARY DEBUG                    ")
            self.logger.info("================================================================")
            self.logger.info(f"Full context:\n{structured_context}")
            self.logger.info(f"\nSummarized prompt:\n{summarized_prompt}")
            self.logger.info("================================================================")

            # Generate image using the summarized prompt
            response: ImagesResponse = self.client.images.generate(
                model="dall-e-3",
                prompt=summarized_prompt,
                size=self.DEFAULT_SIZE,
                quality=self.DEFAULT_QUALITY,
                response_format="b64_json",  # Get base64 data directly instead of URL
                n=1
            )
            
            if not response.data:
                self.logger.error("No image data in response")
                return None
                
            # Get base64 image data
            if not response.data or not hasattr(response.data[0], 'model_dump'):
                self.logger.error("Invalid response format from OpenAI API")
                return None
                
            image_data = response.data[0].model_dump().get('b64_json')
            if not image_data:
                self.logger.error("No base64 data in response")
                return None
                
            try:
                # Add data URI header based on file extension
                ext = os.path.splitext(path)[1].lower()
                mime_type = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png'
                }[ext]
                
                # Add padding if needed
                padding_needed = len(image_data) % 4
                if padding_needed:
                    image_data += '=' * (4 - padding_needed)
                
                # Decode base64 to raw binary
                binary_data = base64.b64decode(image_data)
                
                # Cache the result using complete path and filesystem hash
                if get_cache_enabled():
                    cache_key = ImageCacheKey(
                        filepath=path,  # Complete relative path within filesystem
                        fs_hash=fs_hash
                    )
                    cache_response(cache_key.to_cache_dict(), binary_data)
                
                self.logger.debug(f"""generation_complete:
  content_type: binary
  mime_type: {mime_type}
  content_length: {len(binary_data)}""")
                return binary_data
            except Exception as e:
                self.logger.error(f"Failed to decode base64 image: {str(e)}")
                return None
            
        except Exception as e:
            self.logger.error(f"Failed to generate image: {str(e)}")
            return None
