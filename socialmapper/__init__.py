"""SocialMapper: Simple spatial analysis API.

Five core functions for all your spatial analysis needs:
- create_isochrone: Generate travel-time polygons
- get_census_blocks: Fetch census block groups for an area
- get_census_data: Get demographic data from US Census
- create_map: Generate choropleth map visualizations
- get_poi: Find points of interest near locations
"""

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import the 5 core API functions
from .api import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    create_map,
    get_poi,
)

# Version
__version__ = "0.8.0"

# Public API - just the 5 functions
__all__ = [
    "create_isochrone",
    "get_census_blocks",
    "get_census_data",
    "create_map",
    "get_poi",
]