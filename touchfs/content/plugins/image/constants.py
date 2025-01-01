"""Constants for the image generation plugin."""

# Supported image formats and their MIME types
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
MIME_TYPES = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png'
}

# DALL-E configuration
DEFAULT_SIZE = "1024x1024"  # Square images are fastest to generate
DEFAULT_MODEL = "dall-e-3"
DEFAULT_QUALITY = "standard"

# Image format headers for validation
IMAGE_HEADERS = {
    'jpeg': b'\xFF\xD8\xFF',  # JPEG header
    'png': b'\x89PNG\r\n\x1A\n'  # PNG header
}
