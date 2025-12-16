#!/usr/bin/env python3
"""Modern Progress Tracking System for SocialMapper.

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

import logging
import threading
import time
from collections.abc import Callable
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union

# Import Rich progress bar libraries directly
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    Task,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.text import Text

# Create console instance
console = Console()

# Setup logging
logger = logging.getLogger(__name__)


# Rich Progress Components (moved from console module)
class RichProgressColumn(ProgressColumn):
    """Custom progress column displaying processing speed."""

    def render(self, task: "Task") -> Text:
        """Render the progress speed indicator."""
        if task.speed is None:
            return Text("", style="progress.percentage")

        if task.speed >= 1:
            return Text(f"{task.speed:.1f} items/sec", style="progress.percentage")
        else:
            return Text(f"{1 / task.speed:.1f} sec/item", style="progress.percentage")


class RichProgressWrapper:
    """tqdm-compatible wrapper for Rich progress bars."""

    def __init__(self, iterable=None, desc="", total=None, unit="it", **kwargs):
        """Initialize Rich progress bar with tqdm-compatible interface.

        Parameters
        ----------
        iterable : iterable, optional
            Iterable to wrap with progress bar, by default None.
        desc : str, optional
            Description text for progress bar, by default "".
        total : int, optional
            Total number of iterations, by default None.
        unit : str, optional
            Unit name for items being processed, by default "it".
        **kwargs : dict
            Additional keyword arguments (for compatibility).
        """
        self.iterable = iterable
        self.desc = desc
        self.total = total or (len(iterable) if iterable else None)
        self.unit = unit
        self.position = 0
        self.n = 0  # Add n attribute for tqdm compatibility
        self.task_id = None
        self.progress_instance = None

        # Create progress instance
        self.progress_instance = Progress(
            SpinnerColumn(),
            TextColumn(f"[progress.description]{desc}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            TextColumn("•"),
            RichProgressColumn(),
            console=console,
            refresh_per_second=10,
        )

        # Use try-except to handle Rich live display conflicts
        try:
            self.progress_instance.start()
            self.task_id = self.progress_instance.add_task(desc, total=self.total)
        except (RuntimeError, ValueError, AttributeError, OSError):
            # Graceful degradation when Rich progress bar can't start
            total_msg = f" ({self.total} items)" if self.total else ""
            console.print(f"🔄 {desc}{total_msg}")
            self.progress_instance = None
            self.task_id = None

    def __iter__(self):
        """Iterate with automatic progress updates."""
        if self.iterable:
            for item in self.iterable:
                yield item
                self.update(1)

    def __enter__(self):
        """Enter progress bar context."""
        return self

    def __exit__(self, *args):
        """Exit context and cleanup progress display."""
        self.close()

    def update(self, n=1):
        """Advance progress bar by specified amount."""
        if self.progress_instance and self.task_id is not None:
            with suppress(Exception):
                self.progress_instance.update(self.task_id, advance=n)
        self.position += n
        self.n += n

        # If no progress display, show individual updates for detailed tracking
        if self.progress_instance is None and self.total:
            percentage = (self.position / self.total) * 100
            console.print(f"  Progress: {self.position}/{self.total} ({percentage:.1f}%)")

    def set_description(self, desc):
        """Update the progress bar description text."""
        if self.progress_instance and self.task_id is not None:
            self.progress_instance.update(self.task_id, description=desc)

    def set_postfix(self, postfix_dict):
        """Update the progress bar postfix (tqdm compatibility)."""
        # Rich progress bars don't have postfix, but we'll store it for compatibility

    def refresh(self):
        """Refresh the progress bar display (tqdm compatibility)."""
        if self.progress_instance and self.task_id is not None:
            self.progress_instance.refresh()

    def close(self):
        """Stop and remove the progress bar display."""
        if self.progress_instance:
            try:
                self.progress_instance.stop()
            except (RuntimeError, ValueError, AttributeError, OSError):
                pass  # Graceful degradation on close
            finally:
                self.progress_instance = None
                self.task_id = None

    def write(self, message):
        """Write message to console above progress bar."""
        console.print(message)


def rich_tqdm(*args, **kwargs):
    """Create tqdm-compatible progress bar using Rich."""
    return RichProgressWrapper(*args, **kwargs)


@contextmanager
def progress_bar(
    description: str, total: int | None = None, transient: bool = False, disable: bool = False
):
    """Context manager for Rich progress bar display."""
    if disable:
        class DummyProgress:
            def add_task(self, *args, **kwargs):
                return 0

            def update(self, *args, **kwargs):
                pass

            def advance(self, *args, **kwargs):
                pass

        yield DummyProgress()
        return

    custom_progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        TextColumn("•"),
        RichProgressColumn(),
        console=console,
        transient=transient,
        refresh_per_second=10,
    )

    with custom_progress:
        task_id = custom_progress.add_task(description, total=total)
        custom_progress.task_id = task_id
        yield custom_progress


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
    total_items: int | None = None
    throughput_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    estimated_time_remaining: float | None = None

    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time

    def update_throughput(self):
        """Update throughput calculation."""
        elapsed = self.get_elapsed_time()
        if elapsed > 0:
            self.throughput_per_second = self.items_processed / elapsed

    def estimate_time_remaining(self) -> float | None:
        """Estimate remaining time based on current throughput."""
        if self.total_items and self.throughput_per_second > 0:
            remaining_items = self.total_items - self.items_processed
            return remaining_items / self.throughput_per_second
        return None


class ModernProgressTracker:
    """Modern progress tracker for the optimized SocialMapper pipeline.

    This class provides intelligent progress tracking using tqdm for excellent
    user experience with proper progress bars and performance metrics.
    """

    def __init__(self, enable_performance_metrics: bool = True):
        """Initialize the modern progress tracker.

        Parameters
        ----------
        enable_performance_metrics : bool, optional
            Whether to track performance metrics, by default True.
        """
        self.enable_performance_metrics = enable_performance_metrics
        self.current_stage: ProcessingStage | None = None
        self.stage_metrics: dict[ProcessingStage, ProgressMetrics] = {}
        self.current_pbar: RichProgressWrapper | None = None
        self._lock = threading.Lock()

        # Stage descriptions for user-friendly output
        self.stage_descriptions = {
            ProcessingStage.SETUP: "Setting up analysis environment",
            ProcessingStage.POI_PROCESSING: "Processing points of interest",
            ProcessingStage.ISOCHRONE_GENERATION: "Generating travel time areas",
            ProcessingStage.CENSUS_INTEGRATION: "Integrating census data",
            ProcessingStage.EXPORT_VISUALIZATION: "Exporting results and creating visualizations",
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
            "map_generation": "Creating visualizations",
        }

    def start_stage(
        self, stage: ProcessingStage, total_items: int | None = None
    ) -> ProgressMetrics:
        """Start tracking a new processing stage with tqdm progress bar.

        Parameters
        ----------
        stage : ProcessingStage
            The processing stage to start.
        total_items : int or None, optional
            Total number of items to process, by default None.

        Returns
        -------
        ProgressMetrics
            ProgressMetrics object for this stage.
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

            # Create new progress bar using Rich
            self.current_pbar = rich_tqdm(total=total_items, desc=f"🚀 {description}", unit="items")

            logger.info(f"Starting stage: {description}")

            return metrics

    def update_progress(
        self,
        items_processed: int,
        substage: str | None = None,
        memory_usage_mb: float | None = None,
    ) -> None:
        """Update progress for the current stage with tqdm.

        Parameters
        ----------
        items_processed : int
            Number of items processed.
        substage : str or None, optional
            Substage description, by default None.
        memory_usage_mb : float or None, optional
            Memory usage in MB, by default None.
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
                stage_desc = self.stage_descriptions.get(
                    self.current_stage, str(self.current_stage)
                )
                self.current_pbar.set_description(f"🚀 {stage_desc} - {substage_desc}")

            # Update postfix with performance metrics
            if self.enable_performance_metrics and metrics.throughput_per_second > 0:
                postfix_dict = {}

                if metrics.throughput_per_second >= 1:
                    postfix_dict["rate"] = f"{metrics.throughput_per_second:.1f}/s"
                else:
                    postfix_dict["rate"] = f"{1 / metrics.throughput_per_second:.1f}s/item"

                if memory_usage_mb:
                    postfix_dict["mem"] = f"{memory_usage_mb:.0f}MB"

                self.current_pbar.set_postfix(postfix_dict)

    def complete_stage(self, stage: ProcessingStage) -> None:
        """Mark a processing stage as complete and close progress bar.

        Parameters
        ----------
        stage : ProcessingStage
            The processing stage to complete.
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
                            completion_msg += f" ({1 / avg_throughput:.1f} sec/item)"

                self.current_pbar.set_description(completion_msg)
                self.current_pbar.close()
                self.current_pbar = None

                logger.info(f"Completed stage: {description} in {elapsed:.1f}s")

    def get_stage_metrics(self, stage: ProcessingStage) -> ProgressMetrics | None:
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

        # Use Rich console to print summary
        console.print("\n📊 Processing Summary:")
        console.print(f"   Total time: {total_time:.1f}s")

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
                        rate_str = f" ({1 / throughput:.1f} sec/item)"
                else:
                    rate_str = ""

                console.print(f"   {description}: {elapsed:.1f}s{rate_str}")


# Global progress tracker instance
_global_tracker: ModernProgressTracker | None = None


def get_progress_tracker(enable_performance_metrics: bool = True) -> ModernProgressTracker:
    """Get the global progress tracker instance.

    Parameters
    ----------
    enable_performance_metrics : bool, optional
        Whether to enable performance metrics, by default True.

    Returns
    -------
    ModernProgressTracker
        ModernProgressTracker instance.
    """
    global _global_tracker

    if _global_tracker is None:
        _global_tracker = ModernProgressTracker(enable_performance_metrics)

    return _global_tracker


def get_progress_bar(iterable=None, **kwargs):
    """Return the appropriate progress bar based on the execution context.

    This function provides Rich tqdm progress bars for CLI usage.

    Parameters
    ----------
    iterable : iterable, optional
        The iterable to wrap with a progress bar, by default None.
    **kwargs : dict
        Additional arguments to pass to the progress bar.

    Returns
    -------
    RichProgressWrapper
        A Rich progress bar instance that can be used as a context
        manager.
    """
    # Always use Rich progress bars
    progress_bar_class = rich_tqdm

    # Always return an instance, not a class
    if iterable is not None:
        return progress_bar_class(iterable, **kwargs)
    else:
        # Create an instance with the provided kwargs
        return progress_bar_class(**kwargs)


@contextmanager
def track_stage(stage: ProcessingStage, total_items: int | None = None):
    """Context manager for tracking a processing stage with tqdm progress bar.

    Parameters
    ----------
    stage : ProcessingStage
        The processing stage to track.
    total_items : int or None, optional
        Total number of items to process, by default None.

    Yields
    ------
    ProgressMetrics
        ProgressMetrics object for updating progress.
    """
    tracker = get_progress_tracker()
    metrics = tracker.start_stage(stage, total_items)

    try:
        yield metrics
    finally:
        tracker.complete_stage(stage)


# Convenience functions for common progress tracking patterns
def track_poi_processing(total_pois: int | None = None):
    """Track POI processing stage with tqdm progress bar."""
    return track_stage(ProcessingStage.POI_PROCESSING, total_pois)


def track_isochrone_generation(total_pois: int | None = None):
    """Track isochrone generation stage with tqdm progress bar."""
    return track_stage(ProcessingStage.ISOCHRONE_GENERATION, total_pois)


def track_census_integration(total_block_groups: int | None = None):
    """Track census integration stage with tqdm progress bar."""
    return track_stage(ProcessingStage.CENSUS_INTEGRATION, total_block_groups)


def track_export_visualization(total_outputs: int | None = None):
    """Track export and visualization stage with tqdm progress bar."""
    return track_stage(ProcessingStage.EXPORT_VISUALIZATION, total_outputs)


# Enhanced progress bar creation functions for specific use cases
def create_poi_progress_bar(total_pois: int, desc: str = "Processing POIs") -> RichProgressWrapper:
    """Create a progress bar specifically for POI processing."""
    return rich_tqdm(total=total_pois, desc=f"🎯 {desc}", unit="POI")


def create_isochrone_progress_bar(
    total_isochrones: int, desc: str = "Generating Isochrones"
) -> RichProgressWrapper:
    """Create a progress bar specifically for isochrone generation."""
    return rich_tqdm(total=total_isochrones, desc=f"🗺️ {desc}", unit="isochrone")


def create_census_progress_bar(
    total_blocks: int, desc: str = "Processing Census Data"
) -> RichProgressWrapper:
    """Create a progress bar specifically for census data processing."""
    return rich_tqdm(total=total_blocks, desc=f"📊 {desc}", unit="block")


def create_network_progress_bar(
    total_networks: int, desc: str = "Downloading Networks"
) -> RichProgressWrapper:
    """Create a progress bar specifically for network downloads."""
    return rich_tqdm(total=total_networks, desc=f"🌐 {desc}", unit="network")
