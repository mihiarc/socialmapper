"""Routing API backend using routingpy for fast isochrone generation.

This module provides backends that use external routing APIs via routingpy,
offering 10-100x faster isochrone generation compared to local NetworkX.
"""

import logging
import os

from .base import BaseIsochroneBackend, IsochroneResult

logger = logging.getLogger(__name__)


# Default public Valhalla endpoint (OpenStreetMap foundation)
DEFAULT_VALHALLA_URL = "https://valhalla1.openstreetmap.de"

# Profile mappings for different routing providers
VALHALLA_PROFILES = {
    "drive": "auto",
    "walk": "pedestrian",
    "bike": "bicycle",
}

ORS_PROFILES = {
    "drive": "driving-car",
    "walk": "foot-walking",
    "bike": "cycling-regular",
}

OSRM_PROFILES = {
    "drive": "driving",
    "walk": "walking",
    "bike": "cycling",
}

GRAPHHOPPER_PROFILES = {
    "drive": "car",
    "walk": "foot",
    "bike": "bike",
}


class ValhallaBackend(BaseIsochroneBackend):
    """Isochrone backend using Valhalla routing API.

    Valhalla is a free, open-source routing engine with excellent isochrone
    support. This backend uses the public OpenStreetMap Valhalla instance
    by default, but can be configured to use custom endpoints.

    Features:
    - Very fast (0.5-2 seconds typical)
    - High quality isochrones with contour smoothing
    - No API key required for public instance
    - Supports custom Valhalla deployments
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int = 30,
    ) -> None:
        """Initialize the Valhalla backend.

        Parameters
        ----------
        base_url : str, optional
            Base URL for Valhalla API. Defaults to public OSM instance.
            Can also be set via VALHALLA_URL environment variable.
        timeout : int, optional
            Request timeout in seconds. Default is 30.
        """
        self.base_url = (
            base_url
            or os.environ.get("VALHALLA_URL")
            or DEFAULT_VALHALLA_URL
        )
        self.timeout = timeout
        self._available: bool | None = None
        self._router = None

    @property
    def name(self) -> str:
        """Return the backend name."""
        return "valhalla"

    def is_available(self) -> bool:
        """Check if routingpy and Valhalla endpoint are available.

        Returns
        -------
        bool
            True if routingpy is installed and Valhalla is reachable.
        """
        if self._available is not None:
            return self._available

        try:
            from routingpy import Valhalla

            # Create router instance
            self._router = Valhalla(base_url=self.base_url, timeout=self.timeout)
            self._available = True
            logger.debug(f"Valhalla backend available at {self.base_url}")
        except ImportError:
            self._available = False
            logger.info(
                "Valhalla backend unavailable: routingpy not installed. "
                "Install with: pip install 'socialmapper[routing]'"
            )
        except Exception as e:
            self._available = False
            logger.warning(f"Valhalla backend unavailable: {e}")

        return self._available

    def _get_router(self):
        """Get or create the router instance."""
        if self._router is None:
            from routingpy import Valhalla

            self._router = Valhalla(base_url=self.base_url, timeout=self.timeout)
        return self._router

    def create_isochrone(
        self,
        lat: float,
        lon: float,
        travel_time: int,
        travel_mode: str,
    ) -> IsochroneResult:
        """Create an isochrone using Valhalla API.

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
            raise RuntimeError("Valhalla backend is not available")

        router = self._get_router()

        # Map travel mode to Valhalla profile
        profile = VALHALLA_PROFILES.get(travel_mode, "auto")

        # Convert travel time to seconds
        travel_time_seconds = travel_time * 60

        try:
            # Call Valhalla isochrones API
            # Note: routingpy uses (lon, lat) tuple format
            result = router.isochrones(
                locations=[(lon, lat)],
                profile=profile,
                intervals=[travel_time_seconds],
                interval_type="time",
            )

            if not result or len(result) == 0:
                raise RuntimeError("Valhalla returned empty isochrone result")

            # Extract the isochrone geometry
            isochrone = result[0]

            # Convert geometry to GeoJSON format
            # routingpy returns geometry as list of coordinate rings
            geometry = self._convert_to_geojson(isochrone.geometry)

            # Calculate area
            area_sq_km = self._calculate_area_sq_km(geometry)

            return IsochroneResult(
                geometry=geometry,
                center=(lat, lon),
                travel_time=travel_time,
                travel_mode=travel_mode,
                area_sq_km=area_sq_km,
                backend=self.name,
                metadata={
                    "provider": "valhalla",
                    "base_url": self.base_url,
                    "profile": profile,
                    "interval_seconds": travel_time_seconds,
                },
            )

        except Exception as e:
            logger.error(f"Valhalla isochrone generation failed: {e}")
            raise RuntimeError(f"Valhalla isochrone generation failed: {e}") from e


class ORSBackend(BaseIsochroneBackend):
    """Isochrone backend using OpenRouteService API.

    OpenRouteService provides free routing APIs with an API key.
    Offers 500 free requests per day on their public API.

    Features:
    - High quality isochrones
    - Supports multiple travel modes
    - Requires API key (free tier available)
    """

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 30,
    ) -> None:
        """Initialize the ORS backend.

        Parameters
        ----------
        api_key : str, optional
            OpenRouteService API key. Can also be set via ORS_API_KEY
            environment variable.
        timeout : int, optional
            Request timeout in seconds. Default is 30.
        """
        self.api_key = api_key or os.environ.get("ORS_API_KEY")
        self.timeout = timeout
        self._available: bool | None = None
        self._router = None

    @property
    def name(self) -> str:
        """Return the backend name."""
        return "ors"

    def is_available(self) -> bool:
        """Check if routingpy and ORS API key are available.

        Returns
        -------
        bool
            True if routingpy is installed and API key is configured.
        """
        if self._available is not None:
            return self._available

        try:
            from routingpy import ORS

            if not self.api_key:
                self._available = False
                logger.info(
                    "ORS backend unavailable: API key not configured. "
                    "Set ORS_API_KEY environment variable."
                )
                return self._available

            self._router = ORS(api_key=self.api_key, timeout=self.timeout)
            self._available = True
            logger.debug("ORS backend available")
        except ImportError:
            self._available = False
            logger.info(
                "ORS backend unavailable: routingpy not installed. "
                "Install with: pip install 'socialmapper[routing]'"
            )
        except Exception as e:
            self._available = False
            logger.warning(f"ORS backend unavailable: {e}")

        return self._available

    def _get_router(self):
        """Get or create the router instance."""
        if self._router is None:
            from routingpy import ORS

            self._router = ORS(api_key=self.api_key, timeout=self.timeout)
        return self._router

    def create_isochrone(
        self,
        lat: float,
        lon: float,
        travel_time: int,
        travel_mode: str,
    ) -> IsochroneResult:
        """Create an isochrone using ORS API.

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
            raise RuntimeError("ORS backend is not available")

        router = self._get_router()

        # Map travel mode to ORS profile
        profile = ORS_PROFILES.get(travel_mode, "driving-car")

        # Convert travel time to seconds
        travel_time_seconds = travel_time * 60

        try:
            # Call ORS isochrones API
            # Note: routingpy uses (lon, lat) tuple format
            result = router.isochrones(
                locations=[(lon, lat)],
                profile=profile,
                intervals=[travel_time_seconds],
                interval_type="time",
            )

            if not result or len(result) == 0:
                raise RuntimeError("ORS returned empty isochrone result")

            # Extract the isochrone geometry
            isochrone = result[0]

            # Convert geometry to GeoJSON format
            geometry = self._convert_to_geojson(isochrone.geometry)

            # Calculate area
            area_sq_km = self._calculate_area_sq_km(geometry)

            return IsochroneResult(
                geometry=geometry,
                center=(lat, lon),
                travel_time=travel_time,
                travel_mode=travel_mode,
                area_sq_km=area_sq_km,
                backend=self.name,
                metadata={
                    "provider": "openrouteservice",
                    "profile": profile,
                    "interval_seconds": travel_time_seconds,
                },
            )

        except Exception as e:
            logger.error(f"ORS isochrone generation failed: {e}")
            raise RuntimeError(f"ORS isochrone generation failed: {e}") from e


class OSRMBackend(BaseIsochroneBackend):
    """Isochrone backend using OSRM/Mapbox API.

    Uses the Mapbox OSRM isochrone API which requires an API key.

    Features:
    - Fast isochrone generation
    - Supports driving, walking, cycling
    - Requires Mapbox API key
    """

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 30,
    ) -> None:
        """Initialize the OSRM/Mapbox backend.

        Parameters
        ----------
        api_key : str, optional
            Mapbox API key. Can also be set via MAPBOX_API_KEY
            environment variable.
        timeout : int, optional
            Request timeout in seconds. Default is 30.
        """
        self.api_key = api_key or os.environ.get("MAPBOX_API_KEY")
        self.timeout = timeout
        self._available: bool | None = None
        self._router = None

    @property
    def name(self) -> str:
        """Return the backend name."""
        return "osrm"

    def is_available(self) -> bool:
        """Check if routingpy and Mapbox API key are available.

        Returns
        -------
        bool
            True if routingpy is installed and API key is configured.
        """
        if self._available is not None:
            return self._available

        try:
            from routingpy import MapboxOSRM

            if not self.api_key:
                self._available = False
                logger.info(
                    "OSRM/Mapbox backend unavailable: API key not configured. "
                    "Set MAPBOX_API_KEY environment variable."
                )
                return self._available

            self._router = MapboxOSRM(api_key=self.api_key, timeout=self.timeout)
            self._available = True
            logger.debug("OSRM/Mapbox backend available")
        except ImportError:
            self._available = False
            logger.info(
                "OSRM/Mapbox backend unavailable: routingpy not installed. "
                "Install with: pip install 'socialmapper[routing]'"
            )
        except Exception as e:
            self._available = False
            logger.warning(f"OSRM/Mapbox backend unavailable: {e}")

        return self._available

    def _get_router(self):
        """Get or create the router instance."""
        if self._router is None:
            from routingpy import MapboxOSRM

            self._router = MapboxOSRM(api_key=self.api_key, timeout=self.timeout)
        return self._router

    def create_isochrone(
        self,
        lat: float,
        lon: float,
        travel_time: int,
        travel_mode: str,
    ) -> IsochroneResult:
        """Create an isochrone using OSRM/Mapbox API.

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
            raise RuntimeError("OSRM/Mapbox backend is not available")

        router = self._get_router()

        # Map travel mode to OSRM profile
        profile = OSRM_PROFILES.get(travel_mode, "driving")

        # Convert travel time to seconds
        travel_time_seconds = travel_time * 60

        try:
            # Call Mapbox OSRM isochrones API
            # Note: routingpy uses (lon, lat) tuple format
            result = router.isochrones(
                locations=(lon, lat),
                profile=profile,
                intervals=[travel_time_seconds],
                polygons=True,  # Return polygons instead of lines
            )

            if not result or len(result) == 0:
                raise RuntimeError("OSRM returned empty isochrone result")

            # Extract the isochrone geometry
            isochrone = result[0]

            # Convert geometry to GeoJSON format
            geometry = self._convert_to_geojson(isochrone.geometry)

            # Calculate area
            area_sq_km = self._calculate_area_sq_km(geometry)

            return IsochroneResult(
                geometry=geometry,
                center=(lat, lon),
                travel_time=travel_time,
                travel_mode=travel_mode,
                area_sq_km=area_sq_km,
                backend=self.name,
                metadata={
                    "provider": "mapbox_osrm",
                    "profile": profile,
                    "interval_seconds": travel_time_seconds,
                },
            )

        except Exception as e:
            logger.error(f"OSRM isochrone generation failed: {e}")
            raise RuntimeError(f"OSRM isochrone generation failed: {e}") from e


class GraphHopperBackend(BaseIsochroneBackend):
    """Isochrone backend using GraphHopper API.

    GraphHopper provides free routing APIs with an API key.

    Features:
    - Fast isochrone generation
    - Multiple travel modes
    - Requires API key (free tier available)
    """

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 30,
    ) -> None:
        """Initialize the GraphHopper backend.

        Parameters
        ----------
        api_key : str, optional
            GraphHopper API key. Can also be set via GRAPHHOPPER_API_KEY
            environment variable.
        timeout : int, optional
            Request timeout in seconds. Default is 30.
        """
        self.api_key = api_key or os.environ.get("GRAPHHOPPER_API_KEY")
        self.timeout = timeout
        self._available: bool | None = None
        self._router = None

    @property
    def name(self) -> str:
        """Return the backend name."""
        return "graphhopper"

    def is_available(self) -> bool:
        """Check if routingpy and GraphHopper API key are available.

        Returns
        -------
        bool
            True if routingpy is installed and API key is configured.
        """
        if self._available is not None:
            return self._available

        try:
            from routingpy import Graphhopper

            if not self.api_key:
                self._available = False
                logger.info(
                    "GraphHopper backend unavailable: API key not configured. "
                    "Set GRAPHHOPPER_API_KEY environment variable."
                )
                return self._available

            self._router = Graphhopper(api_key=self.api_key, timeout=self.timeout)
            self._available = True
            logger.debug("GraphHopper backend available")
        except ImportError:
            self._available = False
            logger.info(
                "GraphHopper backend unavailable: routingpy not installed. "
                "Install with: pip install 'socialmapper[routing]'"
            )
        except Exception as e:
            self._available = False
            logger.warning(f"GraphHopper backend unavailable: {e}")

        return self._available

    def _get_router(self):
        """Get or create the router instance."""
        if self._router is None:
            from routingpy import Graphhopper

            self._router = Graphhopper(api_key=self.api_key, timeout=self.timeout)
        return self._router

    def create_isochrone(
        self,
        lat: float,
        lon: float,
        travel_time: int,
        travel_mode: str,
    ) -> IsochroneResult:
        """Create an isochrone using GraphHopper API.

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
            raise RuntimeError("GraphHopper backend is not available")

        router = self._get_router()

        # Map travel mode to GraphHopper profile
        profile = GRAPHHOPPER_PROFILES.get(travel_mode, "car")

        # Convert travel time to seconds
        travel_time_seconds = travel_time * 60

        try:
            # Call GraphHopper isochrones API
            # Note: routingpy uses (lon, lat) tuple format
            result = router.isochrones(
                locations=[(lon, lat)],
                profile=profile,
                intervals=[travel_time_seconds],
                interval_type="time",
            )

            if not result or len(result) == 0:
                raise RuntimeError("GraphHopper returned empty isochrone result")

            # Extract the isochrone geometry
            isochrone = result[0]

            # Convert geometry to GeoJSON format
            geometry = self._convert_to_geojson(isochrone.geometry)

            # Calculate area
            area_sq_km = self._calculate_area_sq_km(geometry)

            return IsochroneResult(
                geometry=geometry,
                center=(lat, lon),
                travel_time=travel_time,
                travel_mode=travel_mode,
                area_sq_km=area_sq_km,
                backend=self.name,
                metadata={
                    "provider": "graphhopper",
                    "profile": profile,
                    "interval_seconds": travel_time_seconds,
                },
            )

        except Exception as e:
            logger.error(f"GraphHopper isochrone generation failed: {e}")
            raise RuntimeError(f"GraphHopper isochrone generation failed: {e}") from e


# Mapping of backend names to classes for factory use
ROUTING_BACKENDS: dict[str, type[BaseIsochroneBackend]] = {
    "valhalla": ValhallaBackend,
    "ors": ORSBackend,
    "osrm": OSRMBackend,
    "graphhopper": GraphHopperBackend,
}
