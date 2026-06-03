"""License expiry label widget for displaying remaining days."""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from datetime import datetime
from utils.security import security_manager


class LicenseExpiryLabel(QLabel):
    """Label to display license expiration countdown."""
    
    def __init__(self, parent=None):
        """Initialize license expiry label."""
        super().__init__(parent)
        self.setup_style()
        self.update_expiry_text()
        
        # Update every hour
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_expiry_text)
        self.timer.start(3600000)  # 1 hour in milliseconds
    
    def setup_style(self):
        """Setup label styling."""
        font = QFont()
        font.setPointSize(8)
        self.setFont(font)
        
        self.setAlignment(Qt.AlignRight | Qt.AlignBottom)
    
    def update_expiry_text(self):
        """Update the expiry text based on remaining days."""
        if not security_manager.license_valid:
            self.setText("No License")
            self.setStyleSheet("""
                QLabel {
                    color: #f44336;
                    background-color: transparent;
                    padding: 5px;
                }
            """)
            return
        
        if security_manager.license_expiry is None:
            # Master license or permanent license
            self.setText("License: Permanent")
            self.setStyleSheet("""
                QLabel {
                    color: #4CAF50;
                    background-color: transparent;
                    padding: 5px;
                }
            """)
            return
        
        # Calculate days remaining
        now = datetime.utcnow()
        days_remaining = (security_manager.license_expiry - now).days
        
        if days_remaining < 0:
            # Expired
            self.setText("License: EXPIRED")
            self.setStyleSheet("""
                QLabel {
                    color: #f44336;
                    background-color: transparent;
                    padding: 5px;
                    font-weight: bold;
                }
            """)
        elif days_remaining <= 7:
            # Expiring soon (red)
            self.setText(f"License: {days_remaining} days left")
            self.setStyleSheet("""
                QLabel {
                    color: #f44336;
                    background-color: transparent;
                    padding: 5px;
                    font-weight: bold;
                }
            """)
        elif days_remaining <= 30:
            # Warning (orange)
            self.setText(f"License: {days_remaining} days left")
            self.setStyleSheet("""
                QLabel {
                    color: #FF9800;
                    background-color: transparent;
                    padding: 5px;
                }
            """)
        else:
            # Good (green)
            self.setText(f"License: {days_remaining} days left")
            self.setStyleSheet("""
                QLabel {
                    color: #4CAF50;
                    background-color: transparent;
                    padding: 5px;
                }
            """)