#!/usr/bin/env python3
"""
Tutorial: Using Different Travel Modes

This tutorial demonstrates how to generate isochrones using different travel modes
(walk, bike, drive) with SocialMapper.
"""

from pathlib import Path

from socialmapper.api import SocialMapperBuilder, SocialMapperClient
from socialmapper.isochrone import TravelMode


def main():
    """Run travel mode comparison example."""
    print("=== SocialMapper Travel Mode Example ===\n")
    
    # Example 1: Walking isochrone for parks
    print("1. Generating 15-minute walking isochrone for parks in Chapel Hill, NC")
    
    config = (
        SocialMapperBuilder()
        .with_location("Chapel Hill", "NC")
        .with_osm_pois("leisure", "park")
        .with_travel_time(15)
        .with_travel_mode("walk")  # Can use string or TravelMode.WALK
        .with_census_variables("total_population", "median_age")
        .limit_pois(3)  # Limit to 3 parks for quick demo
        .with_output_directory("output/walk_example")
        .build()
    )
    
    with SocialMapperClient() as client:
        result = client.run_analysis(config)
        
        if result.is_ok():
            data = result.unwrap()
            print(f"✅ Found {data.poi_count} parks")
            print(f"✅ Generated {data.isochrone_count} walking isochrones")
            print(f"✅ Analyzed {data.census_units_analyzed} census units")
        else:
            error = result.unwrap_err()
            print(f"❌ Error: {error.message}")
    
    # Example 2: Biking isochrone for libraries
    print("\n2. Generating 10-minute biking isochrone for libraries in Chapel Hill, NC")
    
    config = (
        SocialMapperBuilder()
        .with_location("Chapel Hill", "NC")
        .with_osm_pois("amenity", "library")
        .with_travel_time(10)
        .with_travel_mode(TravelMode.BIKE)  # Using enum directly
        .with_census_variables("total_population", "median_household_income")
        .limit_pois(3)
        .with_output_directory("output/bike_example")
        .build()
    )
    
    with SocialMapperClient() as client:
        result = client.run_analysis(config)
        
        if result.is_ok():
            data = result.unwrap()
            print(f"✅ Found {data.poi_count} libraries")
            print(f"✅ Generated {data.isochrone_count} biking isochrones")
            print(f"✅ Analyzed {data.census_units_analyzed} census units")
        else:
            error = result.unwrap_err()
            print(f"❌ Error: {error.message}")
    
    # Example 3: Driving isochrone for hospitals
    print("\n3. Generating 20-minute driving isochrone for hospitals in Chapel Hill, NC")
    
    config = (
        SocialMapperBuilder()
        .with_location("Chapel Hill", "NC")
        .with_osm_pois("amenity", "hospital")
        .with_travel_time(20)
        .with_travel_mode("drive")  # Default mode
        .with_census_variables("total_population", "median_age")
        .limit_pois(2)
        .with_output_directory("output/drive_example")
        .build()
    )
    
    with SocialMapperClient() as client:
        result = client.run_analysis(config)
        
        if result.is_ok():
            data = result.unwrap()
            print(f"✅ Found {data.poi_count} hospitals")
            print(f"✅ Generated {data.isochrone_count} driving isochrones")
            print(f"✅ Analyzed {data.census_units_analyzed} census units")
        else:
            error = result.unwrap_err()
            print(f"❌ Error: {error.message}")
    
    # Example 4: Using custom POIs with different travel modes
    print("\n4. Using custom POI file with bike mode")
    
    # Create a simple custom POI file
    custom_poi_file = Path("output/custom_pois.csv")
    custom_poi_file.parent.mkdir(exist_ok=True)
    custom_poi_file.write_text(
        "name,lat,lon\n"
        "UNC Campus,35.9049,-79.0482\n"
        "Franklin Street,35.9132,-79.0558\n"
        "Carrboro Plaza,35.9101,-79.0753\n"
    )
    
    config = (
        SocialMapperBuilder()
        .with_custom_pois(custom_poi_file)
        .with_travel_time(15)
        .with_travel_mode("bike")
        .with_census_variables("total_population", "median_age")
        .with_output_directory("output/custom_bike_example")
        .build()
    )
    
    with SocialMapperClient() as client:
        result = client.run_analysis(config)
        
        if result.is_ok():
            data = result.unwrap()
            print(f"✅ Loaded {data.poi_count} custom POIs")
            print(f"✅ Generated {data.isochrone_count} biking isochrones")
            print(f"✅ Analyzed {data.census_units_analyzed} census units")
        else:
            error = result.unwrap_err()
            print(f"❌ Error: {error.message}")
    
    print("\n=== Travel Mode Comparison Complete ===")
    print("\nNote: Different travel modes use different road networks:")
    print("- Walk: Pedestrian paths, sidewalks, crosswalks")
    print("- Bike: Bike lanes, shared roads, trails")
    print("- Drive: Roads accessible by cars")
    print("\nCheck the output folders to compare the different isochrone shapes!")


if __name__ == "__main__":
    main()