"""Configuration selection screen for CAN bus monitoring application."""

import os
import sys
import platform
import subprocess
from functools import partial
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QListWidget, QListWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from config.config_loader import ConfigurationLoader
from config.app_config import APP_NAME
from gui.utils import create_logo_widget
from gui.widgets import ConnectionStatusWidget


class ConfigSelectionScreen(QWidget):
    """Screen for selecting monitoring configuration."""

    configuration_selected = pyqtSignal(dict)
    reconnect_requested = pyqtSignal()  # User wants to reconfigure connection

    def __init__(self, config_loader: ConfigurationLoader, parent=None):
        """
        Initialize configuration selection screen.

        Args:
            config_loader: Configuration loader instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_loader = config_loader
        self.configurations = []
        self.connection_status_widget = None

        self._init_ui()
        self._load_configurations()

    def _init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle(f"{APP_NAME} - Configuration Selection")
        self.setMinimumSize(500, 400)

        # Main layout
        layout = QVBoxLayout()

        # Top bar with and connection status
        top_bar = QHBoxLayout()
        
        # Logo in top left
        logo_widget = create_logo_widget(self)
        if logo_widget:
            top_bar.addWidget(logo_widget)
        
        top_bar.addStretch()
        
        # Connection status in top right
        self.connection_status_widget = ConnectionStatusWidget()
        top_bar.addWidget(self.connection_status_widget)
        
        layout.addLayout(top_bar)

        # Title
        title = QLabel("Select Monitoring Configuration")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            "Select a configuration from the list below and click 'Start monitoring'.\n"
            "Note: for checking LMB signal engine MUST BE RUNNING!"
        )
        instructions.setStyleSheet("font-size: 14px; font-weight: bold; margin: 20px;")
        instructions.setWordWrap(True)
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)

        # Configuration list
        list_label = QLabel("Available Configurations:")
        list_label.setStyleSheet("margin-top: 20px; font-weight: bold;")
        layout.addWidget(list_label)

        self.config_list = QListWidget()
        self.config_list.itemDoubleClicked.connect(self._load_selected_config)
        layout.addWidget(self.config_list)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("margin: 10px; color: red;")
        layout.addWidget(self.status_label)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Configure Connection button
        self.configure_connection_btn = QPushButton("To BaudRate configuration")
        self.configure_connection_btn.setMinimumSize(180, 40)
        self.configure_connection_btn.clicked.connect(self._on_reconnect_requested)
        button_layout.addWidget(self.configure_connection_btn)

        # Load button
        self.load_button = QPushButton("Start Monitoring")
        self.load_button.setMinimumSize(150, 40)
        self.load_button.clicked.connect(self._load_selected_config)
        button_layout.addWidget(self.load_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_configurations(self):
        """Load configurations from file."""
        try:
            self.configurations = self.config_loader.load_configurations()

            if not self.configurations:
                self.status_label.setText("No configurations found in file.")
                self.load_button.setEnabled(False)
                return

            # Populate list
            for idx, config in enumerate(self.configurations):
                config_name = config.get('name', 'Unnamed')
                signal_count = len(config.get('signals', []))
                
                # Create list item
                item = QListWidgetItem(self.config_list)
                
                # Create widget for this item
                item_widget = QWidget()
                item_layout = QHBoxLayout(item_widget)
                item_layout.setContentsMargins(5, 2, 5, 2)
                
                # Configuration name label
                name_label = QLabel(f"{config_name} ({signal_count} signals)")
                item_layout.addWidget(name_label)
                item_layout.addStretch()
                
                # Add info button if PDF documentation exists
                info_pdf = config.get('info_pdf')
                if info_pdf:
                    info_button = QPushButton("ℹ️")
                    info_button.setFixedSize(30, 30)
                    info_button.setToolTip("View documentation")
                    info_button.setStyleSheet("""
                        QPushButton {
                            font-size: 16px;
                            border: 1px solid #ccc;
                            border-radius: 15px;
                            background-color: #f0f0f0;
                        }
                        QPushButton:hover {
                            background-color: #e0e0e0;
                        }
                    """)
                    # Connect to PDF opening function using partial to avoid lambda issues
                    info_button.clicked.connect(partial(self._open_pdf_documentation, idx))
                    item_layout.addWidget(info_button)
                
                item_widget.setLayout(item_layout)
                
                # Set the widget for the item
                item.setSizeHint(item_widget.sizeHint())
                self.config_list.addItem(item)
                self.config_list.setItemWidget(item, item_widget)

            # Select first item by default
            if self.config_list.count() > 0:
                self.config_list.setCurrentRow(0)

        except FileNotFoundError:
            self.status_label.setText("Configuration file not found!")
            self.load_button.setEnabled(False)
            QMessageBox.critical(
                self,
                "Error",
                "Configuration file 'configurations.json' not found.\n"
                "Please ensure the file exists in the application directory."
            )
        except Exception as e:
            self.status_label.setText(f"Error loading configurations: {str(e)}")
            self.load_button.setEnabled(False)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load configurations:\n{str(e)}"
            )

    def _open_pdf_documentation(self, config_index):
        """Open PDF documentation directly (no encryption)."""
        if config_index < 0 or config_index >= len(self.configurations):
            return
    
        config = self.configurations[config_index]
        info_pdf = config.get('info_pdf')
    
        if not info_pdf:
            QMessageBox.warning(self, "No Documentation", 
                           "No documentation is available for this configuration.")
            return
    
        # Remove .enc extension if present (backwards compatibility)
        if info_pdf.lower().endswith('.enc'):
            info_pdf = info_pdf[:-4]  # Remove .enc extension
        
        # Ensure it's a PDF
        if not info_pdf.lower().endswith('.pdf'):
            info_pdf = info_pdf + '.pdf'
    
        from utils.resource_path import resource_path
    
        try:
            # Get PDF path (no encryption)
            pdf_path = resource_path(info_pdf)
        
            print(f"DEBUG: Looking for PDF: {pdf_path}")
        
            if not os.path.exists(pdf_path):
                QMessageBox.critical(self, "Documentation Not Found",
                                f"Documentation file not found:\n{info_pdf}\n\n"
                                f"Expected at: {pdf_path}\n\n"
                                f"Please ensure the PDF file exists in the correct location.")
                return
        
            print(f"DEBUG: Opening PDF: {pdf_path}")
        
            # Open PDF with system default viewer
            system = platform.system()
            if system == 'Windows':
                os.startfile(pdf_path)
            elif system == 'Darwin':  # macOS
                subprocess.run(['open', pdf_path], check=True)
            else:  # Linux
                subprocess.run(['xdg-open', pdf_path], check=True)
        
            print(f"DEBUG: PDF opened successfully")
        
        except FileNotFoundError:
            QMessageBox.critical(self, "File Not Found",
                            f"The PDF file could not be found:\n{info_pdf}")
        except Exception as e:
            QMessageBox.critical(self, "Error Opening Documentation",
                            f"Failed to open documentation:\n{str(e)}\n\n"
                            f"Please ensure you have a PDF viewer installed.")
            import traceback
            traceback.print_exc()

    def _load_selected_config(self):
        """Load selected configuration and emit signal."""
        current_item = self.config_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a configuration from the list."
            )
            return

        current_row = self.config_list.currentRow()
        if current_row >= 0 and current_row < len(self.configurations):
            selected_config = self.configurations[current_row]

            # Validate configuration
            if not self.config_loader.validate_configuration(selected_config):
                QMessageBox.critical(
                    self,
                    "Invalid Configuration",
                    "The selected configuration is invalid. Please check the JSON file."
                )
                return

            self.configuration_selected.emit(selected_config)

    def set_connection_status(self, connected: bool):
        """
        Update connection status indicator.

        Args:
            connected: True if connected, False if offline
        """
        if self.connection_status_widget:
            self.connection_status_widget.set_connected(connected)

    def _on_reconnect_requested(self):
        """Handle reconnect button click."""
        self.reconnect_requested.emit()