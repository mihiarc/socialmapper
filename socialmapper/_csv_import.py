"""Internal CSV import utilities for SocialMapper."""

import csv
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def parse_csv_pois(
    csv_path: str,
    name_field: str,
    lat_field: str,
    lon_field: str,
    type_field: str
) -> List[Dict[str, Any]]:
    """Parse POIs from a CSV file.

    Args:
        csv_path: Path to the CSV file
        name_field: Column name for POI names
        lat_field: Column name for latitude
        lon_field: Column name for longitude
        type_field: Column name for POI type

    Returns
    -------
        List of POI dicts in standard format
    """
    # Security: Validate and sanitize file path
    csv_file = Path(csv_path)

    # Resolve to absolute path and check for path traversal
    try:
        csv_file = csv_file.resolve(strict=False)
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Invalid file path: {e}")

    # Ensure file has .csv extension
    if csv_file.suffix.lower() != '.csv':
        raise ValueError(f"File must have .csv extension, got: {csv_file.suffix}")

    # Check file exists and is a regular file
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    if not csv_file.is_file():
        raise ValueError(f"Path is not a regular file: {csv_path}")

    # Optional: Check file is within allowed directory
    # This can be configured based on deployment needs
    # allowed_dir = Path.cwd() / "data"
    # if not str(csv_file).startswith(str(allowed_dir)):
    #     raise ValueError("File access not allowed outside data directory")

    pois = []

    # Map common column name variations
    lat_variations = [lat_field, "lat", "latitude", "y", "LAT", "Latitude", "Y"]
    lon_variations = [lon_field, "lon", "lng", "longitude", "x", "LON", "Longitude", "X"]
    name_variations = [name_field, "name", "Name", "NAME", "title", "Title"]
    type_variations = [type_field, "type", "Type", "TYPE", "category", "Category"]

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        # Find the actual column names
        lat_col = next((h for h in headers if h in lat_variations), None)
        lon_col = next((h for h in headers if h in lon_variations), None)
        name_col = next((h for h in headers if h in name_variations), None)
        type_col = next((h for h in headers if h in type_variations), None)

        if not lat_col or not lon_col:
            available_cols = ", ".join(headers) if headers else "none"
            raise ValueError(
                f"Could not find latitude/longitude columns. "
                f"Looking for lat: {lat_variations}, lon: {lon_variations}. "
                f"Available columns: {available_cols}"
            )

        for i, row in enumerate(reader):
            try:
                lat = float(row[lat_col])
                lon = float(row[lon_col])

                # Validate coordinates
                if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                    logger.warning(f"Invalid coordinates in row {i+1}: ({lat}, {lon})")
                    continue

                # Get name
                if name_col and row.get(name_col):
                    name = row[name_col]
                else:
                    name = f"Location {i+1}"

                # Get type
                if type_col and row.get(type_col):
                    poi_type = row[type_col]
                else:
                    poi_type = "custom"

                poi = {
                    "name": name,
                    "lat": lat,
                    "lon": lon,
                    "type": poi_type,
                    "tags": {}
                }

                # Add other columns as tags
                for key, value in row.items():
                    if key not in [lat_col, lon_col, name_col, type_col] and value:
                        poi["tags"][key] = value

                pois.append(poi)

            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping row {i+1}: {e}")
                continue

    if not pois:
        raise ValueError(f"No valid POIs found in {csv_path}")

    logger.info(f"Imported {len(pois)} POIs from {csv_path}")
    return pois