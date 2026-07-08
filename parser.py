import fitz  # PyMuPDF
from pathlib import Path
from config import MIN_TEXT_LENGTH_THRESHOLD
from logger import logger

def extract_pdf_text_native(pdf_path: Path) -> str:
    """
    Extracts native text from a PDF file using PyMuPDF.
    
    Args:
        pdf_path (Path): Path to the PDF file.
        
    Returns:
        str: Extracted text.
    """
    logger.info(f"Attempting native text extraction from: {pdf_path.name}")
    text_content = []
    
    try:
        # Open document
        with fitz.open(pdf_path) as doc:
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                text_content.append(page_text)
                
        full_text = "\n".join(text_content).strip()
        logger.info(f"Native extraction successful. Extracted {len(full_text)} characters.")
        return full_text
        
    except Exception as e:
        logger.error(f"Error during native PDF text extraction on {pdf_path.name}: {str(e)}")
        # Return empty string to trigger OCR fallback
        return ""

def extract_text(pdf_path: Path) -> str:
    """
    Main entry point for text extraction. Extracts text using native methods.
    If the extracted text is below the threshold, it triggers OCR fallback.
    
    Args:
        pdf_path (Path): Path to the PDF file.
        
    Returns:
        str: Extracted text (either native or OCR).
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        logger.error(f"PDF file does not exist: {pdf_path}")
        raise FileNotFoundError(f"File not found: {pdf_path}")
        
    # Step 1: Try native extraction
    extracted_text = extract_pdf_text_native(pdf_path)
    
    # Step 2: Check if text is sufficient
    if len(extracted_text) < MIN_TEXT_LENGTH_THRESHOLD:
        logger.warning(
            f"Native text length ({len(extracted_text)}) is below threshold "
            f"({MIN_TEXT_LENGTH_THRESHOLD}). Triggering OCR fallback..."
        )
        
        # Delayed import to avoid circular dependency
        from ocr import run_ocr_on_pdf
        
        try:
            extracted_text = run_ocr_on_pdf(pdf_path)
            logger.info("OCR text extraction completed successfully.")
        except Exception as e:
            logger.critical(f"OCR fallback failed on {pdf_path.name}: {str(e)}")
            # In case OCR fails completely, return whatever native text was found (even if empty/garbage)
            
    return extracted_text
