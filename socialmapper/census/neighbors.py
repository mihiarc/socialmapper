#!/usr/bin/env python3
"""
Neighbor relationship management for the SocialMapper census module.

This module provides optimized neighbor identification using a dedicated DuckDB database
to pre-compute and store all neighbor relationships (states, counties, tracts, block groups).
This replaces the need for separate states and counties modules by providing
fast lookups without real-time spatial computation bottlenecks.
"""

import logging
import asyncio
import duckdb
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any
import pandas as pd
import geopandas as gpd
import requests
from shapely.geometry import Point

from socialmapper.progress import get_progress_bar
from socialmapper.util import get_census_api_key, rate_limiter
from . import get_census_database

logger = logging.getLogger(__name__)

# Default path for the dedicated neighbor database
# Use packaged database if available, otherwise fall back to user directory
def get_default_neighbor_db_path() -> Path:
    """Get the default path for the neighbor database."""
    # Try packaged database first
    package_db_path = Path(__file__).parent.parent / "data" / "neighbors.duckdb"
    if package_db_path.exists():
        return package_db_path
    
    # Fall back to user directory for development/custom setups
    return Path.home() / ".socialmapper" / "neighbors.duckdb"

DEFAULT_NEIGHBOR_DB_PATH = get_default_neighbor_db_path()


class NeighborDatabase:
    """
    Dedicated DuckDB database for neighbor relationships.
    
    This keeps neighbor data separate from the main census cache to prevent bloat.
    """
    
    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        """
        Initialize the neighbor database.
        
        Args:
            db_path: Path to the neighbor database file. If None, uses default location.
        """
        self.db_path = Path(db_path) if db_path else DEFAULT_NEIGHBOR_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize connection
        self.conn = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the DuckDB database with spatial extension and neighbor tables."""
        try:
            self.conn = duckdb.connect(str(self.db_path))
            
            # Install and load spatial extension
            self.conn.execute("INSTALL spatial;")
            self.conn.execute("LOAD spatial;")
            
            # Create schema for neighbor relationships
            self._create_neighbor_schema()
            
            get_progress_bar().write(f"Initialized neighbor database at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize neighbor database: {e}")
            raise
    
    def _create_neighbor_schema(self):
        """Create the database schema for neighbor relationships."""
        
        # State neighbor relationships (pre-computed from known adjacencies)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS state_neighbors (
                state_fips VARCHAR(2) NOT NULL,
                neighbor_state_fips VARCHAR(2) NOT NULL,
                relationship_type VARCHAR(20) DEFAULT 'adjacent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(state_fips, neighbor_state_fips)
            );
        """)
        
        # County neighbor relationships (computed from spatial analysis)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS county_neighbors (
                state_fips VARCHAR(2) NOT NULL,
                county_fips VARCHAR(3) NOT NULL,
                neighbor_state_fips VARCHAR(2) NOT NULL,
                neighbor_county_fips VARCHAR(3) NOT NULL,
                relationship_type VARCHAR(20) DEFAULT 'adjacent',
                shared_boundary_length DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(state_fips, county_fips, neighbor_state_fips, neighbor_county_fips)
            );
        """)
        
        # Tract neighbor relationships
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tract_neighbors (
                geoid VARCHAR(11) NOT NULL,
                neighbor_geoid VARCHAR(11) NOT NULL,
                relationship_type VARCHAR(20) DEFAULT 'adjacent',
                shared_boundary_length DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(geoid, neighbor_geoid)
            );
        """)
        
        # Block group neighbor relationships
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS block_group_neighbors (
                geoid VARCHAR(12) NOT NULL,
                neighbor_geoid VARCHAR(12) NOT NULL,
                relationship_type VARCHAR(20) DEFAULT 'adjacent',
                shared_boundary_length DOUBLE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(geoid, neighbor_geoid)
            );
        """)
        
        # Point-to-geography lookup cache for fast POI processing
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS point_geography_cache (
                lat DOUBLE NOT NULL,
                lon DOUBLE NOT NULL,
                state_fips VARCHAR(2),
                county_fips VARCHAR(3),
                tract_geoid VARCHAR(11),
                block_group_geoid VARCHAR(12),
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(lat, lon)
            );
        """)
        
        # Metadata table for tracking neighbor data
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS neighbor_metadata (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create spatial indexes for fast lookups
        self._create_neighbor_indexes()
    
    def _create_neighbor_indexes(self):
        """Create indexes optimized for neighbor lookups."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_state_neighbors_state ON state_neighbors(state_fips);",
            "CREATE INDEX IF NOT EXISTS idx_county_neighbors_county ON county_neighbors(state_fips, county_fips);",
            "CREATE INDEX IF NOT EXISTS idx_tract_neighbors_tract ON tract_neighbors(geoid);",
            "CREATE INDEX IF NOT EXISTS idx_block_group_neighbors_bg ON block_group_neighbors(geoid);",
            "CREATE INDEX IF NOT EXISTS idx_point_cache_coords ON point_geography_cache(lat, lon);",
            "CREATE INDEX IF NOT EXISTS idx_point_cache_state ON point_geography_cache(state_fips);",
            "CREATE INDEX IF NOT EXISTS idx_point_cache_county ON point_geography_cache(state_fips, county_fips);"
        ]
        
        for index_sql in indexes:
            try:
                self.conn.execute(index_sql)
            except Exception as e:
                logger.warning(f"Failed to create index: {e}")
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class NeighborManager:
    """
    Manages pre-computed neighbor relationships using a dedicated DuckDB database.
    
    This class handles:
    - Pre-computing neighbor relationships for all geographic levels
    - Fast neighbor lookups without real-time spatial computation
    - Point-to-geography lookups for POIs
    - Cross-state neighbor relationships
    """
    
    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        """
        Initialize the neighbor manager with a dedicated database.
        
        Args:
            db_path: Path to the neighbor database file. If None, uses default location.
        """
        self.db = NeighborDatabase(db_path)
    
    def initialize_state_neighbors(self, force_refresh: bool = False) -> int:
        """
        Initialize state neighbor relationships from known adjacencies.
        
        Args:
            force_refresh: Whether to refresh existing data
            
        Returns:
            Number of neighbor relationships created
        """
        # Check if already initialized
        if not force_refresh:
            count = self.db.conn.execute("SELECT COUNT(*) FROM state_neighbors").fetchone()[0]
            if count > 0:
                get_progress_bar().write(f"State neighbors already initialized ({count} relationships)")
                return count
        
        # State adjacency data (from the states module)
        STATE_NEIGHBORS = {
            '01': ['12', '13', '28', '47'],  # AL: FL, GA, MS, TN
            '02': [],  # AK: (no land borders)
            '04': ['06', '08', '35', '32', '49'],  # AZ: CA, CO, NM, NV, UT
            '05': ['22', '29', '28', '40', '47', '48'],  # AR: LA, MO, MS, OK, TN, TX
            '06': ['04', '32', '41'],  # CA: AZ, NV, OR
            '08': ['04', '20', '31', '35', '40', '49', '56'],  # CO: AZ, KS, NE, NM, OK, UT, WY
            '09': ['25', '36', '44'],  # CT: MA, NY, RI
            '10': ['24', '34', '42'],  # DE: MD, NJ, PA
            '12': ['01', '13'],  # FL: AL, GA
            '13': ['01', '12', '37', '45', '47'],  # GA: AL, FL, NC, SC, TN
            '15': [],  # HI: (no land borders)
            '16': ['30', '32', '41', '49', '53', '56'],  # ID: MT, NV, OR, UT, WA, WY
            '17': ['18', '19', '21', '29', '55'],  # IL: IN, IA, KY, MO, WI
            '18': ['17', '21', '26', '39'],  # IN: IL, KY, MI, OH
            '19': ['17', '27', '29', '31', '46', '55'],  # IA: IL, MN, MO, NE, SD, WI
            '20': ['08', '29', '31', '40'],  # KS: CO, MO, NE, OK
            '21': ['17', '18', '29', '39', '47', '51', '54'],  # KY: IL, IN, MO, OH, TN, VA, WV
            '22': ['05', '28', '48'],  # LA: AR, MS, TX
            '23': ['33'],  # ME: NH
            '24': ['10', '42', '51', '54', '11'],  # MD: DE, PA, VA, WV, DC
            '25': ['09', '33', '36', '44', '50'],  # MA: CT, NH, NY, RI, VT
            '26': ['18', '39', '55'],  # MI: IN, OH, WI
            '27': ['19', '38', '46', '55'],  # MN: IA, ND, SD, WI
            '28': ['01', '05', '22', '47'],  # MS: AL, AR, LA, TN
            '29': ['05', '17', '19', '20', '21', '31', '40', '47'],  # MO: AR, IL, IA, KS, KY, NE, OK, TN
            '30': ['16', '38', '46', '56'],  # MT: ID, ND, SD, WY
            '31': ['08', '19', '20', '29', '46', '56'],  # NE: CO, IA, KS, MO, SD, WY
            '32': ['04', '06', '16', '41', '49'],  # NV: AZ, CA, ID, OR, UT
            '33': ['23', '25', '50'],  # NH: ME, MA, VT
            '34': ['10', '36', '42'],  # NJ: DE, NY, PA
            '35': ['04', '08', '40', '48', '49'],  # NM: AZ, CO, OK, TX, UT
            '36': ['09', '25', '34', '42', '50'],  # NY: CT, MA, NJ, PA, VT
            '37': ['13', '45', '47', '51'],  # NC: GA, SC, TN, VA
            '38': ['27', '30', '46'],  # ND: MN, MT, SD
            '39': ['18', '21', '26', '42', '54'],  # OH: IN, KY, MI, PA, WV
            '40': ['05', '08', '20', '29', '35', '48'],  # OK: AR, CO, KS, MO, NM, TX
            '41': ['06', '16', '32', '53'],  # OR: CA, ID, NV, WA
            '42': ['10', '24', '34', '36', '39', '54'],  # PA: DE, MD, NJ, NY, OH, WV
            '44': ['09', '25'],  # RI: CT, MA
            '45': ['13', '37'],  # SC: GA, NC
            '46': ['19', '27', '30', '31', '38', '56'],  # SD: IA, MN, MT, NE, ND, WY
            '47': ['01', '05', '13', '21', '28', '29', '37', '51'],  # TN: AL, AR, GA, KY, MS, MO, NC, VA
            '48': ['05', '22', '35', '40'],  # TX: AR, LA, NM, OK
            '49': ['04', '08', '16', '35', '32', '56'],  # UT: AZ, CO, ID, NM, NV, WY
            '50': ['25', '33', '36'],  # VT: MA, NH, NY
            '51': ['21', '24', '37', '47', '54', '11'],  # VA: KY, MD, NC, TN, WV, DC
            '53': ['16', '41'],  # WA: ID, OR
            '54': ['21', '24', '39', '42', '51'],  # WV: KY, MD, OH, PA, VA
            '55': ['17', '19', '26', '27'],  # WI: IL, IA, MI, MN
            '56': ['08', '16', '30', '31', '46', '49'],  # WY: CO, ID, MT, NE, SD, UT
            '11': ['24', '51']  # DC: MD, VA
        }
        
        # Clear existing data if refreshing
        if force_refresh:
            self.db.conn.execute("DELETE FROM state_neighbors")
        
        # Insert state neighbor relationships
        relationships = []
        for state_fips, neighbors in STATE_NEIGHBORS.items():
            for neighbor_fips in neighbors:
                relationships.append((state_fips, neighbor_fips, 'adjacent'))
        
        if relationships:
            self.db.conn.executemany(
                "INSERT OR IGNORE INTO state_neighbors (state_fips, neighbor_state_fips, relationship_type) VALUES (?, ?, ?)",
                relationships
            )
        
        count = len(relationships)
        get_progress_bar().write(f"Initialized {count} state neighbor relationships")
        
        # Update metadata
        self.db.conn.execute(
            "INSERT OR REPLACE INTO neighbor_metadata (key, value) VALUES (?, ?)",
            ['state_neighbors_initialized', str(count)]
        )
        
        return count
    
    async def initialize_county_neighbors(
        self, 
        state_fips_list: Optional[List[str]] = None,
        force_refresh: bool = False,
        include_cross_state: bool = True
    ) -> int:
        """
        Initialize county neighbor relationships using spatial analysis.
        
        NOTE: This method is for package development/setup only. In production,
        county neighbor relationships should be pre-computed and included in the package.
        End users should not need to call this method.
        
        Args:
            state_fips_list: List of state FIPS codes to process. If None, processes all states.
            force_refresh: Whether to refresh existing data
            include_cross_state: Whether to include cross-state county neighbors
            
        Returns:
            Number of neighbor relationships created
        """
        if state_fips_list is None:
            # Get all states from the state neighbors table
            state_fips_list = [row[0] for row in self.db.conn.execute("SELECT DISTINCT state_fips FROM state_neighbors").fetchall()]
        
        total_relationships = 0
        
        for state_fips in state_fips_list:
            # Check if already processed
            if not force_refresh:
                count = self.db.conn.execute(
                    "SELECT COUNT(*) FROM county_neighbors WHERE state_fips = ?", 
                    [state_fips]
                ).fetchone()[0]
                
                if count > 0:
                    get_progress_bar().write(f"County neighbors for state {state_fips} already initialized ({count} relationships)")
                    total_relationships += count
                    continue
            
            # Get counties with geometries for this state
            counties_gdf = await self._get_counties_with_geometries(state_fips)
            if counties_gdf.empty:
                get_progress_bar().write(f"No counties found for state {state_fips}")
                continue
            
            # Compute within-state neighbors
            within_state_neighbors = self._compute_county_neighbors_spatial(counties_gdf, state_fips)
            
            # Clear existing data for this state if refreshing
            if force_refresh:
                self.db.conn.execute("DELETE FROM county_neighbors WHERE state_fips = ?", [state_fips])
            
            # Insert within-state relationships
            if within_state_neighbors:
                self.db.conn.executemany("""
                    INSERT OR IGNORE INTO county_neighbors 
                    (state_fips, county_fips, neighbor_state_fips, neighbor_county_fips, relationship_type, shared_boundary_length)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, within_state_neighbors)
                
                total_relationships += len(within_state_neighbors)
                get_progress_bar().write(f"Added {len(within_state_neighbors)} within-state neighbors for {state_fips}")
            
            # Compute cross-state neighbors if requested
            if include_cross_state:
                # Get neighboring states
                neighboring_states = self.get_neighboring_states(state_fips)
                
                for neighbor_state_fips in neighboring_states:
                    # Get counties for neighboring state
                    neighbor_counties_gdf = await self._get_counties_with_geometries(neighbor_state_fips)
                    if neighbor_counties_gdf.empty:
                        continue
                    
                    # Compute cross-state neighbors
                    cross_state_neighbors = self._compute_cross_state_county_neighbors(
                        counties_gdf, neighbor_counties_gdf, state_fips, neighbor_state_fips
                    )
                    
                    if cross_state_neighbors:
                        self.db.conn.executemany("""
                            INSERT OR IGNORE INTO county_neighbors 
                            (state_fips, county_fips, neighbor_state_fips, neighbor_county_fips, relationship_type, shared_boundary_length)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, cross_state_neighbors)
                        
                        total_relationships += len(cross_state_neighbors)
                        get_progress_bar().write(f"Added {len(cross_state_neighbors)} cross-state neighbors between {state_fips} and {neighbor_state_fips}")
        
        # Update metadata
        self.db.conn.execute(
            "INSERT OR REPLACE INTO neighbor_metadata (key, value) VALUES (?, ?)",
            ['county_neighbors_total', str(total_relationships)]
        )
        
        return total_relationships
    
    async def _get_counties_with_geometries(self, state_fips: str) -> gpd.GeoDataFrame:
        """
        Get counties with geometries for a state using local shapefile.
        
        Args:
            state_fips: State FIPS code
            
        Returns:
            GeoDataFrame with county geometries
        """
        try:
            # Use local US county shapefile and filter by state
            counties_gdf = await self._fetch_counties_from_local_shapefile(state_fips)
            
            return counties_gdf
            
        except Exception as e:
            logger.error(f"Failed to get counties for state {state_fips}: {e}")
            return gpd.GeoDataFrame()
    
    # Note: Deprecated methods have been removed.
    # County neighbor relationships are now pre-computed and packaged.
    
    def _compute_county_neighbors_spatial(self, counties_gdf: gpd.GeoDataFrame, state_fips: str) -> List[Tuple]:
        """
        Compute county neighbor relationships using spatial analysis.
        
        Args:
            counties_gdf: GeoDataFrame with county geometries
            state_fips: State FIPS code
            
        Returns:
            List of tuples: (state_fips, county_fips, neighbor_state_fips, neighbor_county_fips, relationship_type, boundary_length)
        """
        neighbors = []
        
        for i, county1 in counties_gdf.iterrows():
            for j, county2 in counties_gdf.iterrows():
                if i >= j:  # Avoid duplicates and self-comparison
                    continue
                
                try:
                    # Check if counties share a boundary
                    if county1.geometry.touches(county2.geometry):
                        # Calculate shared boundary length
                        intersection = county1.geometry.boundary.intersection(county2.geometry.boundary)
                        boundary_length = intersection.length if hasattr(intersection, 'length') else 0
                        
                        # Add both directions
                        neighbors.append((
                            state_fips, county1['COUNTYFP'], state_fips, county2['COUNTYFP'], 
                            'adjacent', boundary_length
                        ))
                        neighbors.append((
                            state_fips, county2['COUNTYFP'], state_fips, county1['COUNTYFP'], 
                            'adjacent', boundary_length
                        ))
                        
                except Exception as e:
                    logger.warning(f"Failed to compute neighbor relationship between counties: {e}")
                    continue
        
        return neighbors
    
    def _compute_cross_state_county_neighbors(
        self, 
        counties1_gdf: gpd.GeoDataFrame, 
        counties2_gdf: gpd.GeoDataFrame,
        state1_fips: str,
        state2_fips: str
    ) -> List[Tuple]:
        """
        Compute cross-state county neighbor relationships.
        
        Args:
            counties1_gdf: Counties from first state
            counties2_gdf: Counties from second state
            state1_fips: First state FIPS code
            state2_fips: Second state FIPS code
            
        Returns:
            List of neighbor relationships
        """
        neighbors = []
        
        for _, county1 in counties1_gdf.iterrows():
            for _, county2 in counties2_gdf.iterrows():
                try:
                    # Check if counties share a boundary
                    if county1.geometry.touches(county2.geometry):
                        # Calculate shared boundary length
                        intersection = county1.geometry.boundary.intersection(county2.geometry.boundary)
                        boundary_length = intersection.length if hasattr(intersection, 'length') else 0
                        
                        # Add relationship from state1 to state2
                        neighbors.append((
                            state1_fips, county1['COUNTYFP'], state2_fips, county2['COUNTYFP'], 
                            'adjacent', boundary_length
                        ))
                        
                except Exception as e:
                    logger.warning(f"Failed to compute cross-state neighbor relationship: {e}")
                    continue
        
        return neighbors
    
    def get_neighboring_states(self, state_fips: str) -> List[str]:
        """
        Get neighboring states for a given state.
        
        Args:
            state_fips: State FIPS code
            
        Returns:
            List of neighboring state FIPS codes
        """
        result = self.db.conn.execute(
            "SELECT neighbor_state_fips FROM state_neighbors WHERE state_fips = ? ORDER BY neighbor_state_fips",
            [state_fips]
        ).fetchall()
        
        return [row[0] for row in result]
    
    def get_neighboring_counties(
        self, 
        state_fips: str, 
        county_fips: str,
        include_cross_state: bool = True
    ) -> List[Tuple[str, str]]:
        """
        Get neighboring counties for a given county.
        
        Args:
            state_fips: State FIPS code
            county_fips: County FIPS code
            include_cross_state: Whether to include cross-state neighbors
            
        Returns:
            List of (neighbor_state_fips, neighbor_county_fips) tuples
        """
        if include_cross_state:
            query = """
                SELECT neighbor_state_fips, neighbor_county_fips 
                FROM county_neighbors 
                WHERE state_fips = ? AND county_fips = ?
                ORDER BY neighbor_state_fips, neighbor_county_fips
            """
        else:
            query = """
                SELECT neighbor_state_fips, neighbor_county_fips 
                FROM county_neighbors 
                WHERE state_fips = ? AND county_fips = ? AND neighbor_state_fips = ?
                ORDER BY neighbor_county_fips
            """
        
        if include_cross_state:
            result = self.db.conn.execute(query, [state_fips, county_fips]).fetchall()
        else:
            result = self.db.conn.execute(query, [state_fips, county_fips, state_fips]).fetchall()
        
        return [(row[0], row[1]) for row in result]
    
    def get_geography_from_point(
        self, 
        lat: float, 
        lon: float,
        use_cache: bool = True,
        cache_result: bool = True
    ) -> Dict[str, Optional[str]]:
        """
        Get geographic identifiers for a point using cached lookups.
        
        Args:
            lat: Latitude
            lon: Longitude
            use_cache: Whether to use cached results
            cache_result: Whether to cache the result
            
        Returns:
            Dictionary with state_fips, county_fips, tract_geoid, block_group_geoid
        """
        # Check cache first
        if use_cache:
            cached = self.db.conn.execute(
                "SELECT state_fips, county_fips, tract_geoid, block_group_geoid FROM point_geography_cache WHERE lat = ? AND lon = ?",
                [lat, lon]
            ).fetchone()
            
            if cached:
                return {
                    'state_fips': cached[0],
                    'county_fips': cached[1], 
                    'tract_geoid': cached[2],
                    'block_group_geoid': cached[3]
                }
        
        # Geocode the point
        result = self._geocode_point(lat, lon)
        
        # Cache the result
        if cache_result:
            self.db.conn.execute("""
                INSERT OR REPLACE INTO point_geography_cache 
                (lat, lon, state_fips, county_fips, tract_geoid, block_group_geoid)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [
                lat, lon, 
                result.get('state_fips'),
                result.get('county_fips'),
                result.get('tract_geoid'),
                result.get('block_group_geoid')
            ])
        
        return result
    
    def _geocode_point(self, lat: float, lon: float) -> Dict[str, Optional[str]]:
        """
        Geocode a point to get geographic identifiers using Census API.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with geographic identifiers
        """
        try:
            # Use Census Geocoding API
            url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
            params = {
                'x': lon,
                'y': lat,
                'benchmark': 'Public_AR_Current',
                'vintage': 'Current_Current',
                'format': 'json'
            }
            
            rate_limiter.wait_if_needed("census")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'result' not in data or 'geographies' not in data['result']:
                return {
                    'state_fips': None,
                    'county_fips': None,
                    'tract_geoid': None,
                    'block_group_geoid': None
                }
            
            geographies = data['result']['geographies']
            
            # Extract identifiers
            state_fips = None
            county_fips = None
            tract_geoid = None
            block_group_geoid = None
            
            # Get state
            if 'States' in geographies and geographies['States']:
                state_fips = geographies['States'][0].get('STATE')
            
            # Get county
            if 'Counties' in geographies and geographies['Counties']:
                county_fips = geographies['Counties'][0].get('COUNTY')
            
            # Get tract
            if 'Census Tracts' in geographies and geographies['Census Tracts']:
                tract_geoid = geographies['Census Tracts'][0].get('GEOID')
            
            # Get block group
            if 'Census Block Groups' in geographies and geographies['Census Block Groups']:
                block_group_geoid = geographies['Census Block Groups'][0].get('GEOID')
            
            return {
                'state_fips': state_fips,
                'county_fips': county_fips,
                'tract_geoid': tract_geoid,
                'block_group_geoid': block_group_geoid
            }
            
        except Exception as e:
            logger.warning(f"Failed to geocode point ({lat}, {lon}): {e}")
            return {
                'state_fips': None,
                'county_fips': None,
                'tract_geoid': None,
                'block_group_geoid': None
            }
    
    def get_counties_from_pois(
        self, 
        pois: List[Dict],
        include_neighbors: bool = True,
        neighbor_distance: int = 1
    ) -> List[Tuple[str, str]]:
        """
        Get counties for a list of POIs, optionally including neighboring counties.
        
        Args:
            pois: List of POI dictionaries with 'lat' and 'lon' keys
            include_neighbors: Whether to include neighboring counties
            neighbor_distance: Distance of neighbors to include (1 = immediate neighbors)
            
        Returns:
            List of unique (state_fips, county_fips) tuples
        """
        counties = set()
        
        # Get counties for each POI
        for poi in pois:
            if 'lat' not in poi or 'lon' not in poi:
                continue
            
            try:
                geography = self.get_geography_from_point(poi['lat'], poi['lon'])
                
                if geography['state_fips'] and geography['county_fips']:
                    counties.add((geography['state_fips'], geography['county_fips']))
                    
                    # Add neighboring counties if requested
                    if include_neighbors:
                        neighbor_counties = self._get_county_neighbors_recursive(
                            geography['state_fips'], 
                            geography['county_fips'], 
                            neighbor_distance
                        )
                        counties.update(neighbor_counties)
                        
            except Exception as e:
                logger.warning(f"Failed to process POI {poi}: {e}")
                continue
        
        return list(counties)
    
    def _get_county_neighbors_recursive(
        self, 
        state_fips: str, 
        county_fips: str, 
        distance: int,
        visited: Optional[Set] = None
    ) -> Set[Tuple[str, str]]:
        """
        Get county neighbors recursively up to a specified distance.
        
        Args:
            state_fips: State FIPS code
            county_fips: County FIPS code
            distance: Maximum distance to search
            visited: Set of already visited counties
            
        Returns:
            Set of (state_fips, county_fips) tuples
        """
        if visited is None:
            visited = set()
        
        if distance <= 0:
            return set()
        
        current_county = (state_fips, county_fips)
        if current_county in visited:
            return set()
        
        visited.add(current_county)
        neighbors = set()
        
        # Get immediate neighbors
        immediate_neighbors = self.get_neighboring_counties(state_fips, county_fips)
        neighbors.update(immediate_neighbors)
        
        # Recursively get neighbors at greater distances
        if distance > 1:
            for neighbor_state, neighbor_county in immediate_neighbors:
                if (neighbor_state, neighbor_county) not in visited:
                    recursive_neighbors = self._get_county_neighbors_recursive(
                        neighbor_state, neighbor_county, distance - 1, visited.copy()
                    )
                    neighbors.update(recursive_neighbors)
        
        return neighbors
    
    def get_neighbor_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the neighbor relationships in the database.
        
        Returns:
            Dictionary with statistics
        """
        stats = {}
        
        # State neighbor statistics
        state_count = self.db.conn.execute("SELECT COUNT(*) FROM state_neighbors").fetchone()[0]
        stats['state_relationships'] = state_count
        
        # County neighbor statistics
        county_count = self.db.conn.execute("SELECT COUNT(*) FROM county_neighbors").fetchone()[0]
        stats['county_relationships'] = county_count
        
        # Cross-state county relationships
        cross_state_count = self.db.conn.execute(
            "SELECT COUNT(*) FROM county_neighbors WHERE state_fips != neighbor_state_fips"
        ).fetchone()[0]
        stats['cross_state_county_relationships'] = cross_state_count
        
        # Point cache statistics
        cache_count = self.db.conn.execute("SELECT COUNT(*) FROM point_geography_cache").fetchone()[0]
        stats['cached_points'] = cache_count
        
        # States with county data
        states_with_counties = self.db.conn.execute(
            "SELECT COUNT(DISTINCT state_fips) FROM county_neighbors"
        ).fetchone()[0]
        stats['states_with_county_data'] = states_with_counties
        
        return stats


# Global instance
_neighbor_manager = None

def get_neighbor_manager(db_path: Optional[Union[str, Path]] = None) -> NeighborManager:
    """
    Get the global neighbor manager instance.
    
    Args:
        db_path: Optional path to neighbor database file
        
    Returns:
        NeighborManager instance
    """
    global _neighbor_manager
    
    if _neighbor_manager is None or db_path is not None:
        _neighbor_manager = NeighborManager(db_path)
    
    return _neighbor_manager

def initialize_all_neighbors(force_refresh: bool = False) -> Dict[str, int]:
    """
    Initialize all neighbor relationships.
    
    Args:
        force_refresh: Whether to refresh existing data
        
    Returns:
        Dictionary with counts of relationships created
    """
    manager = get_neighbor_manager()
    
    results = {}
    
    # Initialize state neighbors
    results['state_neighbors'] = manager.initialize_state_neighbors(force_refresh)
    
    # Initialize county neighbors (async)
    import asyncio
    results['county_neighbors'] = asyncio.run(
        manager.initialize_county_neighbors(force_refresh=force_refresh)
    )
    
    return results

def get_neighboring_states(state_fips: str) -> List[str]:
    """Get neighboring states for a given state."""
    manager = get_neighbor_manager()
    return manager.get_neighboring_states(state_fips)

def get_neighboring_counties(state_fips: str, county_fips: str, include_cross_state: bool = True) -> List[Tuple[str, str]]:
    """Get neighboring counties for a given county."""
    manager = get_neighbor_manager()
    return manager.get_neighboring_counties(state_fips, county_fips, include_cross_state)

def get_geography_from_point(lat: float, lon: float) -> Dict[str, Optional[str]]:
    """Get geographic identifiers for a point."""
    manager = get_neighbor_manager()
    return manager.get_geography_from_point(lat, lon)

def get_counties_from_pois(pois: List[Dict], include_neighbors: bool = True) -> List[Tuple[str, str]]:
    """Get counties for a list of POIs."""
    manager = get_neighbor_manager()
    return manager.get_counties_from_pois(pois, include_neighbors) 