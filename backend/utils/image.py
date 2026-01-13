"""
Image utility functions for OCR preprocessing
"""
import cv2
import numpy as np
from pdf2image import convert_from_bytes
import logging

logger = logging.getLogger(__name__)


def load_image_from_bytes(file_bytes: bytes, dpi: int = 200) -> np.ndarray:
    """
    Load image from bytes, handling both image files and PDFs.
    
    Args:
        file_bytes: Raw bytes of the file
        dpi: DPI for PDF rendering
        
    Returns:
        OpenCV image (BGR format)
    """
    # Try to decode as image first
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # If failed, check if it's a PDF
    if img is None:
        if file_bytes.startswith(b'%PDF'):
            logger.info(f"Detected PDF file, converting to image with DPI {dpi}...")
            images = convert_from_bytes(
                file_bytes, 
                first_page=1, 
                last_page=1, 
                dpi=dpi, 
                thread_count=4
            )
            if images:
                pil_image = images[0]
                img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            else:
                raise ValueError("Could not convert PDF to image")
        else:
            raise ValueError("Could not decode image (Not a valid Image or PDF)")
    
    return img


def preprocess_for_ocr(img: np.ndarray, grayscale: bool = True) -> np.ndarray:
    """
    Apply preprocessing to improve OCR accuracy.
    
    Args:
        img: OpenCV image (BGR format)
        grayscale: Whether to convert to grayscale
        
    Returns:
        Preprocessed image
    """
    if grayscale:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def resize_for_ocr(img: np.ndarray, max_width: int = 1800, max_height: int = 1800) -> np.ndarray:
    """
    Resize image if too large for faster OCR processing.
    
    Args:
        img: OpenCV image
        max_width: Maximum width in pixels (default 1800 for balanced speed/accuracy)
        max_height: Maximum height in pixels
        
    Returns:
        Resized image (or original if already small enough)
    """
    h, w = img.shape[:2]
    if w > max_width or h > max_height:
        scale = min(max_width / w, max_height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        logger.info(f"Resizing image from {w}x{h} to {new_w}x{new_h} for faster OCR")
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return img


def encode_for_api(img: np.ndarray, format: str = "jpeg", quality: int = 85) -> tuple:
    """
    Encode image for API transmission with compression.
    Uses JPEG for smaller file size and faster transmission.
    
    Args:
        img: OpenCV image (BGR format)
        format: "jpeg" or "png"
        quality: JPEG quality (1-100), higher = better quality but larger size
        
    Returns:
        Tuple of (encoded_bytes, mime_type)
    """
    if format == "jpeg":
        # Resize for API if too large
        img = resize_for_ocr(img, max_width=1600, max_height=1600)
        _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return buffer.tobytes(), "image/jpeg"
    else:
        _, buffer = cv2.imencode('.png', img)
        return buffer.tobytes(), "image/png"


def load_pdf_pages(file_bytes: bytes, dpi: int = 200, max_pages: int = 50) -> list:
    """
    Load all pages from a PDF file.
    
    Args:
        file_bytes: Raw bytes of the PDF
        dpi: DPI for rendering
        max_pages: Maximum number of pages to process
        
    Returns:
        List of OpenCV images (BGR format), one per page
    """
    if not file_bytes.startswith(b'%PDF'):
        raise ValueError("Not a valid PDF file")
    
    logger.info(f"Converting PDF to images with DPI {dpi}...")
    pil_images = convert_from_bytes(
        file_bytes, 
        dpi=dpi, 
        thread_count=4
    )
    
    # Limit pages
    if len(pil_images) > max_pages:
        logger.warning(f"PDF has {len(pil_images)} pages, limiting to {max_pages}")
        pil_images = pil_images[:max_pages]
    
    logger.info(f"Extracted {len(pil_images)} page(s) from PDF")
    
    # Convert to OpenCV format
    images = []
    for pil_image in pil_images:
        img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        images.append(img)
    
    return images


def is_pdf(file_bytes: bytes) -> bool:
    """Check if file bytes represent a PDF"""
    return file_bytes.startswith(b'%PDF')
