"""
POI extraction module for the SocialMapper pipeline.

This module handles extraction of POI data from custom files or OpenStreetMap.
"""

import csv
import json
import os
import random
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import URLError

from ..util import PathSecurityError, sanitize_path


def parse_custom_coordinates(
    file_path: str, name_field: str = None, type_field: str = None, preserve_original: bool = True
) -> Dict:
    """
    Parse a custom coordinates file (JSON or CSV) into the POI format expected by the isochrone generator.

    Args:
        file_path: Path to the custom coordinates file
        name_field: Field name to use for the POI name (if different from 'name')
        type_field: Field name to use for the POI type (if different from 'type')
        preserve_original: Whether to preserve original properties in tags

    Returns:
        Dictionary containing POI data in the format expected by the isochrone generator
    """
    # Sanitize the file path
    try:
        safe_file_path = sanitize_path(file_path, allow_absolute=True)
    except PathSecurityError as e:
        raise ValueError(f"Invalid file path: {e}")

    if not safe_file_path.exists():
        raise FileNotFoundError(f"Custom coordinates file not found: {file_path}")

    file_extension = safe_file_path.suffix.lower()

    pois = []
    states_found = set()

    if file_extension == ".json":
        with open(safe_file_path, "r") as f:
            data = json.load(f)

        # Handle different possible JSON formats
        if isinstance(data, list):
            # List of POIs
            for item in data:
                # Check for required fields
                if ("lat" in item and "lon" in item) or (
                    "latitude" in item and "longitude" in item
                ):
                    # Extract lat/lon
                    lat = float(item.get("lat", item.get("latitude")))
                    lon = float(item.get("lon", item.get("longitude")))

                    # State is no longer required
                    state = item.get("state")
                    if state:
                        states_found.add(state)

                    # Use user-specified field for name if provided
                    if name_field and name_field in item:
                        name = item.get(name_field)
                    else:
                        name = item.get("name", f"Custom POI {len(pois)}")

                    # Use user-specified field for type if provided
                    poi_type = None
                    if type_field and type_field in item:
                        poi_type = item.get(type_field)
                    else:
                        poi_type = item.get("type", "custom")

                    # Create tags dict and preserve original properties if requested
                    tags = item.get("tags", {})
                    if preserve_original and "original_properties" in item:
                        tags.update(item["original_properties"])

                    poi = {
                        "id": item.get("id", f"custom_{len(pois)}"),
                        "name": name,
                        "type": poi_type,
                        "lat": lat,
                        "lon": lon,
                        "tags": tags,
                    }

                    # If preserve_original is True, keep all original properties
                    if preserve_original:
                        for key, value in item.items():
                            if key not in ["id", "name", "lat", "lon", "tags", "type", "state"]:
                                poi["tags"][key] = value

                    pois.append(poi)
                else:
                    print(f"Warning: Skipping item missing required coordinates: {item}")
        elif isinstance(data, dict) and "pois" in data:
            pois = data["pois"]

    elif file_extension == ".csv":
        # Use newline="" to ensure correct universal newline handling across platforms
        with open(safe_file_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                # Try to find lat/lon in different possible column names
                lat = None
                lon = None

                for lat_key in ["lat", "latitude", "y"]:
                    if lat_key in row:
                        lat = float(row[lat_key])
                        break

                for lon_key in ["lon", "lng", "longitude", "x"]:
                    if lon_key in row:
                        lon = float(row[lon_key])
                        break

                if lat is not None and lon is not None:
                    # Use user-specified field for name if provided
                    if name_field and name_field in row:
                        name = row.get(name_field)
                    else:
                        name = row.get("name", f"Custom POI {i}")

                    # Use user-specified field for type if provided
                    poi_type = None
                    if type_field and type_field in row:
                        poi_type = row.get(type_field)
                    else:
                        poi_type = row.get("type", "custom")

                    poi = {
                        "id": row.get("id", f"custom_{i}"),
                        "name": name,
                        "type": poi_type,
                        "lat": lat,
                        "lon": lon,
                        "tags": {},
                    }

                    # Add any additional columns as tags
                    for key, value in row.items():
                        if key not in [
                            "id",
                            "name",
                            "lat",
                            "latitude",
                            "y",
                            "lon",
                            "lng",
                            "longitude",
                            "x",
                            "state",
                            "type",
                        ]:
                            poi["tags"][key] = value

                    pois.append(poi)
                else:
                    print(f"Warning: Skipping row {i+1} - missing required coordinates")

    else:
        raise ValueError(
            f"Unsupported file format: {file_extension}. Please provide a JSON or CSV file."
        )

    if not pois:
        raise ValueError(
            f"No valid coordinates found in {file_path}. Please check the file format."
        )

    return {
        "pois": pois,
        "metadata": {
            "source": "custom",
            "count": len(pois),
            "file_path": file_path,
            "states": list(states_found),
        },
    }


def extract_poi_data(
    custom_coords_path: Optional[str] = None,
    geocode_area: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    poi_type: Optional[str] = None,
    poi_name: Optional[str] = None,
    additional_tags: Optional[Dict] = None,
    name_field: Optional[str] = None,
    type_field: Optional[str] = None,
    max_poi_count: Optional[int] = None,
) -> Tuple[Dict[str, Any], str, List[str], bool]:
    """
    Extract POI data from either custom coordinates or OpenStreetMap.

    Returns:
        Tuple of (poi_data, base_filename, state_abbreviations, sampled_pois)
    """
    from ..query import build_overpass_query, create_poi_config, format_results, query_overpass
    from ..census.services.geography_service import StateFormat
    from ..census import get_census_system

    # Get census system for state normalization
    census_system = get_census_system()
    
    state_abbreviations = []
    sampled_pois = False

    if custom_coords_path:
        print("\n=== Using Custom Coordinates (Skipping POI Query) ===")
        poi_data = parse_custom_coordinates(custom_coords_path, name_field, type_field)

        # Extract state information from the custom coordinates if available
        if (
            "metadata" in poi_data
            and "states" in poi_data["metadata"]
            and poi_data["metadata"]["states"]
        ):
            state_abbreviations = census_system.normalize_state_list(
                poi_data["metadata"]["states"], to_format=StateFormat.ABBREVIATION
            )

            if state_abbreviations:
                print(f"Using states from custom coordinates: {', '.join(state_abbreviations)}")

        # Set a name for the output file based on the custom coords file
        file_basename = os.path.basename(custom_coords_path)
        base_filename = f"custom_{os.path.splitext(file_basename)[0]}"

        # Apply POI limit if specified
        if max_poi_count and "pois" in poi_data and len(poi_data["pois"]) > max_poi_count:
            original_count = len(poi_data["pois"])
            poi_data["pois"] = random.sample(poi_data["pois"], max_poi_count)
            poi_data["poi_count"] = len(poi_data["pois"])
            print(f"Sampled {max_poi_count} POIs from {original_count} total POIs")
            sampled_pois = True

            # Add sampling info to metadata
            if "metadata" not in poi_data:
                poi_data["metadata"] = {}
            poi_data["metadata"]["sampled"] = True
            poi_data["metadata"]["original_count"] = original_count

        print(f"Using {len(poi_data['pois'])} custom coordinates from {custom_coords_path}")

    else:
        # Query POIs from OpenStreetMap
        print("\n=== Querying Points of Interest ===")

        if not (geocode_area and poi_type and poi_name):
            raise ValueError(
                "Missing required POI parameters: geocode_area, poi_type, and poi_name are required"
            )

        # Normalize state to abbreviation if provided
        state_abbr = census_system.normalize_state(state, to_format=StateFormat.ABBREVIATION) if state else None

        # Create POI configuration
        config = create_poi_config(
            geocode_area=geocode_area,
            state=state_abbr,
            city=city or geocode_area,
            poi_type=poi_type,
            poi_name=poi_name,
            additional_tags=additional_tags,
        )
        print(f"Querying OpenStreetMap for: {geocode_area} - {poi_type} - {poi_name}")

        # Execute query with error handling
        query = build_overpass_query(config)
        try:
            raw_results = query_overpass(query)
        except (URLError, OSError) as e:
            error_msg = str(e)
            if "Connection refused" in error_msg:
                raise ValueError(
                    "Unable to connect to OpenStreetMap API. This could be due to:\n"
                    "- Temporary API outage\n"
                    "- Network connectivity issues\n"
                    "- Rate limiting\n\n"
                    "Please try:\n"
                    "1. Waiting a few minutes and trying again\n"
                    "2. Checking your internet connection\n"
                    "3. Using a different POI type or location"
                ) from e
            else:
                raise ValueError(f"Error querying OpenStreetMap: {error_msg}") from e

        poi_data = format_results(raw_results, config)

        # Generate base filename from POI configuration
        poi_type_str = config.get("type", "poi")
        poi_name_str = config.get("name", "custom").replace(" ", "_").lower()
        location = config.get("geocode_area", "").replace(" ", "_").lower()

        if location:
            base_filename = f"{location}_{poi_type_str}_{poi_name_str}"
        else:
            base_filename = f"{poi_type_str}_{poi_name_str}"

        # Apply POI limit if specified
        if max_poi_count and "pois" in poi_data and len(poi_data["pois"]) > max_poi_count:
            original_count = len(poi_data["pois"])
            poi_data["pois"] = random.sample(poi_data["pois"], max_poi_count)
            poi_data["poi_count"] = len(poi_data["pois"])
            print(f"Sampled {max_poi_count} POIs from {original_count} total POIs")
            sampled_pois = True

            # Add sampling info to metadata
            if "metadata" not in poi_data:
                poi_data["metadata"] = {}
            poi_data["metadata"]["sampled"] = True
            poi_data["metadata"]["original_count"] = original_count

        print(f"Found {len(poi_data['pois'])} POIs")

        # Extract state from config if available
        state_name = config.get("state")
        if state_name:
            state_abbr = census_system.normalize_state(state_name, to_format=StateFormat.ABBREVIATION)
            if state_abbr and state_abbr not in state_abbreviations:
                state_abbreviations.append(state_abbr)
                print(f"Using state from parameters: {state_name} ({state_abbr})")

    # Validate that we have POIs to process
    if not poi_data or "pois" not in poi_data or not poi_data["pois"]:
        raise ValueError(
            "No POIs found to analyze. Please try different search criteria or check your input data."
        )

    return poi_data, base_filename, state_abbreviations, sampled_pois
