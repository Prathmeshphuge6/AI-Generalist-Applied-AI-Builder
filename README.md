# AI-Powered Detailed Diagnostic Report (DDR) Generator

An enterprise-ready building diagnostics intelligence system that parses visual and thermal building inspection reports, extracts contextualized layout diagrams, conducts a 9-stage analysis pipeline using Google Gemini, and generates client-ready Detailed Diagnostic Reports (DDR) in print-ready PDF and editable Word formats.

## 🚀 Key Features

- **Automated Text Extraction & OCR Fallback**: Automatically extracts document text natives using PyMuPDF. If native text is insufficient or missing, falls back to OCR via Tesseract.
- **Context-Aware Image Extraction**: Automatically extracts images from reports, reads surrounding context, computes page bounding boxes, and links them directly to observations.
- **9-Stage Diagnostics Pipeline**:
  1. Observation Extraction
  2. Spatial Area Grouping
  3. Duplicate Resolution & Consolidation
  4. Visual-Thermal Conflict Detection
  5. Probable Root Cause Ingress
  6. Severity & Mathematical Confidence Assessor
  7. Time-Prioritized Recommendation Matrix
  8. Executive Summary & Overall Risk Computations
  9. Final Pydantic Schema Compilation & Validation
- **Double Report Export**: Downloads reports as styled Word DOCX documents (`python-docx`) and structured PDF prints (`ReportLab`) with embedded page headers and figures.
- **Premium Dark Dashboard**: Features drag-and-drop file upload, real-time stage progress logging, image galleries, and metric indicators.

---

## 🛠 Directory Structure

```
DDR_AI/
├── app.py                # Main Streamlit UI dashboard
├── config.py             # Global constants and LLM configuration
├── logger.py             # Console and file-based rotating logger
├── models.py             # Strongly typed Pydantic models for validation
├── parser.py             # PDF text parser module
├── ocr.py                # Pytesseract OCR extraction logic
├── image_extractor.py    # Coordinate and text-aware image extraction
├── prompt.py             # System directives and templates for the 9 stages
├── analyzer.py           # Core Gemini multi-stage pipeline orchestration
├── report_generator.py   # DOCX and PDF compilers
├── utils.py              # Application helpers (workspace reset, format tools)
├── requirements.txt      # Python dependencies
├── .env                  # Environment keys and overrides
├── tests/                # Test suite
│   ├── test_parser.py
│   ├── test_image_extractor.py
│   ├── test_analyzer.py
│   └── test_report_generator.py
└── README.md             # Setup and deployment manual
```

---

## 💻 Installation

### 1. Prerequisites (System Binaries)
The OCR fallback and image conversion engine require external system binaries.

#### Windows Setup:
1. **Tesseract OCR**:
   - Download and run the installer from: [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
   - Default install path: `C:\Program Files\Tesseract-OCR\tesseract.exe`.
2. **Poppler**:
   - Download binary packaging from: [Poppler for Windows](http://blog.alivate.com.au/poppler-windows/) or [GitHub releases](https://github.com/oschwartz10612/poppler-windows/releases)
   - Extract and locate the `bin/` directory (e.g., `C:\Program Files\poppler\bin`).
   - Add this path to your Windows system Environment Variables `PATH`.

*Note: If installed in custom directories, update `TESSERACT_CMD` and `POPPLER_PATH` in `.env` or `config.py`.*

### 2. Python Environment Setup
1. Clone or copy this repository to your target directory.
2. Initialize virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

### 3. API Keys Configuration
Create a `.env` file in the root folder (or rename the provided `.env` template):
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

---

## 🏃 Running the Application

Launch the Streamlit dashboard:
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser. Drag and drop your inspection PDFs, and generate reports!

---

## 🧪 Testing

To run automated checks:
```bash
pytest tests/
```
