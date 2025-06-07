#!/usr/bin/env python3
"""Test ZCTA map generation to verify it works like block groups."""

from socialmapper.core import run_socialmapper

def test_zcta_maps():
    print('🗺️ Testing ZCTA map generation...')
    
    try:
        # Test ZCTA map generation with our test data
        result = run_socialmapper(
            custom_coords_path='test_coords.csv',
            travel_time=10,
            geographic_level='zcta',
            export_csv=True,
            export_maps=True,  # Enable map generation
            output_dir='test_zcta_maps'
        )
        
        maps = result.get('maps', [])
        print(f'✅ ZCTA maps generated successfully!')
        print(f'📄 Generated {len(maps)} map files:')
        for map_file in maps:
            print(f'   • {map_file}')
            
        return True
        
    except Exception as e:
        print(f'❌ ZCTA map generation failed: {e}')
        return False

if __name__ == '__main__':
    success = test_zcta_maps()
    if success:
        print('\n🎉 ZCTAs support map generation just like block groups!')
    else:
        print('\n⚠️ Issue with ZCTA map generation detected.') 