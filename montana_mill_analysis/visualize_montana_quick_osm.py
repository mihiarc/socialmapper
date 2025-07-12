#!/usr/bin/env python3
"""
Quick visualization of Montana timber mill with OSM basemap.
Optimized for speed - only creates the comparison view.
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
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

print("Loading data...")

# Create figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 9))

# Mill location
mill_lat = 47.167012
mill_lon = -113.466881

# Load both isochrones to determine overall bounds
iso_30 = gpd.read_parquet(files[30]['isochrone']).to_crs('EPSG:3857')
iso_120 = gpd.read_parquet(files[120]['isochrone']).to_crs('EPSG:3857')

# Get combined bounds with generous buffer for context
all_bounds = np.array([
    min(iso_30.total_bounds[0], iso_120.total_bounds[0]),
    min(iso_30.total_bounds[1], iso_120.total_bounds[1]),
    max(iso_30.total_bounds[2], iso_120.total_bounds[2]),
    max(iso_30.total_bounds[3], iso_120.total_bounds[3])
])

# Add 30% buffer to show surrounding area
x_range = all_bounds[2] - all_bounds[0]
y_range = all_bounds[3] - all_bounds[1]
buffer = 0.3
xlim = (all_bounds[0] - x_range * buffer, all_bounds[2] + x_range * buffer)
ylim = (all_bounds[1] - y_range * buffer, all_bounds[3] + y_range * buffer)

print("Creating visualizations...")

for ax, travel_time, iso_gdf in zip([ax1, ax2], [30, 120], [iso_30, iso_120]):
    # Load census data
    census_df = pd.read_csv(files[travel_time]['census'])
    
    # Create mill point
    mill_gdf = gpd.GeoDataFrame(
        [{'name': 'Mill'}], 
        geometry=gpd.points_from_xy([mill_lon], [mill_lat]),
        crs='EPSG:4326'
    ).to_crs('EPSG:3857')
    
    # Set bounds FIRST before adding basemap
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    
    # Add basemap with appropriate zoom
    print(f"Downloading basemap for {travel_time}-minute view...")
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=7)
    
    # Plot isochrone
    iso_gdf.plot(ax=ax, color='none', edgecolor='red', linewidth=3, alpha=0.9)
    iso_gdf.plot(ax=ax, color='red', alpha=0.15)
    
    # Plot mill location
    mill_gdf.plot(ax=ax, color='yellow', markersize=400, marker='*', 
                  edgecolor='black', linewidth=2, zorder=10)
    
    # Stats
    total_pop = census_df['B01003_001E'].sum()
    area_km2 = iso_gdf.to_crs('EPSG:5070').area.sum() / 1_000_000
    
    ax.set_title(f'{travel_time}-Minute Drive Radius\n'
                 f'Population: {total_pop:,}\n'
                 f'Area: {area_km2:,.0f} km²', 
                 fontsize=14, fontweight='bold', pad=20)
    
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Add key cities
    if travel_time == 120:
        cities = [
            ('Missoula', 46.8721, -113.9940),
            ('Butte', 46.0038, -112.5348),
            ('Helena', 46.5891, -112.0391),
            ('Philipsburg', 46.3321, -113.2948)
        ]
        
        for city_name, lat, lon in cities:
            city_point = gpd.GeoDataFrame(
                [{'name': city_name}],
                geometry=gpd.points_from_xy([lon], [lat]),
                crs='EPSG:4326'
            ).to_crs('EPSG:3857')
            
            x, y = city_point.geometry.x[0], city_point.geometry.y[0]
            ax.plot(x, y, 'ko', markersize=8)
            ax.text(x, y+8000, city_name, ha='center', va='bottom', 
                   fontsize=11, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                           edgecolor='black', alpha=0.8))

# Main title
fig.suptitle('Montana Timber Mill - Workforce Catchment Areas (Same Scale)', 
             fontsize=18, fontweight='bold')

# Info text
info = ("Maps shown at identical scale with OpenStreetMap basemap\n"
        "Yellow star = Proposed mill location | Red area = Drive time catchment")
fig.text(0.5, 0.02, info, ha='center', fontsize=12)

plt.tight_layout()
plt.subplots_adjust(top=0.92, bottom=0.08)

# Save
output_file = 'montana_mill_osm_comparison.png'
print(f"Saving to {output_file}...")
plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
print("Done!")

plt.show()