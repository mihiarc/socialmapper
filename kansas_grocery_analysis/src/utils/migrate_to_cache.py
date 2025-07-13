#!/usr/bin/env python3
"""
Migrate existing isochrone GeoParquet files to DuckDB cache.

This script scans for existing isochrone files and imports them into
the DuckDB cache for faster future access.
"""

import logging
from pathlib import Path
import re
from typing import List, Tuple

import geopandas as gpd
import pandas as pd
from rich.console import Console
from rich.progress import track

from .isochrone_cache import IsochroneCache

logger = logging.getLogger(__name__)
console = Console()


def find_isochrone_files(base_dir: Path = Path("data/output")) -> List[Path]:
    """Find all isochrone GeoParquet files in the output directory.
    
    Args:
        base_dir: Base directory to search
        
    Returns:
        List of paths to isochrone files
    """
    isochrone_files = []
    
    # Common patterns for isochrone files
    patterns = [
        "*isochrone*.geoparquet",
        "*isochrone*.parquet",
        "*_isochrones.geoparquet"
    ]
    
    for pattern in patterns:
        isochrone_files.extend(base_dir.rglob(pattern))
    
    # Remove duplicates
    isochrone_files = list(set(isochrone_files))
    
    console.print(f"[green]Found {len(isochrone_files)} isochrone files[/green]")
    return sorted(isochrone_files)


def extract_parameters_from_filename(filename: str) -> Tuple[int, str]:
    """Extract travel time and mode from filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        Tuple of (travel_time_minutes, travel_mode)
    """
    # Common patterns in filenames
    time_match = re.search(r'(\d+)min', filename)
    travel_time = int(time_match.group(1)) if time_match else 30
    
    # Check for travel mode
    if 'walk' in filename.lower():
        travel_mode = 'walk'
    elif 'bike' in filename.lower() or 'bicycle' in filename.lower():
        travel_mode = 'bike'
    else:
        travel_mode = 'drive'
    
    return travel_time, travel_mode


def migrate_file_to_cache(file_path: Path, cache: IsochroneCache) -> Tuple[int, int]:
    """Migrate a single isochrone file to the cache.
    
    Args:
        file_path: Path to the isochrone file
        cache: IsochroneCache instance
        
    Returns:
        Tuple of (added_count, skipped_count)
    """
    console.print(f"\n[blue]Processing: {file_path.name}[/blue]")
    
    try:
        # Load the isochrones
        gdf = gpd.read_parquet(file_path)
        
        # Extract default parameters from filename
        default_time, default_mode = extract_parameters_from_filename(file_path.name)
        
        added = 0
        skipped = 0
        
        for idx, row in track(gdf.iterrows(), total=len(gdf), 
                             description="Migrating isochrones"):
            try:
                # Extract location coordinates
                if 'poi_lat' in row and 'poi_lon' in row:
                    lat = row['poi_lat']
                    lon = row['poi_lon']
                elif hasattr(row.geometry, 'centroid'):
                    centroid = row.geometry.centroid
                    lat = centroid.y
                    lon = centroid.x
                else:
                    logger.warning(f"Could not extract coordinates for row {idx}")
                    skipped += 1
                    continue
                
                # Extract parameters
                travel_time = row.get('travel_time_minutes', default_time)
                travel_mode = row.get('travel_mode', default_mode)
                
                # Build isochrone data
                isochrone_data = {
                    'latitude': lat,
                    'longitude': lon,
                    'travel_time_minutes': int(travel_time),
                    'travel_mode': travel_mode,
                    'origin_name': row.get('poi_name', row.get('name', '')),
                    'origin_type': row.get('poi_type', row.get('type', ''))
                }
                
                # Add metadata
                metadata = {
                    'data_source': str(file_path),
                    'version': '0.6.1',
                    'network_nodes': row.get('network_nodes', 0),
                    'network_edges': row.get('network_edges', 0)
                }
                
                # Add to cache
                success, message = cache.add_isochrone(isochrone_data, row.geometry, metadata)
                if success:
                    added += 1
                else:
                    skipped += 1
                    logger.debug(f"Skipped: {message}")
                    
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                skipped += 1
        
        console.print(f"[green]Added: {added}, Skipped: {skipped}[/green]")
        return added, skipped
        
    except Exception as e:
        console.print(f"[red]Error loading file: {e}[/red]")
        return 0, 0


def verify_migration(cache: IsochroneCache):
    """Verify the migration by checking cache statistics.
    
    Args:
        cache: IsochroneCache instance
    """
    stats = cache.get_statistics()
    
    console.print("\n[bold]Migration Summary:[/bold]")
    console.print(f"  Total isochrones in cache: [green]{stats['total_isochrones']:,}[/green]")
    console.print(f"  Unique locations: [cyan]{stats['unique_locations']:,}[/cyan]")
    console.print(f"  Average area: [yellow]{stats['avg_area_km2']:.1f} km²[/yellow]")
    console.print(f"  Travel modes: Drive={stats['drive_count']}, Walk={stats['walk_count']}, Bike={stats['bike_count']}")
    
    # Check for potential issues
    if stats['avg_area_km2'] < 100:
        console.print("\n[yellow]⚠️  Warning: Average isochrone area seems small. Check for batch processing issues.[/yellow]")
    
    # Export a sample for verification
    sample_df = cache.find_nearby_isochrones(
        lat=39.0,  # Central Kansas
        lon=-98.0,
        radius_km=200
    )
    
    if not sample_df.empty:
        console.print(f"\n[bold]Sample of cached isochrones near central Kansas:[/bold]")
        console.print(sample_df.head())


def main():
    """Run the migration process."""
    console.print("[bold]Isochrone Cache Migration Tool[/bold]")
    console.print("=" * 50)
    
    # Initialize cache
    cache_path = "cache/isochrones.duckdb"
    console.print(f"\nInitializing cache at: {cache_path}")
    
    with IsochroneCache(cache_path) as cache:
        # Get initial statistics
        initial_stats = cache.get_statistics()
        initial_count = initial_stats['total_isochrones'] or 0
        console.print(f"Initial cache size: {initial_count:,} isochrones")
        
        # Find isochrone files
        isochrone_files = find_isochrone_files()
        
        if not isochrone_files:
            console.print("[yellow]No isochrone files found to migrate.[/yellow]")
            return
        
        # Migrate each file
        total_added = 0
        total_skipped = 0
        
        for file_path in isochrone_files:
            added, skipped = migrate_file_to_cache(file_path, cache)
            total_added += added
            total_skipped += skipped
        
        # Final summary
        console.print(f"\n[bold green]Migration Complete![/bold green]")
        console.print(f"  Files processed: {len(isochrone_files)}")
        console.print(f"  Isochrones added: {total_added:,}")
        console.print(f"  Isochrones skipped: {total_skipped:,}")
        
        # Verify migration
        verify_migration(cache)
        
        # Export cache to GeoParquet for backup
        if total_added > 0:
            backup_path = "cache/isochrones_backup.geoparquet"
            console.print(f"\n[blue]Exporting cache backup to: {backup_path}[/blue]")
            count = cache.export_to_geoparquet(backup_path)
            console.print(f"[green]Exported {count:,} isochrones to backup[/green]")


if __name__ == "__main__":
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    main()