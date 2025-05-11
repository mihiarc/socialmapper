import json
import os

def convert_geojson_to_json(geojson_path, json_path):
    """
    Convert a GeoJSON file with trail head points to a JSON format that preserves all properties
    but is compatible with SocialMapper custom coordinates format.
    """
    # Open and read the GeoJSON file
    with open(geojson_path, 'r') as f:
        data = json.load(f)
    
    # Create a list to hold all trail points with their properties
    trail_points = []
    
    # Process each feature in the GeoJSON
    for i, feature in enumerate(data['features']):
        properties = feature['properties']
        geometry = feature['geometry']
        
        # Extract coordinates (GeoJSON format is [longitude, latitude])
        longitude, latitude = geometry['coordinates']
        
        # Extract name from the TRAIL_NAME property
        name = properties.get('TRAIL_NAME', f'Trail_{i}')
        
        # Determine state based on FOREST code
        forest_code = properties.get('FOREST', '')
        forest_to_state = {
            '05': 'FL',  # Florida
            '02': 'KY',  # Kentucky 
            '03': 'GA',  # Georgia
            '13': 'TX',  # Texas
            '60': 'KY',  # Land Between the Lakes in Kentucky/Tennessee
            '09': 'AR',  # Arkansas
        }
        state = forest_to_state.get(forest_code, 'Unknown')
        
        # Create a point object that includes all original properties plus required fields
        point = {
            'id': i,
            'name': name,
            'lat': latitude,
            'lon': longitude,
            'state': state,
            'original_properties': properties
        }
        
        trail_points.append(point)
    
    # Write the result to JSON file
    with open(json_path, 'w') as f:
        json.dump(trail_points, f, indent=2)
    
    print(f"Converted {len(trail_points)} trail heads to JSON format at: {json_path}")
    print(f"All original properties have been preserved under the 'original_properties' field.")

if __name__ == "__main__":
    # Paths
    input_file = "examples/trail_heads_08.geojson"
    output_file = "examples/trail_heads.json"
    
    # Ensure input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file not found at {input_file}")
        exit(1)
    
    # Convert the file
    convert_geojson_to_json(input_file, output_file)
    print("Conversion complete. You can now use this JSON file for more detailed analysis.")
    print("The JSON format includes all required fields for SocialMapper while preserving all original GeoJSON properties.") 