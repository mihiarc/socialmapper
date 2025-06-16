#!/usr/bin/env python3
"""Test POI search to debug Streamlit issue."""

import os
from socialmapper import SocialMapperClient, SocialMapperBuilder

# Set API key if needed
if 'CENSUS_API_KEY' not in os.environ:
    print("Warning: CENSUS_API_KEY not set")

# Test 1: Basic POI search as done in Streamlit
print("Test 1: Basic search (Durham, North Carolina)")
print("=" * 50)

try:
    with SocialMapperClient() as client:
        config = (SocialMapperBuilder()
            .with_location("Durham", "North Carolina")  # Split as done in streamlit
            .with_osm_pois("amenity", "library")
            .with_travel_time(15)
            .with_travel_mode("walk")
            .with_census_variables("B01003_001E")
            .with_exports(csv=True, isochrones=True, maps=False)
            .build()
        )
        
        print(f"Config: {config}")
        result = client.run_analysis(config)
        
        if result.is_ok():
            analysis_data = result.unwrap()
            print(f"Success! POI count: {analysis_data.poi_count}")
        else:
            error = result.unwrap_err()
            print(f"Failed: {error.message}")
            
except Exception as e:
    print(f"Exception: {e}")

print("\n")

# Test 2: Try with full location string
print("Test 2: Full location string")
print("=" * 50)

try:
    # Import the query module directly to test
    from socialmapper.query import create_poi_config, build_overpass_query, query_overpass, format_results
    
    # Create config as the pipeline would
    config = create_poi_config(
        geocode_area="Durham",
        state="North Carolina",
        city="Durham",
        poi_type="amenity",
        poi_name="library"
    )
    
    print(f"POI Config: {config}")
    
    # Build and show the query
    query = build_overpass_query(config)
    print(f"\nOverpass Query:\n{query}")
    
    # Try to execute it
    print("\nExecuting query...")
    try:
        raw_results = query_overpass(query)
        poi_data = format_results(raw_results, config)
        print(f"Found {len(poi_data['pois'])} POIs")
        
        # Show first few POIs if any
        if poi_data['pois']:
            print("\nFirst 3 POIs:")
            for i, poi in enumerate(poi_data['pois'][:3]):
                print(f"  {i+1}. {poi.get('tags', {}).get('name', 'Unnamed')} at ({poi['lat']}, {poi['lon']})")
    except Exception as e:
        print(f"Query failed: {e}")
        
except Exception as e:
    print(f"Exception: {e}")

print("\n")

# Test 3: Try with state abbreviation
print("Test 3: Using state abbreviation (NC)")
print("=" * 50)

try:
    from socialmapper.query import create_poi_config, build_overpass_query
    
    config = create_poi_config(
        geocode_area="Durham",
        state="NC",
        city="Durham",
        poi_type="amenity",
        poi_name="library"
    )
    
    query = build_overpass_query(config)
    print(f"Overpass Query:\n{query}")
    
except Exception as e:
    print(f"Exception: {e}")