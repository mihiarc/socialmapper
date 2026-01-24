"""Base protocol and types for isochrone backends.

This module defines the protocol (interface) that all isochrone backends
must implement, enabling strategy pattern for backend selection.
"""

import logging
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@dataclass
class IsochroneResult:
    """Standardized result from isochrone generation.

    Attributes
    ----------
    geometry : dict
        GeoJSON geometry (Polygon or MultiPolygon) of the isochrone.
    center : tuple[float, float]
        Center point (lat, lon) of the isochrone.
    travel_time : int
        Travel time in minutes.
    travel_mode : str
        Mode of transportation used.
    area_sq_km : float
        Area of the isochrone in square kilometers.
    backend : str
        Name of the backend that generated this isochrone.
    metadata : dict
        Additional backend-specific metadata.
    """

    geometry: dict[str, Any]
    center: tuple[float, float]
    travel_time: int
    travel_mode: str
    area_sq_km: float
    backend: str
    metadata: dict[str, Any] | None = None


@runtime_checkable
class IsochroneBackend(Protocol):
    """Protocol defining the interface for isochrone generation backends.

    All backends must implement this protocol to be usable with the
    backend factory and public API.
    """

    @property
    def name(self) -> str:
        """Return the unique name of this backend."""
        ...

    def is_available(self) -> bool:
        """Check if this backend is available for use.

        Returns
        -------
        bool
            True if the backend is ready to use, False otherwise.
            For API-based backends, this may check network connectivity.
            For local backends, this checks required dependencies.
        """
        ...

    def create_isochrone(
        self,
        lat: float,
        lon: float,
        travel_time: int,
        travel_mode: str,
    ) -> IsochroneResult:
        """Create an isochrone for the given location.

        Parameters
        ----------
        lat : float
            Latitude of the center point.
        lon : float
            Longitude of the center point.
        travel_time : int
            Travel time in minutes.
        travel_mode : str
            Mode of transportation ('drive', 'walk', 'bike').

        Returns
        -------
        IsochroneResult
            Standardized isochrone result with geometry and metadata.

        Raises
        ------
        ValueError
            If parameters are invalid.
        RuntimeError
            If isochrone generation fails.
        """
        ...


class BaseIsochroneBackend:
    """Base class providing common functionality for backends.

    Subclasses should implement the abstract methods and can override
    the helper methods as needed.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of this backend."""
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available for use."""
        raise NotImplementedError

    @abstractmethod
    def create_isochrone(
        self,
        lat: float,
        lon: float,
        travel_time: int,
        travel_mode: str,
    ) -> IsochroneResult:
        """Create an isochrone for the given location."""
        raise NotImplementedError

    def _validate_coordinates(self, lat: float, lon: float) -> None:
        """Validate latitude and longitude values.

        Parameters
        ----------
        lat : float
            Latitude (-90 to 90).
        lon : float
            Longitude (-180 to 180).

        Raises
        ------
        ValueError
            If coordinates are out of valid range.
        """
        if not -90 <= lat <= 90:
            raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
        if not -180 <= lon <= 180:
            raise ValueError(f"Longitude must be between -180 and 180, got {lon}")

    def _validate_travel_time(self, travel_time: int) -> None:
        """Validate travel time value.

        Parameters
        ----------
        travel_time : int
            Travel time in minutes.

        Raises
        ------
        ValueError
            If travel time is out of valid range.
        """
        if not 1 <= travel_time <= 120:
            raise ValueError(f"Travel time must be between 1 and 120 minutes, got {travel_time}")

    def _validate_travel_mode(self, travel_mode: str) -> None:
        """Validate travel mode value.

        Parameters
        ----------
        travel_mode : str
            Mode of transportation.

        Raises
        ------
        ValueError
            If travel mode is invalid.
        """
        valid_modes = {"drive", "walk", "bike"}
        if travel_mode not in valid_modes:
            raise ValueError(
                f"Travel mode must be one of {valid_modes}, got '{travel_mode}'"
            )

    def _calculate_area_sq_km(self, geometry: dict[str, Any]) -> float:
        """Calculate area of a geometry in square kilometers.

        Parameters
        ----------
        geometry : dict
            GeoJSON geometry dict.

        Returns
        -------
        float
            Area in square kilometers.
        """
        import pyproj
        from shapely.geometry import shape
        from shapely.ops import transform

        # Create shapely geometry from GeoJSON
        geom = shape(geometry)

        # Project to equal-area projection for accurate area calculation
        # Use Albers Equal Area centered on the geometry
        centroid = geom.centroid
        proj_string = (
            f"+proj=aea +lat_1={centroid.y - 1} +lat_2={centroid.y + 1} "
            f"+lat_0={centroid.y} +lon_0={centroid.x} +datum=WGS84 +units=m"
        )

        project = pyproj.Transformer.from_crs(
            "EPSG:4326",
            proj_string,
            always_xy=True,
        ).transform

        projected_geom = transform(project, geom)
        area_sq_m = projected_geom.area
        area_sq_km = area_sq_m / 1_000_000

        return round(area_sq_km, 4)

    def _convert_to_geojson(self, geometry: Any) -> dict[str, Any]:
        """Convert routing API geometry to GeoJSON format.

        Parameters
        ----------
        geometry : Any
            Geometry from routing API (can be list of coords, Shapely geometry,
            or dict).

        Returns
        -------
        dict
            GeoJSON geometry dict.

        Raises
        ------
        ValueError
            If geometry cannot be converted.
        """
        # If it's already a dict (GeoJSON), return as-is
        if isinstance(geometry, dict):
            return geometry

        # If it has __geo_interface__ (Shapely geometry), use that
        if hasattr(geometry, "__geo_interface__"):
            return geometry.__geo_interface__

        # If it's a list of coordinates, convert to GeoJSON Polygon
        if isinstance(geometry, list):
            # routingpy returns coords as [[lon, lat], [lon, lat], ...]
            # Need to wrap in another list for GeoJSON Polygon format
            if geometry and isinstance(geometry[0], (list, tuple)):
                # Check if first element is a coordinate pair or a ring
                if len(geometry[0]) == 2 and isinstance(geometry[0][0], (int, float)):
                    # It's a single ring of coordinates
                    return {
                        "type": "Polygon",
                        "coordinates": [geometry],
                    }
                else:
                    # It's already nested (multiple rings or MultiPolygon)
                    return {
                        "type": "Polygon",
                        "coordinates": geometry,
                    }

        raise ValueError(f"Cannot convert geometry of type {type(geometry)} to GeoJSON")
