"""Splash screen for application startup."""

import os
from PyQt5.QtWidgets import QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor
from config.app_config import APP_NAME, APP_VERSION, LOGO_PATH
from utils.resource_path import resource_path  # ← ADD THIS


class SplashScreen(QSplashScreen):
    """Splash screen displayed during application startup."""

    def __init__(self):
        """Initialize splash screen with logo and application info."""
        # Use resource_path for PyInstaller compatibility
        logo_path = resource_path(LOGO_PATH)  # ← CHANGE THIS
        
        # Load logo image or create fallback
        if os.path. exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            # Scale logo if it's too small
            if logo_pixmap. width() < 300 or logo_pixmap.height() < 150:
                logo_pixmap = logo_pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            # Create a default pixmap with text if logo is missing
            print(f"Warning: Logo not found at {logo_path}")  # ← ADD THIS for debugging
            logo_pixmap = QPixmap(400, 300)
            logo_pixmap. fill(Qt.white)
        
        # Store logo dimensions
        self.logo_width = logo_pixmap.width()
        self.logo_height = logo_pixmap.height()
        
        # Add space below logo for text (100 pixels)
        text_space = 100
        total_width = self.logo_width
        total_height = self.logo_height + text_space
        
        # Create combined pixmap (logo + text area)
        self.base_pixmap = QPixmap(total_width, total_height)
        self.base_pixmap.fill(Qt.white)
        
        # Draw logo at the top
        painter = QPainter(self.base_pixmap)
        painter.drawPixmap(0, 0, logo_pixmap)
        painter.end()
        
        # Store dimensions for animation
        self.total_width = total_width
        self.total_height = total_height
        
        # Initialize with base pixmap
        super().__init__(self.base_pixmap. copy(), Qt.WindowStaysOnTopHint)
        
        # Set window flags for frameless, centered splash
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint |
            Qt.SplashScreen
        )
        
        # Animation state for dots
        self.dot_count = 0
        
        # Draw initial text
        self._update_text()
        
        # Start animation timer for loading dots
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_text)
        self.timer.start(500)  # Update every 500ms
        
    def _update_text(self):
        """Update text below logo with animated dots."""
        # Create new pixmap from base
        pixmap = self.base_pixmap.copy()
        
        # Draw text below logo
        painter = QPainter(pixmap)
        painter.setPen(QColor(0, 0, 0))  # Black text
        
        # App name (bold, larger)
        font_name = QFont()
        font_name.setPointSize(14)
        font_name.setBold(True)
        painter.setFont(font_name)
        painter.drawText(
            0, self.logo_height + 20, self.total_width, 25, 
            Qt.AlignCenter, 
            APP_NAME
        )
        
        # Version (normal, medium)
        font_version = QFont()
        font_version. setPointSize(11)
        painter.setFont(font_version)
        painter.drawText(
            0, self.logo_height + 50, self.total_width, 20, 
            Qt.AlignCenter, 
            f"Version {APP_VERSION}"
        )
        
        # Loading with animated dots
        dots = "." * self.dot_count
        loading_text = f"Loading{dots}"
        painter.drawText(
            0, self.logo_height + 75, self.total_width, 20, 
            Qt.AlignCenter, 
            loading_text
        )
        
        painter.end()
        
        # Update splash screen
        self.setPixmap(pixmap)
        
        # Cycle dots: 0 → 1 → 2 → 3 → 0
        self.dot_count = (self.dot_count + 1) % 4
    
    def closeEvent(self, event):
        """Stop timer when splash closes."""
        if hasattr(self, 'timer'):
            self.timer.stop()
        super().closeEvent(event)