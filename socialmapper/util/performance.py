"""
Performance measurement utilities for SocialMapper.

This module provides tools for measuring and comparing performance
of different processing methods, particularly for isochrone generation.
"""

import time
import functools
import logging
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
import json
import os
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    operation: str
    start_time: float
    end_time: float
    duration: float
    memory_usage_mb: Optional[float] = None
    additional_metrics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_formatted(self) -> str:
        """Return formatted duration string."""
        if self.duration < 1:
            return f"{self.duration * 1000:.2f}ms"
        elif self.duration < 60:
            return f"{self.duration:.2f}s"
        else:
            minutes, seconds = divmod(self.duration, 60)
            return f"{int(minutes)}m {seconds:.2f}s"

class PerformanceBenchmark:
    """
    Performance benchmarking utility for comparing different implementations.
    """
    
    def __init__(self, name: str = "benchmark"):
        self.name = name
        self.metrics: List[PerformanceMetrics] = []
        self.comparisons: Dict[str, List[PerformanceMetrics]] = {}
    
    @contextmanager
    def measure(self, operation: str, **additional_metrics):
        """
        Context manager for measuring operation performance.
        
        Args:
            operation: Name of the operation being measured
            **additional_metrics: Additional metrics to track
        """
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            duration = end_time - start_time
            memory_delta = end_memory - start_memory if start_memory and end_memory else None
            
            metrics = PerformanceMetrics(
                operation=operation,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                memory_usage_mb=memory_delta,
                additional_metrics=additional_metrics
            )
            
            self.metrics.append(metrics)
            logger.info(f"Operation '{operation}' completed in {metrics.duration_formatted}")
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return None
    
    def add_comparison_group(self, group_name: str):
        """Add a new comparison group."""
        if group_name not in self.comparisons:
            self.comparisons[group_name] = []
    
    def add_to_comparison(self, group_name: str, metrics: PerformanceMetrics):
        """Add metrics to a comparison group."""
        if group_name not in self.comparisons:
            self.comparisons[group_name] = []
        self.comparisons[group_name].append(metrics)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.metrics:
            return {"message": "No metrics recorded"}
        
        total_duration = sum(m.duration for m in self.metrics)
        avg_duration = total_duration / len(self.metrics)
        
        summary = {
            "benchmark_name": self.name,
            "total_operations": len(self.metrics),
            "total_duration": total_duration,
            "average_duration": avg_duration,
            "operations": []
        }
        
        # Group by operation type
        operations = {}
        for metric in self.metrics:
            if metric.operation not in operations:
                operations[metric.operation] = []
            operations[metric.operation].append(metric)
        
        for op_name, op_metrics in operations.items():
            op_summary = {
                "operation": op_name,
                "count": len(op_metrics),
                "total_duration": sum(m.duration for m in op_metrics),
                "average_duration": sum(m.duration for m in op_metrics) / len(op_metrics),
                "min_duration": min(m.duration for m in op_metrics),
                "max_duration": max(m.duration for m in op_metrics)
            }
            summary["operations"].append(op_summary)
        
        return summary
    
    def compare_groups(self) -> Dict[str, Any]:
        """Compare performance between different groups."""
        if len(self.comparisons) < 2:
            return {"message": "Need at least 2 comparison groups"}
        
        comparison_results = {}
        
        for group_name, group_metrics in self.comparisons.items():
            if not group_metrics:
                continue
                
            total_duration = sum(m.duration for m in group_metrics)
            avg_duration = total_duration / len(group_metrics)
            
            comparison_results[group_name] = {
                "count": len(group_metrics),
                "total_duration": total_duration,
                "average_duration": avg_duration,
                "min_duration": min(m.duration for m in group_metrics),
                "max_duration": max(m.duration for m in group_metrics)
            }
        
        # Calculate improvements
        if len(comparison_results) == 2:
            groups = list(comparison_results.keys())
            baseline = comparison_results[groups[0]]
            improved = comparison_results[groups[1]]
            
            speedup = baseline["average_duration"] / improved["average_duration"]
            time_saved = baseline["total_duration"] - improved["total_duration"]
            
            comparison_results["improvement"] = {
                "speedup_factor": speedup,
                "time_saved_seconds": time_saved,
                "percentage_improvement": ((baseline["average_duration"] - improved["average_duration"]) / baseline["average_duration"]) * 100
            }
        
        return comparison_results
    
    def save_results(self, output_path: str):
        """Save benchmark results to file."""
        results = {
            "benchmark_name": self.name,
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "comparisons": self.compare_groups() if self.comparisons else {},
            "raw_metrics": [
                {
                    "operation": m.operation,
                    "duration": m.duration,
                    "memory_usage_mb": m.memory_usage_mb,
                    "additional_metrics": m.additional_metrics
                }
                for m in self.metrics
            ]
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Benchmark results saved to {output_path}")
    
    def print_summary(self):
        """Print a formatted summary of the benchmark results."""
        summary = self.get_summary()
        
        print(f"\n{'='*60}")
        print(f"Performance Benchmark: {self.name}")
        print(f"{'='*60}")
        
        if "message" in summary:
            print(summary["message"])
            return
        
        print(f"Total Operations: {summary['total_operations']}")
        print(f"Total Duration: {summary['total_duration']:.2f}s")
        print(f"Average Duration: {summary['average_duration']:.2f}s")
        
        print(f"\nOperation Breakdown:")
        print(f"{'Operation':<20} {'Count':<8} {'Total':<12} {'Average':<12} {'Min':<10} {'Max':<10}")
        print("-" * 80)
        
        for op in summary["operations"]:
            print(f"{op['operation']:<20} {op['count']:<8} {op['total_duration']:<12.2f} "
                  f"{op['average_duration']:<12.2f} {op['min_duration']:<10.2f} {op['max_duration']:<10.2f}")
        
        # Print comparisons if available
        if self.comparisons:
            comparison = self.compare_groups()
            if "improvement" in comparison:
                print(f"\nPerformance Comparison:")
                print(f"{'='*40}")
                imp = comparison["improvement"]
                print(f"Speedup Factor: {imp['speedup_factor']:.2f}x")
                print(f"Time Saved: {imp['time_saved_seconds']:.2f}s")
                print(f"Percentage Improvement: {imp['percentage_improvement']:.1f}%")

def performance_timer(operation_name: str = None):
    """
    Decorator for timing function execution.
    
    Args:
        operation_name: Name of the operation (defaults to function name)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                logger.info(f"Function '{op_name}' completed in {duration:.2f}s")
        
        return wrapper
    return decorator

class IsochroneBenchmark(PerformanceBenchmark):
    """
    Specialized benchmark for isochrone generation performance.
    """
    
    def __init__(self):
        super().__init__("isochrone_generation")
        self.poi_count = 0
        self.network_stats = {}
    
    def set_poi_count(self, count: int):
        """Set the number of POIs being processed."""
        self.poi_count = count
    
    def record_network_stats(self, poi_id: str, node_count: int, edge_count: int):
        """Record network statistics for a POI."""
        self.network_stats[poi_id] = {
            "nodes": node_count,
            "edges": edge_count
        }
    
    def get_isochrone_summary(self) -> Dict[str, Any]:
        """Get isochrone-specific summary."""
        summary = self.get_summary()
        summary["poi_count"] = self.poi_count
        summary["network_stats"] = self.network_stats
        
        if self.network_stats:
            total_nodes = sum(stats["nodes"] for stats in self.network_stats.values())
            total_edges = sum(stats["edges"] for stats in self.network_stats.values())
            summary["total_network_nodes"] = total_nodes
            summary["total_network_edges"] = total_edges
            summary["avg_nodes_per_poi"] = total_nodes / len(self.network_stats)
            summary["avg_edges_per_poi"] = total_edges / len(self.network_stats)
        
        return summary 