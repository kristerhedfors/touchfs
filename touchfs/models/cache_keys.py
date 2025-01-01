"""Cache key models for different types of content generation."""
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field

class ImageCacheKey(BaseModel):
    """Cache key for image generation requests."""
    type: Literal["image"] = "image"
    filepath: str = Field(description="Complete relative path of the file being generated within the filesystem")
    fs_hash: str = Field(description="SHA256 hash of all relevant files in filesystem")
    
    class Config:
        frozen = True  # Makes the model immutable
        
    def __hash__(self):
        """Make the model hashable for caching."""
        import hashlib
        # Create a unique hash from filepath and filesystem hash
        key_str = f"{self.filepath}:{self.fs_hash}"
        return hash(hashlib.sha256(key_str.encode()).hexdigest())
        
    def to_cache_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary suitable for caching.
        
        Returns a minimal dictionary containing only the fields that affect the output.
        This ensures consistent cache keys across different file paths or timestamps.
        """
        import hashlib
        # Create a unique hash from filepath and filesystem hash
        key_str = f"{self.filepath}:{self.fs_hash}"
        key_hash = hashlib.sha256(key_str.encode()).hexdigest()
        return {
            "type": self.type,
            "cache_key": key_hash
        }
