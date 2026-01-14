"""
Images to PDF - Convert multiple images to a single PDF file
"""
import io
import logging
from typing import List
from PIL import Image

logger = logging.getLogger(__name__)


def images_to_pdf(images: List[bytes], quality: int = 85) -> bytes:
    """
    Convert multiple images to a single PDF file.
    
    Args:
        images: List of image bytes (JPEG, PNG, WEBP supported)
        quality: Output quality for compression (1-100)
        
    Returns:
        PDF file as bytes
    """
    if not images:
        raise ValueError("No images provided")
    
    pil_images = []
    
    for i, img_bytes in enumerate(images):
        try:
            img = Image.open(io.BytesIO(img_bytes))
            
            # Auto-rotate based on EXIF orientation
            try:
                from PIL import ExifTags
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == 'Orientation':
                        break
                exif = img._getexif()
                if exif is not None:
                    exif = dict(exif.items())
                    orientation_val = exif.get(orientation)
                    if orientation_val == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation_val == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation_val == 8:
                        img = img.rotate(90, expand=True)
            except (AttributeError, KeyError, IndexError):
                pass  # No EXIF data, skip rotation
            
            # Convert to RGB if needed (PDF doesn't support RGBA)
            if img.mode in ['RGBA', 'P']:
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if len(img.split()) == 4:
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            pil_images.append(img)
            logger.info(f"Processed image {i + 1}: {img.size}")
            
        except Exception as e:
            logger.error(f"Failed to process image {i + 1}: {e}")
            raise ValueError(f"Failed to process image {i + 1}: {str(e)}")
    
    # Create PDF from images
    output = io.BytesIO()
    
    if len(pil_images) == 1:
        pil_images[0].save(
            output, 
            format='PDF', 
            resolution=100.0
        )
    else:
        # First image as base, rest appended
        first_img = pil_images[0]
        rest_imgs = pil_images[1:]
        first_img.save(
            output, 
            format='PDF', 
            resolution=100.0,
            save_all=True,
            append_images=rest_imgs
        )
    
    output.seek(0)
    logger.info(f"Generated PDF with {len(pil_images)} pages, size: {len(output.getvalue())} bytes")
    return output.read()
