#!/usr/bin/env python3
"""
Minimal test with real SocialMapper analysis - just 2 stores to run quickly.
"""

import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Create minimal test files
test_walmart = pd.DataFrame({
    'name': ['Walmart Supercenter Topeka', 'Walmart Supercenter Salina'],
    'latitude': [39.0167, 38.8397],
    'longitude': [-95.7616, -97.6086],
    'type': ['walmart', 'walmart'],
    'address': ['1501 Southwest Wanamaker Road, Topeka, KS 66604', '2900 South 9th Street, Salina, KS 67401'],
    'city': ['Topeka', 'Salina'],
    'subtype': ['supercenter', 'supercenter']
})

test_grocer = pd.DataFrame({
    'name': ['Dillons Topeka', 'Hy-Vee Salina'],
    'latitude': [39.0483, 38.8022],
    'longitude': [-95.6758, -97.6114],
    'type': ['small_grocer', 'small_grocer'],
    'address': ['2951 Southwest Wanamaker Road, Topeka, KS 66614', '2350 Planet Avenue, Salina, KS 67401'],
    'city': ['Topeka', 'Salina'],
    'subtype': ['supermarket', 'supermarket']
})

# Save test files
test_dir = project_root / "data" / "test_minimal"
test_dir.mkdir(exist_ok=True, parents=True)

test_walmart.to_csv(test_dir / "walmart_test.csv", index=False)
test_grocer.to_csv(test_dir / "grocer_test.csv", index=False)

print(f"Test files created in {test_dir}")

# Now run a modified analysis
from src.analysis.analyze_access import KansasGroceryAnalyzer

class TestAnalyzer(KansasGroceryAnalyzer):
    """Modified analyzer that uses test files."""
    
    def __init__(self):
        super().__init__(
            data_dir=test_dir,
            output_dir=test_dir / "output"
        )
        # Reduce travel times for faster testing
        self.walmart_travel_time = 10  # minutes
        self.small_grocer_travel_time = 5  # minutes
    
    def analyze_walmart_access(self):
        """Override to use test file."""
        # Temporarily rename our test file
        import shutil
        test_file = self.data_dir / "walmart_test.csv"
        target_file = self.data_dir / "walmart_cleaned.csv"
        
        if target_file.exists():
            target_file.unlink()
        shutil.copy(test_file, target_file)
        
        return super().analyze_walmart_access()
    
    def analyze_small_grocer_access(self):
        """Override to use test file."""
        import shutil
        test_file = self.data_dir / "grocer_test.csv"
        target_file = self.data_dir / "small_grocers_all.csv"
        
        if target_file.exists():
            target_file.unlink()
        shutil.copy(test_file, target_file)
        
        return super().analyze_small_grocer_access()

if __name__ == "__main__":
    print("\nRunning minimal real analysis with 2 Walmarts and 2 grocers...")
    print("This should complete quickly and show any AttributeErrors")
    print("=" * 60)
    
    analyzer = TestAnalyzer()
    
    try:
        analyzer.run_full_analysis()
        print("\n✓ Analysis completed successfully!")
    except Exception as e:
        print(f"\n✗ Error during analysis: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
        # Check log file
        log_files = list((project_root / "logs").glob("*.log"))
        if log_files:
            latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
            print(f"\nCheck log file for details: {latest_log}")
            
            # Show last 50 lines of log
            print("\nLast 50 lines of log:")
            print("-" * 60)
            with open(latest_log, 'r') as f:
                lines = f.readlines()
                for line in lines[-50:]:
                    print(line.rstrip())