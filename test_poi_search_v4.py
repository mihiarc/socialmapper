#!/usr/bin/env python3
"""
Test script to find the correct area for Durham, NC
"""

import overpy

def test_find_durham_nc():
    api = overpy.Overpass()
    
    # First, let's find what areas exist for Durham in NC
    query = """
[out:json];
area["ISO3166-2"="US-NC"]->.state;
area[name~"Durham"](area.state);
out tags;
"""
    
    print("=== Finding Durham areas in North Carolina ===")
    print("Query:")
    print(query)
    
    try:
        result = api.query(query)
        print(f"\nFound {len(result.areas)} areas")
        
        for area in result.areas:
            print(f"\nArea ID: {area.id}")
            print(f"Tags: {area.tags}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Now let's try a working query for Durham, NC libraries
    print("\n\n=== Testing working query for Durham, NC libraries ===")
    
    # Use a more specific query that should work
    query2 = """
[out:json];
area["ISO3166-2"="US-NC"]->.state;
(
  node["amenity"="library"](area.state);
  way["amenity"="library"](area.state);
  relation["amenity"="library"](area.state);
);
out center;
"""
    
    print("Query:")
    print(query2)
    
    try:
        result = api.query(query2)
        total = len(result.nodes) + len(result.ways) + len(result.relations)
        print(f"\nFound {total} libraries in North Carolina")
        
        # Filter for Durham area (approximate coordinates)
        durham_libs = []
        for node in result.nodes:
            if 35.9 < node.lat < 36.1 and -79.0 < node.lon < -78.8:
                durham_libs.append((node.tags.get('name', 'Unnamed'), node.lat, node.lon))
        
        print(f"\nLibraries in Durham area: {len(durham_libs)}")
        for name, lat, lon in durham_libs[:5]:
            print(f"  - {name} at ({lat}, {lon})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_find_durham_nc()