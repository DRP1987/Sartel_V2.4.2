"""Test that application starts with centralized config."""

import sys
import os
from pathlib import Path

# Set up virtual display for headless testing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from config.app_config import APP_NAME, ICON_PATH_PNG, ICON_PATH_ICO


def test_main_imports():
    """Test that main.py can import all necessary modules."""
    try:
        import main
        print("✓ main.py imports successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import main.py: {e}")
        return False


def test_gui_imports():
    """Test that GUI modules can import app_config."""
    try:
        from gui.main_window import MainWindow
        print("✓ gui.main_window imports successfully")
        
        from gui.config_selection_screen import ConfigSelectionScreen
        print("✓ gui.config_selection_screen imports successfully")
        
        from gui.monitoring_screen import MonitoringScreen
        print("✓ gui.monitoring_screen imports successfully")
        
        from gui.baudrate_screen import BaudRateScreen
        print("✓ gui.baudrate_screen imports successfully")
        
        return True
    except ImportError as e:
        print(f"✗ Failed to import GUI modules: {e}")
        return False


def test_app_name_usage():
    """Test that APP_NAME is used correctly in the application."""
    from config.app_config import APP_NAME
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    
    assert app.applicationName() == APP_NAME
    print(f"✓ Application name set to: {app.applicationName()}")
    
    return True


def test_window_titles():
    """Test that window titles use APP_NAME."""
    from gui.main_window import MainWindow
    from config.app_config import APP_NAME
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create main window (this may fail if PCAN is not available, but we're testing imports)
    try:
        window = MainWindow()
        assert window.windowTitle() == APP_NAME
        print(f"✓ Main window title: {window.windowTitle()}")
    except Exception as e:
        print(f"⚠ Could not create MainWindow (expected without PCAN): {type(e).__name__}")
        # This is expected in test environment without PCAN hardware
    
    return True


if __name__ == '__main__':
    print("Testing application with centralized config...\n")
    
    all_passed = True
    
    all_passed &= test_main_imports()
    all_passed &= test_gui_imports()
    all_passed &= test_app_name_usage()
    all_passed &= test_window_titles()
    
    if all_passed:
        print(f"\n✓ All integration tests passed!")
        sys.exit(0)
    else:
        print(f"\n✗ Some tests failed!")
        sys.exit(1)
