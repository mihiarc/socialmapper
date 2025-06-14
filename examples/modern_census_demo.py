#!/usr/bin/env python3
"""
Modern Census Module Demonstration

This script demonstrates the new modern census module architecture
with its clean API, dependency injection, and modern Python patterns.
"""

import os
import logging
from typing import List

# Import the modern census module
from socialmapper.census_modern import (
    CensusManager,
    CensusConfig,
    create_census_manager,
    create_dependencies
)
from socialmapper.census_modern.domain.entities import CensusDataPoint, GeographicUnit


def demo_basic_usage():
    """Demonstrate basic usage of the modern census module."""
    print("=== Basic Usage Demo ===")
    
    # Create a simple configuration
    config = CensusConfig(
        cache_enabled=True,
        cache_ttl_seconds=300,
        log_level="INFO"
    )
    
    # Create a census manager
    manager = create_census_manager(config)
    
    print(f"✓ Created census manager with config: cache_enabled={config.cache_enabled}")
    
    # Note: In a real scenario, you would make actual API calls
    # For this demo, we'll show the API structure
    print("✓ Manager ready for census data operations")
    print("  - get_census_data(geoids, variable_codes, year, dataset)")
    print("  - get_block_groups(state_codes)")
    print("  - geocode_point(latitude, longitude)")
    print()


def demo_dependency_injection():
    """Demonstrate the dependency injection capabilities."""
    print("=== Dependency Injection Demo ===")
    
    # Create custom dependencies
    container = create_dependencies()
    
    # You can access and configure individual components
    print(f"✓ Configuration: {type(container.config).__name__}")
    print(f"✓ Logger: {type(container.logger).__name__}")
    print(f"✓ API Client: {type(container.api_client).__name__}")
    print(f"✓ Cache: {type(container.cache).__name__}")
    print(f"✓ Rate Limiter: {type(container.rate_limiter).__name__}")
    
    # Create manager with custom dependencies
    manager = CensusManager(container)
    print("✓ Created manager with custom dependency injection")
    print()


def demo_configuration_options():
    """Demonstrate different configuration options."""
    print("=== Configuration Options Demo ===")
    
    # Configuration from explicit values
    config1 = CensusConfig(
        census_api_key="your_api_key_here",
        cache_enabled=True,
        cache_ttl_seconds=600,
        rate_limit_requests_per_minute=120,
        log_level="DEBUG"
    )
    print("✓ Explicit configuration created")
    
    # Configuration from environment variables
    # Set some example environment variables
    os.environ.update({
        "CENSUS_API_KEY": "env_api_key",
        "CENSUS_CACHE_ENABLED": "true",
        "CENSUS_RATE_LIMIT": "60"
    })
    
    config2 = CensusConfig.from_environment()
    print("✓ Environment-based configuration created")
    print(f"  - API Key: {config2.census_api_key}")
    print(f"  - Cache Enabled: {config2.cache_enabled}")
    print(f"  - Rate Limit: {config2.rate_limit_requests_per_minute}")
    print()


def demo_modern_patterns():
    """Demonstrate modern Python patterns used in the module."""
    print("=== Modern Python Patterns Demo ===")
    
    # Immutable dataclasses
    from socialmapper.census_modern.domain.entities import CensusVariable, CensusDataPoint
    
    variable = CensusVariable(
        code="B01003_001E",
        name="Total Population",
        description="Total population in the past 12 months",
        unit="people"
    )
    print(f"✓ Immutable entity: {variable.code} - {variable.name}")
    
    # Type-safe interfaces
    print("✓ Protocol-based interfaces for dependency injection")
    print("✓ Full type hints throughout the codebase")
    
    # Clean separation of concerns
    print("✓ Domain/Service/Infrastructure layer separation")
    print("✓ No global state or singletons")
    print()


def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("=== Error Handling Demo ===")
    
    config = CensusConfig(cache_enabled=False)
    manager = create_census_manager(config)
    
    try:
        # This would normally make an API call and handle errors gracefully
        data = manager.get_census_data(
            geoids=["invalid_geoid"],
            variable_codes=["B01003_001E"]
        )
        print(f"✓ Error handling: returned {len(data)} results (graceful failure)")
    except Exception as e:
        print(f"✓ Error handling: {type(e).__name__}: {e}")
    
    print()


def demo_backward_compatibility():
    """Demonstrate backward compatibility with legacy APIs."""
    print("=== Backward Compatibility Demo ===")
    
    # Import legacy adapter functions
    from socialmapper.census_modern.adapters.legacy_adapter import (
        get_streaming_census_manager,
        clear_cache
    )
    
    print("✓ Legacy functions available with deprecation warnings:")
    print("  - get_streaming_census_manager()")
    print("  - get_block_groups()")
    print("  - get_census_data()")
    print("  - clear_cache()")
    
    # These would emit deprecation warnings when called
    print("✓ Smooth migration path from legacy to modern API")
    print()


def demo_caching_strategies():
    """Demonstrate different caching strategies."""
    print("=== Caching Strategies Demo ===")
    
    # In-memory caching (default)
    config1 = CensusConfig(
        cache_enabled=True,
        cache_ttl_seconds=300
    )
    manager1 = create_census_manager(config1)
    print("✓ In-memory caching configured (default)")
    
    # Longer cache TTL
    config2 = CensusConfig(
        cache_enabled=True,
        cache_ttl_seconds=3600,
        cache_max_size=5000
    )
    manager2 = create_census_manager(config2)
    print("✓ Extended caching configured (1 hour TTL, 5000 items)")
    
    # Disabled caching
    config3 = CensusConfig(cache_enabled=False)
    manager3 = create_census_manager(config3)
    print("✓ Caching disabled")
    print()


def main():
    """Run all demonstrations."""
    print("🏛️  Modern Census Module Demonstration")
    print("=" * 50)
    print()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run all demos
    demo_basic_usage()
    demo_dependency_injection()
    demo_configuration_options()
    demo_modern_patterns()
    demo_error_handling()
    demo_backward_compatibility()
    demo_caching_strategies()
    
    print("🎉 All demonstrations completed!")
    print()
    print("Key Benefits of the Modern Architecture:")
    print("✓ No global state - fully configurable")
    print("✓ Dependency injection - easy testing")
    print("✓ Protocol-based design - flexible implementations")
    print("✓ Immutable entities - thread-safe")
    print("✓ Clean separation of concerns")
    print("✓ Backward compatibility maintained")
    print("✓ Modern Python patterns throughout")


if __name__ == "__main__":
    main() 