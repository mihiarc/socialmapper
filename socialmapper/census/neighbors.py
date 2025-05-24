#!/usr/bin/env python3
"""
Neighbor relationship management for the SocialMapper census module.

This module provides optimized neighbor identification using DuckDB spatial indexing
to pre-compute and store all neighbor relationships (states, counties, tracts, block groups).
This replaces the need for separate states and counties modules by providing
fast lookups without real-time spatial computation bottlenecks.
"""

import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any
import pandas as pd
import geopandas as gpd
import requests
from shapely.geometry import Point

from socialmapper.progress import get_progress_bar
from socialmapper.util import get_census_api_key, rate_limiter
from . import get_census_database, CensusDatabase

logger = logging.getLogger(__name__)


class NeighborManager:
    """
    Manages pre-computed neighbor relationships using DuckDB spatial indexing.
    
    This class handles:
    - Pre-computing neighbor relationships for all geographic levels
    - Fast neighbor lookups without real-time spatial computation
    - Point-to-geography lookups for POIs
    - Cross-state neighbor relationships
    """
    
    def __init__(self, db: Optional[CensusDatabase] = None):
        self.db = db or get_census_database()
        self._ensure_neighbor_schema()
    
    def _ensure_neighbor_schema(self):
        """Create neighbor relationship tables if they don't exist."""
        
        # State neighbor relationships (pre-computed from known adjacencies)
        self.db.conn.execute("""
            CREATE TABLE IF NOT EXISTS state_neighbors (
                state_fips VARCHAR(2) NOT NULL,
                neighbor_state_fips VARCHAR(2) NOT NULL,
                relationship_type VARCHAR(20) DEFAULT 'adjacent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(state_fips, neighbor_state_fips)
            );
        """)
        
        # County neighbor relationships (computed from spatial analysis)
        self.db.conn.execute("""
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
        self.db.conn.execute("""
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
        self.db.conn.execute("""
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
        self.db.conn.execute("""
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
                self.db.conn.execute(index_sql)
            except Exception as e:
                logger.warning(f"Failed to create index: {e}")
    
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
        
        # Insert neighbor relationships
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
        return count
    
    async def initialize_county_neighbors(
        self, 
        state_fips_list: Optional[List[str]] = None,
        force_refresh: bool = False,
        include_cross_state: bool = True
    ) -> int:
        """
        Initialize county neighbor relationships using spatial analysis.
        
        Args:
            state_fips_list: List of states to process (None for all)
            force_refresh: Whether to refresh existing data
            include_cross_state: Whether to include cross-state neighbors
            
        Returns:
            Number of neighbor relationships created
        """
        if state_fips_list is None:
            # Get all states that have geographic units
            result = self.db.conn.execute("""
                SELECT DISTINCT STATEFP 
                FROM geographic_units 
                WHERE unit_type = 'county' 
                ORDER BY STATEFP
            """).fetchall()
            state_fips_list = [row[0] for row in result]
        
        if not state_fips_list:
            get_progress_bar().write("No states found for county neighbor initialization")
            return 0
        
        # Check if already initialized
        if not force_refresh:
            count = self.db.conn.execute("SELECT COUNT(*) FROM county_neighbors").fetchone()[0]
            if count > 0:
                get_progress_bar().write(f"County neighbors already initialized ({count} relationships)")
                return count
        
        total_relationships = 0
        
        # Process each state
        for state_fips in get_progress_bar(state_fips_list, desc="Computing county neighbors", unit="state"):
            try:
                # Get counties for this state with geometries
                counties_gdf = await self._get_counties_with_geometries(state_fips)
                if counties_gdf.empty:
                    continue
                
                # Find neighbors within the same state
                intra_state_neighbors = self._compute_county_neighbors_spatial(counties_gdf, state_fips)
                total_relationships += len(intra_state_neighbors)
                
                # Find cross-state neighbors if requested
                if include_cross_state:
                    neighboring_states = self.get_neighboring_states(state_fips)
                    for neighbor_state in neighboring_states:
                        neighbor_counties_gdf = await self._get_counties_with_geometries(neighbor_state)
                        if not neighbor_counties_gdf.empty:
                            cross_state_neighbors = self._compute_cross_state_county_neighbors(
                                counties_gdf, neighbor_counties_gdf, state_fips, neighbor_state
                            )
                            total_relationships += len(cross_state_neighbors)
                
            except Exception as e:
                logger.error(f"Failed to process county neighbors for state {state_fips}: {e}")
                continue
        
        get_progress_bar().write(f"Initialized {total_relationships} county neighbor relationships")
        return total_relationships
    
    async def _get_counties_with_geometries(self, state_fips: str) -> gpd.GeoDataFrame:
        """Get counties for a state with their geometries."""
        try:
            # Try to get from boundary cache first
            if self.db.cache_boundaries:
                cached_gdf = self.db.conn.execute("""
                    SELECT 
                        gu.GEOID,
                        gu.STATEFP,
                        gu.COUNTYFP,
                        gu.NAME,
                        ST_AsText(bc.geometry) as geometry_wkt
                    FROM geographic_units gu
                    JOIN boundary_cache bc ON gu.GEOID = bc.GEOID
                    WHERE gu.STATEFP = ? AND gu.unit_type = 'county'
                """, [state_fips]).df()
                
                if not cached_gdf.empty:
                    from shapely import wkt
                    cached_gdf['geometry'] = cached_gdf['geometry_wkt'].apply(wkt.loads)
                    return gpd.GeoDataFrame(cached_gdf.drop('geometry_wkt', axis=1), 
                                          geometry='geometry', crs='EPSG:4326')
            
            # Fetch from Census API
            return await self._fetch_counties_from_api(state_fips)
            
        except Exception as e:
            logger.error(f"Failed to get counties for state {state_fips}: {e}")
            return gpd.GeoDataFrame()
    
    async def _fetch_counties_from_api(self, state_fips: str) -> gpd.GeoDataFrame:
        """Fetch county boundaries from Census API."""
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query"
        params = {
            'where': f"STATE='{state_fips}'",
            'outFields': 'STATE,COUNTY,NAME,GEOID',
            'returnGeometry': 'true',
            'f': 'geojson'
        }
        
        rate_limiter.wait_if_needed("census")
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        if 'features' not in data or not data['features']:
            return gpd.GeoDataFrame()
        
        gdf = gpd.GeoDataFrame.from_features(data['features'], crs="EPSG:4326")
        
        # Standardize column names
        if 'STATE' in gdf.columns:
            gdf['STATEFP'] = gdf['STATE']
        if 'COUNTY' in gdf.columns:
            gdf['COUNTYFP'] = gdf['COUNTY']
        
        # Create GEOID if missing
        if 'GEOID' not in gdf.columns:
            gdf['GEOID'] = gdf['STATEFP'].str.zfill(2) + gdf['COUNTYFP'].str.zfill(3)
        
        return gdf
    
    def _compute_county_neighbors_spatial(self, counties_gdf: gpd.GeoDataFrame, state_fips: str) -> List[Tuple]:
        """Compute neighbor relationships within a state using spatial analysis."""
        relationships = []
        
        for i, county1 in counties_gdf.iterrows():
            for j, county2 in counties_gdf.iterrows():
                if i >= j:  # Avoid duplicates and self-comparison
                    continue
                
                try:
                    geom1 = county1.geometry
                    geom2 = county2.geometry
                    
                    if geom1.is_valid and geom2.is_valid and geom1.touches(geom2):
                        # Calculate shared boundary length
                        shared_boundary = geom1.boundary.intersection(geom2.boundary)
                        boundary_length = shared_boundary.length if hasattr(shared_boundary, 'length') else 0
                        
                        # Add both directions
                        relationships.extend([
                            (state_fips, county1['COUNTYFP'], state_fips, county2['COUNTYFP'], 'adjacent', boundary_length),
                            (state_fips, county2['COUNTYFP'], state_fips, county1['COUNTYFP'], 'adjacent', boundary_length)
                        ])
                
                except Exception as e:
                    logger.warning(f"Failed to compute neighbor relationship: {e}")
                    continue
        
        # Store in database
        if relationships:
            self.db.conn.executemany("""
                INSERT OR IGNORE INTO county_neighbors 
                (state_fips, county_fips, neighbor_state_fips, neighbor_county_fips, relationship_type, shared_boundary_length)
                VALUES (?, ?, ?, ?, ?, ?)
            """, relationships)
        
        return relationships
    
    def _compute_cross_state_county_neighbors(
        self, 
        counties1_gdf: gpd.GeoDataFrame, 
        counties2_gdf: gpd.GeoDataFrame,
        state1_fips: str,
        state2_fips: str
    ) -> List[Tuple]:
        """Compute neighbor relationships between counties in different states."""
        relationships = []
        
        for _, county1 in counties1_gdf.iterrows():
            for _, county2 in counties2_gdf.iterrows():
                try:
                    geom1 = county1.geometry
                    geom2 = county2.geometry
                    
                    if geom1.is_valid and geom2.is_valid and geom1.touches(geom2):
                        # Calculate shared boundary length
                        shared_boundary = geom1.boundary.intersection(geom2.boundary)
                        boundary_length = shared_boundary.length if hasattr(shared_boundary, 'length') else 0
                        
                        # Add both directions
                        relationships.extend([
                            (state1_fips, county1['COUNTYFP'], state2_fips, county2['COUNTYFP'], 'adjacent', boundary_length),
                            (state2_fips, county2['COUNTYFP'], state1_fips, county1['COUNTYFP'], 'adjacent', boundary_length)
                        ])
                
                except Exception as e:
                    logger.warning(f"Failed to compute cross-state neighbor relationship: {e}")
                    continue
        
        # Store in database
        if relationships:
            self.db.conn.executemany("""
                INSERT OR IGNORE INTO county_neighbors 
                (state_fips, county_fips, neighbor_state_fips, neighbor_county_fips, relationship_type, shared_boundary_length)
                VALUES (?, ?, ?, ?, ?, ?)
            """, relationships)
        
        return relationships
    
    # Fast lookup methods (the main benefit of pre-computation)
    
    def get_neighboring_states(self, state_fips: str) -> List[str]:
        """Get neighboring states for a given state (fast lookup)."""
        result = self.db.conn.execute("""
            SELECT neighbor_state_fips 
            FROM state_neighbors 
            WHERE state_fips = ?
            ORDER BY neighbor_state_fips
        """, [state_fips]).fetchall()
        
        return [row[0] for row in result]
    
    def get_neighboring_counties(
        self, 
        state_fips: str, 
        county_fips: str,
        include_cross_state: bool = True
    ) -> List[Tuple[str, str]]:
        """Get neighboring counties for a given county (fast lookup)."""
        if include_cross_state:
            result = self.db.conn.execute("""
                SELECT neighbor_state_fips, neighbor_county_fips 
                FROM county_neighbors 
                WHERE state_fips = ? AND county_fips = ?
                ORDER BY neighbor_state_fips, neighbor_county_fips
            """, [state_fips, county_fips]).fetchall()
        else:
            result = self.db.conn.execute("""
                SELECT neighbor_state_fips, neighbor_county_fips 
                FROM county_neighbors 
                WHERE state_fips = ? AND county_fips = ? AND neighbor_state_fips = ?
                ORDER BY neighbor_county_fips
            """, [state_fips, county_fips, state_fips]).fetchall()
        
        return [(row[0], row[1]) for row in result]
    
    def get_geography_from_point(
        self, 
        lat: float, 
        lon: float,
        use_cache: bool = True,
        cache_result: bool = True
    ) -> Dict[str, Optional[str]]:
        """
        Get geographic identifiers for a point (fast lookup with caching).
        
        Args:
            lat: Latitude
            lon: Longitude
            use_cache: Whether to check cache first
            cache_result: Whether to cache the result
            
        Returns:
            Dictionary with state_fips, county_fips, tract_geoid, block_group_geoid
        """
        # Check cache first
        if use_cache:
            cached = self.db.conn.execute("""
                SELECT state_fips, county_fips, tract_geoid, block_group_geoid
                FROM point_geography_cache
                WHERE lat = ? AND lon = ?
            """, [lat, lon]).fetchone()
            
            if cached:
                return {
                    'state_fips': cached[0],
                    'county_fips': cached[1], 
                    'tract_geoid': cached[2],
                    'block_group_geoid': cached[3]
                }
        
        # Use Census Geocoder API
        result = self._geocode_point(lat, lon)
        
        # Cache the result
        if cache_result and any(result.values()):
            self.db.conn.execute("""
                INSERT OR REPLACE INTO point_geography_cache 
                (lat, lon, state_fips, county_fips, tract_geoid, block_group_geoid)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [lat, lon, result['state_fips'], result['county_fips'], 
                  result['tract_geoid'], result['block_group_geoid']])
        
        return result
    
    def _geocode_point(self, lat: float, lon: float) -> Dict[str, Optional[str]]:
        """Geocode a point using Census Geocoder API."""
        url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
        params = {
            "x": lon,
            "y": lat,
            "benchmark": "Public_AR_Current",
            "vintage": "Current_Current",
            "format": "json"
        }
        
        try:
            rate_limiter.wait_if_needed("census")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            geographies = data.get("result", {}).get("geographies", {})
            
            result = {
                'state_fips': None,
                'county_fips': None,
                'tract_geoid': None,
                'block_group_geoid': None
            }
            
            # Extract state and county
            counties = geographies.get("Counties", [])
            if counties:
                county = counties[0]
                result['state_fips'] = county.get("STATE")
                result['county_fips'] = county.get("COUNTY")
            
            # Extract tract
            tracts = geographies.get("Census Tracts", [])
            if tracts:
                tract = tracts[0]
                result['tract_geoid'] = tract.get("GEOID")
            
            # Extract block group
            block_groups = geographies.get("Census Block Groups", [])
            if block_groups:
                bg = block_groups[0]
                result['block_group_geoid'] = bg.get("GEOID")
            
            return result
            
        except Exception as e:
            logger.error(f"Geocoding failed for point ({lat}, {lon}): {e}")
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
        Get counties for POIs with optional neighbors (optimized batch processing).
        
        Args:
            pois: List of POI dictionaries with 'lat' and 'lon' keys
            include_neighbors: Whether to include neighboring counties
            neighbor_distance: How many neighbor levels to include (1=direct, 2=neighbors of neighbors)
            
        Returns:
            List of (state_fips, county_fips) tuples
        """
        counties_set = set()
        
        # Process POIs in batch
        for poi in get_progress_bar(pois, desc="Processing POIs", unit="POI"):
            lat = poi.get('lat')
            lon = poi.get('lon')
            
            if lat is None or lon is None:
                logger.warning(f"POI missing coordinates: {poi.get('id', 'unknown')}")
                continue
            
            # Get geography for this POI
            geography = self.get_geography_from_point(lat, lon)
            
            if geography['state_fips'] and geography['county_fips']:
                counties_set.add((geography['state_fips'], geography['county_fips']))
                
                # Add neighboring counties if requested
                if include_neighbors:
                    neighbors = self._get_county_neighbors_recursive(
                        geography['state_fips'], 
                        geography['county_fips'],
                        neighbor_distance
                    )
                    counties_set.update(neighbors)
        
        return list(counties_set)
    
    def _get_county_neighbors_recursive(
        self, 
        state_fips: str, 
        county_fips: str, 
        distance: int,
        visited: Optional[Set] = None
    ) -> Set[Tuple[str, str]]:
        """Get neighbors recursively up to specified distance."""
        if visited is None:
            visited = set()
        
        if distance <= 0 or (state_fips, county_fips) in visited:
            return set()
        
        visited.add((state_fips, county_fips))
        neighbors = set()
        
        # Get direct neighbors
        direct_neighbors = self.get_neighboring_counties(state_fips, county_fips)
        neighbors.update(direct_neighbors)
        
        # Get neighbors of neighbors if distance > 1
        if distance > 1:
            for neighbor_state, neighbor_county in direct_neighbors:
                if (neighbor_state, neighbor_county) not in visited:
                    recursive_neighbors = self._get_county_neighbors_recursive(
                        neighbor_state, neighbor_county, distance - 1, visited
                    )
                    neighbors.update(recursive_neighbors)
        
        return neighbors
    
    def get_neighbor_statistics(self) -> Dict[str, Any]:
        """Get statistics about neighbor relationships in the database."""
        stats = {}
        
        # State neighbor stats
        state_count = self.db.conn.execute("SELECT COUNT(*) FROM state_neighbors").fetchone()[0]
        stats['state_neighbors'] = state_count
        
        # County neighbor stats
        county_count = self.db.conn.execute("SELECT COUNT(*) FROM county_neighbors").fetchone()[0]
        stats['county_neighbors'] = county_count
        
        # Cross-state county neighbors
        cross_state_count = self.db.conn.execute("""
            SELECT COUNT(*) FROM county_neighbors 
            WHERE state_fips != neighbor_state_fips
        """).fetchone()[0]
        stats['cross_state_county_neighbors'] = cross_state_count
        
        # Point cache stats
        cache_count = self.db.conn.execute("SELECT COUNT(*) FROM point_geography_cache").fetchone()[0]
        stats['cached_points'] = cache_count
        
        # States with county data
        states_with_counties = self.db.conn.execute("""
            SELECT COUNT(DISTINCT state_fips) FROM county_neighbors
        """).fetchone()[0]
        stats['states_with_county_data'] = states_with_counties
        
        return stats


# Convenience functions for backward compatibility and easy access

def get_neighbor_manager(db: Optional[CensusDatabase] = None) -> NeighborManager:
    """Get a NeighborManager instance."""
    return NeighborManager(db)

def initialize_all_neighbors(force_refresh: bool = False) -> Dict[str, int]:
    """Initialize all neighbor relationships."""
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
    """Get neighboring states (fast lookup)."""
    manager = get_neighbor_manager()
    
    # Ensure state neighbors are initialized
    count = manager.db.conn.execute("SELECT COUNT(*) FROM state_neighbors").fetchone()[0]
    if count == 0:
        manager.initialize_state_neighbors()
    
    return manager.get_neighboring_states(state_fips)

def get_neighboring_counties(state_fips: str, county_fips: str, include_cross_state: bool = True) -> List[Tuple[str, str]]:
    """Get neighboring counties (fast lookup)."""
    manager = get_neighbor_manager()
    
    # Check if county neighbors are initialized
    count = manager.db.conn.execute("SELECT COUNT(*) FROM county_neighbors").fetchone()[0]
    if count == 0:
        logger.warning("County neighbors not initialized. Run initialize_all_neighbors() first.")
    
    return manager.get_neighboring_counties(state_fips, county_fips, include_cross_state)

def get_geography_from_point(lat: float, lon: float) -> Dict[str, Optional[str]]:
    """Get geographic identifiers for a point (fast lookup with caching)."""
    manager = get_neighbor_manager()
    return manager.get_geography_from_point(lat, lon)

def get_counties_from_pois(pois: List[Dict], include_neighbors: bool = True) -> List[Tuple[str, str]]:
    """Get counties for POIs with optional neighbors (optimized)."""
    manager = get_neighbor_manager()
    return manager.get_counties_from_pois(pois, include_neighbors) 