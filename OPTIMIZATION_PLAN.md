# OPTIMIZATION PLAN

**ASSESSMENT**

## Performance Test Results Analysis

### 🎯 **Key Findings**

**Scaling Performance:**
- **10 POIs**: 91.63s (9.16s per POI)
- **50 POIs**: 467.60s (9.35s per POI) 
- **100 POIs**: 653.13s (6.53s per POI)
- **500 POIs**: 1915.97s (3.83s per POI)

**Surprising Result**: The system actually shows **better than linear scaling** (0.42x), meaning it becomes more efficient per POI as the dataset grows larger. This is unusual and indicates some fixed overhead costs that get amortized across larger datasets.

### 🔍 **Major Bottleneck Identified: Distance Calculations**

The most significant bottleneck is clearly the **travel distance calculation step**:

- **Duration**: ~320 seconds for 500 POIs (67% of total processing time)
- **Progress**: Very slow, taking over 5 minutes with detailed progress updates
- **Complexity**: This appears to be O(n×m) where n=POIs and m=census block groups

Let me examine the distance calculation module to understand the bottleneck:

Now let me examine the isochrone generation module to understand that bottleneck:

Now let me examine the main isochrone creation function:

## 📊 **Comprehensive Bottleneck Assessment**

Based on my analysis of the performance test results and code examination, here are the key bottlenecks and optimization opportunities:

### 🚨 **Primary Bottleneck: Distance Calculations (67% of processing time)**

**Problem**: The distance calculation step took **320 seconds out of 1916 total seconds** (67% of processing time) for 500 POIs.

**Root Cause**: **O(n×m) complexity** where:
- n = number of POIs (500)
- m = number of census block groups (1,451)
- Total calculations = 500 × 1,451 = **725,500 distance calculations**

**Specific Issues**:
1. **Nested loops**: For each block group, it calculates distance to ALL POIs to find the minimum
2. **Repeated CRS transformations**: Each distance calculation creates new GeoDataFrames and transforms coordinates
3. **Inefficient geometry operations**: Using `calculate_distance()` function that creates temporary GeoDataFrames for each calculation

### 🔧 **Secondary Bottleneck: Isochrone Generation**

**Problem**: Road network downloads for each POI individually
- **500 separate network downloads** from OpenStreetMap
- Each download includes network processing, speed assignment, and graph projection
- No spatial optimization or caching

### 💾 **Memory Usage**

**Current**: ~422MB memory increase for 500 POIs
**Projection**: For 2,659 POIs = ~2.2GB memory usage
**Issue**: Memory grows with dataset size, suggesting potential memory leaks or inefficient data structures

### 🎯 **Optimization Recommendations**

#### **1. Distance Calculation Optimization (Highest Impact)**

**Current Approach**:
```python
# For each block group:
for idx, row in df.iterrows():
    for poi in poi_points:
        distance = calculate_distance(poi, centroid)  # Creates new GeoDataFrames each time
```

**Optimized Approach**:
```python
# Vectorized distance calculation using spatial indexing
from sklearn.neighbors import BallTree
import numpy as np

# Pre-transform all coordinates once
poi_coords = np.array([[poi.x, poi.y] for poi in poi_points])
centroid_coords = np.array([[centroid.x, centroid.y] for centroid in centroids])

# Use spatial indexing for nearest neighbor search
tree = BallTree(poi_coords, metric='haversine')
distances, indices = tree.query(centroid_coords, k=1)
```

**Expected Improvement**: **80-90% reduction** in distance calculation time

#### **2. Isochrone Generation Optimization**

**Current**: Individual network downloads per POI
**Optimized**: 
- **Spatial clustering** of nearby POIs (already partially implemented)
- **Bounding box downloads** for POI clusters
- **Network caching** and reuse

**Expected Improvement**: **50-70% reduction** in isochrone generation time

#### **3. Memory Optimization**

- **Streaming processing** for large datasets
- **Garbage collection** between major steps
- **Efficient data structures** (use numpy arrays where possible)

### 📈 **Performance Projections**

**Current Performance**: 7.22 seconds per POI average
**With Optimizations**: 
- Distance calc optimization: ~1.5 seconds per POI
- Isochrone optimization: ~0.8 seconds per POI
- **Total optimized**: ~2.3 seconds per POI

**Full Dataset (2,659 POIs)**:
- **Current estimate**: 5.3 hours
- **Optimized estimate**: 1.7 hours (68% improvement)

### 🛠 **Implementation Priority**

1. **High Priority**: Distance calculation vectorization
2. **Medium Priority**: Isochrone clustering optimization  
3. **Low Priority**: Memory management improvements

The distance calculation optimization alone would provide the biggest performance gain and should be implemented first.

```python
# For each block group:
for idx, row in df.iterrows():
    for poi in poi_points:
        distance = calculate_distance(poi, centroid)  # Creates new GeoDataFrames each time
```

```python
# Vectorized distance calculation using spatial indexing
from sklearn.neighbors import BallTree
import numpy as np

# Pre-transform all coordinates once
poi_coords = np.array([[poi.x, poi.y] for poi in poi_points])
centroid_coords = np.array([[centroid.x, centroid.y] for centroid in centroids])

# Use spatial indexing for nearest neighbor search
tree = BallTree(poi_coords, metric='haversine')
distances, indices = tree.query(centroid_coords, k=1)
```

---

**User**

in markdown, write a detailed development plan/roadmap for implementing the recommended optimizations. 

---

**Cursor**

# SocialMapper Performance Optimization Roadmap

## 🎯 Executive Summary

Based on performance analysis of the trail_heads.csv dataset (2,659 POIs), the current pipeline processes at **7.22 seconds per POI**, requiring an estimated **5.3 hours** for the full dataset. This roadmap outlines optimizations to reduce processing time to **~1.7 hours (68% improvement)** through targeted algorithmic and architectural improvements.

## 📊 Current Performance Baseline

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Time per POI | 7.22 seconds | 2.3 seconds | 68% faster |
| Full dataset (2,659 POIs) | 5.3 hours | 1.7 hours | 3.6 hours saved |
| Distance calc time | 320s (67%) | 48s (15%) | 85% reduction |
| Memory usage | 422MB/500 POIs | 250MB/500 POIs | 40% reduction |

---

## 🚀 Phase 1: Distance Calculation Optimization (High Priority)

**Impact**: 85% reduction in distance calculation time  
**Timeline**: 2-3 weeks  
**Effort**: Medium  

### 1.1 Vectorized Distance Calculations

**Current Bottleneck**: O(n×m) nested loops with repeated CRS transformations
- 500 POIs × 1,451 block groups = 725,500 individual distance calculations
- Each calculation creates temporary GeoDataFrames

**Solution**: Implement vectorized spatial operations

#### Implementation Steps:

1. **Create optimized distance module** (`socialmapper/distance/vectorized.py`)
   ```python
   from sklearn.neighbors import BallTree
   import numpy as np
   from geopy.distance import geodesic
   
   def calculate_distances_vectorized(poi_coords, centroid_coords):
       """Vectorized distance calculation using spatial indexing"""
       # Implementation details below
   ```

2. **Pre-transform coordinates once**
   - Convert all POI and centroid coordinates to projected CRS upfront
   - Store in numpy arrays for efficient computation

3. **Implement spatial indexing**
   - Use BallTree or KDTree for nearest neighbor search
   - Calculate distances in batches rather than individually

4. **Add distance calculation method selection**
   ```python
   def add_travel_distances(
       block_groups_gdf: gpd.GeoDataFrame,
       poi_data: Union[Dict, List[Dict]],
       method: str = "vectorized",  # "vectorized" or "legacy"
       **kwargs
   ):
   ```

#### Code Changes Required:

**File**: `socialmapper/distance/__init__.py`
- Add `method` parameter to `add_travel_distances()`
- Implement vectorized calculation path
- Maintain backward compatibility with legacy method

**File**: `socialmapper/distance/vectorized.py` (new)
```python
import numpy as np
from sklearn.neighbors import BallTree
import geopandas as gpd
from typing import List, Tuple

def vectorized_distance_calculation(
    poi_points: List[Point],
    centroids: gpd.GeoSeries,
    crs: str = "EPSG:5070"
) -> np.ndarray:
    """
    Calculate distances using vectorized operations and spatial indexing.
    
    Returns:
        Array of minimum distances for each centroid to nearest POI
    """
    # Pre-transform all coordinates
    poi_gdf = gpd.GeoDataFrame(geometry=poi_points, crs="EPSG:4326")
    poi_projected = poi_gdf.to_crs(crs)
    
    centroids_gdf = gpd.GeoDataFrame(geometry=centroids, crs="EPSG:4326")
    centroids_projected = centroids_gdf.to_crs(crs)
    
    # Extract coordinates as numpy arrays
    poi_coords = np.array([[geom.x, geom.y] for geom in poi_projected.geometry])
    centroid_coords = np.array([[geom.x, geom.y] for geom in centroids_projected.geometry])
    
    # Use BallTree for efficient nearest neighbor search
    tree = BallTree(poi_coords, metric='euclidean')
    distances, indices = tree.query(centroid_coords, k=1)
    
    # Convert from meters to kilometers
    return distances.flatten() / 1000
```

### 1.2 Parallel Processing Implementation

**Goal**: Utilize multiple CPU cores for distance calculations

#### Implementation:
```python
from multiprocessing import Pool
import numpy as np

def parallel_distance_calculation(
    centroids_batch: np.ndarray,
    poi_coords: np.ndarray,
    n_processes: int = None
) -> np.ndarray:
    """Calculate distances in parallel batches"""
    if n_processes is None:
        n_processes = min(4, os.cpu_count())
    
    # Split centroids into batches
    batch_size = len(centroids_batch) // n_processes
    batches = [centroids_batch[i:i+batch_size] 
               for i in range(0, len(centroids_batch), batch_size)]
    
    with Pool(n_processes) as pool:
        results = pool.starmap(calculate_batch_distances, 
                              [(batch, poi_coords) for batch in batches])
    
    return np.concatenate(results)
```

### 1.3 Testing and Validation

1. **Unit tests** for vectorized calculations
2. **Performance benchmarks** comparing old vs new methods
3. **Accuracy validation** ensuring distance calculations remain correct
4. **Integration tests** with existing pipeline

**Expected Results**:
- Distance calculation time: 320s → 48s (85% reduction)
- Overall pipeline improvement: 25-30% faster

---

## 🗺️ Phase 2: Isochrone Generation Optimization (Medium Priority)

**Impact**: 50-70% reduction in isochrone generation time  
**Timeline**: 3-4 weeks  
**Effort**: High  

### 2.1 Enhanced Spatial Clustering

**Current**: Individual network downloads per POI  
**Target**: Clustered network downloads with intelligent merging

#### Implementation Steps:

1. **Improve clustering algorithm** (`socialmapper/isochrone/clustering.py`)
   ```python
   def smart_poi_clustering(
       pois: List[Dict],
       max_cluster_radius_km: float = 10.0,
       travel_time_minutes: int = 15,
       network_buffer_factor: float = 1.5
   ) -> List[List[Dict]]:
       """
       Cluster POIs based on network accessibility and travel time overlap
       """
   ```

2. **Implement network caching**
   ```python
   class NetworkCache:
       def __init__(self, cache_dir: str = "cache/networks"):
           self.cache_dir = cache_dir
           self.cache = {}
       
       def get_network(self, bbox: Tuple[float, float, float, float]) -> nx.Graph:
           """Get cached network or download if not available"""
   ```

3. **Add progressive network expansion**
   - Start with smaller bounding boxes
   - Expand only when POIs are near cluster edges
   - Reuse networks for overlapping areas

#### Code Changes Required:

**File**: `socialmapper/isochrone/clustering.py`
- Enhance `cluster_pois_by_proximity()` with network-aware clustering
- Add network overlap detection
- Implement cluster merging strategies

**File**: `socialmapper/isochrone/cache.py` (new)
```python
import pickle
import hashlib
import os
from typing import Dict, Tuple
import networkx as nx

class NetworkCache:
    def __init__(self, cache_dir: str = "cache/networks", max_cache_size_gb: float = 2.0):
        self.cache_dir = cache_dir
        self.max_cache_size = max_cache_size_gb * 1024**3  # Convert to bytes
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, bbox: Tuple[float, float, float, float], network_type: str) -> str:
        """Generate cache key from bounding box and network type"""
        bbox_str = f"{bbox[0]:.6f},{bbox[1]:.6f},{bbox[2]:.6f},{bbox[3]:.6f}"
        return hashlib.md5(f"{bbox_str}_{network_type}".encode()).hexdigest()
    
    def get_network(self, bbox: Tuple[float, float, float, float], network_type: str = "drive") -> nx.Graph:
        """Get cached network or download if not available"""
        cache_key = self._get_cache_key(bbox, network_type)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        
        # Download network if not cached
        import osmnx as ox
        G = ox.graph_from_bbox(bbox[3], bbox[1], bbox[2], bbox[0], network_type=network_type)
        
        # Cache the network
        with open(cache_file, 'wb') as f:
            pickle.dump(G, f)
        
        return G
```

### 2.2 Batch Isochrone Processing

**Goal**: Process multiple POIs in single network downloads

#### Implementation:
```python
def create_batch_isochrones(
    poi_cluster: List[Dict],
    travel_time_limit: int,
    network_cache: NetworkCache
) -> List[gpd.GeoDataFrame]:
    """
    Create isochrones for a cluster of POIs using shared network
    """
    # Calculate optimal bounding box for cluster
    bbox = calculate_cluster_bbox(poi_cluster, travel_time_limit)
    
    # Get cached or download network
    G = network_cache.get_network(bbox)
    
    # Process all POIs in cluster using same network
    isochrones = []
    for poi in poi_cluster:
        isochrone = create_isochrone_from_network(poi, G, travel_time_limit)
        isochrones.append(isochrone)
    
    return isochrones
```

### 2.3 Asynchronous Network Downloads

**Goal**: Download networks concurrently while processing isochrones

#### Implementation:
```python
import asyncio
import aiohttp

async def download_networks_async(
    clusters: List[List[Dict]],
    travel_time_limit: int
) -> Dict[str, nx.Graph]:
    """Download multiple networks concurrently"""
    tasks = []
    for cluster in clusters:
        bbox = calculate_cluster_bbox(cluster, travel_time_limit)
        task = asyncio.create_task(download_network_async(bbox))
        tasks.append(task)
    
    networks = await asyncio.gather(*tasks)
    return {f"cluster_{i}": network for i, network in enumerate(networks)}
```

**Expected Results**:
- Isochrone generation time: 50-70% reduction
- Network download efficiency: 60-80% fewer downloads
- Memory usage: 30-40% reduction through network reuse

---

## 💾 Phase 3: Memory and I/O Optimization (Low Priority)

**Impact**: 40% reduction in memory usage, improved stability  
**Timeline**: 2 weeks  
**Effort**: Low-Medium  

### 3.1 Streaming Data Processing

**Goal**: Process large datasets without loading everything into memory

#### Implementation:
```python
def process_pois_streaming(
    poi_data: Dict,
    batch_size: int = 100,
    **kwargs
) -> Iterator[gpd.GeoDataFrame]:
    """
    Process POIs in batches to manage memory usage
    """
    pois = poi_data['pois']
    
    for i in range(0, len(pois), batch_size):
        batch = pois[i:i+batch_size]
        batch_data = {'pois': batch}
        
        # Process batch
        result = run_socialmapper_batch(batch_data, **kwargs)
        
        # Yield result and clean up memory
        yield result
        gc.collect()
```

### 3.2 Efficient Data Formats

**Goal**: Use optimized file formats for better I/O performance

#### Implementation:
1. **Default to Parquet** for all intermediate files
2. **Implement compression** for large datasets
3. **Use Arrow** for in-memory operations

```python
# Configuration for optimized I/O
IO_CONFIG = {
    'default_format': 'parquet',
    'compression': 'snappy',
    'use_arrow': True,
    'chunk_size': 10000
}
```

### 3.3 Memory Monitoring and Cleanup

#### Implementation:
```python
import psutil
import gc

class MemoryManager:
    def __init__(self, max_memory_gb: float = 4.0):
        self.max_memory = max_memory_gb * 1024**3
    
    def check_memory_usage(self) -> float:
        """Return current memory usage in GB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024**3
    
    def cleanup_if_needed(self):
        """Force garbage collection if memory usage is high"""
        if self.check_memory_usage() > self.max_memory * 0.8:
            gc.collect()
```

---

## 🧪 Phase 4: Testing and Validation

**Timeline**: 1-2 weeks (parallel with other phases)  
**Effort**: Medium  

### 4.1 Performance Testing Framework

#### Implementation:
```python
class PerformanceBenchmark:
    def __init__(self, test_datasets: List[str]):
        self.test_datasets = test_datasets
        self.results = {}
    
    def run_benchmark(self, optimization_level: str) -> Dict:
        """Run performance tests with different optimization levels"""
        results = {}
        
        for dataset in self.test_datasets:
            start_time = time.time()
            memory_start = psutil.Process().memory_info().rss
            
            # Run pipeline
            result = run_socialmapper(
                custom_coords_path=dataset,
                optimization_level=optimization_level
            )
            
            end_time = time.time()
            memory_end = psutil.Process().memory_info().rss
            
            results[dataset] = {
                'duration': end_time - start_time,
                'memory_delta': memory_end - memory_start,
                'poi_count': len(result['poi_data']['pois'])
            }
        
        return results
```

### 4.2 Regression Testing

1. **Accuracy tests**: Ensure optimizations don't change results
2. **Performance tests**: Validate improvement targets
3. **Memory tests**: Confirm memory usage reductions
4. **Integration tests**: Test with various input formats

### 4.3 Benchmarking Datasets

| Dataset | POI Count | Purpose |
|---------|-----------|---------|
| Small test | 10 POIs | Unit testing |
| Medium test | 100 POIs | Integration testing |
| Large test | 500 POIs | Performance validation |
| Full trail_heads | 2,659 POIs | Production validation |

---

## 📋 Implementation Timeline

### Month 1: Distance Optimization
- **Week 1-2**: Implement vectorized distance calculations
- **Week 3**: Add parallel processing
- **Week 4**: Testing and integration

### Month 2: Isochrone Optimization  
- **Week 1-2**: Enhanced clustering and network caching
- **Week 3**: Batch processing implementation
- **Week 4**: Asynchronous downloads

### Month 3: Memory & Polish
- **Week 1**: Memory optimization and streaming
- **Week 2**: Performance testing framework
- **Week 3**: Documentation and final testing
- **Week 4**: Release preparation

---

## 🎯 Success Metrics

### Performance Targets
- [ ] **Distance calculation time**: < 50 seconds for 500 POIs
- [ ] **Overall processing time**: < 2.5 seconds per POI average
- [ ] **Memory usage**: < 300MB for 500 POIs
- [ ] **Full dataset processing**: < 2 hours for 2,659 POIs

### Quality Targets
- [ ] **Accuracy**: 100% identical results vs current implementation
- [ ] **Reliability**: 99.9% success rate on test datasets
- [ ] **Backward compatibility**: All existing APIs continue to work
- [ ] **Documentation**: Complete API docs and performance guides

---

## 🔧 Configuration Management

### New Configuration Options
```python
# socialmapper/config.py
OPTIMIZATION_CONFIG = {
    'distance_calculation': {
        'method': 'vectorized',  # 'vectorized' or 'legacy'
        'parallel_processes': 4,
        'batch_size': 1000
    },
    'isochrone_generation': {
        'use_clustering': True,
        'max_cluster_radius_km': 10.0,
        'enable_caching': True,
        'cache_dir': 'cache/networks'
    },
    'memory_management': {
        'max_memory_gb': 4.0,
        'streaming_batch_size': 100,
        'enable_gc': True
    }
}
```

---

## 🚀 Deployment Strategy

### Phase Rollout
1. **Alpha**: Internal testing with small datasets
2. **Beta**: Limited release with performance monitoring
3. **Production**: Full release with fallback to legacy methods

### Backward Compatibility
- Maintain all existing API endpoints
- Add `optimization_level` parameter with options: `'legacy'`, `'standard'`, `'aggressive'`
- Default to `'standard'` for new installations, `'legacy'` for upgrades

### Monitoring
- Performance metrics collection
- Error rate monitoring  
- Memory usage tracking
- User feedback collection

This roadmap provides a comprehensive path to achieving the targeted 68% performance improvement while maintaining system reliability and backward compatibility.

```python
   from sklearn.neighbors import BallTree
   import numpy as np
   from geopy.distance import geodesic
   
   def calculate_distances_vectorized(poi_coords, centroid_coords):
       """Vectorized distance calculation using spatial indexing"""
       # Implementation details below
```

```python
   def add_travel_distances(
       block_groups_gdf: gpd.GeoDataFrame,
       poi_data: Union[Dict, List[Dict]],
       method: str = "vectorized",  # "vectorized" or "legacy"
       **kwargs
   ):
```

```python
import numpy as np
from sklearn.neighbors import BallTree
import geopandas as gpd
from typing import List, Tuple

def vectorized_distance_calculation(
    poi_points: List[Point],
    centroids: gpd.GeoSeries,
    crs: str = "EPSG:5070"
) -> np.ndarray:
    """
    Calculate distances using vectorized operations and spatial indexing.
    
    Returns:
        Array of minimum distances for each centroid to nearest POI
    """
    # Pre-transform all coordinates
    poi_gdf = gpd.GeoDataFrame(geometry=poi_points, crs="EPSG:4326")
    poi_projected = poi_gdf.to_crs(crs)
    
    centroids_gdf = gpd.GeoDataFrame(geometry=centroids, crs="EPSG:4326")
    centroids_projected = centroids_gdf.to_crs(crs)
    
    # Extract coordinates as numpy arrays
    poi_coords = np.array([[geom.x, geom.y] for geom in poi_projected.geometry])
    centroid_coords = np.array([[geom.x, geom.y] for geom in centroids_projected.geometry])
    
    # Use BallTree for efficient nearest neighbor search
    tree = BallTree(poi_coords, metric='euclidean')
    distances, indices = tree.query(centroid_coords, k=1)
    
    # Convert from meters to kilometers
    return distances.flatten() / 1000
```

```python
from multiprocessing import Pool
import numpy as np

def parallel_distance_calculation(
    centroids_batch: np.ndarray,
    poi_coords: np.ndarray,
    n_processes: int = None
) -> np.ndarray:
    """Calculate distances in parallel batches"""
    if n_processes is None:
        n_processes = min(4, os.cpu_count())
    
    # Split centroids into batches
    batch_size = len(centroids_batch) // n_processes
    batches = [centroids_batch[i:i+batch_size] 
               for i in range(0, len(centroids_batch), batch_size)]
    
    with Pool(n_processes) as pool:
        results = pool.starmap(calculate_batch_distances, 
                              [(batch, poi_coords) for batch in batches])
    
    return np.concatenate(results)
```

```python
   def smart_poi_clustering(
       pois: List[Dict],
       max_cluster_radius_km: float = 10.0,
       travel_time_minutes: int = 15,
       network_buffer_factor: float = 1.5
   ) -> List[List[Dict]]:
       """
       Cluster POIs based on network accessibility and travel time overlap
       """
```

```python
   class NetworkCache:
       def __init__(self, cache_dir: str = "cache/networks"):
           self.cache_dir = cache_dir
           self.cache = {}
       
       def get_network(self, bbox: Tuple[float, float, float, float]) -> nx.Graph:
           """Get cached network or download if not available"""
```

```python
import pickle
import hashlib
import os
from typing import Dict, Tuple
import networkx as nx

class NetworkCache:
    def __init__(self, cache_dir: str = "cache/networks", max_cache_size_gb: float = 2.0):
        self.cache_dir = cache_dir
        self.max_cache_size = max_cache_size_gb * 1024**3  # Convert to bytes
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, bbox: Tuple[float, float, float, float], network_type: str) -> str:
        """Generate cache key from bounding box and network type"""
        bbox_str = f"{bbox[0]:.6f},{bbox[1]:.6f},{bbox[2]:.6f},{bbox[3]:.6f}"
        return hashlib.md5(f"{bbox_str}_{network_type}".encode()).hexdigest()
    
    def get_network(self, bbox: Tuple[float, float, float, float], network_type: str = "drive") -> nx.Graph:
        """Get cached network or download if not available"""
        cache_key = self._get_cache_key(bbox, network_type)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        
        # Download network if not cached
        import osmnx as ox
        G = ox.graph_from_bbox(bbox[3], bbox[1], bbox[2], bbox[0], network_type=network_type)
        
        # Cache the network
        with open(cache_file, 'wb') as f:
            pickle.dump(G, f)
        
        return G
```

```python
def create_batch_isochrones(
    poi_cluster: List[Dict],
    travel_time_limit: int,
    network_cache: NetworkCache
) -> List[gpd.GeoDataFrame]:
    """
    Create isochrones for a cluster of POIs using shared network
    """
    # Calculate optimal bounding box for cluster
    bbox = calculate_cluster_bbox(poi_cluster, travel_time_limit)
    
    # Get cached or download network
    G = network_cache.get_network(bbox)
    
    # Process all POIs in cluster using same network
    isochrones = []
    for poi in poi_cluster:
        isochrone = create_isochrone_from_network(poi, G, travel_time_limit)
        isochrones.append(isochrone)
    
    return isochrones
```

```python
import asyncio
import aiohttp

async def download_networks_async(
    clusters: List[List[Dict]],
    travel_time_limit: int
) -> Dict[str, nx.Graph]:
    """Download multiple networks concurrently"""
    tasks = []
    for cluster in clusters:
        bbox = calculate_cluster_bbox(cluster, travel_time_limit)
        task = asyncio.create_task(download_network_async(bbox))
        tasks.append(task)
    
    networks = await asyncio.gather(*tasks)
    return {f"cluster_{i}": network for i, network in enumerate(networks)}
```

```python
def process_pois_streaming(
    poi_data: Dict,
    batch_size: int = 100,
    **kwargs
) -> Iterator[gpd.GeoDataFrame]:
    """
    Process POIs in batches to manage memory usage
    """
    pois = poi_data['pois']
    
    for i in range(0, len(pois), batch_size):
        batch = pois[i:i+batch_size]
        batch_data = {'pois': batch}
        
        # Process batch
        result = run_socialmapper_batch(batch_data, **kwargs)
        
        # Yield result and clean up memory
        yield result
        gc.collect()
```

```python
# Configuration for optimized I/O
IO_CONFIG = {
    'default_format': 'parquet',
    'compression': 'snappy',
    'use_arrow': True,
    'chunk_size': 10000
}
```

```python
import psutil
import gc

class MemoryManager:
    def __init__(self, max_memory_gb: float = 4.0):
        self.max_memory = max_memory_gb * 1024**3
    
    def check_memory_usage(self) -> float:
        """Return current memory usage in GB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024**3
    
    def cleanup_if_needed(self):
        """Force garbage collection if memory usage is high"""
        if self.check_memory_usage() > self.max_memory * 0.8:
            gc.collect()
```

```python
class PerformanceBenchmark:
    def __init__(self, test_datasets: List[str]):
        self.test_datasets = test_datasets
        self.results = {}
    
    def run_benchmark(self, optimization_level: str) -> Dict:
        """Run performance tests with different optimization levels"""
        results = {}
        
        for dataset in self.test_datasets:
            start_time = time.time()
            memory_start = psutil.Process().memory_info().rss
            
            # Run pipeline
            result = run_socialmapper(
                custom_coords_path=dataset,
                optimization_level=optimization_level
            )
            
            end_time = time.time()
            memory_end = psutil.Process().memory_info().rss
            
            results[dataset] = {
                'duration': end_time - start_time,
                'memory_delta': memory_end - memory_start,
                'poi_count': len(result['poi_data']['pois'])
            }
        
        return results
```

```python
# socialmapper/config.py
OPTIMIZATION_CONFIG = {
    'distance_calculation': {
        'method': 'vectorized',  # 'vectorized' or 'legacy'
        'parallel_processes': 4,
        'batch_size': 1000
    },
    'isochrone_generation': {
        'use_clustering': True,
        'max_cluster_radius_km': 10.0,
        'enable_caching': True,
        'cache_dir': 'cache/networks'
    },
    'memory_management': {
        'max_memory_gb': 4.0,
        'streaming_batch_size': 100,
        'enable_gc': True
    }
}
```

