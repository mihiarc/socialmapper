"""Backend factory for automatic selection and instantiation.

This module provides a factory function that selects the best available
isochrone backend based on user preference and availability.
"""

import logging
import os
from typing import Any

from .base import BaseIsochroneBackend, IsochroneBackend
from .networkx_backend import NetworkXBackend
from .routing_api import (
    GraphHopperBackend,
    ORSBackend,
    OSRMBackend,
    ValhallaBackend,
)

logger = logging.getLogger(__name__)


# All available backends in order of preference for "auto" selection
# Valhalla is preferred because it's free and doesn't require an API key
BACKEND_PRIORITY = [
    "valhalla",
    "ors",
    "osrm",
    "graphhopper",
    "networkx",
]

# Mapping of backend names to classes
BACKEND_CLASSES: dict[str, type[BaseIsochroneBackend]] = {
    "networkx": NetworkXBackend,
    "valhalla": ValhallaBackend,
    "ors": ORSBackend,
    "osrm": OSRMBackend,
    "graphhopper": GraphHopperBackend,
}


def get_backend(
    backend_name: str = "auto",
    **kwargs: Any,
) -> IsochroneBackend:
    """Get an isochrone backend by name or auto-select the best available.

    Parameters
    ----------
    backend_name : str, optional
        Name of the backend to use. Options:
        - "auto": Automatically select the best available backend
        - "valhalla": Use Valhalla (free, no API key required)
        - "ors": Use OpenRouteService (requires ORS_API_KEY)
        - "osrm": Use Mapbox OSRM (requires MAPBOX_API_KEY)
        - "graphhopper": Use GraphHopper (requires GRAPHHOPPER_API_KEY)
        - "networkx": Use local NetworkX/OSMnx (slower but offline)

        Can also be set via SOCIALMAPPER_ROUTING_BACKEND environment variable.
        Default is "auto".

    **kwargs : Any
        Additional arguments passed to the backend constructor.
        - api_key: API key for backends that require one
        - base_url: Custom endpoint URL (for Valhalla)
        - timeout: Request timeout in seconds

    Returns
    -------
    IsochroneBackend
        An instantiated isochrone backend.

    Raises
    ------
    ValueError
        If the specified backend is unknown.
    RuntimeError
        If no backend is available.

    Examples
    --------
    >>> # Auto-select best available backend
    >>> backend = get_backend()
    >>> backend.name
    'valhalla'

    >>> # Use specific backend
    >>> backend = get_backend("networkx")
    >>> backend.name
    'networkx'

    >>> # Configure with custom URL
    >>> backend = get_backend("valhalla", base_url="http://localhost:8002")
    """
    # Check environment variable for default
    if backend_name == "auto":
        backend_name = os.environ.get("SOCIALMAPPER_ROUTING_BACKEND", "auto")

    # Normalize backend name
    backend_name = backend_name.lower().strip()

    if backend_name == "auto":
        return _auto_select_backend(**kwargs)

    if backend_name not in BACKEND_CLASSES:
        available = ", ".join(BACKEND_CLASSES.keys())
        raise ValueError(
            f"Unknown backend '{backend_name}'. Available backends: {available}"
        )

    # Instantiate the requested backend
    backend_class = BACKEND_CLASSES[backend_name]
    backend = backend_class(**kwargs)

    if not backend.is_available():
        # Provide helpful error messages
        if backend_name in ("ors", "osrm", "graphhopper"):
            env_var = {
                "ors": "ORS_API_KEY",
                "osrm": "MAPBOX_API_KEY",
                "graphhopper": "GRAPHHOPPER_API_KEY",
            }[backend_name]
            raise RuntimeError(
                f"Backend '{backend_name}' is not available. "
                f"Make sure routingpy is installed and {env_var} is set."
            )
        elif backend_name == "valhalla":
            raise RuntimeError(
                f"Backend '{backend_name}' is not available. "
                "Make sure routingpy is installed: pip install 'socialmapper[routing]'"
            )
        else:
            raise RuntimeError(f"Backend '{backend_name}' is not available.")

    logger.info(f"Using isochrone backend: {backend_name}")
    return backend


def _auto_select_backend(**kwargs: Any) -> IsochroneBackend:
    """Automatically select the best available backend.

    Tries backends in priority order and returns the first one that's available.

    Parameters
    ----------
    **kwargs : Any
        Additional arguments passed to backend constructors.

    Returns
    -------
    IsochroneBackend
        The first available backend.

    Raises
    ------
    RuntimeError
        If no backend is available.
    """
    for backend_name in BACKEND_PRIORITY:
        try:
            backend_class = BACKEND_CLASSES[backend_name]
            backend = backend_class(**kwargs)

            if backend.is_available():
                logger.info(f"Auto-selected isochrone backend: {backend_name}")
                return backend

        except Exception as e:
            logger.debug(f"Backend '{backend_name}' failed availability check: {e}")
            continue

    # If we get here, no backend is available
    raise RuntimeError(
        "No isochrone backend is available. "
        "Install routingpy for fast API-based backends: pip install 'socialmapper[routing]' "
        "or ensure networkx and osmnx are installed for local processing."
    )


def list_available_backends() -> list[str]:
    """List all available isochrone backends.

    Returns
    -------
    list of str
        Names of backends that are currently available.

    Examples
    --------
    >>> available = list_available_backends()
    >>> print(available)
    ['valhalla', 'networkx']
    """
    available = []
    for backend_name, backend_class in BACKEND_CLASSES.items():
        try:
            backend = backend_class()
            if backend.is_available():
                available.append(backend_name)
        except Exception:
            continue

    return available


def get_backend_info() -> dict[str, dict[str, Any]]:
    """Get detailed information about all backends.

    Returns
    -------
    dict
        Dictionary mapping backend names to their info:
        - available: Whether the backend is currently available
        - requires_api_key: Whether an API key is required
        - description: Brief description of the backend

    Examples
    --------
    >>> info = get_backend_info()
    >>> info['valhalla']['available']
    True
    >>> info['ors']['requires_api_key']
    True
    """
    info = {}

    backend_descriptions = {
        "networkx": "Local NetworkX/OSMnx backend (slower, but offline capable)",
        "valhalla": "Valhalla routing API (fast, free, no API key required)",
        "ors": "OpenRouteService API (fast, requires free API key)",
        "osrm": "Mapbox OSRM API (fast, requires Mapbox API key)",
        "graphhopper": "GraphHopper API (fast, requires free API key)",
    }

    api_key_required = {
        "networkx": False,
        "valhalla": False,
        "ors": True,
        "osrm": True,
        "graphhopper": True,
    }

    for backend_name, backend_class in BACKEND_CLASSES.items():
        try:
            backend = backend_class()
            available = backend.is_available()
        except Exception:
            available = False

        info[backend_name] = {
            "available": available,
            "requires_api_key": api_key_required.get(backend_name, False),
            "description": backend_descriptions.get(backend_name, ""),
        }

    return info
