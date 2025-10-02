"""POI extraction module for the SocialMapper pipeline.

This module handles extraction of POI data from custom files or OpenStreetMap.
"""

import csv
import json
import random
from pathlib import Path
from typing import Any
from urllib.error import URLError

from ..exceptions import (
    FileNotFoundError as SocialMapperFileNotFoundError,
)
from ..exceptions import (
    FileSystemError,
    NoDataFoundError,
)
from ..util import PathSecurityError, sanitize_path
from ..util.error_handling import validate_type


def parse_custom_coordinates(
    file_path: str,
    name_field: str | None = None,
    type_field: str | None = None,
    preserve_original: bool = True,
) -> dict:
    """
    Parse custom coordinates from JSON or CSV files into POI format.

    Converts various coordinate file formats into the standardized POI
    structure required by the isochrone generator, with flexible field
    mapping and property preservation.

    Parameters
    ----------
    file_path : str
        Path to the custom coordinates file (JSON or CSV).
    name_field : str or None, optional
        Field name to extract POI names from, by default uses 'name'.
    type_field : str or None, optional
        Field name to extract POI types from, by default uses 'type'.
    preserve_original : bool, optional
        Whether to preserve all original properties in the tags dict,
        by default True.

    Returns
    -------
    dict
        Dictionary with structure:
        - 'pois': List of POI dictionaries with lat, lon, name, type, tags
        - 'metadata': Source information and POI count

    Raises
    ------
    FileSystemError
        If the file path contains security risks.
    SocialMapperFileNotFoundError
        If the specified file doesn't exist.
    ValueError
        If the file format is unsupported or no valid coordinates found.

    Notes
    -----
    Supports multiple coordinate field names:
    - Latitude: 'lat', 'latitude', 'y'
    - Longitude: 'lon', 'lng', 'longitude', 'x'

    Examples
    --------
    >>> # Parse JSON file
    >>> poi_data = parse_custom_coordinates(
    ...     "locations.json",
    ...     name_field="business_name"
    ... )
    >>> print(f"Loaded {poi_data['metadata']['count']} POIs")

    >>> # Parse CSV with custom fields
    >>> poi_data = parse_custom_coordinates(
    ...     "stores.csv",
    ...     name_field="store_name",
    ...     type_field="category"
    ... )
    """
    # Validate inputs
    validate_type(file_path, str, "file_path")

    # Sanitize the file path
    try:
        safe_file_path = sanitize_path(file_path, allow_absolute=True)
    except PathSecurityError as e:
        raise FileSystemError(
            f"Invalid file path: {file_path}", cause=e, file_path=file_path
        ).add_suggestion("Ensure the file path does not contain '..' or other security risks")

    if not safe_file_path.exists():
        raise SocialMapperFileNotFoundError(str(safe_file_path))

    file_extension = safe_file_path.suffix.lower()

    pois = []
    states_found = set()

    if file_extension == ".json":
        with open(safe_file_path) as f:
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
                    # Log warning but don't fail - some POIs might be malformed
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Skipping item missing required coordinates: {item}")
        elif isinstance(data, dict) and "pois" in data:
            pois = data["pois"]

    elif file_extension == ".csv":
        # Use newline="" to ensure correct universal newline handling across platforms
        with open(safe_file_path, newline="") as f:
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
                    print(f"Warning: Skipping row {i + 1} - missing required coordinates")

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
    custom_coords_path: str | None = None,
    geocode_area: str | None = None,
    state: str | None = None,
    city: str | None = None,
    poi_type: str | None = None,
    poi_name: str | None = None,
    additional_tags: dict | None = None,
    name_field: str | None = None,
    type_field: str | None = None,
    max_poi_count: int | None = None,
) -> tuple[dict[str, Any], str, list[str], bool]:
    """
    Extract POI data from custom files or OpenStreetMap.

    Provides a unified interface for obtaining POI data either from
    user-provided coordinate files or by querying OpenStreetMap based
    on location and POI type criteria.

    Parameters
    ----------
    custom_coords_path : str or None, optional
        Path to custom coordinates file (JSON/CSV). If provided,
        skips OSM query.
    geocode_area : str or None, optional
        Area to geocode for OSM query (e.g., "Portland, OR").
    state : str or None, optional
        State for OSM query (name or abbreviation).
    city : str or None, optional
        City name for OSM query.
    poi_type : str or None, optional
        POI type to search for in OSM (e.g., "hospital", "school").
    poi_name : str or None, optional
        Specific POI name to search for in OSM.
    additional_tags : dict or None, optional
        Additional OSM tags to filter results.
    name_field : str or None, optional
        Field name for POI names in custom file.
    type_field : str or None, optional
        Field name for POI types in custom file.
    max_poi_count : int or None, optional
        Maximum number of POIs to process (samples randomly if exceeded).

    Returns
    -------
    tuple[dict[str, Any], str, list[str], bool]
        A tuple containing:
        - poi_data: Dictionary with POIs and metadata
        - base_filename: Suggested filename for outputs
        - state_abbreviations: List of state codes involved
        - sampled_pois: Whether POIs were randomly sampled

    Raises
    ------
    NoDataFoundError
        If no POI data could be extracted from the specified source.
    URLError
        If OSM query fails due to network issues.

    Examples
    --------
    >>> # Extract from custom file
    >>> poi_data, filename, states, sampled = extract_poi_data(
    ...     custom_coords_path="hospitals.csv"
    ... )

    >>> # Query OpenStreetMap
    >>> poi_data, filename, states, sampled = extract_poi_data(
    ...     geocode_area="Seattle, WA",
    ...     poi_type="library",
    ...     max_poi_count=50
    ... )
    """
    from ..census import get_census_system
    from ..census.services.geography_service import StateFormat

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
        file_path = Path(custom_coords_path)
        base_filename = f"custom_{file_path.stem}"

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
        # Query POIs from OpenStreetMap using OSMnx
        print("\n=== Querying Points of Interest ===")

        if not (geocode_area and poi_type and poi_name):
            raise ValueError(
                "Missing required POI parameters: geocode_area, poi_type, and poi_name are required"
            )

        # Normalize state to abbreviation if provided
        state_abbr = (
            census_system.normalize_state(state, to_format=StateFormat.ABBREVIATION)
            if state
            else None
        )

        print(f"Querying OpenStreetMap for: {geocode_area} - {poi_type} - {poi_name}")

        # Use the new OSMnx-based query method
        from ..query.osmnx_query import query_pois_with_fallback
        
        try:
            poi_data = query_pois_with_fallback(
                location=geocode_area,
                poi_type=poi_type,
                poi_name=poi_name,
                state=state_abbr,
                additional_tags=additional_tags,
                use_overpass_fallback=True,  # Enable fallback for robustness
            )
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

        # Generate base filename from POI parameters
        poi_type_str = poi_type
        poi_name_str = poi_name.replace(" ", "_").lower()
        location = geocode_area.replace(" ", "_").lower()

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

        # Extract state from parameters if available
        if state_abbr and state_abbr not in state_abbreviations:
            state_abbreviations.append(state_abbr)
            print(f"Using state from parameters: {state} ({state_abbr})")

    # Validate that we have POIs to process
    if not poi_data or "pois" not in poi_data or not poi_data["pois"]:
        if custom_coords_path:
            raise NoDataFoundError("coordinates", location=custom_coords_path).add_suggestion(
                "Check that the file contains valid lat/lon coordinates"
            )
        else:
            error = NoDataFoundError("POIs", location=geocode_area)
            error.add_suggestion("Try a different POI type or expand the search area")
            error.add_suggestion(f"Verify that {poi_type}:{poi_name} exists in this area")

            # Add specific suggestions for common naming issues
            if " " in geocode_area and "-" not in geocode_area:
                # Suggest hyphenated version for multi-word city names
                hyphenated = geocode_area.replace(" ", "-")
                error.add_suggestion(f"Try using the hyphenated form: {hyphenated}")

            # Check for specific known cities with different OSM names
            known_variations = {
                "fuquay varina": "Fuquay-Varina",
                "winston salem": "Winston-Salem",
                "chapel hill": "Chapel Hill",
                "kitty hawk": "Kitty Hawk",
                "kill devil hills": "Kill Devil Hills",
            }

            location_lower = geocode_area.lower()
            if location_lower in known_variations:
                error.add_suggestion(
                    f"Try using: {known_variations[location_lower]}, {state or 'NC'}"
                )

            raise error

    return poi_data, base_filename, state_abbreviations, sampled_pois
