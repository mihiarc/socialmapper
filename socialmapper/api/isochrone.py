"""Simple isochrone API for SocialMapper.

Direct access to isochrone generation without unnecessary abstractions.
"""

from typing import Optional, Union, Tuple
import geopandas as gpd
from shapely.geometry import Point

from ..isochrone import TravelMode, create_isochrone_from_poi
from ..geocoding import geocode_address
from ..console import get_logger

logger = get_logger(__name__)


def create_isochrone(
    location: Union[str, Tuple[float, float]],
    travel_time: int = 15,
    travel_mode: str = "drive",
    simplify: bool = True,
    return_type: str = "geometry"
) -> Union[gpd.GeoDataFrame, dict]:
    """Create an isochrone (travel-time polygon) from a location.
    
    This is the core spatial analysis function that generates a polygon 
    representing all areas reachable within a given travel time.
    
    Args:
        location: Either "City, State" string or (latitude, longitude) tuple
        travel_time: Travel time in minutes (1-120)
        travel_mode: Mode of travel ("drive", "walk", "bike")
        simplify: Whether to simplify the geometry for smaller size
        return_type: "geometry" for GeoDataFrame, "dict" for GeoJSON-like dict
        
    Returns:
        GeoDataFrame with isochrone polygon or dict representation
        
    Raises:
        ValueError: If inputs are invalid
        RuntimeError: If isochrone generation fails
        
    Example:
        ```python
        # From city name
        isochrone = create_isochrone("Portland, OR", travel_time=20)
        
        # From coordinates  
        isochrone = create_isochrone((45.5152, -122.6784), travel_time=15)
        
        # Get as dict for JSON serialization
        iso_dict = create_isochrone("Boston, MA", return_type="dict")
        ```
    """
    # Validate inputs
    if not 1 <= travel_time <= 120:
        raise ValueError(f"Travel time must be between 1 and 120 minutes, got {travel_time}")
    
    if travel_mode not in ["drive", "walk", "bike"]:
        raise ValueError(f"Travel mode must be 'drive', 'walk', or 'bike', got {travel_mode}")
    
    # Get coordinates
    if isinstance(location, str):
        # Geocode the location
        from ..geocoding.models import AddressInput, GeocodingConfig, AddressProvider
        from ..geocoding.engine import AddressGeocodingEngine
        
        config = GeocodingConfig(
            primary_provider=AddressProvider.NOMINATIM,
            fallback_providers=[AddressProvider.CENSUS]
        )
        engine = AddressGeocodingEngine(config)
        result = engine.geocode_address(AddressInput(address=location))
        
        if not result or not result.success:
            raise ValueError(f"Failed to geocode location: {location}")
        
        lat, lon = result.latitude, result.longitude
        location_name = location
    elif isinstance(location, (tuple, list)) and len(location) == 2:
        lat, lon = location
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError(f"Invalid coordinates: {location}")
        location_name = f"{lat:.4f}, {lon:.4f}"
    else:
        raise ValueError("Location must be 'City, State' string or (lat, lon) tuple")
    
    # Map travel mode string to enum
    mode_map = {
        "drive": TravelMode.DRIVE,
        "walk": TravelMode.WALK,
        "bike": TravelMode.BIKE
    }
    travel_mode_enum = mode_map[travel_mode]
    
    # Create POI dict for the isochrone function
    poi = {
        "lat": lat,
        "lon": lon,
        "tags": {"name": location_name}
    }
    
    # Generate isochrone
    logger.info(f"Creating {travel_time}-minute {travel_mode} isochrone for {location_name}")
    
    try:
        # Generate without saving to file
        isochrone_gdf = create_isochrone_from_poi(
            poi=poi,
            travel_time_limit=travel_time,
            travel_mode=travel_mode_enum,
            save_file=False,
            simplify_tolerance=0.001 if simplify else None
        )
        
        # Add metadata
        isochrone_gdf["location"] = location_name
        isochrone_gdf["travel_time"] = travel_time
        isochrone_gdf["travel_mode"] = travel_mode
        
        if return_type == "dict":
            # Convert to GeoJSON-like dict
            return {
                "type": "Feature",
                "geometry": isochrone_gdf.geometry.iloc[0].__geo_interface__,
                "properties": {
                    "location": location_name,
                    "travel_time": travel_time,
                    "travel_mode": travel_mode,
                    "area_sq_km": isochrone_gdf.geometry.iloc[0].area / 1e6
                }
            }
        else:
            return isochrone_gdf
            
    except Exception as e:
        raise RuntimeError(f"Failed to create isochrone: {str(e)}") from e