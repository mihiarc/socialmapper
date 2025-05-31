#!/usr/bin/env python3
"""
Demonstration of SocialMapper's streamlined output approach.
This script shows the difference between the old approach (with all outputs) 
and the new streamlined approach (CSV only).
"""

import os
import time
import shutil
from pathlib import Path
from socialmapper.core import run_socialmapper

def count_files_in_directory(directory):
    """Count all files in a directory recursively."""
    if not os.path.exists(directory):
        return 0
    
    count = 0
    for root, dirs, files in os.walk(directory):
        count += len(files)
    return count

def get_directory_size(directory):
    """Get total size of directory in bytes."""
    if not os.path.exists(directory):
        return 0
    
    total_size = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.exists(file_path):
                total_size += os.path.getsize(file_path)
    return total_size

def format_size(size_bytes):
    """Format bytes as human readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def main():
    """Demonstrate the difference between old and new approaches."""
    
    print("🚀 SocialMapper Output Comparison Demo")
    print("=" * 60)
    
    # Use the same POI for both tests
    custom_coords_path = "examples/custom_coordinates.csv"
    
    # Test 1: Old approach with all outputs
    print("\n📊 Test 1: Old Approach (All Outputs)")
    print("-" * 40)
    
    old_output_dir = "demo_output_old"
    if os.path.exists(old_output_dir):
        shutil.rmtree(old_output_dir)
    
    start_time = time.time()
    
    result_old = run_socialmapper(
        custom_coords_path=custom_coords_path,
        travel_time=15,
        census_variables=["total_population", "median_income"],
        output_dir=old_output_dir,
        export_csv=True,
        export_maps=True,
        export_isochrones=True
    )
    
    old_time = time.time() - start_time
    old_file_count = count_files_in_directory(old_output_dir)
    old_size = get_directory_size(old_output_dir)
    
    print(f"⏱️  Processing time: {old_time:.1f} seconds")
    print(f"📁 Files created: {old_file_count}")
    print(f"💾 Total size: {format_size(old_size)}")
    
    # Test 2: New streamlined approach (CSV only)
    print("\n📈 Test 2: New Streamlined Approach (CSV Only)")
    print("-" * 40)
    
    new_output_dir = "demo_output_new"
    if os.path.exists(new_output_dir):
        shutil.rmtree(new_output_dir)
    
    start_time = time.time()
    
    result_new = run_socialmapper(
        custom_coords_path=custom_coords_path,
        travel_time=15,
        census_variables=["total_population", "median_income"],
        output_dir=new_output_dir,
        export_csv=True,
        export_maps=False,
        export_isochrones=False
    )
    
    new_time = time.time() - start_time
    new_file_count = count_files_in_directory(new_output_dir)
    new_size = get_directory_size(new_output_dir)
    
    print(f"⏱️  Processing time: {new_time:.1f} seconds")
    print(f"📁 Files created: {new_file_count}")
    print(f"💾 Total size: {format_size(new_size)}")
    
    # Comparison
    print("\n📊 Comparison Results")
    print("=" * 60)
    
    time_savings = old_time - new_time
    time_savings_pct = (time_savings / old_time) * 100
    
    file_reduction = old_file_count - new_file_count
    file_reduction_pct = (file_reduction / old_file_count) * 100 if old_file_count > 0 else 0
    
    size_reduction = old_size - new_size
    size_reduction_pct = (size_reduction / old_size) * 100 if old_size > 0 else 0
    
    print(f"⚡ Time savings: {time_savings:.1f}s ({time_savings_pct:.1f}% faster)")
    print(f"📁 File reduction: {file_reduction} files ({file_reduction_pct:.1f}% fewer)")
    print(f"💾 Size reduction: {format_size(size_reduction)} ({size_reduction_pct:.1f}% smaller)")
    
    print("\n✅ Key Benefits of Streamlined Approach:")
    print("   • Faster processing (no map generation overhead)")
    print("   • Minimal disk usage (only essential CSV output)")
    print("   • Same analytical data quality")
    print("   • Can still generate maps/isochrones when needed")
    print("   • Perfect for large-scale batch processing")
    
    print("\n📄 Essential Output (Both Approaches):")
    print(f"   • CSV file with {len(result_new.get('census_data', []))} census records")
    print("   • Travel distances and demographic data")
    print("   • Geographic identifiers for further analysis")
    
    print("\n🎯 Recommendation:")
    print("   Use streamlined approach (CSV only) for:")
    print("   • Large datasets with many POIs")
    print("   • Batch processing workflows")
    print("   • Data analysis pipelines")
    print("   • When storage space is limited")
    print()
    print("   Enable maps/isochrones only when:")
    print("   • Creating presentations or reports")
    print("   • Exploring individual POI patterns")
    print("   • Need visual validation of results")
    
    print(f"\n📁 Output directories:")
    print(f"   Old approach: {os.path.abspath(old_output_dir)}")
    print(f"   New approach: {os.path.abspath(new_output_dir)}")

if __name__ == "__main__":
    main() 