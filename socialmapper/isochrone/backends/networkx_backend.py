"""NetworkX-based isochrone backend using OSMnx.

This backend wraps the existing NetworkX/OSMnx-based isochrone generation,
providing offline capability and full control over the routing algorithm.
"""

import logging

from .base import BaseIsochroneBackend, IsochroneResult

logger = logging.getLogger(__name__)


class NetworkXBackend(BaseIsochroneBackend):
    """Isochrone backend using NetworkX and OSMnx.

    This backend downloads the road network from OpenStreetMap and computes
    isochrones locally using graph algorithms. It provides:
    - Offline capability after initial network download
    - Full control over the routing algorithm
    - High accuracy (follows actual road network)

    Trade-offs:
    - Slower than API-based backends (3-15 seconds typical)
    - Requires network download for each new area
    """

    def __init__(self) -> None:
        """Initialize the NetworkX backend."""
        self._available: bool | None = None

    @property
    def name(self) -> str:
        """Return the backend name."""
        return "networkx"

    def is_available(self) -> bool:
        """Check if NetworkX and OSMnx are available.

        Returns
        -------
        bool
            True if required packages are installed.
        """
        if self._available is not None:
            return self._available

        try:
            import networkx  # noqa: F401
            import osmnx  # noqa: F401

            self._available = True
        except ImportError:
            self._available = False
            logger.warning(
                "NetworkX backend unavailable: missing networkx or osmnx packages"
            )

        return self._available

    def create_isochrone(
        self,
        lat: float,
        lon: float,
        travel_time: int,
        travel_mode: str,
    ) -> IsochroneResult:
        """Create an isochrone using NetworkX graph algorithms.

        Parameters
        ----------
        lat : float
            Latitude of the center point.
        lon : float
            Longitude of the center point.
        travel_time : int
            Travel time in minutes (1-120).
        travel_mode : str
            Mode of transportation ('drive', 'walk', 'bike').

        Returns
        -------
        IsochroneResult
            Standardized isochrone result.

        Raises
        ------
        ValueError
            If parameters are invalid.
        RuntimeError
            If isochrone generation fails.
        """
        # Validate inputs
        self._validate_coordinates(lat, lon)
        self._validate_travel_time(travel_time)
        self._validate_travel_mode(travel_mode)

        if not self.is_available():
            raise RuntimeError("NetworkX backend is not available")

        # Import the existing isochrone generation function
        from ..cache import download_and_cache_network, get_global_cache
        from ..clustering import create_isochrone_from_poi_with_network
        from ..travel_modes import TravelMode

        # Map travel mode string to enum
        mode_map = {
            "drive": TravelMode.DRIVE,
            "walk": TravelMode.WALK,
            "bike": TravelMode.BIKE,
        }
        travel_mode_enum = mode_map[travel_mode]

        # Create POI dict for the existing function
        poi = {
            "lat": lat,
            "lon": lon,
            "tags": {"name": "api_location"},
            "id": "api_location",
        }

        # Calculate bounding box for network download
        buffer_km = travel_time * 1.5  # Adaptive buffer based on travel time
        buffer_deg = buffer_km / 111.0
        bbox = (
            lat - buffer_deg,
            lon - buffer_deg,
            lat + buffer_deg,
            lon + buffer_deg,
        )

        # Download network with caching
        cache = get_global_cache()
        graph = download_and_cache_network(
            bbox=bbox,
            travel_time_minutes=travel_time,
            cluster_size=1,
            cache=cache,
            travel_mode=travel_mode_enum,
        )

        if graph is None:
            raise RuntimeError(f"Failed to download road network for ({lat}, {lon})")

        # Create isochrone using optimized method
        isochrone_gdf = create_isochrone_from_poi_with_network(
            poi=poi,
            network=graph,
            network_crs=graph.graph["crs"],
            travel_time_minutes=travel_time,
            travel_mode=travel_mode_enum,
        )

        if isochrone_gdf is None:
            raise RuntimeError(f"Failed to create isochrone for ({lat}, {lon})")

        # Extract geometry from GeoDataFrame
        polygon = isochrone_gdf.geometry.iloc[0]
        geometry = polygon.__geo_interface__

        # Calculate area
        area_sq_km = self._calculate_area_sq_km(geometry)

        # Extract metadata from GeoDataFrame
        metadata = {
            "min_distance_km": float(isochrone_gdf["min_distance_km"].iloc[0]),
            "max_distance_km": float(isochrone_gdf["max_distance_km"].iloc[0]),
            "avg_distance_km": float(isochrone_gdf["avg_distance_km"].iloc[0]),
            "median_distance_km": float(isochrone_gdf["median_distance_km"].iloc[0]),
            "reachable_nodes": int(isochrone_gdf["reachable_nodes"].iloc[0]),
            "network_nodes": len(graph.nodes),
            "network_edges": len(graph.edges),
        }

        return IsochroneResult(
            geometry=geometry,
            center=(lat, lon),
            travel_time=travel_time,
            travel_mode=travel_mode,
            area_sq_km=area_sq_km,
            backend=self.name,
            metadata=metadata,
        )
