"""Baud rate detection screen for CAN bus monitoring application."""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QMessageBox, QProgressBar, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from canbus.pcan_interface import PCANInterface
from gui.utils import create_logo_widget
from gui.version_label import VersionLabel
from config.app_config import APP_NAME
from gui.license_expiry_label import LicenseExpiryLabel


class BaudRateDetectionThread(QThread):
    """Thread for detecting baud rate without blocking GUI."""

    baudrate_detected = pyqtSignal(int, str)
    detection_failed = pyqtSignal()
    progress_update = pyqtSignal(int)

    def __init__(self, pcan_interface: PCANInterface, channel: str = 'PCAN_USBBUS1'):
        """
        Initialize detection thread.

        Args:
            pcan_interface: PCAN interface instance
            channel: PCAN channel name
        """
        super().__init__()
        self.pcan_interface = pcan_interface
        self.channel = channel

    def run(self):
        """Run baud rate detection."""
        result = self.pcan_interface.detect_baudrate(
            self.channel,
            callback=self.progress_update.emit
        )

        if result:
            baudrate, can_type = result
            self.baudrate_detected.emit(baudrate, can_type)
        else:
            self.detection_failed.emit()


class BaudRateScreen(QWidget):
    """Screen for automatic baud rate detection."""

    baudrate_confirmed = pyqtSignal(int, str)  # baudrate, channel
    continue_offline = pyqtSignal()  # User chose to continue without connection

    def __init__(self, pcan_interface: PCANInterface, parent=None):
        """
        Initialize baud rate detection screen.

        Args:
            pcan_interface: PCAN interface instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.pcan_interface = pcan_interface
        self.detected_baudrate = None
        self.detected_can_type = None
        self.detection_thread = None
        self.available_channels = []
        self.selected_channel = None

        self._init_ui()
        # Perform initial channel scan
        self._refresh_channels()

    def _init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle(f"{APP_NAME} - Baud Rate Detection")
        self.setMinimumSize(400, 300)

        # Main layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Logo in top right corner
        logo_widget = create_logo_widget(self)
        if logo_widget:
            logo_layout = QHBoxLayout()
            logo_layout.addStretch()
            logo_layout.addWidget(logo_widget)
            layout.addLayout(logo_layout)

        # Title
        title = QLabel("CAN Bus Baud Rate Detection")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Channel selection with refresh button
        channel_layout = QHBoxLayout()
        channel_layout.addStretch()
        channel_label = QLabel("PCAN Channel:")
        channel_layout.addWidget(channel_label)
        

        self.channel_combo = QComboBox()
        self.channel_combo.setMinimumWidth(150)
        self.channel_combo.currentIndexChanged.connect(self._on_channel_selected)
        channel_layout.addWidget(self.channel_combo)
        
        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.setMinimumWidth(60)
        self.refresh_button.clicked.connect(self._refresh_channels)
        channel_layout.addWidget(self.refresh_button)

        channel_layout.addStretch()
        
        layout.addLayout(channel_layout)
        
        # Channel status label
        self.channel_status_label = QLabel("")
        self.channel_status_label.setAlignment(Qt.AlignCenter)
        self.channel_status_label.setStyleSheet("margin: 5px; font-size: 11px; color: gray;")
        layout.addWidget(self.channel_status_label)

        # Instructions
        instructions = QLabel(
            "Click the button below to automatically detect the CAN bus baud rate.\n"
            "Make sure Ignition is ON and Engine is NOT running\n"
            "This process will try common baud rates: 125k, 250k, 500k, 1000k."
        )
        instructions.setWordWrap(True)
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("margin: 10px; font-size: 12px;")
        layout.addWidget(self.status_label)

       # Progress bar container (FIXED - truly centered)
        progress_container = QHBoxLayout()
        progress_container.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setFixedWidth(700)
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #cccccc;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        progress_container.addWidget(self.progress_bar)
        progress_container.addStretch()

        layout.addLayout(progress_container)

        # Detected baud rate label
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(self.result_label)

        # CAN bus type label
        self.can_type_label = QLabel("")
        self.can_type_label.setAlignment(Qt.AlignCenter)
        self.can_type_label.setStyleSheet("font-size: 13px; font-weight: bold; margin: 5px;")
        layout.addWidget(self.can_type_label)

        layout.addStretch()

        # Button layout (UPDATED WITH OFFLINE MODE)
        button_layout = QHBoxLayout()

        # Offline Mode button (NEW)
        self.offline_button = QPushButton("📴 Offline Mode")
        self.offline_button.setMinimumSize(150, 40)
        self.offline_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        self.offline_button.clicked.connect(self._on_offline_mode)
        button_layout.addWidget(self.offline_button)

        # Detect button
        self.detect_button = QPushButton("🔍 Detect Baud Rate")
        self.detect_button.setMinimumSize(150, 40)
        self.detect_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.detect_button.clicked.connect(self._start_detection)
        button_layout.addWidget(self.detect_button)

        # Confirm button
        self.confirm_button = QPushButton("✓ Confirm & Continue")
        self.confirm_button.setMinimumSize(150, 40)
        self.confirm_button.setEnabled(False)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.confirm_button.clicked.connect(self._confirm_baudrate)
        button_layout.addWidget(self.confirm_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _on_offline_mode(self):
        """Handle offline mode button click (NEW METHOD)."""
        # Show warning dialog
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Offline Mode")
        msg.setText("⚠️  No PCAN Device Detected")
        msg.setInformativeText(
            "You are about to enter Offline Mode.\n\n"
            "In Offline Mode, you will NOT be able to:\n"
            "• Connect to CAN bus\n"
            "• Monitor real-time CAN messages\n"
            "• Detect baud rates automatically\n\n"
            "You CAN still:\n"
            "✓ View saved configurations\n"
            "✓ Read documentation\n"
            "✓ Review settings\n\n"
            "To use full functionality:\n"
            "1. Connect a PCAN-USB device\n"
            "2. Install PCAN drivers from www.peak-system.com or\n"
               "request drives to GFS support SARENS team\n"
            "3. Click 'Refresh' or restart the application\n\n"
            "Do you want to continue in Offline Mode?"
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        
        # Style the message box
        #msg.setStyleSheet("""
        #    QMessageBox {
        #        background-color: white;
        #    }
        #    QLabel {
        #        color: #333333;
        #        font-size: 10pt;
        #        min-width: 400px;
        #    }
        #    QPushButton {
        #        min-width: 80px;
        #        min-height: 30px;
        #        font-size: 10pt;
        #    }
        #""")
        msg.setFixedSize(600,400)

        result = msg.exec_()
        
        if result == QMessageBox.Yes:
            # User confirmed - emit signal to continue offline
            self.continue_offline.emit()

    def _start_detection(self):
        """Start baud rate detection process."""
        if not self.selected_channel:
            QMessageBox.warning(
                self,
                "No Channel Selected",
                "Please select a PCAN channel before starting detection."
            )
            return

        self.detect_button.setEnabled(False)
        self.confirm_button.setEnabled(False)
        self.result_label.setText("")
        self.can_type_label.setText("")
        self.status_label.setText("Detecting baud rate...")
        self.progress_bar.setVisible(True)

        # Create and start detection thread with selected channel
        self.detection_thread = BaudRateDetectionThread(
            self.pcan_interface, 
            self.selected_channel
        )
        self.detection_thread.baudrate_detected.connect(self._on_detection_success)
        self.detection_thread.detection_failed.connect(self._on_detection_failed)
        self.detection_thread.progress_update.connect(self._on_progress_update)
        self.detection_thread.finished.connect(self._on_detection_finished)
        self.detection_thread.start()

    def _on_progress_update(self, baudrate: int):
        """
        Handle progress update.

        Args:
            baudrate: Currently testing baud rate
        """
        self.status_label.setText(f"Testing baud rate: {baudrate} bps...")

    def _on_detection_success(self, baudrate: int, can_type: str):
        """
        Handle successful detection.

        Args:
            baudrate: Detected baud rate
            can_type: Detected CAN bus type string
        """
        self.detected_baudrate = baudrate
        self.detected_can_type = can_type
        self.result_label.setText(f"Detected Baud Rate: {baudrate} bps")
        self.result_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; margin: 10px; color: green;"
        )
        # Set CAN type label color based on type
        if "Powertrain" in can_type:
            color = "#FF6600"  # Orange for Powertrain
        else:
            color = "#2196F3"  # Blue for Control
        self.can_type_label.setText(f"🔌 {can_type}")
        self.can_type_label.setStyleSheet(
            f"font-size: 22px; font-weight: bold; margin: 5px; color: {color};"
        )
        self.status_label.setText("Detection successful!")
        self.confirm_button.setEnabled(True)

    def _on_detection_failed(self):
        """Handle failed detection."""
        self.result_label.setText("Detection Failed")
        self.result_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; margin: 10px; color: red;"
        )
        self.can_type_label.setText("")
        self.status_label.setText("No CAN bus activity detected. Please check your connection.")

        # Create custom message box with two buttons
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Baudrate Detection Failed")
        msg_box.setText("Could not detect CAN bus baudrate.")
        msg_box.setInformativeText(
            "Possible solutions:\n"
            "• Check CAN cable connection\n"
            "• Make sure CanH and CanL are not inverted!\n"
            "• Make sure Ignition is ON and engine Not running!\n"
            "• Verify CAN bus has traffic\n"
            "• Check PCAN device\n\n"
            "You can try again or continue without a live connection - Offline Mode."
        )
        
        # Add custom buttons
        try_again_btn = msg_box.addButton("Try Again", QMessageBox.AcceptRole)
        continue_offline_btn = msg_box.addButton("Continue Offline", QMessageBox.RejectRole)
        
        # Show dialog and get result
        msg_box.exec_()
        
        # Handle user's choice
        if msg_box.clickedButton() == try_again_btn:
            # User wants to try again - stay on this screen
            pass
        elif msg_box.clickedButton() == continue_offline_btn:
            # User wants to continue without connection
            self.continue_offline.emit()

    def _on_detection_finished(self):
        """Handle detection thread finished."""
        self.progress_bar.setVisible(False)
        # Only enable button if a valid channel is selected
        self.detect_button.setEnabled(bool(self.selected_channel))

    def _confirm_baudrate(self):
        """Confirm detected baud rate and proceed."""
        if self.detected_baudrate and self.selected_channel:
            self.baudrate_confirmed.emit(self.detected_baudrate, self.selected_channel)
        else:
            # This should never happen due to UI state management, but handle defensively
            QMessageBox.warning(
                self,
                "Invalid State",
                "Cannot confirm: baud rate or channel not properly detected."
            )

    def _detect_channels(self):
        """Detect available PCAN channels and populate dropdown."""
        self._update_channel_list(show_warning=True)
    
    def _update_channel_list(self, show_warning: bool = False):
        """
        Update the channel list by scanning for available PCAN devices.
        
        Args:
            show_warning: Whether to show a warning dialog if no devices found
        """
        # Show loading message
        self.status_label.setText("Scanning for PCAN devices...")
        self.channel_status_label.setText("")
        
        # Get available channels
        available_channels = self.pcan_interface.get_available_channels()
        
        # Debug logging
        print(f"DEBUG: Found {len(available_channels)} channels: {available_channels}")
        
        # Clear and repopulate combo box
        self.channel_combo.clear()
        
        if available_channels:
            for channel in available_channels:
                # Convert PCAN_USBBUS1 to "PCAN-USB 1" for display
                display_name = channel.replace('PCAN_USBBUS', 'PCAN-USB ')
                self.channel_combo.addItem(display_name, channel)  # Display name, actual value
            
            # Update status with correct count
            count = len(available_channels)
            self.channel_status_label.setText(f"✓ Found {count} PCAN device(s)")
            self.channel_status_label.setStyleSheet("margin: 5px; font-size: 11px; color: green;")
            
            # Select first channel by default
            self.selected_channel = available_channels[0]
            
            # Enable detection
            self.detect_button.setEnabled(True)
            self.status_label.setText(f"Select a channel and click 'Detect Baud Rate'.")
        else:
            # No devices found
            self.channel_combo.addItem("No PCAN devices found", None)
            self.detect_button.setEnabled(False)
            self.status_label.setText("")
            self.channel_status_label.setText("⚠ No PCAN devices found. Please connect a device and click Refresh.")
            self.channel_status_label.setStyleSheet("margin: 5px; font-size: 11px; color: red;")
            
            if show_warning:
                QMessageBox.warning(
                    self,
                    "No PCAN Devices",
                    "No PCAN devices were detected.\n\n"
                    "Please ensure:\n"
                    "- PCAN device is connected via USB\n"
                    "- PCAN drivers are properly installed\n"
                    "- Device has power and is recognized by the system\n\n"
                    "Try reconnecting the device and click the Refresh button."
                )

    def _on_channel_selected(self, index: int):
        """
        Handle channel selection change.

        Args:
            index: Selected combo box index
        """
        if index >= 0:
            # Get the actual channel value (not display name)
            self.selected_channel = self.channel_combo.itemData(index)
            if self.selected_channel:
                print(f"Selected channel: {self.selected_channel}")
                self.detect_button.setEnabled(True)
            else:
                self.detect_button.setEnabled(False)
    
    def _refresh_channels(self):
        """Refresh available PCAN channels and update dropdown."""
        # Disable refresh button during scanning
        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("Scanning...")
        
        # Update channel list (no warning dialog on refresh)
        self._update_channel_list(show_warning=False)
        
        # Re-enable refresh button
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("🔄 Refresh")