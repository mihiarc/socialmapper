"""File readers for various input formats."""

import csv
import json
import logging
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

logger = logging.getLogger(__name__)


def read_poi_data(filepath: Path | str) -> dict[str, Any]:
    """Read POI data from various file formats."""
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    file_extension = filepath.suffix.lower()

    if file_extension == ".json":
        return read_poi_json(filepath)
    elif file_extension == ".csv":
        return read_poi_csv(filepath)
    elif file_extension == ".geojson":
        return read_poi_geojson(filepath)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")


def read_poi_json(filepath: Path) -> dict[str, Any]:
    """Read POI data from JSON file."""
    with open(filepath) as f:
        data = json.load(f)

    # Ensure proper structure
    if "pois" not in data:
        # If it's a list, wrap it
        if isinstance(data, list):
            data = {"pois": data}
        else:
            raise ValueError("JSON file must contain 'pois' key or be a list")

    logger.info(f"Read {len(data['pois'])} POIs from {filepath}")
    return data


def read_poi_csv(filepath: Path) -> dict[str, Any]:
    """Read POI data from CSV file."""
    pois = []

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):
            # Try to find lat/lon in different possible column names
            lat = None
            lon = None

            for lat_key in ["lat", "latitude", "y", "LAT", "LATITUDE", "Y"]:
                if row.get(lat_key):
                    try:
                        lat = float(row[lat_key])
                        break
                    except ValueError:
                        continue

            for lon_key in ["lon", "lng", "longitude", "x", "LON", "LNG", "LONGITUDE", "X"]:
                if row.get(lon_key):
                    try:
                        lon = float(row[lon_key])
                        break
                    except ValueError:
                        continue

            if lat is not None and lon is not None:
                poi = {
                    "id": row.get("id", f"poi_{i}"),
                    "name": row.get("name", f"POI {i}"),
                    "lat": lat,
                    "lon": lon,
                    "tags": {
                        k: v
                        for k, v in row.items()
                        if k not in ["id", "name", "lat", "lon", "latitude", "longitude"]
                    },
                }
                pois.append(poi)
            else:
                logger.warning(f"Skipping row {i} - missing valid coordinates")

    logger.info(f"Read {len(pois)} POIs from {filepath}")
    return {"pois": pois}


def read_poi_geojson(filepath: Path) -> dict[str, Any]:
    """Read POI data from GeoJSON file."""
    gdf = gpd.read_file(filepath)
    pois = []

    for idx, row in gdf.iterrows():
        # Extract coordinates from geometry
        if row.geometry.geom_type == "Point":
            lon, lat = row.geometry.x, row.geometry.y
        else:
            # Use centroid for non-point geometries
            centroid = row.geometry.centroid
            lon, lat = centroid.x, centroid.y

        # Create POI dict
        poi = {
            "id": row.get("id", f"poi_{idx}"),
            "name": row.get("name", f"POI {idx}"),
            "lat": lat,
            "lon": lon,
            "tags": {k: v for k, v in row.items() if k not in ["id", "name", "geometry"]},
        }
        pois.append(poi)

    logger.info(f"Read {len(pois)} POIs from {filepath}")
    return {"pois": pois}


def read_custom_pois(
    filepath: Path | str,
    name_field: str | None = None,
    type_field: str | None = None,
) -> list[dict[str, Any]]:
    """Read custom POI coordinates from CSV."""
    filepath = Path(filepath)
    df = pd.read_csv(filepath)

    # Normalize column names
    column_mapping = {
        "latitude": "lat",
        "longitude": "lon",
        "long": "lon",
        "lng": "lon",
        "x": "lon",
        "y": "lat",
    }

    df.columns = [column_mapping.get(col.lower(), col.lower()) for col in df.columns]

    # Validate required columns
    required_cols = ["lat", "lon"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"CSV must contain columns: {', '.join(missing_cols)}")

    # Create POI list
    pois = []
    for idx, row in df.iterrows():
        poi = {
            "id": f"custom_{idx}",
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "tags": {},
        }

        # Add name
        if name_field and name_field in row:
            poi["name"] = row[name_field]
        elif "name" in row:
            poi["name"] = row["name"]
        else:
            poi["name"] = f"Custom POI {idx}"

        # Add type
        if type_field and type_field in row:
            poi["type"] = row[type_field]
        elif "type" in row:
            poi["type"] = row["type"]

        # Add all other fields to tags
        for col in df.columns:
            if col not in ["lat", "lon", "name", "type"]:
                poi["tags"][col] = row[col]

        pois.append(poi)

    logger.info(f"Read {len(pois)} custom POIs from {filepath}")
    return pois


def read_census_data(filepath: Path | str) -> pd.DataFrame:
    """Read census data from CSV or Parquet."""
    filepath = Path(filepath)

    if filepath.suffix.lower() == ".csv":
        return pd.read_csv(filepath)
    elif filepath.suffix.lower() in [".parquet", ".pq"]:
        return pd.read_parquet(filepath)
    else:
        raise ValueError(f"Unsupported census data format: {filepath.suffix}")


def read_geospatial_data(filepath: Path | str) -> gpd.GeoDataFrame:
    """Read geospatial data from various formats."""
    filepath = Path(filepath)

    if filepath.suffix.lower() == ".geojson":
        return gpd.read_file(filepath)
    elif filepath.suffix.lower() in [".geoparquet", ".parquet"]:
        return gpd.read_parquet(filepath)
    elif filepath.suffix.lower() in [".shp", ".gpkg"]:
        return gpd.read_file(filepath)
    else:
        raise ValueError(f"Unsupported geospatial format: {filepath.suffix}")
