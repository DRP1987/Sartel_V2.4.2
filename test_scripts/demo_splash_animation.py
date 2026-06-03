"""Visual demo of the splash screen animation."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from gui.splash_screen import SplashScreen


def main():
    """Display the splash screen with animation for 5 seconds."""
    app = QApplication(sys.argv)
    
    # Create and show splash screen
    splash = SplashScreen()
    splash.show()
    
    # Close after 5 seconds to see multiple animation cycles
    QTimer.singleShot(5000, splash.close)
    QTimer.singleShot(5100, app.quit)
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == '__main__':
    print("Displaying splash screen with animation for 5 seconds...")
    print("Watch the 'Loading' text animate with dots:")
    print("  Loading")
    print("  Loading.")
    print("  Loading..")
    print("  Loading...")
    print("  (repeats)")
    print()
    main()
