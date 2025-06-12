#!/usr/bin/env python3
"""
Configuration package for SocialMapper optimization.

This package provides centralized configuration management for all
optimization settings and performance tuning.
"""

from .optimization import (
    OPTIMIZED_CONFIG,
    DistanceConfig,
    IOConfig,
    IsochroneConfig,
    MemoryConfig,
    OptimizationConfig,
    PerformancePresets,
    get_config,
    reset_config,
    update_config,
)

__all__ = [
    "OptimizationConfig",
    "DistanceConfig",
    "IsochroneConfig",
    "MemoryConfig",
    "IOConfig",
    "PerformancePresets",
    "get_config",
    "update_config",
    "reset_config",
    "OPTIMIZED_CONFIG",
]
