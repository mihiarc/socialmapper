#!/usr/bin/env python3
"""
SocialMapper Demo Script

This script demonstrates the main features of SocialMapper:
1. Analyzing demographics around libraries in a city
2. Using custom coordinates for analysis
3. Exploring neighbor functionality
4. Exporting results for further analysis

Run this script to see SocialMapper in action!
"""

import os
import json
import tempfile
import logging
from pathlib import Path

# Configure logging to the highest level (CRITICAL) - least verbose
logging.basicConfig(
    level=logging.CRITICAL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Also set the root logger to CRITICAL to ensure all modules use this level
logging.getLogger().setLevel(logging.CRITICAL)

print("🔧 Logging configured to CRITICAL level (least verbose)")

def demo_basic_poi_analysis():
    """Demo 1: Basic POI analysis - Libraries in Raleigh, NC"""
    print("=" * 60)
    print("DEMO 1: Analyzing Libraries in Raleigh, NC")
    print("=" * 60)
    
    try:
        from socialmapper import run_socialmapper
        
        print("🔍 Searching for libraries in Raleigh, NC...")
        print("📊 Analyzing demographics within 15-minute travel time")
        print("📈 Variables: Population, Income, Education")
        
        # Run the analysis
        results = run_socialmapper(
            geocode_area="Raleigh",
            state="North Carolina", 
            poi_type="amenity",
            poi_name="library",
            travel_time=15,
            census_variables=["total_population", "median_household_income", "education_bachelors_plus"],
            export_csv=True,
            export_maps=False,  # Skip maps for demo speed
            use_interactive_maps=False
        )
        
        print(f"✅ Analysis complete!")
        print(f"   • Found {results.get('poi_count', 0)} libraries")
        print(f"   • Analyzed {results.get('block_group_count', 0)} census block groups")
        print(f"   • Results saved to: {results.get('output_dir', 'output')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo 1 failed: {e}")
        return False

def demo_custom_coordinates():
    """Demo 2: Using custom coordinates"""
    print("\n" + "=" * 60)
    print("DEMO 2: Custom Coordinates Analysis")
    print("=" * 60)
    
    try:
        from socialmapper import run_socialmapper
        
        # Create a temporary CSV file with custom coordinates
        custom_coords = [
            {"id": "raleigh_downtown", "name": "Downtown Raleigh", "lat": 35.7796, "lon": -78.6382},
            {"id": "nc_state", "name": "NC State University", "lat": 35.7866, "lon": -78.6820},
            {"id": "rdu_airport", "name": "RDU Airport", "lat": 35.8776, "lon": -78.7875}
        ]
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_coords, f, indent=2)
            temp_file = f.name
        
        print("📍 Using custom coordinates:")
        for coord in custom_coords:
            print(f"   • {coord['name']} ({coord['lat']}, {coord['lon']})")
        
        print("\n🔍 Analyzing demographics within 10-minute travel time...")
        
        # Run analysis with custom coordinates
        results = run_socialmapper(
            custom_coords_path=temp_file,
            travel_time=10,
            census_variables=["total_population", "median_household_income"],
            export_csv=True,
            export_maps=False,
            use_interactive_maps=False
        )
        
        print(f"✅ Custom coordinates analysis complete!")
        print(f"   • Analyzed {len(custom_coords)} custom locations")
        print(f"   • Found {results.get('block_group_count', 0)} census block groups")
        
        # Clean up
        os.unlink(temp_file)
        return True
        
    except Exception as e:
        print(f"❌ Demo 2 failed: {e}")
        return False

def demo_neighbor_functionality():
    """Demo 3: Neighbor functionality"""
    print("\n" + "=" * 60)
    print("DEMO 3: Geographic Neighbor Analysis")
    print("=" * 60)
    
    try:
        import socialmapper.neighbors as neighbors
        
        print("🗺️  Exploring geographic relationships...")
        
        # State neighbors
        print("\n🏛️  State Neighbors:")
        nc_neighbors = neighbors.get_neighboring_states_by_abbr('NC')
        print(f"   North Carolina neighbors: {', '.join(nc_neighbors)}")
        
        ca_neighbors = neighbors.get_neighboring_states_by_abbr('CA')
        print(f"   California neighbors: {', '.join(ca_neighbors)}")
        
        # Point geocoding
        print("\n📍 Point Geocoding:")
        raleigh_geo = neighbors.get_geography_from_point(35.7796, -78.6382)
        print(f"   Raleigh, NC location:")
        print(f"     • State FIPS: {raleigh_geo['state_fips']}")
        print(f"     • County FIPS: {raleigh_geo['county_fips']}")
        
        # County neighbors
        print("\n🏘️  County Neighbors:")
        wake_neighbors = neighbors.get_neighboring_counties('37', '183')  # Wake County, NC
        print(f"   Wake County, NC has {len(wake_neighbors)} neighboring counties")
        
        # Database statistics
        print("\n📊 Database Statistics:")
        stats = neighbors.get_statistics()
        print(f"   • State relationships: {stats['state_relationships']:,}")
        print(f"   • County relationships: {stats['county_relationships']:,}")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo 3 failed: {e}")
        return False

def demo_batch_poi_processing():
    """Demo 4: Batch POI processing"""
    print("\n" + "=" * 60)
    print("DEMO 4: Batch POI Processing")
    print("=" * 60)
    
    try:
        import socialmapper.neighbors as neighbors
        
        # Sample POIs across different states
        pois = [
            {'lat': 35.7796, 'lon': -78.6382, 'name': 'Raleigh, NC'},
            {'lat': 35.2271, 'lon': -80.8431, 'name': 'Charlotte, NC'},
            {'lat': 34.0522, 'lon': -118.2437, 'name': 'Los Angeles, CA'},
            {'lat': 29.7604, 'lon': -95.3698, 'name': 'Houston, TX'},
        ]
        
        print(f"🔄 Processing {len(pois)} POIs across multiple states:")
        for poi in pois:
            print(f"   • {poi['name']}")
        
        # Get counties for POIs
        counties_only = neighbors.get_counties_from_pois(pois, include_neighbors=False)
        counties_with_neighbors = neighbors.get_counties_from_pois(pois, include_neighbors=True)
        
        print(f"\n📊 Results:")
        print(f"   • POI counties only: {len(counties_only)}")
        print(f"   • Including neighbors: {len(counties_with_neighbors)}")
        print(f"   • Expansion factor: {len(counties_with_neighbors) / len(counties_only):.1f}x")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo 4 failed: {e}")
        return False

def show_output_structure():
    """Show the output directory structure"""
    print("\n" + "=" * 60)
    print("OUTPUT DIRECTORY STRUCTURE")
    print("=" * 60)
    
    output_dir = Path("output")
    if output_dir.exists():
        print("📁 Generated files in output/:")
        
        # Show CSV files
        csv_dir = output_dir / "csv"
        if csv_dir.exists():
            csv_files = list(csv_dir.glob("*.csv"))
            if csv_files:
                print(f"\n📊 CSV Files ({len(csv_files)}):")
                for file in csv_files[:3]:  # Show first 3
                    print(f"   • {file.name}")
                if len(csv_files) > 3:
                    print(f"   • ... and {len(csv_files) - 3} more")
        
        # Show isochrone files
        iso_dir = output_dir / "isochrones"
        if iso_dir.exists():
            iso_files = list(iso_dir.glob("*.geojson"))
            if iso_files:
                print(f"\n🗺️  Isochrone Files ({len(iso_files)}):")
                for file in iso_files[:3]:
                    print(f"   • {file.name}")
                if len(iso_files) > 3:
                    print(f"   • ... and {len(iso_files) - 3} more")
        
        # Show POI files
        poi_dir = output_dir / "pois"
        if poi_dir.exists():
            poi_files = list(poi_dir.glob("*.json"))
            if poi_files:
                print(f"\n📍 POI Files ({len(poi_files)}):")
                for file in poi_files[:3]:
                    print(f"   • {file.name}")
                if len(poi_files) > 3:
                    print(f"   • ... and {len(poi_files) - 3} more")
    else:
        print("📁 No output directory found - run a demo first!")

def main():
    """Run all demonstrations"""
    print("🏘️  SocialMapper Demo Script")
    print("=" * 60)
    print("This script demonstrates the key features of SocialMapper:")
    print("• POI analysis with OpenStreetMap data")
    print("• Custom coordinate analysis") 
    print("• Geographic neighbor relationships")
    print("• Batch processing capabilities")
    print("=" * 60)
    
    # Track success of each demo
    results = {}
    
    # Run demonstrations
    print("\n🚀 Starting demonstrations...\n")
    
    results['poi_analysis'] = demo_basic_poi_analysis()
    results['custom_coords'] = demo_custom_coordinates()
    results['neighbors'] = demo_neighbor_functionality()
    results['batch_processing'] = demo_batch_poi_processing()
    
    # Show output structure
    show_output_structure()
    
    # Summary
    print("\n" + "=" * 60)
    print("DEMO SUMMARY")
    print("=" * 60)
    
    successful = sum(results.values())
    total = len(results)
    
    print(f"✅ Completed {successful}/{total} demonstrations successfully")
    
    for demo, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   • {demo.replace('_', ' ').title()}: {status}")
    
    if successful == total:
        print("\n🎉 All demonstrations completed successfully!")
        print("\n📋 Next Steps:")
        print("• Explore the output/ directory for generated files")
        print("• Try the Streamlit app: python -m socialmapper.ui.streamlit.app")
        print("• Use the CLI: socialmapper --help")
        print("• Check the documentation for more advanced usage")
    else:
        print(f"\n⚠️  {total - successful} demonstration(s) failed")
        print("• Check your environment and dependencies")
        print("• Ensure you have internet connectivity for POI queries")
        print("• Try running individual functions to debug issues")
    
    return successful == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 