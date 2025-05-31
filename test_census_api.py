#!/usr/bin/env python3
"""
Test script to debug Census API geocoding
"""

import requests
import json

def test_census_api():
    """Test the Census geocoding API directly"""
    lat = 35.5846
    lon = -78.7997
    
    url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
    params = {
        'x': lon,
        'y': lat,
        'benchmark': 'Public_AR_Current',
        'vintage': 'Current_Current',
        'format': 'json'
    }
    
    print(f"Testing Census API with coordinates: {lat}, {lon}")
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response structure:")
            print(f"  Top-level keys: {list(data.keys())}")
            
            if 'result' in data:
                result = data['result']
                print(f"  Result keys: {list(result.keys())}")
                
                if 'geographies' in result:
                    geographies = result['geographies']
                    print(f"  Geography layers: {list(geographies.keys())}")
                    
                    if 'Counties' in geographies:
                        counties = geographies['Counties']
                        print(f"  Counties found: {len(counties)}")
                        
                        if counties:
                            county = counties[0]
                            print(f"  County data:")
                            print(f"    STATE: {repr(county.get('STATE'))}")
                            print(f"    COUNTY: {repr(county.get('COUNTY'))}")
                            print(f"    NAME: {repr(county.get('NAME'))}")
                            
                            # Test the geocoding logic
                            state_fips = county.get('STATE')
                            county_fips = county.get('COUNTY')
                            
                            print(f"\n  Extracted values:")
                            print(f"    state_fips: {repr(state_fips)} (type: {type(state_fips)})")
                            print(f"    county_fips: {repr(county_fips)} (type: {type(county_fips)})")
                            
                            # Test None checks
                            print(f"\n  None checks:")
                            print(f"    state_fips is None: {state_fips is None}")
                            print(f"    county_fips is None: {county_fips is None}")
                            print(f"    state_fips == '': {state_fips == ''}")
                            print(f"    county_fips == '': {county_fips == ''}")
                            
                            return {
                                'state_fips': state_fips,
                                'county_fips': county_fips,
                                'tract_geoid': None,
                                'block_group_geoid': None
                            }
                        else:
                            print("  No counties in response")
                    else:
                        print("  No Counties layer in geographies")
                else:
                    print("  No geographies in result")
            else:
                print("  No result in response")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")
        
    return None

if __name__ == "__main__":
    result = test_census_api()
    print(f"\nFinal result: {result}") 