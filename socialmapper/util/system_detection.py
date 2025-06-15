#!/usr/bin/env python3
"""
System Detection Utilities for SocialMapper.

This module provides utilities to detect system capabilities and resources
for optimal configuration and performance tuning.
"""

import multiprocessing as mp
import platform
from typing import Any, Dict, Optional

import psutil


def get_system_capabilities() -> Dict[str, Any]:
    """
    Get comprehensive system capability information.

    Returns:
        Dictionary with system information including CPU, memory, disk, and OS details
    """
    try:
        cpu_count = mp.cpu_count()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        return {
            # CPU Information
            "cpu_count": cpu_count,
            "cpu_count_physical": psutil.cpu_count(logical=False) or cpu_count,
            
            # Memory Information  
            "memory_total_gb": memory.total / 1024**3,
            "memory_available_gb": memory.available / 1024**3,
            "memory_used_gb": memory.used / 1024**3,
            "memory_percent_used": memory.percent,
            
            # Disk Information
            "disk_total_gb": disk.total / 1024**3,
            "disk_free_gb": disk.free / 1024**3,
            "disk_used_gb": disk.used / 1024**3,
            "disk_percent_used": (disk.used / disk.total) * 100,
            
            # System Information
            "platform": platform.system(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
        }
    except Exception as e:
        return {"error": str(e), "cpu_count": 1, "memory_total_gb": 1.0}


def get_optimal_worker_count(task_type: str = "cpu_bound") -> int:
    """
    Get optimal number of workers based on system capabilities and task type.

    Args:
        task_type: Type of task ("cpu_bound", "io_bound", "mixed")

    Returns:
        Optimal number of workers
    """
    cpu_count = mp.cpu_count()
    
    if task_type == "cpu_bound":
        # For CPU-bound tasks, use all cores
        return cpu_count
    elif task_type == "io_bound":
        # For I/O-bound tasks, can use more workers
        return min(32, cpu_count * 2)
    else:  # mixed or unknown
        # Conservative default
        return cpu_count


def get_available_memory_gb() -> float:
    """
    Get available system memory in GB.

    Returns:
        Available memory in gigabytes
    """
    try:
        memory = psutil.virtual_memory()
        return memory.available / 1024**3
    except Exception:
        return 1.0  # Conservative fallback


def get_total_memory_gb() -> float:
    """
    Get total system memory in GB.

    Returns:
        Total memory in gigabytes
    """
    try:
        memory = psutil.virtual_memory()
        return memory.total / 1024**3
    except Exception:
        return 1.0  # Conservative fallback


def get_free_disk_space_gb(path: str = "/") -> float:
    """
    Get free disk space in GB for the given path.

    Args:
        path: Path to check disk space for

    Returns:
        Free disk space in gigabytes
    """
    try:
        disk = psutil.disk_usage(path)
        return disk.free / 1024**3
    except Exception:
        return 1.0  # Conservative fallback


def is_memory_constrained() -> bool:
    """
    Determine if the system is memory constrained.

    Returns:
        True if system has limited memory (< 4GB)
    """
    return get_total_memory_gb() < 4.0


def is_high_performance_system() -> bool:
    """
    Determine if this is a high-performance system.

    Returns:
        True if system has abundant resources (>= 16GB RAM, >= 8 cores)
    """
    return get_total_memory_gb() >= 16.0 and mp.cpu_count() >= 8


def get_recommended_cache_size_gb() -> float:
    """
    Get recommended cache size based on available disk space.

    Returns:
        Recommended cache size in GB (10% of free space, max 20GB)
    """
    free_space = get_free_disk_space_gb()
    # Use 10% of free space, but cap at 20GB and minimum 0.5GB
    recommended = max(0.5, min(20.0, free_space * 0.1))
    return recommended


def get_recommended_memory_limit_gb() -> float:
    """
    Get recommended memory limit for processing.

    Returns:
        Recommended memory limit in GB (50% of total memory)
    """
    total_memory = get_total_memory_gb()
    # Use up to 50% of total memory, minimum 1GB
    return max(1.0, total_memory * 0.5)


def get_performance_tier() -> str:
    """
    Classify system performance tier.

    Returns:
        Performance tier: "low", "medium", "high", or "enterprise"
    """
    memory_gb = get_total_memory_gb()
    cpu_count = mp.cpu_count()
    
    if memory_gb >= 32 and cpu_count >= 16:
        return "enterprise"
    elif memory_gb >= 16 and cpu_count >= 8:
        return "high"
    elif memory_gb >= 8 and cpu_count >= 4:
        return "medium"
    else:
        return "low"


def validate_system_requirements() -> Dict[str, Any]:
    """
    Validate system meets minimum requirements for SocialMapper.

    Returns:
        Dictionary with validation results and warnings
    """
    memory_gb = get_total_memory_gb()
    cpu_count = mp.cpu_count()
    free_disk_gb = get_free_disk_space_gb()
    
    warnings = []
    errors = []
    
    # Check minimum requirements
    if memory_gb < 2.0:
        errors.append(f"Insufficient memory: {memory_gb:.1f}GB (minimum 2GB required)")
    elif memory_gb < 4.0:
        warnings.append(f"Low memory: {memory_gb:.1f}GB (4GB+ recommended)")
    
    if cpu_count < 2:
        warnings.append(f"Limited CPU cores: {cpu_count} (2+ recommended)")
    
    if free_disk_gb < 1.0:
        errors.append(f"Insufficient disk space: {free_disk_gb:.1f}GB (minimum 1GB required)")
    elif free_disk_gb < 5.0:
        warnings.append(f"Limited disk space: {free_disk_gb:.1f}GB (5GB+ recommended)")
    
    return {
        "meets_requirements": len(errors) == 0,
        "performance_tier": get_performance_tier(),
        "warnings": warnings,
        "errors": errors,
        "recommendations": _get_system_recommendations(memory_gb, cpu_count, free_disk_gb),
    }


def _get_system_recommendations(memory_gb: float, cpu_count: int, free_disk_gb: float) -> list[str]:
    """Get system-specific recommendations."""
    recommendations = []
    
    if memory_gb < 8.0:
        recommendations.append("Consider increasing memory for better performance with large datasets")
    
    if cpu_count < 4:
        recommendations.append("More CPU cores would improve parallel processing performance")
    
    if free_disk_gb < 10.0:
        recommendations.append("More disk space recommended for caching and large outputs")
    
    if memory_gb >= 16.0 and cpu_count >= 8:
        recommendations.append("System well-suited for high-performance configurations")
    
    return recommendations 