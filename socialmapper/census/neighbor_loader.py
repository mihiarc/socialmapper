#!/usr/bin/env python3
"""Load neighbor data from distributed formats (DuckDB or JSON)."""

import json
import gzip
import duckdb
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import logging

logger = logging.getLogger(__name__)

class DistributedNeighborLoader:
    """Load neighbor data from distributed formats with automatic fallback."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the loader.
        
        Args:
            data_dir: Directory containing neighbor data files. If None, looks in package data.
        """
        self.data_dir = Path(data_dir) if data_dir else self._find_data_dir()
        self._state_neighbors = None
        self._county_neighbors = None
        self._metadata = None
        self._loaded_format = None
        
    def _find_data_dir(self) -> Path:
        """Find the data directory in the package."""
        # Look for data files in the package
        package_dir = Path(__file__).parent
        possible_dirs = [
            package_dir / "data",
            package_dir.parent / "data", 
            package_dir.parent.parent / "data",
            Path.cwd()  # Current directory as fallback
        ]
        
        for data_dir in possible_dirs:
            if self._has_neighbor_data(data_dir):
                return data_dir
        
        # Default to package directory
        return package_dir / "data"
    
    def _has_neighbor_data(self, data_dir: Path) -> bool:
        """Check if directory contains neighbor data files."""
        if not data_dir.exists():
            return False
        
        # Check for DuckDB or JSON files
        duckdb_file = data_dir / "neighbor_data.duckdb"
        json_files = [
            data_dir / "neighbor_data_compact.json.gz",
            data_dir / "neighbor_data.json.gz",
            data_dir / "neighbor_data_compact.json",
            data_dir / "neighbor_data.json"
        ]
        
        return duckdb_file.exists() or any(f.exists() for f in json_files)
    
    def load_data(self, force_format: Optional[str] = None) -> bool:
        """Load neighbor data from available formats.
        
        Args:
            force_format: Force loading from specific format ('duckdb' or 'json')
            
        Returns:
            True if data was loaded successfully
        """
        if self._state_neighbors is not None:
            return True  # Already loaded
        
        logger.info(f"Loading neighbor data from: {self.data_dir}")
        
        # Try formats in order of preference
        if force_format == 'duckdb':
            success = self._load_from_duckdb()
        elif force_format == 'json':
            success = self._load_from_json()
        else:
            # Auto-detect best format
            success = self._load_from_duckdb() or self._load_from_json()
        
        if success:
            logger.info(f"Successfully loaded neighbor data from {self._loaded_format}")
            return True
        else:
            logger.error("Failed to load neighbor data from any format")
            return False
    
    def _load_from_duckdb(self) -> bool:
        """Load data from DuckDB format."""
        duckdb_file = self.data_dir / "neighbor_data.duckdb"
        
        if not duckdb_file.exists():
            logger.debug("DuckDB file not found")
            return False
        
        try:
            logger.info("Loading from DuckDB format...")
            conn = duckdb.connect(str(duckdb_file), read_only=True)
            
            # Load metadata
            try:
                metadata_rows = conn.execute("SELECT key, value FROM export_metadata").fetchall()
                self._metadata = {key: value for key, value in metadata_rows}
            except Exception:
                self._metadata = {"format": "duckdb", "source": "distributed"}
            
            # Load state neighbors
            self._state_neighbors = {}
            state_rows = conn.execute("""
                SELECT state_fips, neighbor_state_fips, relationship_type
                FROM state_neighbors
                ORDER BY state_fips, neighbor_state_fips
            """).fetchall()
            
            for state_fips, neighbor_state, rel_type in state_rows:
                if state_fips not in self._state_neighbors:
                    self._state_neighbors[state_fips] = []
                self._state_neighbors[state_fips].append({
                    "neighbor_state": neighbor_state,
                    "relationship_type": rel_type
                })
            
            # Load county neighbors
            self._county_neighbors = {}
            county_rows = conn.execute("""
                SELECT state_fips, county_fips, neighbor_state_fips, neighbor_county_fips,
                       relationship_type, shared_boundary_length
                FROM county_neighbors
                ORDER BY state_fips, county_fips, neighbor_state_fips, neighbor_county_fips
            """).fetchall()
            
            for state_fips, county_fips, neighbor_state, neighbor_county, rel_type, boundary_length in county_rows:
                county_key = f"{state_fips}{county_fips}"
                
                if county_key not in self._county_neighbors:
                    self._county_neighbors[county_key] = {
                        "state_fips": state_fips,
                        "county_fips": county_fips,
                        "neighbors": []
                    }
                
                self._county_neighbors[county_key]["neighbors"].append({
                    "state_fips": neighbor_state,
                    "county_fips": neighbor_county,
                    "shared_boundary_length": boundary_length,
                    "relationship_type": rel_type
                })
            
            conn.close()
            self._loaded_format = "duckdb"
            
            logger.info(f"Loaded {len(state_rows)} state relationships and {len(county_rows)} county relationships from DuckDB")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load from DuckDB: {e}")
            return False
    
    def _load_from_json(self) -> bool:
        """Load data from JSON format."""
        # Try JSON files in order of preference
        json_files = [
            self.data_dir / "neighbor_data_compact.json.gz",
            self.data_dir / "neighbor_data.json.gz", 
            self.data_dir / "neighbor_data_compact.json",
            self.data_dir / "neighbor_data.json"
        ]
        
        for json_file in json_files:
            if json_file.exists():
                try:
                    logger.info(f"Loading from JSON format: {json_file.name}")
                    
                    # Load JSON data
                    if json_file.suffix == '.gz':
                        with gzip.open(json_file, 'rt') as f:
                            data = json.load(f)
                    else:
                        with open(json_file, 'r') as f:
                            data = json.load(f)
                    
                    # Extract data
                    self._metadata = data.get("metadata", {})
                    self._state_neighbors = data.get("state_neighbors", {})
                    self._county_neighbors = data.get("county_neighbors", {})
                    
                    self._loaded_format = f"json ({json_file.name})"
                    
                    # Count relationships
                    state_count = sum(len(neighbors) for neighbors in self._state_neighbors.values())
                    county_count = sum(len(county_info["neighbors"]) for county_info in self._county_neighbors.values())
                    
                    logger.info(f"Loaded {state_count} state relationships and {county_count} county relationships from JSON")
                    return True
                    
                except Exception as e:
                    logger.warning(f"Failed to load from {json_file}: {e}")
                    continue
        
        logger.debug("No valid JSON files found")
        return False
    
    def get_state_neighbors(self, state_fips: str) -> List[str]:
        """Get neighboring states for a given state.
        
        Args:
            state_fips: State FIPS code
            
        Returns:
            List of neighboring state FIPS codes
        """
        if not self.load_data():
            return []
        
        neighbors = self._state_neighbors.get(state_fips, [])
        return [n["neighbor_state"] for n in neighbors]
    
    def get_county_neighbors(self, state_fips: str, county_fips: str) -> List[Tuple[str, str]]:
        """Get neighboring counties for a given county.
        
        Args:
            state_fips: State FIPS code
            county_fips: County FIPS code
            
        Returns:
            List of (neighbor_state_fips, neighbor_county_fips) tuples
        """
        if not self.load_data():
            return []
        
        county_key = f"{state_fips}{county_fips}"
        county_info = self._county_neighbors.get(county_key, {})
        neighbors = county_info.get("neighbors", [])
        
        return [(n["state_fips"], n["county_fips"]) for n in neighbors]
    
    def get_county_neighbors_with_details(self, state_fips: str, county_fips: str) -> List[Dict]:
        """Get neighboring counties with full details.
        
        Args:
            state_fips: State FIPS code
            county_fips: County FIPS code
            
        Returns:
            List of neighbor dictionaries with state_fips, county_fips, shared_boundary_length, etc.
        """
        if not self.load_data():
            return []
        
        county_key = f"{state_fips}{county_fips}"
        county_info = self._county_neighbors.get(county_key, {})
        return county_info.get("neighbors", [])
    
    def get_all_states_with_neighbors(self) -> Set[str]:
        """Get all state FIPS codes that have neighbor data.
        
        Returns:
            Set of state FIPS codes
        """
        if not self.load_data():
            return set()
        
        return set(self._state_neighbors.keys())
    
    def get_all_counties_with_neighbors(self) -> Set[Tuple[str, str]]:
        """Get all counties that have neighbor data.
        
        Returns:
            Set of (state_fips, county_fips) tuples
        """
        if not self.load_data():
            return set()
        
        counties = set()
        for county_info in self._county_neighbors.values():
            counties.add((county_info["state_fips"], county_info["county_fips"]))
        
        return counties
    
    def get_metadata(self) -> Dict:
        """Get metadata about the loaded data.
        
        Returns:
            Dictionary with metadata information
        """
        if not self.load_data():
            return {}
        
        metadata = self._metadata.copy()
        metadata["loaded_format"] = self._loaded_format
        metadata["data_dir"] = str(self.data_dir)
        
        return metadata
    
    def is_data_available(self) -> bool:
        """Check if neighbor data is available to load.
        
        Returns:
            True if data files are found
        """
        return self._has_neighbor_data(self.data_dir)


# Global instance for easy access
_distributed_loader = None

def get_distributed_neighbor_loader(data_dir: Optional[Path] = None) -> DistributedNeighborLoader:
    """Get the global distributed neighbor loader instance.
    
    Args:
        data_dir: Directory containing neighbor data files
        
    Returns:
        DistributedNeighborLoader instance
    """
    global _distributed_loader
    
    if _distributed_loader is None or data_dir is not None:
        _distributed_loader = DistributedNeighborLoader(data_dir)
    
    return _distributed_loader

# Convenience functions for direct access
def get_neighboring_states_distributed(state_fips: str) -> List[str]:
    """Get neighboring states using distributed data.
    
    Args:
        state_fips: State FIPS code
        
    Returns:
        List of neighboring state FIPS codes
    """
    loader = get_distributed_neighbor_loader()
    return loader.get_state_neighbors(state_fips)

def get_neighboring_counties_distributed(state_fips: str, county_fips: str) -> List[Tuple[str, str]]:
    """Get neighboring counties using distributed data.
    
    Args:
        state_fips: State FIPS code
        county_fips: County FIPS code
        
    Returns:
        List of (neighbor_state_fips, neighbor_county_fips) tuples
    """
    loader = get_distributed_neighbor_loader()
    return loader.get_county_neighbors(state_fips, county_fips) 