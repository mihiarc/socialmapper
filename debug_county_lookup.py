import json
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Add parent directory to path so we can import socialmapper modules
sys.path.insert(0, str(Path(__file__).parent))

from socialmapper.counties import get_county_fips_from_point, get_counties_from_pois

# Load test POIs
test_pois_path = "tests/test_output/test_pois.json"
with open(test_pois_path, "r") as f:
    poi_data = json.load(f)

print(f"Loaded {len(poi_data.get('pois', []))} POIs from {test_pois_path}")

# First, test individual county lookup for each POI
print("\n=== Testing individual county lookups ===")
for i, poi in enumerate(poi_data.get('pois', [])[:3]):  # Just test first 3 for brevity
    lat = poi.get('lat')
    lon = poi.get('lon')
    print(f"\nPOI {i}: {poi.get('id')} at ({lat}, {lon})")
    try:
        state_fips, county_fips = get_county_fips_from_point(lat, lon)
        if state_fips and county_fips:
            print(f"✅ Found county: State FIPS {state_fips}, County FIPS {county_fips}")
        else:
            print(f"❌ Could not determine county for coordinates ({lat}, {lon})")
    except Exception as e:
        print(f"❌ Error determining county: {e}")

# Now test the full counties_from_pois function
print("\n=== Testing get_counties_from_pois ===")
try:
    counties = get_counties_from_pois(poi_data, include_neighbors=True)
    if counties:
        print(f"✅ Found {len(counties)} counties (including neighbors)")
        for i, (state_fips, county_fips) in enumerate(counties[:5]):  # Just show first 5
            print(f"  - County {i+1}: State FIPS {state_fips}, County FIPS {county_fips}")
    else:
        print("❌ No counties found")
except Exception as e:
    print(f"❌ Error getting counties: {e}") 