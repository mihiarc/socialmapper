"""Backend factory for Valhalla isochrone generation.

This module provides a factory function that returns the Valhalla
isochrone backend.
"""

import logging
from typing import Any

from .base import IsochroneBackend
from .routing_api import ValhallaBackend

logger = logging.getLogger(__name__)


def get_backend(
    backend_name: str = "auto",
    **kwargs: Any,
) -> IsochroneBackend:
    """Get the Valhalla isochrone backend.

    Parameters
    ----------
    backend_name : str, optional
        Backend name. Only "auto" and "valhalla" are accepted.
        Default is "auto".

    **kwargs : Any
        Additional arguments passed to the backend constructor.
        - base_url: Custom Valhalla endpoint URL
        - timeout: Request timeout in seconds

    Returns
    -------
    IsochroneBackend
        An instantiated Valhalla backend.

    Raises
    ------
    ValueError
        If the specified backend is not "auto" or "valhalla".
    RuntimeError
        If the Valhalla backend is not available.

    Examples
    --------
    >>> backend = get_backend()
    >>> backend.name
    'valhalla'

    >>> backend = get_backend("valhalla", base_url="http://localhost:8002")
    """
    backend_name = backend_name.lower().strip()

    if backend_name not in ("auto", "valhalla"):
        raise ValueError(
            f"Unknown backend '{backend_name}'. Only 'valhalla' is supported."
        )

    backend = ValhallaBackend(**kwargs)

    if not backend.is_available():
        raise RuntimeError(
            "Valhalla backend is not available. "
            "Make sure routingpy is installed: pip install socialmapper"
        )

    logger.info("Using isochrone backend: valhalla")
    return backend
