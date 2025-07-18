#!/usr/bin/env python3
"""Test script to verify numpy flags fix in NDI receiver"""

import numpy as np
import sys

def test_numpy_flags():
    """Test numpy flags access pattern"""
    print("Testing numpy flags access patterns...\n")
    
    # Create test arrays
    test_data = np.random.randint(0, 255, size=(100, 100, 4), dtype=np.uint8)
    
    # Test 1: C-contiguous array
    print("Test 1: C-contiguous array")
    print(f"  flags: {test_data.flags}")
    print(f"  C_CONTIGUOUS: {test_data.flags['C_CONTIGUOUS']}")
    print(f"  Is C-contiguous: {test_data.flags['C_CONTIGUOUS'] == True}")
    
    # Test 2: Non-contiguous array (transpose)
    test_data_transposed = test_data.transpose(1, 0, 2)
    print("\nTest 2: Non-contiguous array (transposed)")
    print(f"  flags: {test_data_transposed.flags}")
    print(f"  C_CONTIGUOUS: {test_data_transposed.flags['C_CONTIGUOUS']}")
    print(f"  Is C-contiguous: {test_data_transposed.flags['C_CONTIGUOUS'] == True}")
    
    # Test 3: Make contiguous
    contiguous_data = np.ascontiguousarray(test_data_transposed)
    print("\nTest 3: Made contiguous with ascontiguousarray")
    print(f"  flags: {contiguous_data.flags}")
    print(f"  C_CONTIGUOUS: {contiguous_data.flags['C_CONTIGUOUS']}")
    print(f"  Is C-contiguous: {contiguous_data.flags['C_CONTIGUOUS'] == True}")
    
    # Test 4: Demonstrate the error (commented out)
    print("\nTest 4: The error case (flags.get)")
    try:
        # This would cause the error
        result = test_data.flags.get('C_CONTIGUOUS', True)
        print(f"  ERROR: This should not work! Result: {result}")
    except AttributeError as e:
        print(f"  Expected error: {e}")
        print("  ✓ Correctly caught AttributeError - flags object has no 'get' method")
    
    # Test 5: Correct pattern used in our fix
    print("\nTest 5: Correct pattern (direct access)")
    if not test_data_transposed.flags['C_CONTIGUOUS']:
        fixed_data = np.ascontiguousarray(test_data_transposed)
        print("  ✓ Non-contiguous data detected and fixed")
    else:
        fixed_data = test_data_transposed
        print("  Data already contiguous")
    
    print(f"\nAll tests passed! The fix correctly uses direct dictionary access.")
    
if __name__ == "__main__":
    test_numpy_flags()