#!/usr/bin/env python3
"""
Script to query OpenStreetMap using Overpass API and output POI data as JSON.
"""
import argparse
import json
import os
import sys
import yaml
import overpy

def load_poi_config(file_path):
    """Load POI configuration from YAML file."""
    try:
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

def build_overpass_query(poi_config):
    """Build an Overpass API query from the configuration."""
    query = "[out:json]"
    
    # Add timeout if specified
    if 'timeout' in poi_config:
        query += f"[timeout:{poi_config['timeout']}]"
    else:
        query += "[timeout:30]"
    
    query += ";\n"
    
    # Handle different area specifications
    if 'geocode_area' in poi_config:
        # Use area name for locations
        area_name = poi_config['geocode_area']
        
        # Check if state and city are both specified
        state = poi_config.get('state')
        city = poi_config.get('city')
        
        if state and city:
            # First create an area for the state
            query += f"area[name=\"{state}\"][\"admin_level\"=\"4\"]->.state;\n"
            # Then find the city within that state
            query += f"area[name=\"{city}\"](area.state)->.searchArea;\n"
        else:
            # Simple area query
            query += f"area[name=\"{area_name}\"]->.searchArea;\n"
        
        # Use short format for node, way, relation (nwr)
        tag_filter = ""
        if 'type' in poi_config and 'tags' in poi_config:
            for key, value in poi_config['tags'].items():
                tag_filter += f"[{key}=\"{value}\"]"
        elif 'type' in poi_config and 'name' in poi_config:
            # Handle simple type:name combination
            poi_type = poi_config['type']
            poi_name = poi_config['name']
            tag_filter += f"[{poi_type}=\"{poi_name}\"]"
            
        # Add the search instruction
        query += f"nwr{tag_filter}(area.searchArea);\n"
        
    elif 'bbox' in poi_config:
        # Use bounding box format: south,west,north,east
        bbox = poi_config['bbox']
        bbox_str = ""
        if isinstance(bbox, str):
            # Use bbox as is if it's a string
            bbox_str = bbox
        else:
            # Format from list or dict to string
            south, west, north, east = bbox
            bbox_str = f"{south},{west},{north},{east}"
            
        # Build tag filters
        tag_filter = ""
        if 'type' in poi_config and 'tags' in poi_config:
            for key, value in poi_config['tags'].items():
                tag_filter += f"[{key}=\"{value}\"]"
        elif 'type' in poi_config and 'name' in poi_config:
            # Handle simple type:name combination
            poi_type = poi_config['type']
            poi_name = poi_config['name']
            tag_filter += f"[{poi_type}=\"{poi_name}\"]"
            
        # Add the search instruction with bbox
        query += f"nwr{tag_filter}({bbox_str});\n"
    else:
        # Default global search with a limit
        print("Warning: No area name or bbox specified. Using global search.")
        
        # Build tag filters
        tag_filter = ""
        if 'type' in poi_config and 'tags' in poi_config:
            for key, value in poi_config['tags'].items():
                tag_filter += f"[{key}=\"{value}\"]"
        elif 'type' in poi_config and 'name' in poi_config:
            # Handle simple type:name combination
            poi_type = poi_config['type']
            poi_name = poi_config['name']
            tag_filter += f"[{poi_type}=\"{poi_name}\"]"
            
        # Global search with tag filter
        query += f"nwr{tag_filter};\n"
    
    # Add output statement - simplified to match the working query
    query += "out center;\n"
    
    return query

def query_overpass(query):
    """Query the Overpass API with the given query."""
    api = overpy.Overpass()
    try:
        return api.query(query)
    except Exception as e:
        print(f"Error querying Overpass API: {e}")
        print(f"Query used: {query}")
        sys.exit(1)

def format_results(result):
    """Format the Overpass API results into a structured dictionary."""
    data = {
        "pois": []
    }
    
    # Process nodes
    for node in result.nodes:
        poi_data = {
            "id": node.id,
            "type": "node",
            "lat": float(node.lat),
            "lon": float(node.lon),
            "tags": node.tags
        }
        data["pois"].append(poi_data)
    
    # Process ways - with 'out center' format
    for way in result.ways:
        # Get center coordinates if available
        center_lat = getattr(way, 'center_lat', None)
        center_lon = getattr(way, 'center_lon', None)
        
        poi_data = {
            "id": way.id,
            "type": "way",
            "tags": way.tags
        }
        
        # Add center coordinates if available
        if center_lat and center_lon:
            poi_data["lat"] = float(center_lat)
            poi_data["lon"] = float(center_lon)
        
        data["pois"].append(poi_data)
    
    # Process relations - with 'out center' format
    for relation in result.relations:
        # Get center coordinates if available
        center_lat = getattr(relation, 'center_lat', None)
        center_lon = getattr(relation, 'center_lon', None)
        
        poi_data = {
            "id": relation.id,
            "type": "relation",
            "tags": relation.tags
        }
        
        # Add center coordinates if available
        if center_lat and center_lon:
            poi_data["lat"] = float(center_lat)
            poi_data["lon"] = float(center_lon)
        
        data["pois"].append(poi_data)
    
    return data

def save_json(data, output_file):
    """Save data to a JSON file."""
    try:
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Results saved to {output_file}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        sys.exit(1)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Query POIs from OpenStreetMap via Overpass API")
    parser.add_argument("config_file", help="YAML configuration file")
    parser.add_argument("-o", "--output", help="Output JSON file (default: output.json)",
                        default="output.json")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print the Overpass query")
    args = parser.parse_args()
    
    # Load configuration
    config = load_poi_config(args.config_file)
    
    # Build query
    query = build_overpass_query(config)
    
    # Print query if verbose mode is enabled
    if args.verbose:
        print("Overpass Query:")
        print(query)
    
    # Execute query
    print("Querying Overpass API...")
    result = query_overpass(query)
    
    # Format results
    data = format_results(result)
    
    # Output statistics
    print(f"Found {len(data['pois'])} POIs")
    
    # Save results
    save_json(data, args.output)

if __name__ == "__main__":
    main() 