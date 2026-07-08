import pytesseract
from pdf2image import convert_from_path
from pathlib import Path
from config import TESSERACT_CMD, POPPLER_PATH
from logger import logger

# Configure pytesseract binary path (critical on Windows if not in system PATH)
if Path(TESSERACT_CMD).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    logger.debug(f"Pytesseract binary configured to: {TESSERACT_CMD}")
else:
    logger.warning(
        f"Tesseract executable not found at specified path: '{TESSERACT_CMD}'. "
        "Will attempt to run using system PATH."
    )

def run_ocr_on_pdf(pdf_path: Path) -> str:
    """
    Converts PDF pages into images and runs pytesseract OCR on each page to extract text.
    
    Args:
        pdf_path (Path): Path to the PDF file to extract text from.
        
    Returns:
        str: Consolidated text extracted via OCR.
        
    Raises:
        RuntimeError: If Tesseract or Poppler is missing or fails.
    """
    pdf_path = Path(pdf_path)
    logger.info(f"Starting OCR processing for: {pdf_path.name}")
    
    # Verify file existence
    if not pdf_path.exists():
        logger.error(f"Cannot run OCR. File does not exist: {pdf_path}")
        raise FileNotFoundError(f"File not found: {pdf_path}")
        
    extracted_text = []
    
    try:
        # Step 1: Convert PDF to images using pdf2image
        # Specify poppler path if configured in config.py
        poppler_dir = POPPLER_PATH if POPPLER_PATH and Path(POPPLER_PATH).exists() else None
        
        logger.info(f"Converting PDF pages to images (Poppler Path override: {poppler_dir})...")
        images = convert_from_path(pdf_path, poppler_path=poppler_dir)
        logger.info(f"Successfully converted PDF into {len(images)} page images.")
        
        # Step 2: Loop through page images and apply Tesseract OCR
        for index, image in enumerate(images):
            page_num = index + 1
            logger.info(f"Processing OCR on page {page_num}/{len(images)}...")
            
            # Perform OCR on image
            page_text = pytesseract.image_to_string(image)
            extracted_text.append(f"--- OCR Page {page_num} ---\n{page_text}")
            
        full_ocr_text = "\n".join(extracted_text).strip()
        logger.info(f"OCR text extraction complete. Extracted {len(full_ocr_text)} characters.")
        return full_ocr_text
        
    except FileNotFoundError as fnf_err:
        error_msg = (
            "OCR Failure: 'poppler' utility (pdf2image dependency) is missing. "
            "Please install poppler and check POPPLER_PATH in config.py. "
            f"Details: {str(fnf_err)}"
        )
        logger.critical(error_msg)
        raise RuntimeError(error_msg) from fnf_err
        
    except pytesseract.TesseractNotFoundError as tess_err:
        error_msg = (
            "OCR Failure: Tesseract executable not found. "
            "Please install Tesseract-OCR and check TESSERACT_CMD in config.py. "
            f"Details: {str(tess_err)}"
        )
        logger.critical(error_msg)
        raise RuntimeError(error_msg) from tess_err
        
    except Exception as e:
        error_msg = f"OCR processing failed due to unexpected error: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
