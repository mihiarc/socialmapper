"""File writers for various output formats."""

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)


def write_csv(
    data: pd.DataFrame | dict[str, Any], filepath: Path, metadata: dict[str, Any] | None = None
) -> None:
    """Write data to CSV file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data, dict):
        # Convert dict to DataFrame
        df = pd.DataFrame(data)
    else:
        df = data

    df.to_csv(filepath, index=False)
    logger.info(f"Wrote CSV to {filepath} ({len(df)} rows)")


def write_parquet(
    data: pd.DataFrame, filepath: Path, metadata: dict[str, Any] | None = None
) -> None:
    """Write DataFrame to Parquet file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    data.to_parquet(filepath, index=False, compression="snappy")
    logger.info(f"Wrote Parquet to {filepath} ({len(data)} rows)")


def write_geoparquet(
    data: gpd.GeoDataFrame, filepath: Path, metadata: dict[str, Any] | None = None
) -> None:
    """Write GeoDataFrame to GeoParquet file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    data.to_parquet(filepath, index=False, compression="snappy")
    logger.info(f"Wrote GeoParquet to {filepath} ({len(data)} features)")


def write_geojson(
    data: gpd.GeoDataFrame | dict[str, Any], filepath: Path, metadata: dict[str, Any] | None = None
) -> None:
    """Write data to GeoJSON file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data, gpd.GeoDataFrame):
        data.to_file(filepath, driver="GeoJSON")
        logger.info(f"Wrote GeoJSON to {filepath} ({len(data)} features)")
    else:
        # Assume it's already a GeoJSON dict
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Wrote GeoJSON to {filepath}")


def write_json(
    data: dict[str, Any], filepath: Path, metadata: dict[str, Any] | None = None
) -> None:
    """Write data to JSON file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Wrote JSON to {filepath}")


def write_map(
    figure: plt.Figure | Any, filepath: Path, metadata: dict[str, Any] | None = None
) -> None:
    """Write a map/plot to image file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Default DPI and format
    dpi = metadata.get("dpi", 300) if metadata else 300
    format = filepath.suffix[1:] or "png"

    if hasattr(figure, "savefig"):
        # Matplotlib figure
        figure.savefig(filepath, dpi=dpi, format=format, bbox_inches="tight")
        plt.close(figure)
    elif hasattr(figure, "save"):
        # Custom map object with save method
        figure.save(filepath, format=format, dpi=dpi)
    else:
        raise ValueError(f"Don't know how to save object of type {type(figure)}")

    logger.info(f"Wrote map to {filepath}")


def write_html(content: str, filepath: Path, metadata: dict[str, Any] | None = None) -> None:
    """Write HTML content to file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Wrote HTML to {filepath}")


# Registry of writers by file type
WRITERS: dict[str, Callable] = {
    "csv": write_csv,
    "parquet": write_parquet,
    "geoparquet": write_geoparquet,
    "geojson": write_geojson,
    "json": write_json,
    "map": write_map,
    "html": write_html,
    "isochrone": write_geoparquet,  # Isochrones are GeoParquet
}
