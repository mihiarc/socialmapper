"""Internal CSV import utilities for SocialMapper."""

import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def parse_csv_pois(
    csv_path: str,
    name_field: str = "name",
    lat_field: str = "latitude",
    lon_field: str = "longitude",
    type_field: str = "type",
) -> list[dict[str, Any]]:
    """Parse POIs from a CSV file into standard format.

    Parameters
    ----------
    csv_path : str
        Path to the CSV file.
    name_field : str
        Column name for POI names.
    lat_field : str
        Column name for latitude values.
    lon_field : str
        Column name for longitude values.
    type_field : str
        Column name for POI type/category.

    Returns
    -------
    list of dict
        POIs in standard format with keys: name, lat, lon, category.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(path)

    required_fields = [name_field, lat_field, lon_field]
    missing = [f for f in required_fields if f not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    pois = []
    for _, row in df.iterrows():
        poi = {
            "name": str(row[name_field]),
            "lat": float(row[lat_field]),
            "lon": float(row[lon_field]),
            "category": str(row[type_field]) if type_field in df.columns else "unknown",
        }
        pois.append(poi)

    logger.info(f"Imported {len(pois)} POIs from {csv_path}")
    return pois
