#!/usr/bin/env python3
"""
Modern census module for SocialMapper using DuckDB for efficient data management.

This module replaces the old census and blockgroups modules, providing:
- Census boundary management (block groups, tracts, counties, states)
- Census data retrieval and caching
- Efficient spatial queries using DuckDB spatial extension
- Views for data analysis and mapping
- Backward compatibility with existing APIs
"""

import os
import logging
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
import warnings

import duckdb
import pandas as pd
import geopandas as gpd
import requests
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely import wkt

# Import existing utilities
from socialmapper.progress import get_progress_bar
from socialmapper.util import (
    normalize_census_variable,
    get_census_api_key,
    get_readable_census_variables,
    CENSUS_VARIABLE_MAPPING,
    rate_limiter
)
from socialmapper.states import (
    normalize_state,
    normalize_state_list,
    StateFormat,
    state_fips_to_name
)

# Configure logging
logger = logging.getLogger(__name__)

# Default database path
DEFAULT_DB_PATH = Path.home() / ".socialmapper" / "census.duckdb"

class CensusDatabase:
    """
    DuckDB-based census data management system with optional boundary caching.
    
    This class provides a unified interface for:
    - Managing census data with fast analytical queries
    - Streaming boundary data (block groups, tracts, counties) as needed
    - Creating views for analysis without storing large geometries
    - Optional boundary caching for frequently used areas
    """
    
    def __init__(self, db_path: Optional[Union[str, Path]] = None, cache_boundaries: bool = False):
        """
        Initialize the census database.
        
        Args:
            db_path: Path to the DuckDB database file. If None, uses default location.
            cache_boundaries: Whether to cache boundary geometries in the database.
                             If False, boundaries are streamed as needed (recommended).
        """
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_boundaries = cache_boundaries
        
        # Initialize connection
        self.conn = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the DuckDB database with spatial extension and required tables."""
        try:
            self.conn = duckdb.connect(str(self.db_path))
            
            # Install and load spatial extension
            self.conn.execute("INSTALL spatial;")
            self.conn.execute("LOAD spatial;")
            
            # Create schema for census data (optimized for analytics)
            self._create_schema()
            
            cache_mode = "with boundary caching" if self.cache_boundaries else "streaming boundaries"
            get_progress_bar().write(f"Initialized census database at {self.db_path} ({cache_mode})")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _create_schema(self):
        """Create the database schema optimized for census data analytics."""
        
        # Geographic reference tables using Census schema (lightweight, no geometries)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS geographic_units (
                GEOID VARCHAR(12) PRIMARY KEY,
                unit_type VARCHAR(20) NOT NULL, -- 'state', 'county', 'tract', 'block_group'
                STATEFP VARCHAR(2) NOT NULL,
                COUNTYFP VARCHAR(3),
                TRACTCE VARCHAR(6),
                BLKGRPCE VARCHAR(1),
                NAME VARCHAR(200),
                ALAND BIGINT,
                AWATER BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Census data table (the main focus for DuckDB analytics)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS census_data (
                GEOID VARCHAR(12) NOT NULL,
                variable_code VARCHAR(20) NOT NULL,
                variable_name VARCHAR(100),
                value DOUBLE,
                margin_of_error DOUBLE,
                year INTEGER NOT NULL,
                dataset VARCHAR(20) NOT NULL DEFAULT 'acs5',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(GEOID, variable_code, year, dataset)
            );
        """)
        
        # Optional boundary cache table (only created if caching is enabled)
        if self.cache_boundaries:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS boundary_cache (
                    GEOID VARCHAR(12) PRIMARY KEY,
                    geometry GEOMETRY NOT NULL,
                    cache_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        
        # Metadata table for tracking data sources and updates
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes optimized for analytics
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_geographic_units_type ON geographic_units(unit_type);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_geographic_units_state ON geographic_units(STATEFP);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_census_data_geoid ON census_data(GEOID);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_census_data_variable ON census_data(variable_code);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_census_data_year ON census_data(year);")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_census_data_composite ON census_data(GEOID, variable_code, year);")
    
    def get_or_stream_block_groups(
        self, 
        state_fips: List[str], 
        force_refresh: bool = False,
        api_key: Optional[str] = None
    ) -> gpd.GeoDataFrame:
        """
        Get block groups for specified states, streaming from APIs as needed.
        
        Args:
            state_fips: List of state FIPS codes
            force_refresh: Whether to force refresh from API
            api_key: Census API key
            
        Returns:
            GeoDataFrame with block groups (streamed, not cached by default)
        """
        # Normalize state FIPS codes
        normalized_fips = []
        for state in state_fips:
            fips = normalize_state(state, to_format=StateFormat.FIPS)
            if fips:
                normalized_fips.append(fips)
            else:
                logger.warning(f"Could not normalize state identifier: {state}")
        
        if not normalized_fips:
            raise ValueError("No valid state identifiers provided")
        
        # Check if we have geographic unit metadata (lightweight check)
        cached_states = []
        missing_states = []
        
        if not force_refresh:
            for fips in normalized_fips:
                count = self.conn.execute(
                    "SELECT COUNT(*) FROM geographic_units WHERE STATEFP = ? AND unit_type = 'block_group'", 
                    [fips]
                ).fetchone()[0]
                
                if count > 0:
                    cached_states.append(fips)
                    get_progress_bar().write(f"Found metadata for {count} block groups in state {fips}")
                else:
                    missing_states.append(fips)
        else:
            missing_states = normalized_fips
        
        # Stream boundaries for all requested states (cached or not)
        all_gdfs = []
        
        for fips in normalized_fips:
            get_progress_bar().write(f"Streaming block groups for state {fips}")
            
            # Try to get from boundary cache first (if enabled)
            if self.cache_boundaries and fips in cached_states:
                cached_gdf = self._get_cached_boundaries(fips, 'block_group')
                if cached_gdf is not None and not cached_gdf.empty:
                    all_gdfs.append(cached_gdf)
                    continue
            
            # Stream from API
            gdf = self._stream_block_groups_from_api(fips, api_key)
            if gdf is not None and not gdf.empty:
                all_gdfs.append(gdf)
                
                # Store metadata (lightweight) and optionally cache boundaries
                self._store_geographic_metadata(gdf, 'block_group')
                if self.cache_boundaries:
                    self._cache_boundaries(gdf)
        
        if not all_gdfs:
            raise ValueError(f"No block groups found for states: {normalized_fips}")
        
        # Combine all state data
        combined_gdf = pd.concat(all_gdfs, ignore_index=True)
        
        # Add computed columns for backward compatibility with old API
        if 'STATEFP' in combined_gdf.columns:
            combined_gdf['STATE'] = combined_gdf['STATEFP']
        if 'COUNTYFP' in combined_gdf.columns:
            combined_gdf['COUNTY'] = combined_gdf['COUNTYFP']
        if 'TRACTCE' in combined_gdf.columns:
            combined_gdf['TRACT'] = combined_gdf['TRACTCE']
        if 'BLKGRPCE' in combined_gdf.columns:
            combined_gdf['BLKGRP'] = combined_gdf['BLKGRPCE']
        
        return combined_gdf
    
    def _stream_block_groups_from_api(self, state_fips: str, api_key: Optional[str] = None) -> Optional[gpd.GeoDataFrame]:
        """
        Stream block groups from Census API without persistent storage.
        
        Args:
            state_fips: State FIPS code
            api_key: Census API key
            
        Returns:
            GeoDataFrame with block groups or None if failed
        """
        if not api_key:
            api_key = get_census_api_key()
            if not api_key:
                raise ValueError("Census API key required for streaming boundary data")
        
        state_name = state_fips_to_name(state_fips) or state_fips
        get_progress_bar().write(f"Streaming block groups for {state_name} ({state_fips})")
        
        # Try multiple approaches in order of preference
        gdf = None
        
        # Method 1: Census Cartographic Boundary Files (preferred)
        try:
            gdf = self._fetch_from_cartographic_files(state_fips)
            if gdf is not None and not gdf.empty:
                get_progress_bar().write(f"Streamed {len(gdf)} block groups from cartographic files")
                return gdf
        except Exception as e:
            get_progress_bar().write(f"Cartographic files failed: {e}, trying TIGER API")
        
        # Method 2: TIGER/Web API with GeoJSON format (fallback)
        try:
            gdf = self._fetch_from_tiger_geojson(state_fips)
            if gdf is not None and not gdf.empty:
                get_progress_bar().write(f"Streamed {len(gdf)} block groups from TIGER GeoJSON API")
                return gdf
        except Exception as e:
            get_progress_bar().write(f"TIGER GeoJSON API failed: {e}, trying ESRI JSON")
        
        # Method 3: TIGER/Web API with ESRI JSON format (last resort)
        try:
            gdf = self._fetch_from_tiger_esri_json(state_fips)
            if gdf is not None and not gdf.empty:
                get_progress_bar().write(f"Streamed {len(gdf)} block groups from TIGER ESRI JSON API")
                return gdf
        except Exception as e:
            logger.error(f"All streaming methods failed for state {state_fips}: {e}")
        
        return None
    
    def _fetch_from_cartographic_files(self, state_fips: str) -> Optional[gpd.GeoDataFrame]:
        """
        Fetch block groups from Census Cartographic Boundary Files.
        
        Args:
            state_fips: State FIPS code
            
        Returns:
            GeoDataFrame with block groups or None if failed
        """
        # Use Census Cartographic Boundary Files API
        # For block groups, we'll use the 2021 cartographic boundary files
        url = f"https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_{state_fips}_bg_500k.zip"
        
        rate_limiter.wait_if_needed("census")
        
        # Download the ZIP file
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
        except requests.exceptions.SSLError:
            # Fallback with SSL verification disabled only if needed
            import warnings
            warnings.filterwarnings('ignore', message='Unverified HTTPS request')
            response = requests.get(url, timeout=60, verify=False)
            response.raise_for_status()
            warnings.resetwarnings()
        
        # Save to temporary file and extract
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
            tmp_zip.write(response.content)
            tmp_zip_path = tmp_zip.name
        
        try:
            # Extract and read the shapefile
            with tempfile.TemporaryDirectory() as tmp_dir:
                with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmp_dir)
                
                # Find the .shp file
                shp_files = list(Path(tmp_dir).glob("*.shp"))
                if not shp_files:
                    return None
                
                # Load as GeoDataFrame
                gdf = gpd.read_file(shp_files[0])
                
                # Ensure GEOID is properly formatted if missing
                if gdf is not None and not gdf.empty and 'GEOID' not in gdf.columns:
                    if all(col in gdf.columns for col in ['STATEFP', 'COUNTYFP', 'TRACTCE', 'BLKGRPCE']):
                        gdf['GEOID'] = (
                            gdf['STATEFP'].astype(str).str.zfill(2) +
                            gdf['COUNTYFP'].astype(str).str.zfill(3) +
                            gdf['TRACTCE'].astype(str).str.zfill(6) +
                            gdf['BLKGRPCE'].astype(str)
                        )
                
                return gdf
        finally:
            # Clean up temporary ZIP file
            Path(tmp_zip_path).unlink()
    
    def _fetch_from_tiger_geojson(self, state_fips: str) -> Optional[gpd.GeoDataFrame]:
        """
        Fetch block groups from TIGER/Web API using GeoJSON format.
        
        Args:
            state_fips: State FIPS code
            
        Returns:
            GeoDataFrame with block groups or None if failed
        """
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/1/query"
        
        params = {
            'where': f"STATE='{state_fips}'",
            'outFields': 'STATE,COUNTY,TRACT,BLKGRP,GEOID,ALAND,AWATER',
            'returnGeometry': 'true',
            'f': 'geojson'  # Request GeoJSON format
        }
        
        rate_limiter.wait_if_needed("census")
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        if 'features' not in data or not data['features']:
            return None
        
        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(data['features'], crs="EPSG:4326")
        
        # Standardize column names to match shapefile format
        column_mapping = {
            'STATE': 'STATEFP',
            'COUNTY': 'COUNTYFP', 
            'TRACT': 'TRACTCE',
            'BLKGRP': 'BLKGRPCE'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in gdf.columns and new_col not in gdf.columns:
                gdf[new_col] = gdf[old_col]
        
        # Ensure GEOID is properly formatted
        if 'GEOID' not in gdf.columns:
            gdf['GEOID'] = (
                gdf['STATEFP'].astype(str).str.zfill(2) +
                gdf['COUNTYFP'].astype(str).str.zfill(3) +
                gdf['TRACTCE'].astype(str).str.zfill(6) +
                gdf['BLKGRPCE'].astype(str)
            )
        
        return gdf
    
    def _fetch_from_tiger_esri_json(self, state_fips: str) -> Optional[gpd.GeoDataFrame]:
        """
        Fetch block groups from TIGER/Web API using ESRI JSON format and convert geometries.
        
        Args:
            state_fips: State FIPS code
            
        Returns:
            GeoDataFrame with block groups or None if failed
        """
        url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/1/query"
        
        params = {
            'where': f"STATE='{state_fips}'",
            'outFields': 'STATE,COUNTY,TRACT,BLKGRP,GEOID,ALAND,AWATER',
            'returnGeometry': 'true',
            'f': 'json'  # Request ESRI JSON format
        }
        
        rate_limiter.wait_if_needed("census")
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        if 'features' not in data or not data['features']:
            return None
        
        # Convert ESRI JSON to GeoDataFrame
        gdf = self._convert_esri_json_to_geodataframe(data)
        
        # Standardize column names to match shapefile format
        column_mapping = {
            'STATE': 'STATEFP',
            'COUNTY': 'COUNTYFP', 
            'TRACT': 'TRACTCE',
            'BLKGRP': 'BLKGRPCE'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in gdf.columns and new_col not in gdf.columns:
                gdf[new_col] = gdf[old_col]
        
        # Ensure GEOID is properly formatted
        if 'GEOID' not in gdf.columns:
            gdf['GEOID'] = (
                gdf['STATEFP'].astype(str).str.zfill(2) +
                gdf['COUNTYFP'].astype(str).str.zfill(3) +
                gdf['TRACTCE'].astype(str).str.zfill(6) +
                gdf['BLKGRPCE'].astype(str)
            )
        
        return gdf
    
    def _convert_esri_json_to_geodataframe(self, esri_data: Dict) -> gpd.GeoDataFrame:
        """
        Convert ESRI JSON format to GeoDataFrame.
        
        Args:
            esri_data: ESRI JSON response data
            
        Returns:
            GeoDataFrame with converted geometries
        """
        from shapely.geometry import Polygon, MultiPolygon
        
        features = []
        
        for feature in esri_data['features']:
            # Extract attributes
            attributes = feature.get('attributes', {})
            
            # Convert ESRI geometry to Shapely geometry
            esri_geom = feature.get('geometry', {})
            shapely_geom = self._convert_esri_geometry_to_shapely(esri_geom)
            
            if shapely_geom is not None:
                # Create feature dictionary
                feature_dict = attributes.copy()
                feature_dict['geometry'] = shapely_geom
                features.append(feature_dict)
        
        if not features:
            return gpd.GeoDataFrame()
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")
        return gdf
    
    def _convert_esri_geometry_to_shapely(self, esri_geom: Dict) -> Optional[Union[Polygon, MultiPolygon]]:
        """
        Convert ESRI geometry to Shapely geometry.
        
        Args:
            esri_geom: ESRI geometry dictionary
            
        Returns:
            Shapely geometry or None if conversion fails
        """
        from shapely.geometry import Polygon, MultiPolygon, LinearRing, Point
        
        try:
            if 'rings' in esri_geom:
                rings = esri_geom['rings']
                
                if not rings:
                    return None
                
                # Separate exterior and interior rings
                exterior_rings = []
                interior_rings = []
                
                for ring in rings:
                    if len(ring) < 4:  # Need at least 4 points for a valid ring
                        continue
                    
                    # Check if ring is clockwise (exterior) or counterclockwise (interior)
                    # ESRI uses clockwise for exterior rings
                    signed_area = self._calculate_signed_area(ring)
                    
                    if signed_area > 0:  # Clockwise = exterior
                        exterior_rings.append(ring)
                    else:  # Counterclockwise = interior
                        interior_rings.append(ring)
                
                if not exterior_rings:
                    return None
                
                polygons = []
                
                # Create polygons from exterior rings
                for ext_ring in exterior_rings:
                    try:
                        # Find interior rings that belong to this exterior ring
                        holes = []
                        ext_polygon = Polygon(ext_ring)
                        
                        for int_ring in interior_rings:
                            int_point = Point(int_ring[0])
                            if ext_polygon.contains(int_point):
                                holes.append(int_ring)
                        
                        # Create polygon with holes
                        if holes:
                            polygon = Polygon(ext_ring, holes)
                        else:
                            polygon = Polygon(ext_ring)
                        
                        if polygon.is_valid:
                            polygons.append(polygon)
                        else:
                            # Try to fix invalid geometry
                            fixed = polygon.buffer(0)
                            if fixed.is_valid:
                                polygons.append(fixed)
                    
                    except Exception as e:
                        logger.warning(f"Failed to create polygon from ring: {e}")
                        continue
                
                if not polygons:
                    return None
                elif len(polygons) == 1:
                    return polygons[0]
                else:
                    return MultiPolygon(polygons)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to convert ESRI geometry: {e}")
            return None
    
    def _calculate_signed_area(self, ring: List[List[float]]) -> float:
        """
        Calculate the signed area of a ring to determine orientation.
        
        Args:
            ring: List of [x, y] coordinate pairs
            
        Returns:
            Signed area (positive = clockwise, negative = counterclockwise)
        """
        if len(ring) < 3:
            return 0
        
        area = 0
        for i in range(len(ring)):
            j = (i + 1) % len(ring)
            area += ring[i][0] * ring[j][1]
            area -= ring[j][0] * ring[i][1]
        
        return area / 2
    
    def _store_geographic_metadata(self, gdf: gpd.GeoDataFrame, unit_type: str):
        """
        Store lightweight geographic metadata without geometries using Census schema.
        
        Args:
            gdf: GeoDataFrame with geographic units
            unit_type: Type of geographic unit ('block_group', 'tract', etc.)
        """
        records = []
        for _, row in gdf.iterrows():
            # Use Census schema directly - no transformation needed
            geoid = str(row.get('GEOID', ''))
            statefp = str(row.get('STATEFP', ''))
            countyfp = str(row.get('COUNTYFP', '')) if 'COUNTYFP' in row else None
            tractce = str(row.get('TRACTCE', '')) if 'TRACTCE' in row else None
            blkgrpce = str(row.get('BLKGRPCE', '')) if 'BLKGRPCE' in row else None
            
            # Create name if not provided
            name = row.get('NAME')
            if not name and unit_type == 'block_group':
                name = f"Block Group {blkgrpce}, Census Tract {tractce}, {state_fips_to_name(statefp) or statefp}"
            elif not name:
                name = f"{unit_type.title()} {geoid}"
            
            record = {
                'GEOID': geoid,
                'unit_type': unit_type,
                'STATEFP': statefp,
                'COUNTYFP': countyfp,
                'TRACTCE': tractce,
                'BLKGRPCE': blkgrpce,
                'NAME': name,
                'ALAND': row.get('ALAND'),
                'AWATER': row.get('AWATER')
            }
            records.append(record)
        
        # Insert records (replace if exists)
        if records:
            # Delete existing records for this combination
            statefp = records[0]['STATEFP']
            self.conn.execute(
                "DELETE FROM geographic_units WHERE STATEFP = ? AND unit_type = ?", 
                [statefp, unit_type]
            )
            
            # Insert new records
            self.conn.executemany("""
                INSERT INTO geographic_units 
                (GEOID, unit_type, STATEFP, COUNTYFP, TRACTCE, BLKGRPCE, NAME, ALAND, AWATER)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (r['GEOID'], r['unit_type'], r['STATEFP'], r['COUNTYFP'], 
                 r['TRACTCE'], r['BLKGRPCE'], r['NAME'], r['ALAND'], r['AWATER'])
                for r in records
            ])
    
    def _get_cached_boundaries(self, state_fips: str, unit_type: str) -> Optional[gpd.GeoDataFrame]:
        """
        Get cached boundaries if boundary caching is enabled.
        
        Args:
            state_fips: State FIPS code
            unit_type: Type of geographic unit
            
        Returns:
            GeoDataFrame with cached boundaries or None
        """
        if not self.cache_boundaries:
            return None
        
        query = """
            SELECT 
                gu.GEOID,
                gu.STATEFP,
                gu.COUNTYFP,
                gu.TRACTCE,
                gu.BLKGRPCE,
                gu.NAME,
                ST_AsText(bc.geometry) as geometry_wkt,
                gu.ALAND,
                gu.AWATER
            FROM geographic_units gu
            JOIN boundary_cache bc ON gu.GEOID = bc.GEOID
            WHERE gu.STATEFP = ? AND gu.unit_type = ?
        """
        
        df = self.conn.execute(query, [state_fips, unit_type]).df()
        
        if df.empty:
            return None
        
        # Convert to GeoDataFrame
        df['geometry'] = df['geometry_wkt'].apply(wkt.loads)
        gdf = gpd.GeoDataFrame(df.drop('geometry_wkt', axis=1), geometry='geometry', crs='EPSG:4326')
        
        return gdf
    
    def _cache_boundaries(self, gdf: gpd.GeoDataFrame):
        """
        Cache boundaries in the database if caching is enabled.
        
        Args:
            gdf: GeoDataFrame with boundaries to cache
        """
        if not self.cache_boundaries:
            return
        
        records = []
        for _, row in gdf.iterrows():
            if row.geometry is None or not hasattr(row.geometry, 'wkt'):
                continue
                
            try:
                geom_wkt = row.geometry.wkt
                if geom_wkt and isinstance(geom_wkt, str):
                    records.append((row['GEOID'], geom_wkt))
            except Exception as e:
                logger.warning(f"Failed to cache geometry for GEOID {row.get('GEOID', 'unknown')}: {e}")
                continue
        
        if records:
            # Insert or replace cached boundaries
            self.conn.executemany("""
                INSERT OR REPLACE INTO boundary_cache (GEOID, geometry)
                VALUES (?, ST_GeomFromText(?))
            """, records)
    
    def find_intersecting_block_groups(
        self,
        geometry: Union[Polygon, gpd.GeoDataFrame],
        state_fips: Optional[List[str]] = None,
        selection_mode: str = "intersect"
    ) -> gpd.GeoDataFrame:
        """
        Find block groups that intersect with the given geometry by streaming boundaries.
        
        Args:
            geometry: Polygon or GeoDataFrame to intersect with
            state_fips: Optional list of states to search in (for performance)
            selection_mode: 'intersect', 'contain', or 'clip'
            
        Returns:
            GeoDataFrame with intersecting block groups
        """
        # Handle different input types
        if isinstance(geometry, gpd.GeoDataFrame):
            union_geom = geometry.geometry.unary_union
            search_bounds = geometry.total_bounds
        elif hasattr(geometry, 'wkt'):
            union_geom = geometry
            search_bounds = geometry.bounds
        else:
            raise ValueError("Geometry must be a Polygon or GeoDataFrame")
        
        # Determine states to search if not provided
        if state_fips is None:
            # Use a broad search - in practice, you might want to implement
            # a more sophisticated method to determine relevant states
            from socialmapper.states import get_all_states
            state_fips = get_all_states(StateFormat.FIPS)
            get_progress_bar().write("No states specified, searching all states (this may be slow)")
        
        # Stream block groups for relevant states
        all_block_groups = self.get_or_stream_block_groups(state_fips)
        
        # Perform spatial intersection in memory (fast with GeoPandas)
        if selection_mode == "contain":
            # Find block groups completely within the geometry
            intersecting = all_block_groups[all_block_groups.geometry.within(union_geom)]
        else:  # intersect or clip
            intersecting = all_block_groups[all_block_groups.geometry.intersects(union_geom)]
        
        # Handle clipping if requested
        if selection_mode == "clip":
            clipped_geoms = []
            for geom in intersecting.geometry:
                try:
                    clipped = geom.intersection(union_geom)
                    clipped_geoms.append(clipped)
                except Exception:
                    clipped_geoms.append(geom)
            intersecting = intersecting.copy()
            intersecting.geometry = clipped_geoms
        
        return intersecting
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Global database instance
_census_db = None

def get_census_database(
    db_path: Optional[Union[str, Path]] = None, 
    cache_boundaries: bool = False
) -> CensusDatabase:
    """
    Get the global census database instance.
    
    Args:
        db_path: Optional path to database file
        cache_boundaries: Whether to cache boundary geometries (default: False for streaming)
        
    Returns:
        CensusDatabase instance
    """
    global _census_db
    
    # If a specific path is provided, always create a new instance for that path
    if db_path is not None:
        return CensusDatabase(db_path, cache_boundaries)
    
    # For the default path, use the global instance
    if _census_db is None or _census_db.conn is None:
        _census_db = CensusDatabase(cache_boundaries=cache_boundaries)
    
    return _census_db


# Import and expose submodules
from .data import (
    CensusDataManager
)

from .utils import (
    optimize_database,
    export_database_info,
    create_summary_views,
    backup_database,
    restore_database,
    clear_cache
)

from .neighbors import (
    NeighborDatabase,
    NeighborManager,
    get_neighbor_manager,
    initialize_all_neighbors,
    get_neighboring_states,
    get_neighboring_counties,
    get_geography_from_point,
    get_counties_from_pois,
    DEFAULT_NEIGHBOR_DB_PATH
)

# Note: Development utilities (migrate.py, neighbor_loader.py, init_neighbors.py, export_neighbors.py) 
# have been removed as they are no longer needed in production.

# Note: Backward compatibility functions have been removed.
# Users should migrate to the new optimized APIs.


# Public API
__all__ = [
    # Core classes
    'CensusDatabase',
    'CensusDataManager',
    'NeighborDatabase',
    'NeighborManager',
    'get_census_database',
    'get_neighbor_manager',
    
    # Neighbor functions (replaces states and counties modules)
    'initialize_all_neighbors',
    'get_neighboring_states',
    'get_neighboring_counties',
    'get_geography_from_point',
    'get_counties_from_pois',
    
    # Note: Distributed neighbor functions removed (no longer needed)
    
    # Note: Backward compatibility functions removed
    
    # Utility functions
    'optimize_database',
    'export_database_info',
    'create_summary_views',
    'backup_database',
    'restore_database',
    'clear_cache',
    
    # Constants
    'DEFAULT_DB_PATH',
    'DEFAULT_NEIGHBOR_DB_PATH'
] 