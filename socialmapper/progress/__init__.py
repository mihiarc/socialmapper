#!/usr/bin/env python3
"""
Modern Progress Tracking System for SocialMapper.

This module provides intelligent progress tracking using tqdm for excellent
user experience with proper progress bars and performance metrics.

Key Features:
- Beautiful tqdm progress bars with performance metrics
- Streamlined progress tracking for optimized pipeline stages
- Intelligent context detection (CLI vs Streamlit)
- Memory usage monitoring integration
- Adaptive progress reporting based on dataset size
- Clean, professional output with minimal noise

Optimized Pipeline Stages (from OPTIMIZATION_PLAN.md):
1. Setup & Validation
2. POI Processing (Query/Custom Coords)
3. Isochrone Generation (Clustering + Concurrent Processing)
4. Census Data Integration (Streaming + Distance Calculation)
5. Export & Visualization (Modern Formats)
"""

import time
import threading
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
from enum import Enum
import logging

# Import progress bar libraries
from tqdm import tqdm

# Streamlit detection and import
_IN_STREAMLIT = False
try:
    import streamlit as st
    from streamlit import runtime
    if runtime.exists():
        _IN_STREAMLIT = True
        from stqdm import stqdm
except (ImportError, ModuleNotFoundError):
    pass

logger = logging.getLogger(__name__)


class ProcessingStage(Enum):
    """Enumeration of main processing stages in the optimized pipeline."""
    SETUP = "setup"
    POI_PROCESSING = "poi_processing"
    ISOCHRONE_GENERATION = "isochrone_generation"
    CENSUS_INTEGRATION = "census_integration"
    EXPORT_VISUALIZATION = "export_visualization"


@dataclass
class ProgressMetrics:
    """Performance metrics for progress tracking."""
    stage: ProcessingStage
    start_time: float = field(default_factory=time.time)
    items_processed: int = 0
    total_items: Optional[int] = None
    throughput_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    estimated_time_remaining: Optional[float] = None
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
    
    def update_throughput(self):
        """Update throughput calculation."""
        elapsed = self.get_elapsed_time()
        if elapsed > 0:
            self.throughput_per_second = self.items_processed / elapsed
    
    def estimate_time_remaining(self) -> Optional[float]:
        """Estimate remaining time based on current throughput."""
        if self.total_items and self.throughput_per_second > 0:
            remaining_items = self.total_items - self.items_processed
            return remaining_items / self.throughput_per_second
        return None


class ModernProgressTracker:
    """
    Modern progress tracker for the optimized SocialMapper pipeline.
    
    This class provides intelligent progress tracking using tqdm for excellent
    user experience with proper progress bars and performance metrics.
    """
    
    def __init__(self, enable_performance_metrics: bool = True):
        """
        Initialize the modern progress tracker.
        
        Args:
            enable_performance_metrics: Whether to track performance metrics
        """
        self.enable_performance_metrics = enable_performance_metrics
        self.current_stage: Optional[ProcessingStage] = None
        self.stage_metrics: Dict[ProcessingStage, ProgressMetrics] = {}
        self.current_pbar: Optional[Union[tqdm, 'stqdm']] = None
        self._lock = threading.Lock()
        
        # Stage descriptions for user-friendly output
        self.stage_descriptions = {
            ProcessingStage.SETUP: "Setting up analysis environment",
            ProcessingStage.POI_PROCESSING: "Processing points of interest",
            ProcessingStage.ISOCHRONE_GENERATION: "Generating travel time areas",
            ProcessingStage.CENSUS_INTEGRATION: "Integrating census data",
            ProcessingStage.EXPORT_VISUALIZATION: "Exporting results and creating visualizations"
        }
        
        # Substage descriptions for detailed progress
        self.substage_descriptions = {
            "poi_query": "Querying OpenStreetMap",
            "poi_validation": "Validating POI data",
            "clustering": "Optimizing POI clusters",
            "network_download": "Downloading road networks",
            "isochrone_calculation": "Calculating travel areas",
            "block_group_intersection": "Finding census areas",
            "distance_calculation": "Calculating travel distances",
            "census_data_fetch": "Retrieving census statistics",
            "data_export": "Exporting data files",
            "map_generation": "Creating visualizations"
        }
    
    def start_stage(self, stage: ProcessingStage, total_items: Optional[int] = None) -> ProgressMetrics:
        """
        Start tracking a new processing stage with tqdm progress bar.
        
        Args:
            stage: The processing stage to start
            total_items: Optional total number of items to process
            
        Returns:
            ProgressMetrics object for this stage
        """
        with self._lock:
            # Close any existing progress bar
            if self.current_pbar is not None:
                self.current_pbar.close()
                self.current_pbar = None
            
            self.current_stage = stage
            metrics = ProgressMetrics(stage=stage, total_items=total_items)
            self.stage_metrics[stage] = metrics
            
            # Get stage description
            description = self.stage_descriptions.get(stage, str(stage))
            
            # Create new progress bar
            progress_bar_class = stqdm if _IN_STREAMLIT else tqdm
            
            # Configure progress bar with performance metrics
            bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
            
            self.current_pbar = progress_bar_class(
                total=total_items,
                desc=f"🚀 {description}",
                unit="items",
                bar_format=bar_format,
                dynamic_ncols=True,
                leave=True
            )
            
            logger.info(f"Starting stage: {description}")
            
            return metrics
    
    def update_progress(self, 
                       items_processed: int, 
                       substage: Optional[str] = None,
                       memory_usage_mb: Optional[float] = None) -> None:
        """
        Update progress for the current stage with tqdm.
        
        Args:
            items_processed: Number of items processed
            substage: Optional substage description
            memory_usage_mb: Optional memory usage in MB
        """
        if not self.current_stage:
            return
        
        # Check if progress bar exists more safely
        if self.current_pbar is None:
            return
        
        with self._lock:
            metrics = self.stage_metrics.get(self.current_stage)
            if not metrics:
                return
            
            # Calculate progress delta
            progress_delta = items_processed - metrics.items_processed
            metrics.items_processed = items_processed
            
            if memory_usage_mb:
                metrics.memory_usage_mb = memory_usage_mb
            
            if self.enable_performance_metrics:
                metrics.update_throughput()
                metrics.estimated_time_remaining = metrics.estimate_time_remaining()
            
            # Update progress bar
            if progress_delta > 0:
                self.current_pbar.update(progress_delta)
            
            # Update description with substage if provided
            if substage:
                substage_desc = self.substage_descriptions.get(substage, substage)
                stage_desc = self.stage_descriptions.get(self.current_stage, str(self.current_stage))
                self.current_pbar.set_description(f"🚀 {stage_desc} - {substage_desc}")
            
            # Update postfix with performance metrics
            if self.enable_performance_metrics and metrics.throughput_per_second > 0:
                postfix_dict = {}
                
                if metrics.throughput_per_second >= 1:
                    postfix_dict["rate"] = f"{metrics.throughput_per_second:.1f}/s"
                else:
                    postfix_dict["rate"] = f"{1/metrics.throughput_per_second:.1f}s/item"
                
                if memory_usage_mb:
                    postfix_dict["mem"] = f"{memory_usage_mb:.0f}MB"
                
                self.current_pbar.set_postfix(postfix_dict)
    
    def complete_stage(self, stage: ProcessingStage) -> None:
        """
        Mark a processing stage as complete and close progress bar.
        
        Args:
            stage: The processing stage to complete
        """
        with self._lock:
            metrics = self.stage_metrics.get(stage)
            if metrics and self.current_pbar is not None:
                elapsed = metrics.get_elapsed_time()
                description = self.stage_descriptions.get(stage, str(stage))
                
                # Ensure progress bar shows completion
                if metrics.total_items:
                    self.current_pbar.n = metrics.total_items
                    self.current_pbar.refresh()
                
                # Update final description
                completion_msg = f"✅ {description} completed"
                if self.enable_performance_metrics:
                    completion_msg += f" in {elapsed:.1f}s"
                    if metrics.items_processed > 0 and elapsed > 0:
                        avg_throughput = metrics.items_processed / elapsed
                        if avg_throughput >= 1:
                            completion_msg += f" ({avg_throughput:.1f} items/sec)"
                        else:
                            completion_msg += f" ({1/avg_throughput:.1f} sec/item)"
                
                self.current_pbar.set_description(completion_msg)
                self.current_pbar.close()
                self.current_pbar = None
                
                logger.info(f"Completed stage: {description} in {elapsed:.1f}s")
    
    def get_stage_metrics(self, stage: ProcessingStage) -> Optional[ProgressMetrics]:
        """Get metrics for a specific stage."""
        return self.stage_metrics.get(stage)
    
    def get_total_elapsed_time(self) -> float:
        """Get total elapsed time across all stages."""
        if not self.stage_metrics:
            return 0.0
        
        earliest_start = min(metrics.start_time for metrics in self.stage_metrics.values())
        return time.time() - earliest_start
    
    def print_summary(self) -> None:
        """Print a summary of all processing stages."""
        if not self.stage_metrics:
            return
        
        total_time = self.get_total_elapsed_time()
        
        # Use tqdm.write to avoid interfering with progress bars
        tqdm.write("\n📊 Processing Summary:")
        tqdm.write(f"   Total time: {total_time:.1f}s")
        
        for stage in ProcessingStage:
            metrics = self.stage_metrics.get(stage)
            if metrics:
                elapsed = metrics.get_elapsed_time()
                description = self.stage_descriptions.get(stage, str(stage))
                
                if metrics.items_processed > 0 and elapsed > 0:
                    throughput = metrics.items_processed / elapsed
                    if throughput >= 1:
                        rate_str = f" ({throughput:.1f} items/sec)"
                    else:
                        rate_str = f" ({1/throughput:.1f} sec/item)"
                else:
                    rate_str = ""
                
                tqdm.write(f"   {description}: {elapsed:.1f}s{rate_str}")


# Global progress tracker instance
_global_tracker: Optional[ModernProgressTracker] = None


def get_progress_tracker(enable_performance_metrics: bool = True) -> ModernProgressTracker:
    """
    Get the global progress tracker instance.
    
    Args:
        enable_performance_metrics: Whether to enable performance metrics
        
    Returns:
        ModernProgressTracker instance
    """
    global _global_tracker
    
    if _global_tracker is None:
        _global_tracker = ModernProgressTracker(enable_performance_metrics)
    
    return _global_tracker


def get_progress_bar(iterable=None, **kwargs):
    """
    Return the appropriate progress bar based on the execution context.
    
    This function provides tqdm progress bars for both CLI and Streamlit contexts.
    
    Args:
        iterable: The iterable to wrap with a progress bar
        **kwargs: Additional arguments to pass to the progress bar
        
    Returns:
        A progress bar instance that can be used as a context manager
    """
    # Use the environment detection done at import time
    progress_bar_class = stqdm if _IN_STREAMLIT else tqdm
    
    # Always return an instance, not a class
    if iterable is not None:
        return progress_bar_class(iterable, **kwargs)
    else:
        # Create an instance with the provided kwargs
        return progress_bar_class(**kwargs)


@contextmanager
def track_stage(stage: ProcessingStage, total_items: Optional[int] = None):
    """
    Context manager for tracking a processing stage with tqdm progress bar.
    
    Args:
        stage: The processing stage to track
        total_items: Optional total number of items to process
        
    Yields:
        ProgressMetrics object for updating progress
    """
    tracker = get_progress_tracker()
    metrics = tracker.start_stage(stage, total_items)
    
    try:
        yield metrics
    finally:
        tracker.complete_stage(stage)


# Convenience functions for common progress tracking patterns
def track_poi_processing(total_pois: Optional[int] = None):
    """Track POI processing stage with tqdm progress bar."""
    return track_stage(ProcessingStage.POI_PROCESSING, total_pois)


def track_isochrone_generation(total_pois: Optional[int] = None):
    """Track isochrone generation stage with tqdm progress bar."""
    return track_stage(ProcessingStage.ISOCHRONE_GENERATION, total_pois)


def track_census_integration(total_block_groups: Optional[int] = None):
    """Track census integration stage with tqdm progress bar."""
    return track_stage(ProcessingStage.CENSUS_INTEGRATION, total_block_groups)


def track_export_visualization(total_outputs: Optional[int] = None):
    """Track export and visualization stage with tqdm progress bar."""
    return track_stage(ProcessingStage.EXPORT_VISUALIZATION, total_outputs)


# Enhanced progress bar creation functions for specific use cases
def create_poi_progress_bar(total_pois: int, desc: str = "Processing POIs") -> Union[tqdm, 'stqdm']:
    """Create a progress bar specifically for POI processing."""
    progress_bar_class = stqdm if _IN_STREAMLIT else tqdm
    return progress_bar_class(
        total=total_pois,
        desc=f"🎯 {desc}",
        unit="POI",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} POIs [{elapsed}<{remaining}, {rate_fmt}]",
        dynamic_ncols=True
    )


def create_isochrone_progress_bar(total_isochrones: int, desc: str = "Generating Isochrones") -> Union[tqdm, 'stqdm']:
    """Create a progress bar specifically for isochrone generation."""
    progress_bar_class = stqdm if _IN_STREAMLIT else tqdm
    return progress_bar_class(
        total=total_isochrones,
        desc=f"🗺️ {desc}",
        unit="isochrone",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} isochrones [{elapsed}<{remaining}, {rate_fmt}]",
        dynamic_ncols=True
    )


def create_census_progress_bar(total_blocks: int, desc: str = "Processing Census Data") -> Union[tqdm, 'stqdm']:
    """Create a progress bar specifically for census data processing."""
    progress_bar_class = stqdm if _IN_STREAMLIT else tqdm
    return progress_bar_class(
        total=total_blocks,
        desc=f"📊 {desc}",
        unit="block",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} blocks [{elapsed}<{remaining}, {rate_fmt}]",
        dynamic_ncols=True
    )


def create_network_progress_bar(total_networks: int, desc: str = "Downloading Networks") -> Union[tqdm, 'stqdm']:
    """Create a progress bar specifically for network downloads."""
    progress_bar_class = stqdm if _IN_STREAMLIT else tqdm
    return progress_bar_class(
        total=total_networks,
        desc=f"🌐 {desc}",
        unit="network",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} networks [{elapsed}<{remaining}, {rate_fmt}]",
        dynamic_ncols=True
    ) 