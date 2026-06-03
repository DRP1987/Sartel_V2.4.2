"""Capture screenshots of the splash screen animation states."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from gui.splash_screen import SplashScreen


def capture_animation_states():
    """Capture screenshots of all 4 animation states."""
    app = QApplication(sys.argv)
    
    # Create splash screen
    splash = SplashScreen()
    splash.show()
    app.processEvents()
    
    # Capture initial state (0 dots - "Loading")
    print("Capturing state 0: Loading")
    pixmap = splash.grab()
    pixmap.save("/tmp/splash_state_0.png")
    
    # Trigger animation update and capture state 1 (1 dot - "Loading.")
    splash._update_loading_text()
    app.processEvents()
    print("Capturing state 1: Loading.")
    pixmap = splash.grab()
    pixmap.save("/tmp/splash_state_1.png")
    
    # State 2 (2 dots - "Loading..")
    splash._update_loading_text()
    app.processEvents()
    print("Capturing state 2: Loading..")
    pixmap = splash.grab()
    pixmap.save("/tmp/splash_state_2.png")
    
    # State 3 (3 dots - "Loading...")
    splash._update_loading_text()
    app.processEvents()
    print("Capturing state 3: Loading...")
    pixmap = splash.grab()
    pixmap.save("/tmp/splash_state_3.png")
    
    # Close splash
    splash.close()
    
    print("\nScreenshots saved to /tmp/splash_state_*.png")
    print("\nAnimation sequence:")
    print("  State 0: Loading")
    print("  State 1: Loading.")
    print("  State 2: Loading..")
    print("  State 3: Loading...")
    print("  (cycles back to State 0)")


if __name__ == '__main__':
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    capture_animation_states()
