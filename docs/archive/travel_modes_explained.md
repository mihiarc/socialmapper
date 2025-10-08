# Travel Modes in SocialMapper

This document explains how SocialMapper handles different travel modes (walking, biking, driving) when generating isochrones and calculating accessibility.

## Overview

SocialMapper uses OpenStreetMap (OSM) data via OSMnx to create network graphs for each travel mode. Each mode has different characteristics that affect the size and shape of isochrones.

## Travel Mode Characteristics

### 🚶 Walking Mode

**Network Type**: `walk`  
**Default Speed**: 5 km/h (3.1 mph)  
**Speed Range**: 3-7 km/h

**What's Included:**
- Sidewalks and footways
- Pedestrian paths and zones
- Residential streets (assumed walkable)
- Shared pedestrian/bicycle paths
- Steps and stairs
- Pedestrian crossings
- Parks and public spaces with paths
- Most roads where pedestrian access isn't explicitly forbidden

**What's Excluded:**
- Motorways/highways
- Roads tagged with `foot=no`
- Private roads without pedestrian access

**Key Behaviors:**
- All edges are bidirectional (ignores one-way restrictions)
- Includes roads without sidewalks if pedestrian access is legal
- Speed varies by path type (stairs: 1.5 km/h, paths: 4.5 km/h, sidewalks: 5 km/h)

### 🚴 Biking Mode

**Network Type**: `bike`  
**Default Speed**: 15 km/h (9.3 mph)  
**Speed Range**: 8-30 km/h

**What's Included:**
- Dedicated bike lanes and cycleways
- Roads where cycling is permitted
- Shared pedestrian/bicycle paths
- Most streets (unless cycling is forbidden)
- Some footpaths where cycling is allowed

**What's Excluded:**
- Motorways/highways
- Footways where cycling is forbidden
- Roads tagged with `bicycle=no`
- Stairs (unlike walking mode)

**Key Behaviors:**
- Respects one-way streets but may include contraflow bike lanes
- Speeds vary by infrastructure (bike lanes: 18 km/h, shared paths: 12 km/h)
- Generally 3x faster than walking

### 🚗 Driving Mode

**Network Type**: `drive`  
**Default Speed**: 50 km/h (31 mph) in urban areas  
**Speed Range**: 20-130 km/h

**What's Included:**
- All roads accessible to cars
- Service roads and parking aisles
- Highway ramps and connectors

**What's Excluded:**
- Pedestrian-only streets
- Bike paths
- Footways
- Roads tagged with `motor_vehicle=no`

**Key Behaviors:**
- Strictly follows one-way restrictions
- Uses actual speed limits from OSM when available
- Falls back to road-type-based speeds (residential: 30 km/h, primary: 65 km/h, motorway: 110 km/h)
- Accounts for road hierarchy in routing

## Speed Assignment Hierarchy

SocialMapper uses OSMnx's sophisticated speed assignment system:

1. **OSM Speed Limits**: Uses actual `maxspeed` tags when available
2. **Road Type Defaults**: Falls back to speeds based on highway classification
3. **Statistical Imputation**: For unmapped types, uses mean speed of similar roads
4. **Mode Default**: Final fallback to the travel mode's default speed

### Example Speed Assignments

**Walking on Different Surfaces:**
- Footway/sidewalk: 5.0 km/h
- Stairs: 1.5 km/h
- Rough paths: 4.5 km/h
- Residential streets: 4.8 km/h

**Biking on Different Infrastructure:**
- Dedicated cycleway: 18.0 km/h
- Shared with pedestrians: 8.0 km/h
- Residential streets: 15.0 km/h
- Primary roads: 20.0 km/h

**Driving on Different Roads:**
- Residential: 30 km/h
- Secondary roads: 55 km/h
- Primary roads: 65 km/h
- Highways: 110 km/h

## Understanding Isochrone Differences

### Why Walking Isochrones May Seem Large

- Includes all legally walkable routes, not just those with sidewalks
- Rural roads without sidewalks are included if walking is permitted
- Assumes constant speed without fatigue or comfort considerations

### Why Driving Isochrones Consider More Factors

- Respects one-way streets and turn restrictions
- Varies speed significantly based on road type
- Excludes pedestrian infrastructure

### Realistic Travel Time Estimates

**15-minute travel distances (approximate):**
- Walking: 1.0-1.5 km radius
- Biking: 3.0-4.5 km radius  
- Driving: 7.5-15 km radius (varies greatly with traffic and road types)

## Data Quality Considerations

### What Affects Accuracy

1. **OSM Completeness**: Some areas have better mapping than others
2. **Speed Limit Data**: Not all roads have maxspeed tags
3. **Path Networks**: Footpaths and bike lanes may be undermapped
4. **Access Restrictions**: Not all private roads are properly tagged

### Limitations

- No traffic consideration for driving times
- No elevation/hill effects on walking/biking speeds
- No weather or seasonal variations
- Intersection delays not modeled
- Assumes direct routing without stops

## Best Practices for Analysis

1. **Urban vs Rural**: Expect larger walking isochrones in rural areas due to road walking
2. **Data Validation**: Check OSM data quality in your area of interest
3. **Multiple Modes**: Compare modes to understand transportation equity
4. **Local Knowledge**: Adjust expectations based on local infrastructure

## Technical Implementation

SocialMapper enforces realistic speeds by:
- Capping walking speeds at 7 km/h maximum
- Capping biking speeds at 30 km/h maximum
- Using mode-specific highway speed tables
- Recalculating travel times after speed adjustments

This ensures that even if OSM data has unrealistic speeds, the isochrones remain reasonable for each travel mode.