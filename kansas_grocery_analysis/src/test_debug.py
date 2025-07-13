#!/usr/bin/env python3
"""
Quick test script with minimal locations for debugging.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Monkey patch the analyzer to use test files
from analysis.analyze_access import KansasGroceryAnalyzer

# Override the data files
original_init = KansasGroceryAnalyzer.__init__

def patched_init(self, data_dir=None, output_dir=None):
    # Call original init
    original_init(self, data_dir, output_dir)
    
    # Override output directory to avoid overwriting real results
    self.output_dir = Path(__file__).parent.parent / "data" / "test_output"
    self.output_dir.mkdir(exist_ok=True, parents=True)
    
    print(f"[TEST MODE] Output directory: {self.output_dir}")

# Apply the patch
KansasGroceryAnalyzer.__init__ = patched_init

# Override the analyze methods to use test files
original_walmart_analyze = KansasGroceryAnalyzer.analyze_walmart_access
original_grocer_analyze = KansasGroceryAnalyzer.analyze_small_grocer_access

def test_walmart_analyze(self):
    """Use test Walmart file."""
    # Use the project root to find the test file
    test_file = project_root / "data" / "input" / "test_walmart_few.csv"
    if not test_file.exists():
        print(f"[ERROR] Test file not found: {test_file}")
        return None
    
    # Backup original paths
    orig_cleaned = self.data_dir / "walmart_cleaned.csv"
    orig_all = self.data_dir / "walmart_all.csv"
    
    # Temporarily rename files
    import shutil
    if orig_cleaned.exists():
        shutil.move(orig_cleaned, orig_cleaned.with_suffix('.csv.bak'))
    if orig_all.exists():
        shutil.move(orig_all, orig_all.with_suffix('.csv.bak'))
    
    # Copy test file
    shutil.copy(test_file, orig_cleaned)
    
    try:
        # Run original analysis
        result = original_walmart_analyze(self)
    finally:
        # Restore original files
        if orig_cleaned.exists():
            orig_cleaned.unlink()
        if orig_cleaned.with_suffix('.csv.bak').exists():
            shutil.move(orig_cleaned.with_suffix('.csv.bak'), orig_cleaned)
        if orig_all.with_suffix('.csv.bak').exists():
            shutil.move(orig_all.with_suffix('.csv.bak'), orig_all)
    
    return result

def test_grocer_analyze(self):
    """Use test grocer file."""
    # Use the project root to find the test file
    test_file = project_root / "data" / "input" / "test_grocers_few.csv"
    if not test_file.exists():
        print(f"[ERROR] Test file not found: {test_file}")
        return None
    
    # Backup original
    orig_file = self.data_dir / "small_grocers_all.csv"
    
    import shutil
    if orig_file.exists():
        shutil.move(orig_file, orig_file.with_suffix('.csv.bak'))
    
    # Copy test file
    shutil.copy(test_file, orig_file)
    
    try:
        # Run original analysis
        result = original_grocer_analyze(self)
    finally:
        # Restore original
        if orig_file.exists():
            orig_file.unlink()
        if orig_file.with_suffix('.csv.bak').exists():
            shutil.move(orig_file.with_suffix('.csv.bak'), orig_file)
    
    return result

# Apply patches
KansasGroceryAnalyzer.analyze_walmart_access = test_walmart_analyze
KansasGroceryAnalyzer.analyze_small_grocer_access = test_grocer_analyze

# Now run the analysis
if __name__ == "__main__":
    print("\n[TEST MODE] Running analysis with 5 Walmarts and 5 small grocers")
    print("=" * 60)
    
    from analysis.analyze_access import main
    main()