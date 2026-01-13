"""
QR Code Tools - Generate QR codes
"""
import io
import logging
import qrcode
from qrcode.image.styledpil import StyledPilImage

logger = logging.getLogger(__name__)


def generate_qr(content: str, size: int = 300) -> bytes:
    """
    Generate QR code image.
    
    Args:
        content: Content to encode in QR code
        size: Output image size in pixels
        
    Returns:
        PNG image as bytes
    """
    qr = qrcode.QRCode(
        version=None,  # Auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(content)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Resize to requested size
    img = img.resize((size, size))
    
    output = io.BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    return output.read()
