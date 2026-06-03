"""Test hardware ID stability."""

from utils.hardware_id import get_stable_hardware_id, get_hardware_id_components
import time

print("="*70)
print("HARDWARE ID STABILITY TEST")
print("="*70)
print()

# Get initial hardware ID
hw_id_1 = get_stable_hardware_id()
print(f"Hardware ID (1st check): {hw_id_1}")

# Wait a moment
time.sleep(1)

# Get it again
hw_id_2 = get_stable_hardware_id()
print(f"Hardware ID (2nd check): {hw_id_2}")

# Check components
print("\n" + "="*70)
print("HARDWARE COMPONENTS")
print("="*70)
components = get_hardware_id_components()
for key, value in components.items():
    if key != 'final_hardware_id':
        print(f"  {key:<25}: {value or '(not available)'}")

print("\n" + "="*70)

if hw_id_1 == hw_id_2:
    print("✅ STABLE: Hardware ID is consistent")
else:
    print("❌ UNSTABLE: Hardware ID changed between checks!")

print("="*70)
print()
print("Please run this test multiple times:")
print("  1. Run it now and note the Hardware ID")
print("  2. Restart your computer")
print("  3. Run it again - ID should be the same")
print("  4. Connect/disconnect USB devices")
print("  5. Run it again - ID should still be the same")
print()

input("Press Enter to exit...")