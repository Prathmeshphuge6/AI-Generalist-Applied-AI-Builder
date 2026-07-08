import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path

# Import log directory settings from our configuration module
from config import LOG_DIR

def setup_logger(name: str = "DDR_AI") -> logging.Logger:
    """
    Configures and returns a logger instance that outputs to both the console
    and a rotating log file under the logs/ directory.
    
    Args:
        name (str): The name of the logger instance.
        
    Returns:
        logging.Logger: The configured Logger object.
    """
    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Establish a log file name based on the current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file_path = LOG_DIR / f"ddr_ai_{current_date}.log"
    
    # Create the logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers to prevent duplicate logging
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # Create formats for logs
    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 1. Console Handler (outputs INFO and higher messages)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # 2. Rotating File Handler (outputs DEBUG and higher, max 5MB per file, keeps 5 backups)
    try:
        file_handler = RotatingFileHandler(
            filename=str(log_file_path),
            mode='a',
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    except Exception as e:
        # Fallback in case of permission issues or file locks
        print(f"Warning: Failed to initialize file logging handler: {str(e)}")
        
    return logger

# Single globally shared logger instance for the application
logger: logging.Logger = setup_logger()
