import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Any, Tuple
import uuid

from config import EXTRACTED_IMAGE_DIR, MAX_IMAGES
from logger import logger

def get_nearby_text(page: fitz.Page, bbox: fitz.Rect, vertical_offset: float = 120.0) -> str:
    """
    Extracts text surrounding the given bounding box on the PDF page.
    Looks slightly above and below the image box.
    
    Args:
        page (fitz.Page): The PyMuPDF page object.
        bbox (fitz.Rect): The bounding box of the image on the page.
        vertical_offset (float): The distance above/below the image to search for text.
        
    Returns:
        str: Cleaned text found near the image.
    """
    try:
        # Create a search rect that expands vertically
        search_rect = fitz.Rect(
            0,                     # Search full page width
            max(0, bbox.y0 - vertical_offset),
            page.rect.width,       # Search full page width
            min(page.rect.height, bbox.y1 + vertical_offset)
        )
        
        # Extract text in that region
        text = page.get_text("text", clip=search_rect)
        
        # Clean extra newlines and spaces
        cleaned_lines = [line.strip() for line in text.split("\n") if line.strip()]
        return " | ".join(cleaned_lines)
    except Exception as e:
        logger.warning(f"Failed to extract nearby text for image at {bbox}: {str(e)}")
        return ""

def extract_images_from_pdf(pdf_path: Path, source_name: str) -> List[Dict[str, Any]]:
    """
    Extracts embedded images from a PDF, saves them, and returns metadata including 
    bounding boxes and nearby text context.
    
    Args:
        pdf_path (Path): Path to the source PDF document.
        source_name (str): Label for the source, e.g. "Inspection Report" or "Thermal Report".
        
    Returns:
        List[Dict[str, Any]]: List of metadata dictionaries for each extracted image.
    """
    pdf_path = Path(pdf_path)
    logger.info(f"Extracting images from {pdf_path.name}...")
    extracted_images_metadata: List[Dict[str, Any]] = []
    
    # Ensure extraction directory exists
    EXTRACTED_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        with fitz.open(pdf_path) as doc:
            total_images_saved = 0
            
            for page_num in range(len(doc)):
                if total_images_saved >= MAX_IMAGES:
                    logger.warning(f"Reached limit of MAX_IMAGES ({MAX_IMAGES}). Stopping image extraction.")
                    break
                    
                page = doc[page_num]
                image_list = page.get_images(full=True)
                
                if not image_list:
                    continue
                    
                logger.info(f"Found {len(image_list)} image records on page {page_num + 1}.")
                
                # Deduplicate images on the same page based on xref
                processed_xrefs = set()
                
                for img_idx, img_info in enumerate(image_list):
                    if total_images_saved >= MAX_IMAGES:
                        break
                        
                    xref = img_info[0]
                    if xref in processed_xrefs:
                        continue
                        
                    processed_xrefs.add(xref)
                    
                    # Extract the image bytes
                    try:
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # Get drawing rectangle of the image on the page
                        rects = page.get_image_rects(xref)
                        if rects:
                            bbox = rects[0]
                        else:
                            # Fallback if no layout rect is associated
                            bbox = fitz.Rect(0, 0, page.rect.width, page.rect.height)
                            
                        # Generate unique filename for the image
                        unique_id = f"IMG_{uuid.uuid4().hex[:8]}"
                        image_filename = f"{unique_id}.{image_ext}"
                        save_path = EXTRACTED_IMAGE_DIR / image_filename
                        
                        # Save the image to the disk
                        with open(save_path, "wb") as img_file:
                            img_file.write(image_bytes)
                            
                        # Retrieve nearby text to act as context/captions
                        nearby_text = get_nearby_text(page, bbox)
                        
                        # Store metadata
                        metadata = {
                            "image_id": unique_id,
                            "page_number": page_num + 1,
                            "bbox": [bbox.x0, bbox.y0, bbox.x1, bbox.y1],
                            "nearby_text": nearby_text,
                            "path": str(save_path),
                            "filename": image_filename,
                            "source_document": source_name
                        }
                        
                        extracted_images_metadata.append(metadata)
                        total_images_saved += 1
                        logger.info(f"Successfully extracted and saved image {unique_id} ({image_filename}) from page {page_num + 1}.")
                        
                    except Exception as img_err:
                        logger.error(f"Failed to process image index {img_idx} (xref: {xref}) on page {page_num + 1}: {str(img_err)}")
                        continue
                        
        logger.info(f"Finished image extraction. Extracted {len(extracted_images_metadata)} images in total.")
        return extracted_images_metadata
        
    except Exception as e:
        logger.error(f"Error during image extraction workflow: {str(e)}")
        return []
