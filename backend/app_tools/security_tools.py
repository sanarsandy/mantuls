
import io
import pikepdf

def protect_pdf(pdf_bytes: bytes, password: str) -> bytes:
    """
    Encrypt PDF with a password.
    
    Args:
        pdf_bytes: Content of the PDF file
        password: Password to set
        
    Returns:
        Encrypted PDF bytes
    """
    try:
        # Open the PDF
        pdf = pikepdf.Pdf.open(io.BytesIO(pdf_bytes))
        
        # Define encryption settings (AES-256)
        encryption = pikepdf.Encryption(
            user=password, 
            owner=password, 
            R=6
        )
        
        # Save to bytes
        output = io.BytesIO()
        pdf.save(output, encryption=encryption)
        output.seek(0)
        return output.read()
    except Exception as e:
        raise ValueError(f"Failed to protect PDF: {str(e)}")

def unlock_pdf(pdf_bytes: bytes, password: str) -> bytes:
    """
    Remove password from a PDF.
    
    Args:
        pdf_bytes: Content of the locked PDF file
        password: Password to unlock it
        
    Returns:
        Decrypted PDF bytes (no password)
    """
    try:
        # Open the PDF with the password
        pdf = pikepdf.Pdf.open(io.BytesIO(pdf_bytes), password=password)
        
        # Save without encryption
        output = io.BytesIO()
        pdf.save(output)
        output.seek(0)
        return output.read()
    except pikepdf.PasswordError:
        raise ValueError("Invalid password provided.")
    except Exception as e:
        raise ValueError(f"Failed to unlock PDF: {str(e)}")
