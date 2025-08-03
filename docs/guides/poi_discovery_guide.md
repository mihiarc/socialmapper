# 🎯 POI Discovery Usage Guide

This comprehensive guide walks you through using SocialMapper's POI Discovery feature, from simple queries to advanced analysis workflows. You'll learn practical techniques for exploring Points of Interest around any location within realistic travel constraints.

## Table of Contents

- [Quick Start](#quick-start)
- [Basic Usage Patterns](#basic-usage-patterns)
- [Advanced Configurations](#advanced-configurations)
- [Working with Results](#working-with-results)
- [Real-World Use Cases](#real-world-use-cases)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Quick Start

### Your First POI Discovery

Let's start with the simplest possible POI discovery - finding what's within a 15-minute walk of downtown Portland:

```python
from socialmapper import SocialMapperClient

# Simple POI discovery
with SocialMapperClient() as client:
    result = client.discover_nearby_pois(
        location="Pioneer Square, Portland, OR",
        travel_time=15,
        travel_mode="walk"
    )
    
    match result:
        case result if result.is_ok():
            poi_result = result.unwrap()
            print(f"🎉 Found {poi_result.total_poi_count} POIs!")
            
            # Show what we found
            for category, count in poi_result.category_counts.items():
                print(f"  {category}: {count} locations")
                
        case result if result.is_err():
            error = result.unwrap_err()
            print(f"❌ Error: {error.message}")
```

This creates:
- 📊 CSV file with all POI data
- 🗺️ GeoJSON files for mapping
- 🌐 Interactive HTML map
- 📁 All files in `output/` directory

### Understanding the Output

After running your first discovery, check the `output/` directory:

```
output/
├── poi_discovery_15min_walk.csv          # All POIs in spreadsheet format
├── poi_discovery_15min_walk_pois.geojson # POI locations for GIS
├── poi_discovery_15min_walk_isochrone.geojson # Travel boundary
└── poi_discovery_map_15min.html          # Interactive map
```

**Pro Tip:** Open the HTML map in your browser to visually explore your results!

---

## Basic Usage Patterns

### 1. Location Specification

POI discovery supports two ways to specify your starting location:

#### Using Addresses
```python
# City center
result = client.discover_nearby_pois(location="downtown Seattle, WA")

# Specific address
result = client.discover_nearby_pois(location="1600 Pennsylvania Avenue, Washington DC")

# Landmark
result = client.discover_nearby_pois(location="Golden Gate Bridge, San Francisco")
```

#### Using Coordinates
```python
# Precise coordinates (latitude, longitude)
result = client.discover_nearby_pois(location=(40.7589, -73.9851))  # Times Square

# From GPS data
gps_lat, gps_lon = get_current_location()  # Your GPS function
result = client.discover_nearby_pois(location=(gps_lat, gps_lon))
```

### 2. Travel Modes and Times

#### Walking Analysis (Best for Urban Areas)
```python
# 10-minute walk - immediate neighborhood
result = client.discover_nearby_pois(
    location="Harvard Square, Cambridge, MA",
    travel_time=10,
    travel_mode="walk"
)

# 20-minute walk - extended neighborhood
result = client.discover_nearby_pois(
    location="downtown Boulder, CO", 
    travel_time=20,
    travel_mode="walk"
)
```

#### Biking Analysis (Best for Mid-Distance)
```python
# 15-minute bike ride - good for commute analysis
result = client.discover_nearby_pois(
    location="University of Texas, Austin",
    travel_time=15,
    travel_mode="bike"
)

# 30-minute bike ride - comprehensive area coverage
result = client.discover_nearby_pois(
    location="downtown Portland, OR",
    travel_time=30,
    travel_mode="bike"
)
```

#### Driving Analysis (Best for Rural/Suburban)
```python
# 10-minute drive - local area
result = client.discover_nearby_pois(
    location="Small Town Main Street",
    travel_time=10,
    travel_mode="drive"
)

# 30-minute drive - regional analysis
result = client.discover_nearby_pois(
    location="Rural Community Center",
    travel_time=30,
    travel_mode="drive"
)
```

### 3. Category Filtering

#### Focus on Specific Categories
```python
# Healthcare accessibility study
result = client.discover_nearby_pois(
    location="Senior Living Community",
    travel_time=15,
    travel_mode="drive",
    poi_categories=["healthcare"]
)

# Food access analysis
result = client.discover_nearby_pois(
    location="Low-income neighborhood",
    travel_time=20,
    travel_mode="walk",
    poi_categories=["food_and_drink", "shopping"]
)

# Student needs analysis
result = client.discover_nearby_pois(
    location="University Campus",
    travel_time=15,
    travel_mode="bike",
    poi_categories=["food_and_drink", "education", "recreation"]
)
```

#### Exclude Unwanted Categories
```python
# Everything except utilities (focus on services)
result = client.discover_nearby_pois(
    location="City Hall",
    travel_time=20,
    exclude_categories=["utilities"]
)
```

---

## Advanced Configurations

### 1. Using the Builder Pattern

For complex analysis, use the builder pattern for better control:

```python
from socialmapper.api.builder import SocialMapperBuilder
from socialmapper.isochrone import TravelMode
from pathlib import Path

# Comprehensive analysis configuration
analysis = (
    SocialMapperBuilder()
    .with_nearby_poi_discovery(
        location="Downtown Denver, CO",
        travel_time=25,
        travel_mode=TravelMode.BIKE
    )
    .with_poi_categories(
        "food_and_drink", 
        "healthcare", 
        "education",
        "recreation"
    )
    .exclude_poi_categories("utilities")
    .limit_pois_per_category(30)
    .with_export_options(
        csv=True,
        geojson=True,
        maps=True,
        output_dir=Path("analysis/denver_bike_access")
    )
)

result = analysis.execute()
```

### 2. Pipeline Direct Usage

For maximum control, use the pipeline directly:

```python
from socialmapper.api.result_types import NearbyPOIDiscoveryConfig
from socialmapper.pipeline.poi_discovery import execute_poi_discovery_pipeline
from socialmapper.isochrone import TravelMode
from pathlib import Path

# Detailed configuration
config = NearbyPOIDiscoveryConfig(
    location=(37.7749, -122.4194),  # San Francisco
    travel_time=20,
    travel_mode=TravelMode.WALK,
    poi_categories=["food_and_drink", "healthcare", "services"],
    exclude_categories=["utilities"],
    export_csv=True,
    export_geojson=True,
    create_map=True,
    output_dir=Path("sf_analysis"),
    max_pois_per_category=50,
    include_poi_details=True
)

result = execute_poi_discovery_pipeline(config)
```

### 3. Convenience Functions

For simple coordinate-based analysis:

```python
from socialmapper.pipeline.poi_discovery import (
    discover_pois_near_address,
    discover_pois_near_coordinates
)

# Quick address analysis
result = discover_pois_near_address(
    address="Times Square, New York",
    travel_time=15,
    categories=["food_and_drink", "recreation"]
)

# Quick coordinate analysis  
result = discover_pois_near_coordinates(
    latitude=34.0522, 
    longitude=-118.2437,  # Los Angeles
    travel_time=20,
    travel_mode=TravelMode.DRIVE
)
```

---

## Working with Results

### 1. Exploring POI Data

#### Basic Result Analysis
```python
if result.is_ok():
    poi_result = result.unwrap()
    
    # Overview statistics
    print(f"Total POIs found: {poi_result.total_poi_count}")
    print(f"Categories covered: {len(poi_result.pois_by_category)}")
    print(f"Search area: {poi_result.isochrone_area_km2:.1f} km²")
    
    # Category breakdown
    print("\n📊 POIs by Category:")
    for category, count in poi_result.category_counts.items():
        print(f"  {category.replace('_', ' ').title()}: {count}")
```

#### Detailed POI Information
```python
# Get all POIs as a flat list
all_pois = poi_result.get_all_pois()

# Show detailed info for first few POIs
for poi in all_pois[:5]:
    distance_km = poi.straight_line_distance_m / 1000
    print(f"\n🏪 {poi.name}")
    print(f"   Category: {poi.category} → {poi.subcategory}")
    print(f"   Distance: {distance_km:.1f} km")
    print(f"   Location: {poi.latitude:.4f}, {poi.longitude:.4f}")
    
    if poi.address:
        print(f"   Address: {poi.address}")
    if poi.phone:
        print(f"   Phone: {poi.phone}")
    if poi.website:
        print(f"   Website: {poi.website}")
```

#### Distance-Based Analysis
```python
# Get POIs sorted by distance
nearest_pois = poi_result.get_pois_by_distance()

print("🚶‍♀️ Nearest POIs:")
for poi in nearest_pois[:10]:  # Top 10 nearest
    distance_m = poi.straight_line_distance_m
    print(f"  {distance_m:4.0f}m - {poi.name} ({poi.category})")

# Filter by maximum distance
nearby_pois = poi_result.get_pois_by_distance(max_distance_m=1000)
print(f"\nPOIs within 1km: {len(nearby_pois)}")
```

### 2. Category-Specific Analysis

```python
# Analyze specific categories
for category, pois in poi_result.pois_by_category.items():
    if not pois:
        continue
        
    distances = [poi.straight_line_distance_m for poi in pois]
    avg_distance = sum(distances) / len(distances)
    min_distance = min(distances)
    
    print(f"\n{category.replace('_', ' ').title()}:")
    print(f"  Count: {len(pois)}")
    print(f"  Nearest: {min_distance:.0f}m")
    print(f"  Average distance: {avg_distance:.0f}m")
    
    # Show top 3 in this category
    sorted_pois = sorted(pois, key=lambda p: p.straight_line_distance_m)
    for i, poi in enumerate(sorted_pois[:3], 1):
        print(f"    {i}. {poi.name} ({poi.straight_line_distance_m:.0f}m)")
```

### 3. Export and Integration

#### Working with Generated Files
```python
if poi_result.files_generated:
    print("\n📁 Generated Files:")
    for file_type, path in poi_result.files_generated.items():
        print(f"  {file_type}: {path}")
        
        # You can now use these files with other tools:
        if file_type == "csv":
            import pandas as pd
            df = pd.read_csv(path)
            print(f"    CSV has {len(df)} rows")
            
        elif file_type == "poi_geojson":
            import geopandas as gpd
            gdf = gpd.read_file(path)
            print(f"    GeoJSON has {len(gdf)} features")
```

#### Integration with Pandas
```python
# Convert POI data to DataFrame for analysis
import pandas as pd

poi_data = []
for poi in poi_result.get_all_pois():
    poi_data.append({
        'name': poi.name,
        'category': poi.category,
        'subcategory': poi.subcategory,
        'distance_km': poi.straight_line_distance_m / 1000,
        'lat': poi.latitude,
        'lon': poi.longitude,
        'has_phone': poi.phone is not None,
        'has_website': poi.website is not None
    })

df = pd.DataFrame(poi_data)

# Analyze with pandas
print(df.groupby('category')['distance_km'].agg(['count', 'mean', 'min']).round(2))
```

---

## Real-World Use Cases

### 1. Food Desert Analysis

Identify areas with limited food access:

```python
def analyze_food_desert(location, max_walk_time=15):
    """Analyze food accessibility for a location."""
    
    result = client.discover_nearby_pois(
        location=location,
        travel_time=max_walk_time,
        travel_mode="walk",
        poi_categories=["food_and_drink", "shopping"],
        output_dir=f"food_analysis/{location.replace(' ', '_')}"
    )
    
    if result.is_ok():
        poi_result = result.unwrap()
        
        # Count food-related POIs
        grocery_count = 0
        restaurant_count = 0
        
        for category, pois in poi_result.pois_by_category.items():
            if category == "food_and_drink":
                restaurant_count = len(pois)
            elif category == "shopping":
                # Filter for grocery stores
                grocery_count = len([
                    poi for poi in pois 
                    if "supermarket" in poi.subcategory.lower() or
                       "grocery" in poi.name.lower()
                ])
        
        # Assess food access
        total_food_options = grocery_count + restaurant_count
        area_km2 = poi_result.isochrone_area_km2
        
        print(f"\n🍎 Food Access Analysis for {location}")
        print(f"Walk time constraint: {max_walk_time} minutes")
        print(f"Analysis area: {area_km2:.1f} km²")
        print(f"Grocery stores: {grocery_count}")
        print(f"Restaurants/cafes: {restaurant_count}")
        print(f"Total food options: {total_food_options}")
        
        # Food desert criteria (customize as needed)
        if total_food_options == 0:
            print("⚠️  SEVERE: No food sources found")
        elif total_food_options < 3:
            print("⚠️  LIMITED: Very few food options")
        elif grocery_count == 0:
            print("⚠️  CONCERN: No grocery stores found")
        else:
            print("✅ ADEQUATE: Good food access")
            
        return poi_result
    else:
        print(f"❌ Analysis failed: {result.unwrap_err().message}")
        return None

# Analyze multiple neighborhoods
neighborhoods = [
    "East Austin, TX",
    "South Chicago, IL",
    "Rural Valley, Small Town"
]

for neighborhood in neighborhoods:
    analyze_food_desert(neighborhood)
```

### 2. Healthcare Accessibility Study

Evaluate healthcare access for different travel modes:

```python
def healthcare_accessibility_study(location):
    """Comprehensive healthcare accessibility analysis."""
    
    travel_scenarios = [
        {"mode": "walk", "time": 15, "description": "Walking access"},
        {"mode": "bike", "time": 15, "description": "Cycling access"},
        {"mode": "drive", "time": 15, "description": "Driving access"},
    ]
    
    results = {}
    
    for scenario in travel_scenarios:
        print(f"\n🏥 Analyzing {scenario['description']} for {location}")
        
        result = client.discover_nearby_pois(
            location=location,
            travel_time=scenario["time"],
            travel_mode=scenario["mode"],
            poi_categories=["healthcare"],
            output_dir=f"healthcare_study/{scenario['mode']}"
        )
        
        if result.is_ok():
            poi_result = result.unwrap()
            healthcare_pois = poi_result.pois_by_category.get("healthcare", [])
            
            # Categorize healthcare types
            hospitals = [p for p in healthcare_pois if "hospital" in p.subcategory.lower()]
            clinics = [p for p in healthcare_pois if "clinic" in p.subcategory.lower()]
            pharmacies = [p for p in healthcare_pois if "pharmacy" in p.subcategory.lower()]
            dentists = [p for p in healthcare_pois if "dentist" in p.subcategory.lower()]
            
            results[scenario["mode"]] = {
                "total": len(healthcare_pois),
                "hospitals": len(hospitals),
                "clinics": len(clinics),
                "pharmacies": len(pharmacies),
                "dentists": len(dentists),
                "area_km2": poi_result.isochrone_area_km2,
                "nearest_distance": min([p.straight_line_distance_m for p in healthcare_pois]) if healthcare_pois else None
            }
            
            print(f"  Found {len(healthcare_pois)} healthcare facilities")
            print(f"  Hospitals: {len(hospitals)}, Clinics: {len(clinics)}")
            print(f"  Pharmacies: {len(pharmacies)}, Dentists: {len(dentists)}")
            
            if healthcare_pois:
                nearest = min(healthcare_pois, key=lambda p: p.straight_line_distance_m)
                print(f"  Nearest: {nearest.name} ({nearest.straight_line_distance_m:.0f}m)")
    
    # Compare accessibility across travel modes
    print(f"\n📊 Healthcare Accessibility Comparison for {location}")
    print("Mode     | Total | Hospitals | Clinics | Pharmacies | Nearest (m)")
    print("-" * 65)
    
    for mode, data in results.items():
        nearest_str = f"{data['nearest_distance']:.0f}" if data['nearest_distance'] else "None"
        print(f"{mode:8} | {data['total']:5} | {data['hospitals']:9} | "
              f"{data['clinics']:7} | {data['pharmacies']:10} | {nearest_str}")
    
    return results

# Run healthcare study
healthcare_results = healthcare_accessibility_study("Rural Hospital, Small Town")
```

### 3. Transit-Oriented Development Analysis

Analyze POI density around transit stations:

```python
def transit_pod_analysis(transit_station_location):
    """Analyze Points of Interest around transit stations."""
    
    # Different walking distances from transit
    walk_times = [5, 10, 15]  # minutes
    
    for walk_time in walk_times:
        print(f"\n🚉 {walk_time}-minute walk from {transit_station_location}")
        
        result = client.discover_nearby_pois(
            location=transit_station_location,
            travel_time=walk_time,
            travel_mode="walk",
            exclude_categories=["utilities"],  # Focus on services
            output_dir=f"transit_analysis/{walk_time}min_walk"
        )
        
        if result.is_ok():
            poi_result = result.unwrap()
            
            # Calculate POI density
            area_km2 = poi_result.isochrone_area_km2
            poi_density = poi_result.total_poi_count / area_km2
            
            print(f"  Area: {area_km2:.2f} km²")
            print(f"  Total POIs: {poi_result.total_poi_count}")
            print(f"  POI Density: {poi_density:.1f} POIs/km²")
            
            # Analyze category mix
            essential_categories = ["food_and_drink", "healthcare", "shopping", "services"]
            essential_count = sum(
                poi_result.category_counts.get(cat, 0) 
                for cat in essential_categories
            )
            
            print(f"  Essential services: {essential_count}/{poi_result.total_poi_count} ({essential_count/poi_result.total_poi_count*100:.1f}%)")
            
            # TOD quality assessment
            if poi_density > 50 and essential_count > 20:
                print("  ✅ HIGH QUALITY: Excellent transit-oriented development")
            elif poi_density > 25 and essential_count > 10:
                print("  ✅ GOOD: Good transit-oriented development")
            elif poi_density > 10:
                print("  ⚠️  MODERATE: Some transit-oriented development")
            else:
                print("  ❌ LOW: Limited transit-oriented development")

# Analyze multiple transit stations
stations = [
    "Union Station, Portland, OR",
    "Harvard Square T Station, Cambridge, MA",
    "Downtown Transit Center, Small City"
]

for station in stations:
    transit_pod_analysis(station)
```

---

## Performance Optimization

### 1. Managing Query Complexity

#### Large Area Optimization
```python
# For large travel times or areas, consider limitations
result = client.discover_nearby_pois(
    location="Rural Center",
    travel_time=45,  # Large area
    travel_mode="drive",
    max_pois_per_category=25,  # Limit results
    poi_categories=["healthcare", "shopping"]  # Focus on essentials
)
```

#### Progressive Analysis
```python
def progressive_poi_analysis(location, max_time=30):
    """Analyze POI availability at increasing distances."""
    
    time_intervals = [5, 10, 15, 20, 30]
    cumulative_results = {}
    
    for travel_time in time_intervals:
        if travel_time > max_time:
            break
            
        print(f"Analyzing {travel_time}-minute accessibility...")
        
        result = client.discover_nearby_pois(
            location=location,
            travel_time=travel_time,
            travel_mode="walk",
            max_pois_per_category=20  # Keep results manageable
        )
        
        if result.is_ok():
            poi_result = result.unwrap()
            cumulative_results[travel_time] = {
                "total_pois": poi_result.total_poi_count,
                "area_km2": poi_result.isochrone_area_km2,
                "categories": len(poi_result.pois_by_category)
            }
    
    # Show progressive accessibility
    print(f"\n📈 Progressive Accessibility from {location}")
    print("Time | POIs | Area(km²) | Categories")
    print("-" * 35)
    
    for time, data in cumulative_results.items():
        print(f"{time:4}m | {data['total_pois']:4} | {data['area_km2']:8.2f} | {data['categories']:10}")
```

### 2. Batch Processing

#### Multiple Location Analysis
```python
def batch_poi_analysis(locations, travel_time=15, travel_mode="walk"):
    """Analyze multiple locations efficiently."""
    
    results = {}
    
    for i, location in enumerate(locations, 1):
        print(f"\n[{i}/{len(locations)}] Analyzing {location}")
        
        try:
            result = client.discover_nearby_pois(
                location=location,
                travel_time=travel_time,
                travel_mode=travel_mode,
                output_dir=f"batch_analysis/location_{i:02d}"
            )
            
            if result.is_ok():
                poi_result = result.unwrap()
                results[location] = {
                    "success": True,
                    "total_pois": poi_result.total_poi_count,
                    "categories": list(poi_result.category_counts.keys()),
                    "area_km2": poi_result.isochrone_area_km2
                }
                print(f"  ✅ Found {poi_result.total_poi_count} POIs")
            else:
                error = result.unwrap_err()
                results[location] = {
                    "success": False,
                    "error": error.message
                }
                print(f"  ❌ Error: {error.message}")
                
        except Exception as e:
            results[location] = {
                "success": False,
                "error": str(e)
            }
            print(f"  ❌ Exception: {str(e)}")
    
    # Summary report
    successful = sum(1 for r in results.values() if r["success"])
    print(f"\n📊 Batch Analysis Summary")
    print(f"Locations processed: {len(locations)}")
    print(f"Successful analyses: {successful}")
    print(f"Failed analyses: {len(locations) - successful}")
    
    return results

# Example batch analysis
city_centers = [
    "downtown Seattle, WA",
    "downtown Portland, OR", 
    "downtown Denver, CO",
    "downtown Austin, TX"
]

batch_results = batch_poi_analysis(city_centers, travel_time=20, travel_mode="walk")
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Location Geocoding Problems

**Issue:** "Failed to geocode address"
```python
# Problem: Vague or ambiguous address
result = client.discover_nearby_pois(location="Main Street")  # ❌ Too vague

# Solution: Be more specific
result = client.discover_nearby_pois(location="Main Street, Portland, OR")  # ✅ Better

# Or use coordinates for precision
result = client.discover_nearby_pois(location=(45.5152, -122.6784))  # ✅ Precise
```

**Issue:** International address problems
```python
# For international locations, include country
result = client.discover_nearby_pois(location="Leicester Square, London, UK")

# Or use local language if needed
result = client.discover_nearby_pois(location="Place de la République, Paris, France")
```

#### 2. No POIs Found

**Issue:** "No POIs found within the travel time isochrone"

This often happens in rural areas or with restrictive category filters.

```python
# Check 1: Increase travel time
result = client.discover_nearby_pois(
    location="Rural Location",
    travel_time=30,  # ⬆️ Increased from 15
    travel_mode="drive"
)

# Check 2: Remove category restrictions
result = client.discover_nearby_pois(
    location="Rural Location",
    travel_time=20
    # ❌ Don't use poi_categories for rural areas initially
)

# Check 3: Use driving instead of walking
result = client.discover_nearby_pois(
    location="Suburban Location",
    travel_time=15,
    travel_mode="drive"  # ⬆️ Changed from "walk"
)
```

#### 3. Performance Issues

**Issue:** Queries timing out or taking too long

```python
# Solution 1: Limit results
result = client.discover_nearby_pois(
    location="Large City Center",
    travel_time=30,
    max_pois_per_category=25,  # ⬇️ Limit results
    poi_categories=["food_and_drink", "healthcare"]  # ⬇️ Fewer categories
)

# Solution 2: Progressive approach
def smart_poi_discovery(location):
    """Try quick analysis first, then expand if needed."""
    
    # Start with modest parameters
    result = client.discover_nearby_pois(
        location=location,
        travel_time=15,
        max_pois_per_category=10
    )
    
    if result.is_ok() and result.unwrap().total_poi_count < 20:
        # If few results, expand search
        print("Few POIs found, expanding search...")
        result = client.discover_nearby_pois(
            location=location,
            travel_time=25,
            max_pois_per_category=20
        )
    
    return result
```

#### 4. Data Quality Issues

**Issue:** POIs with missing information

```python
# Check POI completeness
if result.is_ok():
    poi_result = result.unwrap()
    
    complete_pois = []
    incomplete_pois = []
    
    for poi in poi_result.get_all_pois():
        if poi.address and poi.phone:
            complete_pois.append(poi)
        else:
            incomplete_pois.append(poi)
    
    print(f"Complete POI data: {len(complete_pois)}")
    print(f"Incomplete POI data: {len(incomplete_pois)}")
    
    # You can still use incomplete POIs for location analysis
    if incomplete_pois:
        print(f"Note: {len(incomplete_pois)} POIs have limited contact information")
```

### Error Handling Patterns

#### Robust Analysis Function
```python
def robust_poi_analysis(location, travel_time=15, travel_mode="walk"):
    """POI analysis with comprehensive error handling."""
    
    try:
        result = client.discover_nearby_pois(
            location=location,
            travel_time=travel_time,
            travel_mode=travel_mode
        )
        
        match result:
            case result if result.is_ok():
                poi_result = result.unwrap()
                
                if poi_result.total_poi_count == 0:
                    print(f"⚠️  No POIs found for {location}")
                    print("   Try increasing travel time or changing travel mode")
                    return None
                
                if poi_result.warnings:
                    print(f"⚠️  Warnings for {location}:")
                    for warning in poi_result.warnings:
                        print(f"     {warning}")
                
                print(f"✅ {location}: {poi_result.total_poi_count} POIs found")
                return poi_result
                
            case result if result.is_err():
                error = result.unwrap_err()
                
                match error.type:
                    case ErrorType.LOCATION_GEOCODING:
                        print(f"❌ {location}: Could not find location")
                        print(f"   Try being more specific with the address")
                        
                    case ErrorType.POI_QUERY:
                        print(f"❌ {location}: No POIs in area")
                        print(f"   Try increasing travel time or using different travel mode")
                        
                    case ErrorType.NETWORK:
                        print(f"❌ {location}: Network error")
                        print(f"   Check internet connection and try again")
                        
                    case _:
                        print(f"❌ {location}: {error.message}")
                
                return None
                
    except Exception as e:
        print(f"❌ {location}: Unexpected error - {str(e)}")
        return None

# Use robust function
locations = ["Valid City, State", "Invalid Location", "Rural Area"]
for location in locations:
    result = robust_poi_analysis(location)
    if result:
        print(f"   Analysis completed for {location}")
```

---

## Best Practices

### 1. Analysis Design

#### Choose Appropriate Travel Parameters
```python
# Urban analysis - walking focus
urban_params = {
    "travel_time": 15,
    "travel_mode": "walk",
    "poi_categories": ["food_and_drink", "services", "recreation"]
}

# Suburban analysis - mixed mode
suburban_params = {
    "travel_time": 20, 
    "travel_mode": "bike",
    "poi_categories": ["shopping", "healthcare", "education"]
}

# Rural analysis - driving focus
rural_params = {
    "travel_time": 30,
    "travel_mode": "drive",
    "poi_categories": ["healthcare", "shopping", "services"]
}
```

#### Layer Your Analysis
```python
def comprehensive_location_analysis(location):
    """Multi-layered POI analysis for comprehensive understanding."""
    
    analyses = {
        "immediate": {"time": 5, "mode": "walk", "focus": "Daily needs"},
        "neighborhood": {"time": 15, "mode": "walk", "focus": "Walking access"},
        "local_area": {"time": 15, "mode": "bike", "focus": "Cycling access"},
        "regional": {"time": 30, "mode": "drive", "focus": "Driving access"}
    }
    
    results = {}
    
    for analysis_name, params in analyses.items():
        print(f"\n🔍 {params['focus']} analysis ({params['time']}min {params['mode']})")
        
        result = client.discover_nearby_pois(
            location=location,
            travel_time=params["time"],
            travel_mode=params["mode"],
            output_dir=f"comprehensive_analysis/{analysis_name}"
        )
        
        if result.is_ok():
            poi_result = result.unwrap()
            results[analysis_name] = poi_result
            
            print(f"  Found {poi_result.total_poi_count} POIs")
            print(f"  Coverage: {poi_result.isochrone_area_km2:.1f} km²")
        else:
            print(f"  ❌ Analysis failed: {result.unwrap_err().message}")
    
    return results
```

### 2. Data Management

#### Organize Output Files
```python
from datetime import datetime
from pathlib import Path

def organized_poi_analysis(location, analysis_name):
    """POI analysis with organized file output."""
    
    # Create organized directory structure
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"poi_analyses/{analysis_name}/{timestamp}")
    
    result = client.discover_nearby_pois(
        location=location,
        travel_time=20,
        travel_mode="walk",
        output_dir=output_dir
    )
    
    if result.is_ok():
        poi_result = result.unwrap()
        
        # Save analysis metadata
        metadata = {
            "analysis_name": analysis_name,
            "location": location,
            "timestamp": timestamp,
            "total_pois": poi_result.total_poi_count,
            "categories": list(poi_result.category_counts.keys()),
            "parameters": {
                "travel_time": 20,
                "travel_mode": "walk"
            }
        }
        
        metadata_file = output_dir / "analysis_metadata.json"
        with open(metadata_file, 'w') as f:
            import json
            json.dump(metadata, f, indent=2, default=str)
        
        print(f"✅ Analysis saved to: {output_dir}")
        return poi_result
    
    return None
```

#### Result Comparison
```python
def compare_poi_analyses(results_dict):
    """Compare multiple POI analysis results."""
    
    import pandas as pd
    
    comparison_data = []
    
    for name, poi_result in results_dict.items():
        if poi_result:
            comparison_data.append({
                "analysis": name,
                "total_pois": poi_result.total_poi_count,
                "area_km2": poi_result.isochrone_area_km2,
                "poi_density": poi_result.total_poi_count / poi_result.isochrone_area_km2,
                "categories": len(poi_result.pois_by_category),
                "food_and_drink": poi_result.category_counts.get("food_and_drink", 0),
                "healthcare": poi_result.category_counts.get("healthcare", 0),
                "shopping": poi_result.category_counts.get("shopping", 0)
            })
    
    df = pd.DataFrame(comparison_data)
    
    print("📊 POI Analysis Comparison")
    print("=" * 60)
    print(df.to_string(index=False))
    
    return df

# Example usage
locations = {
    "urban_center": "downtown Portland, OR",
    "suburban": "Beaverton, OR", 
    "small_town": "Hood River, OR"
}

results = {}
for name, location in locations.items():
    result = client.discover_nearby_pois(location=location, travel_time=15, travel_mode="walk")
    if result.is_ok():
        results[name] = result.unwrap()

comparison_df = compare_poi_analyses(results)
```

### 3. Quality Assurance

#### Validate Results
```python
def validate_poi_results(poi_result, location):
    """Validate POI discovery results for quality."""
    
    validation_issues = []
    
    # Check basic result quality
    if poi_result.total_poi_count == 0:
        validation_issues.append("No POIs found - may indicate rural area or restrictive search")
    
    if poi_result.isochrone_area_km2 < 0.1:
        validation_issues.append("Very small search area - may need longer travel time")
    
    if poi_result.isochrone_area_km2 > 100:
        validation_issues.append("Very large search area - results may be overwhelming")
    
    # Check category distribution
    if len(poi_result.pois_by_category) < 3:
        validation_issues.append("Few POI categories found - may indicate limited area diversity")
    
    # Check for data completeness
    all_pois = poi_result.get_all_pois()
    pois_with_details = [p for p in all_pois if p.address or p.phone or p.website]
    detail_rate = len(pois_with_details) / len(all_pois) if all_pois else 0
    
    if detail_rate < 0.3:
        validation_issues.append(f"Low detail rate ({detail_rate:.1%}) - POIs may lack contact information")
    
    # Report validation results
    if validation_issues:
        print(f"⚠️  Validation issues for {location}:")
        for issue in validation_issues:
            print(f"   • {issue}")
    else:
        print(f"✅ Results for {location} passed validation")
    
    return len(validation_issues) == 0
```

This comprehensive usage guide provides practical knowledge for effectively using SocialMapper's POI Discovery feature. From simple queries to complex analysis workflows, you now have the tools to explore accessibility and resource distribution in any area of interest.

For detailed API documentation, see the [POI Discovery API Reference](../api/poi_discovery.md). For an overview of the feature's capabilities, check out the [POI Discovery Feature Overview](../features/nearby_poi_discovery.md).