#!/usr/bin/env python3
"""
SocialMapper Tutorial 01: Getting Started with Accessibility Analysis

LEARNING OBJECTIVES:
- Create travel-time isochrones from any location
- Discover points of interest within accessible areas
- Retrieve and analyze census demographics
- Visualize accessibility patterns on interactive maps
- Understand the core concepts of accessibility analysis

PREREQUISITES:
- Basic Python knowledge (variables, functions, loops)
- Understanding of geographic coordinates (latitude/longitude)
- SocialMapper installed: pip install socialmapper
- Census API key (optional): Set CENSUS_API_KEY environment variable

KEY CONCEPTS:
- Isochrone: Area reachable within a specified travel time
- POI (Point of Interest): Locations like libraries, hospitals, parks
- Census Block Group: Geographic unit for demographic data (~600-3000 people)
- Accessibility Analysis: Understanding who can reach what resources
- Travel Modes: Different transportation methods (walk, bike, drive)

TIME ESTIMATE: 15-20 minutes

WHAT YOU'LL BUILD:
A complete accessibility analysis showing libraries reachable within 15 minutes
of driving from downtown Raleigh, NC, including population demographics and
visualization maps.
"""

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available - continue without it
    pass

import sys
from pathlib import Path

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    create_map,
    get_poi
)


def main():
    """Run a basic SocialMapper analysis with choropleth visualization."""

    print("🗺️  SocialMapper Tutorial 01: Getting Started\n")
    print("This tutorial will analyze accessibility in Raleigh, NC using")
    print("the simplified functional API - no client class needed!\n")

    # =================================================================
    # Step 1: Create an isochrone
    # =================================================================
    print("Step 1: Creating a travel-time isochrone...")
    print("An isochrone shows all areas reachable within a given time.")
    print("Think of it as a 'reachability bubble' around your location.\n")

    # Location coordinates - Raleigh, NC downtown
    # TIP: Find coordinates by right-clicking in Google Maps → "What's here?"
    location = (35.7796, -78.6382)
    travel_time = 15  # minutes - typical threshold for walkable/drivable access
    travel_mode = "drive"  # Options: "walk", "bike", "drive"

    print(f"  📍 Location: Raleigh, NC {location}")
    print(f"  ⏱️  Travel Time: {travel_time} minutes")
    print(f"  🚗 Travel Mode: {travel_mode}\n")

    try:
        # Create the isochrone polygon
        # This calls the OSRM routing engine to calculate reachable areas
        isochrone = create_isochrone(
            location=location,
            travel_time=travel_time,
            travel_mode=travel_mode
        )

        print(f"✅ Isochrone created!")

        # The isochrone is a GeoJSON Feature with properties
        area_km2 = isochrone['properties']['area_sq_km']
        print(f"   Area: {area_km2:.2f} km²")

        # Real-world context: How big is this area?
        if area_km2 < 10:
            print(f"   Context: About the size of a small town")
        elif area_km2 < 50:
            print(f"   Context: About the size of a mid-sized city district")
        else:
            print(f"   Context: Covers multiple city districts")
        print()

        # =================================================================
        # Step 2: Find POIs within the isochrone
        # =================================================================
        print("Step 2: Finding libraries near the location...")
        print("POIs help us understand what resources are accessible.\n")

        # Search for libraries within our travel time
        # The function automatically filters by the isochrone boundary
        pois = get_poi(
            location=location,
            categories=["library"],  # Can be multiple: ["library", "school"]
            travel_time=travel_time,
            limit=10  # Maximum POIs to return
        )

        print(f"✅ Found {len(pois)} libraries within {travel_time} minutes")

        if pois:
            print("   Top 3 closest libraries:")
            for i, poi in enumerate(pois[:3], 1):
                name = poi.get('name', 'Unknown')
                distance = poi.get('distance_km', 0)
                # Convert to minutes (rough estimate: 40 km/h average speed)
                time_estimate = (distance / 40) * 60
                print(f"   {i}. {name}")
                print(f"      Distance: {distance:.2f} km (~{time_estimate:.0f} min drive)")

            # Analyze distribution
            distances = [poi.get('distance_km', 0) for poi in pois]
            avg_distance = sum(distances) / len(distances)
            print(f"\n   Average distance to libraries: {avg_distance:.2f} km")
        else:
            print("   No libraries found - try a different location or category")
        print()

        # =================================================================
        # Step 3: Get census blocks within the isochrone
        # =================================================================
        print("Step 3: Getting census blocks within the isochrone...")
        print("Census blocks let us understand WHO lives in accessible areas.\n")

        # Find all census block groups that intersect our isochrone
        # These are the smallest geographic units with detailed demographics
        blocks = get_census_blocks(polygon=isochrone)

        print(f"✅ Found {len(blocks)} census block groups")

        if blocks:
            # Calculate coverage statistics
            total_area = sum(b.get('area_sq_km', 0) for b in blocks)
            avg_block_area = total_area / len(blocks) if blocks else 0

            print(f"   Total area covered: {total_area:.2f} km²")
            print(f"   Average block size: {avg_block_area:.2f} km²")

            # Check how well the blocks match our isochrone
            coverage = (total_area / area_km2) * 100 if area_km2 > 0 else 0
            print(f"   Coverage accuracy: {coverage:.0f}% of isochrone area")
        print()

        # =================================================================
        # Step 4: Get census data for those blocks
        # =================================================================
        print("Step 4: Fetching demographic data from US Census...")
        print("This reveals the socioeconomic characteristics of the area.\n")

        if blocks:
            # Extract GEOIDs (unique identifiers) from blocks
            geoids = [block['geoid'] for block in blocks]
            print(f"   Fetching data for {len(geoids)} block groups...")

            # Get demographic data from Census Bureau
            # These variables help understand equity and needs
            census_data = get_census_data(
                location=geoids,
                variables=["population", "median_income", "median_age"],
                year=2022  # Most recent ACS 5-year estimates
            )

            if census_data:
                print(f"✅ Retrieved census data for {len(census_data)} block groups\n")

                # Calculate comprehensive statistics
                populations = []
                incomes = []
                ages = []

                for geoid, data in census_data.items():
                    pop = data.get('population', 0)
                    if pop > 0:
                        populations.append(pop)

                    income = data.get('median_income', 0)
                    if income > 0:  # Filter out missing data
                        incomes.append(income)

                    age = data.get('median_age', 0)
                    if age > 0:
                        ages.append(age)

                # Population analysis
                if populations:
                    total_pop = sum(populations)
                    avg_pop = total_pop / len(populations)
                    print(f"   POPULATION STATISTICS:")
                    print(f"   Total population: {total_pop:,}")
                    print(f"   Average per block: {avg_pop:,.0f}")
                    print(f"   Population density: {total_pop/total_area:,.0f} people/km²")

                # Income analysis
                if incomes:
                    avg_income = sum(incomes) / len(incomes)
                    min_income = min(incomes)
                    max_income = max(incomes)
                    print(f"\n   INCOME STATISTICS:")
                    print(f"   Average median income: ${avg_income:,.0f}")
                    print(f"   Range: ${min_income:,} - ${max_income:,}")

                    # Context for income levels
                    if avg_income < 30000:
                        print(f"   Context: Low-income area")
                    elif avg_income < 60000:
                        print(f"   Context: Middle-income area")
                    else:
                        print(f"   Context: High-income area")

                # Age analysis
                if ages:
                    avg_age = sum(ages) / len(ages)
                    min_age = min(ages)
                    max_age = max(ages)
                    print(f"\n   AGE STATISTICS:")
                    print(f"   Average median age: {avg_age:.1f} years")
                    print(f"   Range: {min_age:.1f} - {max_age:.1f} years")

                    # Context for age distribution
                    if avg_age < 30:
                        print(f"   Context: Young population (students/young professionals)")
                    elif avg_age < 40:
                        print(f"   Context: Middle-aged population (families)")
                    else:
                        print(f"   Context: Older population (established residents)")
                print()

                # =================================================================
                # Step 5: Create visualization maps
                # =================================================================
                print("Step 5: Creating choropleth maps...")
                print("Visual maps help communicate findings effectively.\n")

                # Combine block geometry with census data for mapping
                map_data = []
                for block in blocks:
                    geoid = block['geoid']
                    if geoid in census_data:
                        map_data.append({
                            'geometry': block['geometry'],
                            'geoid': geoid,
                            'population': census_data[geoid].get('population', 0),
                            'median_income': census_data[geoid].get('median_income', 0),
                            'median_age': census_data[geoid].get('median_age', 0),
                            # Add calculated density
                            'pop_density': (census_data[geoid].get('population', 0) /
                                          block.get('area_sq_km', 1) if block.get('area_sq_km', 0) > 0 else 0)
                        })

                if map_data:
                    # Create output directory
                    output_dir = Path("output/maps")
                    output_dir.mkdir(parents=True, exist_ok=True)

                    # Create population density map (more meaningful than raw population)
                    pop_map = create_map(
                        data=map_data,
                        column="pop_density",
                        title=f"Population Density - {travel_time}min {travel_mode.title()} from Raleigh",
                        save_path=str(output_dir / "tutorial01_population_density.png")
                    )
                    print("   ✅ Created population density map")

                    # Create income map with better title
                    income_map = create_map(
                        data=map_data,
                        column="median_income",
                        title=f"Median Household Income - {travel_time}min {travel_mode.title()} from Raleigh",
                        save_path=str(output_dir / "tutorial01_income.png")
                    )
                    print("   ✅ Created median income map")

                    # Create age map
                    age_map = create_map(
                        data=map_data,
                        column="median_age",
                        title=f"Median Age Distribution - {travel_time}min {travel_mode.title()} from Raleigh",
                        save_path=str(output_dir / "tutorial01_age.png")
                    )
                    print("   ✅ Created median age map")

                    print(f"\n📁 Maps saved to: {output_dir.absolute()}/")
                    print("   Open these images to see geographic patterns in the data!\n")
            else:
                print("⚠️  No census data available - check your Census API key\n")
        else:
            print("⚠️  No census blocks found - try a different location\n")

        # =================================================================
        # Summary and Next Steps
        # =================================================================
        print("=" * 70)
        print("🎉 Tutorial complete! Here's what you learned:\n")

        print("📚 WHAT WE DID:")
        print(f"1. Created a {travel_time}-minute {travel_mode} isochrone around Raleigh")
        print(f"2. Found {len(pois)} libraries within that area")
        print(f"3. Retrieved {len(blocks)} census block groups")
        print("4. Analyzed demographics (population, income, age)")
        print("5. Created choropleth maps to visualize patterns")

        print("\n💡 KEY INSIGHTS FROM THIS ANALYSIS:")
        if pois and blocks and census_data:
            lib_per_capita = len(pois) / (total_pop / 10000) if total_pop > 0 else 0
            print(f"- Library access: {lib_per_capita:.2f} libraries per 10,000 people")
            print(f"- Service area: {total_pop:,} people within {travel_time} min")
            print(f"- Demographics: Median income ${avg_income:,.0f}, age {avg_age:.0f}")

        print("\n🔧 KEY API FUNCTIONS LEARNED:")
        print("- create_isochrone(): Define reachable areas")
        print("- get_poi(): Find points of interest")
        print("- get_census_blocks(): Get geographic units")
        print("- get_census_data(): Retrieve demographics")
        print("- create_map(): Visualize spatial data")

        print("\n🚀 NEXT STEPS:")
        print("- Continue to Tutorial 02 to compare walk/bike/drive modes")
        print("- Try different locations (your city!)")
        print("- Explore other POI types: 'hospital', 'school', 'grocery'")
        print("- Adjust travel times: 5, 10, 20, 30 minutes")

        print("\n⚠️  COMMON MISTAKES TO AVOID:")
        print("- Using addresses instead of coordinates (geocoding limits)")
        print("- Forgetting to set Census API key (get free at census.gov)")
        print("- Not checking if data exists before processing")
        print("- Ignoring coordinate order: (latitude, longitude)")

        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔍 TROUBLESHOOTING:")
        print("1. Check your internet connection")
        print("2. Verify Census API key is set:")
        print("   - Get free key at: https://api.census.gov/data/key_signup.html")
        print("   - Set in .env file: CENSUS_API_KEY=your_key_here")
        print("3. Ensure coordinates are valid (lat between -90 and 90)")
        print("4. Try with demo mode if API issues persist")
        return 1


# =================================================================
# EXERCISES SECTION
# =================================================================
"""
EXERCISES: Test your understanding!

EXERCISE 1: MODIFY LOCATION (Beginner - 5 min)
   Change the location to your hometown or a city you're interested in.

   Hint: Use Google Maps to find coordinates (right-click → "What's here?")
   Expected: New isochrone covering a different area

   Solution:
   # Example: New York City
   location = (40.7128, -74.0060)
   # Example: San Francisco
   location = (37.7749, -122.4194)

EXERCISE 2: COMPARE TRAVEL TIMES (Beginner - 10 min)
   Create isochrones for 5, 10, 15, and 20 minutes. How does area scale?

   Hint: Use a loop to iterate over travel_time values
   Expected: Area increases non-linearly with time (roughly quadratic)

   Solution:
   for minutes in [5, 10, 15, 20]:
       iso = create_isochrone(location, minutes, "drive")
       area = iso['properties']['area_sq_km']
       print(f"{minutes} min: {area:.2f} km²")

EXERCISE 3: MULTI-POI SEARCH (Intermediate - 10 min)
   Find hospitals, schools, AND parks. Which is most accessible?

   Hint: Loop through different category lists
   Expected: Different POI types have different distributions

   Solution:
   poi_types = ["hospital", "school", "park"]
   for poi_type in poi_types:
       pois = get_poi(location, [poi_type], 15, limit=20)
       print(f"{poi_type}: {len(pois)} found")
       if pois:
           avg_dist = sum(p['distance_km'] for p in pois) / len(pois)
           print(f"  Average distance: {avg_dist:.2f} km")

EXERCISE 4: CALCULATE EQUITY METRICS (Intermediate - 15 min)
   What percentage of low-income residents can reach a library in 15 minutes?

   Hint: Filter census_data where median_income < 40000
   Expected: A percentage showing library access for low-income areas

   Solution:
   low_income_pop = 0
   total_pop = 0
   for geoid, data in census_data.items():
       pop = data.get('population', 0)
       income = data.get('median_income', 0)
       total_pop += pop
       if income > 0 and income < 40000:
           low_income_pop += pop

   if total_pop > 0:
       pct = (low_income_pop / total_pop) * 100
       print(f"Low-income population with access: {pct:.1f}%")

EXERCISE 5: CREATE COMPARISON MAP (Advanced - 20 min)
   Create a map showing library density (libraries per 10,000 people)

   Hint: Calculate metric for each block, add to map_data
   Expected: Choropleth showing which areas have better library access

   Solution:
   # For each block, calculate libraries within 5km
   for block in map_data:
       block_center = (
           block['geometry']['coordinates'][0][0][1],  # lat
           block['geometry']['coordinates'][0][0][0]   # lon
       )
       nearby_libs = get_poi(block_center, ["library"], 5, limit=10)
       pop = block['population']
       block['lib_per_10k'] = (len(nearby_libs) / pop * 10000) if pop > 0 else 0

   # Create the map
   lib_map = create_map(
       data=map_data,
       column="lib_per_10k",
       title="Libraries per 10,000 People",
       save_path="output/maps/library_density.png"
   )

CHALLENGE: ACCESSIBILITY REPORT (Advanced - 30 min)
   Generate a text report summarizing accessibility for decision makers.
   Include: population served, average distance to services, equity gaps.

   Bonus: Export to CSV or JSON for further analysis.
"""

if __name__ == "__main__":
    sys.exit(main())