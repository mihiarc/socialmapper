#!/usr/bin/env python3
"""
Test script to debug POI search functionality with better state filtering
"""

import os
from socialmapper.query import create_poi_config, build_overpass_query, query_overpass, format_results

# Set up test configuration
def test_poi_search():
    # Test 1: Try with full state name
    print("=== Test 1: Full state name ===")
    config1 = create_poi_config(
        geocode_area="Durham",
        state="North Carolina",
        city="Durham",
        poi_type="amenity",
        poi_name="library"
    )
    
    query1 = build_overpass_query(config1)
    print("Query 1:")
    print(query1)
    print()
    
    # Test 2: Try with state abbreviation
    print("=== Test 2: State abbreviation ===")
    config2 = create_poi_config(
        geocode_area="Durham",
        state="NC",
        city="Durham",
        poi_type="amenity",
        poi_name="library"
    )
    
    query2 = build_overpass_query(config2)
    print("Query 2:")
    print(query2)
    print()
    
    # Test 3: Try with city, state format
    print("=== Test 3: City, State format ===")
    config3 = create_poi_config(
        geocode_area="Durham, North Carolina",
        state="North Carolina",
        city="Durham",
        poi_type="amenity",
        poi_name="library"
    )
    
    query3 = build_overpass_query(config3)
    print("Query 3:")
    print(query3)
    print()
    
    # Execute the first query and check results
    try:
        print("Executing query 1...")
        result = query_overpass(query1)
        data = format_results(result, config1)
        
        print(f"Found {len(data['pois'])} POIs")
        
        # Check if any are actually in North Carolina
        nc_pois = []
        for poi in data['pois']:
            tags = poi.get('tags', {})
            # Check if POI has state info or is in expected location
            if poi.get('lat', 0) > 35 and poi.get('lat', 0) < 37 and poi.get('lon', 0) < -77 and poi.get('lon', 0) > -80:
                nc_pois.append(poi)
        
        print(f"POIs likely in NC: {len(nc_pois)}")
        
        # Print first few NC POIs
        for i, poi in enumerate(nc_pois[:5]):
            print(f"\nNC POI {i+1}:")
            print(f"  Name: {poi.get('tags', {}).get('name', 'Unnamed')}")
            print(f"  Lat: {poi.get('lat', 'N/A')}")
            print(f"  Lon: {poi.get('lon', 'N/A')}")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_poi_search()