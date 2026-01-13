
import io
from rembg import remove
from PIL import Image

def remove_background(image_bytes: bytes) -> bytes:
    """
    Remove background from image using AI (rembg).
    
    Args:
        image_bytes: Input image content
        
    Returns:
        PNG image bytes with transparent background
    """
    try:
        # Convert bytes to PIL Image
        input_image = Image.open(io.BytesIO(image_bytes))
        
        # Remove background
        # alpha_matting=True improves edge quality but is slower
        output_image = remove(input_image, alpha_matting=True, alpha_matting_foreground_threshold=240)
        
        # Save to bytes as PNG
        output_buffer = io.BytesIO()
        output_image.save(output_buffer, format="PNG")
        output_buffer.seek(0)
        
        return output_buffer.read()
    except Exception as e:
        raise ValueError(f"Failed to remove background: {str(e)}")
