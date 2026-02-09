"""Valhalla routing API backend for isochrone generation.

This module provides the Valhalla backend using routingpy for fast
isochrone generation via the public OpenStreetMap Valhalla instance.
"""

import logging
import os

from .base import BaseIsochroneBackend, IsochroneResult

logger = logging.getLogger(__name__)


# Default public Valhalla endpoint (OpenStreetMap foundation)
DEFAULT_VALHALLA_URL = "https://valhalla1.openstreetmap.de"

# Profile mappings for Valhalla
VALHALLA_PROFILES = {
    "drive": "auto",
    "walk": "pedestrian",
    "bike": "bicycle",
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
            logger.debug("Valhalla backend available at %s", self.base_url)
        except ImportError:
            self._available = False
            logger.info(
                "Valhalla backend unavailable: routingpy not installed. "
                "Install with: pip install socialmapper"
            )
        except Exception as e:
            self._available = False
            logger.warning("Valhalla backend unavailable: %s", e)

        return self._available

    def _get_router(self):
        """Get or create the router instance."""
        if self._router is None:
            from routingpy import Valhalla

            self._router = Valhalla(base_url=self.base_url, timeout=self.timeout)
        return self._router

    def get_router(self):
        """Get the routingpy router instance (public API).

        Returns
        -------
        routingpy.Valhalla
            The underlying Valhalla router.
        """
        return self._get_router()

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
            logger.error("Valhalla isochrone generation failed: %s", e)
            raise RuntimeError(f"Valhalla isochrone generation failed: {e}") from e
