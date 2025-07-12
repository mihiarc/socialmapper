#!/usr/bin/env python3
"""
Quick demo of analyzing the Montana timber mill location using SocialMapper.

This simple example shows the basic usage pattern for custom POI analysis.
"""

from socialmapper import SocialMapperBuilder, SocialMapperClient


def main():
    print("🏭 Montana Timber Mill Analysis - Quick Demo\n")
    
    # Simple analysis using the builder pattern
    with SocialMapperClient() as client:
        # Configure the analysis
        config = (
            SocialMapperBuilder()
            .with_custom_pois("montana_mill_location.csv")
            .with_travel_time(30)  # 30-minute commute radius
            .with_travel_mode("drive")
            .with_census_variables(
                "total_population",
                "median_income",
                "median_age",
                "households"
            )
            .enable_isochrone_export()  # Export the travel-time boundary
            .enable_map_generation()    # Create demographic maps
            .build()
        )
        
        # Run the analysis
        print("Running analysis...")
        result = client.run_analysis(config)
        
        if result.is_ok():
            analysis = result.unwrap()
            
            print("\n✅ Analysis Complete!")
            print(f"\nResults Summary:")
            print(f"- Census units analyzed: {analysis.census_units_analyzed}")
            print(f"- Isochrone area: {analysis.isochrone_area:.1f} km²")
            
            # Display demographic summary
            demographics = analysis.demographics
            print(f"\nDemographics within 30-minute drive:")
            print(f"- Total population: {demographics.get('total_population', 0):,.0f}")
            print(f"- Households: {demographics.get('households', 0):,.0f}")
            print(f"- Median income: ${demographics.get('median_income', 0):,.0f}")
            print(f"- Median age: {demographics.get('median_age', 0):.1f} years")
            
            print(f"\nFiles generated:")
            for file_type, file_path in analysis.files_generated.items():
                print(f"- {file_type}: {file_path}")
                
        else:
            error = result.unwrap_err()
            print(f"❌ Error: {error.message}")
            print("\nTroubleshooting:")
            print("- Ensure montana_mill_location.csv exists")
            print("- Check that you have a Census API key configured")
            print("- Verify internet connection for map tiles")


if __name__ == "__main__":
    main()