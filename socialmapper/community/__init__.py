"""
AI-Powered Community Boundary Detection Module

This module integrates computer vision, spatial clustering, and machine learning
to automatically discover organic community boundaries based on spatial patterns,
building characteristics, and environmental features.

🆕 NEW: Real satellite imagery integration via geoai package
- Automatic NAIP, Sentinel-2, and Landsat data fetching
- Intelligent caching and cloud filtering
- Fallback to simulation when real data unavailable
"""

from .spatial_clustering import (
    detect_housing_developments,
    cluster_building_patterns,
    identify_natural_boundaries
)

from .computer_vision import (
    analyze_satellite_imagery,
    extract_building_features,
    classify_neighborhood_types
)

from .boundary_detection import (
    discover_community_boundaries,
    validate_boundaries_with_demographics,
    merge_administrative_and_organic_boundaries
)

from .satellite_data_fetcher import (
    SatelliteDataFetcher,
    fetch_satellite_imagery_for_community_analysis,
    get_imagery_bounds_info
)

__all__ = [
    'detect_housing_developments',
    'cluster_building_patterns', 
    'identify_natural_boundaries',
    'analyze_satellite_imagery',
    'extract_building_features',
    'classify_neighborhood_types',
    'discover_community_boundaries',
    'validate_boundaries_with_demographics',
    'merge_administrative_and_organic_boundaries',
    'SatelliteDataFetcher',
    'fetch_satellite_imagery_for_community_analysis',
    'get_imagery_bounds_info'
] 