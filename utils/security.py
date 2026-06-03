"""Maximum security module for license validation and encryption."""

import os
import sys
import hashlib
import json
import requests
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64


class SecurityManager:
    """Handles all security operations."""
    
    # Your server URL (change this to your actual server)
    LICENSE_SERVER = "https://your-server.com/api/validate_license"
    
    # Master encryption key - CHANGE THIS TO A RANDOM 32-BYTE STRING! 
    MASTER_KEY = b"^\xaa\xca_\xc5\xc1\x93AQUq\xb0\x9f\x9c\x97{\xdd\xe5\x8b+\\\xd2\xe8\xc1_\xb7\x9a\x1e\x9aW\x08\x0c"
    
    def __init__(self):
        """Initialize security manager."""
        self.hardware_id = None
        self.license_valid = False
        self.license_data = None
        self.license_expiry = None
        
    def get_hardware_id(self):
        """
        Get stable unique hardware identifier.
        Uses motherboard, BIOS, and system UUID for stability.
        """
        if self.hardware_id:
            return self.hardware_id
        
        try:
            from utils.hardware_id import get_stable_hardware_id
            hw_id = get_stable_hardware_id()
            self.hardware_id = hw_id
            print(f"DEBUG: Hardware ID: {hw_id}")
            return hw_id
        except ImportError:
            # Fallback to old method if hardware_id module not available
            print("WARNING: Using fallback hardware ID method (less stable)")
            return self._get_legacy_hardware_id()
    
    def _get_legacy_hardware_id(self):
        """
        Legacy hardware ID method (DEPRECATED - less stable).
        Only used as fallback if utils.hardware_id module is missing.
        """
        import platform
        import subprocess
        
        identifiers = []
        
        try:
            # Try to get motherboard serial (most stable)
            if platform.system() == "Windows":
                result = subprocess.check_output(
                    "wmic baseboard get serialnumber",
                    shell=True,
                    stderr=subprocess.DEVNULL,
                    timeout=5
                ).decode()
                
                lines = result.strip().split('\n')
                if len(lines) > 1:
                    mb_serial = lines[1].strip()
                    if mb_serial and mb_serial.lower() not in ['to be filled by o.e.m.', 'default string', 'none']:
                        identifiers.append(f"MB:{mb_serial}")
            
            # System UUID
            if platform.system() == "Windows":
                result = subprocess.check_output(
                    "wmic csproduct get uuid",
                    shell=True,
                    stderr=subprocess.DEVNULL,
                    timeout=5
                ).decode()
                
                lines = result.strip().split('\n')
                if len(lines) > 1:
                    sys_uuid = lines[1].strip()
                    identifiers.append(f"UUID:{sys_uuid}")
            
            # Computer name
            identifiers.append(f"NAME:{platform.node()}")
            
            # Combine and hash
            combined = "|".join(identifiers)
            hw_hash = hashlib.sha256(combined.encode()).hexdigest()
            return hw_hash[:32].upper()
            
        except Exception as e: 
            print(f"Error getting hardware ID: {e}")
            # Last resort fallback
            import uuid
            mac = uuid.getnode()
            hw_string = f"{mac}_{platform.system()}_{platform.node()}"
            return hashlib.sha256(hw_string.encode()).hexdigest()[:32].upper()
    
    def validate_license_online(self, license_key):
        """Validate license key with server."""
        try:
            self.hardware_id = self.get_hardware_id()
            print(f"DEBUG: Validating license online...")
            print(f"DEBUG: Hardware ID: {self.hardware_id}")
            
            response = requests.post(
                self.LICENSE_SERVER,
                json={
                    'license_key': license_key,
                    'hardware_id': self.hardware_id,
                    'app_version': '2.0.0',
                    'timestamp': datetime.utcnow().isoformat()
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('valid'):
                    expiry_str = data.get('expiry_date')
                    if expiry_str:
                        expiry = datetime.fromisoformat(expiry_str)
                        if datetime.utcnow() > expiry:
                            return False, "License has expired"
                        self.license_expiry = expiry
                    else:
                        # No expiry = permanent license
                        self.license_expiry = None
                    
                    self.license_data = data
                    self.license_valid = True
                    self._cache_license(license_key, data)
                    return True, "License valid"
                else: 
                    return False, data.get('message', 'Invalid license')
            else:
                return False, f"Server error: {response.status_code}"
        except requests.exceptions.RequestException as e:
            print(f"DEBUG: Online validation failed: {e}")
            return self._validate_license_offline(license_key)
        except Exception as e: 
            return False, f"Validation error: {str(e)}"
    
    def _validate_license_offline(self, license_key):
        """Validate license offline using cached data."""
        try:
            cache_file = self._get_license_cache_path()
            if not os.path.exists(cache_file):
                return False, "No offline license cache. Internet connection required."
            
            with open(cache_file, 'rb') as f:
                encrypted_data = f.read()
            
            cipher = Fernet(self._derive_key(license_key))
            decrypted = cipher.decrypt(encrypted_data)
            data = json.loads(decrypted.decode())
            
            # Validate hardware ID
            cached_hw_id = data.get('hardware_id')
            current_hw_id = self.get_hardware_id()
            
            if cached_hw_id != current_hw_id:
                print(f"DEBUG: Hardware ID mismatch!")
                print(f"  Cached:  {cached_hw_id}")
                print(f"  Current: {current_hw_id}")
                return False, "License not valid for this computer"
            
            # Check expiry
            expiry_str = data.get('expiry_date')
            if expiry_str:
                expiry = datetime.fromisoformat(expiry_str)
                if datetime.utcnow() > expiry:
                    return False, "License has expired"
                self.license_expiry = expiry
            else:
                self.license_expiry = None
            
            # Check cache age
            cached_time = datetime.fromisoformat(data.get('cached_at'))
            if datetime.utcnow() - cached_time > timedelta(days=7):
                return False, "Offline license expired. Please connect to internet."
            
            self.license_data = data
            self.license_valid = True
            return True, "License valid (offline mode)"
        except Exception as e:
            print(f"DEBUG: Offline validation error: {e}")
            return False, f"Offline validation failed: {str(e)}"
    
    def _cache_license(self, license_key, data):
        """Cache license data for offline validation."""
        try:
            cache_file = self._get_license_cache_path()
            data['cached_at'] = datetime.utcnow().isoformat()
            data['hardware_id'] = self.hardware_id
            
            cipher = Fernet(self._derive_key(license_key))
            encrypted = cipher.encrypt(json.dumps(data).encode())
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            
            with open(cache_file, 'wb') as f:
                f.write(encrypted)
            
            print(f"DEBUG: License cached to: {cache_file}")
        except Exception as e: 
            print(f"Error caching license: {e}")
    
    def _get_license_cache_path(self):
        """Get path to license cache file."""
        # Store in AppData folder
        appdata = os.getenv('APPDATA')
        if appdata:
            cache_dir = os.path.join(appdata, 'CANBusMonitor')
            return os.path.join(cache_dir, '.canbus_lic')
        else:
            # Fallback to home directory
            return os.path.join(os.path.expanduser('~'), '.canbus_lic')
    
    def _derive_key(self, password):
        """Derive encryption key from password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.MASTER_KEY[:16],
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def decrypt_file(self, encrypted_path, password=None):
        """Decrypt an encrypted file."""
        if not self.license_valid:
            raise PermissionError("Valid license required to decrypt files")
        
        try:
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            
            if password: 
                key = self._derive_key(password)
            else:
                key = base64.urlsafe_b64encode(self.MASTER_KEY)
            
            cipher = Fernet(key)
            return cipher.decrypt(encrypted_data)
        except Exception as e:
            raise Exception(f"Decryption failed: {e}")
    
    def decrypt_data(self, encrypted_data, password=None):
        """
        Decrypt encrypted data bytes.
        
        Args:
            encrypted_data: Encrypted bytes
            password: Optional password for decryption
            
        Returns:
            Decrypted bytes
        """
        if not self.license_valid:
            raise PermissionError("Valid license required to decrypt data")
        
        try:
            if password: 
                key = self._derive_key(password)
            else:
                key = base64.urlsafe_b64encode(self.MASTER_KEY)
            
            cipher = Fernet(key)
            return cipher.decrypt(encrypted_data)
        except Exception as e:
            raise Exception(f"Decryption failed: {e}")
    
    def encrypt_file(self, input_path, output_path, password=None):
        """Encrypt a file."""
        try:
            with open(input_path, 'rb') as f:
                data = f.read()
            
            if password:
                key = self._derive_key(password)
            else:
                key = base64.urlsafe_b64encode(self.MASTER_KEY)
            
            cipher = Fernet(key)
            encrypted = cipher.encrypt(data)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted)
            
            print(f"✅ Encrypted: {input_path} -> {output_path}")
        except Exception as e:
            print(f"❌ Encryption failed: {e}")
            raise
    
    def check_anti_debug(self):
        """Basic anti-debugging check."""
        try:
            if sys.platform.startswith('win'):
                import ctypes
                is_debugged = ctypes.windll.kernel32.IsDebuggerPresent()
                return bool(is_debugged)
        except:
            pass
        return False
    
    def verify_integrity(self):
        """Verify app hasn't been tampered with."""
        if not hasattr(sys, '_MEIPASS'):
            return True
        if self.check_anti_debug():
            return False
        return True
    
    def get_hardware_info(self):
        """
        Get detailed hardware information for debugging.
        
        Returns:
            Dictionary with hardware details
        """
        try:
            from utils.hardware_id import get_hardware_id_components
            return get_hardware_id_components()
        except ImportError:
            return {
                'hardware_id': self.get_hardware_id(),
                'method': 'legacy',
                'warning': 'Using less stable hardware ID method'
            }


# Global security manager instance
security_manager = SecurityManager()