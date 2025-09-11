"""Minimal SocialMapper client for API operations.

A lightweight client that provides the essential methods needed by tutorials
and examples while avoiding overengineering.
"""

import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass

from ..console import get_logger
from .isochrone import create_isochrone
from ..pipeline.orchestrator import PipelineOrchestrator, PipelineConfig

logger = get_logger(__name__)


class SocialMapper:
    """Minimal client for SocialMapper operations.
    
    Provides essential methods for spatial analysis while keeping the API simple.
    This implementation focuses on the most commonly used functionality.
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
    
    def analyze_location(
        self,
        location: str,
        poi_types: List[str],
        travel_time: int = 15,
        census_variables: Optional[List[str]] = None,
        output_dir: str = "output",
        create_maps: bool = False
    ) -> Dict[str, Any]:
        """Analyze a location with POIs and demographics.
        
        This is the main method used by tutorials and examples.
        
        Args:
            location: Location to analyze (e.g., "City, State")
            poi_types: Types of POIs to search for (e.g., ["library"])
            travel_time: Travel time in minutes for isochrones
            census_variables: Census variables to analyze
            output_dir: Directory for output files
            create_maps: Whether to create choropleth maps
            
        Returns:
            Dictionary with analysis results
        """
        # Map simple POI types to OSM tags
        poi_mapping = {
            "library": ("amenity", "library"),
            "hospital": ("amenity", "hospital"),
            "school": ("amenity", "school"),
            "park": ("leisure", "park"),
            "restaurant": ("amenity", "restaurant"),
            "grocery": ("shop", "supermarket"),
        }
        
        # Get the first POI type and map it
        poi_key = poi_types[0] if poi_types else "library"
        poi_type, poi_name = poi_mapping.get(poi_key, ("amenity", poi_key))
        
        # Create a pipeline configuration
        config = PipelineConfig(
            geocode_area=location,
            poi_type=poi_type,
            poi_name=poi_name,
            travel_time=travel_time,
            census_variables=census_variables or ["total_population"],
            output_dir=output_dir,
            create_maps=create_maps
        )
        
        # Create and run the pipeline
        try:
            pipeline = PipelineOrchestrator(config)
            result = pipeline.run()
            
            # Format the result for compatibility
            return {
                'poi_count': len(result.get('pois', [])),
                'census_units_analyzed': len(result.get('census_data', [])),
                'isochrone_area_km2': result.get('total_area_km2', 0),
                'demographics': result.get('summary_stats', {}),
                'files_created': result.get('output_files', []),
                'success': True
            }
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                'poi_count': 0,
                'census_units_analyzed': 0,
                'isochrone_area_km2': 0,
                'demographics': {},
                'files_created': [],
                'success': False,
                'error': str(e)
            }
    
    def create_isochrone(
        self,
        location: str,
        travel_time: int = 15,
        travel_mode: str = "drive"
    ) -> Any:
        """Create an isochrone for a location.
        
        Wrapper around the standalone create_isochrone function.
        
        Args:
            location: Location string or coordinates
            travel_time: Travel time in minutes
            travel_mode: Mode of travel
            
        Returns:
            Isochrone GeoDataFrame
        """
        return create_isochrone(
            location=location,
            travel_time=travel_time,
            travel_mode=travel_mode
        )
    
    def __repr__(self):
        return f"SocialMapper(api_key={'***' if self.api_key else None}, cache={self.cache_enabled})"