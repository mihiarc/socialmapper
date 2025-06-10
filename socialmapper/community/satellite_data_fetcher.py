#!/usr/bin/env python3
"""
Satellite Data Fetcher for SocialMapper Community Module

This module integrates with the geoai package to fetch real satellite imagery
(NAIP and Sentinel-2) for computer vision analysis in community boundary detection.

Features:
- NAIP imagery download from Microsoft Planetary Computer
- Sentinel-2 imagery with cloud filtering
- Intelligent caching system with bounds-based keys
- Automatic cache validation and cleanup
- Geographic bounds-based fetching
- Integration with existing computer vision pipeline
"""

import os
import tempfile
import warnings
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
import numpy as np
import geopandas as gpd
from shapely.geometry import box
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.merge import merge
from ..util import sanitize_path, safe_join_path, PathSecurityError
import logging

# Check if geoai is available
try:
    import geoai
    GEOAI_AVAILABLE = True
except ImportError:
    GEOAI_AVAILABLE = False
    warnings.warn("geoai package not available. Install with: pip install geoai-py")

logger = logging.getLogger(__name__)


class SatelliteDataFetcher:
    """
    Fetches real satellite imagery using the geoai package for community analysis.
    Features intelligent caching system for fast iteration during testing.
    """
    
    def __init__(self, 
                 cache_dir: Optional[str] = None,
                 max_cloud_cover: float = 20.0,
                 preferred_resolution: float = 1.0):
        """
        Initialize the satellite data fetcher.
        
        Args:
            cache_dir: Directory to cache downloaded imagery
            max_cloud_cover: Maximum cloud cover percentage for imagery selection
            preferred_resolution: Preferred resolution in meters per pixel
        """
        if not GEOAI_AVAILABLE:
            raise ImportError("geoai package required. Install with: pip install geoai-py")
        
        # Securely handle cache directory
        if cache_dir:
            try:
                # Validate user-provided cache directory
                self.cache_dir = sanitize_path(cache_dir, allow_absolute=True)
            except PathSecurityError:
                # If validation fails, use default temp directory
                self.cache_dir = Path(tempfile.gettempdir()) / "socialmapper_satellite_cache"
        else:
            self.cache_dir = Path(tempfile.gettempdir()) / "socialmapper_satellite_cache"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create organized cache structure using safe path joining
        self.sentinel2_cache = safe_join_path(self.cache_dir, "sentinel2")
        self.naip_cache = safe_join_path(self.cache_dir, "naip")
        self.landsat_cache = safe_join_path(self.cache_dir, "landsat")
        self.metadata_cache = safe_join_path(self.cache_dir, "metadata")
        
        for cache_subdir in [self.sentinel2_cache, self.naip_cache, self.landsat_cache, self.metadata_cache]:
            cache_subdir.mkdir(exist_ok=True)
        
        self.max_cloud_cover = max_cloud_cover
        self.preferred_resolution = preferred_resolution
        
        logger.info(f"SatelliteDataFetcher initialized with cache dir: {self.cache_dir}")
        logger.info(f"Cache structure: sentinel2/, naip/, landsat/, metadata/")
    
    def _create_cache_key(self, bounds: Tuple[float, float, float, float], 
                         imagery_type: str, time_range: str, 
                         max_cloud_cover: float) -> str:
        """
        Create a unique cache key based on parameters for intelligent caching.
        
        Args:
            bounds: Geographic bounds
            imagery_type: Type of imagery
            time_range: Time range string
            max_cloud_cover: Cloud cover threshold
            
        Returns:
            Unique cache key string
        """
        # Round bounds to reasonable precision to enable cache hits for nearby areas
        rounded_bounds = tuple(round(coord, 4) for coord in bounds)
        
        cache_params = {
            "bounds": rounded_bounds,
            "imagery_type": imagery_type.lower(),
            "time_range": time_range,
            "max_cloud_cover": max_cloud_cover
        }
        
        # Create hash of parameters
        params_str = json.dumps(cache_params, sort_keys=True)
        cache_hash = hashlib.sha256(params_str.encode()).hexdigest()[:12]
        
        return f"{imagery_type.lower()}_{cache_hash}"
    
    def _validate_cached_file(self, file_path: Path) -> bool:
        """
        Validate that a cached file is complete and readable.
        
        Args:
            file_path: Path to cached file
            
        Returns:
            True if file is valid, False otherwise
        """
        try:
            if not file_path.exists():
                return False
            
            # Check file size is reasonable (> 1MB for satellite imagery)
            if file_path.stat().st_size < 1024 * 1024:
                logger.warning(f"Cached file {file_path} too small ({file_path.stat().st_size} bytes)")
                return False
            
            # Try to open with rasterio to validate
            with rasterio.open(file_path) as src:
                # Check basic properties
                if src.width == 0 or src.height == 0:
                    return False
                if src.count == 0:
                    return False
                # Try to read a small sample
                _ = src.read(1, window=((0, min(10, src.height)), (0, min(10, src.width))))
            
            return True
            
        except Exception as e:
            logger.warning(f"Cache validation failed for {file_path}: {e}")
            return False
    
    def _save_cache_metadata(self, cache_key: str, metadata: Dict) -> None:
        """Save metadata about cached imagery for future reference."""
        try:
            metadata_file = self.metadata_cache / f"{cache_key}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save cache metadata: {e}")
    
    def _load_cache_metadata(self, cache_key: str) -> Optional[Dict]:
        """Load metadata about cached imagery."""
        try:
            metadata_file = self.metadata_cache / f"{cache_key}.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache metadata: {e}")
        return None

    def get_best_imagery_for_bounds(self,
                                  bounds: Tuple[float, float, float, float],
                                  imagery_type: str = "naip",
                                  time_range: Optional[str] = None,
                                  max_items: int = 5) -> Optional[str]:
        """
        Get the best available imagery for given geographic bounds with intelligent caching.
        
        Args:
            bounds: Geographic bounds (minx, miny, maxx, maxy) in WGS84
            imagery_type: Type of imagery ("naip", "sentinel2", "landsat")
            time_range: Time range in format "YYYY-MM-DD/YYYY-MM-DD"
            max_items: Maximum number of items to search
            
        Returns:
            Path to downloaded imagery file, or None if not available
        """
        # Set default time range if not provided
        if time_range is None:
            end_date = datetime.now()
            if imagery_type.lower() == "naip":
                start_date = end_date - timedelta(days=5*365)  # 5 years for NAIP
            elif imagery_type.lower() == "sentinel2":
                start_date = end_date - timedelta(days=1*365)  # 1 year for Sentinel-2
            else:
                start_date = end_date - timedelta(days=3*365)  # 3 years for others
            time_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        
        # Create cache key
        cache_key = self._create_cache_key(bounds, imagery_type, time_range, self.max_cloud_cover)
        
        # Determine cache subdirectory
        if imagery_type.lower() == "sentinel2":
            cache_subdir = self.sentinel2_cache
        elif imagery_type.lower() == "naip":
            cache_subdir = self.naip_cache
        else:
            cache_subdir = self.landsat_cache
        
        cached_file = cache_subdir / f"{cache_key}.tif"
        
        # Check if we have a valid cached version
        if self._validate_cached_file(cached_file):
            logger.info(f"✅ Using cached {imagery_type} imagery: {cached_file}")
            metadata = self._load_cache_metadata(cache_key)
            if metadata:
                logger.info(f"   Cached on: {metadata.get('cached_date', 'unknown')}")
                logger.info(f"   Source item: {metadata.get('source_item_id', 'unknown')}")
                logger.info(f"   Cloud cover: {metadata.get('cloud_cover', 'unknown')}%")
            return str(cached_file)
        
        # Cache miss - fetch new imagery
        logger.info(f"🔄 Cache miss for {imagery_type} bounds {bounds}")
        logger.info(f"   Cache key: {cache_key}")
        
        if imagery_type.lower() == "naip":
            result = self._fetch_naip_imagery(bounds, time_range, max_items, cached_file)
        elif imagery_type.lower() == "sentinel2":
            result = self._fetch_sentinel2_imagery(bounds, time_range, max_items, cached_file)
        elif imagery_type.lower() == "landsat":
            result = self._fetch_landsat_imagery(bounds, time_range, max_items, cached_file)
        else:
            raise ValueError(f"Unsupported imagery type: {imagery_type}")
        
        return result
    
    def _fetch_naip_imagery(self,
                           bounds: Tuple[float, float, float, float],
                           time_range: Optional[str] = None,
                           max_items: int = 5,
                           cached_file: Optional[Path] = None) -> Optional[str]:
        """
        Fetch NAIP imagery using geoai.
        
        Args:
            bounds: Geographic bounds (minx, miny, maxx, maxy)
            time_range: Time range string
            max_items: Maximum items to search
            cached_file: Path to cached file
            
        Returns:
            Path to downloaded NAIP imagery
        """
        try:
            # Set default time range if not provided (last 5 years)
            if time_range is None:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=5*365)
                time_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            
            logger.info(f"Searching for NAIP imagery in bounds {bounds} for time range {time_range}")
            
            # Search for NAIP imagery
            items = geoai.pc_stac_search(
                collection="naip",
                bbox=bounds,
                time_range=time_range,
                max_items=max_items
            )
            
            if not items:
                logger.warning(f"No NAIP imagery found for bounds {bounds}")
                return None
            
            logger.info(f"Found {len(items)} NAIP items, selecting best quality")
            
            # Select the most recent item (items are usually sorted by date)
            best_item = items[0]
            
            # Create cache filename
            item_id = best_item.id
            cache_filename = f"naip_{item_id}.tif"
            cache_path = self.naip_cache / cache_filename
            
            # Check if already cached
            if cached_file and cached_file.exists():
                logger.info(f"Using cached NAIP imagery: {cached_file}")
                return str(cached_file)
            
            # Download the imagery
            logger.info(f"Downloading NAIP imagery: {item_id}")
            try:
                downloaded = geoai.pc_stac_download(
                    best_item,
                    output_dir=str(self.naip_cache),
                    assets=["image"],
                    max_workers=1  # Reduce workers for stability
                )
                
                # Find the downloaded file - check multiple patterns
                possible_patterns = [
                    f"*{item_id}*image*.tif",
                    f"*{item_id}*.tif", 
                    f"{item_id}*.tif",
                    "*.tif"  # Last resort - get any new .tif file
                ]
                
                downloaded_files = []
                for pattern in possible_patterns:
                    downloaded_files = list(self.naip_cache.glob(pattern))
                    if downloaded_files:
                        break
                
                if downloaded_files:
                    # Get the most recently created file
                    downloaded_path = max(downloaded_files, key=lambda f: f.stat().st_mtime)
                    # Rename to our expected format
                    final_path = cache_path
                    if downloaded_path != final_path:
                        downloaded_path.rename(final_path)
                    logger.info(f"Successfully downloaded NAIP imagery: {final_path}")
                    return str(final_path)
                else:
                    logger.error("Download completed but no .tif files found")
                    return None
                    
            except Exception as e:
                logger.error(f"Download failed: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching NAIP imagery: {e}")
            return None
    
    def _fetch_sentinel2_imagery(self,
                                bounds: Tuple[float, float, float, float],
                                time_range: Optional[str] = None,
                                max_items: int = 10,
                                cached_file: Optional[Path] = None) -> Optional[str]:
        """
        Fetch Sentinel-2 imagery using geoai.
        
        Args:
            bounds: Geographic bounds (minx, miny, maxx, maxy)
            time_range: Time range string
            max_items: Maximum items to search
            cached_file: Path to cached file
            
        Returns:
            Path to processed Sentinel-2 imagery
        """
        try:
            # Set default time range if not provided (last 2 years)
            if time_range is None:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=2*365)
                time_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            
            logger.info(f"Searching for Sentinel-2 imagery in bounds {bounds} for time range {time_range}")
            
            # Search for Sentinel-2 imagery with cloud filtering
            items = geoai.pc_stac_search(
                collection="sentinel-2-l2a",
                bbox=bounds,
                time_range=time_range,
                query={"eo:cloud_cover": {"lt": self.max_cloud_cover}},
                max_items=max_items
            )
            
            if not items:
                logger.warning(f"No low-cloud Sentinel-2 imagery found for bounds {bounds}")
                return None
            
            logger.info(f"Found {len(items)} Sentinel-2 items, selecting best quality")
            
            # Select item with lowest cloud cover
            best_item = min(items, key=lambda x: x.properties.get('eo:cloud_cover', 100))
            cloud_cover = best_item.properties.get('eo:cloud_cover', 'unknown')
            
            logger.info(f"Selected Sentinel-2 item with {cloud_cover}% cloud cover")
            
            # Create cache filename
            item_id = best_item.id
            cache_filename = f"sentinel2_{item_id}_rgb.tif"
            cache_path = self.sentinel2_cache / cache_filename
            
            # Check if already cached
            if cached_file and cached_file.exists():
                logger.info(f"Using cached Sentinel-2 imagery: {cached_file}")
                return str(cached_file)
            
            # Download RGB bands (B04=red, B03=green, B02=blue for Sentinel-2)
            logger.info(f"Downloading Sentinel-2 imagery: {item_id}")
            try:
                downloaded = geoai.pc_stac_download(
                    best_item,
                    output_dir=str(self.sentinel2_cache),
                    assets=["B04", "B03", "B02"],  # Sentinel-2 RGB bands
                    max_workers=1  # Reduce workers for stability
                )
            except Exception as e:
                logger.error(f"Sentinel-2 download failed: {e}")
                return None
            
            # Use the cached file path provided by the calling function
            target_path = cached_file if cached_file else cache_path
            
            # Combine RGB bands into single file
            rgb_path = self._combine_sentinel2_bands(downloaded, target_path)
            if rgb_path:
                logger.info(f"Successfully processed Sentinel-2 imagery: {rgb_path}")
                
                # Save metadata for future reference
                cache_key = str(target_path.stem)
                metadata = {
                    "cached_date": datetime.now().isoformat(),
                    "source_item_id": item_id,
                    "cloud_cover": cloud_cover,
                    "bounds": bounds,
                    "time_range": time_range,
                    "imagery_type": "sentinel2"
                }
                self._save_cache_metadata(cache_key, metadata)
                
                return str(rgb_path)
            else:
                logger.error("Failed to combine Sentinel-2 bands")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching Sentinel-2 imagery: {e}")
            return None
    
    def _fetch_landsat_imagery(self,
                              bounds: Tuple[float, float, float, float],
                              time_range: Optional[str] = None,
                              max_items: int = 10,
                              cached_file: Optional[Path] = None) -> Optional[str]:
        """
        Fetch Landsat imagery using geoai.
        
        Args:
            bounds: Geographic bounds (minx, miny, maxx, maxy)
            time_range: Time range string
            max_items: Maximum items to search
            cached_file: Path to cached file
            
        Returns:
            Path to processed Landsat imagery
        """
        try:
            # Set default time range if not provided (last 3 years)
            if time_range is None:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=3*365)
                time_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            
            logger.info(f"Searching for Landsat imagery in bounds {bounds} for time range {time_range}")
            
            # Search for Landsat imagery with cloud filtering
            items = geoai.pc_stac_search(
                collection="landsat-c2-l2",
                bbox=bounds,
                time_range=time_range,
                query={"eo:cloud_cover": {"lt": self.max_cloud_cover}},
                max_items=max_items
            )
            
            if not items:
                logger.warning(f"No low-cloud Landsat imagery found for bounds {bounds}")
                return None
            
            logger.info(f"Found {len(items)} Landsat items, selecting best quality")
            
            # Select item with lowest cloud cover
            best_item = min(items, key=lambda x: x.properties.get('eo:cloud_cover', 100))
            
            # Create cache filename
            item_id = best_item.id
            cache_filename = f"landsat_{item_id}_rgb.tif"
            cache_path = self.landsat_cache / cache_filename
            
            # Check if already cached
            if cached_file and cached_file.exists():
                logger.info(f"Using cached Landsat imagery: {cached_file}")
                return str(cached_file)
            
            # Download RGB bands
            logger.info(f"Downloading Landsat imagery: {item_id}")
            downloaded = geoai.pc_stac_download(
                best_item,
                output_dir=str(self.landsat_cache),
                assets=["red", "green", "blue"]
            )
            
            # Combine RGB bands into single file
            rgb_path = self._combine_landsat_bands(downloaded, cache_path)
            if rgb_path:
                logger.info(f"Successfully processed Landsat imagery: {rgb_path}")
                return str(rgb_path)
            else:
                logger.error("Failed to combine Landsat bands")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching Landsat imagery: {e}")
            return None
    
    def _combine_sentinel2_bands(self, downloaded_info: Dict, output_path: Path) -> Optional[str]:
        """
        Combine Sentinel-2 RGB bands into a single file.
        
        Args:
            downloaded_info: Information about downloaded files
            output_path: Path for combined output file
            
        Returns:
            Path to combined RGB file
        """
        try:
            # Find downloaded band files - prioritize most recent files
            all_tif_files = list(self.sentinel2_cache.glob("*.tif"))
            
            # Sort by modification time to get most recent downloads
            recent_files = sorted(all_tif_files, key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Find band files by name patterns, preferring recent downloads
            band_files = {}
            
            for file_path in recent_files:
                file_str = str(file_path)
                # Check for Sentinel-2 band patterns (be more specific to avoid conflicts)
                if "B04" in file_str and 'red' not in band_files:
                    band_files['red'] = file_path
                elif "B03" in file_str and 'green' not in band_files:
                    band_files['green'] = file_path  
                elif "B02" in file_str and 'blue' not in band_files:
                    band_files['blue'] = file_path
                
                # Stop when we have all three bands
                if len(band_files) == 3:
                    break
            
            logger.info(f"Found {len(band_files)} band files: {list(band_files.keys())}")
            logger.info(f"Band file paths:")
            for color, path in band_files.items():
                logger.info(f"  {color}: {path.name}")
            
            if len(band_files) != 3:
                logger.error(f"Expected 3 bands, found {len(band_files)}")
                logger.info(f"Available files: {[f.name for f in recent_files[:10]]}")  # Show first 10
                
                # Try alternative approach - use the 3 most recent .tif files
                if len(recent_files) >= 3:
                    logger.info("Attempting fallback with 3 most recent files...")
                    band_files = {
                        'red': recent_files[0], 
                        'green': recent_files[1], 
                        'blue': recent_files[2]
                    }
                    logger.info(f"Fallback mapping:")
                    for color, path in band_files.items():
                        logger.info(f"  {color}: {path.name}")
                else:
                    return None
            
            # Read bands and combine
            with rasterio.open(band_files['red']) as red_src:
                red_data = red_src.read(1)
                profile = red_src.profile
                
            with rasterio.open(band_files['green']) as green_src:
                green_data = green_src.read(1)
                
            with rasterio.open(band_files['blue']) as blue_src:
                blue_data = blue_src.read(1)
            
            # Update profile for RGB
            profile.update(count=3, dtype='uint16')
            
            # Write combined RGB file
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(red_data, 1)
                dst.write(green_data, 2)
                dst.write(blue_data, 3)
            
            # Clean up individual band files
            for band_file in band_files.values():
                try:
                    band_file.unlink()
                except:
                    pass
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error combining Sentinel-2 bands: {e}")
            return None
    
    def _combine_landsat_bands(self, downloaded_info: Dict, output_path: Path) -> Optional[str]:
        """
        Combine Landsat RGB bands into a single file.
        
        Args:
            downloaded_info: Information about downloaded files
            output_path: Path for combined output file
            
        Returns:
            Path to combined RGB file
        """
        try:
            # Find downloaded band files
            band_files = {}
            for file_path in self.landsat_cache.glob("*.tif"):
                if "red" in str(file_path).lower():
                    band_files['red'] = file_path
                elif "green" in str(file_path).lower():
                    band_files['green'] = file_path
                elif "blue" in str(file_path).lower():
                    band_files['blue'] = file_path
            
            if len(band_files) != 3:
                logger.error(f"Expected 3 bands, found {len(band_files)}")
                return None
            
            # Read bands and combine (similar to Sentinel-2)
            with rasterio.open(band_files['red']) as red_src:
                red_data = red_src.read(1)
                profile = red_src.profile
                
            with rasterio.open(band_files['green']) as green_src:
                green_data = green_src.read(1)
                
            with rasterio.open(band_files['blue']) as blue_src:
                blue_data = blue_src.read(1)
            
            # Update profile for RGB
            profile.update(count=3, dtype='uint16')
            
            # Write combined RGB file
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(red_data, 1)
                dst.write(green_data, 2)
                dst.write(blue_data, 3)
            
            # Clean up individual band files
            for band_file in band_files.values():
                try:
                    band_file.unlink()
                except:
                    pass
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error combining Landsat bands: {e}")
            return None
    
    def get_imagery_for_buildings(self,
                                buildings_gdf: gpd.GeoDataFrame,
                                buffer_meters: float = 1000,
                                imagery_type: str = "naip") -> Optional[str]:
        """
        Get satellite imagery covering a set of buildings.
        
        Args:
            buildings_gdf: GeoDataFrame containing building footprints
            buffer_meters: Buffer around buildings in meters
            imagery_type: Type of imagery to fetch
            
        Returns:
            Path to satellite imagery covering the buildings
        """
        # Calculate bounds of buildings with buffer
        buildings_bounds = buildings_gdf.total_bounds
        
        # Convert to geographic CRS if needed
        if buildings_gdf.crs != 'EPSG:4326':
            buildings_geo = buildings_gdf.to_crs('EPSG:4326')
            buildings_bounds = buildings_geo.total_bounds
        
        # Add buffer (approximate conversion from meters to degrees)
        buffer_degrees = buffer_meters / 111000  # Rough conversion
        buffered_bounds = (
            buildings_bounds[0] - buffer_degrees,  # minx
            buildings_bounds[1] - buffer_degrees,  # miny
            buildings_bounds[2] + buffer_degrees,  # maxx
            buildings_bounds[3] + buffer_degrees   # maxy
        )
        
        logger.info(f"Fetching {imagery_type} imagery for buildings with bounds {buffered_bounds}")
        
        return self.get_best_imagery_for_bounds(
            bounds=buffered_bounds,
            imagery_type=imagery_type
        )
    
    def clear_cache(self, older_than_days: Optional[int] = None):
        """
        Clear cached satellite imagery.
        
        Args:
            older_than_days: Only clear files older than this many days. If None, clear all.
        """
        if older_than_days is not None:
            cutoff_time = datetime.now() - timedelta(days=older_than_days)
            
        cleared_count = 0
        for file_path in self.cache_dir.glob("*.tif"):
            try:
                if older_than_days is None:
                    file_path.unlink()
                    cleared_count += 1
                else:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        cleared_count += 1
            except Exception as e:
                logger.warning(f"Could not remove {file_path}: {e}")
        
        logger.info(f"Cleared {cleared_count} cached files")


# Convenience functions for integration with existing code

def fetch_satellite_imagery_for_community_analysis(buildings_gdf: gpd.GeoDataFrame,
                                                  imagery_type: str = "naip",
                                                  cache_dir: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to fetch satellite imagery for community boundary analysis.
    
    Args:
        buildings_gdf: GeoDataFrame containing building footprints
        imagery_type: Type of imagery ("naip", "sentinel2", "landsat")
        cache_dir: Directory for caching imagery
        
    Returns:
        Path to satellite imagery file, or None if unavailable
    """
    if not GEOAI_AVAILABLE:
        logger.warning("geoai package not available, cannot fetch real satellite imagery")
        return None
    
    try:
        fetcher = SatelliteDataFetcher(cache_dir=cache_dir)
        return fetcher.get_imagery_for_buildings(buildings_gdf, imagery_type=imagery_type)
    except Exception as e:
        logger.error(f"Error fetching satellite imagery: {e}")
        return None


def get_imagery_bounds_info(image_path: str) -> Dict[str, Any]:
    """
    Get geographic bounds and metadata from a satellite image.
    
    Args:
        image_path: Path to satellite image file
        
    Returns:
        Dictionary with bounds and metadata
    """
    try:
        with rasterio.open(image_path) as src:
            bounds = src.bounds
            crs = src.crs
            shape = src.shape
            
            return {
                'bounds': (bounds.left, bounds.bottom, bounds.right, bounds.top),
                'crs': str(crs),
                'width': shape[1],
                'height': shape[0],
                'bands': src.count,
                'dtype': str(src.dtype),
                'resolution': src.res
            }
    except Exception as e:
        logger.error(f"Error reading image metadata: {e}")
        return {} 