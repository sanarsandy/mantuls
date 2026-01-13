"""
PDF Converter Tools - Convert PDF to other formats
"""
import io
import logging
from pdf2docx import Converter
import tempfile
import os

logger = logging.getLogger(__name__)


def pdf_to_word(pdf_bytes: bytes) -> bytes:
    """
    Convert PDF to Word document (DOCX).
    
    Args:
        pdf_bytes: PDF file content as bytes
        
    Returns:
        DOCX file as bytes
    """
    # pdf2docx requires file paths, so we use temp files
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as pdf_temp:
        pdf_temp.write(pdf_bytes)
        pdf_path = pdf_temp.name
    
    docx_path = pdf_path.replace('.pdf', '.docx')
    
    try:
        # Convert PDF to DOCX
        cv = Converter(pdf_path)
        cv.convert(docx_path)
        cv.close()
        
        # Read the result
        with open(docx_path, 'rb') as f:
            result = f.read()
        
        return result
        
    except Exception as e:
        logger.error(f"PDF to Word conversion failed: {e}")
        raise ValueError(f"Failed to convert PDF to Word: {str(e)}")
        
    finally:
        # Cleanup temp files
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
        if os.path.exists(docx_path):
            os.unlink(docx_path)


def word_to_pdf(doc_bytes: bytes, filename: str = "document.docx") -> bytes:
    """
    Convert Word document (DOC/DOCX) to PDF using LibreOffice.
    
    Args:
        doc_bytes: Word document content as bytes
        filename: Original filename to determine format
        
    Returns:
        PDF file as bytes
    """
    import subprocess
    
    # Determine file extension
    ext = '.docx'
    if filename.lower().endswith('.doc'):
        ext = '.doc'
    
    # Create temp file with proper extension
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as doc_temp:
        doc_temp.write(doc_bytes)
        doc_path = doc_temp.name
    
    # Output directory for LibreOffice
    output_dir = tempfile.mkdtemp()
    
    try:
        # Convert using LibreOffice headless
        result = subprocess.run([
            'libreoffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', output_dir,
            doc_path
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            logger.error(f"LibreOffice conversion failed: {result.stderr}")
            raise ValueError(f"Failed to convert document: {result.stderr}")
        
        # Find the output PDF
        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
        
        if not os.path.exists(pdf_path):
            raise ValueError("PDF output not found after conversion")
        
        # Read the result
        with open(pdf_path, 'rb') as f:
            result = f.read()
        
        return result
        
    except subprocess.TimeoutExpired:
        raise ValueError("Conversion timed out. File may be too large or complex.")
    except Exception as e:
        logger.error(f"Word to PDF conversion failed: {e}")
        raise ValueError(f"Failed to convert document to PDF: {str(e)}")
        
    finally:
        # Cleanup temp files
        import shutil
        if os.path.exists(doc_path):
            os.unlink(doc_path)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir, ignore_errors=True)
