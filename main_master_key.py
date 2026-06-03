"""Main entry point with offline license validation."""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QInputDialog, QLineEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer
from gui.main_window import MainWindow
from gui.splash_screen import SplashScreen
from config.app_config import APP_NAME, ICON_PATH_PNG, ICON_PATH_ICO, SHOW_SPLASH_SCREEN, SPLASH_DURATION
from utils.resource_path import resource_path
from utils.security import security_manager
import hashlib


# Your secret salt - CHANGE THIS!
SECRET_SALT = "YOUR_SECRET_SALT_HERE"

# Master license key (works on any computer) - KEEP THIS SECRET!
MASTER_LICENSE_KEY = "MASTER-XXXXX-XXXXX-XXXXX-XXXXX"


def validate_license_simple():
    """
    Simple license validation without server. 
    Checks for license key that matches hardware ID or master key.
    
    Returns:
        True if license is valid, False otherwise
    """
    # Get hardware ID
    hw_id = security_manager.get_hardware_id()
    print(f"DEBUG: Hardware ID: {hw_id}")
    
    # Check for license file in user's home directory
    license_file = os.path.join(os.path.expanduser('~'), '.canbus_license.key')
    
    # If license file exists, try to validate it
    if os.path.exists(license_file):
        try:
            with open(license_file, 'r') as f:
                stored_license = f.read().strip()
            
            print(f"DEBUG: Found saved license: {stored_license}")
            
            # Check if it's the master key
            if stored_license. upper() == MASTER_LICENSE_KEY.upper():
                print("DEBUG: Master license key validated")
                security_manager.license_valid = True
                return True
            
            # Verify license matches hardware
            if verify_license_key(stored_license, hw_id):
                print("DEBUG: License validated successfully")
                security_manager.license_valid = True
                return True
            else:
                print("DEBUG:  Saved license invalid")
        except Exception as e:
            print(f"DEBUG: Error reading license:  {e}")
    
    # No valid license found - ask user for license key
    while True:
        license_key, ok = QInputDialog.getText(
            None,
            "License Activation Required",
            f"Please enter your license key:\n\n"
            f"Your Hardware ID: {hw_id}\n"
            f"(Send this Hardware ID to get your license key)",
            echo=QLineEdit.Normal
        )
        
        if not ok: 
            # User cancelled
            QMessageBox.warning(None, "License Required",
                               "A valid license is required to use this application.")
            return False
        
        if not license_key:
            continue
        
        # Check if it's the master key
        if license_key.strip().upper() == MASTER_LICENSE_KEY.upper():
            # Valid master key - save it
            try:
                with open(license_file, 'w') as f:
                    f.write(license_key. strip())
                
                security_manager.license_valid = True
                QMessageBox.information(None, "License Activated",
                                       "Master license activated successfully!\n\n"
                                       "This license works on any computer.")
                return True
            except Exception as e:
                QMessageBox.critical(None, "Error",
                                    f"Could not save license: {e}")
                return False
        
        # Verify the license key
        if verify_license_key(license_key. strip(), hw_id):
            # Valid license - save it
            try:
                with open(license_file, 'w') as f:
                    f.write(license_key.strip())
                
                security_manager.license_valid = True
                QMessageBox.information(None, "License Activated",
                                       "License activated successfully!\n\n"
                                       "The application will now start.")
                return True
            except Exception as e:
                QMessageBox.critical(None, "Error",
                                    f"Could not save license: {e}")
                return False
        else:
            # Invalid license
            retry = QMessageBox.question(
                None,
                "Invalid License",
                f"The license key is invalid or not valid for this computer.\n\n"
                f"Hardware ID: {hw_id}\n"
                f"License Key:  {license_key.strip()}\n\n"
                f"Try again? ",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if retry == QMessageBox.No:
                return False


def verify_license_key(license_key, hardware_id):
    """
    Verify that license key matches hardware ID.
    
    Args:
        license_key: License key from user
        hardware_id: This computer's hardware ID
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Generate expected license key for this hardware
        combined = f"{hardware_id}_{SECRET_SALT}"
        expected_license = hashlib.sha256(combined.encode()).hexdigest()[:20]. upper()
        
        # Format:  XXXXX-XXXXX-XXXXX-XXXXX
        expected_formatted = '-'.join([expected_license[i:i+5] for i in range(0, 20, 5)])
        
        print(f"DEBUG:  Expected license: {expected_formatted}")
        print(f"DEBUG:  Provided license: {license_key.upper()}")
        
        return license_key.upper() == expected_formatted
    except Exception as e:
        print(f"DEBUG: License verification error: {e}")
        return False


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("DRP1987")
    
    # PRODUCTION:  Enable license validation
    if not validate_license_simple():
        sys.exit(1)
    
    # Set application icon
    icon_path = None
    if sys.platform. startswith('win'):
        icon_path = resource_path(ICON_PATH_ICO)
    else:
        icon_path = resource_path(ICON_PATH_PNG)
    
    if icon_path and os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Show splash screen
    splash = None
    if SHOW_SPLASH_SCREEN:
        splash = SplashScreen()
        splash.show()
        app.processEvents()
    
    # Create main window
    window = MainWindow()
    
    # Show main window after splash
    if SHOW_SPLASH_SCREEN and splash:
        QTimer.singleShot(SPLASH_DURATION, lambda: (splash.close(), window.show()))
    else:
        window.show()
    
    # Run application
    sys.exit(app. exec_())


if __name__ == "__main__":
    main()