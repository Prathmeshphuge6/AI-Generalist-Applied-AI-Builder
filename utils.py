import shutil
from pathlib import Path
from typing import Union
from config import REQUIRED_DIRECTORIES, LOG_DIR, EXTRACTED_IMAGE_DIR, OUTPUT_DIR, REPORT_DIR
from logger import logger

def initialize_workspace() -> None:
    """
    Initializes all necessary directories required by the application
    at startup. Ensures that folders for logs, output files, images, 
    and reports exist.
    """
    logger.info("Initializing DDR AI application workspace...")
    for directory in REQUIRED_DIRECTORIES:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory verified/created: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {str(e)}")
            raise OSError(f"Could not initialize application directory: {directory}") from e
    logger.info("Workspace initialization complete.")

def reset_project() -> None:
    """
    Cleans up the workspace by clearing all generated outputs, reports, 
    and extracted images. Re-initializes empty directories afterwards.
    """
    logger.warning("Reset project requested. Clearing all output and temporary folders...")
    
    folders_to_clear = [OUTPUT_DIR, EXTRACTED_IMAGE_DIR, REPORT_DIR]
    
    for folder in folders_to_clear:
        if folder.exists():
            try:
                # Remove entire directory structure
                shutil.rmtree(folder)
                logger.info(f"Successfully removed directory: {folder}")
            except Exception as e:
                logger.error(f"Error removing directory {folder}: {str(e)}")
                
    # Recreate the deleted directories
    initialize_workspace()

def format_file_size(size_bytes: int) -> str:
    """
    Formats bytes into human-readable file sizes (e.g., KB, MB).
    
    Args:
        size_bytes (int): Size in bytes.
        
    Returns:
        str: Formatted file size string.
    """
    for unit in ['Bytes', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def get_unique_filename(directory: Union[str, Path], filename: str) -> Path:
    """
    Generates a unique file path within a directory to prevent overwriting existing files.
    If a file with the same name exists, it appends a counter (e.g., file_1.pdf).
    
    Args:
        directory (Union[str, Path]): Target directory.
        filename (str): The initial filename.
        
    Returns:
        Path: Unique target Path.
    """
    dir_path = Path(directory)
    file_path = dir_path / filename
    if not file_path.exists():
        return file_path
        
    stem = file_path.stem
    suffix = file_path.suffix
    counter = 1
    
    while True:
        new_filename = f"{stem}_{counter}{suffix}"
        new_path = dir_path / new_filename
        if not new_path.exists():
            return new_path
        counter += 1

def update_env_key(key_name: str, key_val: str) -> None:
    """
    Updates or inserts an environment key-value pair in the local .env file.
    """
    env_path = Path("C:/Users/Prathamesh/.gemini/antigravity/scratch/DDR_AI/.env")
    if not env_path.exists():
        env_path.touch()
        
    try:
        content = env_path.read_text(encoding="utf-8")
        lines = content.splitlines()
    except Exception:
        lines = []
        
    key_found = False
    for idx, line in enumerate(lines):
        if line.strip().startswith(f"{key_name}="):
            lines[idx] = f"{key_name}={key_val}"
            key_found = True
            break
            
    if not key_found:
        lines.append(f"{key_name}={key_val}")
        
    try:
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        logger.info(f"Successfully saved {key_name} to .env file.")
    except Exception as e:
        logger.error(f"Failed to write to .env file: {str(e)}")
