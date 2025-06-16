#!/usr/bin/env python3
"""Configuration package for SocialMapper optimization.

This package provides clean dataclass-based configuration schemas for all
optimization settings and performance tuning.

For configuration management utilities, import from socialmapper.util:
- ConfigPresets: Configuration factory with presets
- get_global_config, set_global_config: Global configuration management
- apply_preset, validate_config: Configuration utilities
"""

from .optimization import (
    DistanceConfig,
    IOConfig,
    IsochroneConfig,
    MemoryConfig,
    OptimizationConfig,
)

__all__ = [
    "DistanceConfig",
    "IOConfig",
    "IsochroneConfig",
    "MemoryConfig",
    "OptimizationConfig",
]
