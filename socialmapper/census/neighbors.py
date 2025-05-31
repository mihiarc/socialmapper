#!/usr/bin/env python3
"""
Neighbor management system for SocialMapper.

This module provides efficient neighbor identification using Parquet files
to store pre-computed neighbor relationships. This provides fast lookups
for geographic neighbors at state, county, tract, and block group levels.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_parquet_path() -> Path:
    """Get the path to the Parquet neighbor data directory."""
    # First check if packaged with the module
    package_parquet_path = Path(__file__).parent.parent / "data" / "neighbors"
    if package_parquet_path.exists() and any(package_parquet_path.glob("*.parquet")):
        return package_parquet_path
    
    # Check user directory
    user_parquet_path = Path.home() / ".socialmapper" / "neighbors"
    if user_parquet_path.exists() and any(user_parquet_path.glob("*.parquet")):
        return user_parquet_path
    
    # Default location for creation
    return Path.home() / ".socialmapper" / "neighbors"

def _detect_neighbor_system() -> str:
    """
    Detect which neighbor system is available.
    
    Returns:
        'parquet' if Parquet system should be used, 'none' if neither
    """
    # Check for Parquet system (preferred)
    parquet_paths = [
        Path(__file__).parent.parent / "data" / "neighbors",
        Path.home() / ".socialmapper" / "neighbors"
    ]
    
    for path in parquet_paths:
        if path.exists() and any(path.glob("*.parquet")):
            return 'parquet'
    
    return 'none'

# Detect the available neighbor system
NEIGHBOR_SYSTEM = _detect_neighbor_system()

if NEIGHBOR_SYSTEM == 'parquet':
    from .neighbors_parquet import NeighborManager as ParquetNeighborManager
    logger.info("Using Parquet neighbor system")
else:
    logger.warning("No neighbor system detected")

class NeighborManager:
    """
    Unified neighbor manager that automatically detects and uses the best available system.
    
    Supports:
    - Parquet-based system (preferred, for high performance)
    
    The manager automatically detects which system is available and uses the most appropriate one.
    """
    
    def __init__(self, data_path: Optional[Union[str, Path]] = None):
        """
        Initialize the neighbor manager.
        
        Args:
            data_path: Optional path to neighbor data. If None, auto-detects.
        """
        if data_path:
            self.data_path = Path(data_path)
            self.system_type = self._detect_system_type()
        else:
            self.system_type = NEIGHBOR_SYSTEM
            if self.system_type == 'parquet':
                self.data_path = _get_parquet_path()
            else:
                self.data_path = None
        
        # Initialize the appropriate manager
        if self.system_type == 'parquet':
            self._manager = ParquetNeighborManager(self.data_path)
        else:
            raise RuntimeError(f"No neighbor system available. System detected: {self.system_type}")
        
        logger.info(f"Initialized NeighborManager with {self.system_type} system at {self.data_path}")
    
    def _detect_system_type(self) -> str:
        """Detect the system type based on the data path."""
        if not self.data_path.exists():
            return 'none'
        
        # Check for Parquet files
        if any(self.data_path.glob("*.parquet")):
            return 'parquet'
        
        # Check if it's a directory with Parquet files
        if self.data_path.is_dir() and any(self.data_path.glob("*.parquet")):
            return 'parquet'
        
        if NEIGHBOR_SYSTEM == 'parquet':
            return 'parquet'
        
        return 'none'
    
    def initialize_state_neighbors(self) -> bool:
        """Initialize state neighbor relationships."""
        return self._manager.initialize_state_neighbors()
    
    def get_neighboring_states(self, state_fips: str) -> List[str]:
        """Get neighboring states for a given state FIPS code."""
        return self._manager.get_neighboring_states(state_fips)
    
    def get_neighboring_counties(self, county_fips: str) -> List[str]:
        """Get neighboring counties for a given county FIPS code."""
        # Extract state FIPS from county FIPS (first 2 digits)
        if len(county_fips) >= 2:
            state_fips = county_fips[:2]
            county_code = county_fips[2:] if len(county_fips) > 2 else county_fips
        else:
            state_fips = county_fips
            county_code = county_fips
        
        # Call the underlying method with the expected signature
        neighbor_tuples = self._manager.get_neighboring_counties(state_fips, county_code, include_cross_state=True)
        
        # Convert tuples to full county FIPS codes
        neighbor_county_fips = []
        for state, county in neighbor_tuples:
            full_county_fips = f"{state}{county}"
            neighbor_county_fips.append(full_county_fips)
        
        return neighbor_county_fips
    
    def get_geography_from_point(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get geographic information for a point."""
        return self._manager.get_geography_from_point(lat, lon)
    
    def get_counties_from_pois(self, pois: List[Dict], include_neighbors: bool = True) -> List[str]:
        """Get counties for POIs with optional neighbors."""
        # Call the underlying method
        county_tuples = self._manager.get_counties_from_pois(pois, include_neighbors)
        
        # Convert tuples to full county FIPS codes
        county_fips_list = []
        for state, county in county_tuples:
            full_county_fips = f"{state}{county}"
            county_fips_list.append(full_county_fips)
        
        return county_fips_list
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the neighbor system."""
        stats = self._manager.get_neighbor_statistics()
        stats['manager_type'] = 'unified'
        stats['system_type'] = self.system_type
        stats['data_path'] = str(self.data_path) if self.data_path else None
        return stats

# Global neighbor manager instance
_neighbor_manager = None

def get_neighbor_manager(data_path: Optional[Union[str, Path]] = None) -> NeighborManager:
    """
    Get the global neighbor manager instance.
    
    Args:
        data_path: Optional path to neighbor data
        
    Returns:
        NeighborManager instance
    """
    global _neighbor_manager
    
    if _neighbor_manager is None or data_path is not None:
        _neighbor_manager = NeighborManager(data_path)
    
    return _neighbor_manager

def get_neighboring_states(state_fips: str) -> List[str]:
    """
    Get neighboring states for a given state FIPS code.
    
    Args:
        state_fips: State FIPS code (e.g., '06' for California)
        
    Returns:
        List of neighboring state FIPS codes
    """
    manager = get_neighbor_manager()
    return manager.get_neighboring_states(state_fips)

def get_neighboring_counties(county_fips: str) -> List[str]:
    """
    Get neighboring counties for a given county FIPS code.
    
    Args:
        county_fips: County FIPS code (e.g., '06001' for Alameda County, CA)
        
    Returns:
        List of neighboring county FIPS codes
    """
    manager = get_neighbor_manager()
    return manager.get_neighboring_counties(county_fips)

def get_geography_from_point(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Get geographic information for a point.
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        Dictionary with geographic information or None if not found
    """
    manager = get_neighbor_manager()
    return manager.get_geography_from_point(lat, lon)

def get_counties_from_pois(pois: List[Dict], include_neighbors: bool = True) -> List[str]:
    """
    Get counties for POIs with optional neighbors.
    
    Args:
        pois: List of POI dictionaries with 'lat' and 'lon' keys
        include_neighbors: Whether to include neighboring counties
        
    Returns:
        List of county FIPS codes
    """
    manager = get_neighbor_manager()
    return manager.get_counties_from_pois(pois, include_neighbors)

def initialize_all_neighbors() -> bool:
    """
    Initialize all neighbor relationships.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        manager = get_neighbor_manager()
        return manager.initialize_state_neighbors()
    except Exception as e:
        logger.error(f"Failed to initialize neighbors: {e}")
        return False

def get_system_status() -> Dict[str, Any]:
    """
    Get status information about the neighbor system.
    
    Returns:
        Dictionary with system status information
    """
    try:
        manager = get_neighbor_manager()
        stats = manager.get_statistics()
        
        return {
            'available': True,
            'system_type': stats.get('system_type', 'unknown'),
            'data_path': stats.get('data_path'),
            'statistics': stats
        }
    except Exception as e:
        return {
            'available': False,
            'error': str(e),
            'system_type': NEIGHBOR_SYSTEM
        } 