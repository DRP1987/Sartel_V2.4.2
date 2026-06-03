"""Main window controller for CAN bus monitoring application."""

"""Main window controller for CAN bus monitoring application."""

from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QTabWidget, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import pyqtSlot, QTimer
from gui.baudrate_screen import BaudRateScreen
from gui.config_selection_screen import ConfigSelectionScreen
from gui.monitoring_screen import MonitoringScreen
from gui.release_notes_widget import ReleaseNotesWidget
from gui.documentation_widget import DocumentationWidget
from canbus.pcan_interface import PCANInterface
from config.config_loader import ConfigurationLoader
from config.app_config import APP_NAME, APP_VERSION
from utils.security import security_manager
from datetime import datetime


class MainWindow(QMainWindow):
    """Main application window managing screen transitions."""

    def __init__(self):
        """Initialize main window."""
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(950, 800)

        # Initialize components
        self.pcan_interface = PCANInterface()
        self.config_loader = ConfigurationLoader()
        self.detected_baudrate = None
        self.selected_channel = None
        self.selected_configuration = None
        self.is_connected = False  # Track connection status

        # Create main container with tabs
        self.main_container = QWidget()
        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Stacked widget for screen management (main application flow)
        self.stacked_widget = QStackedWidget()

        # Initialize screens
        self._init_screens()

        # Add main screens as first tab
        self.tabs.addTab(self.stacked_widget, "🖥️ Application")
        
        # Add Release Notes tab
        self.release_tab = ReleaseNotesWidget()
        self.tabs.addTab(self.release_tab, "📋 Release")
        
        # Add Documentation tab
        self.documentation_tab = DocumentationWidget()
        self.tabs.addTab(self.documentation_tab, "📄 Documentation")
        
        # Set main container as central widget
        self.setCentralWidget(self.main_container)

        # Initialize status bar with version and license info
        self._init_status_bar()

        # Check for updates 3 seconds after startup (non-blocking, silent if no update)
        QTimer.singleShot(3000, self._check_for_update)

        # Show baud rate screen first
        self.stacked_widget.setCurrentWidget(self.baudrate_screen)

    def _init_status_bar(self):
        """Initialize status bar with version and license information."""
        # Create status bar
        status_bar = self.statusBar()
        
        # Version label (left side)
        self.version_label = QLabel(f"Version {APP_VERSION}")
        self.version_label.setStyleSheet("color: #888888; padding: 2px 10px;")
        status_bar.addWidget(self.version_label)
        
        # License expiry label (right side)
        self.license_label = QLabel()
        self.license_label.setStyleSheet("padding: 2px 10px;")
        status_bar.addPermanentWidget(self.license_label)
        
        # Update license info
        self._update_license_status()
        
        # Setup timer to update license status every hour
        self.license_timer = QTimer()
        self.license_timer.timeout.connect(self._update_license_status)
        self.license_timer.start(3600000)  # Update every hour (3600000 ms)
        
        # Style the status bar
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #f5f5f5;
                border-top: 1px solid #cccccc;
                font-size: 9pt;
            }
        """)
    
    def _update_license_status(self):
        """Update the license status label."""
        if not security_manager.license_valid:
            self.license_label.setText("License: Invalid")
            self.license_label.setStyleSheet("color: #f44336; padding: 2px 10px; font-weight: bold;")
            return
        
        if security_manager.license_expiry is None:
            # Master license or permanent license
            self.license_label.setText("License: Permanent")
            self.license_label.setStyleSheet("color: #4CAF50; padding: 2px 10px;")
            return
        
        # Calculate days remaining
        now = datetime.utcnow()
        days_remaining = (security_manager.license_expiry - now).days
        
        if days_remaining < 0:
            # Expired
            self.license_label.setText("License: EXPIRED")
            self.license_label.setStyleSheet("color: #f44336; padding: 2px 10px; font-weight: bold;")
        elif days_remaining == 0:
            # Expires today
            self.license_label.setText("License: Expires TODAY")
            self.license_label.setStyleSheet("color: #f44336; padding: 2px 10px; font-weight: bold;")
        elif days_remaining == 1:
            # Expires tomorrow
            self.license_label.setText("License: 1 day left")
            self.license_label.setStyleSheet("color: #f44336; padding: 2px 10px; font-weight: bold;")
        elif days_remaining <= 7:
            # Expiring soon (red, bold)
            self.license_label.setText(f"License: {days_remaining} days left")
            self.license_label.setStyleSheet("color: #f44336; padding: 2px 10px; font-weight: bold;")
        elif days_remaining <= 30:
            # Warning (orange)
            self.license_label.setText(f"License: {days_remaining} days left")
            self.license_label.setStyleSheet("color: #FF9800; padding: 2px 10px;")
        else:
            # Good (green)
            self.license_label.setText(f"License: {days_remaining} days left")
            self.license_label.setStyleSheet("color: #4CAF50; padding: 2px 10px;")

    def _init_screens(self):
        """Initialize all application screens."""
        # Baud rate detection screen
        self.baudrate_screen = BaudRateScreen(self.pcan_interface)
        self.baudrate_screen.baudrate_confirmed.connect(self._on_baudrate_confirmed)
        self.baudrate_screen.continue_offline.connect(self._on_continue_offline)
        self.stacked_widget.addWidget(self.baudrate_screen)

        # Configuration selection screen
        self.config_selection_screen = ConfigSelectionScreen(self.config_loader)
        self.config_selection_screen.configuration_selected.connect(
            self._on_configuration_selected
        )
        self.config_selection_screen.reconnect_requested.connect(
            self._on_reconnect_requested
        )
        self.stacked_widget.addWidget(self.config_selection_screen)

    def _check_for_update(self):
        """Check for available updates silently in the background."""
        from utils.updater import check_for_update
        from gui.update_dialog import UpdateDialog
        try:
            manifest = check_for_update()
            if manifest:
                dialog = UpdateDialog(manifest, parent=self)
                dialog.exec_()
        except Exception as e:
            print("[MainWindow] Update check error: {}".format(e))

    @pyqtSlot(int, str)
    def _on_baudrate_confirmed(self, baudrate: int, channel: str):
        """
        Handle baud rate confirmation.

        Args:
            baudrate: Confirmed baud rate
            channel: Selected PCAN channel
        """
        self.detected_baudrate = baudrate
        self.selected_channel = channel
        self.is_connected = True
        # Update connection status in config screen
        self.config_selection_screen.set_connection_status(True)
        # Move to configuration selection screen
        self.stacked_widget.setCurrentWidget(self.config_selection_screen)

    @pyqtSlot()
    def _on_continue_offline(self):
        """Handle user choosing to continue without connection."""
        self.detected_baudrate = None
        self.selected_channel = None
        self.is_connected = False
        # Update connection status in config screen
        self.config_selection_screen.set_connection_status(False)
        # Move to configuration selection screen
        self.stacked_widget.setCurrentWidget(self.config_selection_screen)

    @pyqtSlot()
    def _on_reconnect_requested(self):
        """Handle user requesting to reconfigure connection."""
        # Go back to baudrate screen
        self.stacked_widget.setCurrentWidget(self.baudrate_screen)

    @pyqtSlot(dict)
    def _on_configuration_selected(self, configuration: dict):
        """
        Handle configuration selection.

        Args:
            configuration: Selected configuration dictionary
        """
        self.selected_configuration = configuration

        # Remove any existing monitoring screens to prevent memory leaks
        for i in range(self.stacked_widget.count() - 1, 1, -1):
            widget = self.stacked_widget.widget(i)
            if isinstance(widget, MonitoringScreen):
                self.stacked_widget.removeWidget(widget)
                widget.deleteLater()

        # Create and show monitoring screen with connection status
        monitoring_screen = MonitoringScreen(
            self.pcan_interface,
            configuration,
            self.detected_baudrate,
            self.selected_channel,
            self.is_connected
        )
        # Connect back signal
        monitoring_screen.back_to_config.connect(self._on_back_to_config)
        self.stacked_widget.addWidget(monitoring_screen)
        self.stacked_widget.setCurrentWidget(monitoring_screen)

    @pyqtSlot()
    def _on_back_to_config(self):
        """Handle back to configuration navigation."""
        # Remove monitoring screen
        for i in range(self.stacked_widget.count() - 1, 1, -1):
            widget = self.stacked_widget.widget(i)
            if isinstance(widget, MonitoringScreen):
                self.stacked_widget.removeWidget(widget)
                widget.deleteLater()
        
        # Show configuration selection screen
        self.stacked_widget.setCurrentWidget(self.config_selection_screen)

    def closeEvent(self, event):
        """
        Handle window close event.

        Args:
            event: Close event
        """
        # Stop license timer
        if hasattr(self, 'license_timer'):
            self.license_timer.stop()
        
        # Ensure PCAN interface is disconnected
        if self.pcan_interface:
            self.pcan_interface.disconnect()
        event.accept()