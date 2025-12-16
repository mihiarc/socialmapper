"""Internal OpenStreetMap/POI query utilities for SocialMapper."""

import logging
import time
from typing import Any

import requests
from shapely.geometry import Polygon

from .constants import (
    HTTP_OK,
    HTTP_RATE_LIMITED,
    HTTP_SERVER_ERROR,
    OVERPASS_ENDPOINTS,
    OVERPASS_TIMEOUT,
)
from .poi_categorization import POI_CATEGORY_MAPPING

logger = logging.getLogger(__name__)


# OSM key mappings for building Overpass queries
# Maps OSM tag values to their key=value format for Overpass API
OSM_KEY_MAPPINGS = {
    # Amenity tags
    "restaurant": "amenity=restaurant",
    "cafe": "amenity=cafe",
    "bar": "amenity=bar",
    "pub": "amenity=pub",
    "fast_food": "amenity=fast_food",
    "food_court": "amenity=food_court",
    "ice_cream": "amenity=ice_cream",
    "biergarten": "amenity=biergarten",
    "nightclub": "amenity=nightclub",
    "school": "amenity=school",
    "university": "amenity=university",
    "college": "amenity=college",
    "library": "amenity=library",
    "kindergarten": "amenity=kindergarten",
    "hospital": "amenity=hospital",
    "clinic": "amenity=clinic",
    "doctors": "amenity=doctors",
    "dentist": "amenity=dentist",
    "pharmacy": "amenity=pharmacy",
    "veterinary": "amenity=veterinary",
    "bank": "amenity=bank",
    "atm": "amenity=atm",
    "post_office": "amenity=post_office",
    "fuel": "amenity=fuel",
    "parking": "amenity=parking",
    "cinema": "amenity=cinema",
    "theatre": "amenity=theatre",
    "place_of_worship": "amenity=place_of_worship",
    "community_centre": "amenity=community_centre",
    "toilets": "amenity=toilets",
    # Shop tags
    "supermarket": "shop=supermarket",
    "convenience": "shop=convenience",
    "bakery": "shop=bakery",
    "butcher": "shop=butcher",
    "clothes": "shop=clothes",
    "electronics": "shop=electronics",
    "furniture": "shop=furniture",
    "hardware": "shop=hardware",
    "mall": "shop=mall",
    "department_store": "shop=department_store",
    "books": "shop=books",
    "florist": "shop=florist",
    "optician": "shop=optician",
    "hairdresser": "shop=hairdresser",
    # Leisure tags
    "park": "leisure=park",
    "playground": "leisure=playground",
    "sports_centre": "leisure=sports_centre",
    "stadium": "leisure=stadium",
    "pitch": "leisure=pitch",
    "swimming_pool": "leisure=swimming_pool",
    "fitness_centre": "leisure=fitness_centre",
    "garden": "leisure=garden",
    "golf_course": "leisure=golf_course",
    "marina": "leisure=marina",
    # Tourism tags
    "hotel": "tourism=hotel",
    "motel": "tourism=motel",
    "hostel": "tourism=hostel",
    "guest_house": "tourism=guest_house",
    "museum": "tourism=museum",
    "gallery": "tourism=gallery",
    "zoo": "tourism=zoo",
    "aquarium": "tourism=aquarium",
    "theme_park": "tourism=theme_park",
    "attraction": "tourism=attraction",
    # Office tags
    "office": "office=yes",
    "lawyer": "office=lawyer",
    "insurance": "office=insurance",
    "estate_agent": "office=estate_agent",
    # Healthcare tags
    "healthcare": "healthcare=yes",
    # Religion tags
    "church": "building=church",
    "mosque": "building=mosque",
    "temple": "building=temple",
    "synagogue": "building=synagogue",
}


def query_pois(
    area: Polygon,
    categories: list[str] | None = None
) -> list[dict[str, Any]]:
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


def _expand_categories_to_osm_tags(categories: list[str] | None) -> list[str]:
    """
    Expand category names to OSM tags for Overpass API queries.

    Handles both high-level categories (like 'food_and_drink') from
    POI_CATEGORY_MAPPING and individual OSM values (like 'restaurant').
    Only uses tags that have known OSM key mappings to avoid overly
    large queries.

    Parameters
    ----------
    categories : list of str, optional
        Category names from POI_CATEGORY_MAPPING or individual OSM values.

    Returns
    -------
    list of str
        List of OSM tags in key=value format (e.g., 'amenity=restaurant').
    """
    tags = []

    if not categories:
        # Get common tags from all categories - only known mappings
        for cat_values in POI_CATEGORY_MAPPING.values():
            tags.extend(
                OSM_KEY_MAPPINGS[value]
                for value in cat_values[:10]  # Limit to top 10 per category
                if value in OSM_KEY_MAPPINGS
            )
        return list(set(tags))

    for cat in categories:
        # Check if it's a high-level category (e.g., "food_and_drink")
        if cat in POI_CATEGORY_MAPPING:
            # Expand to OSM values that have known key mappings
            tags.extend(
                OSM_KEY_MAPPINGS[value]
                for value in POI_CATEGORY_MAPPING[cat]
                if value in OSM_KEY_MAPPINGS
            )
        # Check if it's an individual OSM value (e.g., "restaurant")
        elif cat in OSM_KEY_MAPPINGS:
            tags.append(OSM_KEY_MAPPINGS[cat])
        # Try as raw OSM tag if it contains =
        elif "=" in cat:
            tags.append(cat)
        else:
            # Try common OSM key for unknown values
            tags.append(f"amenity={cat}")

    return list(set(tags))


def build_overpass_query(area: Polygon, categories: list[str] | None) -> str:
    """
    Build an Overpass QL query string for POI retrieval.

    Constructs a properly formatted Overpass Query Language (QL) string
    to retrieve POIs within a bounding box. Handles both high-level
    categories (e.g., 'food_and_drink') and specific OSM values
    (e.g., 'restaurant').

    Parameters
    ----------
    area : shapely.geometry.Polygon
        Geographic area polygon used to determine bounding box for
        the query.
    categories : list of str, optional
        POI categories to include in query. Supports:
        - High-level categories: 'food_and_drink', 'healthcare', etc.
        - Specific OSM values: 'restaurant', 'hospital', etc.
        - Raw OSM tags: 'amenity=cafe', 'shop=supermarket', etc.

    Returns
    -------
    str
        Overpass QL query string ready for API submission.

    Examples
    --------
    >>> from shapely.geometry import box
    >>> area = box(-122.4, 47.5, -122.3, 47.6)
    >>> query = build_overpass_query(area, ['food_and_drink'])
    >>> 'amenity=restaurant' in query
    True
    """
    # Get bounding box
    bounds = area.bounds  # (minx, miny, maxx, maxy)
    bbox = f"{bounds[1]},{bounds[0]},{bounds[3]},{bounds[2]}"  # S,W,N,E

    # Expand categories to OSM tags
    tags = _expand_categories_to_osm_tags(categories)

    if not tags:
        logger.warning("No valid OSM tags found for categories: %s", categories)
        # Default to common POI types
        tags = [
            "amenity=restaurant", "amenity=cafe", "amenity=hospital",
            "amenity=school", "shop=supermarket", "leisure=park"
        ]

    logger.debug("Building Overpass query with %d tags for categories: %s", len(tags), categories)

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


def execute_overpass_query(query: str) -> list[dict[str, Any]]:
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
    last_error = None

    for endpoint in OVERPASS_ENDPOINTS:
        try:
            response = requests.post(
                endpoint,
                data={"data": query},
                timeout=OVERPASS_TIMEOUT
            )

            if response.status_code == HTTP_OK:
                data = response.json()
                elements = data.get("elements", [])
                logger.info(f"Overpass query returned {len(elements)} elements")
                return elements
            elif response.status_code == HTTP_RATE_LIMITED:
                from .exceptions import RateLimitError
                logger.warning(f"Overpass endpoint {endpoint} returned rate limit")
                last_error = RateLimitError("OpenStreetMap Overpass API")
            elif response.status_code >= HTTP_SERVER_ERROR:
                from .exceptions import InvalidAPIResponseError
                logger.warning(f"Overpass endpoint {endpoint} returned server error {response.status_code}")
                last_error = InvalidAPIResponseError(
                    "OpenStreetMap Overpass API",
                    status_code=response.status_code
                )
            else:
                logger.warning(f"Overpass endpoint {endpoint} returned status {response.status_code}")

        except requests.exceptions.Timeout:
            from .exceptions import NetworkError
            logger.warning(f"Overpass endpoint {endpoint} timed out")
            last_error = NetworkError("OpenStreetMap Overpass API", "Request timed out")
        except requests.exceptions.ConnectionError as e:
            from .exceptions import NetworkError
            logger.warning(f"Overpass endpoint {endpoint} connection error: {e}")
            last_error = NetworkError("OpenStreetMap Overpass API", str(e))
        except requests.exceptions.RequestException as e:
            from .exceptions import NetworkError
            logger.warning(f"Overpass endpoint {endpoint} request error: {e}")
            last_error = NetworkError("OpenStreetMap Overpass API", str(e))
        except (ValueError, KeyError) as e:
            from .exceptions import DataError
            logger.warning(f"Overpass endpoint {endpoint} returned invalid data: {e}")
            last_error = DataError(f"Invalid response from Overpass API: {e}")

        # Small delay before trying next endpoint
        time.sleep(0.5)

    # All endpoints failed, raise the most helpful error
    logger.error("All Overpass endpoints failed")
    if last_error and isinstance(last_error, Exception):
        raise last_error
    else:
        from .exceptions import APIError
        raise APIError("All OpenStreetMap Overpass API endpoints failed")


def process_poi_results(elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
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


def determine_category(tags: dict[str, str]) -> str:
    """
    Determine POI category from OpenStreetMap tags.

    Maps OSM tags to standardized POI categories using the
    POI_CATEGORY_MAPPING from poi_categorization module.

    Parameters
    ----------
    tags : dict
        Dictionary of OSM tags (key-value pairs) from a POI element.

    Returns
    -------
    str
        Standardized category name (e.g., 'food_and_drink', 'shopping',
        'healthcare') or 'other' if no match found.

    Examples
    --------
    >>> tags = {'amenity': 'restaurant', 'name': 'Pizza Place'}
    >>> determine_category(tags)
    'food_and_drink'

    >>> tags = {'shop': 'supermarket'}
    >>> determine_category(tags)
    'shopping'
    """
    # Check OSM tag values against POI_CATEGORY_MAPPING
    osm_keys = ["amenity", "shop", "leisure", "tourism", "healthcare", "office"]

    for osm_key in osm_keys:
        if osm_key in tags:
            tag_value = tags[osm_key].lower()

            # Check each category's values
            for category, values in POI_CATEGORY_MAPPING.items():
                if tag_value in [v.lower() for v in values]:
                    return category

    # If no match, return raw OSM tag value for transparency
    for osm_key in osm_keys:
        if osm_key in tags:
            return tags[osm_key]

    return "other"
