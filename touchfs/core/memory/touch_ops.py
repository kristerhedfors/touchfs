"""Touch operation detection and handling for Memory filesystem."""
from ...content.plugins.touch_detector import is_being_touched

# Touch detection is now handled by the TouchDetectorPlugin
# This module re-exports the detection function for backwards compatibility
__all__ = ['is_being_touched']
