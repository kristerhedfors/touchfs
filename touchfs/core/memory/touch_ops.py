"""Touch operation detection and handling for Memory filesystem."""
from ...content.plugins.touch_detector import is_being_touched, find_touch_processes

# Touch detection is now handled by the TouchDetectorPlugin
# This module re-exports the detection functions for backwards compatibility
__all__ = ['is_being_touched', 'find_touch_processes']
