"""License activation dialog with copyable Hardware ID."""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QMessageBox, QTextEdit,
                             QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from utils.security import security_manager


class LicenseDialog(QDialog):
    """Dialog for license activation with copyable Hardware ID."""
    
    def __init__(self, parent=None):
        """Initialize license dialog."""
        super().__init__(parent)
        self.setWindowTitle("License Activation")
        self.setMinimumWidth(600)
        self.setModal(True)
        
        self.validation_callback = None  # Will be set by main.py
        
        self._init_ui()
    
    def set_validation_callback(self, callback):
        """
        Set the callback function for license validation.
        
        Args:
            callback: Function that takes license_key and returns (success, message)
        """
        self.validation_callback = callback
    
    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("🔑 License Activation Required")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Info message
        info = QLabel(
            "This application requires a valid license to run.\n"
            "Please contact support with your Hardware ID to obtain a license key."
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #666666; margin: 10px 0px;")
        layout.addWidget(info)
        
        # Hardware ID Section
        hw_id_label = QLabel("Your Hardware ID:")
        hw_id_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(hw_id_label)
        
        # Copyable Hardware ID (using QLineEdit - read-only)
        self.hardware_id_field = QLineEdit()
        hardware_id = security_manager.get_hardware_id()
        self.hardware_id_field.setText(hardware_id)
        self.hardware_id_field.setReadOnly(True)
        self.hardware_id_field.setAlignment(Qt.AlignCenter)
        self.hardware_id_field.setStyleSheet("""
            QLineEdit {
                background-color: #f0f0f0;
                border: 2px solid #cccccc;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12pt;
                font-weight: bold;
                color: #333333;
            }
        """)
        # Select all text by default for easy copying
        self.hardware_id_field.selectAll()
        self.hardware_id_field.setFocus()
        layout.addWidget(self.hardware_id_field)
        
        # Copy button
        copy_button_layout = QHBoxLayout()
        copy_button_layout.addStretch()
        
        self.copy_button = QPushButton("📋 Copy Hardware ID")
        self.copy_button.setMinimumHeight(35)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.copy_button.clicked.connect(self._copy_hardware_id)
        copy_button_layout.addWidget(self.copy_button)
        
        copy_button_layout.addStretch()
        layout.addLayout(copy_button_layout)
        
        # Instructions
        instructions = QLabel(
            "📧 Send this Hardware ID to diego.rodriguez@sarens.com and/or gfs.support.tech@sarens.com\n"
            "You will receive a license key via email."
        )
        instructions.setWordWrap(True)
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setStyleSheet("""
            QLabel {
                background-color: #E3F2FD;
                border-left: 4px solid #2196F3;
                padding: 10px;
                margin: 10px 0px;
                border-radius: 3px;
            }
        """)
        layout.addWidget(instructions)
        
        # License Key Input Section
        license_label = QLabel("Enter License Key:")
        license_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        layout.addWidget(license_label)
        
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("XXXXX-XXXXX-XXXXX-XXXXXXXX")
        self.license_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cccccc;
                border-radius: 5px;
                padding: 10px;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        layout.addWidget(self.license_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.exit_button = QPushButton("Exit")
        self.exit_button.setMinimumSize(100, 40)
        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        self.exit_button.clicked.connect(self.reject)
        button_layout.addWidget(self.exit_button)
        
        button_layout.addStretch()
        
        self.activate_button = QPushButton("Activate License")
        self.activate_button.setMinimumSize(150, 40)
        self.activate_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.activate_button.clicked.connect(self._activate_license)
        button_layout.addWidget(self.activate_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _copy_hardware_id(self):
        """Copy Hardware ID to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.hardware_id_field.text())
        
        # Visual feedback
        original_text = self.copy_button.text()
        self.copy_button.setText("✓ Copied!")
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 10pt;
                font-weight: bold;
            }
        """)
        
        # Reset button after 2 seconds
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self._reset_copy_button(original_text))
    
    def _reset_copy_button(self, original_text):
        """Reset copy button to original state."""
        self.copy_button.setText(original_text)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
    
    def _activate_license(self):
        """Activate license with entered key."""
        license_key = self.license_input.text().strip()
        
        if not self.validation_callback:
            QMessageBox.critical(self, "Error", "Validation callback not set.")
            return
        
        # Call the validation callback from main.py
        success, message = self.validation_callback(license_key)
        
        if success:
            QMessageBox.information(
                self,
                "License Activated",
                message
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Activation Failed",
                message
            )


class LicenseInfoDialog(QDialog):
    """Dialog showing current license information."""
    
    def __init__(self, parent=None):
        """Initialize license info dialog."""
        super().__init__(parent)
        self.setWindowTitle("License Information")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("License Information")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Hardware ID
        hw_label = QLabel("Hardware ID:")
        hw_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(hw_label)
        
        self.hardware_id_field = QLineEdit()
        hardware_id = security_manager.get_hardware_id()
        self.hardware_id_field.setText(hardware_id)
        self.hardware_id_field.setReadOnly(True)
        self.hardware_id_field.setStyleSheet("""
            QLineEdit {
                background-color: #f0f0f0;
                border: 2px solid #cccccc;
                border-radius: 5px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.hardware_id_field)
        
        # Copy button
        copy_btn = QPushButton("📋 Copy Hardware ID")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(hardware_id))
        layout.addWidget(copy_btn)
        
        # License Status
        if security_manager.license_valid:
            status_text = "✅ License is VALID"
            status_color = "green"
            
            if security_manager.license_expiry:
                from datetime import datetime
                days_left = (security_manager.license_expiry - datetime.utcnow()).days
                expiry_text = f"Expires: {security_manager.license_expiry.strftime('%Y-%m-%d')} ({days_left} days left)"
            else:
                expiry_text = "Expires: PERMANENT"
        else:
            status_text = "❌ No Valid License"
            status_color = "red"
            expiry_text = ""
        
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold; font-size: 12pt; margin-top: 10px;")
        layout.addWidget(status_label)
        
        if expiry_text:
            expiry_label = QLabel(expiry_text)
            expiry_label.setStyleSheet("color: #666666;")
            layout.addWidget(expiry_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)