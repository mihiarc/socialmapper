#!/usr/bin/env python3
"""
Test script to debug POI search functionality with manual Overpass query
"""

import overpy

def test_manual_query():
    api = overpy.Overpass()
    
    # Test different query approaches
    queries = {
        "Method 1: State + City": """
[out:json];
area["ISO3166-2"="US-NC"]->.state;
area[name="Durham"](area.state)->.searchArea;
nwr[amenity="library"](area.searchArea);
out center;
""",
        "Method 2: Combined area search": """
[out:json];
area[name="Durham"]["admin_level"="8"]["is_in:state"="North Carolina"]->.searchArea;
nwr[amenity="library"](area.searchArea);
out center;
""",
        "Method 3: Geocode area ID": """
[out:json];
area[name="Durham County"]["admin_level"="6"]["is_in:state"="North Carolina"]->.searchArea;
nwr[amenity="library"](area.searchArea);
out center;
"""
    }
    
    for method, query in queries.items():
        print(f"\n=== {method} ===")
        print("Query:")
        print(query)
        
        try:
            result = api.query(query)
            print(f"Found {len(result.nodes) + len(result.ways) + len(result.relations)} POIs")
            
            # Show first few results
            count = 0
            for node in result.nodes:
                if count < 3:
                    name = node.tags.get('name', 'Unnamed')
                    print(f"  - {name} at ({node.lat}, {node.lon})")
                    count += 1
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_manual_query()