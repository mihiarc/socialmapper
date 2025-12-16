"""OSMnx-based POI query module for SocialMapper.

This module replaces the direct Overpass API approach with OSMnx's more reliable
features_from_place() method, which handles location name variations better.
"""

import logging
from typing import Any

import osmnx as ox
import pandas as pd
from shapely.geometry import Point

from ..constants import MIN_INDEX_TUPLE_ELEMENTS

logger = logging.getLogger(__name__)

# Configure OSMnx settings for better reliability
ox.settings.use_cache = True
ox.settings.log_console = False
ox.settings.requests_timeout = 180  # 3 minutes timeout


def query_pois_osmnx(
    location: str,
    poi_tags: dict[str, Any],
    state: str | None = None,
) -> dict[str, Any]:
    """
    Query POIs from OpenStreetMap using OSMnx.

    Uses OSMnx's features_from_place method for reliable geocoding and
    POI extraction with better handling of location name variations.

    Parameters
    ----------
    location : str
        Location name (e.g., "Fuquay-Varina", "Denver", "Seattle").
    poi_tags : dict
        OpenStreetMap tags to filter POIs (e.g., {"amenity": "school"}).
    state : str, optional
        State name or abbreviation for disambiguation.

    Returns
    -------
    dict
        POI data dictionary containing:
        - 'poi_count': Number of POIs found
        - 'pois': List of POI dictionaries with:
            - 'id': Unique identifier
            - 'type': POI type from tags
            - 'lat': Latitude coordinate
            - 'lon': Longitude coordinate
            - 'tags': Original OSM tags
            - 'name': POI name (if available)
            - 'state': State code (if available)

    Notes
    -----
    Uses Nominatim geocoding through OSMnx which handles place name
    variations and abbreviations better than direct Overpass queries.

    Examples
    --------
    >>> pois = query_pois_osmnx(
    ...     "Seattle, WA",
    ...     {"amenity": "hospital"}
    ... )
    >>> print(f"Found {pois['poi_count']} hospitals")
    Found 12 hospitals
    """
    # Format location string for OSMnx
    # Add state to location if not already present
    location_query = f"{location}, {state}" if state and ", " not in location else location

    logger.info(f"Querying POIs in '{location_query}' with tags: {poi_tags}")

    try:
        # Use OSMnx's features_from_place which handles name variations better
        # It uses Nominatim geocoding which is more flexible with place names
        gdf = ox.features_from_place(location_query, poi_tags)

        if gdf.empty:
            logger.warning(f"No POIs found for location '{location_query}' with tags {poi_tags}")
            return {"poi_count": 0, "pois": []}

        logger.info(f"Found {len(gdf)} POIs using OSMnx")

        # Convert GeoDataFrame to SocialMapper format
        pois = []

        for idx, row in gdf.iterrows():
            # Get the geometry centroid for lat/lon
            geom = row.geometry

            # Handle different geometry types
            centroid = geom.centroid if hasattr(geom, 'centroid') else geom

            # Extract coordinates
            if isinstance(centroid, Point):
                lon = centroid.x
                lat = centroid.y
            else:
                # Try to get representative point
                try:
                    point = geom.representative_point()
                    lon = point.x
                    lat = point.y
                except (AttributeError, ValueError, TypeError):
                    logger.warning(f"Could not extract coordinates for POI {idx}, skipping")
                    continue

            # Extract OSM ID from the index (OSMnx uses multi-index with element_type and osmid)
            if isinstance(idx, tuple) and len(idx) >= MIN_INDEX_TUPLE_ELEMENTS:
                element_type = idx[0]  # 'node', 'way', or 'relation'
                osmid = idx[1]
            else:
                element_type = 'unknown'
                osmid = str(idx)

            # Build tags dictionary from all non-geometry columns
            tags = {}
            for col in gdf.columns:
                if col != 'geometry' and pd.notna(row[col]):
                    tags[col] = row[col]

            # Create POI entry
            poi = {
                "id": osmid,
                "type": element_type,
                "lat": lat,
                "lon": lon,
                "tags": tags,
            }

            # Add name if available
            if 'name' in tags:
                poi['name'] = tags['name']

            # Add state if provided
            if state:
                poi['state'] = state

            pois.append(poi)

        result = {
            "poi_count": len(pois),
            "pois": pois
        }

        logger.info(f"Successfully extracted {len(pois)} POIs")
        return result

    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Data error querying POIs with OSMnx: {e}")
        logger.debug(f"Location: {location_query}, Tags: {poi_tags}")
        raise
    except (ox._errors.InsufficientResponseError, ConnectionError, TimeoutError) as e:
        logger.error(f"Network error querying POIs with OSMnx: {e}")
        logger.debug(f"Location: {location_query}, Tags: {poi_tags}")

        # Try alternative approach if the first fails
        if ", " not in location_query and state:
            # Try without state if we added it
            logger.info("Retrying without state qualifier...")
            try:
                gdf = ox.features_from_place(location, poi_tags)

                if gdf.empty:
                    return {"poi_count": 0, "pois": []}

                # Process results (same as above)
                pois = []
                for idx, row in gdf.iterrows():
                    geom = row.geometry
                    centroid = geom.centroid if hasattr(geom, 'centroid') else geom

                    if isinstance(centroid, Point):
                        lon = centroid.x
                        lat = centroid.y
                    else:
                        try:
                            point = geom.representative_point()
                            lon = point.x
                            lat = point.y
                        except (AttributeError, ValueError, TypeError):
                            continue

                    if isinstance(idx, tuple) and len(idx) >= MIN_INDEX_TUPLE_ELEMENTS:
                        element_type = idx[0]
                        osmid = idx[1]
                    else:
                        element_type = 'unknown'
                        osmid = str(idx)

                    tags = {}
                    for col in gdf.columns:
                        if col != 'geometry' and pd.notna(row[col]):
                            tags[col] = row[col]

                    poi = {
                        "id": osmid,
                        "type": element_type,
                        "lat": lat,
                        "lon": lon,
                        "tags": tags,
                    }

                    if 'name' in tags:
                        poi['name'] = tags['name']

                    if state:
                        poi['state'] = state

                    pois.append(poi)

                return {"poi_count": len(pois), "pois": pois}

            except (ValueError, KeyError, TypeError, ox._errors.InsufficientResponseError, ConnectionError, TimeoutError) as e2:
                logger.error(f"Retry also failed: {e2}")

        # If all attempts fail, raise the original error
        raise


def build_osmnx_tags(poi_type: str, poi_name: str, additional_tags: dict | None = None) -> dict:
    """Build OSM tags dictionary for OSMnx query.

    Parameters
    ----------
    poi_type : str
        The OSM key (e.g., 'amenity', 'leisure', 'shop').
    poi_name : str
        The OSM value (e.g., 'school', 'park', 'supermarket').
    additional_tags : dict, optional
        Optional additional tags to filter by, by default None.

    Returns
    -------
    dict
        Dictionary of OSM tags for OSMnx query.
    """
    tags = {poi_type: poi_name}

    if additional_tags:
        tags.update(additional_tags)

    return tags


def query_pois_with_fallback(
    location: str,
    poi_type: str,
    poi_name: str,
    state: str | None = None,
    additional_tags: dict | None = None,
    use_overpass_fallback: bool = False,
) -> dict[str, Any]:
    """Query POIs with OSMnx and optional Overpass fallback.

    Parameters
    ----------
    location : str
        Location name.
    poi_type : str
        OSM tag key.
    poi_name : str
        OSM tag value.
    state : str, optional
        Optional state for disambiguation, by default None.
    additional_tags : dict, optional
        Optional additional OSM tags, by default None.
    use_overpass_fallback : bool, optional
        Whether to fall back to Overpass API if OSMnx fails,
        by default False.

    Returns
    -------
    dict
        Dictionary with POI data.
    """
    # Build tags for OSMnx
    tags = build_osmnx_tags(poi_type, poi_name, additional_tags)

    try:
        # Try OSMnx first (more reliable with location names)
        return query_pois_osmnx(location, tags, state)

    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"OSMnx query data error: {e}")
        raise
    except (ox._errors.InsufficientResponseError, ConnectionError, TimeoutError) as e:
        logger.error(f"OSMnx query network error: {e}")

        if use_overpass_fallback:
            logger.info("Falling back to Overpass API...")
            # Import here to avoid circular dependency
            from . import build_overpass_query, create_poi_config, format_results, query_overpass

            try:
                config = create_poi_config(
                    geocode_area=location,
                    state=state,
                    city=location,
                    poi_type=poi_type,
                    poi_name=poi_name,
                    additional_tags=additional_tags
                )
                query = build_overpass_query(config)
                raw_results = query_overpass(query)
                return format_results(raw_results, config)
            except (ValueError, KeyError, TypeError, ConnectionError, TimeoutError) as e2:
                logger.error(f"Overpass fallback also failed: {e2}")
                raise
        else:
            raise
