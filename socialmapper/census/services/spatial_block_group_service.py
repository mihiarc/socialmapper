"""
Spatial block group service that uses polygon intersection to fetch block groups.

This service fetches block groups that intersect with isochrones, regardless of 
county boundaries, using the TIGER REST API's spatial query capabilities.
"""

import json
import logging
from typing import List, Optional, Dict, Any, Union

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.ops import unary_union

from ..config import CensusConfig
from ...progress import get_progress_bar

logger = logging.getLogger(__name__)


class SpatialBlockGroupService:
    """Service for fetching block groups using spatial queries."""
    
    def __init__(self, config: Optional[CensusConfig] = None):
        """Initialize the spatial block group service.
        
        Args:
            config: Census configuration object
        """
        self.config = config or CensusConfig()
        self.base_url = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/1/query"
        
    def fetch_block_groups_by_polygon(
        self,
        polygon: Union[Polygon, MultiPolygon],
        state_fips: Optional[List[str]] = None,
        use_bbox_fallback: bool = True
    ) -> gpd.GeoDataFrame:
        """
        Fetch block groups that intersect with a polygon.
        
        Args:
            polygon: Shapely polygon or multipolygon to query with
            state_fips: Optional list of state FIPS codes to limit the query
            use_bbox_fallback: If polygon query fails, fall back to bounding box
            
        Returns:
            GeoDataFrame with block groups that intersect the polygon
        """
        try:
            # First try polygon intersection
            logger.info("Attempting to fetch block groups using polygon intersection")
            return self._query_by_polygon(polygon, state_fips)
            
        except Exception as e:
            logger.warning(f"Polygon query failed: {e}")
            
            if use_bbox_fallback:
                logger.info("Falling back to bounding box query")
                return self._query_by_bbox(polygon.bounds, state_fips)
            else:
                raise
    
    def fetch_block_groups_by_isochrones(
        self,
        isochrone_gdf: gpd.GeoDataFrame,
        chunk_size: int = 10
    ) -> gpd.GeoDataFrame:
        """
        Fetch block groups that intersect with isochrones.
        
        Args:
            isochrone_gdf: GeoDataFrame containing isochrone geometries
            chunk_size: Number of isochrones to process at once
            
        Returns:
            GeoDataFrame with all block groups intersecting any isochrone
        """
        if isochrone_gdf.empty:
            return gpd.GeoDataFrame()
        
        # Ensure isochrones are in Web Mercator for the API
        if isochrone_gdf.crs != "EPSG:3857":
            logger.info(f"Projecting isochrones from {isochrone_gdf.crs} to EPSG:3857")
            isochrone_gdf = isochrone_gdf.to_crs("EPSG:3857")
        
        # Create union of all isochrones
        logger.info(f"Creating union of {len(isochrone_gdf)} isochrones")
        isochrone_union = unary_union(isochrone_gdf.geometry)
        
        # Simplify the union to reduce complexity for the API
        # Use a tolerance that preserves the general shape but reduces vertices
        tolerance = 100  # 100 meters in Web Mercator
        simplified_union = isochrone_union.simplify(tolerance, preserve_topology=True)
        
        logger.info(f"Simplified isochrone union from {self._count_vertices(isochrone_union)} to {self._count_vertices(simplified_union)} vertices")
        
        # Fetch block groups
        result_gdf = self.fetch_block_groups_by_polygon(simplified_union)
        
        # Convert back to original CRS if needed
        if result_gdf.crs != isochrone_gdf.crs:
            result_gdf = result_gdf.to_crs(isochrone_gdf.crs)
        
        return result_gdf
    
    def _query_by_polygon(
        self,
        polygon: Union[Polygon, MultiPolygon],
        state_fips: Optional[List[str]] = None
    ) -> gpd.GeoDataFrame:
        """Execute polygon intersection query."""
        
        # Convert polygon to GeoJSON-like structure for the API
        if isinstance(polygon, MultiPolygon):
            # For MultiPolygon, use the convex hull to simplify
            polygon = polygon.convex_hull
        
        # Get polygon coordinates in the format the API expects
        coords = list(polygon.exterior.coords)
        
        # Build the geometry parameter
        geometry = {
            "rings": [[[x, y] for x, y in coords]],
            "spatialReference": {"wkid": 3857}  # Web Mercator
        }
        
        # Build query parameters
        params = {
            "geometry": json.dumps(geometry),
            "geometryType": "esriGeometryPolygon",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "STATE,COUNTY,TRACT,BLKGRP,GEOID",
            "returnGeometry": "true",
            "f": "geojson",
            "outSR": 4326  # Return in WGS84
        }
        
        # Add state filter if provided
        if state_fips:
            state_list = ",".join([f"'{fips}'" for fips in state_fips])
            params["where"] = f"STATE IN ({state_list})"
        else:
            params["where"] = "1=1"  # No attribute filter
        
        # Execute query
        logger.info(f"Querying TIGER API with polygon ({len(coords)} vertices)")
        response = requests.get(self.base_url, params=params, timeout=60)
        
        if response.status_code != 200:
            raise ValueError(f"API returned status code {response.status_code}: {response.text}")
        
        # Parse response
        data = response.json()
        
        if "error" in data:
            raise ValueError(f"API error: {data['error']}")
        
        # Convert to GeoDataFrame
        features = data.get("features", [])
        if not features:
            logger.warning("No block groups found in polygon query")
            return gpd.GeoDataFrame()
        
        gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
        logger.info(f"Retrieved {len(gdf)} block groups from polygon query")
        
        return gdf
    
    def _query_by_bbox(
        self,
        bounds: tuple,
        state_fips: Optional[List[str]] = None
    ) -> gpd.GeoDataFrame:
        """Execute bounding box query as fallback."""
        
        # bounds is (minx, miny, maxx, maxy)
        minx, miny, maxx, maxy = bounds
        
        # Build the geometry parameter for bbox
        geometry = {
            "xmin": minx,
            "ymin": miny,
            "xmax": maxx,
            "ymax": maxy,
            "spatialReference": {"wkid": 3857}
        }
        
        # Build query parameters
        params = {
            "geometry": json.dumps(geometry),
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "STATE,COUNTY,TRACT,BLKGRP,GEOID",
            "returnGeometry": "true",
            "f": "geojson",
            "outSR": 4326
        }
        
        # Add state filter if provided
        if state_fips:
            state_list = ",".join([f"'{fips}'" for fips in state_fips])
            params["where"] = f"STATE IN ({state_list})"
        else:
            params["where"] = "1=1"
        
        # Execute query
        logger.info(f"Querying TIGER API with bounding box")
        response = requests.get(self.base_url, params=params, timeout=60)
        
        if response.status_code != 200:
            raise ValueError(f"API returned status code {response.status_code}")
        
        # Parse response
        data = response.json()
        
        if "error" in data:
            raise ValueError(f"API error: {data['error']}")
        
        # Convert to GeoDataFrame
        features = data.get("features", [])
        if not features:
            logger.warning("No block groups found in bbox query")
            return gpd.GeoDataFrame()
        
        gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
        logger.info(f"Retrieved {len(gdf)} block groups from bbox query")
        
        return gdf
    
    def _count_vertices(self, geom: Union[Polygon, MultiPolygon]) -> int:
        """Count vertices in a geometry."""
        if isinstance(geom, Polygon):
            return len(geom.exterior.coords)
        elif isinstance(geom, MultiPolygon):
            return sum(len(p.exterior.coords) for p in geom.geoms)
        return 0