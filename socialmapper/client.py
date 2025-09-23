"""SocialMapper client for convenient API access."""

import os
from typing import Optional, Union, List, Dict, Any, Tuple
import logging

from .api import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    create_map,
    get_poi,
)

logger = logging.getLogger(__name__)


class SocialMapper:
    """
    Client class for SocialMapper API.

    Provides a convenient object-oriented interface to the SocialMapper
    functionality with configuration management and method access.

    Parameters
    ----------
    api_key : str, optional
        Census API key. If not provided, will try to load from
        CENSUS_API_KEY environment variable.
    cache_enabled : bool, optional
        Whether to enable caching, by default True.
    default_travel_time : int, optional
        Default travel time in minutes, by default 15.
    default_travel_mode : str, optional
        Default travel mode, by default 'drive'.
    default_output_dir : str, optional
        Default output directory for files, by default 'output'.

    Examples
    --------
    >>> mapper = SocialMapper(api_key="your_key")
    >>> isochrone = mapper.create_isochrone("Seattle, WA", travel_time=20)
    >>> blocks = mapper.get_census_blocks(isochrone["geometry"])
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_enabled: bool = True,
        default_travel_time: int = 15,
        default_travel_mode: str = "drive",
        default_output_dir: str = "output",
        **kwargs
    ):
        """Initialize SocialMapper client with configuration."""
        # Set API key from parameter or environment
        self.api_key = api_key or os.getenv("CENSUS_API_KEY")

        # Store configuration
        self.config = {
            "cache_enabled": cache_enabled,
            "default_travel_time": default_travel_time,
            "default_travel_mode": default_travel_mode,
            "default_output_dir": default_output_dir,
        }

        # Add any additional kwargs to config
        self.config.update(kwargs)

        # Create output directory if it doesn't exist
        if not os.path.exists(self.config["default_output_dir"]):
            os.makedirs(self.config["default_output_dir"], exist_ok=True)

    def create_isochrone(
        self,
        location: Union[str, Tuple[float, float]],
        travel_time: Optional[int] = None,
        travel_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a travel-time polygon from a location.

        Parameters
        ----------
        location : str or tuple of float
            Either a "City, State" string or (latitude, longitude) tuple.
        travel_time : int, optional
            Travel time in minutes. Uses default if not specified.
        travel_mode : str, optional
            Travel mode ('drive', 'walk', 'bike'). Uses default if not specified.

        Returns
        -------
        dict
            GeoJSON-like dictionary with isochrone geometry.
        """
        travel_time = travel_time or self.config["default_travel_time"]
        travel_mode = travel_mode or self.config["default_travel_mode"]

        return create_isochrone(location, travel_time, travel_mode)

    def get_census_blocks(
        self,
        geometry: Union[Dict, List[Tuple[float, float]]]
    ) -> List[Dict[str, Any]]:
        """
        Get census block groups that intersect with a geometry.

        Parameters
        ----------
        geometry : dict or list of tuple
            GeoJSON geometry dict or list of (lat, lon) coordinates.

        Returns
        -------
        list of dict
            Census block groups with their GEOIDs and geometries.
        """
        return get_census_blocks(geometry)

    def get_census_data(
        self,
        blocks: List[Dict[str, Any]],
        variables: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get census data for specified block groups.

        Parameters
        ----------
        blocks : list of dict
            Block groups returned from get_census_blocks.
        variables : list of str, optional
            Census variables to fetch. Defaults to common demographics.

        Returns
        -------
        dict
            Census data keyed by GEOID.
        """
        # Use API key if available
        if self.api_key:
            os.environ["CENSUS_API_KEY"] = self.api_key

        return get_census_data(blocks, variables)

    def create_map(
        self,
        blocks: List[Dict[str, Any]],
        census_data: Dict[str, Dict[str, Any]],
        variable: str = "population",
        title: Optional[str] = None,
        save_path: Optional[str] = None
    ) -> Any:
        """
        Create a choropleth map visualization.

        Parameters
        ----------
        blocks : list of dict
            Block groups with geometries.
        census_data : dict
            Census data from get_census_data.
        variable : str, optional
            Variable to visualize, by default "population".
        title : str, optional
            Map title.
        save_path : str, optional
            Path to save the map HTML file.

        Returns
        -------
        folium.Map or None
            The map object if successful.
        """
        if save_path is None:
            save_path = f"{self.config['default_output_dir']}/map.html"

        return create_map(blocks, census_data, variable, title, save_path)

    def get_poi(
        self,
        location: Union[str, Tuple[float, float]],
        categories: Optional[List[str]] = None,
        radius: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Find points of interest near a location.

        Parameters
        ----------
        location : str or tuple of float
            Location to search near.
        categories : list of str, optional
            POI categories to search for.
        radius : int, optional
            Search radius in meters, by default 1000.

        Returns
        -------
        list of dict
            Points of interest with details.
        """
        return get_poi(location, categories, radius)

    def analyze_location(
        self,
        location: Union[str, Tuple[float, float]],
        travel_time: Optional[int] = None,
        travel_mode: Optional[str] = None,
        census_variables: Optional[List[str]] = None,
        poi_categories: Optional[List[str]] = None,
        poi_types: Optional[List[str]] = None  # Alias for poi_categories
    ) -> Dict[str, Any]:
        """
        Perform complete location analysis.

        Combines isochrone generation, census data collection,
        and POI discovery into a single analysis.

        Parameters
        ----------
        location : str or tuple of float
            Location to analyze.
        travel_time : int, optional
            Travel time for isochrone.
        travel_mode : str, optional
            Mode of travel.
        census_variables : list of str, optional
            Census variables to collect.
        poi_categories : list of str, optional
            POI categories to find.

        Returns
        -------
        dict
            Complete analysis results including:
            - isochrone: Travel-time polygon
            - blocks: Census block groups
            - census_data: Demographic data
            - pois: Points of interest
        """
        # Generate isochrone
        isochrone = self.create_isochrone(location, travel_time, travel_mode)

        # Get census blocks
        blocks = self.get_census_blocks(isochrone["geometry"])

        # Get census data
        census_data = self.get_census_data(blocks, census_variables) if blocks else {}

        # Get POIs (support both poi_categories and poi_types parameters)
        categories = poi_categories or poi_types
        pois = self.get_poi(location, categories) if categories else []

        return {
            "location": location,
            "isochrone": isochrone,
            "blocks": blocks,
            "census_data": census_data,
            "pois": pois,
            "summary": {
                "block_count": len(blocks),
                "poi_count": len(pois),
                "travel_time": travel_time or self.config["default_travel_time"],
                "travel_mode": travel_mode or self.config["default_travel_mode"]
            }
        }

    def discover_nearby_pois(
        self,
        location: Union[str, Tuple[float, float]],
        poi_types: Optional[List[str]] = None,
        radius: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Discover points of interest near a location.

        Alias for get_poi method for backward compatibility.

        Parameters
        ----------
        location : str or tuple of float
            Location to search near.
        poi_types : list of str, optional
            POI categories to search for.
        radius : int, optional
            Search radius in meters.

        Returns
        -------
        list of dict
            Points of interest with details.
        """
        return self.get_poi(location, poi_types, radius)

    def analyze_custom_pois(
        self,
        location: Union[str, Tuple[float, float]],
        custom_pois: List[Dict[str, Any]],
        travel_time: Optional[int] = None,
        travel_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a location with custom POI data.

        Parameters
        ----------
        location : str or tuple of float
            Location to analyze.
        custom_pois : list of dict
            Custom POI data to include.
        travel_time : int, optional
            Travel time for isochrone.
        travel_mode : str, optional
            Mode of travel.

        Returns
        -------
        dict
            Analysis results with custom POIs.
        """
        # Generate isochrone
        isochrone = self.create_isochrone(location, travel_time, travel_mode)

        # Get census blocks
        blocks = self.get_census_blocks(isochrone["geometry"])

        # Get census data
        census_data = self.get_census_data(blocks, None) if blocks else {}

        return {
            "location": location,
            "isochrone": isochrone,
            "blocks": blocks,
            "census_data": census_data,
            "pois": custom_pois,
            "summary": {
                "block_count": len(blocks),
                "poi_count": len(custom_pois),
                "travel_time": travel_time or self.config["default_travel_time"],
                "travel_mode": travel_mode or self.config["default_travel_mode"]
            }
        }