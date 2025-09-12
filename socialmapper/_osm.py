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
    """Query POIs within a given area using Overpass API.
    
    Args:
        area: Shapely Polygon defining search area
        categories: List of category names to filter, or None for all
    
    Returns:
        List of POI dicts with name, category, coordinates, etc.
    """
    # Build Overpass query
    query = build_overpass_query(area, categories)
    
    # Execute query
    pois = execute_overpass_query(query)
    
    # Process and categorize results
    return process_poi_results(pois)


def build_overpass_query(area: Polygon, categories: Optional[List[str]]) -> str:
    """Build an Overpass QL query for POIs in an area.
    
    Args:
        area: Search area polygon
        categories: Categories to filter for
    
    Returns:
        Overpass QL query string
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
    """Execute an Overpass API query.
    
    Args:
        query: Overpass QL query string
    
    Returns:
        List of raw POI elements from Overpass
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
    """Process raw Overpass elements into clean POI dicts.
    
    Args:
        elements: Raw elements from Overpass API
    
    Returns:
        List of processed POI dicts
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
    """Determine the category of a POI from its OSM tags.
    
    Args:
        tags: OSM tags dict
    
    Returns:
        Category name string
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