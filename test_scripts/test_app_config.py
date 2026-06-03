"""Test application configuration and icon support."""

import os
import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.app_config import APP_NAME, APP_VERSION, ICON_PATH_PNG, ICON_PATH_ICO


class TestAppConfig(unittest.TestCase):
    """Test application configuration."""

    def test_app_name_defined(self):
        """Test that APP_NAME is defined."""
        self.assertIsNotNone(APP_NAME)
        self.assertIsInstance(APP_NAME, str)
        self.assertGreater(len(APP_NAME), 0)
        print(f"APP_NAME: {APP_NAME}")

    def test_app_version_defined(self):
        """Test that APP_VERSION is defined."""
        self.assertIsNotNone(APP_VERSION)
        self.assertIsInstance(APP_VERSION, str)
        self.assertGreater(len(APP_VERSION), 0)
        print(f"APP_VERSION: {APP_VERSION}")

    def test_icon_paths_defined(self):
        """Test that icon paths are defined."""
        self.assertIsNotNone(ICON_PATH_PNG)
        self.assertIsNotNone(ICON_PATH_ICO)
        self.assertIsInstance(ICON_PATH_PNG, str)
        self.assertIsInstance(ICON_PATH_ICO, str)
        print(f"ICON_PATH_PNG: {ICON_PATH_PNG}")
        print(f"ICON_PATH_ICO: {ICON_PATH_ICO}")

    def test_icon_files_exist(self):
        """Test that icon files exist."""
        project_root_path = Path(__file__).parent
        icon_png_path = project_root_path / ICON_PATH_PNG
        icon_ico_path = project_root_path / ICON_PATH_ICO
        
        self.assertTrue(icon_png_path.exists(), f"PNG icon not found at {icon_png_path}")
        self.assertTrue(icon_ico_path.exists(), f"ICO icon not found at {icon_ico_path}")
        print(f"Icon files found: {icon_png_path}, {icon_ico_path}")

    def test_assets_readme_exists(self):
        """Test that assets README exists."""
        project_root_path = Path(__file__).parent
        readme_path = project_root_path / "assets" / "README.md"
        
        self.assertTrue(readme_path.exists(), f"Assets README not found at {readme_path}")
        print(f"Assets README found at {readme_path}")

    def test_icon_files_are_valid(self):
        """Test that icon files are valid image files."""
        try:
            from PIL import Image
            
            project_root_path = Path(__file__).parent
            icon_png_path = project_root_path / ICON_PATH_PNG
            icon_ico_path = project_root_path / ICON_PATH_ICO
            
            # Try to open the PNG
            with Image.open(icon_png_path) as img:
                self.assertEqual(img.format, 'PNG')
                self.assertGreaterEqual(img.width, 256)
                self.assertGreaterEqual(img.height, 256)
                print(f"PNG icon is valid: {img.width}x{img.height}")
            
            # Try to open the ICO
            with Image.open(icon_ico_path) as img:
                self.assertEqual(img.format, 'ICO')
                print(f"ICO icon is valid")
                
        except ImportError:
            print("Pillow not installed, skipping image validation")


if __name__ == '__main__':
    unittest.main(verbosity=2)
