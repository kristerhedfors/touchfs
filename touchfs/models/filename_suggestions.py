"""Models for filename suggestions."""
from pydantic import BaseModel
from typing import List

class FilenameSuggestions(BaseModel):
    """Collection of filename suggestions."""
    filenames: List[str]
