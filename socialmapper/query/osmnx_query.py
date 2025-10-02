"""OSMnx-based POI query module for SocialMapper.

This module replaces the direct Overpass API approach with OSMnx's more reliable
features_from_place() method, which handles location name variations better.
"""

import sys
from typing import Any, Optional

import osmnx as ox
import pandas as pd
from shapely.geometry import Point

import logging

logger = logging.getLogger(__name__)

# Configure OSMnx settings for better reliability
ox.settings.use_cache = True
ox.settings.log_console = False
ox.settings.requests_timeout = 180  # 3 minutes timeout


def query_pois_osmnx(
    location: str,
    poi_tags: dict[str, Any],
    state: Optional[str] = None,
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
    if state and ", " not in location:
        # Add state to location if not already present
        location_query = f"{location}, {state}"
    else:
        location_query = location
    
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
            if hasattr(geom, 'centroid'):
                centroid = geom.centroid
            else:
                centroid = geom
            
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
                except:
                    logger.warning(f"Could not extract coordinates for POI {idx}, skipping")
                    continue
            
            # Extract OSM ID from the index (OSMnx uses multi-index with element_type and osmid)
            if isinstance(idx, tuple) and len(idx) >= 2:
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
        
    except Exception as e:
        logger.error(f"Error querying POIs with OSMnx: {e}")
        logger.debug(f"Location: {location_query}, Tags: {poi_tags}")
        
        # Try alternative approach if the first fails
        if ", " not in location_query and state:
            # Try without state if we added it
            logger.info(f"Retrying without state qualifier...")
            try:
                gdf = ox.features_from_place(location, poi_tags)
                
                if gdf.empty:
                    return {"poi_count": 0, "pois": []}
                
                # Process results (same as above)
                pois = []
                for idx, row in gdf.iterrows():
                    geom = row.geometry
                    if hasattr(geom, 'centroid'):
                        centroid = geom.centroid
                    else:
                        centroid = geom
                    
                    if isinstance(centroid, Point):
                        lon = centroid.x
                        lat = centroid.y
                    else:
                        try:
                            point = geom.representative_point()
                            lon = point.x
                            lat = point.y
                        except:
                            continue
                    
                    if isinstance(idx, tuple) and len(idx) >= 2:
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
                
            except Exception as e2:
                logger.error(f"Retry also failed: {e2}")
        
        # If all attempts fail, raise the original error
        raise


def build_osmnx_tags(poi_type: str, poi_name: str, additional_tags: Optional[dict] = None) -> dict:
    """Build OSM tags dictionary for OSMnx query.
    
    Args:
        poi_type: The OSM key (e.g., 'amenity', 'leisure', 'shop')
        poi_name: The OSM value (e.g., 'school', 'park', 'supermarket')
        additional_tags: Optional additional tags to filter by
        
    Returns:
        Dictionary of OSM tags for OSMnx query
    """
    tags = {poi_type: poi_name}
    
    if additional_tags:
        tags.update(additional_tags)
    
    return tags


def query_pois_with_fallback(
    location: str,
    poi_type: str,
    poi_name: str,
    state: Optional[str] = None,
    additional_tags: Optional[dict] = None,
    use_overpass_fallback: bool = False,
) -> dict[str, Any]:
    """Query POIs with OSMnx as primary method and optional Overpass fallback.
    
    Args:
        location: Location name
        poi_type: OSM tag key
        poi_name: OSM tag value
        state: Optional state for disambiguation
        additional_tags: Optional additional OSM tags
        use_overpass_fallback: Whether to fall back to Overpass API if OSMnx fails
        
    Returns:
        Dictionary with POI data
    """
    # Build tags for OSMnx
    tags = build_osmnx_tags(poi_type, poi_name, additional_tags)
    
    try:
        # Try OSMnx first (more reliable with location names)
        return query_pois_osmnx(location, tags, state)
        
    except Exception as e:
        logger.error(f"OSMnx query failed: {e}")
        
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
            except Exception as e2:
                logger.error(f"Overpass fallback also failed: {e2}")
                raise
        else:
            raise