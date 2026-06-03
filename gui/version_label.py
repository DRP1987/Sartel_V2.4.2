"""Version label widget for displaying app version."""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from config.app_config import APP_VERSION


class VersionLabel(QLabel):
    """Label to display application version."""
    
    def __init__(self, parent=None):
        """Initialize version label."""
        super().__init__(parent)
        self.setText(f"v{APP_VERSION}")
        self.setup_style()
    
    def setup_style(self):
        """Setup label styling."""
        # Set font
        font = QFont()
        font.setPointSize(8)
        self.setFont(font)
        
        # Set style
        self.setStyleSheet("""
            QLabel {
                color: #888888;
                background-color: transparent;
                padding: 5px;
            }
        """)
        
        # Set alignment
        self.setAlignment(Qt.AlignLeft | Qt.AlignBottom)