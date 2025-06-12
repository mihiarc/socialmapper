"""
Modern API for SocialMapper.

This module provides a clean, type-safe API following modern software
engineering best practices.

Example:
    ```python
    from socialmapper.api import SocialMapperClient, SocialMapperBuilder

    # Simple usage
    with SocialMapperClient() as client:
        result = client.analyze(
            location="San Francisco, CA",
            poi_type="amenity",
            poi_name="library"
        )

        if result.is_ok():
            analysis = result.unwrap()
            print(f"Found {analysis.poi_count} libraries")

    # Advanced usage with builder
    config = (SocialMapperBuilder()
        .with_location("Chicago", "IL")
        .with_osm_pois("leisure", "park")
        .with_travel_time(20)
        .with_census_variables("total_population", "median_income")
        .build()
    )

    with SocialMapperClient() as client:
        result = client.run_analysis(config)
    ```
"""

# Version information
__version__ = "0.5.4"

# Builder pattern for configuration
# Type exports for better IDE support
from typing import TYPE_CHECKING

# Async support
from .async_client import (
    AsyncSocialMapper,
    IsochroneResult,
    POIResult,
    run_async_analysis,
)
from .builder import (
    AnalysisResult,
    GeographicLevel,
    SocialMapperBuilder,
)

# Main client
from .client import (
    CacheStrategy,
    ClientConfig,
    SocialMapperClient,
)

# Convenience functions
from .convenience import (
    analyze_custom_pois,
    analyze_location,
    quick_analysis,
)

# Result types for error handling
from .result_types import (
    Err,
    Error,
    ErrorType,
    Ok,
    Result,
    collect_results,
    result_handler,
    try_all,
)

if TYPE_CHECKING:
    from typing import Any, Dict, List, Optional

# Public API
__all__ = [
    # Version
    "__version__",
    # Builder
    "SocialMapperBuilder",
    "AnalysisResult",
    "GeographicLevel",
    # Client
    "SocialMapperClient",
    "ClientConfig",
    "CacheStrategy",
    # Result types
    "Result",
    "Ok",
    "Err",
    "Error",
    "ErrorType",
    "collect_results",
    "try_all",
    "result_handler",
    # Async
    "AsyncSocialMapper",
    "run_async_analysis",
    "POIResult",
    "IsochroneResult",
    # Convenience
    "quick_analysis",
    "analyze_location",
    "analyze_custom_pois",
]


# Deprecation warnings for old API
def run_socialmapper(*args, **kwargs):
    """
    Deprecated: Use SocialMapperClient instead.

    This function is maintained for backward compatibility only.
    """
    import warnings

    warnings.warn(
        "run_socialmapper is deprecated. Use SocialMapperClient instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Import old function
    from ..core import run_socialmapper as _old_run

    return _old_run(*args, **kwargs)
