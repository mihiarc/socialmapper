#!/usr/bin/env python3
"""
Cached analysis wrapper that uses DuckDB isochrone cache.

This module provides a wrapper around the standard analysis that:
1. Checks the cache for existing isochrones
2. Only generates new isochrones for uncached locations
3. Combines cached and new results
4. Updates the cache with new validated isochrones
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import geopandas as gpd
from datetime import datetime

from .isochrone_cache import IsochroneCache
from socialmapper import SocialMapperBuilder, SocialMapperClient

logger = logging.getLogger(__name__)


class CachedAnalysisRunner:
    """Run SocialMapper analysis with DuckDB isochrone caching."""
    
    def __init__(self, cache_path: str = "cache/isochrones.duckdb"):
        """Initialize the cached analysis runner.
        
        Args:
            cache_path: Path to the DuckDB cache database
        """
        self.cache = IsochroneCache(cache_path)
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'time_saved_seconds': 0
        }
    
    def analyze_with_cache(self, poi_file: str, travel_time: int = 30,
                          travel_mode: str = 'drive', 
                          output_dir: Optional[Path] = None) -> Dict:
        """Run analysis using cached isochrones where available.
        
        Args:
            poi_file: Path to CSV file with POI locations
            travel_time: Travel time in minutes
            travel_mode: Mode of travel (walk, bike, drive)
            output_dir: Output directory for results
            
        Returns:
            Dictionary with analysis results and cache statistics
        """
        start_time = datetime.now()
        
        # Load POI data
        poi_df = pd.read_csv(poi_file)
        total_pois = len(poi_df)
        
        logger.info(f"Analyzing {total_pois} POIs with {travel_time}-minute {travel_mode} isochrones")
        
        # Check cache for each POI
        cached_isochrones = []
        uncached_pois = []
        
        for idx, poi in poi_df.iterrows():
            lat = poi.get('latitude', poi.get('lat'))
            lon = poi.get('longitude', poi.get('lon', poi.get('lng')))
            
            # Check cache
            cached = self.cache.get_isochrone(lat, lon, travel_time, travel_mode)
            
            if cached:
                self.stats['cache_hits'] += 1
                cached_isochrones.append({
                    'poi_id': poi.get('poi_id', f'poi_{idx}'),
                    'poi_name': poi.get('name', ''),
                    'latitude': lat,
                    'longitude': lon,
                    'geometry_wkt': cached['geometry_wkt'],
                    'area_km2': cached['area_km2'],
                    'from_cache': True
                })
            else:
                self.stats['cache_misses'] += 1
                uncached_pois.append(poi)
        
        logger.info(f"Cache hits: {self.stats['cache_hits']}, misses: {self.stats['cache_misses']}")
        
        # Generate isochrones for uncached POIs
        new_isochrones = []
        if uncached_pois:
            logger.info(f"Generating {len(uncached_pois)} new isochrones...")
            
            # Create temporary POI file for uncached locations
            temp_poi_file = Path(output_dir or '.') / 'temp_uncached_pois.csv'
            uncached_df = pd.DataFrame(uncached_pois)
            uncached_df.to_csv(temp_poi_file, index=False)
            
            try:
                # Run SocialMapper for uncached POIs only
                config = (
                    SocialMapperBuilder()
                    .with_custom_pois(str(temp_poi_file))
                    .with_travel_time(travel_time)
                    .with_travel_mode(travel_mode)
                    .enable_isochrone_export()
                    .with_output_directory(output_dir)
                    .build()
                )
                
                with SocialMapperClient() as client:
                    result = client.run_analysis(config)
                    
                    if result.is_ok():
                        analysis = result.unwrap()
                        
                        # Extract and cache the new isochrones
                        for file_type, file_path in analysis.files_generated.items():
                            if 'isochrone' in file_type.lower() and file_path.suffix == '.geoparquet':
                                new_gdf = gpd.read_parquet(file_path)
                                
                                for idx, row in new_gdf.iterrows():
                                    # Add to cache
                                    isochrone_data = {
                                        'latitude': row.get('poi_lat', row.geometry.centroid.y),
                                        'longitude': row.get('poi_lon', row.geometry.centroid.x),
                                        'travel_time_minutes': travel_time,
                                        'travel_mode': travel_mode,
                                        'origin_name': row.get('poi_name', ''),
                                        'origin_type': row.get('poi_type', '')
                                    }
                                    
                                    success, msg = self.cache.add_isochrone(isochrone_data, row.geometry)
                                    if not success:
                                        logger.warning(f"Failed to cache isochrone: {msg}")
                                    
                                    # Add to results
                                    new_isochrones.append({
                                        'poi_id': row.get('poi_id'),
                                        'poi_name': row.get('poi_name'),
                                        'latitude': isochrone_data['latitude'],
                                        'longitude': isochrone_data['longitude'],
                                        'geometry': row.geometry,
                                        'area_km2': row.geometry.area * 111.32 * 111.32,
                                        'from_cache': False
                                    })
                    else:
                        logger.error(f"SocialMapper analysis failed: {result.unwrap_err()}")
                        
            finally:
                # Clean up temp file
                if temp_poi_file.exists():
                    temp_poi_file.unlink()
        
        # Combine cached and new results
        all_isochrones = []
        
        # Convert cached WKT to geometries
        from shapely import wkt
        for cached_iso in cached_isochrones:
            cached_iso['geometry'] = wkt.loads(cached_iso['geometry_wkt'])
            del cached_iso['geometry_wkt']
            all_isochrones.append(cached_iso)
        
        all_isochrones.extend(new_isochrones)
        
        # Create combined GeoDataFrame
        if all_isochrones:
            combined_gdf = gpd.GeoDataFrame(all_isochrones)
            combined_gdf.set_crs(epsg=4326, inplace=True)
            
            # Save combined results
            if output_dir:
                output_file = Path(output_dir) / f'cached_isochrones_{travel_time}min_{travel_mode}.geoparquet'
                combined_gdf.to_parquet(output_file)
                logger.info(f"Saved combined results to {output_file}")
        
        # Calculate time saved
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Estimate time saved (assume 5 seconds per cached isochrone)
        self.stats['time_saved_seconds'] = self.stats['cache_hits'] * 5
        
        return {
            'total_pois': total_pois,
            'cache_stats': self.stats,
            'processing_time_seconds': total_time,
            'combined_gdf': combined_gdf if all_isochrones else None
        }
    
    def validate_cache_quality(self, sample_size: int = 10) -> pd.DataFrame:
        """Validate a sample of cached isochrones by regenerating them.
        
        Args:
            sample_size: Number of random isochrones to validate
            
        Returns:
            DataFrame with validation results
        """
        # Get random sample from cache
        sample_query = f"""
            SELECT * FROM isochrone_cache 
            ORDER BY RANDOM() 
            LIMIT {sample_size}
        """
        
        sample_df = self.cache.conn.execute(sample_query).fetchdf()
        
        validation_results = []
        
        for _, cached in sample_df.iterrows():
            # Regenerate the isochrone
            # (This would use SocialMapper to regenerate and compare)
            # For now, we'll just check basic properties
            
            validation = {
                'cache_key': cached['cache_key'],
                'origin': f"{cached['origin_lat']}, {cached['origin_lon']}",
                'travel_time': cached['travel_time_minutes'],
                'cached_area_km2': cached['area_km2'],
                'is_valid': cached['area_km2'] > 10,  # Basic sanity check
                'notes': 'Size check only'
            }
            
            validation_results.append(validation)
        
        return pd.DataFrame(validation_results)
    
    def export_cache_report(self, output_path: str):
        """Export a detailed cache report.
        
        Args:
            output_path: Path for the report file
        """
        stats = self.cache.get_statistics()
        
        report = f"""# Isochrone Cache Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Summary Statistics

- **Total Cached Isochrones**: {stats['total_isochrones']:,}
- **Unique Locations**: {stats['unique_locations']:,}
- **Total Cache Hits**: {stats['total_hits']:,}
- **Average Isochrone Area**: {stats['avg_area_km2']:.1f} km²

## Cache Performance

- **Hit Rate**: {(self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses']) * 100):.1f}%
- **Time Saved**: {self.stats['time_saved_seconds'] / 60:.1f} minutes
- **Space Used**: ~{stats['total_isochrones'] * 0.1:.1f} MB

## Travel Mode Distribution

- **Drive**: {stats['drive_count']:,} isochrones
- **Walk**: {stats['walk_count']:,} isochrones  
- **Bike**: {stats['bike_count']:,} isochrones

## Cache Age

- **Oldest Entry**: {stats['oldest_entry']}
- **Newest Entry**: {stats['newest_entry']}

## Recommendations

"""
        if stats['total_isochrones'] > 10000:
            report += "- Consider exporting older entries to GeoParquet archive\n"
        
        if self.stats['cache_hits'] > 0:
            hit_rate = self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses'])
            if hit_rate < 0.5:
                report += "- Low hit rate suggests many unique locations\n"
        
        with open(output_path, 'w') as f:
            f.write(report)
    
    def close(self):
        """Close the cache connection."""
        self.cache.close()
    
    def __enter__(self):
        """Context manager support."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python cached_analysis.py <poi_file.csv>")
        sys.exit(1)
    
    poi_file = sys.argv[1]
    
    with CachedAnalysisRunner() as runner:
        # Run cached analysis
        results = runner.analyze_with_cache(
            poi_file=poi_file,
            travel_time=30,
            travel_mode='drive',
            output_dir=Path('data/output/cached')
        )
        
        print(f"\nAnalysis Complete:")
        print(f"  Total POIs: {results['total_pois']}")
        print(f"  Cache hits: {results['cache_stats']['cache_hits']}")
        print(f"  Cache misses: {results['cache_stats']['cache_misses']}")
        print(f"  Time saved: {results['cache_stats']['time_saved_seconds'] / 60:.1f} minutes")
        
        # Export cache report
        runner.export_cache_report('cache_report.md')
        print(f"\nCache report saved to cache_report.md")