"""
Spatial Clustering for Community Boundary Detection

This module uses advanced spatial clustering algorithms to identify patterns in:
- Building footprints and arrangements
- Housing development layouts
- Natural community boundaries
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.cluster import DBSCAN, HDBSCAN
from sklearn.preprocessing import StandardScaler
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import unary_union
import rasterio
from rasterio.features import shapes
import cv2
from typing import Dict, List, Tuple, Optional, Union

# Try importing advanced clustering libraries
try:
    from hdbscan import HDBSCAN
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False

try:
    import alphashape
    ALPHASHAPE_AVAILABLE = True
except ImportError:
    ALPHASHAPE_AVAILABLE = False


class CommunityBoundaryDetector:
    """
    Advanced spatial clustering for detecting organic community boundaries
    based on building patterns, housing developments, and spatial characteristics.
    """
    
    def __init__(self, 
                 clustering_method: str = 'hdbscan',
                 min_cluster_size: int = 20,
                 min_samples: int = 5,
                 cluster_selection_epsilon: float = 0.1):
        """
        Initialize the community boundary detector.
        
        Args:
            clustering_method: 'hdbscan', 'dbscan', or 'spectral'
            min_cluster_size: Minimum number of buildings in a cluster
            min_samples: Minimum samples for DBSCAN
            cluster_selection_epsilon: Epsilon parameter for clustering
        """
        self.clustering_method = clustering_method
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.cluster_selection_epsilon = cluster_selection_epsilon
        self.scaler = StandardScaler()
        
    def extract_building_features(self, buildings_gdf: gpd.GeoDataFrame) -> np.ndarray:
        """
        Extract spatial and morphological features from building footprints.
        
        Args:
            buildings_gdf: GeoDataFrame containing building polygons
            
        Returns:
            Feature matrix with spatial and morphological characteristics
        """
        features = []
        
        for idx, building in buildings_gdf.iterrows():
            geom = building.geometry
            
            # Basic geometric features
            area = geom.area
            perimeter = geom.length
            compactness = (4 * np.pi * area) / (perimeter ** 2)
            
            # Orientation and shape features
            bounds = geom.bounds
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            aspect_ratio = width / height if height > 0 else 0
            
            # Centroid coordinates
            centroid = geom.centroid
            x, y = centroid.x, centroid.y
            
            # Calculate nearest neighbor distances
            distances = [building.geometry.distance(other.geometry) 
                        for _, other in buildings_gdf.iterrows() 
                        if not building.geometry.equals(other.geometry)]
            
            nearest_distance = min(distances) if distances else 0
            avg_distance_5nn = np.mean(sorted(distances)[:5]) if len(distances) >= 5 else nearest_distance
            
            # Density in local neighborhood (500m radius)
            local_area = Point(x, y).buffer(500)
            local_buildings = buildings_gdf[buildings_gdf.intersects(local_area)]
            local_density = len(local_buildings) / local_area.area * 1000000  # buildings per km²
            
            feature_vector = [
                x, y,                    # Location
                area, perimeter,         # Size
                compactness, aspect_ratio, # Shape
                nearest_distance,        # Isolation
                avg_distance_5nn,       # Local spacing
                local_density           # Local density
            ]
            
            features.append(feature_vector)
            
        return np.array(features)
    
    def detect_housing_developments(self, buildings_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Detect housing developments using spatial clustering of building patterns.
        
        Args:
            buildings_gdf: GeoDataFrame containing building polygons
            
        Returns:
            GeoDataFrame with cluster labels and development boundaries
        """
        # Extract features
        features = self.extract_building_features(buildings_gdf)
        
        # Normalize features
        features_scaled = self.scaler.fit_transform(features)
        
        # Apply clustering algorithm
        if self.clustering_method == 'hdbscan' and HDBSCAN_AVAILABLE:
            clusterer = HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=self.min_samples,
                cluster_selection_epsilon=self.cluster_selection_epsilon
            )
        else:
            # Fallback to DBSCAN
            eps = self.cluster_selection_epsilon * 1000  # Convert to meters
            clusterer = DBSCAN(eps=eps, min_samples=self.min_samples)
            
        cluster_labels = clusterer.fit_predict(features_scaled)
        
        # Add cluster labels to buildings
        buildings_gdf = buildings_gdf.copy()
        buildings_gdf['cluster_id'] = cluster_labels
        buildings_gdf['development_type'] = self._classify_development_type(buildings_gdf)
        
        return buildings_gdf
    
    def _classify_development_type(self, clustered_buildings: gpd.GeoDataFrame) -> List[str]:
        """
        Classify the type of housing development based on spatial patterns.
        """
        development_types = []
        
        for _, building in clustered_buildings.iterrows():
            cluster_id = building['cluster_id']
            
            if cluster_id == -1:  # Noise/isolated buildings
                development_types.append('isolated')
                continue
                
            # Get all buildings in this cluster
            cluster_buildings = clustered_buildings[clustered_buildings['cluster_id'] == cluster_id]
            
            # Calculate cluster characteristics
            areas = cluster_buildings.geometry.area
            area_std = areas.std()
            area_mean = areas.mean()
            
            # Calculate spacing regularity
            centroids = [geom.centroid for geom in cluster_buildings.geometry]
            distances = []
            for i, c1 in enumerate(centroids):
                for j, c2 in enumerate(centroids[i+1:], i+1):
                    distances.append(c1.distance(c2))
            
            distance_std = np.std(distances) if distances else 0
            distance_mean = np.mean(distances) if distances else 0
            
            # Classification logic
            if area_std / area_mean < 0.2 and distance_std / distance_mean < 0.3:
                dev_type = 'planned_development'  # Uniform size and spacing
            elif len(cluster_buildings) > 50 and area_mean < 200:  # Small, dense
                dev_type = 'dense_residential'
            elif area_mean > 500:  # Large buildings
                dev_type = 'suburban_development'
            else:
                dev_type = 'mixed_residential'
                
            development_types.append(dev_type)
            
        return development_types
    
    def create_development_boundaries(self, clustered_buildings: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Create polygon boundaries around detected housing developments.
        """
        boundaries = []
        
        unique_clusters = clustered_buildings['cluster_id'].unique()
        unique_clusters = unique_clusters[unique_clusters != -1]  # Exclude noise
        
        for cluster_id in unique_clusters:
            cluster_buildings = clustered_buildings[clustered_buildings['cluster_id'] == cluster_id]
            
            if len(cluster_buildings) < 3:
                continue
                
            # Get centroids
            points = [geom.centroid for geom in cluster_buildings.geometry]
            
            # Create boundary using alpha shape or convex hull
            if ALPHASHAPE_AVAILABLE:
                try:
                    # Alpha shape for more accurate boundaries
                    coords = [(p.x, p.y) for p in points]
                    alpha_shape = alphashape.alphashape(coords, 0.1)
                    boundary = alpha_shape
                except:
                    # Fallback to convex hull
                    boundary = unary_union([p.buffer(100) for p in points]).convex_hull
            else:
                # Convex hull with buffer
                boundary = unary_union([p.buffer(100) for p in points]).convex_hull
            
            # Get development type (most common in cluster)
            dev_type = cluster_buildings['development_type'].mode().iloc[0]
            
            boundaries.append({
                'cluster_id': cluster_id,
                'geometry': boundary,
                'development_type': dev_type,
                'building_count': len(cluster_buildings),
                'avg_building_size': cluster_buildings.geometry.area.mean(),
                'density': len(cluster_buildings) / boundary.area * 1000000  # buildings per km²
            })
        
        return gpd.GeoDataFrame(boundaries, crs=clustered_buildings.crs)


def detect_housing_developments(buildings_gdf: gpd.GeoDataFrame, 
                              method: str = 'hdbscan',
                              **kwargs) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    High-level function to detect housing developments from building footprints.
    
    Args:
        buildings_gdf: GeoDataFrame containing building polygons
        method: Clustering method ('hdbscan', 'dbscan', 'spectral')
        **kwargs: Additional parameters for clustering
        
    Returns:
        Tuple of (clustered_buildings, development_boundaries)
    """
    detector = CommunityBoundaryDetector(clustering_method=method, **kwargs)
    
    # Detect developments
    clustered_buildings = detector.detect_housing_developments(buildings_gdf)
    
    # Create boundaries
    boundaries = detector.create_development_boundaries(clustered_buildings)
    
    return clustered_buildings, boundaries


def cluster_building_patterns(buildings_gdf: gpd.GeoDataFrame,
                            feature_weights: Optional[Dict[str, float]] = None) -> gpd.GeoDataFrame:
    """
    Cluster buildings based on architectural and spatial patterns.
    
    Args:
        buildings_gdf: GeoDataFrame with building footprints
        feature_weights: Weights for different feature types
        
    Returns:
        GeoDataFrame with pattern-based clusters
    """
    if feature_weights is None:
        feature_weights = {
            'spatial': 0.4,      # Location importance
            'morphological': 0.3, # Shape importance  
            'density': 0.3       # Local density importance
        }
    
    detector = CommunityBoundaryDetector()
    return detector.detect_housing_developments(buildings_gdf)


def identify_natural_boundaries(area_gdf: gpd.GeoDataFrame,
                              terrain_raster: Optional[str] = None,
                              water_bodies: Optional[gpd.GeoDataFrame] = None,
                              roads: Optional[gpd.GeoDataFrame] = None) -> gpd.GeoDataFrame:
    """
    Identify natural and infrastructure boundaries that separate communities.
    
    Args:
        area_gdf: Study area polygon
        terrain_raster: Path to elevation/terrain raster
        water_bodies: GeoDataFrame of water features
        roads: GeoDataFrame of road network
        
    Returns:
        GeoDataFrame of natural boundary features
    """
    boundaries = []
    
    # Water body boundaries
    if water_bodies is not None:
        for _, water in water_bodies.iterrows():
            if water.geometry.area > 10000:  # Significant water bodies only
                boundaries.append({
                    'geometry': water.geometry,
                    'boundary_type': 'water',
                    'barrier_strength': 0.9  # Strong barrier
                })
    
    # Major road boundaries  
    if roads is not None:
        major_roads = roads[roads.get('highway', '').isin(['motorway', 'trunk', 'primary'])]
        for _, road in major_roads.iterrows():
            boundaries.append({
                'geometry': road.geometry.buffer(50),  # 50m buffer
                'boundary_type': 'major_road',
                'barrier_strength': 0.7
            })
    
    # Terrain boundaries (requires elevation data)
    if terrain_raster is not None:
        try:
            # This would require more sophisticated terrain analysis
            # For now, placeholder for ridge/valley detection
            pass
        except Exception as e:
            print(f"Could not process terrain data: {e}")
    
    if boundaries:
        return gpd.GeoDataFrame(boundaries, crs=area_gdf.crs)
    else:
        # Return empty GeoDataFrame with proper schema
        return gpd.GeoDataFrame(columns=['geometry', 'boundary_type', 'barrier_strength'], crs=area_gdf.crs) 