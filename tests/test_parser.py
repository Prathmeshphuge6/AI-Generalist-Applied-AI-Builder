import pytest
import fitz  # PyMuPDF
from pathlib import Path
import tempfile

from parser import extract_text, extract_pdf_text_native
from config import MIN_TEXT_LENGTH_THRESHOLD

@pytest.fixture
def temp_pdf_file():
    """
    Fixture that creates a temporary PDF file with sample text
    and returns its path. Cleans up after the test completes.
    """
    # Create temp directory
    temp_dir = tempfile.TemporaryDirectory()
    temp_path = Path(temp_dir.name) / "test_report.pdf"
    
    # Write a simple PDF using PyMuPDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Visual Inspection Report\nArea: Bathroom\nDefect: Minor surface cracks and paint peeling detected on the ceiling.")
    doc.save(temp_path)
    doc.close()
    
    yield temp_path
    
    # Cleanup temp workspace
    temp_dir.cleanup()

def test_extract_pdf_text_native(temp_pdf_file):
    """
    Verifies that PyMuPDF successfully extracts native text from a valid PDF document.
    """
    text = extract_pdf_text_native(temp_pdf_file)
    
    assert "Visual Inspection Report" in text
    assert "Bathroom" in text
    assert "paint peeling" in text

def test_extract_text_threshold_check(temp_pdf_file, monkeypatch):
    """
    Verifies that if the extracted text exceeds the threshold, OCR is NOT triggered.
    We test this by mocking the OCR call and asserting it is never executed.
    """
    # Set the threshold very low so our simple PDF easily exceeds it
    monkeypatch.setattr("parser.MIN_TEXT_LENGTH_THRESHOLD", 10)
    
    # Mock the OCR fallback call to assert it is never called
    ocr_called = False
    def mock_run_ocr(pdf_path):
        nonlocal ocr_called
        ocr_called = True
        return "OCR Text"
        
    monkeypatch.setattr("ocr.run_ocr_on_pdf", mock_run_ocr)
    
    extracted_text = extract_text(temp_pdf_file)
    
    assert ocr_called is False
    assert "Visual Inspection Report" in extracted_text
