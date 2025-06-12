"""
Community Boundary Detection Integration

This module integrates spatial clustering, computer vision, and demographic data
to discover organic community boundaries that reflect how people actually live
and interact within spatial environments.
"""

from typing import List, Optional

import geopandas as gpd
import networkx as nx
import numpy as np
from shapely.ops import unary_union
from sklearn.cluster import DBSCAN, SpectralClustering
from sklearn.preprocessing import StandardScaler

from .computer_vision import SatelliteImageAnalyzer, analyze_satellite_imagery

# Import our community detection modules
from .spatial_clustering import CommunityBoundaryDetector, detect_housing_developments

# Try importing graph analysis libraries
try:
    import community as community_louvain

    LOUVAIN_AVAILABLE = True
except ImportError:
    LOUVAIN_AVAILABLE = False

try:
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial import cKDTree

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


class IntegratedCommunityDetector:
    """
    Integrated system for detecting organic community boundaries using multiple signals:
    - Spatial patterns in building arrangements
    - Computer vision analysis of satellite imagery
    - Demographic and socioeconomic similarity
    - Network analysis of spatial relationships
    """

    def __init__(
        self,
        spatial_weight: float = 0.4,
        visual_weight: float = 0.3,
        demographic_weight: float = 0.3,
        min_community_size: int = 50,
        boundary_buffer: float = 100,
    ):
        """
        Initialize the integrated community detector.

        Args:
            spatial_weight: Weight for spatial clustering features
            visual_weight: Weight for computer vision features
            demographic_weight: Weight for demographic similarity
            min_community_size: Minimum size for a valid community
            boundary_buffer: Buffer distance for boundary smoothing (meters)
        """
        self.spatial_weight = spatial_weight
        self.visual_weight = visual_weight
        self.demographic_weight = demographic_weight
        self.min_community_size = min_community_size
        self.boundary_buffer = boundary_buffer

        # Initialize component detectors
        self.spatial_detector = CommunityBoundaryDetector()
        self.visual_analyzer = SatelliteImageAnalyzer()

        # Normalize weights
        total_weight = spatial_weight + visual_weight + demographic_weight
        self.spatial_weight /= total_weight
        self.visual_weight /= total_weight
        self.demographic_weight /= total_weight

    def discover_community_boundaries(
        self,
        buildings_gdf: gpd.GeoDataFrame,
        satellite_image: Optional[str] = None,
        demographic_data: Optional[gpd.GeoDataFrame] = None,
        existing_boundaries: Optional[gpd.GeoDataFrame] = None,
    ) -> gpd.GeoDataFrame:
        """
        Discover organic community boundaries using integrated multi-modal analysis.

        Args:
            buildings_gdf: Building footprints
            satellite_image: Path to satellite imagery
            demographic_data: Census or demographic data at small area level
            existing_boundaries: Existing administrative boundaries for comparison

        Returns:
            GeoDataFrame containing discovered community boundaries
        """
        print("🏘️ Starting integrated community boundary detection...")

        # Step 1: Spatial pattern analysis
        print("📍 Analyzing spatial patterns...")
        spatial_features = self._extract_spatial_features(buildings_gdf)

        # Step 2: Computer vision analysis (if satellite data available)
        visual_features = None
        if satellite_image is not None:
            print("🛰️ Analyzing satellite imagery...")
            visual_features = self._extract_visual_features(satellite_image, buildings_gdf)

        # Step 3: Demographic similarity analysis (if demographic data available)
        demographic_features = None
        if demographic_data is not None:
            print("👥 Analyzing demographic patterns...")
            demographic_features = self._extract_demographic_features(
                demographic_data, buildings_gdf
            )

        # Step 4: Integrate all features
        print("🔗 Integrating multi-modal features...")
        combined_features = self._combine_features(
            spatial_features, visual_features, demographic_features
        )

        # Step 5: Community detection using multiple algorithms
        print("🎯 Detecting community boundaries...")
        communities = self._detect_communities(combined_features, buildings_gdf)

        # Step 6: Post-process and validate boundaries
        print("✨ Refining and validating boundaries...")
        refined_boundaries = self._refine_boundaries(
            communities, buildings_gdf, existing_boundaries
        )

        print(f"✅ Discovered {len(refined_boundaries)} community boundaries")
        return refined_boundaries

    def _extract_spatial_features(self, buildings_gdf: gpd.GeoDataFrame) -> np.ndarray:
        """Extract spatial clustering features from building patterns."""
        return self.spatial_detector.extract_building_features(buildings_gdf)

    def _extract_visual_features(
        self, satellite_image: Optional[str], buildings_gdf: gpd.GeoDataFrame
    ) -> np.ndarray:
        """Extract visual features from satellite imagery using real data fetching."""
        print("  📸 Extracting visual features from satellite imagery...")

        # Get bounding box of buildings
        bounds = buildings_gdf.total_bounds  # minx, miny, maxx, maxy

        # Convert bounds to WGS84 if needed
        if buildings_gdf.crs != "EPSG:4326":
            buildings_geo = buildings_gdf.to_crs("EPSG:4326")
            bounds = buildings_geo.total_bounds

        # Analyze satellite imagery with automatic data fetching
        try:
            bounds_tuple = (bounds[0], bounds[1], bounds[2], bounds[3])  # minx, miny, maxx, maxy
            patches_gdf = analyze_satellite_imagery(
                bounds=bounds_tuple,
                imagery_type="naip",  # Prefer NAIP for high resolution
                image_path=satellite_image,  # Use provided path if available
            )

            # Spatial join to associate image features with buildings
            # Convert buildings to same CRS as patches if needed
            if buildings_gdf.crs != patches_gdf.crs:
                buildings_for_join = buildings_gdf.to_crs(patches_gdf.crs)
            else:
                buildings_for_join = buildings_gdf

            buildings_with_visual = gpd.sjoin_nearest(buildings_for_join, patches_gdf, how="left")

            # Extract visual feature vectors
            visual_features = []
            for _, building in buildings_with_visual.iterrows():
                # Create feature vector from land use classification
                land_use = building.get("land_use", "unknown")
                analysis_method = building.get("analysis_method", "unknown")

                # One-hot encode land use types with confidence weighting
                confidence_multiplier = 1.0 if analysis_method == "real_satellite_imagery" else 0.5

                land_use_features = {
                    "dense_residential": (
                        confidence_multiplier if land_use == "dense_residential" else 0
                    ),
                    "suburban": confidence_multiplier if land_use == "suburban" else 0,
                    "mixed_urban": confidence_multiplier if land_use == "mixed_urban" else 0,
                    "open_space": confidence_multiplier if land_use == "open_space" else 0,
                    "agricultural": confidence_multiplier if land_use == "agricultural" else 0,
                    "water_forest": confidence_multiplier if land_use == "water_forest" else 0,
                }

                visual_features.append(list(land_use_features.values()))

            print(f"    ✅ Extracted visual features for {len(visual_features)} buildings")
            return np.array(visual_features)

        except Exception as e:
            print(f"    ⚠️ Could not extract visual features: {e}")
            print("    🔄 Using placeholder visual features...")
            return np.zeros((len(buildings_gdf), 6))  # Fallback to zeros

    def _extract_demographic_features(
        self, demographic_data: gpd.GeoDataFrame, buildings_gdf: gpd.GeoDataFrame
    ) -> np.ndarray:
        """Extract demographic similarity features."""
        # Spatial join to associate demographic data with buildings
        buildings_with_demo = gpd.sjoin(
            buildings_gdf, demographic_data, how="left", predicate="within"
        )

        # Select relevant demographic columns (adjust based on your data)
        demo_columns = [
            col
            for col in demographic_data.columns
            if col not in ["geometry"] and demographic_data[col].dtype in ["int64", "float64"]
        ]

        if len(demo_columns) == 0:
            return np.zeros((len(buildings_gdf), 1))

        # Extract demographic features
        demo_features = buildings_with_demo[demo_columns].fillna(0).values

        # Normalize features
        scaler = StandardScaler()
        demo_features_scaled = scaler.fit_transform(demo_features)

        return demo_features_scaled

    def _combine_features(
        self,
        spatial_features: np.ndarray,
        visual_features: Optional[np.ndarray] = None,
        demographic_features: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Combine multi-modal features with appropriate weighting."""
        # Start with spatial features
        combined = spatial_features * self.spatial_weight

        # Add visual features if available
        if visual_features is not None:
            # Normalize visual features to same scale as spatial
            visual_normalized = StandardScaler().fit_transform(visual_features)
            combined = np.concatenate([combined, visual_normalized * self.visual_weight], axis=1)

        # Add demographic features if available
        if demographic_features is not None:
            combined = np.concatenate(
                [combined, demographic_features * self.demographic_weight], axis=1
            )

        return combined

    def _detect_communities(
        self, features: np.ndarray, buildings_gdf: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        """Detect communities using ensemble of clustering algorithms."""

        # Method 1: HDBSCAN clustering
        clusters_hdbscan = self._cluster_hdbscan(features)

        # Method 2: Spectral clustering
        clusters_spectral = self._cluster_spectral(features, buildings_gdf)

        # Method 3: Network-based community detection
        clusters_network = self._cluster_network(features, buildings_gdf)

        # Combine clustering results using ensemble voting
        final_clusters = self._ensemble_clustering(
            [clusters_hdbscan, clusters_spectral, clusters_network]
        )

        # Add cluster labels to buildings
        buildings_clustered = buildings_gdf.copy()
        buildings_clustered["community_id"] = final_clusters

        return buildings_clustered

    def _cluster_hdbscan(self, features: np.ndarray) -> np.ndarray:
        """Density-based clustering using HDBSCAN."""
        try:
            from hdbscan import HDBSCAN

            clusterer = HDBSCAN(min_cluster_size=self.min_community_size, min_samples=5)
            return clusterer.fit_predict(features)
        except ImportError:
            # Fallback to DBSCAN
            clusterer = DBSCAN(eps=0.5, min_samples=self.min_community_size // 4)
            return clusterer.fit_predict(features)

    def _cluster_spectral(
        self, features: np.ndarray, buildings_gdf: gpd.GeoDataFrame
    ) -> np.ndarray:
        """Spectral clustering based on spatial and feature similarity."""
        if len(features) < 10:
            return np.zeros(len(features))

        # Estimate number of clusters
        n_clusters = max(2, min(10, len(features) // self.min_community_size))

        clusterer = SpectralClustering(n_clusters=n_clusters, random_state=42)
        return clusterer.fit_predict(features)

    def _cluster_network(self, features: np.ndarray, buildings_gdf: gpd.GeoDataFrame) -> np.ndarray:
        """Network-based community detection using spatial connectivity."""
        if not SCIPY_AVAILABLE:
            return np.zeros(len(features))

        # Create spatial network
        centroids = buildings_gdf.geometry.centroid
        coords = np.array([[p.x, p.y] for p in centroids])

        # Build KD-tree for nearest neighbor search
        tree = cKDTree(coords)

        # Create graph
        G = nx.Graph()
        for i, coord in enumerate(coords):
            G.add_node(i, pos=coord)

        # Add edges based on spatial proximity and feature similarity
        for i in range(len(coords)):
            # Find nearby buildings (within 200m)
            neighbors = tree.query_ball_point(coords[i], r=200)

            for j in neighbors:
                if i != j:
                    # Calculate feature similarity
                    feature_dist = np.linalg.norm(features[i] - features[j])
                    spatial_dist = np.linalg.norm(coords[i] - coords[j])

                    # Add edge if similar enough
                    combined_dist = 0.7 * feature_dist + 0.3 * spatial_dist / 200
                    if combined_dist < 1.0:
                        G.add_edge(i, j, weight=1.0 - combined_dist)

        # Detect communities
        if LOUVAIN_AVAILABLE and len(G.nodes()) > 0:
            try:
                partition = community_louvain.best_partition(G)
                return np.array([partition.get(i, -1) for i in range(len(features))])
            except:
                pass

        # Fallback: use connected components
        communities = list(nx.connected_components(G))
        labels = np.full(len(features), -1)
        for comm_id, community in enumerate(communities):
            for node in community:
                labels[node] = comm_id

        return labels

    def _ensemble_clustering(self, cluster_results: List[np.ndarray]) -> np.ndarray:
        """Combine multiple clustering results using ensemble voting."""
        n_samples = len(cluster_results[0])

        # Simple majority voting
        final_labels = np.zeros(n_samples, dtype=int)

        for i in range(n_samples):
            # Get labels from all methods
            labels = [result[i] for result in cluster_results if result[i] != -1]

            if len(labels) > 0:
                # Use most common label
                unique_labels, counts = np.unique(labels, return_counts=True)
                final_labels[i] = unique_labels[np.argmax(counts)]
            else:
                final_labels[i] = -1  # No consensus

        return final_labels

    def _refine_boundaries(
        self,
        communities: gpd.GeoDataFrame,
        buildings_gdf: gpd.GeoDataFrame,
        existing_boundaries: Optional[gpd.GeoDataFrame] = None,
    ) -> gpd.GeoDataFrame:
        """Refine and validate community boundaries."""
        boundaries = []

        unique_communities = communities["community_id"].unique()
        unique_communities = unique_communities[unique_communities != -1]

        for comm_id in unique_communities:
            community_buildings = communities[communities["community_id"] == comm_id]

            if len(community_buildings) < self.min_community_size:
                continue

            # Create boundary polygon
            building_points = [geom.centroid for geom in community_buildings.geometry]

            # Use alpha shape or convex hull for boundary
            try:
                import alphashape

                coords = [(p.x, p.y) for p in building_points]
                boundary = alphashape.alphashape(coords, 0.1)

                if boundary.is_empty or not boundary.is_valid:
                    raise ValueError("Invalid alpha shape")

            except:
                # Fallback to buffered union
                buffered_buildings = community_buildings.geometry.buffer(self.boundary_buffer)
                boundary = unary_union(buffered_buildings).convex_hull

            # Calculate community characteristics
            total_area = community_buildings.geometry.area.sum()
            avg_building_size = community_buildings.geometry.area.mean()
            building_density = len(community_buildings) / boundary.area * 1000000  # per km²

            # Classify community type
            community_type = self._classify_community_type(community_buildings, building_density)

            boundaries.append(
                {
                    "community_id": comm_id,
                    "geometry": boundary,
                    "community_type": community_type,
                    "building_count": len(community_buildings),
                    "total_building_area": total_area,
                    "avg_building_size": avg_building_size,
                    "density": building_density,
                    "boundary_area": boundary.area,
                }
            )

        result_gdf = gpd.GeoDataFrame(boundaries, crs=buildings_gdf.crs)

        # Validate against existing boundaries if available
        if existing_boundaries is not None:
            result_gdf = self._validate_against_existing(result_gdf, existing_boundaries)

        return result_gdf

    def _classify_community_type(
        self, community_buildings: gpd.GeoDataFrame, density: float
    ) -> str:
        """Classify the type of community based on characteristics."""
        avg_size = community_buildings.geometry.area.mean()
        size_std = community_buildings.geometry.area.std()

        # Classification logic
        if density > 1000:  # High density
            return "urban_core"
        elif density > 500:
            if size_std / avg_size < 0.3:  # Uniform sizes
                return "planned_development"
            else:
                return "mixed_urban"
        elif density > 100:
            return "suburban_residential"
        else:
            return "rural_residential"

    def _validate_against_existing(
        self, detected_boundaries: gpd.GeoDataFrame, existing_boundaries: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        """Validate detected boundaries against existing administrative boundaries."""
        validated = detected_boundaries.copy()

        # Calculate overlap with existing boundaries
        overlaps = []
        for _, detected in detected_boundaries.iterrows():
            max_overlap = 0
            best_match = None

            for _, existing in existing_boundaries.iterrows():
                try:
                    intersection = detected.geometry.intersection(existing.geometry)
                    overlap_ratio = intersection.area / detected.geometry.area

                    if overlap_ratio > max_overlap:
                        max_overlap = overlap_ratio
                        best_match = existing.get("name", "unknown")
                except:
                    overlap_ratio = 0

            overlaps.append(max_overlap)

        validated["admin_overlap"] = overlaps
        validated["confidence"] = np.where(
            np.array(overlaps) > 0.3, "high", np.where(np.array(overlaps) > 0.1, "medium", "low")
        )

        return validated


# High-level interface functions


def discover_community_boundaries(
    buildings_gdf: gpd.GeoDataFrame,
    satellite_image: Optional[str] = None,
    demographic_data: Optional[gpd.GeoDataFrame] = None,
    existing_boundaries: Optional[gpd.GeoDataFrame] = None,
    **kwargs,
) -> gpd.GeoDataFrame:
    """
    High-level function to discover organic community boundaries.

    Args:
        buildings_gdf: Building footprints
        satellite_image: Path to satellite imagery
        demographic_data: Census/demographic data
        existing_boundaries: Administrative boundaries for validation
        **kwargs: Additional parameters for detector

    Returns:
        GeoDataFrame with discovered community boundaries
    """
    print("🏘️ Starting community boundary detection...")

    # Basic spatial clustering for now

    clustered_buildings, boundaries = detect_housing_developments(buildings_gdf)

    print(f"✅ Discovered {len(boundaries)} community boundaries")
    return boundaries


def validate_boundaries_with_demographics(
    boundaries_gdf: gpd.GeoDataFrame, demographic_data: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """
    Validate detected boundaries using demographic homogeneity analysis.
    """
    validated = boundaries_gdf.copy()
    validated["demographic_homogeneity"] = 0.5  # Placeholder
    return validated


def merge_administrative_and_organic_boundaries(
    administrative_gdf: gpd.GeoDataFrame,
    organic_gdf: gpd.GeoDataFrame,
    merge_threshold: float = 0.5,
) -> gpd.GeoDataFrame:
    """
    Merge administrative and organically-detected boundaries.
    """
    return administrative_gdf  # Placeholder
