#!/usr/bin/env python3
"""
Centralized warning configuration for SocialMapper.

This module provides utilities to manage deprecation warnings from various
geospatial libraries that are known issues and don't affect functionality.

The warnings are automatically configured when SocialMapper is imported,
but can be controlled via environment variables or explicit function calls.
"""

import warnings
import os
from typing import Optional


def configure_geospatial_warnings(verbose: bool = False):
    """
    Configure warning filters for known geospatial library deprecation warnings.
    
    This function suppresses warnings that are:
    1. Known issues in upstream libraries
    2. Don't affect functionality
    3. Create noise in logs and benchmarks
    
    Args:
        verbose: If True, print information about which warnings are being suppressed
    """
    
    warning_configs = [
        # OSMnx pandas FutureWarnings
        {
            "category": FutureWarning,
            "module": "osmnx",
            "message": ".*Downcasting object dtype arrays.*",
            "reason": "OSMnx pandas compatibility - known issue, no functional impact"
        },
        
        # Shapely/GeoPandas deprecation warnings
        {
            "category": DeprecationWarning,
            "module": "geopandas._compat",
            "message": ".*shapely.geos.*module is deprecated.*",
            "reason": "GeoPandas internal shapely compatibility - will be fixed in future versions"
        },
        
        # Shapely geos module deprecation (broader catch)
        {
            "category": DeprecationWarning,
            "message": ".*shapely.geos.*module is deprecated.*",
            "module": None,
            "reason": "Shapely geos module deprecation - affects GeoPandas and other libraries"
        },
        
        # Pydantic V1 style validator warnings
        {
            "category": DeprecationWarning,
            "message": ".*Pydantic V1 style.*@validator.*validators are deprecated.*",
            "module": None,
            "reason": "Pydantic V1 to V2 migration warnings - functionality unchanged"
        },
        
        # Pydantic class-based config warnings
        {
            "category": DeprecationWarning,
            "message": ".*class-based.*config.*is deprecated.*",
            "module": None,
            "reason": "Pydantic V2 config migration warnings - functionality unchanged"
        },
        
        # NumPy 2.0+ dtype warnings (general library compatibility)
        {
            "category": DeprecationWarning,
            "message": ".*numpy.ndarray size changed.*",
            "module": None,
            "reason": "NumPy 2.0+ internal array size changes - affects compiled extensions"
        },
        
        # Streamlit context warnings (common in non-streamlit environments)
        {
            "category": UserWarning,
            "module": "streamlit.runtime.scriptrunner_utils.script_run_context",
            "message": ".*missing ScriptRunContext.*",
            "reason": "Streamlit context warnings when running outside Streamlit - safe to ignore"
        }
    ]
    
    if verbose:
        print("🔇 Configuring geospatial library warning filters:")
    
    for config in warning_configs:
        # Build filter arguments
        filter_args = {"category": config["category"]}
        
        if config.get("module"):
            filter_args["module"] = config["module"]
        
        if config.get("message"):
            filter_args["message"] = config["message"]
        
        # Apply filter
        warnings.filterwarnings("ignore", **filter_args)
        
        if verbose:
            module_str = f" (module: {config.get('module', 'any')})"
            print(f"   ✓ {config['category'].__name__}{module_str}")
            print(f"     Reason: {config['reason']}")


def configure_numpy2_compatibility(verbose: bool = False):
    """
    Specific configuration for NumPy 2.0+ compatibility warnings.
    
    This function addresses warnings that appear when using NumPy 2.0+
    with libraries that haven't fully updated their compatibility.
    
    Note: PyProj NumPy array-to-scalar warnings are now prevented at the source
    via Pydantic validation, so those filters have been removed.
    
    Args:
        verbose: If True, print information about NumPy 2 compatibility setup
    """
    
    numpy2_configs = [
        # NumPy 2 dtype size warnings
        {
            "category": RuntimeWarning,
            "message": ".*numpy.ndarray size changed.*",
            "module": None,
            "reason": "NumPy 2.0 internal array size changes"
        },
        
        # NumPy 2 C extension warnings
        {
            "category": RuntimeWarning,
            "message": ".*numpy.ufunc size changed.*",
            "module": None,
            "reason": "NumPy 2.0 ufunc size changes in C extensions"
        }
    ]
    
    if verbose:
        print("🔢 Configuring NumPy 2.0+ compatibility filters:")
        print("   Note: PyProj array-to-scalar warnings prevented via Pydantic validation")
    
    for config in numpy2_configs:
        filter_args = {"category": config["category"]}
        
        if config.get("module"):
            filter_args["module"] = config["module"]
        
        if config.get("message"):
            filter_args["message"] = config["message"]
        
        warnings.filterwarnings("ignore", **filter_args)
        
        if verbose:
            module_str = f" (module: {config.get('module', 'any')})"
            print(f"   ✓ {config['category'].__name__}{module_str}")
            print(f"     Reason: {config['reason']}")


def configure_osmnx_settings(
    max_query_area_size: int = 50000000000,
    timeout: int = 300,
    disable_rate_limit: bool = True,
    quiet_logging: bool = True
):
    """
    Configure OSMnx settings for optimal performance with large datasets.
    
    Args:
        max_query_area_size: Maximum query area size in square meters (default: 50B)
        timeout: Query timeout in seconds (default: 300)
        disable_rate_limit: Whether to disable rate limiting for controlled testing
        quiet_logging: Whether to reduce console logging noise
    """
    try:
        import osmnx as ox
        
        ox.settings.max_query_area_size = max_query_area_size
        ox.settings.timeout = timeout
        ox.settings.overpass_rate_limit = not disable_rate_limit
        ox.settings.log_console = not quiet_logging
        
        return True
    except ImportError:
        warnings.warn("OSMnx not available - skipping configuration")
        return False


def setup_production_environment(verbose: bool = False):
    """
    Complete setup for production environment with optimized settings.
    
    This is automatically called when SocialMapper is imported, unless
    disabled via the SOCIALMAPPER_NO_WARNING_CONFIG environment variable.
    
    Args:
        verbose: Whether to print configuration details
    """
    # Check if user wants to disable automatic warning configuration
    if os.getenv('SOCIALMAPPER_NO_WARNING_CONFIG', '').lower() in ('true', '1', 'yes'):
        if verbose:
            print("⚠️ SocialMapper warning configuration disabled via environment variable")
        return
    
    if verbose:
        print("🚀 Setting up optimized SocialMapper environment:")
    
    # Configure warning filters
    configure_geospatial_warnings(verbose=verbose)
    
    # Configure NumPy 2 compatibility
    configure_numpy2_compatibility(verbose=verbose)
    
    # Configure OSMnx (only for production, not as aggressive as benchmarking)
    osmnx_configured = configure_osmnx_settings(
        max_query_area_size=10000000000,  # 10B sq meters (more conservative)
        timeout=180,  # 3 minutes (reasonable default)
        disable_rate_limit=False,  # Keep rate limiting for production
        quiet_logging=True  # Reduce noise
    )
    
    if verbose:
        if osmnx_configured:
            print("   ✓ OSMnx configured for production use")
        else:
            print("   ⚠ OSMnx not available")
        
        print("   ✓ Warning filters applied")
        print("   ✓ NumPy 2 compatibility configured")
        print("🎯 Environment ready for optimal performance!")


def setup_benchmark_environment(verbose: bool = True):
    """
    Setup environment specifically for benchmarking with minimal noise.
    
    Args:
        verbose: Whether to print setup information
    """
    if verbose:
        print("📊 Setting up benchmark environment:")
    
    # Apply all warning filters
    configure_geospatial_warnings(verbose=False)
    
    # Configure NumPy 2 compatibility
    configure_numpy2_compatibility(verbose=False)
    
    # Configure OSMnx for benchmarking (more aggressive settings)
    osmnx_configured = configure_osmnx_settings(
        max_query_area_size=50000000000,  # 50B sq meters
        timeout=300,  # 5 minutes
        disable_rate_limit=True,
        quiet_logging=True
    )
    
    if verbose:
        print("   ✓ All deprecation warnings suppressed")
        print("   ✓ NumPy 2 compatibility warnings suppressed")
        if osmnx_configured:
            print("   ✓ OSMnx optimized for large datasets")
        print("   ✓ Benchmark environment ready")


def setup_development_environment(verbose: bool = True):
    """
    Setup environment for development with some warnings enabled.
    
    Args:
        verbose: Whether to print setup information
    """
    if verbose:
        print("🛠️ Setting up development environment:")
    
    # Only suppress the most problematic warnings, keep others for development awareness
    # Note: PyProj NumPy warnings are now prevented at source via Pydantic validation
    warning_configs = [
        # OSMnx pandas warnings (also just noise)
        {
            "category": FutureWarning,
            "module": "osmnx",
            "message": ".*Downcasting object dtype arrays.*",
        },
        # Shapely geos warnings (upstream issue)
        {
            "category": DeprecationWarning,
            "message": ".*shapely.geos.*module is deprecated.*",
        },
        # Streamlit context warnings
        {
            "category": UserWarning,
            "module": "streamlit.runtime.scriptrunner_utils.script_run_context",
            "message": ".*missing ScriptRunContext.*",
        }
    ]
    
    for config in warning_configs:
        filter_args = {"category": config["category"]}
        if config.get("module"):
            filter_args["module"] = config["module"]
        if config.get("message"):
            filter_args["message"] = config["message"]
        warnings.filterwarnings("ignore", **filter_args)
    
    # Configure OSMnx for development (conservative settings)
    osmnx_configured = configure_osmnx_settings(
        max_query_area_size=5000000000,  # 5B sq meters
        timeout=120,  # 2 minutes
        disable_rate_limit=False,
        quiet_logging=False  # Keep logging for development
    )
    
    if verbose:
        print("   ✓ Critical warnings suppressed (keeping others for development)")
        print("   ✓ PyProj warnings prevented via Pydantic validation")
        if osmnx_configured:
            print("   ✓ OSMnx configured for development")
        print("   ✓ Development environment ready")


# Convenience function for quick setup
def quick_setup():
    """Quick setup with sensible defaults for most use cases."""
    setup_production_environment(verbose=False)


def disable_warning_filters():
    """
    Disable all warning filters applied by SocialMapper.
    
    This resets the warning system to Python defaults.
    Useful if you want to see all warnings for debugging.
    """
    warnings.resetwarnings()
    print("⚠️ All SocialMapper warning filters have been disabled")
    print("   Python will now show all warnings (including known harmless ones)")


if __name__ == "__main__":
    # Demo the configuration
    print("🧪 SocialMapper Warning Configuration Demo")
    print("=" * 50)
    
    print("\n1. Production Environment:")
    setup_production_environment(verbose=True)
    
    print("\n2. Development Environment:")
    setup_development_environment(verbose=True)
    
    print("\n3. Benchmark Environment:")
    setup_benchmark_environment(verbose=True)
    
    print("\n💡 Environment Variable Control:")
    print("   Set SOCIALMAPPER_NO_WARNING_CONFIG=true to disable automatic configuration")
    print("   This gives you full control over warning behavior") 