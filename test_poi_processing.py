#!/usr/bin/env python3
"""
Test script to run a POI through the SocialMapper system and track file creation.
This will use the Fuquay-Varina Community Library as an example.
"""

import os
import sys
import time
from pathlib import Path
import shutil

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def track_files_before_after(output_dir):
    """Track files before and after processing to see what was created."""
    if not os.path.exists(output_dir):
        return set()
    
    files_before = set()
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            files_before.add(os.path.relpath(os.path.join(root, file), output_dir))
    
    return files_before

def get_all_files_in_dir(output_dir):
    """Get all files in a directory recursively."""
    if not os.path.exists(output_dir):
        return set()
    
    all_files = set()
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            all_files.add(os.path.relpath(os.path.join(root, file), output_dir))
    
    return all_files

def main():
    """Run a POI through the system and track file creation."""
    print("🔍 SocialMapper POI Processing Test")
    print("=" * 50)
    
    # Set up output directory
    output_dir = "test_output"
    
    # Clean up any existing output
    if os.path.exists(output_dir):
        print(f"🧹 Cleaning up existing output directory: {output_dir}")
        shutil.rmtree(output_dir)
    
    # Track files before processing
    print(f"📁 Output directory: {output_dir}")
    files_before = track_files_before_after(output_dir)
    print(f"📊 Files before processing: {len(files_before)}")
    
    # Import SocialMapper
    try:
        from socialmapper.core import run_socialmapper
        print("✅ Successfully imported SocialMapper")
    except ImportError as e:
        print(f"❌ Failed to import SocialMapper: {e}")
        return
    
    # Set up test parameters
    custom_coords_path = "examples/custom_coordinates.csv"
    
    if not os.path.exists(custom_coords_path):
        print(f"❌ Custom coordinates file not found: {custom_coords_path}")
        return
    
    print(f"📍 Using POI data from: {custom_coords_path}")
    
    # Run the processing
    print("\n🚀 Starting SocialMapper processing...")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        result = run_socialmapper(
            custom_coords_path=custom_coords_path,
            travel_time=15,
            census_variables=["total_population", "median_income"],
            output_dir=output_dir,
            export_csv=True,
            export_maps=False,  # Disable maps for streamlined output
            export_isochrones=False  # Disable isochrone files for streamlined output
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"\n✅ Processing completed successfully!")
        print(f"⏱️  Total processing time: {processing_time:.2f} seconds")
        
    except Exception as e:
        print(f"\n❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Track files after processing
    print(f"\n📊 Analyzing output files...")
    files_after = get_all_files_in_dir(output_dir)
    new_files = files_after - files_before
    
    print(f"📁 Total files created: {len(new_files)}")
    
    # Organize files by type/directory
    file_categories = {}
    for file_path in sorted(new_files):
        category = file_path.split('/')[0] if '/' in file_path else 'root'
        if category not in file_categories:
            file_categories[category] = []
        file_categories[category].append(file_path)
    
    # Display file organization
    print(f"\n📂 Files created by category:")
    for category, files in file_categories.items():
        print(f"\n  📁 {category}/ ({len(files)} files)")
        for file_path in files:
            file_full_path = os.path.join(output_dir, file_path)
            if os.path.exists(file_full_path):
                file_size = os.path.getsize(file_full_path)
                if file_size > 1024 * 1024:  # > 1MB
                    size_str = f"{file_size / (1024*1024):.1f} MB"
                elif file_size > 1024:  # > 1KB
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size} B"
                print(f"    📄 {file_path} ({size_str})")
            else:
                print(f"    📄 {file_path} (file not found)")
    
    # Display result summary
    print(f"\n📋 Processing Results Summary:")
    print(f"  🎯 POI data: {len(result.get('poi_data', {}).get('pois', []))} POIs processed")
    
    if 'isochrones' in result:
        isochrones = result['isochrones']
        if hasattr(isochrones, '__len__'):
            print(f"  🗺️  Isochrones: {len(isochrones)} generated")
    
    if 'block_groups' in result:
        block_groups = result['block_groups']
        if hasattr(block_groups, '__len__'):
            print(f"  🏘️  Block groups: {len(block_groups)} found")
    
    if 'census_data' in result:
        census_data = result['census_data']
        if hasattr(census_data, '__len__'):
            print(f"  📊 Census data: {len(census_data)} records")
    
    if 'maps' in result and result['maps']:
        print(f"  🗺️  Maps: {len(result['maps'])} generated")
    
    if 'csv_data' in result:
        print(f"  📄 CSV export: {result['csv_data']}")
    
    # Show key output files
    print(f"\n🎯 Key Output Files:")
    key_files = []
    
    # Look for CSV files
    csv_files = [f for f in new_files if f.endswith('.csv')]
    if csv_files:
        key_files.extend(csv_files)
    
    # Look for map files
    map_files = [f for f in new_files if any(ext in f for ext in ['.png', '.html', '.jpg', '.jpeg'])]
    if map_files:
        key_files.extend(map_files[:3])  # Show first 3 maps
    
    # Look for data files
    data_files = [f for f in new_files if any(ext in f for ext in ['.parquet', '.geojson', '.json'])]
    if data_files:
        key_files.extend(data_files[:3])  # Show first 3 data files
    
    for file_path in key_files:
        full_path = os.path.join(output_dir, file_path)
        print(f"  📄 {file_path}")
        print(f"     📁 {full_path}")
    
    print(f"\n🎉 Test completed successfully!")
    print(f"📁 All output files are in: {os.path.abspath(output_dir)}")
    
    return result

if __name__ == "__main__":
    main() 