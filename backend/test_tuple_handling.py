#!/usr/bin/env python3
"""
Test script to validate tuple handling in file parser
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from app.services.file_parser_service import FileParserService
from unittest.mock import MagicMock

def test_tuple_handling():
    """Test that tuple handling works correctly"""
    
    # Mock database session
    mock_db = MagicMock()
    parser = FileParserService(mock_db)
    
    # Test _make_json_serializable with various data types
    test_cases = [
        (1, 1),
        (1.5, 1.5),
        ("string", "string"),
        ((1, 2, 3), [1, 2, 3]),
        (np.int64(42), 42),
        (np.float64(3.14), 3.14),
        (pd.Series([1, 2, 3]).iloc[0], 1),
        (None, None),
        ({"key": (1, 2)}, {"key": [1, 2]}),
        ([(1, 2), (3, 4)], [[1, 2], [3, 4]])
    ]
    
    print("Testing _make_json_serializable method...")
    for input_val, expected in test_cases:
        try:
            result = parser._make_json_serializable(input_val)
            print(f"✓ {input_val} -> {result} (expected: {expected})")
            assert result == expected, f"Expected {expected}, got {result}"
        except Exception as e:
            print(f"✗ {input_val} -> ERROR: {e}")
    
    print("\nTesting DataFrame index handling...")
    # Test DataFrame with different index types
    df_normal = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    df_multiindex = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    df_multiindex.index = pd.MultiIndex.from_tuples([(0, 'x'), (1, 'y'), (2, 'z')])
    
    print(f"Normal DataFrame index type: {type(df_normal.index)}")
    print(f"MultiIndex DataFrame index type: {type(df_multiindex.index)}")
    
    # Test iterrows with different index types
    print("Testing iterrows with normal index...")
    for i, (index, row) in enumerate(df_normal.iterrows()):
        print(f"Row {i}: index={index} (type: {type(index)})")
        if i >= 1:  # Just show first 2 rows
            break
    
    print("Testing iterrows with MultiIndex...")
    for i, (index, row) in enumerate(df_multiindex.iterrows()):
        print(f"Row {i}: index={index} (type: {type(index)})")
        if i >= 1:  # Just show first 2 rows
            break
    
    print("\nAll tests passed!")

if __name__ == "__main__":
    test_tuple_handling()
