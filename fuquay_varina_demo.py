#!/usr/bin/env python3
"""
Fast Demo: Fuquay-Varina, NC Library Analysis
Using SocialMapper's New Parquet-Based Neighbor System

This demo shows how the new neighbor system optimizes large-scale processing
by analyzing demographics around the Fuquay-Varina library.
"""

import sys
import time
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def demo_neighbor_system():
    """Demo the neighbor system with Fuquay-Varina library."""
    print("🏛️" + "=" * 60)
    print("SocialMapper Demo: Fuquay-Varina, NC Library")
    print("Showcasing the New Parquet-Based Neighbor System")
    print("=" * 60)
    
    # Fuquay-Varina library coordinates
    library_lat = 35.5846
    library_lon = -78.7997
    
    print(f"📍 Target: Fuquay-Varina Library")
    print(f"   Location: {library_lat}, {library_lon}")
    print(f"   Address: 900 S Main St, Fuquay-Varina, NC 27526")
    
    # Test system detection
    print(f"\n🔍 Step 1: System Detection")
    try:
        from socialmapper.census.neighbors import get_system_status
        
        system_info = get_system_status()
        print(f"✅ Current system: {system_info.get('system_type', 'unknown').upper()}")
        print(f"   Available: {system_info['available']}")
        if system_info['available']:
            print(f"   Data path: {system_info.get('data_path', 'N/A')}")
        
    except Exception as e:
        print(f"❌ System detection failed: {e}")
        return False
    
    # Test neighbor lookups
    print(f"\n🗺️  Step 2: Geographic Context")
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
        
    except Exception as e:
        print(f"❌ Neighbor lookup failed: {e}")
        return False
    
    # Test performance comparison
    print(f"\n⚡ Step 3: Performance Test")
    try:
        from socialmapper.census.neighbors import get_neighbor_manager
        
        manager = get_neighbor_manager()
        
        # Time multiple lookups
        test_states = ['37', '13', '45', '47', '51']  # NC and neighbors
        
        start_time = time.time()
        total_neighbors = 0
        
        for state_fips in test_states:
            neighbors = manager.get_neighboring_states(state_fips)
            total_neighbors += len(neighbors)
        
        end_time = time.time()
        lookup_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        print(f"✅ Performance test completed:")
        print(f"   • Looked up {len(test_states)} states")
        print(f"   • Found {total_neighbors} neighbor relationships")
        print(f"   • Time: {lookup_time:.2f} ms")
        print(f"   • Average: {lookup_time/len(test_states):.2f} ms per lookup")
        
        # Show system type advantage
        if manager.system_type == 'parquet':
            print(f"   🚀 Using optimized Parquet system!")
            print(f"      • Columnar storage for fast filtering")
            print(f"      • Better compression (smaller files)")
            print(f"      • Ideal for large-scale processing")
        else:
            print(f"   ⚠️  System type: {manager.system_type}")
            print(f"      • Performance may vary")
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False
    
    # Show statistics
    print(f"\n📊 Step 4: System Statistics")
    try:
        stats = manager.get_statistics()
        
        print(f"✅ Neighbor database statistics:")
        print(f"   • System type: {stats.get('system_type', 'unknown')}")
        if 'state_relationships' in stats:
            print(f"   • State relationships: {stats['state_relationships']:,}")
        if 'county_relationships' in stats:
            print(f"   • County relationships: {stats['county_relationships']:,}")
        if 'cross_state_county_relationships' in stats:
            print(f"   • Cross-state counties: {stats['cross_state_county_relationships']:,}")
        if 'cached_points' in stats:
            print(f"   • Cached points: {stats['cached_points']:,}")
        
        if 'total_size_mb' in stats:
            print(f"   • Total storage: {stats['total_size_mb']:.2f} MB")
        
    except Exception as e:
        print(f"❌ Statistics failed: {e}")
        return False
    
    # Demonstrate system readiness
    print(f"\n🔄 Step 5: System Status")
    try:
        if system_info.get('system_type') == 'parquet':
            print(f"✅ Using optimized Parquet format!")
            print(f"   Your system is ready for large-scale processing")
            print(f"   Benefits:")
            print(f"   • Efficient columnar storage")
            print(f"   • Fast filtering and processing")
            print(f"   • Better compression")
            print(f"   • Easy data inspection")
        else:
            print(f"ℹ️  System type: {system_info.get('system_type', 'unknown')}")
            print(f"   System is available and functional")
        
    except Exception as e:
        print(f"⚠️  System status check failed: {e}")
    
    # Show real-world application
    print(f"\n🎯 Step 6: Real-World Application")
    print(f"✅ Ready for SocialMapper analysis!")
    print(f"   ")
    print(f"   Example workflow for Fuquay-Varina library:")
    print(f"   1. Query POIs around library location")
    print(f"   2. Get counties for POIs + neighbors (fast lookup)")
    print(f"   3. Fetch demographics for all counties")
    print(f"   4. Analyze community connections")
    print(f"   ")
    print(f"   The neighbor system optimizes step 2, making large")
    print(f"   jobs with many POIs much faster!")
    
    print(f"\n" + "=" * 60)
    print(f"🎉 Demo completed successfully!")
    print(f"   The neighbor system is working and ready for use.")
    print(f"=" * 60)
    
    return True

def show_migration_demo():
    """Show system usage examples."""
    print(f"\n📋 System Usage Examples:")
    print(f"   ")
    print(f"   # Check current system")
    print(f"   from socialmapper.census.neighbors import get_system_status")
    print(f"   info = get_system_status()")
    print(f"   print(info['system_type'])")
    print(f"   ")
    print(f"   # Use neighbor functions")
    print(f"   from socialmapper.census.neighbors import get_neighboring_states")
    print(f"   neighbors = get_neighboring_states('37')  # North Carolina")
    print(f"   print(neighbors)")
    print(f"   ")
    print(f"   # Custom manager")
    print(f"   from socialmapper.census.neighbors import get_neighbor_manager")
    print(f"   manager = get_neighbor_manager('/custom/path')")

def main():
    """Main demo function."""
    print(f"🚀 SocialMapper Neighbor System Demo")
    print(f"   Featuring: Fuquay-Varina, NC Library")
    
    success = demo_neighbor_system()
    
    if success:
        show_migration_demo()
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Try running your existing SocialMapper workflows")
        print(f"   2. Notice improved performance with large POI sets")
        print(f"   3. Explore the neighbor system API for custom analysis")
        print(f"   4. Enjoy faster community analysis!")
        
        return True
    else:
        print(f"\n❌ Demo encountered issues.")
        print(f"   Please check the error messages above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 