"""Simplified SocialMapper client.

Minimal client focused on core functionality without overengineering.
"""

import os
from typing import Optional

from ..console import get_logger

logger = get_logger(__name__)


class SocialMapper:
    """Simple client for SocialMapper operations.
    
    Provides access to core spatial analysis functions with minimal overhead.
    
    Example:
        ```python
        mapper = SocialMapper(api_key="your-census-key")
        
        # Use individual functions as needed
        from socialmapper.api import create_isochrone
        isochrone = create_isochrone("Portland, OR", travel_time=20)
        ```
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_enabled: bool = True
    ):
        """Initialize SocialMapper client.
        
        Args:
            api_key: Census API key (optional, can use CENSUS_API_KEY env var)
            cache_enabled: Enable caching for better performance
        """
        self.api_key = api_key or os.getenv('CENSUS_API_KEY')
        self.cache_enabled = cache_enabled
        
        # Set the API key in environment for census functions
        if self.api_key:
            os.environ['CENSUS_API_KEY'] = self.api_key
        
        logger.info("SocialMapper client initialized")
    
    def __repr__(self):
        return f"SocialMapper(api_key={'***' if self.api_key else None}, cache={self.cache_enabled})"