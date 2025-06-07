#!/usr/bin/env python3
"""Quick test of ZCTA feature to verify it works."""

from socialmapper.core import run_socialmapper
from pathlib import Path

def main():
    # Create simple test data
    test_data = '''name,lat,lon,type
Test Library,47.6062,-122.3321,library'''
    
    Path('test_coords.csv').write_text(test_data)
    
    print('🧪 Testing ZCTA feature...')
    
    try:
        result = run_socialmapper(
            custom_coords_path='test_coords.csv',
            travel_time=10, 
            geographic_level='zcta',
            export_csv=True,
            export_maps=False,
            output_dir='test_output_zcta'
        )
        
        print('✅ ZCTA test completed successfully!')
        print(f'Found {len(result.get("geographic_units", []))} ZCTAs')
        print(f'Output saved to: test_output_zcta/')
        
        return True
        
    except Exception as e:
        print(f'❌ ZCTA test failed: {e}')
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 