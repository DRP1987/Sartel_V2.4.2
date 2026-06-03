"""Generate stable hardware ID for license validation."""

import platform
import hashlib
import subprocess
import uuid
import re


def get_stable_hardware_id() -> str:
    """
    Generate a stable hardware ID that survives common changes.
    
    Uses multiple stable identifiers:
    - Motherboard serial number
    - BIOS serial number  
    - System UUID
    - CPU identifier
    
    Returns:
        Stable hardware ID string
    """
    identifiers = []
    
    # 1. Motherboard Serial Number (most stable)
    mb_serial = _get_motherboard_serial()
    if mb_serial:
        identifiers.append(f"MB:{mb_serial}")
    
    # 2. BIOS Serial Number
    bios_serial = _get_bios_serial()
    if bios_serial:
        identifiers.append(f"BIOS:{bios_serial}")
    
    # 3. System UUID (stable on most systems)
    sys_uuid = _get_system_uuid()
    if sys_uuid:
        identifiers.append(f"UUID:{sys_uuid}")
    
    # 4. CPU Identifier (backup)
    cpu_id = _get_cpu_identifier()
    if cpu_id:
        identifiers.append(f"CPU:{cpu_id}")
    
    # 5. Computer Name (least stable, but helps)
    computer_name = platform.node()
    if computer_name:
        identifiers.append(f"NAME:{computer_name}")
    
    # Combine all identifiers
    combined = "|".join(identifiers)
    
    # Hash for privacy and fixed length
    hardware_hash = hashlib.sha256(combined.encode()).hexdigest()
    
    # Return first 32 characters for readability
    return hardware_hash[:32].upper()


def _get_motherboard_serial() -> str:
    """Get motherboard serial number (Windows)."""
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output(
                "wmic baseboard get serialnumber",
                shell=True,
                stderr=subprocess.DEVNULL,
                timeout=5
            ).decode()
            
            # Extract serial number
            lines = result.strip().split('\n')
            if len(lines) > 1:
                serial = lines[1].strip()
                # Filter out invalid serials
                if serial and serial.lower() not in ['to be filled by o.e.m.', 'default string', 'none', '']:
                    return serial
    except:
        pass
    return ""


def _get_bios_serial() -> str:
    """Get BIOS serial number (Windows)."""
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output(
                "wmic bios get serialnumber",
                shell=True,
                stderr=subprocess.DEVNULL,
                timeout=5
            ).decode()
            
            lines = result.strip().split('\n')
            if len(lines) > 1:
                serial = lines[1].strip()
                if serial and serial.lower() not in ['to be filled by o.e.m.', 'default string', 'none', '']:
                    return serial
    except:
        pass
    return ""


def _get_system_uuid() -> str:
    """Get system UUID (most stable identifier)."""
    try:
        if platform.system() == "Windows":
            # Try wmic first (most reliable)
            result = subprocess.check_output(
                "wmic csproduct get uuid",
                shell=True,
                stderr=subprocess.DEVNULL,
                timeout=5
            ).decode()
            
            lines = result.strip().split('\n')
            if len(lines) > 1:
                system_uuid = lines[1].strip()
                # Validate UUID format
                if re.match(r'^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$', 
                           system_uuid, re.IGNORECASE):
                    return system_uuid
        
        # Fallback to Python's uuid (less stable)
        # Don't use: return str(uuid.getnode())
        
    except:
        pass
    return ""


def _get_cpu_identifier() -> str:
    """Get CPU identifier."""
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output(
                "wmic cpu get processorid",
                shell=True,
                stderr=subprocess.DEVNULL,
                timeout=5
            ).decode()
            
            lines = result.strip().split('\n')
            if len(lines) > 1:
                cpu_id = lines[1].strip()
                if cpu_id and cpu_id.lower() != 'to be filled by o.e.m.':
                    return cpu_id
        
        # Fallback: CPU name
        return platform.processor()
    except:
        pass
    return ""


def get_hardware_id_components() -> dict:
    """
    Get individual hardware ID components for debugging.
    
    Returns:
        Dictionary of hardware identifiers
    """
    return {
        'motherboard_serial': _get_motherboard_serial(),
        'bios_serial': _get_bios_serial(),
        'system_uuid': _get_system_uuid(),
        'cpu_id': _get_cpu_identifier(),
        'computer_name': platform.node(),
        'platform': platform.system(),
        'final_hardware_id': get_stable_hardware_id()
    }


if __name__ == "__main__":
    """Test hardware ID generation."""
    print("="*70)
    print("HARDWARE ID COMPONENTS")
    print("="*70)
    
    components = get_hardware_id_components()
    
    for key, value in components.items():
        if key == 'final_hardware_id':
            print("\n" + "="*70)
            print(f"{key.upper()}: {value}")
            print("="*70)
        else:
            status = "✓" if value else "✗"
            print(f"{status} {key:<20}: {value or '(not available)'}")
    
    print("\nThis Hardware ID should remain stable across:")
    print("  ✓ Network adapter changes")
    print("  ✓ USB device connections")
    print("  ✓ Software reinstalls")
    print("  ✓ Windows updates")
    
    input("\nPress Enter to exit...")