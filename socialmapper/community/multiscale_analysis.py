"""
Multi-Scale Community Analysis

This module provides tools for analyzing communities at multiple spatial and temporal scales,
enabling detection of nested community structures and evolution patterns over time.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from typing import Dict, List, Tuple, Optional, Union, Any
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import unary_union
import json
from datetime import datetime, timedelta
import warnings

# Import community detection modules
from .spatial_clustering import CommunityBoundaryDetector
try:
    from .graph_neural_nets import GNNCommunityDetector
except ImportError:
    GNNCommunityDetector = None

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

try:
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class MultiScaleCommunityAnalyzer:
    """
    Analyzes communities across multiple spatial scales using hierarchical clustering
    and scale-adaptive algorithms.
    """
    
    def __init__(self, 
                 scales: List[Dict[str, Any]] = None,
                 temporal_window: Optional[int] = None):
        """
        Initialize multi-scale community analyzer.
        
        Args:
            scales: List of scale configurations, each with parameters for different spatial scales
            temporal_window: Number of time periods to analyze (for temporal analysis)
        """
        self.scales = scales or [
            {'name': 'micro', 'min_cluster_size': 5, 'distance_threshold': 100, 'description': 'Building clusters'},
            {'name': 'neighborhood', 'min_cluster_size': 20, 'distance_threshold': 500, 'description': 'Neighborhoods'},
            {'name': 'district', 'min_cluster_size': 100, 'distance_threshold': 2000, 'description': 'Districts'},
            {'name': 'macro', 'min_cluster_size': 500, 'distance_threshold': 5000, 'description': 'Large areas'}
        ]
        
        self.temporal_window = temporal_window
        self.analysis_history = []
        
    def analyze_multiscale_communities(self, 
                                     buildings_gdf: gpd.GeoDataFrame,
                                     method: str = 'hierarchical',
                                     include_gnn: bool = False) -> Dict[str, gpd.GeoDataFrame]:
        """
        Analyze communities at multiple spatial scales.
        
        Args:
            buildings_gdf: GeoDataFrame containing building polygons
            method: Analysis method ('hierarchical', 'parallel', 'adaptive')
            include_gnn: Whether to include GNN analysis
            
        Returns:
            Dictionary mapping scale names to community analysis results
        """
        results = {}
        
        if method == 'hierarchical':
            results = self._hierarchical_analysis(buildings_gdf, include_gnn)
        elif method == 'parallel':
            results = self._parallel_analysis(buildings_gdf, include_gnn)
        elif method == 'adaptive':
            results = self._adaptive_analysis(buildings_gdf, include_gnn)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Add metadata
        for scale_name, result_gdf in results.items():
            result_gdf['analysis_timestamp'] = datetime.now()
            result_gdf['scale_level'] = scale_name
            
        return results
    
    def _hierarchical_analysis(self, 
                             buildings_gdf: gpd.GeoDataFrame,
                             include_gnn: bool = False) -> Dict[str, gpd.GeoDataFrame]:
        """
        Perform hierarchical community analysis from fine to coarse scales.
        """
        results = {}
        previous_communities = None
        
        for scale_config in self.scales:
            scale_name = scale_config['name']
            
            # Create detector with scale-specific parameters
            detector = CommunityBoundaryDetector(
                min_cluster_size=scale_config['min_cluster_size'],
                cluster_selection_epsilon=scale_config['distance_threshold'] / 10000
            )
            
            # Detect communities at this scale
            communities = detector.detect_housing_developments(buildings_gdf)
            
            # If we have previous scale results, create hierarchical relationships
            if previous_communities is not None:
                communities = self._create_hierarchical_relationships(
                    communities, previous_communities, scale_name
                )
            
            # Add GNN analysis if requested
            if include_gnn and GNNCommunityDetector is not None:
                try:
                    gnn_detector = GNNCommunityDetector()
                    gnn_results = gnn_detector.detect_communities(buildings_gdf)
                    
                    # Merge GNN results
                    communities['gnn_community_id'] = gnn_results['community_id']
                    communities['gnn_confidence'] = gnn_results['confidence']
                except Exception as e:
                    warnings.warn(f"GNN analysis failed for scale {scale_name}: {e}")
            
            # Add scale-specific metrics
            communities = self._add_scale_metrics(communities, scale_config)
            
            results[scale_name] = communities
            previous_communities = communities
            
        return results
    
    def _parallel_analysis(self, 
                         buildings_gdf: gpd.GeoDataFrame,
                         include_gnn: bool = False) -> Dict[str, gpd.GeoDataFrame]:
        """
        Perform parallel community analysis at all scales independently.
        """
        results = {}
        
        for scale_config in self.scales:
            scale_name = scale_config['name']
            
            # Create detector with scale-specific parameters
            detector = CommunityBoundaryDetector(
                min_cluster_size=scale_config['min_cluster_size'],
                cluster_selection_epsilon=scale_config['distance_threshold'] / 10000
            )
            
            # Detect communities
            communities = detector.detect_housing_developments(buildings_gdf)
            communities = self._add_scale_metrics(communities, scale_config)
            
            results[scale_name] = communities
            
        return results
    
    def _adaptive_analysis(self, 
                         buildings_gdf: gpd.GeoDataFrame,
                         include_gnn: bool = False) -> Dict[str, gpd.GeoDataFrame]:
        """
        Perform adaptive analysis that selects optimal scale based on data characteristics.
        """
        # Calculate data characteristics to guide scale selection
        building_density = len(buildings_gdf) / buildings_gdf.total_bounds.area if hasattr(buildings_gdf, 'total_bounds') else 1
        avg_building_size = buildings_gdf.geometry.area.mean()
        
        # Adapt scales based on data characteristics
        adapted_scales = []
        for scale_config in self.scales:
            adapted_config = scale_config.copy()
            
            # Adjust parameters based on building density
            if building_density > 0.001:  # High density
                adapted_config['min_cluster_size'] *= 2
                adapted_config['distance_threshold'] *= 0.5
            elif building_density < 0.0001:  # Low density
                adapted_config['min_cluster_size'] = max(3, adapted_config['min_cluster_size'] // 2)
                adapted_config['distance_threshold'] *= 2
                
            adapted_scales.append(adapted_config)
        
        # Run analysis with adapted parameters
        self.scales = adapted_scales
        return self._hierarchical_analysis(buildings_gdf, include_gnn)
    
    def _create_hierarchical_relationships(self, 
                                         current_communities: gpd.GeoDataFrame,
                                         parent_communities: gpd.GeoDataFrame,
                                         scale_name: str) -> gpd.GeoDataFrame:
        """
        Create hierarchical relationships between scales.
        """
        # Map each building to its parent community
        parent_mapping = {}
        
        for idx, building in current_communities.iterrows():
            building_geom = building.geometry
            
            # Find parent community
            parent_candidates = parent_communities[
                parent_communities.geometry.intersects(building_geom)
            ]
            
            if len(parent_candidates) > 0:
                # Use the parent with largest overlap
                max_overlap = 0
                parent_id = None
                
                for parent_idx, parent in parent_candidates.iterrows():
                    overlap = building_geom.intersection(parent.geometry).area
                    if overlap > max_overlap:
                        max_overlap = overlap
                        parent_id = parent.get('cluster_id', parent_idx)
                
                parent_mapping[idx] = parent_id
            else:
                parent_mapping[idx] = -1  # No parent
        
        # Add parent information
        current_communities['parent_community_id'] = current_communities.index.map(parent_mapping)
        
        return current_communities
    
    def _add_scale_metrics(self, 
                          communities: gpd.GeoDataFrame,
                          scale_config: Dict[str, Any]) -> gpd.GeoDataFrame:
        """
        Add scale-specific metrics to community analysis results.
        """
        # Calculate scale-specific metrics
        scale_metrics = {}
        
        for cluster_id in communities['cluster_id'].unique():
            if cluster_id == -1:  # Skip noise
                continue
                
            cluster_buildings = communities[communities['cluster_id'] == cluster_id]
            
            # Basic metrics
            metrics = {
                'building_count': len(cluster_buildings),
                'total_area': cluster_buildings.geometry.area.sum(),
                'avg_building_area': cluster_buildings.geometry.area.mean(),
                'area_std': cluster_buildings.geometry.area.std(),
                'compactness': self._calculate_cluster_compactness(cluster_buildings),
                'density_score': len(cluster_buildings) / cluster_buildings.geometry.area.sum() * 1000000
            }
            
            scale_metrics[cluster_id] = metrics
        
        # Add metrics to dataframe
        for metric_name in ['building_count', 'total_area', 'avg_building_area', 
                           'compactness', 'density_score']:
            communities[f'scale_{metric_name}'] = communities['cluster_id'].map(
                lambda x: scale_metrics.get(x, {}).get(metric_name, 0)
            )
        
        return communities
    
    def _calculate_cluster_compactness(self, cluster_buildings: gpd.GeoDataFrame) -> float:
        """
        Calculate compactness score for a cluster of buildings.
        """
        if len(cluster_buildings) < 2:
            return 1.0
            
        # Create convex hull
        union_geom = unary_union(cluster_buildings.geometry)
        if hasattr(union_geom, 'convex_hull'):
            convex_hull = union_geom.convex_hull
            compactness = union_geom.area / convex_hull.area
        else:
            compactness = 1.0
            
        return compactness
    
    def analyze_temporal_dynamics(self, 
                                temporal_data: List[Tuple[datetime, gpd.GeoDataFrame]],
                                track_communities: bool = True) -> pd.DataFrame:
        """
        Analyze how communities evolve over time.
        
        Args:
            temporal_data: List of (timestamp, buildings_gdf) tuples
            track_communities: Whether to track community persistence
            
        Returns:
            DataFrame with temporal community evolution metrics
        """
        temporal_results = []
        community_tracker = {} if track_communities else None
        
        for i, (timestamp, buildings_gdf) in enumerate(temporal_data):
            # Analyze communities at this time point
            multiscale_results = self.analyze_multiscale_communities(buildings_gdf)
            
            # Calculate temporal metrics
            for scale_name, communities in multiscale_results.items():
                scale_stats = {
                    'timestamp': timestamp,
                    'scale': scale_name,
                    'total_communities': len(communities['cluster_id'].unique()) - 1,  # Exclude noise
                    'total_buildings': len(communities),
                    'avg_community_size': communities.groupby('cluster_id').size().mean(),
                    'community_size_std': communities.groupby('cluster_id').size().std(),
                    'largest_community': communities.groupby('cluster_id').size().max(),
                }
                
                # Track community persistence if enabled
                if track_communities and i > 0:
                    persistence_metrics = self._calculate_persistence_metrics(
                        communities, community_tracker, scale_name
                    )
                    scale_stats.update(persistence_metrics)
                
                # Update community tracker
                if track_communities:
                    community_tracker[f"{scale_name}_{i}"] = communities
                
                temporal_results.append(scale_stats)
        
        return pd.DataFrame(temporal_results)
    
    def _calculate_persistence_metrics(self, 
                                     current_communities: gpd.GeoDataFrame,
                                     community_tracker: Dict,
                                     scale_name: str) -> Dict[str, float]:
        """
        Calculate community persistence metrics between time periods.
        """
        # Find the most recent previous analysis for this scale
        previous_key = None
        for key in reversed(list(community_tracker.keys())):
            if key.startswith(scale_name):
                previous_key = key
                break
        
        if previous_key is None:
            return {}
        
        previous_communities = community_tracker[previous_key]
        
        # Calculate overlap between current and previous communities
        current_clusters = current_communities.groupby('cluster_id')
        previous_clusters = previous_communities.groupby('cluster_id')
        
        overlap_scores = []
        
        for current_id, current_group in current_clusters:
            if current_id == -1:  # Skip noise
                continue
                
            max_overlap = 0
            
            for previous_id, previous_group in previous_clusters:
                if previous_id == -1:  # Skip noise
                    continue
                
                # Calculate spatial overlap
                current_union = unary_union(current_group.geometry)
                previous_union = unary_union(previous_group.geometry)
                
                if current_union.intersects(previous_union):
                    intersection = current_union.intersection(previous_union)
                    overlap = intersection.area / current_union.area
                    max_overlap = max(max_overlap, overlap)
            
            overlap_scores.append(max_overlap)
        
        # Calculate persistence metrics
        metrics = {
            'avg_persistence': np.mean(overlap_scores) if overlap_scores else 0,
            'persistence_std': np.std(overlap_scores) if overlap_scores else 0,
            'highly_persistent_communities': sum(1 for score in overlap_scores if score > 0.7),
            'new_communities': sum(1 for score in overlap_scores if score < 0.3),
        }
        
        return metrics
    
    def export_multiscale_results(self, 
                                results: Dict[str, gpd.GeoDataFrame],
                                output_dir: str,
                                format: str = 'geojson') -> List[str]:
        """
        Export multi-scale analysis results to files.
        
        Args:
            results: Multi-scale analysis results
            output_dir: Output directory path
            format: Export format ('geojson', 'shapefile', 'gpkg')
            
        Returns:
            List of created file paths
        """
        import os
        
        created_files = []
        
        for scale_name, communities_gdf in results.items():
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"communities_{scale_name}_{timestamp}"
            
            if format == 'geojson':
                filepath = os.path.join(output_dir, f"{filename}.geojson")
                communities_gdf.to_file(filepath, driver='GeoJSON')
            elif format == 'shapefile':
                filepath = os.path.join(output_dir, f"{filename}.shp")
                communities_gdf.to_file(filepath, driver='ESRI Shapefile')
            elif format == 'gpkg':
                filepath = os.path.join(output_dir, f"{filename}.gpkg")
                communities_gdf.to_file(filepath, driver='GPKG')
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            created_files.append(filepath)
        
        # Create summary metadata file
        metadata = {
            'analysis_timestamp': datetime.now().isoformat(),
            'scales_analyzed': list(results.keys()),
            'total_buildings': len(next(iter(results.values()))),
            'analysis_parameters': {
                'scales': self.scales,
                'temporal_window': self.temporal_window
            }
        }
        
        metadata_file = os.path.join(output_dir, f"multiscale_metadata_{timestamp}.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        created_files.append(metadata_file)
        
        return created_files


def analyze_communities_multiscale(buildings_gdf: gpd.GeoDataFrame,
                                 scales: Optional[List[Dict]] = None,
                                 method: str = 'hierarchical',
                                 include_gnn: bool = False) -> Dict[str, gpd.GeoDataFrame]:
    """
    Convenience function for multi-scale community analysis.
    
    Args:
        buildings_gdf: GeoDataFrame containing building polygons
        scales: Custom scale configurations
        method: Analysis method ('hierarchical', 'parallel', 'adaptive')
        include_gnn: Whether to include GNN analysis
        
    Returns:
        Dictionary mapping scale names to community analysis results
    """
    analyzer = MultiScaleCommunityAnalyzer(scales=scales)
    return analyzer.analyze_multiscale_communities(
        buildings_gdf, method=method, include_gnn=include_gnn
    ) 