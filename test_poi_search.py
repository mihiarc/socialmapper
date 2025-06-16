#!/usr/bin/env python3
"""
Test script to debug POI search functionality
"""

import os
from socialmapper.query import create_poi_config, build_overpass_query, query_overpass, format_results

# Set up test configuration
def test_poi_search():
    # Create a simple POI configuration
    config = create_poi_config(
        geocode_area="Durham",
        state="North Carolina",
        city="Durham",
        poi_type="amenity",
        poi_name="library"
    )
    
    print("POI Configuration:")
    print(config)
    print()
    
    # Build the Overpass query
    query = build_overpass_query(config)
    print("Overpass Query:")
    print(query)
    print()
    
    # Try to execute the query
    try:
        print("Executing query...")
        result = query_overpass(query)
        
        # Format results
        data = format_results(result, config)
        
        print(f"Found {len(data['pois'])} POIs")
        
        # Print first few POIs
        for i, poi in enumerate(data['pois'][:5]):
            print(f"\nPOI {i+1}:")
            print(f"  Name: {poi.get('tags', {}).get('name', 'Unnamed')}")
            print(f"  Lat: {poi.get('lat', 'N/A')}")
            print(f"  Lon: {poi.get('lon', 'N/A')}")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_poi_search()