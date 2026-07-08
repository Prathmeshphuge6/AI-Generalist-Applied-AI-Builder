import pytest
import fitz  # PyMuPDF
from PIL import Image as PILImage
import io
from pathlib import Path
import tempfile

from image_extractor import extract_images_from_pdf, get_nearby_text

@pytest.fixture
def pdf_with_image():
    """
    Creates a temporary PDF containing an embedded image and caption text.
    """
    temp_dir = tempfile.TemporaryDirectory()
    temp_path = Path(temp_dir.name) / "image_test_report.pdf"
    
    # 1. Create a simple red block PNG in memory
    img = PILImage.new("RGB", (100, 100), color="red")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()
    
    # 2. Compile a PDF and insert the image with adjacent text
    doc = fitz.open()
    page = doc.new_page()
    
    # Insert image at rect: x0=50, y0=50, x1=150, y1=150
    image_rect = fitz.Rect(50, 50, 150, 150)
    page.insert_image(image_rect, stream=img_bytes)
    
    # Insert a text caption below the image: y=165
    page.insert_text((50, 165), "Figure 1: Water damage on kitchen ceiling.")
    
    doc.save(temp_path)
    doc.close()
    
    yield temp_path
    temp_dir.cleanup()

def test_extract_images_metadata(pdf_with_image):
    """
    Verifies that the image extractor accurately extracts the image file,
    computes bounding box coordinates, and retrieves the surrounding text context.
    """
    metadata_list = extract_images_from_pdf(pdf_with_image, "Inspection Report")
    
    # Assert one image was extracted
    assert len(metadata_list) == 1
    
    meta = metadata_list[0]
    
    # Assert correct metadata layout keys
    assert meta["page_number"] == 1
    assert meta["source_document"] == "Inspection Report"
    assert "image_id" in meta
    assert "path" in meta
    
    # Assert coordinates match roughly where the image was inserted
    bbox = meta["bbox"]
    assert bbox[0] == pytest.approx(50.0, abs=2.0)
    assert bbox[1] == pytest.approx(50.0, abs=2.0)
    assert bbox[2] == pytest.approx(150.0, abs=2.0)
    assert bbox[3] == pytest.approx(150.0, abs=2.0)
    
    # Assert saved image exists on disk
    saved_file = Path(meta["path"])
    assert saved_file.exists()
    
    # Cleanup extracted test image file
    if saved_file.exists():
        saved_file.unlink()

def test_get_nearby_text(pdf_with_image):
    """
    Tests that get_nearby_text properly grabs page text within the vertical search range.
    """
    doc = fitz.open(pdf_with_image)
    page = doc[0]
    
    # Use image insertion coordinates
    image_rect = fitz.Rect(50, 50, 150, 150)
    
    text_near = get_nearby_text(page, image_rect, vertical_offset=30.0)
    
    assert "Water damage" in text_near
    assert "kitchen ceiling" in text_near
    doc.close()
