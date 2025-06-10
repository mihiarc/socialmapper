"""
Computer Vision for Community Boundary Detection

This module uses computer vision and deep learning techniques to analyze
satellite imagery and extract features relevant to community boundary detection.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from PIL import Image
import cv2
import rasterio
from rasterio.windows import Window
from rasterio.transform import from_bounds
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from typing import Dict, List, Tuple, Optional, Union, Any
import warnings

# Try importing deep learning libraries
try:
    import torch
    import torch.nn as nn
    import torchvision.transforms as transforms
    from torchvision.models import resnet50, ResNet50_Weights
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import tensorflow as tf
    from tensorflow.keras.applications import ResNet50
    from tensorflow.keras.applications.resnet50 import preprocess_input
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

# Try importing specialized computer vision libraries
try:
    from skimage import filters, segmentation, measure, morphology
    from skimage.feature import local_binary_pattern, graycomatrix, graycoprops
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False


class SatelliteImageAnalyzer:
    """
    Computer vision-based analysis of satellite imagery for community detection.
    """
    
    def __init__(self, 
                 patch_size: int = 512,
                 overlap: float = 0.1,
                 use_deep_features: bool = True):
        """
        Initialize the satellite image analyzer.
        
        Args:
            patch_size: Size of image patches for analysis
            overlap: Overlap between patches (0-1)
            use_deep_features: Whether to use deep learning features
        """
        self.patch_size = patch_size
        self.overlap = overlap
        self.use_deep_features = use_deep_features
        
        # Initialize feature extractor
        if use_deep_features and TORCH_AVAILABLE:
            self.feature_extractor = self._initialize_torch_model()
        elif use_deep_features and TF_AVAILABLE:
            self.feature_extractor = self._initialize_tf_model()
        else:
            self.feature_extractor = None
            self.use_deep_features = False
    
    def _initialize_torch_model(self):
        """Initialize PyTorch-based feature extractor."""
        model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
        # Remove the final classification layer
        model = nn.Sequential(*list(model.children())[:-1])
        model.eval()
        return model
    
    def _initialize_tf_model(self):
        """Initialize TensorFlow-based feature extractor."""
        base_model = ResNet50(weights='imagenet', include_top=False, pooling='avg')
        return base_model
    
    def extract_patches(self, 
                       image_array: np.ndarray,
                       bounds: Tuple[float, float, float, float]) -> List[Dict[str, Any]]:
        """
        Extract overlapping patches from satellite imagery.
        
        Args:
            image_array: Satellite image as numpy array (H, W, C)
            bounds: Geographic bounds (minx, miny, maxx, maxy)
            
        Returns:
            List of patch dictionaries with image data and metadata
        """
        height, width = image_array.shape[:2]
        stride = int(self.patch_size * (1 - self.overlap))
        
        patches = []
        patch_id = 0
        
        for y in range(0, height - self.patch_size + 1, stride):
            for x in range(0, width - self.patch_size + 1, stride):
                # Extract patch
                patch = image_array[y:y+self.patch_size, x:x+self.patch_size]
                
                # Calculate geographic bounds of patch
                x_ratio = x / width
                y_ratio = y / height
                width_ratio = self.patch_size / width
                height_ratio = self.patch_size / height
                
                minx = bounds[0] + (bounds[2] - bounds[0]) * x_ratio
                maxx = bounds[0] + (bounds[2] - bounds[0]) * (x_ratio + width_ratio)
                miny = bounds[1] + (bounds[3] - bounds[1]) * (1 - y_ratio - height_ratio)
                maxy = bounds[1] + (bounds[3] - bounds[1]) * (1 - y_ratio)
                
                patches.append({
                    'patch_id': patch_id,
                    'image': patch,
                    'bounds': (minx, miny, maxx, maxy),
                    'center_x': (minx + maxx) / 2,
                    'center_y': (miny + maxy) / 2,
                    'pixel_x': x + self.patch_size // 2,
                    'pixel_y': y + self.patch_size // 2
                })
                
                patch_id += 1
        
        return patches
    
    def extract_texture_features(self, image_patch: np.ndarray) -> np.ndarray:
        """
        Extract texture features from an image patch using traditional computer vision.
        
        Args:
            image_patch: RGB image patch
            
        Returns:
            Feature vector containing texture descriptors
        """
        if not SKIMAGE_AVAILABLE:
            # Fallback to basic features
            return self._extract_basic_features(image_patch)
        
        # Convert to grayscale
        if len(image_patch.shape) == 3:
            gray = cv2.cvtColor(image_patch, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_patch
        
        features = []
        
        # Local Binary Pattern features
        lbp = local_binary_pattern(gray, P=8, R=1, method='uniform')
        lbp_hist, _ = np.histogram(lbp.ravel(), bins=10, range=(0, 10))
        lbp_hist = lbp_hist.astype(float)
        lbp_hist /= (lbp_hist.sum() + 1e-7)  # Normalize
        features.extend(lbp_hist)
        
        # Gray-Level Co-occurrence Matrix (GLCM) features
        # Normalize to 8-bit range for GLCM computation to handle 16-bit Sentinel-2 data
        gray_normalized = ((gray - gray.min()) / (gray.max() - gray.min() + 1e-7) * 255).astype(np.uint8)
        glcm = graycomatrix(gray_normalized, distances=[1], angles=[0, 45, 90, 135], 
                           levels=256, symmetric=True, normed=True)
        
        # Extract GLCM properties
        contrast = graycoprops(glcm, 'contrast').flatten()
        dissimilarity = graycoprops(glcm, 'dissimilarity').flatten()
        homogeneity = graycoprops(glcm, 'homogeneity').flatten()
        energy = graycoprops(glcm, 'energy').flatten()
        
        features.extend(contrast)
        features.extend(dissimilarity)
        features.extend(homogeneity)
        features.extend(energy)
        
        # Statistical features
        features.extend([
            gray.mean(),
            gray.std(),
            np.percentile(gray, 25),
            np.percentile(gray, 75),
            gray.max() - gray.min()
        ])
        
        # Edge density
        edges = filters.sobel(gray)
        edge_density = (edges > filters.threshold_otsu(edges)).mean()
        features.append(edge_density)
        
        return np.array(features)
    
    def _extract_basic_features(self, image_patch: np.ndarray) -> np.ndarray:
        """Extract basic features when advanced libraries are not available."""
        if len(image_patch.shape) == 3:
            gray = cv2.cvtColor(image_patch, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_patch
        
        # Basic statistical features
        features = [
            gray.mean(),
            gray.std(),
            np.percentile(gray, 25),
            np.percentile(gray, 50),
            np.percentile(gray, 75),
            gray.max() - gray.min(),
        ]
        
        # Simple edge detection
        edges = cv2.Canny(gray, 50, 150)
        edge_density = edges.mean() / 255.0
        features.append(edge_density)
        
        # Color features (if RGB)
        if len(image_patch.shape) == 3:
            for channel in range(3):
                channel_data = image_patch[:, :, channel]
                features.extend([
                    channel_data.mean(),
                    channel_data.std()
                ])
        
        return np.array(features)
    
    def extract_deep_features(self, image_patch: np.ndarray) -> np.ndarray:
        """
        Extract deep learning features from image patch.
        
        Args:
            image_patch: RGB image patch
            
        Returns:
            Deep feature vector
        """
        if not self.use_deep_features or self.feature_extractor is None:
            return np.array([])
        
        # Resize patch to expected input size
        if TORCH_AVAILABLE and isinstance(self.feature_extractor, nn.Module):
            return self._extract_torch_features(image_patch)
        elif TF_AVAILABLE:
            return self._extract_tf_features(image_patch)
        else:
            return np.array([])
    
    def _extract_torch_features(self, image_patch: np.ndarray) -> np.ndarray:
        """Extract features using PyTorch model."""
        # Convert uint16 to uint8 for PIL compatibility
        if image_patch.dtype == np.uint16:
            # Normalize from 16-bit to 8-bit
            image_patch = (image_patch / 256).astype(np.uint8)
        elif image_patch.dtype != np.uint8:
            # Ensure proper data type
            image_patch = image_patch.astype(np.uint8)
        
        # Preprocess image
        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        input_tensor = transform(image_patch).unsqueeze(0)
        
        with torch.no_grad():
            features = self.feature_extractor(input_tensor)
            features = features.squeeze().numpy()
        
        return features
    
    def _extract_tf_features(self, image_patch: np.ndarray) -> np.ndarray:
        """Extract features using TensorFlow model."""
        # Resize and preprocess
        resized = cv2.resize(image_patch, (224, 224))
        preprocessed = preprocess_input(np.expand_dims(resized, axis=0))
        
        # Extract features
        features = self.feature_extractor.predict(preprocessed, verbose=0)
        return features.flatten()
    
    def classify_land_use(self, patches: List[Dict[str, Any]]) -> List[str]:
        """
        Classify land use type for image patches.
        
        Args:
            patches: List of image patches with metadata
            
        Returns:
            List of land use classifications
        """
        classifications = []
        
        for patch in patches:
            image = patch['image']
            
            # Extract features
            texture_features = self.extract_texture_features(image)
            
            if self.use_deep_features:
                deep_features = self.extract_deep_features(image)
                if len(deep_features) > 0:
                    combined_features = np.concatenate([texture_features, deep_features])
                else:
                    combined_features = texture_features
            else:
                combined_features = texture_features
            
            # Simple classification based on feature analysis
            # This is a placeholder - in practice, you'd train a classifier
            classification = self._classify_patch(combined_features, image)
            classifications.append(classification)
        
        return classifications
    
    def _classify_patch(self, features: np.ndarray, image: np.ndarray) -> str:
        """
        Classify a single patch based on its features.
        This is a simple heuristic-based classifier.
        """
        # Convert to grayscale for analysis
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Ensure uint8 for OpenCV operations
        if gray.dtype != np.uint8:
            if gray.dtype == np.uint16:
                # Normalize from 16-bit to 8-bit
                gray = (gray / 256).astype(np.uint8)
            else:
                gray = gray.astype(np.uint8)
        
        # Calculate basic statistics
        mean_intensity = gray.mean()
        std_intensity = gray.std()
        edge_density = cv2.Canny(gray, 50, 150).mean() / 255.0
        
        # Simple classification rules
        if edge_density > 0.1 and std_intensity > 30:
            if mean_intensity > 120:
                return 'dense_residential'
            else:
                return 'mixed_urban'
        elif edge_density > 0.05:
            return 'suburban'
        elif mean_intensity > 150:
            return 'open_space'
        elif mean_intensity < 80:
            return 'water_forest'
        else:
            return 'agricultural'


def analyze_satellite_imagery(bounds: Tuple[float, float, float, float],
                            patch_size: int = 512,
                            imagery_type: str = "naip",
                            image_path: Optional[str] = None,
                            cache_dir: Optional[str] = None) -> gpd.GeoDataFrame:
    """
    Analyze satellite imagery to extract land use and spatial patterns.
    
    This function has been updated to automatically fetch real satellite imagery
    using the geoai package integration.
    
    Args:
        bounds: Geographic bounds (minx, miny, maxx, maxy) in WGS84
        patch_size: Size of analysis patches
        imagery_type: Type of imagery to fetch ("naip", "sentinel2", "landsat")
        image_path: Optional direct path to satellite image file (overrides fetching)
        cache_dir: Directory for caching downloaded imagery
        
    Returns:
        GeoDataFrame with patch-level analysis results
    """
    # Try to import and use the satellite data fetcher
    try:
        from .satellite_data_fetcher import SatelliteDataFetcher, GEOAI_AVAILABLE
        
        if image_path is None:
            if not GEOAI_AVAILABLE:
                print("⚠️  geoai package not available - cannot fetch real satellite imagery")
                print("   Install with: pip install geoai-py")
                print("   Falling back to placeholder analysis...")
                return _create_placeholder_analysis(bounds, patch_size)
            
            # Fetch real satellite imagery
            print(f"🛰️  Fetching {imagery_type} satellite imagery for bounds {bounds}")
            fetcher = SatelliteDataFetcher(cache_dir=cache_dir)
            image_path = fetcher.get_best_imagery_for_bounds(
                bounds=bounds,
                imagery_type=imagery_type
            )
            
            if image_path is None:
                print(f"⚠️  No {imagery_type} imagery available for the specified bounds")
                print("   Falling back to placeholder analysis...")
                return _create_placeholder_analysis(bounds, patch_size)
            
            print(f"✅ Successfully obtained imagery: {image_path}")
        
    except ImportError as e:
        print(f"⚠️  Satellite data fetcher not available: {e}")
        if image_path is None:
            print("   Falling back to placeholder analysis...")
            return _create_placeholder_analysis(bounds, patch_size)
    
    # Load and analyze the satellite image
    try:
        with rasterio.open(image_path) as src:
            image_array = src.read([1, 2, 3])  # RGB bands
            image_array = np.transpose(image_array, (1, 2, 0))  # H,W,C format
            
            # Get actual bounds from the imagery if available
            if hasattr(src, 'bounds'):
                actual_bounds = (src.bounds.left, src.bounds.bottom, 
                               src.bounds.right, src.bounds.top)
            else:
                actual_bounds = bounds
    
        print(f"🔍 Analyzing satellite imagery with {image_array.shape} shape")
        
        # Initialize analyzer
        analyzer = SatelliteImageAnalyzer(patch_size=patch_size)
        
        # Extract patches
        patches = analyzer.extract_patches(image_array, actual_bounds)
        
        # Classify patches
        classifications = analyzer.classify_land_use(patches)
        
        # Create GeoDataFrame
        patch_data = []
        for i, (patch, classification) in enumerate(zip(patches, classifications)):
            # Create polygon for patch
            minx, miny, maxx, maxy = patch['bounds']
            from shapely.geometry import box
            polygon = box(minx, miny, maxx, maxy)
            
            patch_data.append({
                'patch_id': patch['patch_id'],
                'geometry': polygon,
                'land_use': classification,
                'center_x': patch['center_x'],
                'center_y': patch['center_y'],
                'imagery_type': imagery_type,
                'analysis_method': 'real_satellite_imagery'
            })
        
        # Create GeoDataFrame (assuming WGS84 for now)
        gdf = gpd.GeoDataFrame(patch_data, crs='EPSG:4326')
        
        print(f"✅ Completed analysis with {len(gdf)} patches and {len(gdf['land_use'].unique())} land use types")
        return gdf
        
    except Exception as e:
        print(f"❌ Error processing satellite imagery: {e}")
        print("   Falling back to placeholder analysis...")
        return _create_placeholder_analysis(bounds, patch_size)


def _create_placeholder_analysis(bounds: Tuple[float, float, float, float], 
                               patch_size: int = 512) -> gpd.GeoDataFrame:
    """
    Create placeholder analysis when real imagery is not available.
    
    Args:
        bounds: Geographic bounds (minx, miny, maxx, maxy)
        patch_size: Size of analysis patches
        
    Returns:
        GeoDataFrame with simulated patch analysis
    """
    print("🔄 Generating placeholder satellite imagery analysis...")
    
    # Calculate patch grid
    minx, miny, maxx, maxy = bounds
    width = maxx - minx
    height = maxy - miny
    
    # Estimate number of patches
    patch_size_degrees = 0.001  # Rough approximation
    patches_x = max(1, int(width / patch_size_degrees))
    patches_y = max(1, int(height / patch_size_degrees))
    
    patch_data = []
    patch_id = 0
    
    # Create simulated land use types based on location heuristics
    land_use_types = ['suburban', 'mixed_urban', 'open_space', 'dense_residential']
    
    for i in range(patches_x):
        for j in range(patches_y):
            # Calculate patch bounds
            patch_minx = minx + (i * width / patches_x)
            patch_maxx = minx + ((i + 1) * width / patches_x)
            patch_miny = miny + (j * height / patches_y)
            patch_maxy = miny + ((j + 1) * height / patches_y)
            
            # Create polygon for patch
            from shapely.geometry import box
            polygon = box(patch_minx, patch_miny, patch_maxx, patch_maxy)
            
            # Simulate land use classification based on position
            # Center patches more likely to be urban, edges more suburban/open
            center_distance = np.sqrt((i - patches_x/2)**2 + (j - patches_y/2)**2)
            max_distance = np.sqrt((patches_x/2)**2 + (patches_y/2)**2)
            normalized_distance = center_distance / max_distance if max_distance > 0 else 0
            
            if normalized_distance < 0.3:
                land_use = 'dense_residential'
            elif normalized_distance < 0.6:
                land_use = 'mixed_urban'
            elif normalized_distance < 0.8:
                land_use = 'suburban'
            else:
                land_use = 'open_space'
            
            patch_data.append({
                'patch_id': patch_id,
                'geometry': polygon,
                'land_use': land_use,
                'center_x': (patch_minx + patch_maxx) / 2,
                'center_y': (patch_miny + patch_maxy) / 2,
                'imagery_type': 'simulated',
                'analysis_method': 'placeholder_heuristic'
            })
            
            patch_id += 1
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(patch_data, crs='EPSG:4326')
    
    print(f"📝 Generated {len(gdf)} simulated patches for analysis")
    return gdf


def extract_building_features(buildings_gdf: gpd.GeoDataFrame,
                            satellite_image: Optional[str] = None) -> gpd.GeoDataFrame:
    """
    Extract visual features from buildings using satellite imagery.
    
    Args:
        buildings_gdf: GeoDataFrame with building footprints
        satellite_image: Path to high-resolution satellite image
        
    Returns:
        GeoDataFrame with enhanced building features
    """
    enhanced_buildings = buildings_gdf.copy()
    
    if satellite_image is not None:
        # This would involve extracting image patches around each building
        # and analyzing roof characteristics, materials, etc.
        # For now, we'll add placeholder features
        enhanced_buildings['roof_area'] = enhanced_buildings.geometry.area
        enhanced_buildings['perimeter'] = enhanced_buildings.geometry.length
        enhanced_buildings['compactness'] = (4 * np.pi * enhanced_buildings['roof_area']) / (enhanced_buildings['perimeter'] ** 2)
    
    return enhanced_buildings


def classify_neighborhood_types(patches_gdf: gpd.GeoDataFrame,
                              method: str = 'clustering') -> gpd.GeoDataFrame:
    """
    Classify neighborhood types based on satellite imagery analysis.
    
    Args:
        patches_gdf: GeoDataFrame with analyzed image patches
        method: Classification method ('clustering', 'rules')
        
    Returns:
        GeoDataFrame with neighborhood type classifications
    """
    result_gdf = patches_gdf.copy()
    
    if method == 'clustering':
        # Use K-means clustering based on land use patterns
        land_use_encoded = pd.get_dummies(patches_gdf['land_use'])
        
        # Cluster into neighborhood types
        kmeans = KMeans(n_clusters=5, random_state=42)
        cluster_labels = kmeans.fit_predict(land_use_encoded)
        
        # Map clusters to neighborhood types
        cluster_to_type = {
            0: 'urban_core',
            1: 'suburban_residential', 
            2: 'mixed_development',
            3: 'rural_residential',
            4: 'undeveloped'
        }
        
        result_gdf['neighborhood_type'] = [cluster_to_type[label] for label in cluster_labels]
    
    else:  # rules-based
        # Simple rules based on land use composition
        result_gdf['neighborhood_type'] = result_gdf['land_use'].map({
            'dense_residential': 'urban_core',
            'suburban': 'suburban_residential',
            'mixed_urban': 'mixed_development', 
            'open_space': 'undeveloped',
            'agricultural': 'rural_residential',
            'water_forest': 'undeveloped'
        })
    
    return result_gdf 