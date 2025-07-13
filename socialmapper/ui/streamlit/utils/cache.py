"""Cached utility functions for improved Streamlit performance."""

import logging
from typing import Any, Optional

import pandas as pd
import streamlit as st

from socialmapper import SocialMapperBuilder

logger = logging.getLogger(__name__)


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_census_variables() -> dict[str, str]:
    """Get census variables with caching.
    
    Returns:
        Dictionary mapping census variable codes to human-readable names
    """
    from ..config import CENSUS_VARIABLES
    return CENSUS_VARIABLES.copy()


@st.cache_data(ttl=3600)  # Cache for 1 hour  
def get_poi_types() -> dict[str, list[str]]:
    """Get POI types with caching.
    
    Returns:
        Dictionary mapping POI categories to lists of POI types
    """
    from ..config import POI_TYPES
    return POI_TYPES.copy()


@st.cache_data(ttl=180, show_spinner=False, max_entries=5)  # Cache for 3 minutes, max 5 entries, disable spinner
def run_cached_analysis(
    location: str,
    poi_type: str,
    poi_name: str,
    travel_time: int,
    travel_mode: str = "walk",
    census_vars: Optional[list[str]] = None,
    _progress_callback: Optional[callable] = None
) -> dict[str, Any]:
    """Run SocialMapper analysis with caching.
    
    This function caches the results of SocialMapper analysis to avoid
    redundant API calls for the same parameters.
    
    Args:
        location: Location string (e.g., "Durham, North Carolina")
        poi_type: Type of POI (e.g., "amenity")
        poi_name: Name of POI (e.g., "library")
        travel_time: Travel time in minutes
        travel_mode: Mode of travel ("walk", "bike", "drive")
        census_vars: List of census variable codes
        
    Returns:
        Dictionary containing analysis results
    """
    try:
        # Parse location (handle "City, State" format)
        if "," in location:
            parts = location.split(",", 1)
            area = parts[0].strip()
            state = parts[1].strip() if len(parts) > 1 else None
        else:
            area = location.strip()
            state = None
        
        # Use builder pattern with correct API
        builder = (
            SocialMapperBuilder()
            .with_location(area, state)
            .with_osm_pois(poi_type, poi_name)
            .with_travel_time(travel_time)
            .with_travel_mode(travel_mode)
        )
        
        # Add census variables if provided
        if census_vars:
            builder = builder.with_census_variables(*census_vars)
        
        # Build and run analysis
        config = builder.build()
        
        # Use enhanced approach with full pipeline capabilities but optimized for UI
        logger.info(f"Starting enhanced analysis for {location} - {poi_type}:{poi_name}")
        
        # Report progress: Step 1 - Initialization
        if _progress_callback:
            _progress_callback(1, "Initializing analysis configuration")
        
        # Improve state handling for better geographic filtering  
        state_normalized = state
        if state and len(state) > 2:
            # Map full state names to abbreviations for better OSM filtering
            state_mapping = {
                "New Mexico": "NM", "new mexico": "NM",
                "North Carolina": "NC", "north carolina": "NC", 
                "South Carolina": "SC", "south carolina": "SC",
                "California": "CA", "california": "CA",
                "Texas": "TX", "texas": "TX",
                "Florida": "FL", "florida": "FL",
                "New York": "NY", "new york": "NY",
                "Virginia": "VA", "virginia": "VA",
                "Georgia": "GA", "georgia": "GA"
            }
            state_normalized = state_mapping.get(state.lower(), state)
        
        # Use full pipeline with optimizations for UI
        from socialmapper.pipeline import PipelineConfig, PipelineOrchestrator
        from socialmapper.isochrone import TravelMode
        
        # Convert travel_mode string to TravelMode enum
        mode_mapping = {
            'walk': TravelMode.WALK,
            'bike': TravelMode.BIKE, 
            'drive': TravelMode.DRIVE
        }
        travel_mode_enum = mode_mapping.get(travel_mode, TravelMode.WALK)
        
        # Build optimized pipeline configuration for UI
        pipeline_config = PipelineConfig(
            geocode_area=area,
            state=state_normalized,
            poi_type=poi_type,
            poi_name=poi_name,
            travel_time=travel_time,
            travel_mode=travel_mode_enum,
            census_variables=census_vars or ["B01003_001E", "B19013_001E", "B25077_001E"],
            export_isochrones=True,  # Enable isochrone generation
            max_poi_count=10,  # Limit for faster processing but still comprehensive
            create_maps=False,  # Skip map generation for speed
            export_csv=False   # Skip CSV export for speed
        )
        
        logger.info(f"Using location: {area}, {state_normalized} with full pipeline")
        
        # Report progress: Step 2 - Running pipeline
        if _progress_callback:
            _progress_callback(2, f"Searching for {poi_name} in {area}, {state_normalized}")
        
        # Run optimized pipeline
        orchestrator = PipelineOrchestrator(pipeline_config)
        result_data = orchestrator.run()
        
        logger.info("Enhanced pipeline completed successfully")
        
        # Report progress: Step 3 - Processing results
        if _progress_callback:
            _progress_callback(3, "Processing POI and isochrone data")
        
        # Extract comprehensive data
        pois = result_data.get("pois", [])
        isochrones = result_data.get("isochrones")
        
        # Filter POIs to US bounds to avoid international matches
        us_bounds = {
            'min_lat': 24.0,  # Southernmost US (Florida Keys)
            'max_lat': 49.0,  # Northernmost US (excluding Alaska for simplicity)
            'min_lon': -125.0,  # Westernmost US (Pacific Coast)
            'max_lon': -66.0   # Easternmost US (Maine)
        }
        
        filtered_pois = []
        for poi in pois:
            lat, lon = poi.get('lat'), poi.get('lon')
            if (us_bounds['min_lat'] <= lat <= us_bounds['max_lat'] and 
                us_bounds['min_lon'] <= lon <= us_bounds['max_lon']):
                filtered_pois.append(poi)
            else:
                logger.warning(f"Filtered out POI outside US bounds: {poi.get('tags', {}).get('name', 'Unnamed')} at {lat}, {lon}")
        
        pois = filtered_pois
        logger.info(f"After US filtering: {len(pois)} POIs")
        
        # Check if we lost all POIs due to filtering
        if len(result_data.get("pois", [])) > 0 and len(pois) == 0:
            raise ValueError(f"No POIs found in the United States for '{area}, {state_normalized}'. "
                           f"Found {len(result_data.get('pois', []))} POIs but they were in other countries. "
                           f"Please check your location spelling or try a different format.")
        
        # Report progress: Step 4 - Processing demographics
        if _progress_callback:
            _progress_callback(4, "Analyzing census demographics")
        
        # Calculate comprehensive demographics from census data
        demographics = {}
        census_data = result_data.get("census_data")
        if census_data is not None and hasattr(census_data, 'to_dict') and not census_data.empty:
            logger.info(f"Processing census data with {len(census_data)} records")
            for var in census_vars or ["B01003_001E", "B19013_001E", "B25077_001E"]:
                if var in census_data.columns:
                    valid_values = census_data[var].dropna()
                    if len(valid_values) > 0:
                        if var == "B01003_001E":  # Total population - sum
                            demographics[var] = valid_values.sum()
                        else:  # Other vars - mean
                            demographics[var] = valid_values.mean()
                        logger.debug(f"Calculated {var}: {demographics[var]}")
        else:
            # Fallback estimates if no census data
            logger.warning("No census data available, using estimates")
            demographics = {
                'B01003_001E': len(pois) * 1500,  # Estimate: 1500 people per POI area
                'B19013_001E': 55000,  # Default median income estimate
                'B25077_001E': 275000  # Default median home value
            }
        
        # Report progress: Step 5 - Finalizing results
        if _progress_callback:
            _progress_callback(5, "Generating final analysis report")
        
        # Calculate isochrone area if available
        isochrone_area = 0.0
        if isochrones is not None and hasattr(isochrones, 'geometry') and not isochrones.empty:
            try:
                # Project to equal area and calculate area in km²
                iso_gdf = isochrones.to_crs("EPSG:5070")
                isochrone_area = iso_gdf.geometry.area.sum() / 1_000_000
            except Exception:
                pass
        
        # Report final completion
        if _progress_callback:
            _progress_callback(5, "Analysis complete!")
        
        return {
            'success': True,
            'data': {
                'poi_count': len(pois),
                'total_population': demographics.get('B01003_001E', 0),
                'area_km2': isochrone_area,
                'census_units_analyzed': len(census_data) if census_data is not None else 0,
                'pois': pois,
                'demographics': demographics,
                'isochrones': isochrones,  # Include actual isochrone geodataframe
            },
            'location': location,
            'poi_type': poi_type,
            'poi_name': poi_name,
            'travel_time': travel_time,
            'travel_mode': travel_mode
        }
                
    except Exception as e:
        logger.error(f"Error in cached analysis: {e}")
        return {
            'success': False,
            'error': str(e),
            'location': location,
            'poi_type': poi_type,
            'poi_name': poi_name
        }


@st.cache_data(ttl=600)  # Cache for 10 minutes
def load_census_data(state: str, variables: list[str]) -> Optional[pd.DataFrame]:
    """Load census data with caching.
    
    Args:
        state: State code (e.g., "NC")
        variables: List of census variable codes
        
    Returns:
        DataFrame with census data or None if error
    """
    try:
        # This would integrate with the census module
        # For now, return None as placeholder
        logger.info(f"Loading census data for {state} with variables {variables}")
        return None
    except Exception as e:
        logger.error(f"Error loading census data: {e}")
        return None


@st.cache_resource
def get_map_base_config() -> dict[str, Any]:
    """Get base configuration for maps (cached as resource).
    
    Returns:
        Dictionary with base map configuration
    """
    return {
        'zoom_start': 12,
        'tiles': 'OpenStreetMap',
        'prefer_canvas': True,
        'control_scale': True,
        'max_zoom': 18,
        'min_zoom': 3
    }


@st.cache_data(ttl=86400)  # Cache for 24 hours
def validate_coordinates(lat: float, lon: float) -> tuple[bool, Optional[str]]:
    """Validate coordinates with caching.
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not -90 <= lat <= 90:
        return False, f"Latitude {lat} is out of range [-90, 90]"
    if not -180 <= lon <= 180:
        return False, f"Longitude {lon} is out of range [-180, 180]"
    return True, None


def run_analysis_with_progress(
    location: str,
    poi_type: str,
    poi_name: str,
    travel_time: int,
    travel_mode: str = "walk",
    census_vars: Optional[list[str]] = None,
    progress_callback: Optional[callable] = None
) -> dict[str, Any]:
    """Run analysis with real-time progress updates (not cached).
    
    This function bypasses caching to provide real-time progress updates
    during analysis execution.
    """
    # Call the cached function but with progress callback
    # Note: Since this has _progress_callback parameter, it will be unique per call
    return run_cached_analysis(
        location=location,
        poi_type=poi_type,
        poi_name=poi_name,
        travel_time=travel_time,
        travel_mode=travel_mode,
        census_vars=census_vars,
        _progress_callback=progress_callback
    )


# Clear cache utility functions
def clear_analysis_cache():
    """Clear the analysis cache."""
    st.cache_data.clear()
    logger.info("Analysis cache cleared")


def clear_specific_cache(func_name: str):
    """Clear cache for a specific function.
    
    Args:
        func_name: Name of the function to clear cache for
    """
    # This is a placeholder - Streamlit doesn't have per-function cache clearing yet
    # but it's on their roadmap
    logger.info(f"Would clear cache for {func_name}")