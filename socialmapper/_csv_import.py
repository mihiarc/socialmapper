"""Internal CSV import utilities for SocialMapper."""

import logging
import math
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
    skipped_count = 0
    for row_idx, row in df.iterrows():
        # Validate coordinate values
        try:
            lat_value = float(row[lat_field])
            lon_value = float(row[lon_field])
        except (ValueError, TypeError):
            skipped_count += 1
            logger.warning(
                "Row %s: non-numeric coordinates (%s, %s), skipping",
                row_idx, row[lat_field], row[lon_field],
            )
            continue

        # Check for NaN
        if math.isnan(lat_value) or math.isnan(lon_value):
            skipped_count += 1
            logger.warning("Row %s: NaN coordinates, skipping", row_idx)
            continue

        # Validate coordinate ranges
        if not (-90 <= lat_value <= 90):
            skipped_count += 1
            logger.warning(
                "Row %s: latitude %s out of range [-90, 90], skipping",
                row_idx, lat_value,
            )
            continue

        if not (-180 <= lon_value <= 180):
            skipped_count += 1
            logger.warning(
                "Row %s: longitude %s out of range [-180, 180], skipping",
                row_idx, lon_value,
            )
            continue

        poi = {
            "name": str(row[name_field]),
            "lat": lat_value,
            "lon": lon_value,
            "category": str(row[type_field]) if type_field in df.columns else "unknown",
        }
        pois.append(poi)

    if skipped_count > 0:
        logger.warning(
            "Skipped %d of %d rows due to invalid coordinates",
            skipped_count, len(df),
        )

    logger.info("Imported %d POIs from %s", len(pois), csv_path)
    return pois
