"""Internal OpenStreetMap/POI query utilities for SocialMapper."""

import requests
from typing import List, Dict, Any, Optional
from shapely.geometry import Polygon, Point
import logging
import time

logger = logging.getLogger(__name__)


# POI category to OSM tag mappings
CATEGORY_MAPPINGS = {
    # Food & Drink
    "restaurant": ["amenity=restaurant"],
    "cafe": ["amenity=cafe"],
    "bar": ["amenity=bar", "amenity=pub"],
    "fast_food": ["amenity=fast_food"],
    
    # Education
    "school": ["amenity=school"],
    "university": ["amenity=university", "amenity=college"],
    "library": ["amenity=library"],
    
    # Healthcare
    "hospital": ["amenity=hospital"],
    "clinic": ["amenity=clinic", "amenity=doctors"],
    "pharmacy": ["amenity=pharmacy"],
    
    # Recreation
    "park": ["leisure=park", "leisure=garden"],
    "playground": ["leisure=playground"],
    "sports": ["leisure=sports_centre", "leisure=stadium", "leisure=pitch"],
    
    # Shopping
    "grocery": ["shop=supermarket", "shop=convenience"],
    "supermarket": ["shop=supermarket"],
    "convenience": ["shop=convenience"],
    
    # Finance
    "bank": ["amenity=bank"],
    "atm": ["amenity=atm"],
    
    # Transportation
    "gas_station": ["amenity=fuel"],
    "parking": ["amenity=parking"],
    "bus_stop": ["highway=bus_stop"],
}


def query_pois(
    area: Polygon,
    categories: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Query Points of Interest within an area using Overpass API.

    Searches for POIs matching specified categories within a geographic
    area. Uses OpenStreetMap's Overpass API to retrieve POI data with
    automatic retry across multiple endpoints.

    Parameters
    ----------
    area : shapely.geometry.Polygon
        Geographic area to search for POIs. Defines the bounding box
        for the query.
    categories : list of str, optional
        List of POI category names to filter (e.g., 'restaurant',
        'school', 'hospital'). If None, retrieves all common POI
        types, by default None.

    Returns
    -------
    list of dict
        List of POI dictionaries, each containing 'name', 'category',
        'lat', 'lon', 'tags', and optionally 'address'.

    Examples
    --------
    >>> from shapely.geometry import box
    >>> area = box(-122.4, 47.5, -122.3, 47.6)
    >>> pois = query_pois(area, categories=['restaurant', 'cafe'])
    >>> len(pois) > 0
    True
    """
    # Build Overpass query
    query = build_overpass_query(area, categories)
    
    # Execute query
    pois = execute_overpass_query(query)
    
    # Process and categorize results
    return process_poi_results(pois)


def build_overpass_query(area: Polygon, categories: Optional[List[str]]) -> str:
    """
    Build an Overpass QL query string for POI retrieval.

    Constructs a properly formatted Overpass Query Language (QL) string
    to retrieve POIs within a bounding box. Handles multiple categories
    by aggregating their associated OSM tags.

    Parameters
    ----------
    area : shapely.geometry.Polygon
        Geographic area polygon used to determine bounding box for
        the query.
    categories : list of str, optional
        POI categories to include in query. Uses predefined category
        mappings to OSM tags.

    Returns
    -------
    str
        Overpass QL query string ready for API submission.

    Examples
    --------
    >>> from shapely.geometry import box
    >>> area = box(-122.4, 47.5, -122.3, 47.6)
    >>> query = build_overpass_query(area, ['restaurant'])
    >>> 'amenity=restaurant' in query
    True
    """
    # Get bounding box
    bounds = area.bounds  # (minx, miny, maxx, maxy)
    bbox = f"{bounds[1]},{bounds[0]},{bounds[3]},{bounds[2]}"  # S,W,N,E
    
    # Determine which OSM tags to query
    if categories:
        # Collect all OSM tags for requested categories
        tags = []
        for cat in categories:
            if cat in CATEGORY_MAPPINGS:
                tags.extend(CATEGORY_MAPPINGS[cat])
            else:
                # Try to interpret as raw OSM tag
                tags.append(cat)
    else:
        # Get all common POI tags
        tags = []
        for cat_tags in CATEGORY_MAPPINGS.values():
            tags.extend(cat_tags)
    
    # Remove duplicates
    tags = list(set(tags))
    
    # Build Overpass query
    query_parts = ["[out:json][timeout:25];("]
    
    for tag in tags:
        # Parse tag into key=value
        if "=" in tag:
            key, value = tag.split("=", 1)
            query_parts.append(f"node[{key}={value}]({bbox});")
            query_parts.append(f"way[{key}={value}]({bbox});")
    
    query_parts.append(");out center;")
    
    return "".join(query_parts)


def execute_overpass_query(query: str) -> List[Dict[str, Any]]:
    """
    Execute an Overpass API query with automatic endpoint fallback.

    Attempts to execute the query across multiple Overpass API
    endpoints for reliability. Includes timeout handling and retry
    logic with delays between attempts.

    Parameters
    ----------
    query : str
        Overpass QL query string to execute.

    Returns
    -------
    list of dict
        List of raw POI element dictionaries from the Overpass API
        response. Returns empty list if all endpoints fail.

    Examples
    --------
    >>> query = '[out:json];node(47.5,-122.4,47.6,-122.3);out;'
    >>> results = execute_overpass_query(query)
    >>> isinstance(results, list)
    True
    """
    # Try multiple Overpass endpoints
    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.openstreetmap.ru/api/interpreter"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.post(
                endpoint,
                data={"data": query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                elements = data.get("elements", [])
                logger.info(f"Overpass query returned {len(elements)} elements")
                return elements
            else:
                logger.warning(f"Overpass endpoint {endpoint} returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"Overpass endpoint {endpoint} timed out")
        except Exception as e:
            logger.warning(f"Overpass endpoint {endpoint} failed: {e}")
        
        # Small delay before trying next endpoint
        time.sleep(0.5)
    
    logger.error("All Overpass endpoints failed")
    return []


def process_poi_results(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process raw Overpass API elements into standardized POI dicts.

    Extracts and normalizes POI data from Overpass API response,
    including coordinates, names, categories, and addresses. Handles
    both node and way geometries with center point extraction.

    Parameters
    ----------
    elements : list of dict
        Raw element dictionaries from Overpass API response.

    Returns
    -------
    list of dict
        List of standardized POI dictionaries with keys: 'name',
        'category', 'lat', 'lon', 'tags', and optionally 'address'.

    Examples
    --------
    >>> elements = [{'type': 'node', 'lat': 47.6, 'lon': -122.3,
    ...              'tags': {'name': 'Cafe', 'amenity': 'cafe'}}]
    >>> pois = process_poi_results(elements)
    >>> len(pois)
    1
    >>> pois[0]['category'] == 'cafe'
    True
    """
    pois = []
    
    for element in elements:
        # Extract basic info
        tags = element.get("tags", {})
        
        # Skip if no name
        name = tags.get("name")
        if not name:
            # Use type as name if no proper name
            name = tags.get("amenity") or tags.get("shop") or tags.get("leisure") or "Unnamed"
        
        # Get coordinates
        if element["type"] == "node":
            lat = element["lat"]
            lon = element["lon"]
        elif element["type"] == "way" and "center" in element:
            lat = element["center"]["lat"]
            lon = element["center"]["lon"]
        else:
            continue
        
        # Determine category
        category = determine_category(tags)
        
        # Build POI dict
        poi = {
            "name": name,
            "category": category,
            "lat": lat,
            "lon": lon,
            "tags": tags
        }
        
        # Add address if available
        address_parts = []
        if "addr:housenumber" in tags:
            address_parts.append(tags["addr:housenumber"])
        if "addr:street" in tags:
            address_parts.append(tags["addr:street"])
        if "addr:city" in tags:
            address_parts.append(tags["addr:city"])
        if "addr:state" in tags:
            address_parts.append(tags["addr:state"])
        if "addr:postcode" in tags:
            address_parts.append(tags["addr:postcode"])
        
        if address_parts:
            poi["address"] = " ".join(address_parts)
        
        pois.append(poi)
    
    return pois


def determine_category(tags: Dict[str, str]) -> str:
    """
    Determine POI category from OpenStreetMap tags.

    Maps OSM tags to standardized POI categories using predefined
    category mappings. Falls back to primary tag type if no mapping
    matches.

    Parameters
    ----------
    tags : dict
        Dictionary of OSM tags (key-value pairs) from a POI element.

    Returns
    -------
    str
        Standardized category name (e.g., 'restaurant', 'school',
        'park') or primary tag type. Returns 'other' if no
        recognizable tags found.

    Examples
    --------
    >>> tags = {'amenity': 'restaurant', 'name': 'Pizza Place'}
    >>> determine_category(tags)
    'restaurant'

    >>> tags = {'shop': 'supermarket'}
    >>> determine_category(tags)
    'grocery'
    """
    # Check each category's tags
    for category, osm_tags in CATEGORY_MAPPINGS.items():
        for osm_tag in osm_tags:
            if "=" in osm_tag:
                key, value = osm_tag.split("=", 1)
                if tags.get(key) == value:
                    return category
    
    # Fallback to primary tag
    if "amenity" in tags:
        return tags["amenity"]
    elif "shop" in tags:
        return tags["shop"]
    elif "leisure" in tags:
        return tags["leisure"]
    elif "tourism" in tags:
        return tags["tourism"]
    else:
        return "other"