import requests
import pandas as pd
import yaml
import json
from pathlib import Path
from scripts.core.config import Config

def load_study_area() -> dict:
    """Load the study area configuration."""
    config = Config()
    return config.get_study_area()

def get_county_boundaries(config: Config) -> tuple[pd.DataFrame, dict]:
    """
    Fetch county boundaries from Census TIGER/Web service for the study area counties.
    
    Args:
        config: Configuration object for path management
    
    Returns:
        tuple: (DataFrame of county metadata, dict of bounding box coordinates)
    """
    # Load study area configuration
    study_area = load_study_area()
    
    # Build list of FIPS codes for our counties
    county_fips = []
    for state in study_area['states']:
        state_counties = study_area['counties'][state['name']]
        county_fips.extend([county['fips'] for county in state_counties])
    
    # Print configured counties for verification
    print("\nConfigured counties:")
    for state_name, counties in study_area['counties'].items():
        print(f"\n{state_name}:")
        for county in counties:
            print(f"  - {county['name']} County (FIPS: {county['fips']})")
    
    # Census TIGER/Web service URL
    base_url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query"
    
    # Build the query parameters
    # Using FIPS codes to filter counties
    fips_list = ",".join(f"'{fips}'" for fips in county_fips)
    
    params = {
        'where': f"GEOID IN ({fips_list})",
        'outFields': '*',  # Get all fields
        'geometryPrecision': 6,
        'outSR': '4326',  # Return in WGS84 (lat/lon)
        'f': 'geojson'    # Return as GeoJSON
    }
    
    print("\nFetching county boundaries...")
    response = requests.get(base_url, params=params)
    
    if response.status_code != 200:
        raise Exception(f"Error fetching county boundaries: {response.status_code}")
    
    # Save the raw GeoJSON response
    geojson_data = response.json()
    
    # Verify that we only got the counties we wanted
    features = geojson_data['features']
    received_fips = [feature['properties']['GEOID'] for feature in features]
    unexpected_fips = set(received_fips) - set(county_fips)
    missing_fips = set(county_fips) - set(received_fips)
    
    if unexpected_fips:
        print("\nWARNING: Received unexpected counties:")
        for fips in unexpected_fips:
            matching_feature = next(f for f in features if f['properties']['GEOID'] == fips)
            print(f"  - {matching_feature['properties']['NAME']} County, State FIPS: {matching_feature['properties']['STATE']}")
            # Remove unexpected counties from the features
            features = [f for f in features if f['properties']['GEOID'] not in unexpected_fips]
        geojson_data['features'] = features
    
    if missing_fips:
        print("\nWARNING: Missing configured counties:")
        for fips in missing_fips:
            for state_name, counties in study_area['counties'].items():
                for county in counties:
                    if county['fips'] == fips:
                        print(f"  - {county['name']} County (FIPS: {fips})")
    
    # Save the filtered GeoJSON
    output_geojson = Path(config.get_path('data.input.county_data')) / 'county_boundaries.geojson'
    output_geojson.parent.mkdir(parents=True, exist_ok=True)
    with open(output_geojson, 'w') as f:
        json.dump(geojson_data, f)
    
    print(f"\nCounty boundaries saved to {output_geojson}")
    
    # Calculate bounding box from features
    if not features:
        raise Exception("No features returned from the query")
    
    # Initialize with first coordinate
    first_coords = features[0]['geometry']['coordinates'][0][0]
    bbox = {
        'west': first_coords[0],   # min longitude
        'east': first_coords[0],   # max longitude
        'south': first_coords[1],  # min latitude
        'north': first_coords[1]   # max latitude
    }
    
    # Find min/max coordinates across all features
    for feature in features:
        coords = feature['geometry']['coordinates'][0]  # Outer ring of polygon
        for lon, lat in coords:
            bbox['west'] = min(bbox['west'], lon)
            bbox['east'] = max(bbox['east'], lon)
            bbox['south'] = min(bbox['south'], lat)
            bbox['north'] = max(bbox['north'], lat)
    
    # Calculate the current size
    width = bbox['east'] - bbox['west']
    height = bbox['north'] - bbox['south']
    
    # Add a buffer that's 10% of current dimensions on each side
    bbox['west'] -= width * 0.1   # Add 10% to the west
    bbox['east'] += width * 0.1   # Add 10% to the east
    bbox['south'] -= height * 0.1  # Add 10% to the south
    bbox['north'] += height * 0.1  # Add 10% to the north
    
    # Save the bounding box
    bbox_path = Path(config.get_path('data.input.county_data')) / 'study_area_bbox.json'
    with open(bbox_path, 'w') as f:
        json.dump(bbox, f, indent=2)
    print(f"Study area bounding box saved to {bbox_path}")
    
    # Extract county properties to a DataFrame
    counties_data = []
    for feature in features:
        props = feature.get('properties', {})
        counties_data.append({
            'GEOID': props.get('GEOID'),
            'NAME': props.get('NAME'),
            'STATE': props.get('STATE'),
            'STUSPS': props.get('STUSPS'),  # State postal code
            'STATEFP': props.get('STATEFP'),  # State FIPS
            'COUNTYFP': props.get('COUNTYFP'),  # County FIPS
            'ALAND': props.get('ALAND'),  # Land area
            'AWATER': props.get('AWATER')  # Water area
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(counties_data)
    
    # Save county metadata to CSV
    output_csv = Path(config.get_path('data.input.county_data')) / 'county_metadata.csv'
    df.to_csv(output_csv, index=False)
    print(f"County metadata saved to {output_csv}")
    
    return df, bbox

def main():
    # Initialize configuration
    config = Config()
    
    # Fetch county boundaries and bounding box
    counties_df, bbox = get_county_boundaries(config)
    
    # Print summaries
    print("\nStudy Area Bounding Box:")
    print(f"North: {bbox['north']:.4f}")
    print(f"South: {bbox['south']:.4f}")
    print(f"East:  {bbox['east']:.4f}")
    print(f"West:  {bbox['west']:.4f}")
    
    print("\nCounties fetched:")
    print(counties_df.groupby('STATE')['NAME'].count())
    print("\nSample of counties:")
    print(counties_df[['NAME', 'STATE', 'GEOID']].head())

if __name__ == "__main__":
    main() 