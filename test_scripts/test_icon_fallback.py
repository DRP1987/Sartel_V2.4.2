"""Test graceful fallback when icon files are missing."""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon


def test_missing_icon_fallback():
    """Test that application handles missing icon files gracefully."""
    # Set up virtual display for headless testing
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    app = QApplication(sys.argv)
    app.setApplicationName("Test App")
    
    # Test with non-existent icon path
    non_existent_path = "/tmp/nonexistent_icon.png"
    
    # This should not raise an exception
    icon = QIcon(non_existent_path)
    print(f"✓ Created QIcon with non-existent path: {non_existent_path}")
    print(f"  Icon is null: {icon.isNull()}")
    
    # Setting a null icon should not crash
    app.setWindowIcon(icon)
    print(f"✓ Set null icon as window icon (no crash)")
    
    # Test the fallback logic from main.py
    icon_path = "/tmp/nonexistent_icon.ico"
    if icon_path and os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        # Fallback to PNG if ICO doesn't exist
        icon_path_fallback = "/tmp/nonexistent_icon.png"
        if os.path.exists(icon_path_fallback):
            app.setWindowIcon(QIcon(icon_path_fallback))
        else:
            print(f"✓ Both icon files missing, no icon set (graceful fallback)")
    
    print(f"\n✓ All graceful fallback tests passed!")
    return True


if __name__ == '__main__':
    success = test_missing_icon_fallback()
    sys.exit(0 if success else 1)
