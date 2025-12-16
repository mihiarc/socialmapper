#!/usr/bin/env python3
"""Script to query OpenStreetMap using Overpass API and output POI data as JSON."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

# Export OSMnx query functions
from .osmnx_query import (
    build_osmnx_tags,
    query_pois_osmnx,
    query_pois_with_fallback,
)

# Export polygon query functions
from .polygon_queries import (
    build_poi_discovery_query,
    query_pois_from_isochrone,
    query_pois_in_polygon,
)

__all__ = [
    "build_osmnx_tags",
    "build_overpass_query",
    "build_poi_discovery_query",
    "create_poi_config",
    "format_results",
    "load_poi_config",
    "query_overpass",
    "query_pois",
    "query_pois_from_isochrone",
    "query_pois_in_polygon",
    "query_pois_osmnx",
    "query_pois_with_fallback",
    "save_json",
]

# Configure logger
import logging

import overpy
import yaml

from ..constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_BACKOFF_EXPONENTIAL,
    OVERPASS_PRIMARY_ENDPOINT,
    US_STATE_ABBREV_LENGTH,
)

logger = logging.getLogger(__name__)


def create_poi_config(geocode_area, state, city, poi_type, poi_name, additional_tags=None):
    """Create a POI configuration dictionary from parameters.

    Parameters
    ----------
    geocode_area : str
        The area to search within (city/town name).
    state : str
        The state name or abbreviation.
    city : str
        The city name (optional, defaults to geocode_area).
    poi_type : str
        The type of POI (e.g., 'amenity', 'leisure').
    poi_name : str
        The name of the POI (e.g., 'library', 'park').
    additional_tags : dict, optional
        Dictionary of additional tags to filter by, by default None.

    Returns
    -------
    dict
        Dictionary containing POI configuration.
    """
    config = {"geocode_area": geocode_area, "state": state, "type": poi_type, "name": poi_name}

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
        with Path(file_path).open() as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {e}")
        sys.exit(1)
    except (OSError, PermissionError) as e:
        logger.error(f"Error reading configuration file: {e}")
        sys.exit(1)


def build_overpass_query(poi_config):
    """Build an Overpass API query from the configuration."""
    query = "[out:json]"

    query += ";\n"

    # Handle different area specifications
    if "geocode_area" in poi_config:
        # Use area name for locations
        area_name = poi_config["geocode_area"]

        # Check if state and city are both specified
        state = poi_config.get("state")
        city = poi_config.get("city")

        if state and city:
            # Map common state names to abbreviations
            state_mapping = {
                "North Carolina": "NC",
                "South Carolina": "SC",
                "New York": "NY",
                "California": "CA",
                "Texas": "TX",
                "Florida": "FL",
                "New Hampshire": "NH",
                "Virginia": "VA",
                "Georgia": "GA",
                # Add more as needed
            }

            # Normalize state
            state_abbrev = state_mapping.get(state, state)

            # Build a geocode query that's more specific
            # First get the state area
            if len(state_abbrev) == US_STATE_ABBREV_LENGTH and state_abbrev.isupper():
                # US state - use ISO code
                query += f'area["ISO3166-2"="US-{state_abbrev}"]->.state;\n'
            else:
                # Non-US or full state name
                query += f'area[name="{state}"]["admin_level"="4"]->.state;\n'

            # Then search for the city within that state
            # Using multiple possible admin levels for cities
            query += "(\n"
            query += f'  area[name="{city}"]["place"="city"](area.state);\n'
            query += f'  area[name="{city}"]["admin_level"="8"](area.state);\n'
            query += f'  area[name="{city}"]["boundary"="administrative"](area.state);\n'
            query += ")->.searchArea;\n"
        else:
            # Simple area based query. If multiple areas have the same name, this will return all of them.
            query += f'area[name="{area_name}"]->.searchArea;\n'

        # Use short format for node, way, relation (nwr)
        tag_filter = ""
        if "type" in poi_config and "tags" in poi_config:
            for key, value in poi_config["tags"].items():
                tag_filter += f'[{key}="{value}"]'
        elif "type" in poi_config and "name" in poi_config:
            # Handle simple type:name combination
            poi_type = poi_config["type"]
            poi_name = poi_config["name"]
            tag_filter += f'[{poi_type}="{poi_name}"]'

        # Add the search instruction
        query += f"nwr{tag_filter}(area.searchArea);\n"

    elif "bbox" in poi_config:
        # Use bounding box format: south,west,north,east
        bbox = poi_config["bbox"]
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
        if "type" in poi_config and "tags" in poi_config:
            for key, value in poi_config["tags"].items():
                tag_filter += f'[{key}="{value}"]'
        elif "type" in poi_config and "name" in poi_config:
            # Handle simple type:name combination
            poi_type = poi_config["type"]
            poi_name = poi_config["name"]
            tag_filter += f'[{poi_type}="{poi_name}"]'

        # Add the search instruction with bbox
        query += f"nwr{tag_filter}({bbox_str});\n"
    else:
        # Default global search with a limit
        logger.warning("No area name or bbox specified. Using global search.")

        # Build tag filters
        tag_filter = ""
        if "type" in poi_config and "tags" in poi_config:
            for key, value in poi_config["tags"].items():
                tag_filter += f'[{key}="{value}"]'
        elif "type" in poi_config and "name" in poi_config:
            # Handle simple type:name combination
            poi_type = poi_config["type"]
            poi_name = poi_config["name"]
            tag_filter += f'[{poi_type}="{poi_name}"]'

        # Global search with tag filter
        query += f"nwr{tag_filter};\n"

    # Add output statement - simplified to match the working query
    query += "out center;\n"

    return query


def query_overpass(query):
    """Query the Overpass API with the given query.

    Uses retry logic to handle transient errors.
    """
    import time

    api = overpy.Overpass(url=OVERPASS_PRIMARY_ENDPOINT)

    for attempt in range(DEFAULT_MAX_RETRIES):
        try:
            logger.info("Sending query to Overpass API...")
            return api.query(query)
        except overpy.exception.OverpassTooManyRequests as e:
            if attempt == DEFAULT_MAX_RETRIES - 1:
                logger.error(f"Overpass API rate limited after {DEFAULT_MAX_RETRIES} attempts: {e}")
                raise
            delay = DEFAULT_RETRY_BACKOFF_EXPONENTIAL * (2 ** attempt)
            logger.warning(f"Rate limited (attempt {attempt + 1}/{DEFAULT_MAX_RETRIES}), retrying in {delay}s")
            time.sleep(delay)
        except overpy.exception.OverpassGatewayTimeout as e:
            if attempt == DEFAULT_MAX_RETRIES - 1:
                logger.error(f"Overpass API gateway timeout after {DEFAULT_MAX_RETRIES} attempts: {e}")
                raise
            delay = DEFAULT_RETRY_BACKOFF_EXPONENTIAL * (2 ** attempt)
            logger.warning(f"Gateway timeout (attempt {attempt + 1}/{DEFAULT_MAX_RETRIES}), retrying in {delay}s")
            time.sleep(delay)
        except (overpy.exception.OverpassError, ConnectionError, TimeoutError) as e:
            if attempt == DEFAULT_MAX_RETRIES - 1:
                logger.error(f"Error querying Overpass API after {DEFAULT_MAX_RETRIES} attempts: {e}")
                logger.debug(f"Query used: {query}")
                raise
            delay = DEFAULT_RETRY_BACKOFF_EXPONENTIAL * (2 ** attempt)
            logger.warning(f"Overpass API query failed (attempt {attempt + 1}/{DEFAULT_MAX_RETRIES}), retrying in {delay}s: {e}")
            time.sleep(delay)


def format_results(result, config=None):
    """Format the Overpass API results into structured dictionary.

    Parameters
    ----------
    result : overpy.Result
        The result from the Overpass API query.
    config : dict, optional
        Optional configuration dictionary that may contain state
        information, by default None.

    Returns
    -------
    dict
        A dictionary containing the POIs in JSON format with keys:
        - poi_count : int
            The total number of POIs found.
        - pois : list of dict
            List of dictionaries containing the POIs with keys:
            - id : int
                The ID of the POI.
            - type : str
                The type of the POI.
            - lat : float
                The latitude of the POI.
            - lon : float
                The longitude of the POI.
            - tags : dict
                Dictionary containing the tags of the POI.
            - state : str
                The state of the POI (if available in config).
    """
    data = {"poi_count": 0, "pois": []}  # Initialize with 0, will be updated at the end

    # Extract state from config if available
    state = None
    if config and "state" in config:
        state = config["state"]

    # Define approximate bounds for US states to filter results
    # This helps when the Overpass query returns results from multiple states
    state_bounds = {
        "NC": {"min_lat": 33.7, "max_lat": 36.6, "min_lon": -84.4, "max_lon": -75.3},
        "North Carolina": {"min_lat": 33.7, "max_lat": 36.6, "min_lon": -84.4, "max_lon": -75.3},
        "CA": {"min_lat": 32.5, "max_lat": 42.0, "min_lon": -124.5, "max_lon": -114.0},
        "NH": {"min_lat": 42.7, "max_lat": 45.3, "min_lon": -72.6, "max_lon": -70.6},
        "CT": {"min_lat": 40.9, "max_lat": 42.1, "min_lon": -73.8, "max_lon": -71.8},
        # Add more states as needed
    }

    # Check if we should filter by bounds
    bounds = None
    if state and state in state_bounds:
        bounds = state_bounds[state]
        logger.info(f"Filtering POIs to {state} bounds: {bounds}")

    # Process nodes
    for node in result.nodes:
        lat = float(node.lat)
        lon = float(node.lon)

        # Skip if outside state bounds
        if bounds and not (
            bounds["min_lat"] <= lat <= bounds["max_lat"]
            and bounds["min_lon"] <= lon <= bounds["max_lon"]
        ):
            continue

        poi_data = {
            "id": node.id,
            "type": "node",
            "lat": lat,
            "lon": lon,
            "tags": node.tags,
        }

        # Add state if available
        if state:
            poi_data["state"] = state

        data["pois"].append(poi_data)

    # Process ways - with 'out center' format
    for way in result.ways:
        # Get center coordinates if available
        center_lat = getattr(way, "center_lat", None)
        center_lon = getattr(way, "center_lon", None)

        # Skip if no coordinates
        if not (center_lat and center_lon):
            continue

        lat = float(center_lat)
        lon = float(center_lon)

        # Skip if outside state bounds
        if bounds and not (
            bounds["min_lat"] <= lat <= bounds["max_lat"]
            and bounds["min_lon"] <= lon <= bounds["max_lon"]
        ):
            continue

        poi_data = {"id": way.id, "type": "way", "tags": way.tags}
        poi_data["lat"] = lat
        poi_data["lon"] = lon

        # Add state if available
        if state:
            poi_data["state"] = state

        data["pois"].append(poi_data)

    # Process relations - with 'out center' format
    for relation in result.relations:
        # Get center coordinates if available
        center_lat = getattr(relation, "center_lat", None)
        center_lon = getattr(relation, "center_lon", None)

        # Skip if no coordinates
        if not (center_lat and center_lon):
            continue

        lat = float(center_lat)
        lon = float(center_lon)

        # Skip if outside state bounds
        if bounds and not (
            bounds["min_lat"] <= lat <= bounds["max_lat"]
            and bounds["min_lon"] <= lon <= bounds["max_lon"]
        ):
            continue

        poi_data = {"id": relation.id, "type": "relation", "tags": relation.tags}
        poi_data["lat"] = lat
        poi_data["lon"] = lon

        # Add state if available
        if state:
            poi_data["state"] = state

        data["pois"].append(poi_data)

    # Update poi count
    data["poi_count"] = len(data["pois"])

    # Log filtering results if bounds were applied
    if bounds:
        total_results = len(result.nodes) + len(result.ways) + len(result.relations)
        logger.info(
            f"Filtered {total_results} results to {data['poi_count']} within {state} bounds"
        )

    return data


def save_json(data, output_file):
    """Save data to a JSON file."""
    try:
        # Create output directory if it doesn't exist
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Results saved to {output_file}")
    except (OSError, PermissionError) as e:
        logger.error(f"Error writing JSON file: {e}")
        sys.exit(1)
    except (TypeError, ValueError) as e:
        logger.error(f"Error serializing data to JSON: {e}")
        sys.exit(1)


def query_pois(
    config: dict[str, Any], output_file: str | None = None, verbose: bool = False
) -> dict[str, Any]:
    """Query POIs from OpenStreetMap with given configuration.

    Parameters
    ----------
    config : dict
        POI configuration dictionary.
    output_file : str, optional
        Optional output file path to save results, by default None.
    verbose : bool, optional
        Whether to output detailed information, by default False.

    Returns
    -------
    dict
        Dictionary with POI results.
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
    """Command-line interface for querying POIs from OpenStreetMap."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Query POIs from OpenStreetMap via Overpass API")
    parser.add_argument("config_file", help="YAML configuration file")
    parser.add_argument(
        "-o",
        "--output",
        help="Output JSON file (default: auto-generated based on query)",
        default=None,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Print the Overpass query")
    args = parser.parse_args()

    # Load configuration
    config = load_poi_config(args.config_file)

    # Generate descriptive output filename if not specified
    if args.output is None:
        # Extract key components for the filename
        geocode_area = config.get("geocode_area", "global")
        poi_type = config.get("type", "")
        poi_name = config.get("name", "")

        # Create a sanitized filename (replace spaces with underscores)
        location_part = geocode_area.replace(" ", "_").lower()
        type_part = poi_type.lower()
        name_part = poi_name.replace(" ", "_").lower()

        # Construct the filename
        if poi_type and poi_name:
            filename = f"{location_part}_{type_part}_{name_part}.json"
        elif "tags" in config:
            # Use first tag for naming
            tag_key = next(iter(config["tags"].keys()))
            tag_value = config["tags"][tag_key]
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
