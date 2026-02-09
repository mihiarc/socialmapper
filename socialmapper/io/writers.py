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

    df = pd.DataFrame(data) if isinstance(data, dict) else data

    df.to_csv(filepath, index=False)
    logger.info("Wrote CSV to %s (%d rows)", filepath, len(df))


def write_parquet(
    data: pd.DataFrame, filepath: Path, metadata: dict[str, Any] | None = None
) -> None:
    """Write DataFrame to Parquet file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    data.to_parquet(filepath, index=False, compression="snappy")
    logger.info("Wrote Parquet to %s (%d rows)", filepath, len(data))


def write_geoparquet(
    data: gpd.GeoDataFrame, filepath: Path, metadata: dict[str, Any] | None = None
) -> None:
    """Write GeoDataFrame to GeoParquet file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    data.to_parquet(filepath, index=False, compression="snappy")
    logger.info("Wrote GeoParquet to %s (%d features)", filepath, len(data))


def write_geojson(
    data: gpd.GeoDataFrame | dict[str, Any], filepath: Path, metadata: dict[str, Any] | None = None
) -> None:
    """Write data to GeoJSON file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data, gpd.GeoDataFrame):
        data.to_file(filepath, driver="GeoJSON")
        logger.info("Wrote GeoJSON to %s (%d features)", filepath, len(data))
    else:
        # Assume it's already a GeoJSON dict
        with filepath.open("w") as f:
            json.dump(data, f, indent=2)
        logger.info("Wrote GeoJSON to %s", filepath)


def write_json(
    data: dict[str, Any], filepath: Path, metadata: dict[str, Any] | None = None
) -> None:
    """Write data to JSON file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with filepath.open("w") as f:
        json.dump(data, f, indent=2)

    logger.info("Wrote JSON to %s", filepath)


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

    logger.info("Wrote map to %s", filepath)


def write_html(content: str, filepath: Path, metadata: dict[str, Any] | None = None) -> None:
    """Write HTML content to file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with filepath.open("w", encoding="utf-8") as f:
        f.write(content)

    logger.info("Wrote HTML to %s", filepath)


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
