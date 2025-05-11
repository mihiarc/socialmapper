#!/usr/bin/env python3
"""
Script to query OpenStreetMap using Overpass API and output POI data as JSON.
"""
import argparse
import json
import sys
import yaml
import overpy
import os
import logging
from typing import Dict, Any, Optional

from ..util import rate_limited, with_retry, RateLimitedClient

# Configure logger
logger = logging.getLogger(__name__)

def create_poi_config(geocode_area, state, city, poi_type, poi_name, additional_tags=None):
    """
    Create a POI configuration dictionary directly from parameters.
    
    Args:
        geocode_area: The area to search within (city/town name)
        state: The state name or abbreviation 
        city: The city name (optional, defaults to geocode_area)
        poi_type: The type of POI (e.g., 'amenity', 'leisure')
        poi_name: The name of the POI (e.g., 'library', 'park')
        additional_tags: Dictionary of additional tags to filter by (optional)
        
    Returns:
        Dictionary containing POI configuration
    """
    config = {
        "geocode_area": geocode_area,
        "state": state,
        "type": poi_type,
        "name": poi_name
    }
    
    # Add city if different from geocode_area
    if city and city != geocode_area:
        config["city"] = city
    else:
        config["city"] = geocode_area
        
    # Add additional tags if provided
    if additional_tags:
        config["tags"] = additional_tags
        
    return config

def load_poi_config(file_path):
    """Load POI configuration from YAML file."""
    try:
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)

def build_overpass_query(poi_config):
    """Build an Overpass API query from the configuration."""
    query = "[out:json]"
    
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
            # Simple area based query. If multiple areas have the same name, this will return all of them.
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
        logger.warning("No area name or bbox specified. Using global search.")
        
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

@with_retry(max_retries=3, base_delay=2.0, service="openstreetmap")
def query_overpass(query):
    """
    Query the Overpass API with the given query.
    
    Uses rate limiting and retry logic to handle transient errors
    and respect API usage limits.
    """
    api = overpy.Overpass(url="https://overpass-api.de/api/interpreter")
    try:
        logger.info("Sending query to Overpass API...")
        return api.query(query)
    except Exception as e:
        logger.error(f"Error querying Overpass API: {e}")
        logger.debug(f"Query used: {query}")
        raise

def format_results(result, config=None):
    """Format the Overpass API results into a structured dictionary.
    
    Args:
        result: The result from the Overpass API query.
        config: Optional configuration dictionary that may contain state information.
        
    Returns:
        A dictionary containing the POIs in JSON format.

        Keys:
            poi_count: The total number of POIs found.
            pois: A list of dictionaries containing the POIs.
                Keys:
                    id: The ID of the POI.
                    type: The type of the POI.
                    lat: The latitude of the POI.
                    lon: The longitude of the POI.
                    tags: A dictionary containing the tags of the POI.
                    state: The state of the POI (if available in config).
    """
    data = {
        "poi_count": 0,  # Initialize with 0, will be updated at the end
        "pois": []
    }
    
    # Extract state from config if available
    state = None
    if config and "state" in config:
        state = config["state"]
    
    # Process nodes
    for node in result.nodes:
        poi_data = {
            "id": node.id,
            "type": "node",
            "lat": float(node.lat),
            "lon": float(node.lon),
            "tags": node.tags
        }
        
        # Add state if available
        if state:
            poi_data["state"] = state
            
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
        
        # Add state if available
        if state:
            poi_data["state"] = state
            
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
        
        # Add state if available
        if state:
            poi_data["state"] = state
            
        data["pois"].append(poi_data)
    
    # Update poi count
    data["poi_count"] = len(data["pois"])
    
    return data

def save_json(data, output_file):
    """Save data to a JSON file."""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Results saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving JSON file: {e}")
        sys.exit(1)

def query_pois(config: Dict[str, Any], output_file: Optional[str] = None, verbose: bool = False) -> Dict[str, Any]:
    """
    Query POIs from OpenStreetMap with the given configuration.
    
    Args:
        config: POI configuration dictionary
        output_file: Optional output file path to save results
        verbose: Whether to output detailed information
        
    Returns:
        Dictionary with POI results
    """
    # Build query
    query = build_overpass_query(config)
    
    # Print query if verbose mode is enabled
    if verbose:
        logger.info("Overpass Query:")
        logger.info(query)
    
    # Execute query with rate limiting and retry
    logger.info("Querying Overpass API...")
    result = query_overpass(query)
    
    # Format results
    data = format_results(result, config)
    
    # Output statistics
    logger.info(f"Found {len(data['pois'])} POIs")
    
    # Save results if output file is specified
    if output_file:
        save_json(data, output_file)
    
    return data

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Query POIs from OpenStreetMap via Overpass API")
    parser.add_argument("config_file", help="YAML configuration file")
    parser.add_argument("-o", "--output", help="Output JSON file (default: auto-generated based on query)",
                        default=None)
    parser.add_argument("-v", "--verbose", action="store_true", help="Print the Overpass query")
    args = parser.parse_args()
    
    # Load configuration
    config = load_poi_config(args.config_file)
    
    # Generate descriptive output filename if not specified
    if args.output is None:
        # Extract key components for the filename
        geocode_area = config.get('geocode_area', 'global')
        poi_type = config.get('type', '')
        poi_name = config.get('name', '')
        
        # Create a sanitized filename (replace spaces with underscores)
        location_part = geocode_area.replace(' ', '_').lower()
        type_part = poi_type.lower()
        name_part = poi_name.replace(' ', '_').lower()
        
        # Construct the filename
        if poi_type and poi_name:
            filename = f"{location_part}_{type_part}_{name_part}.json"
        elif 'tags' in config:
            # Use first tag for naming
            tag_key = list(config['tags'].keys())[0]
            tag_value = config['tags'][tag_key]
            filename = f"{location_part}_{tag_key}_{tag_value}.json"
        else:
            # Fallback
            filename = f"{location_part}_pois.json"
        
        output_file = f"output/pois/{filename}"
    else:
        output_file = args.output
    
    # Query POIs
    query_pois(config, output_file, args.verbose)

if __name__ == "__main__":
    main() 