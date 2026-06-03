"""Main entry point with time-based offline license validation."""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer
from gui.main_window import MainWindow
from gui.splash_screen import SplashScreen
from gui.license_dialog import LicenseDialog
from config.app_config import APP_NAME, ICON_PATH_PNG, ICON_PATH_ICO, SHOW_SPLASH_SCREEN, SPLASH_DURATION
from utils.resource_path import resource_path
from utils.security import security_manager
import hashlib
from datetime import datetime


# Your secret salt - CHANGE THIS!
SECRET_SALT = "ZSU34LPWillwhs0MhaY2uVS24wkiHscoh7b4ByoxHs7DRI69Oy"  # ← UPDATE THIS!

# Master license key (works on any computer) - KEEP THIS SECRET!
MASTER_LICENSE_KEY = "MASTER-XXXXX-XXXXX-XXXXX-XXXXX"  # ← UPDATE THIS!


def validate_license_simple():
    """
    Time-based license validation without server.
    Checks for license key that matches hardware ID and validates expiration.
    
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
            if stored_license.upper() == MASTER_LICENSE_KEY.upper():
                print("DEBUG: Master license key validated")
                security_manager.license_valid = True
                security_manager.license_expiry = None  # Master key never expires
                return True
            
            # Verify license matches hardware and check expiration
            is_valid, expiry_date, message = verify_license_key(stored_license, hw_id)
            
            if is_valid:
                print(f"DEBUG: License validated successfully, expires: {expiry_date}")
                security_manager.license_valid = True
                security_manager.license_expiry = expiry_date
                return True
            else:
                print(f"DEBUG: Saved license invalid: {message}")
                # Delete invalid license
                os.remove(license_file)
        except Exception as e:
            print(f"DEBUG: Error reading license: {e}")
    
    # No valid license found - show new copyable license dialog
    dialog = LicenseDialog()
    dialog.set_validation_callback(lambda key: validate_license_key_with_save(key, hw_id, license_file))
    
    result = dialog.exec_()
    
    if result == QDialog.Rejected:
        # User clicked Exit
        QMessageBox.warning(None, "License Required",
                           "A valid license is required to use this application.")
        return False
    
    # Check if license is now valid (should be set by callback)
    return security_manager.license_valid


def validate_license_key_with_save(license_key, hardware_id, license_file):
    """
    Validate license key and save if valid.
    This is called from the license dialog.
    
    Args:
        license_key: License key to validate
        hardware_id: Hardware ID
        license_file: Path to save license file
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    if not license_key:
        return False, "Please enter a license key."
    
    # Check if it's the master key
    if license_key.strip().upper() == MASTER_LICENSE_KEY.upper():
        try:
            with open(license_file, 'w') as f:
                f.write(license_key.strip())
            
            security_manager.license_valid = True
            security_manager.license_expiry = None  # Master key never expires
            
            return True, "✅ Master license activated successfully!\n\nThis license works on any computer and never expires."
        except Exception as e:
            return False, f"Could not save license: {e}"
    
    # Verify the license key with expiration check
    is_valid, expiry_date, message = verify_license_key(license_key.strip(), hardware_id)
    
    if is_valid:
        # Valid license - save it
        try:
            with open(license_file, 'w') as f:
                f.write(license_key.strip())
            
            security_manager.license_valid = True
            security_manager.license_expiry = expiry_date
            
            days_remaining = (expiry_date - datetime.utcnow()).days
            
            return True, (f"✅ License activated successfully!\n\n"
                         f"Valid until: {expiry_date.strftime('%B %d, %Y')}\n"
                         f"Days remaining: {days_remaining}")
        except Exception as e:
            return False, f"Could not save license: {e}"
    else:
        # Invalid license
        return False, f"❌ {message}\n\nHardware ID: {hardware_id}\n\nPlease verify your license key and try again."


def verify_license_key(license_key, hardware_id):
    """
    Verify that license key matches hardware ID and check expiration.
    
    Args:
        license_key: License key from user (format: XXXXX-XXXXX-XXXXX-YYYYMMDD)
        hardware_id: This computer's hardware ID
        
    Returns:
        Tuple of (is_valid, expiry_date, error_message)
    """
    try:
        # Remove dashes for processing
        clean_key = license_key.replace('-', '')
        
        # License format: 15 chars hash + 8 chars date (YYYYMMDD)
        if len(clean_key) != 23:
            return False, None, "Invalid license key format (expected 23 characters without dashes)"
        
        # Extract expiry date from last 8 characters
        expiry_str = clean_key[-8:]  # YYYYMMDD
        
        # Check for permanent license indicator
        if expiry_str == '99991231':
            # Permanent license
            expiry_date = None
            print("DEBUG: Permanent license detected")
        else:
            try:
                expiry_date = datetime.strptime(expiry_str, '%Y%m%d')
            except:
                return False, None, "Invalid license key format (bad date)"
            
            # Check if license has expired
            if datetime.utcnow() > expiry_date:
                return False, None, f"License expired on {expiry_date.strftime('%Y-%m-%d')}"
        
        # Generate expected license key for this hardware and expiry
        combined = f"{hardware_id}_{expiry_str}_{SECRET_SALT}"
        expected_hash = hashlib.sha256(combined.encode()).hexdigest()[:16].upper()
        
        # Format expected key
        expected_formatted = '-'.join([expected_hash[i:i+5] for i in range(0, 15, 5)]) + '-' + expiry_str
        
        print(f"DEBUG: Expected license: {expected_formatted}")
        print(f"DEBUG: Provided license: {license_key.upper()}")
        
        if license_key.upper() == expected_formatted:
            return True, expiry_date, "Valid"
        else:
            return False, None, "License key does not match this computer's Hardware ID"
            
    except Exception as e:
        print(f"DEBUG: License verification error: {e}")
        return False, None, f"Verification error: {str(e)}"


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("DRP1987")
    
    # PRODUCTION: Enable license validation
    if not validate_license_simple():
        sys.exit(1)
    
    # Set application icon
    icon_path = None
    if sys.platform.startswith('win'):
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
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()