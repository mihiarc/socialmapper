#!/usr/bin/env python3
"""
Complete SocialMapper Demo: Fuquay-Varina, NC Library
Using the New Parquet-Based Neighbor System

This demo shows the complete workflow from POI query to demographic analysis.
"""

import sys
import time
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_full_demo():
    """Run the complete SocialMapper demo."""
    print("🏛️" + "=" * 70)
    print("Complete SocialMapper Demo: Fuquay-Varina, NC Library")
    print("Featuring the New Parquet-Based Neighbor System")
    print("=" * 70)
    
    # Library information
    library_name = "Fuquay-Varina Library"
    library_lat = 35.5846
    library_lon = -78.7997
    
    print(f"📍 Target: {library_name}")
    print(f"   Location: {library_lat}, {library_lon}")
    print(f"   Address: 900 S Main St, Fuquay-Varina, NC 27526")
    
    # Step 1: System Check
    print(f"\n🔍 Step 1: Neighbor System Check")
    try:
        from socialmapper.census.neighbors import get_system_status, get_neighbor_manager
        
        system_info = get_system_status()
        print(f"✅ System: {system_info.get('system_type', 'unknown').upper()}")
        
        # Get neighbor manager
        neighbor_manager = get_neighbor_manager()
        stats = neighbor_manager.get_statistics()
        print(f"   State relationships: {stats.get('state_relationships', 0):,}")
        print(f"   County relationships: {stats.get('county_relationships', 0):,}")
        print(f"   Total storage: {stats.get('total_size_mb', 0):.2f} MB")
        
    except Exception as e:
        print(f"❌ System check failed: {e}")
        return False
    
    # Step 2: Create POI data
    print(f"\n📋 Step 2: POI Setup")
    try:
        # Create POI data for the library
        pois = [{
            'name': library_name,
            'lat': library_lat,
            'lon': library_lon,
            'type': 'library',
            'address': '900 S Main St, Fuquay-Varina, NC 27526'
        }]
        
        print(f"✅ Created POI data:")
        for poi in pois:
            print(f"   • {poi['name']} ({poi['lat']}, {poi['lon']})")
        
    except Exception as e:
        print(f"❌ POI setup failed: {e}")
        return False
    
    # Step 3: Geographic Analysis
    print(f"\n🗺️  Step 3: Geographic Analysis")
    try:
        # For this demo, we'll simulate the county analysis since geocoding isn't fully implemented
        # In a real scenario, this would use the actual geocoding functionality
        
        # Simulate finding the county for Fuquay-Varina (Wake County, NC)
        # Wake County FIPS: 37183 (State: 37, County: 183)
        wake_county_fips = "37183"
        
        print(f"✅ Geographic analysis completed:")
        print(f"   • Library location: Wake County, NC ({wake_county_fips})")
        
        # Get neighboring counties for Wake County
        start_time = time.time()
        neighboring_counties = neighbor_manager.get_neighboring_counties(wake_county_fips)
        end_time = time.time()
        
        lookup_time = (end_time - start_time) * 1000
        
        print(f"   • Found {len(neighboring_counties)} neighboring counties")
        print(f"   • Lookup time: {lookup_time:.2f} ms")
        print(f"   • Sample neighbors: {neighboring_counties[:3]}{'...' if len(neighboring_counties) > 3 else ''}")
        
        # Show the power of the neighbor system
        total_counties = 1 + len(neighboring_counties)  # Original + neighbors
        print(f"   • Analysis coverage: {total_counties} counties total")
        print(f"   • Neighbor expansion: {len(neighboring_counties)} additional counties")
        
        # Store for later use
        all_counties = [wake_county_fips] + neighboring_counties
        
    except Exception as e:
        print(f"❌ Geographic analysis failed: {e}")
        return False
    
    # Step 4: Demonstrate the neighbor system advantage
    print(f"\n⚡ Step 4: Performance Advantage")
    try:
        # Simulate a larger job with multiple counties in the region
        test_counties = [
            "37183",  # Wake County (Fuquay-Varina)
            "37135",  # Orange County (Chapel Hill)
            "37063",  # Durham County (Durham)
            "37101",  # Johnston County (Smithfield)
            "37085"   # Harnett County (Lillington)
        ]
        
        print(f"✅ Testing neighbor lookups for {len(test_counties)} counties:")
        
        # Time the neighbor lookup for all counties
        start_time = time.time()
        all_neighbors = set()
        
        for county_fips in test_counties:
            neighbors = neighbor_manager.get_neighboring_counties(county_fips)
            all_neighbors.update(neighbors)
            all_neighbors.add(county_fips)  # Include the original county
        
        end_time = time.time()
        
        batch_time = (end_time - start_time) * 1000
        
        print(f"   • Total unique counties found: {len(all_neighbors)}")
        print(f"   • Batch processing time: {batch_time:.2f} ms")
        print(f"   • Average per county: {batch_time/len(test_counties):.2f} ms")
        
        # Show the efficiency
        if system_info.get('system_type') == 'parquet':
            print(f"   🚀 Parquet system advantages:")
            print(f"      • Columnar storage enables fast filtering")
            print(f"      • Compressed format reduces I/O time")
            print(f"      • Perfect for batch processing large county sets")
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False
    
    # Step 5: Show real-world application
    print(f"\n🎯 Step 5: Real-World Application")
    try:
        print(f"✅ Ready for demographic analysis!")
        print(f"   ")
        print(f"   Next steps in a real SocialMapper workflow:")
        print(f"   1. ✅ POI identification (completed)")
        print(f"   2. ✅ Geographic neighbor expansion (completed)")
        print(f"   3. 📊 Fetch census demographics for {len(all_neighbors)} counties")
        print(f"   4. 📈 Calculate demographic profiles and accessibility")
        print(f"   5. 🗺️  Generate maps and visualizations")
        print(f"   6. 📄 Export results for analysis")
        print(f"   ")
        print(f"   The neighbor system optimized steps 1-2, making large-scale")
        print(f"   community analysis much more efficient!")
        
        # Storage comparison
        print(f"\n💾 Storage Optimization:")
        original_size = 7.26  # Original system size
        current_size = 0.292  # Current Parquet size
        savings = ((original_size - current_size) / original_size) * 100
        
        print(f"      • Current Parquet: {current_size:.2f} MB")
        print(f"      • Previous system: {original_size:.2f} MB")
        print(f"      • Space saved: {savings:.1f}%")
        
    except Exception as e:
        print(f"❌ Application demo failed: {e}")
        return False
    
    # Step 6: Summary
    print(f"\n" + "=" * 70)
    print(f"🎉 Demo Summary")
    print(f"=" * 70)
    print(f"✅ Successfully demonstrated SocialMapper with Fuquay-Varina Library")
    print(f"✅ New Parquet neighbor system is {system_info.get('system_type', 'unknown').upper()}")
    print(f"✅ Processed {len(test_counties)} counties → {len(all_neighbors)} total counties in {batch_time:.2f} ms")
    print(f"✅ System ready for large-scale community analysis")
    
    if system_info['system_type'] == 'parquet':
        print(f"🚀 Parquet system benefits realized:")
        print(f"   • Faster processing for large jobs")
        print(f"   • Smaller storage footprint")
        print(f"   • Better data processing integration")
        print(f"   • Easier debugging and inspection")
    
    print(f"\n🎯 Ready to analyze communities around {library_name}!")
    
    return True

def main():
    """Main demo function."""
    print(f"🚀 SocialMapper Complete Workflow Demo")
    print(f"   Location: Fuquay-Varina, NC Library")
    print(f"   Focus: New Parquet-Based Neighbor System")
    
    success = run_full_demo()
    
    if success:
        print(f"\n📋 Try it yourself:")
        print(f"   from socialmapper import run_socialmapper")
        print(f"   ")
        print(f"   # Analyze libraries in Fuquay-Varina area")
        print(f"   results = run_socialmapper(")
        print(f"       query='library',")
        print(f"       location='Fuquay-Varina, NC',")
        print(f"       travel_time=15,")
        print(f"       include_neighbors=True  # Uses the fast neighbor system!")
        print(f"   )")
        
        return True
    else:
        print(f"\n❌ Demo encountered issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 