"""
Unit tests for configuration loader with bit match type.

This test validates that the configuration loader correctly parses and validates
bit match type configurations.
"""

import sys
import traceback
from config.config_loader import ConfigurationLoader


def run_tests():
    """Run configuration loader tests for bit match type."""
    print("=" * 70)
    print("CONFIGURATION LOADER - BIT MATCH TYPE TESTS")
    print("=" * 70)
    
    # Test 1: Load configurations.json and verify bit match type is valid
    print("\n[TEST 1] Load configurations.json and validate bit match type")
    print("-" * 70)
    
    loader = ConfigurationLoader("configurations.json")
    configs = loader.load_configurations()
    
    assert len(configs) > 0, "No configurations loaded"
    print(f"✓ Loaded {len(configs)} configuration(s)")
    
    # Find Configuration 1
    config1 = next((config for config in configs if config.get('name') == 'Configuration 1'), None)
    
    assert config1 is not None, "Configuration 1 not found"
    print("✓ Found Configuration 1")
    
    # Verify Signal 1 is bit match type
    signal1 = config1['signals'][0]
    assert signal1.get('name') == 'Signal 1', "Signal 1 not found"
    assert signal1.get('match_type') == 'bit', "Signal 1 should be bit match type"
    print("✓ Signal 1 has match_type = 'bit'")
    
    # Verify required fields are present and parsed
    assert signal1.get('can_id') == 0x119, f"CAN ID should be 0x119, got {signal1.get('can_id')}"
    print(f"✓ CAN ID correctly parsed: 0x{signal1.get('can_id'):03X}")
    
    assert signal1.get('byte_index') == 3, "byte_index should be 3"
    print("✓ byte_index = 3")
    
    assert signal1.get('bit_index') == 0, "bit_index should be 0"
    print("✓ bit_index = 0")
    
    assert signal1.get('bit_value') == 1, "bit_value should be 1"
    print("✓ bit_value = 1")
    
    # Test 2: Validate bit match type configuration
    print("\n[TEST 2] Validate bit match type configuration")
    print("-" * 70)
    
    assert loader.validate_configuration(config1), "Configuration 1 should be valid"
    print("✓ Configuration 1 is valid")
    
    # Test 3: Test validation with missing fields
    print("\n[TEST 3] Test validation with missing required fields")
    print("-" * 70)
    
    # Missing byte_index
    invalid_signal = {
        'name': 'Configuration 1',
        'signals': [{
            'name': 'Test Signal',
            'can_id': 0x119,
            'match_type': 'bit',
            'bit_index': 0,
            'bit_value': 1
            # Missing byte_index
        }]
    }
    assert not loader.validate_configuration(invalid_signal), "Should be invalid without byte_index"
    print("✓ Correctly rejects configuration missing byte_index")
    
    # Missing bit_index
    invalid_signal = {
        'name': 'Configuration 1',
        'signals': [{
            'name': 'Test Signal',
            'can_id': 0x119,
            'match_type': 'bit',
            'byte_index': 3,
            'bit_value': 1
            # Missing bit_index
        }]
    }
    assert not loader.validate_configuration(invalid_signal), "Should be invalid without bit_index"
    print("✓ Correctly rejects configuration missing bit_index")
    
    # Missing bit_value
    invalid_signal = {
        'name': 'Configuration 1',
        'signals': [{
            'name': 'Test Signal',
            'can_id': 0x119,
            'match_type': 'bit',
            'byte_index': 3,
            'bit_index': 0
            # Missing bit_value
        }]
    }
    assert not loader.validate_configuration(invalid_signal), "Should be invalid without bit_value"
    print("✓ Correctly rejects configuration missing bit_value")
    
    # Test 4: Test with valid bit match configuration
    print("\n[TEST 4] Test validation with complete bit match configuration")
    print("-" * 70)
    
    valid_signal = {
        'name': 'Test Configuration',
        'signals': [{
            'name': 'Test Signal',
            'can_id': 0x119,
            'match_type': 'bit',
            'byte_index': 3,
            'bit_index': 0,
            'bit_value': 1
        }]
    }
    assert loader.validate_configuration(valid_signal), "Should be valid with all required fields"
    print("✓ Correctly validates complete bit match configuration")
    
    # Test 5: Test hex string parsing for bit fields
    print("\n[TEST 5] Test hex string parsing for bit fields")
    print("-" * 70)
    
    # Create a temporary config with hex strings
    import json
    import tempfile
    import os
    
    test_config = {
        "configurations": [{
            "name": "Hex Test",
            "signals": [{
                "name": "Hex Signal",
                "can_id": "0x119",
                "match_type": "bit",
                "byte_index": "0x03",
                "bit_index": "0x00",
                "bit_value": "0x01"
            }]
        }]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_config, f)
        temp_file = f.name
    
    try:
        loader2 = ConfigurationLoader(temp_file)
        configs2 = loader2.load_configurations()
        signal = configs2[0]['signals'][0]
        
        assert signal['can_id'] == 0x119, f"CAN ID should be 0x119, got {signal['can_id']}"
        assert signal['byte_index'] == 3, f"byte_index should be 3, got {signal['byte_index']}"
        assert signal['bit_index'] == 0, f"bit_index should be 0, got {signal['bit_index']}"
        assert signal['bit_value'] == 1, f"bit_value should be 1, got {signal['bit_value']}"
        
        print("✓ Hex strings correctly parsed for all bit fields")
    finally:
        os.unlink(temp_file)
    
    # Summary
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
    print("\nConfiguration loader correctly handles bit match type:")
    print("  ✓ Loads and parses bit match configurations")
    print("  ✓ Validates required fields (byte_index, bit_index, bit_value)")
    print("  ✓ Rejects configurations with missing fields")
    print("  ✓ Supports hex string notation for all fields")
    

if __name__ == "__main__":
    try:
        run_tests()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
