"""
Unit tests for bit-level signal matching.

This test validates that the bit matching functionality works correctly
for monitoring individual bits within CAN message bytes.
"""

import sys
import traceback
from canbus.signal_matcher import SignalMatcher


class TestBitMatching:
    """Test bit-level signal matching."""
    
    def __init__(self):
        """Initialize test harness."""
        self.test_count = 0
        self.passed_count = 0
    
    def test(self, name, condition, expected=True):
        """Run a test and track results."""
        self.test_count += 1
        if condition == expected:
            self.passed_count += 1
            print(f"  ✓ {name}")
            return True
        else:
            print(f"  ✗ {name} - Expected {expected}, got {condition}")
            return False


def run_tests():
    """Run all bit matching tests."""
    print("=" * 70)
    print("BIT-LEVEL SIGNAL MATCHING TESTS")
    print("=" * 70)
    
    test = TestBitMatching()
    
    # Test 1: Basic bit matching - bit 0 (LSB) = 1
    print("\n[TEST 1] Bit 0 (LSB) matching")
    print("-" * 70)
    
    signal_config = {
        'can_id': 0x119,
        'match_type': 'bit',
        'byte_index': 3,
        'bit_index': 0,
        'bit_value': 1
    }
    
    # Byte 3 = 0x01 (binary: 00000001) - bit 0 = 1
    data = [0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00]
    result = SignalMatcher.match_signal(signal_config, 0x119, data)
    test.test("Byte 3 = 0x01, bit 0 should be 1", result, True)
    
    # Byte 3 = 0x00 (binary: 00000000) - bit 0 = 0
    data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    result = SignalMatcher.match_signal(signal_config, 0x119, data)
    test.test("Byte 3 = 0x00, bit 0 should be 0 (no match)", result, False)
    
    # Byte 3 = 0x03 (binary: 00000011) - bit 0 = 1
    data = [0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00]
    result = SignalMatcher.match_signal(signal_config, 0x119, data)
    test.test("Byte 3 = 0x03, bit 0 should be 1", result, True)
    
    # Byte 3 = 0xFF (binary: 11111111) - bit 0 = 1
    data = [0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00]
    result = SignalMatcher.match_signal(signal_config, 0x119, data)
    test.test("Byte 3 = 0xFF, bit 0 should be 1", result, True)
    
    # Byte 3 = 0xFE (binary: 11111110) - bit 0 = 0
    data = [0x00, 0x00, 0x00, 0xFE, 0x00, 0x00, 0x00, 0x00]
    result = SignalMatcher.match_signal(signal_config, 0x119, data)
    test.test("Byte 3 = 0xFE, bit 0 should be 0 (no match)", result, False)
    
    # Test 2: Bit matching - bit 7 (MSB)
    print("\n[TEST 2] Bit 7 (MSB) matching")
    print("-" * 70)
    
    signal_config = {
        'can_id': 0x119,
        'match_type': 'bit',
        'byte_index': 2,
        'bit_index': 7,
        'bit_value': 1
    }
    
    # Byte 2 = 0x80 (binary: 10000000) - bit 7 = 1
    data = [0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00]
    result = SignalMatcher.match_signal(signal_config, 0x119, data)
    test.test("Byte 2 = 0x80, bit 7 should be 1", result, True)
    
    # Byte 2 = 0x7F (binary: 01111111) - bit 7 = 0
    data = [0x00, 0x00, 0x7F, 0x00, 0x00, 0x00, 0x00, 0x00]
    result = SignalMatcher.match_signal(signal_config, 0x119, data)
    test.test("Byte 2 = 0x7F, bit 7 should be 0 (no match)", result, False)
    
    # Byte 2 = 0xFF (binary: 11111111) - bit 7 = 1
    data = [0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00]
    result = SignalMatcher.match_signal(signal_config, 0x119, data)
    test.test("Byte 2 = 0xFF, bit 7 should be 1", result, True)
    
    # Test 3: Bit matching - middle bits
    print("\n[TEST 3] Middle bit matching (bit 4)")
    print("-" * 70)
    
    signal_config = {
        'can_id': 0x119,
        'match_type': 'bit',
        'byte_index': 1,
        'bit_index': 4,
        'bit_value': 0
    }
    
    # Byte 1 = 0x0F (binary: 00001111) - bit 4 = 0
    data = [0x00, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    result = SignalMatcher.match_signal(signal_config, 0x119, data)
    test.test("Byte 1 = 0x0F, bit 4 should be 0", result, True)
    
    # Byte 1 = 0x10 (binary: 00010000) - bit 4 = 1
    data = [0x00, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    result = SignalMatcher.match_signal(signal_config, 0x119, data)
    test.test("Byte 1 = 0x10, bit 4 should be 1 (no match)", result, False)
    
    # Byte 1 = 0xEF (binary: 11101111) - bit 4 = 0
    data = [0x00, 0xEF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    result = SignalMatcher.match_signal(signal_config, 0x119, data)
    test.test("Byte 1 = 0xEF, bit 4 should be 0", result, True)
    
    # Test 4: CAN ID mismatch
    print("\n[TEST 4] CAN ID mismatch")
    print("-" * 70)
    
    signal_config = {
        'can_id': 0x119,
        'match_type': 'bit',
        'byte_index': 3,
        'bit_index': 0,
        'bit_value': 1
    }
    
    # Correct bit value but wrong CAN ID
    data = [0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00]
    result = SignalMatcher.match_signal(signal_config, 0x123, data)
    test.test("Wrong CAN ID should not match", result, False)
    
    # Test 5: Invalid byte index
    print("\n[TEST 5] Invalid byte index")
    print("-" * 70)
    
    signal_config = {
        'can_id': 0x119,
        'match_type': 'bit',
        'byte_index': 10,  # Out of range
        'bit_index': 0,
        'bit_value': 1
    }
    
    data = [0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00]
    result = SignalMatcher.match_signal(signal_config, 0x119, data)
    test.test("Invalid byte index should not match", result, False)
    
    # Test 6: Test all 8 bits in a byte
    print("\n[TEST 6] Test all 8 bits individually")
    print("-" * 70)
    
    for bit_pos in range(8):
        signal_config = {
            'can_id': 0x119,
            'match_type': 'bit',
            'byte_index': 0,
            'bit_index': bit_pos,
            'bit_value': 1
        }
        
        # Create byte with only the specified bit set
        byte_value = 1 << bit_pos
        data = [byte_value, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        result = SignalMatcher.match_signal(signal_config, 0x119, data)
        test.test(f"Bit {bit_pos} set in byte 0 (0x{byte_value:02X})", result, True)
    
    # Test 7: Real-world scenario - monitoring bit 0 of byte 3
    print("\n[TEST 7] Real-world scenario - CAN ID 0x119, byte 3, bit 0")
    print("-" * 70)
    
    signal_config = {
        'can_id': 0x119,
        'match_type': 'bit',
        'byte_index': 3,
        'bit_index': 0,
        'bit_value': 1
    }
    
    # Various real-world data patterns
    test_cases = [
        ([0x00, 0x00, 0x00, 0x29, 0x00, 0x00, 0x00, 0x00], True, "0x29 has bit 0 set"),
        ([0x00, 0x00, 0x00, 0x2B, 0x00, 0x00, 0x00, 0x00], True, "0x2B has bit 0 set"),
        ([0x00, 0x00, 0x00, 0x28, 0x00, 0x00, 0x00, 0x00], False, "0x28 has bit 0 clear"),
        ([0x00, 0x00, 0x00, 0x2A, 0x00, 0x00, 0x00, 0x00], False, "0x2A has bit 0 clear"),
        ([0xAA, 0xBB, 0xCC, 0x01, 0xDD, 0xEE, 0xFF, 0x11], True, "Other bytes don't matter"),
    ]
    
    for data, expected, description in test_cases:
        result = SignalMatcher.match_signal(signal_config, 0x119, data)
        test.test(description, result, expected)
    
    # Summary
    print("\n" + "=" * 70)
    print(f"TESTS COMPLETED: {test.passed_count}/{test.test_count} PASSED")
    print("=" * 70)
    
    if test.passed_count == test.test_count:
        print("\n✓ All bit matching tests passed!")
        print("\nThe bit matching logic is working correctly:")
        print("  ✓ Correctly identifies individual bit values (LSB and MSB)")
        print("  ✓ Handles all bit positions (0-7)")
        print("  ✓ Correctly handles CAN ID matching")
        print("  ✓ Validates byte index bounds")
        print("  ✓ Works with real-world data patterns")
        return True
    else:
        print(f"\n✗ {test.test_count - test.passed_count} test(s) failed")
        return False


if __name__ == "__main__":
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
