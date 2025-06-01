#!/usr/bin/env python3
"""
Modern Configuration System for SocialMapper Optimization.

This module provides a centralized configuration system for all optimization
settings, using modern Python patterns like dataclasses and type hints.

Key Features:
- Dataclass-based configuration for type safety
- Intelligent defaults based on system capabilities
- Environment variable support
- Performance-first design
- Easy customization and extension
"""

import os
import multiprocessing as mp
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import psutil

@dataclass
class DistanceConfig:
    """Configuration for distance calculation optimization."""
    
    # Distance engine settings ✅ IMPLEMENTED
    engine: str = "vectorized_numba"  # Only optimized option available
    parallel_processes: int = -1  # Use all cores
    chunk_size: int = 5000
    enable_jit: bool = True
    
    def __post_init__(self):
        """Validate and adjust settings after initialization."""
        if self.parallel_processes == -1:
            self.parallel_processes = mp.cpu_count()
        
        # Ensure chunk size is reasonable
        if self.chunk_size < 100:
            self.chunk_size = 100
        elif self.chunk_size > 50000:
            self.chunk_size = 50000

@dataclass
class IsochroneConfig:
    """Configuration for isochrone generation optimization."""
    
    # Clustering settings 🎯 IMPLEMENTED
    clustering_algorithm: str = "dbscan"  # Only modern option
    max_cluster_radius_km: float = 15.0
    min_cluster_size: int = 2
    auto_clustering_threshold: int = 5  # Auto-enable clustering for 5+ POIs
    
    # Caching settings 🎯 IMPLEMENTED
    enable_caching: bool = True
    cache_dir: str = "cache/networks"
    max_cache_size_gb: float = 5.0
    cache_compression_level: int = 6
    
    # Concurrent processing settings 🎯 IMPLEMENTED
    max_concurrent_downloads: int = 8
    max_concurrent_isochrones: Optional[int] = None  # Defaults to CPU count
    auto_concurrent_threshold: int = 3  # Auto-enable concurrent for 3+ POIs
    enable_resource_monitoring: bool = True
    
    def __post_init__(self):
        """Validate and adjust settings after initialization."""
        if self.max_concurrent_isochrones is None:
            self.max_concurrent_isochrones = mp.cpu_count()
        
        # Adjust based on system resources
        available_memory_gb = psutil.virtual_memory().available / 1024**3
        
        # Reduce concurrent downloads if low memory
        if available_memory_gb < 4.0:
            self.max_concurrent_downloads = min(4, self.max_concurrent_downloads)
        
        # Ensure cache size doesn't exceed available disk space
        try:
            disk_free_gb = psutil.disk_usage('/').free / 1024**3
            if self.max_cache_size_gb > disk_free_gb * 0.1:  # Don't use more than 10% of free space
                self.max_cache_size_gb = max(1.0, disk_free_gb * 0.1)
        except:
            pass  # Fallback to default if disk check fails

@dataclass
class MemoryConfig:
    """Configuration for memory management optimization."""
    
    # Memory management 📋 PLANNED FOR PHASE 3
    max_memory_gb: float = 3.0
    streaming_batch_size: int = 1000
    aggressive_cleanup: bool = True
    enable_memory_monitoring: bool = True
    memory_warning_threshold: float = 0.85  # Warn at 85% memory usage
    cleanup_threshold_mb: float = 1024.0  # Trigger cleanup at 1GB memory usage
    
    def __post_init__(self):
        """Validate and adjust settings based on system memory."""
        total_memory_gb = psutil.virtual_memory().total / 1024**3
        
        # Don't allow more than 50% of system memory
        max_allowed = total_memory_gb * 0.5
        if self.max_memory_gb > max_allowed:
            self.max_memory_gb = max_allowed
        
        # Adjust batch size based on available memory
        if total_memory_gb < 8.0:
            self.streaming_batch_size = min(500, self.streaming_batch_size)
        
        # Adjust cleanup threshold based on system memory
        if total_memory_gb < 4.0:
            self.cleanup_threshold_mb = min(512.0, self.cleanup_threshold_mb)
        elif total_memory_gb > 16.0:
            self.cleanup_threshold_mb = max(2048.0, self.cleanup_threshold_mb)

@dataclass
class IOConfig:
    """Configuration for I/O optimization - Phase 3 Implementation."""
    
    # Modern data formats ✅ IMPLEMENTED FOR PHASE 3
    default_format: str = "parquet"  # Modern formats only
    compression: str = "snappy"
    use_polars: bool = True
    enable_arrow: bool = True
    parallel_io: bool = True
    
    # Streaming configuration ✅ NEW FOR PHASE 3
    streaming_batch_size: int = 1000
    enable_streaming: bool = True
    stream_threshold_mb: float = 100.0  # Use streaming for files > 100MB
    
    # Memory management ✅ NEW FOR PHASE 3
    max_memory_per_operation_mb: float = 1024.0
    enable_memory_monitoring: bool = True
    aggressive_cleanup: bool = True
    
    # Format-specific settings ✅ NEW FOR PHASE 3
    parquet_row_group_size: int = 50000
    parquet_compression_level: int = 6
    arrow_batch_size: int = 10000
    
    def __post_init__(self):
        """Validate I/O settings and adjust based on system capabilities."""
        import psutil
        
        # Check if required libraries are available
        try:
            import pyarrow
            self.enable_arrow = True
        except ImportError:
            self.enable_arrow = False
            if self.default_format == "parquet":
                print("Warning: PyArrow not available, some Parquet features disabled")
        
        try:
            import polars
            self.use_polars = True
        except ImportError:
            self.use_polars = False
            print("Warning: Polars not available, using pandas for data processing")
        
        # Adjust settings based on system memory
        total_memory_gb = psutil.virtual_memory().total / 1024**3
        
        if total_memory_gb < 4.0:
            # Low memory system adjustments
            self.streaming_batch_size = min(500, self.streaming_batch_size)
            self.max_memory_per_operation_mb = min(512.0, self.max_memory_per_operation_mb)
            self.stream_threshold_mb = 50.0  # Stream smaller files
            self.parquet_row_group_size = 25000
            self.arrow_batch_size = 5000
        elif total_memory_gb > 16.0:
            # High memory system optimizations
            self.streaming_batch_size = max(2000, self.streaming_batch_size)
            self.max_memory_per_operation_mb = max(2048.0, self.max_memory_per_operation_mb)
            self.stream_threshold_mb = 500.0  # Only stream very large files
            self.parquet_row_group_size = 100000
            self.arrow_batch_size = 20000
        
        # Validate compression settings
        if self.compression not in ['snappy', 'gzip', 'lz4', 'brotli', None]:
            print(f"Warning: Unknown compression '{self.compression}', using 'snappy'")
            self.compression = 'snappy'
    
    def get_optimal_format_for_size(self, size_mb: float) -> str:
        """Get optimal format based on data size."""
        if size_mb > self.stream_threshold_mb:
            return "streaming_parquet"
        elif size_mb > 10.0:
            return "parquet"
        else:
            return "memory"  # Keep in memory
    
    def should_use_streaming(self, size_mb: float) -> bool:
        """Determine if streaming should be used based on data size."""
        return self.enable_streaming and size_mb > self.stream_threshold_mb

@dataclass
class OptimizationConfig:
    """Master configuration for all SocialMapper optimizations."""
    
    # Component configurations
    distance: DistanceConfig = field(default_factory=DistanceConfig)
    isochrone: IsochroneConfig = field(default_factory=IsochroneConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    io: IOConfig = field(default_factory=IOConfig)
    
    # Global settings
    enable_performance_monitoring: bool = True
    log_level: str = "INFO"
    enable_progress_bars: bool = True
    
    @classmethod
    def from_environment(cls) -> 'OptimizationConfig':
        """Create configuration from environment variables."""
        config = cls()
        
        # Distance settings
        if os.getenv('SOCIALMAPPER_PARALLEL_PROCESSES'):
            config.distance.parallel_processes = int(os.getenv('SOCIALMAPPER_PARALLEL_PROCESSES'))
        
        if os.getenv('SOCIALMAPPER_CHUNK_SIZE'):
            config.distance.chunk_size = int(os.getenv('SOCIALMAPPER_CHUNK_SIZE'))
        
        # Isochrone settings
        if os.getenv('SOCIALMAPPER_MAX_CLUSTER_RADIUS'):
            config.isochrone.max_cluster_radius_km = float(os.getenv('SOCIALMAPPER_MAX_CLUSTER_RADIUS'))
        
        if os.getenv('SOCIALMAPPER_CACHE_SIZE_GB'):
            config.isochrone.max_cache_size_gb = float(os.getenv('SOCIALMAPPER_CACHE_SIZE_GB'))
        
        if os.getenv('SOCIALMAPPER_MAX_WORKERS'):
            config.isochrone.max_concurrent_downloads = int(os.getenv('SOCIALMAPPER_MAX_WORKERS'))
        
        # Memory settings
        if os.getenv('SOCIALMAPPER_MAX_MEMORY_GB'):
            config.memory.max_memory_gb = float(os.getenv('SOCIALMAPPER_MAX_MEMORY_GB'))
        
        # Global settings
        if os.getenv('SOCIALMAPPER_LOG_LEVEL'):
            config.log_level = os.getenv('SOCIALMAPPER_LOG_LEVEL')
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            'distance': {
                'engine': self.distance.engine,
                'parallel_processes': self.distance.parallel_processes,
                'chunk_size': self.distance.chunk_size,
                'enable_jit': self.distance.enable_jit
            },
            'isochrone': {
                'clustering_algorithm': self.isochrone.clustering_algorithm,
                'max_cluster_radius_km': self.isochrone.max_cluster_radius_km,
                'min_cluster_size': self.isochrone.min_cluster_size,
                'enable_caching': self.isochrone.enable_caching,
                'cache_dir': self.isochrone.cache_dir,
                'max_cache_size_gb': self.isochrone.max_cache_size_gb,
                'max_concurrent_downloads': self.isochrone.max_concurrent_downloads,
                'max_concurrent_isochrones': self.isochrone.max_concurrent_isochrones
            },
            'memory': {
                'max_memory_gb': self.memory.max_memory_gb,
                'streaming_batch_size': self.memory.streaming_batch_size,
                'aggressive_cleanup': self.memory.aggressive_cleanup
            },
            'io': {
                'default_format': self.io.default_format,
                'compression': self.io.compression,
                'use_polars': self.io.use_polars,
                'enable_arrow': self.io.enable_arrow
            },
            'global': {
                'enable_performance_monitoring': self.enable_performance_monitoring,
                'log_level': self.log_level,
                'enable_progress_bars': self.enable_progress_bars
            }
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get current system information for optimization decisions."""
        try:
            cpu_count = mp.cpu_count()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_count': cpu_count,
                'memory_total_gb': memory.total / 1024**3,
                'memory_available_gb': memory.available / 1024**3,
                'memory_percent_used': memory.percent,
                'disk_total_gb': disk.total / 1024**3,
                'disk_free_gb': disk.free / 1024**3,
                'disk_percent_used': (disk.used / disk.total) * 100
            }
        except Exception as e:
            return {'error': str(e)}

# Global optimized configuration instance
OPTIMIZED_CONFIG = OptimizationConfig.from_environment()

def get_config() -> OptimizationConfig:
    """Get the global optimization configuration."""
    return OPTIMIZED_CONFIG

def update_config(**kwargs) -> None:
    """Update global configuration with new values."""
    global OPTIMIZED_CONFIG
    
    for key, value in kwargs.items():
        if hasattr(OPTIMIZED_CONFIG, key):
            setattr(OPTIMIZED_CONFIG, key, value)
        else:
            # Handle nested configuration updates
            if '.' in key:
                section, setting = key.split('.', 1)
                if hasattr(OPTIMIZED_CONFIG, section):
                    section_config = getattr(OPTIMIZED_CONFIG, section)
                    if hasattr(section_config, setting):
                        setattr(section_config, setting, value)

def reset_config() -> None:
    """Reset configuration to defaults."""
    global OPTIMIZED_CONFIG
    OPTIMIZED_CONFIG = OptimizationConfig.from_environment()

# Performance presets for different use cases
class PerformancePresets:
    """Predefined performance configurations for different scenarios."""
    
    @staticmethod
    def development() -> OptimizationConfig:
        """Configuration optimized for development and testing."""
        config = OptimizationConfig()
        config.isochrone.max_concurrent_downloads = 2
        config.isochrone.max_concurrent_isochrones = 2
        config.isochrone.max_cache_size_gb = 1.0
        config.memory.max_memory_gb = 1.0
        config.log_level = "DEBUG"
        return config
    
    @staticmethod
    def production() -> OptimizationConfig:
        """Configuration optimized for production workloads."""
        config = OptimizationConfig()
        config.isochrone.max_concurrent_downloads = 16
        config.isochrone.max_concurrent_isochrones = mp.cpu_count()
        config.isochrone.max_cache_size_gb = 10.0
        config.memory.max_memory_gb = 8.0
        config.memory.aggressive_cleanup = True
        return config
    
    @staticmethod
    def memory_constrained() -> OptimizationConfig:
        """Configuration for systems with limited memory."""
        config = OptimizationConfig()
        config.isochrone.max_concurrent_downloads = 2
        config.isochrone.max_concurrent_isochrones = 2
        config.isochrone.max_cache_size_gb = 0.5
        config.memory.max_memory_gb = 1.0
        config.memory.streaming_batch_size = 100
        config.memory.aggressive_cleanup = True
        return config
    
    @staticmethod
    def high_performance() -> OptimizationConfig:
        """Configuration for maximum performance on powerful systems."""
        config = OptimizationConfig()
        config.distance.chunk_size = 10000
        config.isochrone.max_concurrent_downloads = 32
        config.isochrone.max_concurrent_isochrones = mp.cpu_count() * 2
        config.isochrone.max_cache_size_gb = 20.0
        config.memory.max_memory_gb = 16.0
        return config 