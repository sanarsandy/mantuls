"""
Signature Tools - Add signature images to PDF documents
"""
import io
import logging
from PIL import Image

logger = logging.getLogger(__name__)


def has_transparency(img):
    """Check if an image has any transparent pixels."""
    if img.mode != 'RGBA':
        return False
    
    # Check if alpha channel has any transparent pixels
    alpha = img.split()[3]
    # If min alpha is less than 255, there's some transparency
    return alpha.getextrema()[0] < 255


def add_signature(
    pdf_bytes: bytes,
    signature_image: bytes,
    page_number: int = 1,
    x: float = 100,
    y: float = 100,
    width: int = 150,
    height: int = 50
) -> bytes:
    """
    Add signature image to PDF at specified position.
    
    Args:
        pdf_bytes: PDF file content
        signature_image: Signature image bytes (PNG with transparency preferred)
        page_number: Page number to add signature (1-indexed)
        x: X position from left edge (in PDF points)
        y: Y position from bottom edge (in PDF points)
        width: Width of signature in PDF points
        height: Height of signature in PDF points
        
    Returns:
        PDF with signature as bytes
    """
    import pikepdf
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    
    # Open the source PDF
    source_pdf = pikepdf.Pdf.open(io.BytesIO(pdf_bytes))
    total_pages = len(source_pdf.pages)
    
    # Validate page number
    if page_number < 1 or page_number > total_pages:
        raise ValueError(f"Page number must be between 1 and {total_pages}")
    
    # Get page dimensions from target page
    target_page = source_pdf.pages[page_number - 1]
    media_box = target_page.MediaBox
    page_width = float(media_box[2]) - float(media_box[0])
    page_height = float(media_box[3]) - float(media_box[1])
    
    # Process signature image
    sig_img = Image.open(io.BytesIO(signature_image))
    
    # Ensure RGBA for transparency support
    if sig_img.mode != 'RGBA':
        sig_img = sig_img.convert('RGBA')
    
    # Create a temporary buffer for the signature image
    sig_buffer = io.BytesIO()
    sig_img.save(sig_buffer, format='PNG')
    sig_buffer.seek(0)
    
    # Create signature overlay using reportlab
    overlay_buffer = io.BytesIO()
    c = canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))
    
    # Draw signature image at specified position
    # Note: reportlab uses bottom-left origin, same as PDF
    img_reader = ImageReader(sig_buffer)
    c.drawImage(
        img_reader, 
        x, 
        y, 
        width=width, 
        height=height, 
        mask='auto'  # Preserve transparency
    )
    
    c.save()
    overlay_buffer.seek(0)
    
    # Open overlay as PDF
    overlay_pdf = pikepdf.Pdf.open(overlay_buffer)
    overlay_page = overlay_pdf.pages[0]
    
    # Apply overlay to target page only
    target_page.add_overlay(overlay_page)
    
    # Save result
    output = io.BytesIO()
    source_pdf.save(output)
    output.seek(0)
    
    logger.info(f"Added signature to page {page_number} at position ({x}, {y})")
    return output.read()


def get_pdf_page_count(pdf_bytes: bytes) -> int:
    """
    Get the number of pages in a PDF.
    
    Args:
        pdf_bytes: PDF file content
        
    Returns:
        Number of pages
    """
    import pikepdf
    
    pdf = pikepdf.Pdf.open(io.BytesIO(pdf_bytes))
    return len(pdf.pages)


def get_pdf_page_dimensions(pdf_bytes: bytes, page_number: int = 1) -> dict:
    """
    Get dimensions of a specific page.
    
    Args:
        pdf_bytes: PDF file content
        page_number: Page number (1-indexed)
        
    Returns:
        Dict with width and height in PDF points
    """
    import pikepdf
    
    pdf = pikepdf.Pdf.open(io.BytesIO(pdf_bytes))
    
    if page_number < 1 or page_number > len(pdf.pages):
        raise ValueError(f"Page number must be between 1 and {len(pdf.pages)}")
    
    page = pdf.pages[page_number - 1]
    media_box = page.MediaBox
    
    return {
        "width": float(media_box[2]) - float(media_box[0]),
        "height": float(media_box[3]) - float(media_box[1])
    }


def render_pdf_page_preview(pdf_bytes: bytes, page_number: int = 1, max_width: int = 800) -> bytes:
    """
    Render a PDF page as a JPEG image for preview.
    
    Args:
        pdf_bytes: PDF file content
        page_number: Page number (1-indexed)
        max_width: Maximum width of output image
        
    Returns:
        JPEG image as bytes
    """
    from pdf2image import convert_from_bytes
    
    # Convert specific page to image
    images = convert_from_bytes(
        pdf_bytes,
        first_page=page_number,
        last_page=page_number,
        dpi=150  # Good balance between quality and speed
    )
    
    if not images:
        raise ValueError(f"Could not render page {page_number}")
    
    img = images[0]
    
    # Resize if too large
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)
    
    # Convert to JPEG
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=85)
    output.seek(0)
    
    return output.read()

