# Defining Communities in Rural America

## The Problem with County-Level Analysis

In most data analysis and policy work, "community" defaults to a county. Federal datasets aggregate to counties. Funding formulas use county populations. Reports compare counties. This convention works reasonably well in densely populated areas where county boundaries roughly correspond to functional communities. But across vast stretches of rural America -- the Great Plains, the Mountain West, the rural South, Appalachia -- county boundaries are administrative artifacts that have little to do with how people actually organize their lives.

Consider a few realities of rural geography:

- **County seats are historical accidents.** Many were established in the 19th century based on where a courthouse could be reached by horseback in a day. The town that was central in 1880 may be a near-ghost town today while the population has shifted to a crossroads 30 miles away.
- **People drive past county lines without thinking about it.** A family in rural western Kansas might live in one county, send their kids to school in a second county, buy groceries in a third, and see a doctor in a fourth. Their "community" is defined by the roads they drive, not the lines on a political map.
- **Counties span enormous areas with multiple centers of gravity.** A single county in the Great Plains can be larger than some eastern states, with residents gravitating to several different small towns depending on direction and road access.
- **County-level aggregation masks the patterns that matter.** When you report the median income or poverty rate for a county, you are averaging together people whose daily lives may be oriented toward completely different towns. The statistic describes a political unit, not a lived community.

This is not a minor methodological quibble. When a rural hospital closes, the people affected are not "the county" -- they are the people who could reach that hospital within a reasonable drive. When a school consolidation is proposed, the question is not which county the school is in, but which families can get their children there. When USDA invests in rural broadband or a community health center, the service area is shaped by roads and terrain, not county lines.

## How SocialMapper Defines Communities Differently

SocialMapper approaches community boundaries from the ground up. Instead of starting with an administrative polygon and asking "who lives inside it," SocialMapper starts with a place people actually go -- a town center, a grocery store, a hospital -- and asks "who can reach it?"

The core mechanism is the **isochrone**: a polygon that represents everywhere reachable within a given travel time from a point, using the actual road network. A 20-minute drive-time isochrone from a small Kansas town produces an organic boundary shaped by highways, county roads, terrain, and geography. It captures the town's real sphere of influence -- the area from which people can reasonably make a daily trip for work, school, shopping, or services.

This approach has several properties that make it well-suited to rural analysis:

1. **Boundaries follow the road network, not political lines.** An isochrone from a town on an interstate will stretch along the highway corridor. An isochrone from a town surrounded by hills will be compressed by winding mountain roads. The boundary reflects how people actually travel.

2. **Census block groups within the isochrone represent the real community.** Once you have the travel-time polygon, SocialMapper identifies every census block group that intersects it. These block groups -- the smallest geographic unit for which the Census Bureau publishes detailed demographic data -- become the building blocks of your community definition.

3. **Overlapping isochrones from different towns reveal shared zones and gaps.** When you generate isochrones for multiple towns in a region, the overlaps show areas served by more than one center, and the gaps show areas that are underserved. This is information that county boundaries can never provide.

4. **The analysis is reproducible and adjustable.** Change the travel time from 20 minutes to 30 and the community boundary expands. Switch from driving to walking and it contracts dramatically, revealing equity gaps for residents without vehicles. Every parameter is explicit and defensible.

## Practical Use Cases

### Healthcare Access

In rural areas, the difference between a 20-minute drive and a 45-minute drive to a hospital can be the difference between life and death for a stroke or heart attack patient. County-level healthcare statistics obscure this reality. A county might "have" a hospital, but half its residents may live an hour away from it.

SocialMapper lets you define the actual service area of a rural hospital or clinic and ask precise questions: How many people live within 30 minutes of this facility? What are their demographics? If this facility closes, how far would those people need to drive to reach the next one?

### School District Planning

Rural school consolidation decisions hinge on how far families can realistically transport children. A 20-minute school bus ride is different from a 45-minute one, and the terrain matters. SocialMapper's travel-time boundaries account for the actual road network, giving planners a more accurate picture of which families a school can serve.

### Grocery and Food Access

When a small town's only grocery store closes, the impact ripples through a travel-time community. The USDA defines food deserts using distance thresholds, but those thresholds are straight-line distances that ignore winding rural roads. An isochrone-based analysis using SocialMapper provides a more accurate picture of who depends on a particular store and what happens when it disappears.

### Economic Development

Understanding the true service area of a rural town helps planners direct infrastructure investments. A town that serves as the commercial center for a 30-minute driving radius has a different economic profile than its county statistics suggest. Knowing the actual population and demographics of that service area supports better grant applications, workforce development plans, and business recruitment.

### Emergency Services

Fire stations, ambulance services, and law enforcement response zones are fundamentally about travel time, not political boundaries. SocialMapper can define the response area for an emergency facility and identify populations that fall outside acceptable response times.

### Civic and Social Services

Libraries, community centers, agricultural extension offices, and other civic facilities serve populations defined by accessibility, not jurisdiction. Understanding the true reach of these services helps justify funding and identify gaps.

## Code Examples

The following examples demonstrate how to use SocialMapper's API to define and analyze rural communities. All examples use real towns and are runnable as-is.

### Example 1: Define a Rural Community

The most fundamental operation is defining a community boundary around a rural town. Here, a 20-minute driving isochrone from Hays, Kansas -- a small city of about 20,000 in the western Great Plains -- defines "the community" based on who can reach the town for daily needs.

```python
from socialmapper import create_isochrone, get_census_blocks, get_census_data

# A 20-minute drive from Hays, KS defines the functional community
# -- a more meaningful boundary than Ellis County's political lines
community = create_isochrone("Hays, KS", travel_time=20, travel_mode="drive")

print(f"Community area: {community['properties']['area_sq_km']:.0f} sq km")

# Identify the census block groups within this community
blocks = get_census_blocks(polygon=community)
print(f"Block groups in community: {len(blocks)}")

# Get demographic data for the community
demographics = get_census_data(community, variables=["population", "median_income"])

# Aggregate: total population served by this town
total_pop = sum(
    data.get("population", 0)
    for data in demographics.data.values()
    if data.get("population") is not None
)
print(f"Community population: {total_pop:,}")
```

### Example 2: Find What Services a Rural Community Can Reach

A key question for rural communities is access to essential services. SocialMapper's `get_poi()` function searches for points of interest within a travel-time boundary and returns actual routed travel times via the Valhalla routing engine.

```python
from socialmapper import get_poi

# What healthcare facilities can people in the Hays community reach
# within a 30-minute drive?
healthcare = get_poi(
    "Hays, KS",
    categories=["healthcare"],
    travel_time=30,
    travel_mode="drive",
)
print(f"Healthcare facilities within 30 min: {len(healthcare)}")
for facility in healthcare[:5]:
    print(f"  {facility['name']}: {facility['travel_time_minutes']} min")

# What about education?
education = get_poi(
    "Hays, KS",
    categories=["education"],
    travel_time=20,
    travel_mode="drive",
)
print(f"\nEducation facilities within 20 min: {len(education)}")

# Grocery and retail access -- critical in rural areas
# where the nearest supermarket may be the only option
shopping = get_poi(
    "Hays, KS",
    categories=["shopping"],
    travel_time=20,
    travel_mode="drive",
)
print(f"Shopping/grocery within 20 min: {len(shopping)}")
```

### Example 3: Compare Multiple Rural Towns

Understanding regional patterns requires comparing multiple towns. The `analyze_multiple_pois()` function runs the full isochrone-and-census pipeline for each location in parallel and produces comparative rankings.

This example compares four towns across western Kansas, each serving as a regional hub for surrounding agricultural communities.

```python
from socialmapper import analyze_multiple_pois

plains_towns = [
    "Hays, KS",
    "Dodge City, KS",
    "Garden City, KS",
    "Liberal, KS",
]

comparison = analyze_multiple_pois(
    locations=plains_towns,
    travel_time=20,
    travel_mode="drive",
    variables=["population", "median_income", "poverty"],
)

# Print community-level comparison
print(f"{'Town':<20} {'Population':>12} {'Median Income':>15} {'Block Groups':>14}")
print("-" * 63)
for loc in comparison["locations"]:
    if "error" not in loc:
        pop = loc["aggregated"]["population"]["total"]
        income = loc["aggregated"]["median_income"]["mean"]
        bgs = loc["block_group_count"]
        print(f"{loc['location']:<20} {pop:>12,.0f} {income:>14,.0f}  {bgs:>13}")

# Which town serves the largest community?
if "comparison" in comparison:
    largest = comparison["comparison"]["population"]["highest"]
    print(f"\nLargest 20-min community: {largest}")
```

### Example 4: Map a Rural Community

Visualization brings the analysis to life. This example defines a community around Valentine, Nebraska -- a town of roughly 2,700 in the Sand Hills -- and creates a choropleth map showing population density across the block groups within a 30-minute drive.

```python
from socialmapper import create_isochrone, get_census_blocks, get_census_data, create_map

# Define the community
isochrone = create_isochrone("Valentine, NE", travel_time=30, travel_mode="drive")
blocks = get_census_blocks(polygon=isochrone)
census = get_census_data(isochrone, variables=["population"])

# Merge census data onto block group geometries
merged = []
for block in blocks:
    geoid = block["geoid"]
    if geoid in census.data:
        pop = census.data[geoid].get("population", 0)
        merged.append({**block, "population": pop if pop is not None else 0})

# Create the map
map_result = create_map(
    data=merged,
    column="population",
    title="Valentine, NE -- 30-Minute Drive Community",
    overlay_boundary=isochrone,
    show_stats=True,
    save_path="valentine_community.png",
)
print(f"Map saved to: {map_result.file_path}")
```

### Example 5: Identify Healthcare Deserts

One of the most impactful applications is identifying areas where rural residents lack access to critical services. This example checks whether communities around several small towns can reach a healthcare facility within 30 minutes.

```python
from socialmapper import get_poi, create_isochrone, get_census_data

# Small towns in the Nebraska Sand Hills and western Plains
remote_towns = [
    "Valentine, NE",
    "Chadron, NE",
    "Alliance, NE",
    "Ogallala, NE",
]

print(f"{'Town':<20} {'Healthcare POIs':>16} {'30-min Pop':>12}")
print("-" * 50)

for town in remote_towns:
    # How many healthcare facilities within 30 minutes?
    healthcare = get_poi(
        town,
        categories=["healthcare"],
        travel_time=30,
        travel_mode="drive",
    )

    # How many people live within 30 minutes?
    iso = create_isochrone(town, travel_time=30, travel_mode="drive")
    census = get_census_data(iso, variables=["population"])
    total_pop = sum(
        d.get("population", 0)
        for d in census.data.values()
        if d.get("population") is not None
    )

    print(f"{town:<20} {len(healthcare):>16} {total_pop:>12,}")
```

### Example 6: Walk vs. Drive Equity Analysis

In rural towns, the difference between walking and driving access reveals stark equity gaps. Residents without vehicles -- the elderly, the disabled, low-income households -- experience a fundamentally different community than those with cars.

```python
from socialmapper import create_isochrone, get_census_data

town = "Staunton, VA"

# 15-minute drive community
drive_iso = create_isochrone(town, travel_time=15, travel_mode="drive")
drive_census = get_census_data(drive_iso, variables=["population", "poverty"])
drive_pop = sum(
    d.get("population", 0)
    for d in drive_census.data.values()
    if d.get("population") is not None
)

# 15-minute walk community
walk_iso = create_isochrone(town, travel_time=15, travel_mode="walk")
walk_census = get_census_data(walk_iso, variables=["population", "poverty"])
walk_pop = sum(
    d.get("population", 0)
    for d in walk_census.data.values()
    if d.get("population") is not None
)

print(f"15-min drive community: {drive_pop:,} people")
print(f"15-min walk community:  {walk_pop:,} people")
print(f"Access ratio:           {walk_pop / drive_pop:.1%} of drive community")
print(f"\nResidents without cars experience a community")
print(f"  {drive_pop / max(walk_pop, 1):.0f}x smaller than drivers.")
```

## Why This Matters

Rural communities are systematically misrepresented in data analysis. County-level aggregation is the default, and it masks the patterns that matter most for policy and planning. A county poverty rate averages together people oriented toward different towns with different economic realities. A county healthcare statistic counts a hospital as "available" even when half the county's residents live an hour away.

Travel-time boundaries offer a corrective. They respect the actual terrain, road network, and geography that shape daily life. They produce community definitions that correspond to how people experience their world -- where they shop, where their children go to school, where they seek medical care, where they worship.

SocialMapper makes this kind of analysis accessible to practitioners who are not GIS specialists. A rural planner, a community development organization, a USDA analyst, or a policy researcher can define a travel-time community, pull its demographics, inventory its services, and map the results in a few lines of Python. No ArcGIS license, no custom routing infrastructure, no stitching together five different libraries.

When a rural grocery store closes, the community affected is not a county. It is the set of people within a 20-minute drive who depended on it. When a rural hospital shuts down, the impact radiates along road networks, not along county lines. When a school consolidation is proposed, the families affected are defined by bus routes and drive times, not by which side of a county boundary they happen to live on.

SocialMapper makes these communities visible.

## Related Resources

- **Tutorial notebooks**: The [tutorial series](notebooks/) uses small towns as examples -- Bozeman, MT; Boone, NC; Staunton, VA; Charlottesville, VA -- demonstrating these techniques at scale.
- **Census variables reference**: See [census-variables.md](reference/census-variables.md) for the full list of demographic variables available for community profiling.
- **API reference**: See [api-reference.md](api-reference.md) for complete function signatures and parameters.
- **POI categories**: SocialMapper supports 10 POI category groups (`healthcare`, `education`, `shopping`, `food_and_drink`, `services`, `recreation`, `transportation`, `accommodation`, `religious`, `utilities`) covering 338+ individual OpenStreetMap feature types.
