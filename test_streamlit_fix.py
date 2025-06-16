#!/usr/bin/env python3
"""Test to verify the Streamlit fix for POI search."""

import os
import sys

# Ensure we can import SocialMapper
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from socialmapper import SocialMapperClient, SocialMapperBuilder

# Test the exact scenario from Streamlit
location = "Durham, North Carolina"
poi_type = "amenity"
poi_name = "library"
travel_time = 15
travel_mode = "walk"
census_vars = [("B01003_001E", "Total Population"), ("B19013_001E", "Median Household Income")]

print(f"Testing POI search for: {location}")
print(f"Looking for: {poi_type}={poi_name}")
print("=" * 50)

try:
    with SocialMapperClient() as client:
        # Parse location as the fixed Streamlit app would
        if ", " in location:
            city, state = location.split(", ", 1)
            config = (SocialMapperBuilder()
                .with_location(city, state)
                .with_osm_pois(poi_type, poi_name)
                .with_travel_time(travel_time)
                .with_travel_mode(travel_mode)
                .with_census_variables(*[var[0] for var in census_vars])
                .with_exports(csv=True, isochrones=True, maps=False)
                .build()
            )
        else:
            config = (SocialMapperBuilder()
                .with_location(location)
                .with_osm_pois(poi_type, poi_name)
                .with_travel_time(travel_time)
                .with_travel_mode(travel_mode)
                .with_census_variables(*[var[0] for var in census_vars])
                .with_exports(csv=True, isochrones=True, maps=False)
                .build()
            )
        
        print(f"\nConfiguration built:")
        print(f"  geocode_area: {config.get('geocode_area')}")
        print(f"  state: {config.get('state')}")
        print(f"  poi_type: {config.get('poi_type')}")
        print(f"  poi_name: {config.get('poi_name')}")
        
        # Try to run just the POI extraction part
        from socialmapper.pipeline.extraction import extract_poi_data
        
        poi_data, base_filename, state_abbreviations, sampled_pois = extract_poi_data(
            geocode_area=config.get('geocode_area'),
            state=config.get('state'),
            poi_type=config.get('poi_type'),
            poi_name=config.get('poi_name')
        )
        
        print(f"\nPOI extraction successful!")
        print(f"  Found {len(poi_data.get('pois', []))} POIs")
        
        if poi_data.get('pois'):
            print(f"\nFirst 5 POIs:")
            for i, poi in enumerate(poi_data['pois'][:5]):
                name = poi.get('tags', {}).get('name', 'Unnamed')
                lat, lon = poi.get('lat'), poi.get('lon')
                print(f"  {i+1}. {name} at ({lat:.4f}, {lon:.4f})")
        
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()