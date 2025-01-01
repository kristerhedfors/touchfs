"""Configuration package initialization."""
from . import settings
from . import templates
from . import model
from . import prompts
from . import filesystem
from . import features

# Re-export all settings for backward compatibility
from .settings import *
