#!/usr/bin/env python3
"""
Modern Memory Management for SocialMapper.

- Intelligent memory monitoring and alerting
- Automatic cleanup and garbage collection
- Resource-aware processing decisions
- Memory-efficient data structures
- Streaming fallback for large datasets

Key Features:
- Automatic memory pressure detection and response
- Resource-aware batch sizing and processing
- Memory leak detection and prevention
- Performance monitoring and optimization
"""

import gc
import os
import time
import logging
import threading
import warnings
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
from pathlib import Path

import psutil
import pandas as pd
import geopandas as gpd
import numpy as np

from ..config.optimization import MemoryConfig
from ..progress import get_progress_bar

logger = logging.getLogger(__name__)

@dataclass
class MemoryStats:
    """Memory usage statistics and metrics."""
    peak_memory_mb: float = 0.0
    current_memory_mb: float = 0.0
    memory_saved_mb: float = 0.0
    gc_collections: int = 0
    cleanup_operations: int = 0
    memory_warnings: int = 0
    memory_errors: int = 0
    start_time: float = field(default_factory=time.time)
    
    def get_runtime_seconds(self) -> float:
        """Get total runtime in seconds."""
        return time.time() - self.start_time
    
    def get_memory_efficiency(self) -> float:
        """Calculate memory efficiency ratio."""
        if self.peak_memory_mb > 0:
            return self.memory_saved_mb / self.peak_memory_mb
        return 0.0

@dataclass
class MemoryThresholds:
    """Memory usage thresholds for different actions."""
    warning_percent: float = 75.0      # Warn at 75% memory usage
    cleanup_percent: float = 85.0      # Trigger cleanup at 85%
    emergency_percent: float = 95.0    # Emergency actions at 95%
    streaming_percent: float = 80.0    # Switch to streaming at 80%


class MemoryMonitor:
    """
    Real-time memory monitoring and management system.
    
    This class provides:
    - Continuous memory usage monitoring
    - Automatic cleanup triggers
    - Memory pressure detection
    - Resource-aware processing decisions
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        """
        Initialize the memory monitor.
        
        Args:
            config: Memory configuration (uses defaults if None)
        """
        self.config = config or MemoryConfig()
        self.stats = MemoryStats()
        self.thresholds = MemoryThresholds()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        # Get system memory info
        self.system_memory = psutil.virtual_memory()
        self.process = psutil.Process()
        
        logger.info(f"Initialized memory monitor with {self.system_memory.total / 1024**3:.1f}GB total memory")
    
    def start_monitoring(self, interval_seconds: float = 1.0):
        """Start continuous memory monitoring."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self._monitor_thread.start()
        
        logger.info("Started memory monitoring")
    
    def stop_monitoring(self):
        """Stop memory monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        
        logger.info("Stopped memory monitoring")
    
    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a callback for memory events."""
        self._callbacks.append(callback)
    
    def _monitor_loop(self, interval_seconds: float):
        """Main monitoring loop."""
        while self._monitoring:
            try:
                memory_info = self.get_current_memory_info()
                self._check_memory_thresholds(memory_info)
                
                # Update stats
                self.stats.current_memory_mb = memory_info['process_memory_mb']
                self.stats.peak_memory_mb = max(self.stats.peak_memory_mb, memory_info['process_memory_mb'])
                
                time.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in memory monitoring loop: {e}")
                time.sleep(interval_seconds)
    
    def get_current_memory_info(self) -> Dict[str, Any]:
        """Get current memory usage information."""
        try:
            # System memory
            system_memory = psutil.virtual_memory()
            
            # Process memory
            process_memory = self.process.memory_info()
            
            return {
                'system_total_gb': system_memory.total / 1024**3,
                'system_available_gb': system_memory.available / 1024**3,
                'system_used_percent': system_memory.percent,
                'process_memory_mb': process_memory.rss / 1024**2,
                'process_memory_gb': process_memory.rss / 1024**3,
                'memory_pressure': system_memory.percent > self.thresholds.warning_percent
            }
        except Exception as e:
            logger.error(f"Failed to get memory info: {e}")
            return {}
    
    def _check_memory_thresholds(self, memory_info: Dict[str, Any]):
        """Check memory usage against thresholds and trigger actions."""
        system_percent = memory_info.get('system_used_percent', 0)
        
        if system_percent > self.thresholds.emergency_percent:
            self._trigger_emergency_cleanup()
            self.stats.memory_errors += 1
        elif system_percent > self.thresholds.cleanup_percent:
            self._trigger_cleanup()
            self.stats.cleanup_operations += 1
        elif system_percent > self.thresholds.warning_percent:
            self._trigger_warning(memory_info)
            self.stats.memory_warnings += 1
        
        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(memory_info)
            except Exception as e:
                logger.error(f"Error in memory callback: {e}")
    
    def _trigger_warning(self, memory_info: Dict[str, Any]):
        """Trigger memory warning."""
        logger.warning(f"High memory usage: {memory_info.get('system_used_percent', 0):.1f}%")
    
    def _trigger_cleanup(self):
        """Trigger memory cleanup."""
        logger.info("Triggering memory cleanup due to high usage")
        
        # Force garbage collection
        collected = gc.collect()
        self.stats.gc_collections += 1
        
        logger.info(f"Garbage collection freed {collected} objects")
    
    def _trigger_emergency_cleanup(self):
        """Trigger emergency memory cleanup."""
        logger.critical("Emergency memory cleanup - system memory critically low!")
        
        # Aggressive garbage collection
        for generation in range(3):
            collected = gc.collect(generation)
            logger.info(f"Emergency GC generation {generation}: freed {collected} objects")
        
        self.stats.gc_collections += 3
        
        # Clear any cached data
        if hasattr(pd, 'core') and hasattr(pd.core, 'common'):
            try:
                pd.core.common.clear_cache()
            except:
                pass
    
    def should_use_streaming(self, estimated_memory_mb: float) -> bool:
        """Determine if streaming should be used based on memory pressure."""
        current_info = self.get_current_memory_info()
        available_mb = current_info.get('system_available_gb', 0) * 1024
        
        # Use streaming if:
        # 1. Estimated memory usage exceeds available memory
        # 2. System memory usage is above streaming threshold
        # 3. Estimated usage exceeds configured maximum
        
        return (
            estimated_memory_mb > available_mb * 0.8 or  # 80% of available
            current_info.get('system_used_percent', 0) > self.thresholds.streaming_percent or
            estimated_memory_mb > self.config.max_memory_gb * 1024
        )
    
    def get_optimal_batch_size(self, base_batch_size: int, item_size_mb: float) -> int:
        """Calculate optimal batch size based on memory constraints."""
        current_info = self.get_current_memory_info()
        available_mb = current_info.get('system_available_gb', 0) * 1024
        
        # Target using 50% of available memory for batch processing
        target_memory_mb = available_mb * 0.5
        
        if item_size_mb > 0:
            optimal_batch_size = int(target_memory_mb / item_size_mb)
            return max(1, min(optimal_batch_size, base_batch_size))
        
        return base_batch_size
    
    @contextmanager
    def memory_context(self, operation_name: str, expected_memory_mb: Optional[float] = None):
        """Context manager for monitoring memory usage during operations."""
        start_memory = self.get_current_memory_info()['process_memory_mb']
        start_time = time.time()
        
        if expected_memory_mb and self.should_use_streaming(expected_memory_mb):
            logger.info(f"Using streaming for {operation_name} due to memory constraints")
        
        try:
            yield
        finally:
            end_memory = self.get_current_memory_info()['process_memory_mb']
            end_time = time.time()
            
            memory_delta = end_memory - start_memory
            duration = end_time - start_time
            
            if memory_delta > 0:
                logger.debug(f"{operation_name}: +{memory_delta:.1f}MB memory, {duration:.3f}s")
            else:
                logger.debug(f"{operation_name}: {memory_delta:.1f}MB memory (saved), {duration:.3f}s")
                self.stats.memory_saved_mb += abs(memory_delta)
            
            # Trigger cleanup if memory usage is high
            if end_memory > self.config.cleanup_threshold_mb:
                self._trigger_cleanup()


class MemoryEfficientDataProcessor:
    """
    Memory-efficient data processor with automatic optimization.
    
    This class provides:
    - Automatic memory-aware processing
    - Intelligent batch sizing
    - Streaming fallback for large datasets
    - Memory leak prevention
    """
    
    def __init__(self, monitor: Optional[MemoryMonitor] = None):
        """
        Initialize the memory-efficient processor.
        
        Args:
            monitor: Memory monitor instance (creates new if None)
        """
        self.monitor = monitor or MemoryMonitor()
        self._own_monitor = monitor is None
        
        if self._own_monitor:
            self.monitor.start_monitoring()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        if self._own_monitor:
            self.monitor.stop_monitoring()
    
    def process_dataframe_efficiently(self, 
                                    df: pd.DataFrame,
                                    operation: Callable[[pd.DataFrame], pd.DataFrame],
                                    batch_size: Optional[int] = None) -> pd.DataFrame:
        """
        Process DataFrame with memory-efficient batching.
        
        Args:
            df: Input DataFrame
            operation: Function to apply to each batch
            batch_size: Batch size (auto-calculated if None)
            
        Returns:
            Processed DataFrame
        """
        # Estimate memory usage
        estimated_memory_mb = df.memory_usage(deep=True).sum() / 1024**2
        
        with self.monitor.memory_context("DataFrame processing", estimated_memory_mb):
            if self.monitor.should_use_streaming(estimated_memory_mb):
                return self._process_dataframe_streaming(df, operation, batch_size)
            else:
                return self._process_dataframe_memory(df, operation)
    
    def _process_dataframe_memory(self, 
                                df: pd.DataFrame,
                                operation: Callable[[pd.DataFrame], pd.DataFrame]) -> pd.DataFrame:
        """Process DataFrame in memory."""
        logger.info(f"Processing {len(df)} rows in memory")
        return operation(df)
    
    def _process_dataframe_streaming(self, 
                                   df: pd.DataFrame,
                                   operation: Callable[[pd.DataFrame], pd.DataFrame],
                                   batch_size: Optional[int] = None) -> pd.DataFrame:
        """Process DataFrame using streaming with batches."""
        if batch_size is None:
            # Calculate optimal batch size
            row_size_mb = df.memory_usage(deep=True).sum() / len(df) / 1024**2
            batch_size = self.monitor.get_optimal_batch_size(1000, row_size_mb * 1000)
        
        logger.info(f"Processing {len(df)} rows in streaming mode with batch_size={batch_size}")
        
        results = []
        total_batches = (len(df) + batch_size - 1) // batch_size
        
        for i in range(0, len(df), batch_size):
            batch_num = i // batch_size + 1
            end_idx = min(i + batch_size, len(df))
            batch_df = df.iloc[i:end_idx].copy()
            
            with self.monitor.memory_context(f"Batch {batch_num}/{total_batches}"):
                processed_batch = operation(batch_df)
                results.append(processed_batch)
                
                # Clean up batch memory
                del batch_df
                gc.collect()
        
        # Combine results
        logger.info("Combining batch results...")
        return pd.concat(results, ignore_index=True)
    
    def optimize_dataframe_memory(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage through dtype optimization."""
        logger.info(f"Optimizing DataFrame memory usage: {len(df)} rows")
        
        original_memory = df.memory_usage(deep=True).sum() / 1024**2
        
        df_optimized = df.copy()
        
        for col in df_optimized.columns:
            col_type = df_optimized[col].dtype
            
            if col_type == 'object':
                # Try to convert to numeric first
                numeric_series = pd.to_numeric(df_optimized[col], errors='coerce')
                if not numeric_series.isna().all():
                    df_optimized[col] = numeric_series
                else:
                    # Convert to categorical if low cardinality
                    unique_ratio = df_optimized[col].nunique() / len(df_optimized)
                    if unique_ratio < 0.5:
                        df_optimized[col] = df_optimized[col].astype('category')
            
            elif col_type in ['int64', 'float64']:
                # Downcast numeric types
                if 'int' in str(col_type):
                    df_optimized[col] = pd.to_numeric(df_optimized[col], downcast='integer')
                else:
                    df_optimized[col] = pd.to_numeric(df_optimized[col], downcast='float')
        
        optimized_memory = df_optimized.memory_usage(deep=True).sum() / 1024**2
        memory_saved = original_memory - optimized_memory
        
        logger.info(f"Memory optimization: {original_memory:.1f}MB → {optimized_memory:.1f}MB "
                   f"(saved {memory_saved:.1f}MB, {memory_saved/original_memory*100:.1f}%)")
        
        self.monitor.stats.memory_saved_mb += memory_saved
        
        return df_optimized


# Global memory monitor instance
_global_monitor: Optional[MemoryMonitor] = None

def get_memory_monitor(config: Optional[MemoryConfig] = None) -> MemoryMonitor:
    """
    Get the global memory monitor instance.
    
    Args:
        config: Optional memory configuration
        
    Returns:
        MemoryMonitor instance
    """
    global _global_monitor
    
    if _global_monitor is None:
        _global_monitor = MemoryMonitor(config)
        _global_monitor.start_monitoring()
    
    return _global_monitor

def cleanup_global_monitor():
    """Clean up the global memory monitor."""
    global _global_monitor
    
    if _global_monitor is not None:
        _global_monitor.stop_monitoring()
        _global_monitor = None

@contextmanager
def memory_efficient_processing(config: Optional[MemoryConfig] = None):
    """Context manager for memory-efficient processing."""
    monitor = MemoryMonitor(config)
    processor = MemoryEfficientDataProcessor(monitor)
    
    monitor.start_monitoring()
    
    try:
        yield processor
    finally:
        monitor.stop_monitoring()
        
        # Log final statistics
        stats = monitor.stats
        logger.info(f"Memory processing completed: "
                   f"peak={stats.peak_memory_mb:.1f}MB, "
                   f"saved={stats.memory_saved_mb:.1f}MB, "
                   f"efficiency={stats.get_memory_efficiency()*100:.1f}%") 