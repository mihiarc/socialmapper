#!/usr/bin/env python3
"""
Visualize Montana timber mill analysis with basemaps and consistent scale.
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import numpy as np
from matplotlib.patches import Circle
# from matplotlib_scalebar.scalebar import ScaleBar

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

# Create figure with two subplots at same scale
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 9))

# Mill location
mill_lat = 47.167012
mill_lon = -113.466881

# Load 120-minute data first to get overall bounds
iso_120 = gpd.read_parquet(files[120]['isochrone'])
iso_120 = iso_120.to_crs('EPSG:3857')  # Web Mercator for basemap
bounds_120 = iso_120.total_bounds

# Add larger buffer to bounds for full study area context
buffer = 0.5  # 50% buffer to show more surrounding area
x_range = bounds_120[2] - bounds_120[0]
y_range = bounds_120[3] - bounds_120[1]
xlim = (bounds_120[0] - x_range * buffer, bounds_120[2] + x_range * buffer)
ylim = (bounds_120[1] - y_range * buffer, bounds_120[3] + y_range * buffer)

for ax, travel_time in zip([ax1, ax2], [30, 120]):
    # Load data
    census_df = pd.read_csv(files[travel_time]['census'])
    iso_gdf = gpd.read_parquet(files[travel_time]['isochrone'])
    
    # Project to Web Mercator for basemap compatibility
    iso_gdf = iso_gdf.to_crs('EPSG:3857')
    
    # Create mill point
    mill_gdf = gpd.GeoDataFrame(
        [{'name': 'Mill'}], 
        geometry=gpd.points_from_xy([mill_lon], [mill_lat]),
        crs='EPSG:4326'
    ).to_crs('EPSG:3857')
    
    # Plot isochrone with transparency
    iso_gdf.plot(ax=ax, color='none', edgecolor='red', 
                 linewidth=3, alpha=0.9, linestyle='-')
    iso_gdf.plot(ax=ax, color='red', alpha=0.2)
    
    # Add basemap - using OpenStreetMap Mapnik
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom='auto')
    
    # Plot mill location
    mill_gdf.plot(ax=ax, color='yellow', markersize=300, marker='*', 
                  edgecolor='black', linewidth=2, zorder=10)
    
    # Set consistent bounds for both maps
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    
    # Add title and stats
    total_pop = census_df['B01003_001E'].sum()
    area_km2 = iso_gdf.to_crs('EPSG:5070').area.sum() / 1_000_000
    
    ax.set_title(f'{travel_time}-Minute Drive Radius\n'
                 f'Population: {total_pop:,}\n'
                 f'Area: {area_km2:,.0f} km²', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # Remove axis labels
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Add simple scale bar
    # Calculate scale based on current extent
    scale_length = 50000 if travel_time == 30 else 200000  # 50km or 200km
    scale_label = "50 km" if travel_time == 30 else "200 km"
    
    # Position at bottom right
    scale_x = xlim[1] - (xlim[1] - xlim[0]) * 0.3
    scale_y = ylim[0] + (ylim[1] - ylim[0]) * 0.05
    
    ax.plot([scale_x, scale_x + scale_length], [scale_y, scale_y], 
            'k-', linewidth=4, solid_capstyle='butt')
    ax.text(scale_x + scale_length/2, scale_y + scale_length*0.02, 
            scale_label, ha='center', va='bottom', fontsize=10,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # Add city labels for context
    cities = [
        ('Philipsburg', 46.3321, -113.2948),
        ('Missoula', 46.8721, -113.9940),
        ('Butte', 46.0038, -112.5348),
        ('Helena', 46.5891, -112.0391),
        ('Anaconda', 46.1285, -112.9420)
    ]
    
    # Only show cities within current view
    for city_name, lat, lon in cities:
        city_point = gpd.GeoDataFrame(
            [{'name': city_name}],
            geometry=gpd.points_from_xy([lon], [lat]),
            crs='EPSG:4326'
        ).to_crs('EPSG:3857')
        
        x, y = city_point.geometry.x[0], city_point.geometry.y[0]
        if xlim[0] <= x <= xlim[1] and ylim[0] <= y <= ylim[1]:
            ax.plot(x, y, 'ko', markersize=6)
            ax.text(x, y+5000, city_name, ha='center', va='bottom', 
                   fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

# Main title
fig.suptitle('Montana Timber Mill Workforce Analysis - Geographic Context', 
             fontsize=18, fontweight='bold')

# Add summary text
summary = (f"Both maps shown at same scale. The 2-hour radius captures 103x more population.\n"
           f"Yellow star = Mill location | Red boundary = Drive time radius")
fig.text(0.5, 0.02, summary, ha='center', fontsize=12)

plt.tight_layout()
plt.subplots_adjust(top=0.92, bottom=0.08)

# Save
output_file = 'montana_mill_comparison_basemap.png'
plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
print(f"Saved visualization to {output_file}")

# Create a zoomed-in view of just the 30-minute area
fig2, ax = plt.subplots(1, 1, figsize=(12, 12))

# Load 30-minute data
census_df = pd.read_csv(files[30]['census'])
iso_gdf = gpd.read_parquet(files[30]['isochrone'])
iso_gdf = iso_gdf.to_crs('EPSG:3857')

# Get bounds for 30-minute area
bounds_30 = iso_gdf.total_bounds
x_range_30 = bounds_30[2] - bounds_30[0]
y_range_30 = bounds_30[3] - bounds_30[1]
xlim_30 = (bounds_30[0] - x_range_30 * 0.2, bounds_30[2] + x_range_30 * 0.2)
ylim_30 = (bounds_30[1] - y_range_30 * 0.2, bounds_30[3] + y_range_30 * 0.2)

# Plot
iso_gdf.plot(ax=ax, color='none', edgecolor='red', linewidth=3, alpha=0.9)
iso_gdf.plot(ax=ax, color='red', alpha=0.2)

# Add detailed basemap
ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom='auto')

# Mill location
mill_gdf = gpd.GeoDataFrame(
    [{'name': 'Mill'}], 
    geometry=gpd.points_from_xy([mill_lon], [mill_lat]),
    crs='EPSG:4326'
).to_crs('EPSG:3857')
mill_gdf.plot(ax=ax, color='yellow', markersize=400, marker='*', 
              edgecolor='black', linewidth=2, zorder=10)

# Census centroids with population
from shapely import wkt
census_df['geometry'] = census_df['centroid'].apply(wkt.loads)
census_gdf = gpd.GeoDataFrame(census_df, geometry='geometry', crs='EPSG:4326')
census_gdf = census_gdf.to_crs('EPSG:3857')

# Plot census points sized by population
sizes = np.sqrt(census_df['B01003_001E']) * 10
census_gdf.plot(ax=ax, markersize=sizes, color='blue', alpha=0.6, 
                edgecolor='white', linewidth=1, zorder=5)

# Add population labels
for idx, row in census_gdf.iterrows():
    ax.text(row.geometry.x, row.geometry.y, 
            f"{int(row['B01003_001E'])}", 
            fontsize=10, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

ax.set_xlim(xlim_30)
ax.set_ylim(ylim_30)
ax.set_title('30-Minute Drive Radius - Detailed View\n'
             'Blue circles sized by population', 
             fontsize=16, fontweight='bold', pad=20)
ax.set_xticks([])
ax.set_yticks([])

# Add simple scale bar for detailed view
scale_length = 10000  # 10km
scale_x = xlim_30[1] - (xlim_30[1] - xlim_30[0]) * 0.3
scale_y = ylim_30[0] + (ylim_30[1] - ylim_30[0]) * 0.05

ax.plot([scale_x, scale_x + scale_length], [scale_y, scale_y], 
        'k-', linewidth=4, solid_capstyle='butt')
ax.text(scale_x + scale_length/2, scale_y + scale_length*0.02, 
        '10 km', ha='center', va='bottom', fontsize=10,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

# Add Philipsburg label
ax.text(mill_gdf.geometry.x[0] - 15000, mill_gdf.geometry.y[0] - 20000,
        'Philipsburg\n(nearest town)', ha='center', fontsize=11,
        bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', alpha=0.7))

plt.tight_layout()
plt.savefig('montana_mill_30min_detail_basemap.png', dpi=150, bbox_inches='tight', facecolor='white')
print(f"Saved detailed map to montana_mill_30min_detail_basemap.png")

plt.show()