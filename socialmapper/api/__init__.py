"""Simplified SocialMapper API.

Direct access to core spatial analysis functions without unnecessary abstractions.

Example:
    ```python
    from socialmapper.api import create_isochrone
    
    # Simple isochrone creation
    isochrone = create_isochrone("San Francisco, CA", travel_time=15)
    
    # Set Census API key if needed
    import os
    os.environ['CENSUS_API_KEY'] = "your-census-key"
    ```
"""

from .exceptions import AnalysisError, APIError, SocialMapperError, ValidationError
from .isochrone import create_isochrone
from .results import AnalysisResult, POIResult

__all__ = [
    # Core functions
    "create_isochrone",
    # Result types (kept for backward compatibility)
    "AnalysisResult",
    "POIResult",
    # Exceptions
    "SocialMapperError",
    "ValidationError", 
    "AnalysisError",
    "APIError",
]