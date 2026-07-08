import os
from pathlib import Path
from typing import List

# ==========================================
# Directory Configuration
# ==========================================
# Base directory of the DDR_AI project
BASE_DIR: Path = Path(__file__).resolve().parent

# Application directories for outputs, logs, and temp files
OUTPUT_DIR: Path = BASE_DIR / "output"
LOG_DIR: Path = BASE_DIR / "logs"
EXTRACTED_IMAGE_DIR: Path = BASE_DIR / "extracted_images"
REPORT_DIR: Path = BASE_DIR / "reports"
ASSET_DIR: Path = BASE_DIR / "assets"
TEMPLATE_DIR: Path = BASE_DIR / "templates"
TESTS_DIR: Path = BASE_DIR / "tests"

# List of directories that need to be initialized at startup
REQUIRED_DIRECTORIES: List[Path] = [
    OUTPUT_DIR,
    LOG_DIR,
    EXTRACTED_IMAGE_DIR,
    REPORT_DIR,
    ASSET_DIR,
    TEMPLATE_DIR,
    TESTS_DIR
]

# ==========================================
# File Upload Settings
# ==========================================
# Supported file extensions for documents
SUPPORTED_FILE_TYPES: List[str] = ["pdf"]

# Maximum allowed size for uploaded PDFs (in MB)
MAX_UPLOAD_SIZE_MB: int = 50

# Maximum number of images to extract and process per report
MAX_IMAGES: int = 20

# Minimum text length below which OCR is triggered (in characters)
MIN_TEXT_LENGTH_THRESHOLD: int = 200

# ==========================================
# OCR Binary Configuration
# ==========================================
# Path to Tesseract-OCR executable (On Windows, this is often required if not in PATH)
TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

# Path to Poppler bin directory (required for pdf2image on Windows)
POPPLER_PATH: str = os.getenv("POPPLER_PATH", r"C:\Program Files\poppler\bin")

# LLM Provider Configuration (Gemini or DeepSeek)
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "DeepSeek")

# Google Gemini model to use for analysis
# Note: "gemini-1.5-flash" is recommended for high daily quota (1500 RPD vs 20 RPD for 2.5-flash)
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# DeepSeek / NVIDIA NIM settings
DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "qwen/qwen3.5-397b-a17b")
DEEPSEEK_API_BASE: str = os.getenv("DEEPSEEK_API_BASE", "https://integrate.api.nvidia.com/v1")

# LLM Hyperparameters
TEMPERATURE: float = 0.2
TOP_P: float = 0.95
MAX_OUTPUT_TOKENS: int = 65536

# ==========================================
# Risk and Confidence Thresholds
# ==========================================
# Confidence weighting for different evidence sources
WEIGHTS = {
    "visual_inspection": 0.4,
    "thermal_inspection": 0.4,
    "image_evidence": 0.2
}
