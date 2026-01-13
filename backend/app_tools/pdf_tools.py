"""
PDF Tools - Merge, Split, Compress operations
"""
import io
import logging
from typing import List, Optional
from PyPDF2 import PdfReader, PdfWriter

logger = logging.getLogger(__name__)


def merge_pdfs(pdf_files: List[bytes]) -> bytes:
    """
    Merge multiple PDF files into one.
    
    Args:
        pdf_files: List of PDF file contents as bytes
        
    Returns:
        Merged PDF as bytes
    """
    writer = PdfWriter()
    
    for pdf_bytes in pdf_files:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            writer.add_page(page)
    
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.read()


def split_pdf(pdf_bytes: bytes, mode: str = 'all', page_range: Optional[str] = None) -> bytes:
    """
    Split PDF into individual pages or extract range.
    
    Args:
        pdf_bytes: PDF file content
        mode: 'all' to split all pages, 'range' to extract specific pages
        page_range: Page range string like "1-3, 5, 7-10"
        
    Returns:
        ZIP file containing individual PDFs (mode='all') or single PDF (mode='range')
    """
    import zipfile
    
    reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)
    
    if mode == 'all':
        # Split into individual pages, return as ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, page in enumerate(reader.pages, 1):
                writer = PdfWriter()
                writer.add_page(page)
                
                page_buffer = io.BytesIO()
                writer.write(page_buffer)
                page_buffer.seek(0)
                
                zip_file.writestr(f'page_{i:03d}.pdf', page_buffer.read())
        
        zip_buffer.seek(0)
        return zip_buffer.read()
    
    else:
        # Extract specific pages
        pages_to_extract = _parse_page_range(page_range, total_pages)
        
        writer = PdfWriter()
        for page_num in pages_to_extract:
            writer.add_page(reader.pages[page_num - 1])  # 0-indexed
        
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        return output.read()


def _parse_page_range(range_str: str, max_pages: int) -> List[int]:
    """Parse page range string like '1-3, 5, 7-10' into list of page numbers."""
    pages = set()
    
    if not range_str:
        return list(range(1, max_pages + 1))
    
    for part in range_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-', 1)
            start = max(1, int(start.strip()))
            end = min(max_pages, int(end.strip()))
            pages.update(range(start, end + 1))
        else:
            page = int(part)
            if 1 <= page <= max_pages:
                pages.add(page)
    
    return sorted(pages)


def compress_pdf(pdf_bytes: bytes, level: str = 'medium') -> bytes:
    """
    Compress PDF file using pikepdf (QPDF).
    
    Args:
        pdf_bytes: PDF file content
        level: 'low', 'medium', or 'high' compression
        
    Returns:
        Compressed PDF as bytes
    """
    import pikepdf
    
    # Open PDF from bytes
    pdf = pikepdf.Pdf.open(io.BytesIO(pdf_bytes))
    
    # Configure save options based on level
    save_options = {
        'compress_streams': True
    }
    
    if level == 'high':
        # Aggressive structure optimization
        save_options['object_stream_mode'] = pikepdf.ObjectStreamMode.generate
    elif level == 'medium':
        save_options['object_stream_mode'] = pikepdf.ObjectStreamMode.generate
    else: # low
        pass
        
    # Remove metadata for better compression (optional, but good for privacy/size)
    if level in ['medium', 'high']:
        with pdf.open_metadata() as meta:
            try:
                # Clear basic metadata
                pass 
                # Note: modifying metadata in pikepdf requires careful handling, 
                # avoiding for now to prevent corruption, focus on structure.
            except:
                pass

    output = io.BytesIO()
    pdf.save(output, **save_options)
    output.seek(0)
    return output.read()


def add_watermark(
    pdf_bytes: bytes, 
    text: str, 
    position: str = "diagonal",
    opacity: float = 0.3,
    font_size: int = 60
) -> bytes:
    """
    Add text watermark to all pages of a PDF.
    
    Args:
        pdf_bytes: PDF file content
        text: Watermark text (e.g., "CONFIDENTIAL", "DRAFT")
        position: 'diagonal' or 'center'
        opacity: Transparency level (0.0-1.0)
        font_size: Size of watermark text
        
    Returns:
        PDF with watermark as bytes
    """
    import pikepdf
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.colors import Color
    
    # Open the source PDF
    source_pdf = pikepdf.Pdf.open(io.BytesIO(pdf_bytes))
    
    # Get page dimensions from first page (use as reference)
    first_page = source_pdf.pages[0]
    media_box = first_page.MediaBox
    page_width = float(media_box[2]) - float(media_box[0])
    page_height = float(media_box[3]) - float(media_box[1])
    
    # Create watermark overlay using reportlab
    watermark_buffer = io.BytesIO()
    c = canvas.Canvas(watermark_buffer, pagesize=(page_width, page_height))
    
    # Set transparency
    c.setFillColor(Color(0.5, 0.5, 0.5, alpha=opacity))
    c.setFont("Helvetica-Bold", font_size)
    
    # Calculate text width for positioning
    text_width = c.stringWidth(text, "Helvetica-Bold", font_size)
    
    if position == "diagonal":
        # Diagonal watermark across page
        c.saveState()
        c.translate(page_width / 2, page_height / 2)
        c.rotate(45)
        c.drawCentredString(0, 0, text)
        c.restoreState()
    else:  # center
        # Center watermark
        x = (page_width - text_width) / 2
        y = page_height / 2
        c.drawString(x, y, text)
    
    c.save()
    watermark_buffer.seek(0)
    
    # Open watermark as PDF
    watermark_pdf = pikepdf.Pdf.open(watermark_buffer)
    watermark_page = watermark_pdf.pages[0]
    
    # Apply watermark to each page
    for page in source_pdf.pages:
        # Get the watermark as a Form XObject
        watermark_xobj = page.add_overlay(watermark_page)
    
    # Save result
    output = io.BytesIO()
    source_pdf.save(output)
    output.seek(0)
    return output.read()
