"""
Demonstration of the modern SocialMapper API.

This example shows various ways to use the new API with better
error handling, type safety, and modern patterns.
"""

import asyncio
from pathlib import Path

from socialmapper.api import (
    SocialMapperClient,
    SocialMapperBuilder,
    ClientConfig,
    GeographicLevel,
    quick_analysis,
    analyze_location,
    Result,
    Ok,
    Err,
    AsyncSocialMapper,
    run_async_analysis,
)


def example_1_simple_analysis():
    """Example 1: Simple analysis with minimal configuration."""
    print("\n=== Example 1: Simple Analysis ===")
    
    # Quick analysis with convenience function
    result = quick_analysis(
        location="Portland, OR",
        poi_search="amenity:library",
        travel_time=15,
        census_variables=["total_population", "median_income"]
    )
    
    # Pattern matching on result
    match result:
        case Ok(analysis):
            print(f"✅ Success! Found {analysis.poi_count} libraries")
            print(f"   Analyzed {analysis.census_units_analyzed} census units")
            print(f"   Files saved to: {analysis.files_generated}")
        case Err(error):
            print(f"❌ Error: {error}")


def example_2_builder_pattern():
    """Example 2: Using the builder pattern for complex configuration."""
    print("\n=== Example 2: Builder Pattern ===")
    
    # Build configuration step by step
    config = (SocialMapperBuilder()
        .with_location("San Francisco", "CA")
        .with_osm_pois("amenity", "hospital")
        .with_travel_time(20)
        .with_census_variables(
            "total_population",
            "median_income", 
            "median_age",
            "housing_units"
        )
        .with_geographic_level(GeographicLevel.ZCTA)
        .enable_map_export()
        .enable_isochrone_export()
        # .with_output_directory("sf_hospital_analysis")  # Path security issue
        .build()
    )
    
    # Use the client
    with SocialMapperClient() as client:
        result = client.run_analysis(config)
        
        if result.is_ok():
            analysis = result.unwrap()
            print(f"✅ Analyzed {analysis.poi_count} hospitals")
            print(f"   Travel time: {analysis.metadata['travel_time']} minutes")
            print(f"   Geographic level: {analysis.metadata['geographic_level']}")
        else:
            print(f"❌ Failed: {result.unwrap_err()}")


def example_3_error_handling():
    """Example 3: Comprehensive error handling."""
    print("\n=== Example 3: Error Handling ===")
    
    # Configure client with custom settings
    config = ClientConfig(
        api_key="your-census-api-key",
        rate_limit=5,
        retry_attempts=3
    )
    
    with SocialMapperClient(config) as client:
        # This will fail validation
        result = client.analyze(
            location="Invalid Location Format",  # Missing state
            poi_type="amenity",
            poi_name="school"
        )
        
        # Handle different error types
        if result.is_err():
            error = result.unwrap_err()
            
            match error.type:
                case ErrorType.VALIDATION:
                    print(f"❌ Validation error: {error.message}")
                    print(f"   Context: {error.context}")
                case ErrorType.NETWORK:
                    print(f"❌ Network error: {error.message}")
                    print("   Please check your internet connection")
                case ErrorType.RATE_LIMIT:
                    print(f"❌ Rate limit exceeded: {error.message}")
                    print("   Please wait before retrying")
                case _:
                    print(f"❌ Unexpected error: {error}")


def example_4_batch_processing():
    """Example 4: Batch processing multiple analyses."""
    print("\n=== Example 4: Batch Processing ===")
    
    # Define multiple analyses
    cities = [
        ("Seattle", "WA"),
        ("Portland", "OR"),
        ("San Francisco", "CA"),
        ("Los Angeles", "CA")
    ]
    
    configs = []
    for city, state in cities:
        config = (SocialMapperBuilder()
            .with_location(city, state)
            .with_osm_pois("leisure", "park")
            .with_travel_time(10)
            .with_census_variables("total_population")
            .build()
        )
        configs.append(config)
    
    # Process in batch
    with SocialMapperClient() as client:
        with client.batch_analyses(configs) as batch:
            results = batch.run_all()
            
            # Process results
            for i, (result, (city, state)) in enumerate(zip(results, cities)):
                if result.is_ok():
                    analysis = result.unwrap()
                    print(f"✅ {city}, {state}: {analysis.poi_count} parks found")
                else:
                    print(f"❌ {city}, {state}: Failed - {result.unwrap_err()}")


def example_5_custom_pois():
    """Example 5: Analyzing custom POI locations."""
    print("\n=== Example 5: Custom POIs ===")
    
    # Create sample POI file
    poi_file = Path("sample_pois.csv")
    poi_file.write_text("""name,latitude,longitude,type
Community Center 1,45.5152,-122.6784,community_center
Community Center 2,45.5252,-122.6684,community_center
Community Center 3,45.5352,-122.6584,community_center
""")
    
    try:
        # Analyze custom POIs
        config = (SocialMapperBuilder()
            .with_custom_pois(poi_file, name_field="name", type_field="type")
            .with_travel_time(15)
            .with_census_variables("total_population", "median_income")
            .enable_map_export()
            .build()
        )
        
        with SocialMapperClient() as client:
            result = client.run_analysis(config)
            
            if result.is_ok():
                analysis = result.unwrap()
                print(f"✅ Analyzed {analysis.poi_count} community centers")
            else:
                print(f"❌ Failed: {result.unwrap_err()}")
                
    finally:
        # Clean up
        poi_file.unlink(missing_ok=True)


async def example_6_async_operations():
    """Example 6: Asynchronous operations for better performance."""
    print("\n=== Example 6: Async Operations ===")
    
    config = (SocialMapperBuilder()
        .with_location("Chicago", "IL")
        .with_osm_pois("amenity", "pharmacy")
        .with_travel_time(10)
        .build()
    )
    
    # Run asynchronously
    async with AsyncSocialMapper(config) as mapper:
        # Stream POIs as they're found
        print("Streaming POIs...")
        poi_count = 0
        async for poi in mapper.stream_pois():
            poi_count += 1
            print(f"  Found: {poi.name} at ({poi.latitude}, {poi.longitude})")
        
        # Generate isochrones with progress
        print("\nGenerating isochrones...")
        async for progress in mapper.generate_isochrones_with_progress():
            print(f"  Progress: {progress['percent']:.0f}% - {progress['current_poi']}")
        
        # Get final result
        result = await mapper.run_analysis()
        print(f"\n✅ Analysis complete: {result.poi_count} POIs processed")


def example_7_chaining_operations():
    """Example 7: Chaining operations with Result types."""
    print("\n=== Example 7: Chaining Operations ===")
    
    def validate_location(location: str) -> Result[tuple[str, str], Error]:
        """Validate and parse location string."""
        parts = location.split(",")
        if len(parts) != 2:
            return Err(Error(
                type=ErrorType.VALIDATION,
                message="Location must be 'City, State'"
            ))
        return Ok((parts[0].strip(), parts[1].strip()))
    
    def create_config(city_state: tuple[str, str]) -> Result[dict, Error]:
        """Create configuration from city and state."""
        city, state = city_state
        try:
            config = (SocialMapperBuilder()
                .with_location(city, state)
                .with_osm_pois("amenity", "library")
                .build()
            )
            return Ok(config)
        except ValueError as e:
            return Err(Error(ErrorType.VALIDATION, str(e)))
    
    # Chain operations
    result = (validate_location("Boston, MA")
        .and_then(create_config)
        .map(lambda cfg: {**cfg, "travel_time": 20})
    )
    
    if result.is_ok():
        config = result.unwrap()
        print(f"✅ Configuration created for {config['geocode_area']}, {config['state']}")
    else:
        print(f"❌ Failed: {result.unwrap_err()}")


def main():
    """Run all examples."""
    print("🌍 SocialMapper Modern API Examples")
    print("=" * 50)
    
    # Run synchronous examples
    example_1_simple_analysis()
    example_2_builder_pattern()
    example_3_error_handling()
    example_4_batch_processing()
    example_5_custom_pois()
    example_7_chaining_operations()
    
    # Run async example
    print("\nRunning async example...")
    asyncio.run(example_6_async_operations())
    
    print("\n✅ All examples completed!")


if __name__ == "__main__":
    main()