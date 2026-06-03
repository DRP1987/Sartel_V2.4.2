"""Utility functions for GUI components."""

import os
import logging
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

# Configure logger for this module
logger = logging.getLogger(__name__)


def create_logo_widget(parent=None, max_width=150, max_height=50):
    """
    Create a QLabel widget displaying the company logo.
    
    Args:
        parent: Parent widget (optional)
        max_width: Maximum width for the logo in pixels (default: 150)
        max_height: Maximum height for the logo in pixels (default: 50)
        
    Returns:
        QLabel: Label widget containing the logo image, or None if logo not found
    """
    # Get the project root directory (parent of gui directory)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    logo_path = os.path.join(project_root, 'assets', 'logo.png')
    
    # Check if logo exists
    if not os.path.exists(logo_path):
        logger.warning(f"Logo file not found at {logo_path}")
        return None
    
    # Create label with logo
    logo_label = QLabel(parent)
    pixmap = QPixmap(logo_path)
    
    # Check if pixmap loaded successfully
    if pixmap.isNull():
        logger.warning(f"Failed to load logo from {logo_path}")
        return None
    
    # Scale pixmap if it exceeds maximum dimensions
    if pixmap.width() > max_width or pixmap.height() > max_height:
        pixmap = pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    
    # Set pixmap and configure label
    logo_label.setPixmap(pixmap)
    logo_label.setScaledContents(False)  # Keep original/scaled size
    logo_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
    
    return logo_label
