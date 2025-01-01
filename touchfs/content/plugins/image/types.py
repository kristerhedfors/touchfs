"""Type definitions for the image generation plugin."""
from typing import Optional, Dict, Union
from pydantic import BaseModel

class ImageGenerationConfig(BaseModel):
    """Configuration for image generation."""
    size: str
    quality: str
    model: str

class ImageGenerationResult(BaseModel):
    """Result of image generation."""
    content: bytes
    mime_type: str
    error: Optional[str] = None

class ImageValidationResult(BaseModel):
    """Result of image validation."""
    is_valid: bool
    format: Optional[str] = None
    error: Optional[str] = None

class PromptGenerationResult(BaseModel):
    """Result of prompt generation and summarization."""
    base_prompt: str
    context: str
    summarized_prompt: str
    source: str = "generated"  # "generated" or "nearest_file"
    source_path: Optional[str] = None
