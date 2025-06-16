#!/usr/bin/env python3
"""
Test script to verify the improved POI search
"""

import os
from socialmapper.query import create_poi_config, build_overpass_query, query_overpass, format_results

def test_improved_search():
    # Test with the improved query
    print("=== Testing improved query for Durham, NC ===")
    
    config = create_poi_config(
        geocode_area="Durham",
        state="NC",
        city="Durham",
        poi_type="amenity",
        poi_name="library"
    )
    
    query = build_overpass_query(config)
    print("Improved Query:")
    print(query)
    print()
    
    try:
        print("Executing query...")
        result = query_overpass(query)
        data = format_results(result, config)
        
        print(f"Found {len(data['pois'])} POIs")
        
        # Show all results with location info
        for i, poi in enumerate(data['pois']):
            name = poi.get('tags', {}).get('name', 'Unnamed')
            lat = poi.get('lat', 'N/A')
            lon = poi.get('lon', 'N/A')
            print(f"{i+1}. {name} at ({lat}, {lon})")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_search()