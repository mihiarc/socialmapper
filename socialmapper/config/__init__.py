#!/usr/bin/env python3
"""
Configuration package for SocialMapper optimization.

This package provides centralized configuration management for all
optimization settings and performance tuning.
"""

from .optimization import (
    OptimizationConfig,
    DistanceConfig,
    IsochroneConfig,
    MemoryConfig,
    IOConfig,
    PerformancePresets,
    get_config,
    update_config,
    reset_config,
    OPTIMIZED_CONFIG
)

__all__ = [
    'OptimizationConfig',
    'DistanceConfig', 
    'IsochroneConfig',
    'MemoryConfig',
    'IOConfig',
    'PerformancePresets',
    'get_config',
    'update_config', 
    'reset_config',
    'OPTIMIZED_CONFIG'
] 