import json
import csv
import os

def convert_geojson_to_csv(geojson_path, csv_path):
    """
    Convert a GeoJSON file with trail head points to the CSV format expected by SocialMapper.
    
    Required CSV columns: id, name, lat, lon, state
    """
    # Open and read the GeoJSON file
    with open(geojson_path, 'r') as f:
        data = json.load(f)
    
    # Prepare the CSV writer
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write header row
        writer.writerow(['id', 'name', 'lat', 'lon', 'state'])
        
        # Process each feature in the GeoJSON
        for i, feature in enumerate(data['features']):
            properties = feature['properties']
            geometry = feature['geometry']
            
            # Extract coordinates (GeoJSON format is [longitude, latitude])
            longitude, latitude = geometry['coordinates']
            
            # Extract name from the TRAIL_NAME property
            name = properties.get('TRAIL_NAME', f'Trail_{i}')
            
            # Extract state from REGION property or use a default
            # Note: The region code '08' might correspond to a specific forest region, not a state
            # We'll extract the FOREST code to help identify the state
            forest_code = properties.get('FOREST', '')
            region_code = properties.get('REGION', '')
            
            # Determine state based on FOREST code
            # This is a simplified mapping and may need to be adjusted
            forest_to_state = {
                '05': 'FL',  # Florida has forest code 05
                '02': 'KY',  # Kentucky 
                '03': 'GA',  # Georgia
                '13': 'TX',  # Texas
                '60': 'KY',  # Land Between the Lakes in Kentucky/Tennessee
                '09': 'AR',  # Arkansas
            }
            
            state = forest_to_state.get(forest_code, 'Unknown')
            
            # Write the row to CSV
            writer.writerow([i, name, latitude, longitude, state])
    
    print(f"Converted {len(data['features'])} trail heads to CSV format at: {csv_path}")

if __name__ == "__main__":
    # Paths
    input_file = "examples/trail_heads_08.geojson"
    output_file = "examples/trail_heads.csv"
    
    # Ensure input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file not found at {input_file}")
        exit(1)
    
    # Convert the file
    convert_geojson_to_csv(input_file, output_file)
    print("Conversion complete. You can now use this CSV file with SocialMapper's custom coordinates option.")
    print("Example command: socialmapper --custom-coords examples/trail_heads.csv --travel-time 15 --census-variables total_population median_household_income") 