#!/usr/bin/env python3
"""
Simple test to check for AttributeErrors in report generation.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.analyze_access import KansasGroceryAnalyzer

def test_report_generation():
    """Test the report generation with sample data."""
    
    # Create sample analysis dataframe
    analysis_df = pd.DataFrame({
        'census_block_group': ['200019526001', '200019527001', '200019527002'],
        'total_population': [1848.0, 887.0, 996.0],
        'median_income': [63333.0, 58333.0, 66719.0],
        'elderly_population': [406.0, 228.0, 266.0],
        'elderly_percentage': [22.0, 25.7, 26.7],
        'is_low_income': [False, False, False],
        'is_elderly_concentrated': [True, True, True],
        'has_walmart_access': [True, True, True],
        'has_grocer_access': [True, True, True],
        'has_any_access': [True, True, True],
        'classification': ['elderly_served', 'elderly_served', 'elderly_served']
    })
    
    # Create sample summary stats with potential NaN issues
    summary_stats = pd.DataFrame({
        'classification': ['elderly_served', 'well_served', 'food_desert', np.nan, 'low_income_served'],
        'total_population': [3731.0, 5000.0, 1000.0, 500.0, 2000.0],
        'block_groups': [3, 5, 1, 1, 2]
    })
    
    # Test the report generation
    print("Testing report generation with sample data...")
    
    analyzer = KansasGroceryAnalyzer()
    
    try:
        analyzer._generate_comprehensive_report(analysis_df, summary_stats)
        print("✓ Report generation successful!")
    except AttributeError as e:
        print(f"✗ AttributeError: {e}")
        print(f"  Problem with summary_stats:")
        print(summary_stats)
        raise
    except Exception as e:
        print(f"✗ Other error: {type(e).__name__}: {e}")
        raise

def test_food_desert_summary():
    """Test the food desert summary generation."""
    
    # Create summary data that might cause AttributeErrors
    results = pd.DataFrame({
        'classification': ['food_desert', 'elderly_served', np.nan, 'well_served'],
        'block_groups': [10, 20, 5, 100],
        'total_population': [1000.0, 2000.0, 500.0, 10000.0]
    })
    
    print("\nTesting food desert summary generation...")
    
    analyzer = KansasGroceryAnalyzer()
    
    try:
        analyzer._generate_food_desert_summary(results)
        print("✓ Food desert summary successful!")
    except AttributeError as e:
        print(f"✗ AttributeError: {e}")
        print(f"  Problem with results:")
        print(results)
        raise
    except Exception as e:
        print(f"✗ Other error: {type(e).__name__}: {e}")
        raise

if __name__ == "__main__":
    print("Running AttributeError tests...")
    print("=" * 60)
    
    test_report_generation()
    test_food_desert_summary()
    
    print("\n✓ All tests passed!")