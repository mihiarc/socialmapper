# SocialMapper Tutorial Exercises

A comprehensive collection of hands-on exercises from all SocialMapper tutorials. Complete these exercises to master accessibility analysis and urban planning techniques.

## 📚 Exercise Difficulty Levels

- **Beginner** (⭐): 5-15 minutes, basic concepts
- **Intermediate** (⭐⭐): 15-25 minutes, combining concepts
- **Advanced** (⭐⭐⭐): 25-45 minutes, complex analysis
- **Expert** (⭐⭐⭐⭐): 45+ minutes, research-level

## 📋 Exercise Categories

1. [Basic Operations](#basic-operations)
2. [Travel Mode Analysis](#travel-mode-analysis)
3. [Demographic Analysis](#demographic-analysis)
4. [Equity Assessment](#equity-assessment)
5. [Food Security](#food-security)
6. [Challenge Problems](#challenge-problems)

---

## Basic Operations

### Exercise 1.1: Modify Location ⭐
**Tutorial**: 01 - Getting Started
**Time**: 5 minutes
**Objective**: Practice changing analysis location

**Task**: Change the location to your hometown or a city you're interested in.

<details>
<summary>💡 Hint</summary>
Use Google Maps to find coordinates (right-click → "What's here?")
</details>

<details>
<summary>✅ Solution</summary>

```python
# Example: New York City
location = (40.7128, -74.0060)

# Example: San Francisco
location = (37.7749, -122.4194)

# Example: Chicago
location = (41.8781, -87.6298)
```
</details>

---

### Exercise 1.2: Compare Travel Times ⭐
**Tutorial**: 01 - Getting Started
**Time**: 10 minutes
**Objective**: Understand how area scales with travel time

**Task**: Create isochrones for 5, 10, 15, and 20 minutes. How does area scale?

<details>
<summary>💡 Hint</summary>
Use a loop to iterate over travel_time values
</details>

<details>
<summary>✅ Solution</summary>

```python
for minutes in [5, 10, 15, 20]:
    iso = create_isochrone(location, minutes, "drive")
    area = iso['properties']['area_sq_km']
    print(f"{minutes} min: {area:.2f} km²")

# Expected: Area increases roughly quadratically with time
```
</details>

---

### Exercise 1.3: Multi-POI Search ⭐⭐
**Tutorial**: 01 - Getting Started
**Time**: 10 minutes
**Objective**: Compare accessibility to different services

**Task**: Find hospitals, schools, AND parks. Which is most accessible?

<details>
<summary>💡 Hint</summary>
Loop through different category lists
</details>

<details>
<summary>✅ Solution</summary>

```python
poi_types = ["hospital", "school", "park"]
for poi_type in poi_types:
    pois = get_poi(location, [poi_type], 15, limit=20)
    print(f"{poi_type}: {len(pois)} found")
    if pois:
        avg_dist = sum(p['distance_km'] for p in pois) / len(pois)
        print(f"  Average distance: {avg_dist:.2f} km")
```
</details>

---

## Travel Mode Analysis

### Exercise 2.1: Rush Hour Analysis ⭐
**Tutorial**: 02 - Travel Modes
**Time**: 10 minutes
**Objective**: Understand congestion effects

**Task**: Compare travel times during peak vs off-peak hours.

<details>
<summary>💡 Hint</summary>
Some routing APIs support time-of-day parameters
</details>

<details>
<summary>✅ Solution</summary>

```python
# Conceptual - implementation depends on API
peak_iso = create_isochrone(location, 15, "drive")  # peak hours
peak_area = peak_iso['properties']['area_sq_km']

offpeak_iso = create_isochrone(location, 15, "drive")  # off-peak
offpeak_area = offpeak_iso['properties']['area_sq_km']

reduction = (1 - peak_area/offpeak_area) * 100
print(f"Peak hour reduces coverage by {reduction:.0f}%")
```
</details>

---

### Exercise 2.2: Equity Score Calculation ⭐⭐
**Tutorial**: 02 - Travel Modes
**Time**: 15 minutes
**Objective**: Measure transportation equity

**Task**: Calculate an "equity score" based on walk vs drive accessibility.

<details>
<summary>💡 Hint</summary>
Score = (POIs reachable by walk) / (POIs reachable by drive)
</details>

<details>
<summary>✅ Solution</summary>

```python
walk_pois = get_poi(location, ["grocery", "pharmacy"], 15, "walk")
drive_pois = get_poi(location, ["grocery", "pharmacy"], 15, "drive")
equity_score = len(walk_pois) / max(len(drive_pois), 1)

print(f"Equity Score: {equity_score:.2f}")
if equity_score > 0.5:
    print("High equity: Good walkable access")
elif equity_score > 0.2:
    print("Moderate equity: Some walkable access")
else:
    print("Low equity: Car-dependent area")
```
</details>

---

### Exercise 2.3: Multi-Modal Journey ⭐⭐
**Tutorial**: 02 - Travel Modes
**Time**: 15 minutes
**Objective**: Model complex travel patterns

**Task**: Simulate park-and-ride: 10 min drive + 5 min walk.

<details>
<summary>💡 Hint</summary>
Create two isochrones and consider the combined coverage
</details>

<details>
<summary>✅ Solution</summary>

```python
# First leg: 10 min drive from origin
drive_iso = create_isochrone(location, 10, "drive")

# Transfer point (simplified - use actual park-and-ride location)
transfer_point = (location[0] + 0.05, location[1])

# Second leg: 5 min walk from transfer
walk_iso = create_isochrone(transfer_point, 5, "walk")

print("Multi-modal coverage combines both isochrones")
print("Often provides better downtown access than driving alone")
```
</details>

---

## Demographic Analysis

### Exercise 3.1: Calculate Equity Metrics ⭐⭐
**Tutorial**: 01 - Getting Started
**Time**: 15 minutes
**Objective**: Analyze service access by income

**Task**: What percentage of low-income residents can reach a library in 15 minutes?

<details>
<summary>💡 Hint</summary>
Filter census_data where median_income < 40000
</details>

<details>
<summary>✅ Solution</summary>

```python
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
```
</details>

---

## Equity Assessment

### Exercise 4.1: Temporal Equity ⭐
**Tutorial**: 09 - Equity Analysis
**Time**: 15 minutes
**Objective**: Analyze time-based service equity

**Task**: Compare library access during working hours vs evenings.

<details>
<summary>💡 Hint</summary>
Consider library operating hours in your analysis
</details>

<details>
<summary>✅ Solution</summary>

```python
working_hours_access = 0
evening_access = 0

for library in libraries:
    # In practice, fetch actual hours from API
    if "open_evenings" in library.get('tags', []):
        evening_access += 1
    if "open_weekdays" in library.get('tags', []):
        working_hours_access += 1

evening_ratio = evening_access / len(libraries) if libraries else 0
print(f"Libraries with evening hours: {evening_ratio:.0%}")
```
</details>

---

### Exercise 4.2: Multi-Service Equity ⭐⭐
**Tutorial**: 09 - Equity Analysis
**Time**: 20 minutes
**Objective**: Compare equity across service types

**Task**: Compare equity for libraries, healthcare, and grocery stores.

<details>
<summary>💡 Hint</summary>
Run equity analysis for each service category
</details>

<details>
<summary>✅ Solution</summary>

```python
services = ["library", "hospital", "grocery"]
equity_scores = {}

for service in services:
    pois = get_poi(location, [service], 15, "walk")

    # Calculate disparity ratio for each service
    # (simplified - would need full demographic analysis)
    low_income_access = len([p for p in pois if p['distance_km'] < 1])
    total_access = len(pois)

    equity_scores[service] = low_income_access / max(total_access, 1)

worst_service = min(equity_scores, key=lambda x: equity_scores[x])
print(f"Service with worst equity: {worst_service}")
print(f"Equity scores: {equity_scores}")
```
</details>

---

### Exercise 4.3: Intersectional Analysis ⭐⭐⭐
**Tutorial**: 09 - Equity Analysis
**Time**: 30 minutes
**Objective**: Analyze compounded disadvantages

**Task**: Analyze how race and income interact to affect access.

<details>
<summary>💡 Hint</summary>
Create a 2x2 matrix of income × race categories
</details>

<details>
<summary>✅ Solution</summary>

```python
# Get additional demographic variables
census_data = get_census_data(
    location=geoids,
    variables=["population", "median_income", "percent_minority"],
    year=2022
)

# Create intersection groups
groups = {
    'low_income_minority': [],
    'low_income_majority': [],
    'high_income_minority': [],
    'high_income_majority': []
}

for geoid, data in census_data.items():
    income = data.get('median_income', 0)
    minority_pct = data.get('percent_minority', 0)

    is_low_income = income < 40000
    is_high_minority = minority_pct > 50

    if is_low_income and is_high_minority:
        groups['low_income_minority'].append(data)
    elif is_low_income:
        groups['low_income_majority'].append(data)
    elif is_high_minority:
        groups['high_income_minority'].append(data)
    else:
        groups['high_income_majority'].append(data)

# Analyze each group
for group_name, group_data in groups.items():
    if group_data:
        avg_pop = sum(d['population'] for d in group_data) / len(group_data)
        print(f"{group_name}: {len(group_data)} blocks, avg pop {avg_pop:.0f}")
```
</details>

---

## Food Security

### Exercise 5.1: Food Quality Assessment ⭐
**Tutorial**: 10 - Food Desert Analysis
**Time**: 15 minutes
**Objective**: Evaluate food retail quality

**Task**: Calculate a "food quality index" for the area.

<details>
<summary>💡 Hint</summary>
Weight grocery stores positively, fast food negatively
</details>

<details>
<summary>✅ Solution</summary>

```python
# Count different food retailer types
grocery_stores = len([p for p in pois if 'grocery' in p.get('name', '').lower()])
farmers_markets = len([p for p in pois if 'farmers' in p.get('name', '').lower()])
convenience_stores = len([p for p in pois if 'convenience' in p.get('name', '').lower()])
fast_food = len([p for p in pois if 'fast' in p.get('name', '').lower()])

# Calculate quality index
healthy_points = grocery_stores * 10 + farmers_markets * 5
unhealthy_points = convenience_stores * -5 + fast_food * -3
quality_index = max(0, min(100, 50 + healthy_points + unhealthy_points))

print(f"Food Quality Index: {quality_index}/100")
if quality_index > 70:
    print("Good food environment")
elif quality_index > 40:
    print("Moderate food environment")
else:
    print("Poor food environment - potential food swamp")
```
</details>

---

### Exercise 5.2: Intervention Modeling ⭐⭐⭐
**Tutorial**: 10 - Food Desert Analysis
**Time**: 30 minutes
**Objective**: Model policy interventions

**Task**: Model the impact of adding a new grocery store in the most underserved area.

<details>
<summary>💡 Hint</summary>
Place new store at centroid of largest food desert
</details>

<details>
<summary>✅ Solution</summary>

```python
# Find most underserved area
if food_deserts:
    # Get block with lowest income and no grocery access
    most_underserved = min(
        food_deserts,
        key=lambda g: census_data[g].get('median_income', float('inf'))
    )

    # Hypothetical new store location
    # In practice, calculate actual centroid
    new_store_lat = location[0] + 0.01
    new_store_lon = location[1] + 0.01

    # Count population that would benefit
    benefited_pop = 0
    for geoid in food_deserts:
        # Simple distance check (would use actual distance calculation)
        if geoid == most_underserved:
            benefited_pop += census_data[geoid].get('population', 0)

    print(f"New grocery store would serve {benefited_pop:,} people")
    print(f"Reduction in food desert population: {benefited_pop/total_pop*100:.1f}%")
```
</details>

---

## Challenge Problems

### Challenge 1: Accessibility Report ⭐⭐⭐
**Tutorial**: 01 - Getting Started
**Time**: 30 minutes
**Objective**: Create professional report

**Task**: Generate a text report summarizing accessibility for decision makers.

**Requirements**:
- Population served
- Average distance to services
- Equity gaps identified
- Recommendations

<details>
<summary>✅ Solution Framework</summary>

```python
def generate_accessibility_report(location_name, census_data, pois, travel_time):
    """Generate a comprehensive accessibility report."""

    report = []
    report.append("=" * 60)
    report.append(f"ACCESSIBILITY REPORT: {location_name}")
    report.append("=" * 60)

    # Executive Summary
    total_pop = sum(d.get('population', 0) for d in census_data.values())
    avg_income = statistics.mean([d.get('median_income', 0) for d in census_data.values() if d.get('median_income', 0) > 0])

    report.append("\nEXECUTIVE SUMMARY")
    report.append(f"Population Served: {total_pop:,}")
    report.append(f"Service Points: {len(pois)}")
    report.append(f"Average Income: ${avg_income:,.0f}")

    # Service Access
    report.append("\nSERVICE ACCESSIBILITY")
    if pois:
        avg_dist = statistics.mean([p['distance_km'] for p in pois])
        report.append(f"Average Distance: {avg_dist:.2f} km")
        report.append(f"Services per 10,000: {len(pois)/total_pop*10000:.1f}")

    # Equity Analysis
    report.append("\nEQUITY ASSESSMENT")
    low_income_pop = sum(d.get('population', 0) for d in census_data.values()
                         if 0 < d.get('median_income', 0) < 35000)
    report.append(f"Low-Income Population: {low_income_pop:,} ({low_income_pop/total_pop*100:.1f}%)")

    # Recommendations
    report.append("\nRECOMMENDATIONS")
    if len(pois) / total_pop * 10000 < 1:
        report.append("- Increase service density")
    if low_income_pop / total_pop > 0.3:
        report.append("- Focus on low-income area improvements")

    return "\n".join(report)

# Generate and save report
report = generate_accessibility_report(location_name, census_data, pois, travel_time)
print(report)

with open("accessibility_report.txt", "w") as f:
    f.write(report)
```
</details>

---

### Challenge 2: Modal Analysis ⭐⭐⭐
**Tutorial**: 02 - Travel Modes
**Time**: 45 minutes
**Objective**: Complete modal comparison

**Task**: Create a comprehensive report comparing all three modes across multiple dimensions.

**Requirements**:
- Coverage area and population
- Service accessibility by category
- Demographics of covered areas
- Equity implications

---

### Challenge 3: Longitudinal Equity Study ⭐⭐⭐⭐
**Tutorial**: 09 - Equity Analysis
**Time**: 60 minutes
**Objective**: Track equity changes over time

**Task**: Analyze how equity has changed using historical census data.

**Requirements**:
- Compare 2010, 2015, 2020 data
- Track gentrification patterns
- Identify trends
- Project future equity

---

### Challenge 4: Food System Analysis ⭐⭐⭐⭐
**Tutorial**: 10 - Food Desert Analysis
**Time**: 60 minutes
**Objective**: Complete food system assessment

**Task**: Create a comprehensive food system analysis.

**Requirements**:
- Production (urban farms)
- Distribution (stores, markets)
- Consumption (restaurants)
- Waste (composting)
- Climate resilience

---

## 📈 Progress Tracking

Track your progress through the exercises:

- [ ] Complete all Beginner exercises (⭐)
- [ ] Complete 50% of Intermediate exercises (⭐⭐)
- [ ] Complete at least 2 Advanced exercises (⭐⭐⭐)
- [ ] Complete 1 Challenge problem (⭐⭐⭐⭐)

## 🎯 Learning Objectives Checklist

After completing these exercises, you should be able to:

- [ ] Create and analyze isochrones for any location
- [ ] Compare accessibility across different travel modes
- [ ] Perform demographic analysis using census data
- [ ] Calculate equity metrics and identify disparities
- [ ] Analyze food security and identify food deserts
- [ ] Generate data-driven policy recommendations
- [ ] Create visualizations to communicate findings
- [ ] Build reproducible analysis workflows

## 💡 Tips for Success

1. **Start Simple**: Begin with beginner exercises even if you're experienced
2. **Run the Code**: Don't just read solutions - run and modify them
3. **Experiment**: Try different parameters and locations
4. **Document**: Keep notes on what you learn from each exercise
5. **Share**: Discuss solutions with others learning SocialMapper

## 🚀 Next Steps

Once you've completed these exercises:

1. **Apply to Your City**: Run analyses on your local area
2. **Extend the Analysis**: Add new metrics or data sources
3. **Build Applications**: Create web apps or dashboards
4. **Contribute**: Share your analyses and improvements

---

*Happy analyzing! For questions and discussions, visit the SocialMapper community forums.*