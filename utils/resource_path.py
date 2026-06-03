"""Resource path utilities for PyInstaller compatibility."""

import sys
import os


def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    
    When running in development, returns path relative to project root.
    When running as PyInstaller executable, returns path from temp _MEIPASS folder. 
    
    Args:
        relative_path: Relative path to resource (e.g., "config/configurations.json")
        
    Returns:
        Absolute path to resource with proper OS path separators
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Running in normal Python environment
        base_path = os.path.abspath(os. path.dirname(os.path. dirname(__file__)))
    
    # Normalize path separators for the current OS
    relative_path = relative_path.replace('/', os.sep).replace('\\', os.sep)
    
    result = os.path.join(base_path, relative_path)
    
    # Debug output (remove after testing)
    print(f"DEBUG resource_path: {relative_path} -> {result}")
    print(f"DEBUG exists: {os.path.exists(result)}")
    
    return result