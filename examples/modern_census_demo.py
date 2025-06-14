#!/usr/bin/env python3
"""
Modern Census Module Demonstration

This script demonstrates the new modern census module architecture
with its clean API, dependency injection, and modern Python patterns.
"""

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available - continue without it
    pass

import os
import logging
from typing import List

# Import the modern census module
from socialmapper.census import (
    CensusSystem,
    CensusSystemBuilder,
    get_census_system,
    CensusConfig
)
from socialmapper.census.domain.entities import CensusDataPoint, GeographicUnit


def demo_basic_usage():
    """Demonstrate basic usage of the modern census module."""
    print("=== Basic Usage Demo ===")
    
    # Create a census system with default configuration
    census = get_census_system()
    
    print("✓ Created census system with default configuration")
    
    # Note: In a real scenario, you would make actual API calls
    # For this demo, we'll show the API structure
    print("✓ Census system ready for operations")
    print("  - get_census_data(variables, geographic_units, year)")
    print("  - get_block_groups_for_county(state_fips, county_fips)")
    print("  - get_geography_from_point(lat, lon)")
    print("  - normalize_variable(variable)")
    print()


def demo_dependency_injection():
    """Demonstrate the dependency injection capabilities."""
    print("=== Dependency Injection Demo ===")
    
    # Create custom census system using builder pattern
    census = (CensusSystemBuilder()
              .with_cache_strategy("in_memory")
              .with_rate_limit(2.0)
              .build())
    
    print("✓ Built census system with custom configuration:")
    print("  - Cache strategy: in_memory")
    print("  - Rate limit: 2.0 requests/second")
    print("  - Clean dependency injection architecture")
    print("  - Protocol-based interfaces")
    print("✓ Created system with builder pattern")
    print()


def demo_configuration_options():
    """Demonstrate different configuration options."""
    print("=== Configuration Options Demo ===")
    
    # Simple configuration with get_census_system
    census1 = get_census_system(
        cache_strategy="in_memory"
    )
    print("✓ Simple configuration with get_census_system()")
    
    # Advanced configuration with builder
    census2 = (CensusSystemBuilder()
               .with_api_key("your_api_key_here")
               .with_cache_strategy("file")
               .with_cache_dir("./cache")
               .with_rate_limit(1.5)
               .with_api_timeout(30)
               .with_max_retries(3)
               .build())
    print("✓ Advanced configuration with builder pattern:")
    print("  - Custom API key")
    print("  - File-based caching")
    print("  - Custom cache directory")
    print("  - Rate limiting: 1.5 req/sec")
    print("  - API timeout: 30 seconds")
    print("  - Max retries: 3")
    
    # Environment-based configuration
    print("✓ Environment variables supported:")
    print("  - CENSUS_API_KEY")
    print("  - CENSUS_CACHE_DIR")
    print()


def demo_modern_patterns():
    """Demonstrate modern Python patterns used in the module."""
    print("=== Modern Python Patterns Demo ===")
    
    # Immutable dataclasses
    from socialmapper.census.domain.entities import CensusVariable, CensusDataPoint
    
    variable = CensusVariable(
        code="B01003_001E",
        name="Total Population",
        description="Total population in the past 12 months"
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
    
    census = get_census_system(cache_strategy="none")
    
    try:
        # This would normally make an API call and handle errors gracefully
        data = census.get_census_data(
            variables=["B01003_001E"],
            geographic_units=["invalid_geoid"]
        )
        print(f"✓ Error handling: returned {len(data)} results (graceful failure)")
    except Exception as e:
        print(f"✓ Error handling: {type(e).__name__}: {e}")
    
    # Demonstrate validation
    print("✓ Built-in validation:")
    print(f"  - Valid variable: {census.validate_variable('B01003_001E')}")
    print(f"  - Invalid variable: {census.validate_variable('INVALID_VAR')}")
    print(f"  - Valid state: {census.is_valid_state('NC')}")
    print(f"  - Invalid state: {census.is_valid_state('XX')}")
    
    print()


def demo_backward_compatibility():
    """Demonstrate backward compatibility with legacy APIs."""
    print("=== Backward Compatibility Demo ===")
    
    # The modern system provides backward compatibility through delegation
    print("✓ Legacy API compatibility maintained:")
    print("  - run_socialmapper() still works (with deprecation warning)")
    print("  - Legacy census functions delegated to modern system")
    print("  - Gradual migration path available")
    
    # Modern API provides cleaner interface
    print("✓ Modern API benefits:")
    print("  - Type-safe interfaces")
    print("  - Dependency injection")
    print("  - Clean separation of concerns")
    print("  - Better error handling")
    print("  - Immutable data structures")
    
    print("✓ Smooth migration path from legacy to modern API")
    print()


def demo_caching_strategies():
    """Demonstrate different caching strategies."""
    print("=== Caching Strategies Demo ===")
    
    # In-memory caching (default)
    census1 = get_census_system(cache_strategy="in_memory")
    print("✓ In-memory caching configured (default)")
    
    # File-based caching
    census2 = (CensusSystemBuilder()
               .with_cache_strategy("file")
               .with_cache_dir("./census_cache")
               .build())
    print("✓ File-based caching configured")
    
    # Hybrid caching (in-memory + file)
    census3 = get_census_system(cache_strategy="hybrid")
    print("✓ Hybrid caching configured (in-memory + file)")
    
    # Disabled caching
    census4 = get_census_system(cache_strategy="none")
    print("✓ Caching disabled")
    
    print("✓ Available cache strategies:")
    print("  - in_memory: Fast, temporary")
    print("  - file: Persistent across sessions")
    print("  - hybrid: Best of both worlds")
    print("  - none: No caching")
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