#!/usr/bin/env python3
"""
Configuration Manager for SocialMapper.

This module provides utilities for managing global configuration state
and providing centralized access to optimization settings.
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..config.optimization import OptimizationConfig

# Global configuration instance
_global_config: Optional["OptimizationConfig"] = None


def get_global_config() -> "OptimizationConfig":
    """
    Get the global optimization configuration.
    
    Returns:
        Current global optimization configuration
    """
    global _global_config
    
    if _global_config is None:
        from ..config.optimization import OptimizationConfig
        _global_config = OptimizationConfig.from_environment()
    
    return _global_config


def set_global_config(config: "OptimizationConfig") -> None:
    """
    Set a new global configuration.
    
    Args:
        config: New optimization configuration to use globally
    """
    global _global_config
    _global_config = config


def update_global_config(**kwargs) -> None:
    """
    Update the global configuration with new values.
    
    Args:
        **kwargs: Configuration updates using dot notation 
                  (e.g., 'distance.chunk_size', 'memory.max_memory_gb')
    """
    global _global_config
    
    # Ensure config exists
    config = get_global_config()
    
    for key, value in kwargs.items():
        if hasattr(config, key):
            # Direct attribute
            setattr(config, key, value)
        elif "." in key:
            # Nested attribute using dot notation
            section, setting = key.split(".", 1)
            if hasattr(config, section):
                section_config = getattr(config, section)
                if hasattr(section_config, setting):
                    setattr(section_config, setting, value)
                else:
                    raise ValueError(f"Setting '{setting}' not found in section '{section}'")
            else:
                raise ValueError(f"Configuration section '{section}' not found")
        else:
            raise ValueError(f"Configuration setting '{key}' not found")


def reset_global_config() -> None:
    """Reset the global configuration to environment defaults."""
    global _global_config
    from ..config.optimization import OptimizationConfig
    _global_config = OptimizationConfig.from_environment()


def apply_preset(preset_name: str) -> None:
    """
    Apply a configuration preset to the global configuration.
    
    Args:
        preset_name: Name of the preset to apply
                    ("development", "production", "memory_constrained", 
                     "high_performance", "auto", etc.)
    """
    from .config_presets import get_config_for_environment
    
    preset_config = get_config_for_environment(preset_name)
    set_global_config(preset_config)


def get_config_summary() -> dict[str, Any]:
    """
    Get a summary of the current global configuration.
    
    Returns:
        Dictionary with configuration summary
    """
    config = get_global_config()
    
    return {
        "distance": {
            "engine": config.distance.engine,
            "parallel_processes": config.distance.parallel_processes,
            "chunk_size": config.distance.chunk_size,
            "enable_jit": config.distance.enable_jit,
        },
        "isochrone": {
            "clustering_algorithm": config.isochrone.clustering_algorithm,
            "max_cluster_radius_km": config.isochrone.max_cluster_radius_km,
            "enable_caching": config.isochrone.enable_caching,
            "max_cache_size_gb": config.isochrone.max_cache_size_gb,
            "max_concurrent_downloads": config.isochrone.max_concurrent_downloads,
            "max_concurrent_isochrones": config.isochrone.max_concurrent_isochrones,
        },
        "memory": {
            "max_memory_gb": config.memory.max_memory_gb,
            "streaming_batch_size": config.memory.streaming_batch_size,
            "aggressive_cleanup": config.memory.aggressive_cleanup,
            "enable_memory_monitoring": config.memory.enable_memory_monitoring,
        },
        "io": {
            "default_format": config.io.default_format,
            "compression": config.io.compression,
            "use_polars": config.io.use_polars,
            "enable_arrow": config.io.enable_arrow,
            "enable_streaming": config.io.enable_streaming,
            "stream_threshold_mb": config.io.stream_threshold_mb,
        },
        "global": {
            "enable_performance_monitoring": config.enable_performance_monitoring,
            "log_level": config.log_level,
            "enable_progress_bars": config.enable_progress_bars,
        },
    }


def validate_config() -> dict[str, Any]:
    """
    Validate the current global configuration.
    
    Returns:
        Dictionary with validation results
    """
    from .system_detection import validate_system_requirements
    
    config = get_global_config()
    system_validation = validate_system_requirements()
    
    warnings = []
    errors = []
    
    # Validate memory settings
    if config.memory.max_memory_gb > 64:
        warnings.append("Memory limit is very high (>64GB), ensure this is intentional")
    
    if config.memory.streaming_batch_size < 10:
        warnings.append("Streaming batch size is very small, may impact performance")
    
    # Validate isochrone settings
    if config.isochrone.max_concurrent_downloads > 100:
        warnings.append("Very high concurrent downloads may trigger rate limiting")
    
    if config.isochrone.max_cache_size_gb < 0.1:
        warnings.append("Cache size is very small, may impact performance")
    
    # Validate distance settings
    if config.distance.chunk_size < 100:
        warnings.append("Distance chunk size is very small, may impact performance")
    elif config.distance.chunk_size > 100000:
        warnings.append("Distance chunk size is very large, may cause memory issues")
    
    # Combine with system validation
    all_warnings = warnings + system_validation.get("warnings", [])
    all_errors = errors + system_validation.get("errors", [])
    
    return {
        "is_valid": len(all_errors) == 0,
        "warnings": all_warnings,
        "errors": all_errors,
        "system_validation": system_validation,
        "config_summary": get_config_summary(),
    }


def optimize_for_current_system() -> None:
    """
    Automatically optimize configuration for the current system.
    """
    from .config_presets import ConfigPresets
    
    optimized_config = ConfigPresets.auto_detect()
    set_global_config(optimized_config)


def save_config_to_file(filepath: str) -> None:
    """
    Save the current configuration to a JSON file.
    
    Args:
        filepath: Path to save the configuration file
    """
    import json
    from pathlib import Path
    
    config_dict = get_config_summary()
    
    # Ensure directory exists
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(config_dict, f, indent=2)


def load_config_from_file(filepath: str) -> None:
    """
    Load configuration from a JSON file and apply it globally.
    
    Args:
        filepath: Path to the configuration file
    """
    import json
    from pathlib import Path
    
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Configuration file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        config_dict = json.load(f)
    
    # Apply configuration updates
    updates = {}
    for section, settings in config_dict.items():
        if section == "global":
            # Apply global settings directly
            updates.update(settings)
        else:
            # Apply nested settings with dot notation
            for key, value in settings.items():
                updates[f"{section}.{key}"] = value
    
    update_global_config(**updates)


# Convenience functions for common operations
def get_config() -> "OptimizationConfig":
    """Alias for get_global_config() for backward compatibility."""
    return get_global_config()


def update_config(**kwargs) -> None:
    """Alias for update_global_config() for backward compatibility."""
    update_global_config(**kwargs)


def reset_config() -> None:
    """Alias for reset_global_config() for backward compatibility.""" 