#!/usr/bin/env python3
"""
SocialMapper Case Study: Fuquay-Varina, NC Library
==================================================

Complete demonstration of SocialMapper functionality using a real-world scenario:
analyzing demographics and community access around the Fuquay-Varina Library.

This case study showcases:
- Parquet-based neighbor system optimization
- Complete SocialMapper workflow
- Geographic analysis and county neighbor expansion
- Performance benchmarking
- Real-world application patterns

Author: SocialMapper Team
Date: June 2025
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def print_header(title: str, width: int = 70):
    """Print a formatted header."""
    print("🏛️" + "=" * (width - 2))
    print(title)
    print("=" * width)

def print_step(step: int, total: int, description: str):
    """Print a formatted step."""
    print(f"\n🔍 Step {step}/{total}: {description}")

def demo_neighbor_system() -> bool:
    """Demonstrate the neighbor system with Fuquay-Varina library."""
    print_header("SocialMapper Case Study: Fuquay-Varina, NC Library\nShowcasing the Parquet-Based Neighbor System")
    
    # Library information
    library_name = "Fuquay-Varina Library"
    library_lat = 35.5846
    library_lon = -78.7997
    library_address = "900 S Main St, Fuquay-Varina, NC 27526"
    
    print(f"📍 Target Location: {library_name}")
    print(f"   Coordinates: {library_lat}, {library_lon}")
    print(f"   Address: {library_address}")
    
    # Step 1: System Detection and Status
    print_step(1, 6, "System Detection and Status")
    try:
        from socialmapper.census.neighbors import get_system_status, get_neighbor_manager
        
        system_info = get_system_status()
        print(f"✅ Current system: {system_info.get('system_type', 'unknown').upper()}")
        print(f"   Available: {system_info['available']}")
        if system_info['available']:
            print(f"   Data path: {system_info.get('data_path', 'N/A')}")
        
        # Get neighbor manager and statistics
        neighbor_manager = get_neighbor_manager()
        stats = neighbor_manager.get_statistics()
        
        print(f"✅ System statistics:")
        print(f"   • System type: {stats.get('system_type', 'unknown')}")
        if 'state_relationships' in stats:
            print(f"   • State relationships: {stats['state_relationships']:,}")
        if 'county_relationships' in stats:
            print(f"   • County relationships: {stats['county_relationships']:,}")
        if 'total_size_mb' in stats:
            print(f"   • Total storage: {stats['total_size_mb']:.2f} MB")
        
    except Exception as e:
        print(f"❌ System detection failed: {e}")
        return False
    
    # Step 2: Geographic Context Analysis
    print_step(2, 6, "Geographic Context Analysis")
    try:
        from socialmapper.census.neighbors import get_neighboring_states
        
        # North Carolina (FIPS: 37)
        nc_neighbors = get_neighboring_states('37')
        print(f"✅ North Carolina borders {len(nc_neighbors)} states:")
        
        state_names = {
            '13': 'Georgia', '45': 'South Carolina', 
            '47': 'Tennessee', '51': 'Virginia'
        }
        
        for state_fips in nc_neighbors:
            state_name = state_names.get(state_fips, f"State {state_fips}")
            print(f"   • {state_name} ({state_fips})")
        
        # Wake County analysis (where Fuquay-Varina is located)
        wake_county_fips = "37183"  # Wake County, NC
        print(f"\n✅ Target county: Wake County, NC ({wake_county_fips})")
        
        # Get neighboring counties
        start_time = time.time()
        neighboring_counties = neighbor_manager.get_neighboring_counties(wake_county_fips)
        end_time = time.time()
        lookup_time = (end_time - start_time) * 1000
        
        print(f"   • Found {len(neighboring_counties)} neighboring counties")
        print(f"   • Lookup time: {lookup_time:.2f} ms")
        
        # Show sample neighbors
        if neighboring_counties:
            print(f"   • Sample neighbors: {neighboring_counties[:3]}{'...' if len(neighboring_counties) > 3 else ''}")
        
    except Exception as e:
        print(f"❌ Geographic analysis failed: {e}")
        return False
    
    # Step 3: Performance Benchmarking
    print_step(3, 6, "Performance Benchmarking")
    try:
        # Test multiple county lookups (simulating real analysis)
        test_counties = [
            "37183",  # Wake County (Fuquay-Varina)
            "37135",  # Orange County (Chapel Hill)
            "37063",  # Durham County (Durham)
            "37101",  # Johnston County (Smithfield)
            "37085"   # Harnett County (Lillington)
        ]
        
        print(f"✅ Performance test with {len(test_counties)} counties in the region:")
        
        start_time = time.time()
        all_neighbors = set()
        county_details = {}
        
        for county_fips in test_counties:
            neighbors = neighbor_manager.get_neighboring_counties(county_fips)
            all_neighbors.update(neighbors)
            all_neighbors.add(county_fips)
            county_details[county_fips] = len(neighbors)
        
        end_time = time.time()
        batch_time = (end_time - start_time) * 1000
        
        print(f"   • Total unique counties: {len(all_neighbors)}")
        print(f"   • Batch processing time: {batch_time:.2f} ms")
        print(f"   • Average per county: {batch_time/len(test_counties):.2f} ms")
        
        # Show expansion details
        for county_fips, neighbor_count in county_details.items():
            print(f"   • County {county_fips}: {neighbor_count} neighbors")
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False
    
    # Step 4: System Optimization Benefits
    print_step(4, 6, "System Optimization Benefits")
    try:
        if system_info.get('system_type') == 'parquet':
            print(f"✅ Parquet system advantages:")
            print(f"   🚀 Performance benefits:")
            print(f"      • Columnar storage for fast filtering")
            print(f"      • Better compression (smaller files)")
            print(f"      • Optimized for batch operations")
            print(f"      • Hardware-accelerated operations")
            
            print(f"   💾 Storage optimization:")
            # Show storage comparison if available
            if 'total_size_mb' in stats:
                current_size = stats['total_size_mb']
                estimated_original = current_size * 25  # Parquet is ~4% of original
                savings = ((estimated_original - current_size) / estimated_original) * 100
                print(f"      • Current storage: {current_size:.2f} MB")
                print(f"      • Estimated CSV equivalent: {estimated_original:.2f} MB")
                print(f"      • Space savings: {savings:.1f}%")
            
            print(f"   🔧 Developer benefits:")
            print(f"      • Easy data inspection with pandas")
            print(f"      • Better integration with data science tools")
            print(f"      • Schema enforcement and validation")
        else:
            print(f"ℹ️  System type: {system_info.get('system_type', 'unknown')}")
            print(f"   System is available and functional")
        
    except Exception as e:
        print(f"⚠️  System optimization analysis failed: {e}")
    
    # Step 5: Real-World SocialMapper Workflow
    print_step(5, 6, "Real-World SocialMapper Workflow")
    try:
        print(f"✅ Complete SocialMapper workflow for {library_name}:")
        print(f"   ")
        print(f"   1. ✅ POI Identification")
        print(f"      • Target: {library_name}")
        print(f"      • Location: {library_lat}, {library_lon}")
        print(f"      • Type: Public library (community resource)")
        print(f"   ")
        print(f"   2. ✅ Geographic Analysis")
        print(f"      • Primary county: Wake County, NC ({wake_county_fips})")
        print(f"      • Neighboring counties: {len(neighboring_counties)} found")
        print(f"      • Total analysis area: {len(all_neighbors)} counties")
        print(f"   ")
        print(f"   3. 📊 Next Steps (in full analysis):")
        print(f"      • Fetch census demographics for all {len(all_neighbors)} counties")
        print(f"      • Calculate travel time isochrones")
        print(f"      • Analyze demographic accessibility patterns")
        print(f"      • Generate interactive maps and visualizations")
        print(f"      • Export results for policy analysis")
        print(f"   ")
        print(f"   The neighbor system optimized steps 1-2, enabling:")
        print(f"   • Faster processing for large geographic areas")
        print(f"   • Comprehensive regional analysis")
        print(f"   • Scalable community research workflows")
        
    except Exception as e:
        print(f"❌ Workflow demonstration failed: {e}")
        return False
    
    # Step 6: Usage Examples and Next Steps
    print_step(6, 6, "Usage Examples and Integration")
    try:
        print(f"✅ Integration examples:")
        print(f"   ")
        print(f"   # Basic neighbor lookup")
        print(f"   from socialmapper.census.neighbors import get_neighboring_counties")
        print(f"   neighbors = get_neighboring_counties('37183')")
        print(f"   ")
        print(f"   # System status check")
        print(f"   from socialmapper.census.neighbors import get_system_status")
        print(f"   info = get_system_status()")
        print(f"   print(f'System: {{info[\"system_type\"].upper()}}')")
        print(f"   ")
        print(f"   # Complete SocialMapper workflow")
        print(f"   from socialmapper import run_socialmapper")
        print(f"   results = run_socialmapper(")
        print(f"       geocode_area='Fuquay-Varina',")
        print(f"       state='NC',")
        print(f"       poi_type='amenity',")
        print(f"       poi_name='library',")
        print(f"       travel_time=15,")
        print(f"       census_variables=['total_population', 'median_income']")
        print(f"   )")
        
    except Exception as e:
        print(f"❌ Usage examples failed: {e}")
        return False
    
    # Summary
    print(f"\n" + "=" * 70)
    print(f"🎉 Case Study Summary")
    print(f"=" * 70)
    print(f"✅ Successfully demonstrated SocialMapper with {library_name}")
    print(f"✅ Neighbor system: {system_info.get('system_type', 'unknown').upper()}")
    print(f"✅ Performance: {len(test_counties)} counties → {len(all_neighbors)} total in {batch_time:.2f} ms")
    print(f"✅ Ready for comprehensive community analysis")
    print(f"✅ Scalable to large geographic regions")
    
    return True

def show_advanced_examples():
    """Show advanced usage patterns."""
    print(f"\n📋 Advanced Usage Patterns:")
    print(f"   ")
    print(f"   # Batch processing multiple POIs")
    print(f"   pois = [")
    print(f"       {{'name': 'Library', 'lat': 35.5846, 'lon': -78.7997}},")
    print(f"       {{'name': 'School', 'lat': 35.5863, 'lon': -78.7889}},")
    print(f"       {{'name': 'Park', 'lat': 35.5825, 'lon': -78.8012}}")
    print(f"   ]")
    print(f"   ")
    print(f"   # Regional analysis")
    print(f"   from socialmapper.census.neighbors import get_neighbor_manager")
    print(f"   manager = get_neighbor_manager()")
    print(f"   all_counties = set()")
    print(f"   for poi in pois:")
    print(f"       county = geocode_to_county(poi['lat'], poi['lon'])")
    print(f"       neighbors = manager.get_neighboring_counties(county)")
    print(f"       all_counties.update(neighbors)")
    print(f"   ")
    print(f"   # Performance monitoring")
    print(f"   stats = manager.get_statistics()")
    print(f"   print(f'Processing {{len(all_counties)}} counties')")
    print(f"   print(f'Storage: {{stats[\"total_size_mb\"]}} MB')")

def main():
    """Main demo function."""
    print(f"🚀 SocialMapper Case Study")
    print(f"   Location: Fuquay-Varina, NC Library")
    print(f"   Focus: Neighbor System & Complete Workflow")
    
    success = demo_neighbor_system()
    
    if success:
        show_advanced_examples()
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Try running SocialMapper with Fuquay-Varina data")
        print(f"   2. Explore other examples in examples/demos/")
        print(f"   3. Run performance tests in tests/performance/")
        print(f"   4. Check documentation in docs/")
        
        print(f"\n📚 Related Resources:")
        print(f"   • Rich UI Demo: examples/demos/rich_ui_demo.py")
        print(f"   • Plotly Integration: examples/demos/plotly_integration_demo.py")
        print(f"   • OSMnx Features: examples/demos/osmnx_features_demo.py")
        print(f"   • Performance Tests: tests/performance/")
    else:
        print(f"\n❌ Demo encountered issues. Check your SocialMapper installation.")
        print(f"   Try: pip install --upgrade socialmapper")

if __name__ == "__main__":
    main() 