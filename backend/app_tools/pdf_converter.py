"""
PDF Converter Tools - Convert PDF to other formats
"""
import io
import logging
from pdf2docx import Converter
import tempfile
import os

logger = logging.getLogger(__name__)



def pdf_to_excel(pdf_bytes: bytes) -> bytes:
    """
    Convert PDF to Excel (XLSX) by extracting tables and merging them into one sheet.
    
    Args:
        pdf_bytes: PDF file content as bytes
        
    Returns:
        XLSX file as bytes
    """
    import pdfplumber
    import pandas as pd
    
    all_rows = []
    
    # Robust settings for table extraction
    table_settings = {
        "vertical_strategy": "lines", 
        "horizontal_strategy": "lines",
        "intersection_y_tolerance": 10,
        "intersection_x_tolerance": 10,
        "snap_tolerance": 3,
    }
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            # Try to extract tables with settings
            tables = page.extract_tables(table_settings)
            
            # If "lines" strategy fails (no gridlines), fallback to "text" strategy
            if not tables:
                 tables = page.extract_tables()
                 
            for table in tables:
                if table:
                    all_rows.extend(table)
                    
    if not all_rows:
        raise ValueError("No tables found in the PDF")
        
    df = pd.DataFrame(all_rows)
    
    # Cleaning: Drop columns that are completely empty (all None/NaN)
    df.dropna(axis=1, how='all', inplace=True)
    
    # Cleaning: Drop rows that are completely empty
    df.dropna(axis=0, how='all', inplace=True)
    
    # Write to Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Converted Data", index=False, header=False)
            
    output.seek(0)
    return output.read()


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
