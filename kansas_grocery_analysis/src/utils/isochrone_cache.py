#!/usr/bin/env python3
"""
DuckDB-based Isochrone Cache System using Spatial Extension.

This module provides a high-performance cache for validated isochrones using
DuckDB's spatial capabilities and GeoParquet for efficient storage.

Key Features:
- Spatial indexing with Hilbert curves for fast queries
- GeoParquet integration for cloud-native workflows
- Metadata tracking for cache validation
- Automatic deduplication of similar isochrones
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

import duckdb
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape, mapping
from shapely import wkb, wkt

from .isochrone_validator import IsochroneValidator, ValidationStatus

logger = logging.getLogger(__name__)


class IsochroneCache:
    """DuckDB-based cache for validated isochrones with spatial indexing."""
    
    def __init__(self, cache_path: str = "cache/isochrones.duckdb", 
                 validate: bool = True,
                 validation_config: Optional[Dict] = None):
        """Initialize the isochrone cache.
        
        Args:
            cache_path: Path to the DuckDB database file
            validate: Whether to validate isochrones before caching
            validation_config: Custom validation configuration
        """
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Connect to DuckDB
        self.conn = duckdb.connect(str(self.cache_path))
        
        # Install and load spatial extension
        self._setup_spatial_extension()
        
        # Create tables if they don't exist
        self._create_tables()
        
        # Initialize validator if enabled
        self.validate = validate
        if self.validate:
            self.validator = IsochroneValidator(validation_config)
        
    def _setup_spatial_extension(self):
        """Install and load the DuckDB spatial extension."""
        try:
            self.conn.execute("INSTALL spatial")
            self.conn.execute("LOAD spatial")
            logger.info("DuckDB spatial extension loaded successfully")
        except Exception as e:
            logger.warning(f"Spatial extension setup warning: {e}")
            # Extension might already be installed
            try:
                self.conn.execute("LOAD spatial")
            except Exception as e2:
                logger.error(f"Failed to load spatial extension: {e2}")
                raise
    
    def _create_tables(self):
        """Create the cache tables if they don't exist."""
        # Main isochrone cache table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS isochrone_cache (
                -- Unique identifier
                cache_key VARCHAR PRIMARY KEY,
                
                -- Location information
                origin_lat DOUBLE NOT NULL,
                origin_lon DOUBLE NOT NULL,
                origin_name VARCHAR,
                origin_type VARCHAR,
                
                -- Isochrone parameters
                travel_time_minutes INTEGER NOT NULL,
                travel_mode VARCHAR NOT NULL,
                
                -- Geometry data
                geometry GEOMETRY NOT NULL,
                area_km2 DOUBLE NOT NULL,
                perimeter_km DOUBLE NOT NULL,
                bbox_minx DOUBLE NOT NULL,
                bbox_miny DOUBLE NOT NULL,
                bbox_maxx DOUBLE NOT NULL,
                bbox_maxy DOUBLE NOT NULL,
                
                -- Metadata
                created_at TIMESTAMP NOT NULL,
                last_accessed TIMESTAMP NOT NULL,
                access_count INTEGER DEFAULT 1,
                data_source VARCHAR,
                socialmapper_version VARCHAR,
                
                -- Validation status
                is_validated BOOLEAN DEFAULT TRUE,
                validation_notes VARCHAR,
                validation_score DOUBLE,
                validation_status VARCHAR,
                
                -- Performance metrics
                generation_time_seconds DOUBLE,
                network_nodes INTEGER,
                network_edges INTEGER
            )
        """)
        
        # Create spatial index using Hilbert ordering
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_isochrone_spatial 
            ON isochrone_cache USING RTREE (geometry)
        """)
        
        # Create index for common queries
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_isochrone_lookup 
            ON isochrone_cache (origin_lat, origin_lon, travel_time_minutes, travel_mode)
        """)
        
        # Create aggregated statistics table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_statistics (
                stat_date DATE PRIMARY KEY,
                total_isochrones INTEGER,
                total_hits INTEGER,
                unique_locations INTEGER,
                avg_area_km2 DOUBLE,
                total_size_mb DOUBLE
            )
        """)
        
        logger.info("Cache tables created/verified successfully")
    
    def generate_cache_key(self, lat: float, lon: float, travel_time: int, 
                          travel_mode: str) -> str:
        """Generate a unique cache key for an isochrone.
        
        Args:
            lat: Origin latitude
            lon: Origin longitude
            travel_time: Travel time in minutes
            travel_mode: Mode of travel (walk, bike, drive)
            
        Returns:
            Unique cache key string
        """
        # Round coordinates to 6 decimal places (about 0.1m precision)
        lat_rounded = round(lat, 6)
        lon_rounded = round(lon, 6)
        
        # Create deterministic key
        key_data = f"{lat_rounded}|{lon_rounded}|{travel_time}|{travel_mode}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    def add_isochrone(self, isochrone_data: Dict[str, Any], 
                     geometry: Any, metadata: Optional[Dict] = None,
                     force: bool = False) -> Tuple[bool, Optional[str]]:
        """Add a validated isochrone to the cache.
        
        Args:
            isochrone_data: Dictionary containing isochrone parameters
            geometry: Shapely geometry object or WKT string
            metadata: Optional metadata about the isochrone
            force: Force add even if validation fails (not recommended)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Extract parameters
            lat = isochrone_data['latitude']
            lon = isochrone_data['longitude']
            travel_time = isochrone_data['travel_time_minutes']
            travel_mode = isochrone_data.get('travel_mode', 'drive')
            
            # Generate cache key
            cache_key = self.generate_cache_key(lat, lon, travel_time, travel_mode)
            
            # Check if already exists
            existing = self.conn.execute(
                "SELECT cache_key FROM isochrone_cache WHERE cache_key = ?",
                [cache_key]
            ).fetchone()
            
            if existing:
                # Update access count and timestamp
                self.conn.execute("""
                    UPDATE isochrone_cache 
                    SET last_accessed = CURRENT_TIMESTAMP,
                        access_count = access_count + 1
                    WHERE cache_key = ?
                """, [cache_key])
                return False, "Isochrone already exists in cache"
            
            # Convert geometry to WKT if needed
            if hasattr(geometry, 'wkt'):
                geom_wkt = geometry.wkt
                geom_obj = geometry
            else:
                geom_wkt = str(geometry)
                from shapely import wkt as shapely_wkt
                geom_obj = shapely_wkt.loads(geom_wkt)
            
            # Validate if enabled
            validation_score = 1.0
            validation_status = "not_validated"
            validation_notes = ""
            is_validated = True
            
            if self.validate:
                validation_result = self.validator.validate_isochrone(
                    geometry=geom_obj,
                    travel_time=travel_time,
                    travel_mode=travel_mode,
                    origin=(lat, lon),
                    metadata=metadata
                )
                
                validation_score = validation_result.score
                validation_status = validation_result.status.value
                is_validated = validation_result.is_valid
                
                if validation_result.warnings:
                    validation_notes = "; ".join(validation_result.warnings[:3])
                elif validation_result.checks_failed:
                    validation_notes = "; ".join(validation_result.checks_failed[:3])
                
                # Check if we should reject
                if not is_validated and not force:
                    logger.warning(
                        f"Rejecting invalid isochrone {cache_key}: {validation_notes}"
                    )
                    return False, f"Validation failed: {validation_notes}"
                elif not is_validated and force:
                    logger.warning(
                        f"Force-adding invalid isochrone {cache_key}: {validation_notes}"
                    )
            
            # Calculate geometry properties
            area_km2 = geom_obj.area * 111.32 * 111.32
            perimeter_km = geom_obj.length * 111.32
            bounds = geom_obj.bounds
            
            # Insert into cache
            self.conn.execute("""
                INSERT INTO isochrone_cache (
                    cache_key, origin_lat, origin_lon, origin_name, origin_type,
                    travel_time_minutes, travel_mode,
                    geometry, area_km2, perimeter_km,
                    bbox_minx, bbox_miny, bbox_maxx, bbox_maxy,
                    created_at, last_accessed, data_source, socialmapper_version,
                    is_validated, validation_notes, validation_score, validation_status,
                    generation_time_seconds, network_nodes, network_edges
                ) VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?,
                    ST_GeomFromText(?), ?, ?,
                    ?, ?, ?, ?,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?
                )
            """, [
                cache_key, lat, lon, 
                isochrone_data.get('origin_name', ''), 
                isochrone_data.get('origin_type', ''),
                travel_time, travel_mode,
                geom_wkt, area_km2, perimeter_km,
                bounds[0], bounds[1], bounds[2], bounds[3],
                metadata.get('data_source', 'socialmapper') if metadata else 'socialmapper',
                metadata.get('version', '0.6.1') if metadata else '0.6.1',
                is_validated, validation_notes, validation_score, validation_status,
                metadata.get('generation_time', 0) if metadata else 0,
                metadata.get('network_nodes', 0) if metadata else 0,
                metadata.get('network_edges', 0) if metadata else 0
            ])
            
            logger.info(
                f"Added isochrone to cache: {cache_key} "
                f"(score: {validation_score:.2f}, status: {validation_status})"
            )
            return True, f"Successfully cached with score {validation_score:.2f}"
            
        except Exception as e:
            logger.error(f"Error adding isochrone to cache: {e}")
            return False, f"Error: {str(e)}"
    
    def get_isochrone(self, lat: float, lon: float, travel_time: int,
                     travel_mode: str = 'drive') -> Optional[Dict[str, Any]]:
        """Retrieve an isochrone from the cache.
        
        Args:
            lat: Origin latitude
            lon: Origin longitude
            travel_time: Travel time in minutes
            travel_mode: Mode of travel
            
        Returns:
            Dictionary with isochrone data and geometry, or None if not found
        """
        cache_key = self.generate_cache_key(lat, lon, travel_time, travel_mode)
        
        result = self.conn.execute("""
            SELECT 
                cache_key, origin_lat, origin_lon, origin_name, origin_type,
                travel_time_minutes, travel_mode,
                ST_AsText(geometry) as geometry_wkt,
                area_km2, perimeter_km,
                created_at, access_count,
                is_validated, validation_notes
            FROM isochrone_cache
            WHERE cache_key = ?
        """, [cache_key]).fetchone()
        
        if result:
            # Update access statistics
            self.conn.execute("""
                UPDATE isochrone_cache 
                SET last_accessed = CURRENT_TIMESTAMP,
                    access_count = access_count + 1
                WHERE cache_key = ?
            """, [cache_key])
            
            # Convert to dictionary
            columns = [
                'cache_key', 'origin_lat', 'origin_lon', 'origin_name', 'origin_type',
                'travel_time_minutes', 'travel_mode', 'geometry_wkt',
                'area_km2', 'perimeter_km', 'created_at', 'access_count',
                'is_validated', 'validation_notes'
            ]
            
            return dict(zip(columns, result))
        
        return None
    
    def find_nearby_isochrones(self, lat: float, lon: float, 
                              radius_km: float = 5.0) -> pd.DataFrame:
        """Find all cached isochrones near a location.
        
        Args:
            lat: Center latitude
            lon: Center longitude
            radius_km: Search radius in kilometers
            
        Returns:
            DataFrame with nearby isochrones
        """
        # Convert radius to degrees (rough approximation)
        radius_deg = radius_km / 111.32
        
        result = self.conn.execute("""
            SELECT 
                cache_key, origin_lat, origin_lon, origin_name,
                travel_time_minutes, travel_mode,
                area_km2, created_at, access_count,
                ST_Distance(
                    geometry, 
                    ST_Point(?, ?)
                ) * 111.32 as distance_km
            FROM isochrone_cache
            WHERE ST_Distance(
                geometry,
                ST_Point(?, ?)
            ) <= ?
            ORDER BY distance_km
        """, [lon, lat, lon, lat, radius_deg]).fetchdf()
        
        return result
    
    def export_to_geoparquet(self, output_path: str, 
                            filters: Optional[Dict] = None) -> int:
        """Export cached isochrones to GeoParquet format.
        
        Args:
            output_path: Path for the output GeoParquet file
            filters: Optional filters (e.g., {'travel_mode': 'drive'})
            
        Returns:
            Number of isochrones exported
        """
        # Build query
        query = """
            SELECT 
                cache_key, origin_lat, origin_lon, origin_name, origin_type,
                travel_time_minutes, travel_mode,
                geometry, area_km2, perimeter_km,
                created_at, access_count
            FROM isochrone_cache
            WHERE is_validated = TRUE
        """
        
        # Add filters if provided
        params = []
        if filters:
            for key, value in filters.items():
                query += f" AND {key} = ?"
                params.append(value)
        
        # Order by Hilbert curve for spatial optimization
        query += """
            ORDER BY ST_Hilbert(geometry)
        """
        
        # Execute query and export
        self.conn.execute(f"""
            COPY ({query}) 
            TO '{output_path}'
            WITH (FORMAT 'parquet', CODEC 'zstd')
        """, params)
        
        # Get count
        count_result = self.conn.execute(
            "SELECT COUNT(*) FROM isochrone_cache WHERE is_validated = TRUE"
        ).fetchone()
        
        logger.info(f"Exported {count_result[0]} isochrones to {output_path}")
        return count_result[0]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = self.conn.execute("""
            SELECT 
                COUNT(*) as total_isochrones,
                COUNT(DISTINCT origin_lat || ',' || origin_lon) as unique_locations,
                SUM(access_count) as total_hits,
                AVG(area_km2) as avg_area_km2,
                MIN(created_at) as oldest_entry,
                MAX(created_at) as newest_entry,
                SUM(CASE WHEN travel_mode = 'drive' THEN 1 ELSE 0 END) as drive_count,
                SUM(CASE WHEN travel_mode = 'walk' THEN 1 ELSE 0 END) as walk_count,
                SUM(CASE WHEN travel_mode = 'bike' THEN 1 ELSE 0 END) as bike_count,
                SUM(CASE WHEN is_validated THEN 1 ELSE 0 END) as validated_count,
                AVG(validation_score) as avg_validation_score
            FROM isochrone_cache
        """).fetchone()
        
        columns = [
            'total_isochrones', 'unique_locations', 'total_hits', 'avg_area_km2',
            'oldest_entry', 'newest_entry', 'drive_count', 'walk_count', 'bike_count',
            'validated_count', 'avg_validation_score'
        ]
        
        return dict(zip(columns, stats))
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation statistics summary.
        
        Returns:
            Dictionary with validation statistics
        """
        # Get validation status distribution
        status_dist = self.conn.execute("""
            SELECT 
                validation_status,
                COUNT(*) as count,
                AVG(validation_score) as avg_score
            FROM isochrone_cache
            WHERE validation_status IS NOT NULL
            GROUP BY validation_status
        """).fetchdf()
        
        # Get common validation issues
        issues = self.conn.execute("""
            SELECT 
                validation_notes,
                COUNT(*) as count
            FROM isochrone_cache
            WHERE validation_notes IS NOT NULL AND validation_notes != ''
            GROUP BY validation_notes
            ORDER BY count DESC
            LIMIT 10
        """).fetchdf()
        
        # Get score distribution
        score_dist = self.conn.execute("""
            SELECT 
                CASE 
                    WHEN validation_score <= 0.5 THEN '0.0-0.5'
                    WHEN validation_score <= 0.7 THEN '0.5-0.7'
                    WHEN validation_score <= 0.9 THEN '0.7-0.9'
                    ELSE '0.9-1.0'
                END as score_range,
                COUNT(*) as count
            FROM isochrone_cache
            WHERE validation_score IS NOT NULL
            GROUP BY score_range
            ORDER BY score_range
        """).fetchdf()
        
        return {
            'status_distribution': status_dist.to_dict('records') if not status_dist.empty else [],
            'common_issues': issues.to_dict('records') if not issues.empty else [],
            'score_distribution': score_dist.to_dict('records') if not score_dist.empty else []
        }
    
    def cleanup_old_entries(self, days: int = 90) -> int:
        """Remove old entries that haven't been accessed recently.
        
        Args:
            days: Remove entries not accessed in this many days
            
        Returns:
            Number of entries removed
        """
        result = self.conn.execute("""
            DELETE FROM isochrone_cache
            WHERE last_accessed < CURRENT_TIMESTAMP - INTERVAL ? DAY
            AND access_count < 5
        """, [days])
        
        count = result.fetchone()[0] if result else 0
        logger.info(f"Removed {count} old cache entries")
        return count
    
    def close(self):
        """Close the database connection."""
        self.conn.close()
    
    def __enter__(self):
        """Context manager support."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()


# Example usage and integration with SocialMapper
def cache_socialmapper_results(analysis_result, cache: IsochroneCache):
    """Cache isochrones from a SocialMapper analysis result.
    
    Args:
        analysis_result: SocialMapper AnalysisResult object
        cache: IsochroneCache instance
    """
    # Extract isochrones from the analysis result
    for file_type, file_path in analysis_result.files_generated.items():
        if 'isochrone' in file_type.lower() and file_path.suffix == '.geoparquet':
            # Load the isochrones
            isochrones_gdf = gpd.read_parquet(file_path)
            
            # Cache each isochrone
            for idx, row in isochrones_gdf.iterrows():
                isochrone_data = {
                    'latitude': row.get('poi_lat', row.geometry.centroid.y),
                    'longitude': row.get('poi_lon', row.geometry.centroid.x),
                    'travel_time_minutes': row.get('travel_time_minutes', 30),
                    'travel_mode': row.get('travel_mode', 'drive'),
                    'origin_name': row.get('poi_name', ''),
                    'origin_type': row.get('poi_type', '')
                }
                
                metadata = {
                    'data_source': 'socialmapper',
                    'version': '0.6.1',
                    'generation_time': 0,  # Would need to track this
                }
                
                try:
                    cache.add_isochrone(isochrone_data, row.geometry, metadata)
                except Exception as e:
                    logger.warning(f"Failed to cache isochrone: {e}")


if __name__ == "__main__":
    # Example usage
    cache = IsochroneCache()
    
    # Get cache statistics
    stats = cache.get_statistics()
    print("Cache Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Example: Check for cached isochrone
    result = cache.get_isochrone(
        lat=39.3343285,
        lon=-101.7285206,
        travel_time=30,
        travel_mode='drive'
    )
    
    if result:
        print(f"\nFound cached isochrone: {result['cache_key']}")
        print(f"Area: {result['area_km2']:.1f} km²")
    else:
        print("\nNo cached isochrone found")
    
    cache.close()