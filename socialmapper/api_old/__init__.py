"""Simplified SocialMapper API.

Direct access to core spatial analysis functions without unnecessary abstractions.

Example:
    ```python
    from socialmapper.api import create_isochrone, SocialMapper
    
    # Simple isochrone creation
    isochrone = create_isochrone("San Francisco, CA", travel_time=15)
    
    # Or use the client for API key management
    mapper = SocialMapper(api_key="your-census-key")
    ```
"""

from .client import SocialMapper
from .exceptions import AnalysisError, APIError, SocialMapperError, ValidationError
from .isochrone import create_isochrone
from .results import AnalysisResult, POIResult

__all__ = [
    # Core functions
    "create_isochrone",
    # Client (minimal, mainly for API key management)
    "SocialMapper",
    # Result types (kept for backward compatibility)
    "AnalysisResult",
    "POIResult",
    # Exceptions
    "SocialMapperError",
    "ValidationError", 
    "AnalysisError",
    "APIError",
]