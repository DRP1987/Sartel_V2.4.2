"""Generate screenshots of the UI for documentation."""

import sys
import os
from pathlib import Path

# Set up offscreen rendering
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from gui.main_window import MainWindow
from gui.config_selection_screen import ConfigSelectionScreen
from gui.monitoring_screen import MonitoringScreen
from config.config_loader import ConfigurationLoader
from canbus.pcan_interface import PCANInterface


def capture_config_screen_online():
    """Capture configuration screen in online mode."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    config_loader = ConfigurationLoader()
    screen = ConfigSelectionScreen(config_loader)
    
    # Set to online mode
    screen.set_connection_status(True)
    screen.show()
    
    # Take screenshot
    pixmap = screen.grab()
    screenshot_path = "/tmp/config_screen_online.png"
    pixmap.save(screenshot_path)
    print(f"✓ Saved online config screen to: {screenshot_path}")
    
    return screenshot_path


def capture_config_screen_offline():
    """Capture configuration screen in offline mode."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    config_loader = ConfigurationLoader()
    screen = ConfigSelectionScreen(config_loader)
    
    # Set to offline mode
    screen.set_connection_status(False)
    screen.show()
    
    # Take screenshot
    pixmap = screen.grab()
    screenshot_path = "/tmp/config_screen_offline.png"
    pixmap.save(screenshot_path)
    print(f"✓ Saved offline config screen to: {screenshot_path}")
    
    return screenshot_path


def capture_monitoring_screen_offline():
    """Capture monitoring screen in offline mode."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    pcan = PCANInterface()
    config = {
        'name': 'Test Configuration',
        'signals': [
            {
                'name': 'Signal 1',
                'can_id': 0x123,
                'match_type': 'exact',
                'data': [1, 2, 3, 4, 5, 6, 7, 8]
            },
            {
                'name': 'Signal 2',
                'can_id': 0x456,
                'match_type': 'range',
                'data_byte_index': 0,
                'min_value': 10,
                'max_value': 50
            }
        ]
    }
    
    screen = MonitoringScreen(
        pcan_interface=pcan,
        configuration=config,
        baudrate=None,
        channel=None,
        connected=False
    )
    screen.show()
    
    # Take screenshot
    pixmap = screen.grab()
    screenshot_path = "/tmp/monitoring_screen_offline.png"
    pixmap.save(screenshot_path)
    print(f"✓ Saved offline monitoring screen to: {screenshot_path}")
    
    return screenshot_path


def capture_monitoring_screen_online():
    """Capture monitoring screen in online mode (simulated)."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    pcan = PCANInterface()
    config = {
        'name': 'Test Configuration',
        'signals': [
            {
                'name': 'Signal 1',
                'can_id': 0x123,
                'match_type': 'exact',
                'data': [1, 2, 3, 4, 5, 6, 7, 8]
            },
            {
                'name': 'Signal 2',
                'can_id': 0x456,
                'match_type': 'range',
                'data_byte_index': 0,
                'min_value': 10,
                'max_value': 50
            }
        ]
    }
    
    screen = MonitoringScreen(
        pcan_interface=pcan,
        configuration=config,
        baudrate=500000,
        channel='PCAN_USBBUS1',
        connected=True
    )
    screen.show()
    
    # Take screenshot
    pixmap = screen.grab()
    screenshot_path = "/tmp/monitoring_screen_online.png"
    pixmap.save(screenshot_path)
    print(f"✓ Saved online monitoring screen to: {screenshot_path}")
    
    return screenshot_path


if __name__ == '__main__':
    print("Generating UI screenshots...\n")
    
    try:
        capture_config_screen_online()
        capture_config_screen_offline()
        capture_monitoring_screen_offline()
        capture_monitoring_screen_online()
        
        print("\n✓ All screenshots generated successfully!")
        print("Screenshots saved to /tmp/")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Screenshot generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
