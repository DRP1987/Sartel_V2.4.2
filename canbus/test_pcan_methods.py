"""Test different PCAN detection methods."""

import sys

try:
    from PCANBasic import *
    
    print("=== Method 1: GetValue with PCAN_CHANNEL_CONDITION ===")
    pcan = PCANBasic()
    
    channels = [
        (PCAN_USBBUS1, 'PCAN_USBBUS1'),
        (PCAN_USBBUS2, 'PCAN_USBBUS2'),
    ]
    
    for channel, name in channels:
        result = pcan.GetValue(channel, PCAN_CHANNEL_CONDITION)
        print(f"{name}:")
        print(f"  Result code: {result[0]} (OK={PCAN_ERROR_OK})")
        print(f"  Condition: {result[1]}")
        print(f"  AVAILABLE flag: {PCAN_CHANNEL_AVAILABLE}")
        print(f"  Is available: {result[1] & PCAN_CHANNEL_AVAILABLE}")
        print()
    
    print("=== Method 2: Try Initialize ===")
    for channel, name in channels:
        result = pcan.Initialize(channel, PCAN_BAUD_500K)
        print(f"{name}:  Initialize result = {result}")
        
        if result == PCAN_ERROR_OK: 
            print(f"  ✅ {name} initialized successfully")
            # Uninitialize
            pcan.Uninitialize(channel)
        elif result == PCAN_ERROR_CAUTION:
            print(f"  ⚠️  {name} already initialized")
            pcan.Uninitialize(channel)
        else:
            print(f"  ❌ {name} not available (error:  {result})")
        print()
    
    print("=== Method 3: GetValue with PCAN_CHANNEL_FEATURES ===")
    for channel, name in channels:
        result = pcan.GetValue(channel, PCAN_CHANNEL_FEATURES)
        print(f"{name}:  Features = {result}")
        print()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

input("Press Enter to exit...")