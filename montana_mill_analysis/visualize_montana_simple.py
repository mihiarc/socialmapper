#!/usr/bin/env python3
"""
Simple visualization of Montana timber mill analysis results.
This version directly loads the known file paths.
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np

# File paths
files = {
    30: {
        'census': 'output/census_data/custom_montana_mill_location_30min_drive_census_data_data.csv',
        'isochrone': 'output/isochrones/custom_montana_mill_location_30min_drive_isochrones.geoparquet'
    },
    120: {
        'census': 'output/timber_mill_2hour_analysis/census_data/custom_montana_mill_location_120min_drive_census_data_data.csv',
        'isochrone': 'output/timber_mill_2hour_analysis/isochrones/custom_montana_mill_location_120min_drive_isochrones.geoparquet'
    }
}

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

# Mill location (same for both)
mill_lat = 47.167012
mill_lon = -113.466881

for ax, travel_time in zip([ax1, ax2], [30, 120]):
    # Load data
    census_df = pd.read_csv(files[travel_time]['census'])
    iso_gdf = gpd.read_parquet(files[travel_time]['isochrone'])
    
    # Project to Montana State Plane
    iso_gdf = iso_gdf.to_crs('EPSG:32100')
    
    # Create mill point
    mill_gdf = gpd.GeoDataFrame(
        [{'name': 'Mill'}], 
        geometry=gpd.points_from_xy([mill_lon], [mill_lat]),
        crs='EPSG:4326'
    ).to_crs('EPSG:32100')
    
    # Plot isochrone
    iso_gdf.plot(ax=ax, color='lightblue', edgecolor='darkblue', 
                 linewidth=2, alpha=0.6)
    
    # Plot mill location
    mill_gdf.plot(ax=ax, color='red', markersize=200, marker='*', 
                  edgecolor='black', linewidth=1, zorder=5)
    
    # Add title and stats
    total_pop = census_df['B01003_001E'].sum()
    area_km2 = iso_gdf.to_crs('EPSG:5070').area.sum() / 1_000_000
    
    ax.set_title(f'{travel_time}-Minute Drive Radius\n'
                 f'Population: {total_pop:,}\n'
                 f'Area: {area_km2:,.0f} km²', 
                 fontsize=14, fontweight='bold')
    
    # Remove axes labels for cleaner look
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Add scale bar
    # Get bounds
    bounds = ax.get_xlim(), ax.get_ylim()
    width = bounds[0][1] - bounds[0][0]
    
    # Add a simple scale reference
    if travel_time == 30:
        scale_length = 20000  # 20 km in meters
        scale_label = "20 km"
    else:
        scale_length = 100000  # 100 km in meters  
        scale_label = "100 km"
    
    scale_x = bounds[0][0] + width * 0.1
    scale_y = bounds[1][0] + (bounds[1][1] - bounds[1][0]) * 0.1
    
    ax.plot([scale_x, scale_x + scale_length], [scale_y, scale_y], 
            'k-', linewidth=3)
    ax.text(scale_x + scale_length/2, scale_y + scale_length*0.02, 
            scale_label, ha='center', fontsize=10)

# Main title
fig.suptitle('Montana Timber Mill Workforce Analysis Comparison', 
             fontsize=16, fontweight='bold')

# Add summary text
summary = (f"The 2-hour analysis captures {103}x more population than the 30-minute radius.\n"
           f"Major cities within 2 hours: Missoula (80 mi), Butte (60 mi), Helena (90 mi)")
fig.text(0.5, 0.02, summary, ha='center', fontsize=12, style='italic')

plt.tight_layout()
plt.subplots_adjust(top=0.88, bottom=0.1)

# Save and show
output_file = 'montana_mill_comparison.png'
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"Saved visualization to {output_file}")

# Also create a detailed population map for the 30-minute radius
fig2, ax = plt.subplots(1, 1, figsize=(10, 10))

# Load 30-min data again
census_df = pd.read_csv(files[30]['census'])
iso_gdf = gpd.read_parquet(files[30]['isochrone'])

# Create GeoDataFrame from census centroids
from shapely import wkt
census_df['geometry'] = census_df['centroid'].apply(wkt.loads)
census_gdf = gpd.GeoDataFrame(census_df, geometry='geometry', crs='EPSG:4326')
census_gdf = census_gdf.to_crs('EPSG:32100')

# Project isochrone
iso_gdf = iso_gdf.to_crs('EPSG:32100')

# Plot
iso_gdf.plot(ax=ax, color='none', edgecolor='darkblue', linewidth=2)

# Plot census points sized by population
sizes = census_df['B01003_001E'] / 5  # Scale for visibility
census_gdf.plot(ax=ax, markersize=sizes, color='orange', alpha=0.7, 
                edgecolor='black', linewidth=0.5)

# Add labels for each census unit
for idx, row in census_gdf.iterrows():
    ax.text(row.geometry.x, row.geometry.y, 
            f"{int(row['B01003_001E'])}", 
            fontsize=9, ha='center', va='center')

# Mill location
mill_gdf = gpd.GeoDataFrame(
    [{'name': 'Mill'}], 
    geometry=gpd.points_from_xy([mill_lon], [mill_lat]),
    crs='EPSG:4326'
).to_crs('EPSG:32100')
mill_gdf.plot(ax=ax, color='red', markersize=300, marker='*', 
              edgecolor='black', linewidth=2, zorder=5)

ax.set_title('30-Minute Workforce Detail\nPopulation by Census Block Group', 
             fontsize=14, fontweight='bold')
ax.set_xlabel('Montana State Plane (meters)')
ax.set_ylabel('Montana State Plane (meters)')

plt.tight_layout()
plt.savefig('montana_mill_30min_detail.png', dpi=150, bbox_inches='tight')
print(f"Saved detailed map to montana_mill_30min_detail.png")

plt.show()