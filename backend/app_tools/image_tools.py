"""
Image Tools - Format conversion and compression
"""
import io
import logging
from PIL import Image

logger = logging.getLogger(__name__)


def convert_image(image_bytes: bytes, target_format: str = 'jpg', quality: int = 85) -> bytes:
    """
    Convert image to different format.
    
    Args:
        image_bytes: Original image bytes
        target_format: Target format ('jpg', 'png', 'webp')
        quality: Quality for lossy formats (1-100)
        
    Returns:
        Converted image as bytes
    """
    img = Image.open(io.BytesIO(image_bytes))
    
    # Convert to RGB if needed (for JPEG/WEBP from RGBA)
    if target_format in ['jpg', 'jpeg'] and img.mode in ['RGBA', 'P']:
        # Create white background
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
        img = background
    elif target_format in ['jpg', 'jpeg']:
        img = img.convert('RGB')
    
    output = io.BytesIO()
    
    if target_format in ['jpg', 'jpeg']:
        img.save(output, format='JPEG', quality=quality, optimize=True)
    elif target_format == 'png':
        img.save(output, format='PNG', optimize=True)
    elif target_format == 'webp':
        img.save(output, format='WEBP', quality=quality)
    else:
        raise ValueError(f"Unsupported format: {target_format}")
    
    output.seek(0)
    return output.read()
