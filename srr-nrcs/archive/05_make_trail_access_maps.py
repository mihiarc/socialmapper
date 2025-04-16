import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import os
import numpy as np
from matplotlib.colors import BoundaryNorm
from matplotlib.patches import Patch
import matplotlib.patheffects as pe

# Ensure the 'forest_access_maps' directory exists
output_folder = 'forest_access_maps'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Read the filtered block groups GeoPackage
block_groups = gpd.read_file('/Users/mihiarc/Work/repos/nfs-econ-research/data/block_group_population_near_trails.gpkg')

# Ensure geometries are valid
block_groups = block_groups[block_groups.is_valid]

# Read places data
places = gpd.read_parquet('/Users/mihiarc/Work/data/spatial-boundaries/combined_census_places.parquet')
places = places.to_crs(epsg=3857)
places['centroid'] = places.geometry.centroid

# Filter the trails based on isochrone_trails
isochrone_trails = block_groups['hiking_trail'].unique()

# List of hiking trails
hiking_trails = isochrone_trails

# Loop over each hiking trail
for trail in hiking_trails:
    # Filter block groups for the current trail
    trail_block_groups = block_groups[block_groups['hiking_trail'] == trail]

    # Reproject to Web Mercator for contextily basemap
    trail_block_groups = trail_block_groups.to_crs(epsg=3857)

    # Create a plot
    fig, ax = plt.subplots(figsize=(12, 12))

    # Plot the block groups, using population data for choropleth
    cmap = 'RdPu'  # colormap
    trail_block_groups.plot(
        column='Population',
        cmap=cmap,
        linewidth=0.5,
        edgecolor='white',
        legend=False,  # We'll add a custom legend
        alpha=0.7,     # Adjust transparency
        ax=ax
    )

    # Add basemap
    ctx.add_basemap(
        ax,
        source=ctx.providers.OpenStreetMap.Mapnik,
        crs=trail_block_groups.crs.to_string()
    )

    # Zoom out by adjusting the extent
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_margin = (xlim[1] - xlim[0]) * 0.4  # 40% margin
    y_margin = (ylim[1] - ylim[0]) * 0.4  # 40% margin
    ax.set_xlim(xlim[0] - x_margin, xlim[1] + x_margin)
    ax.set_ylim(ylim[0] - y_margin, ylim[1] + y_margin)

    # Create a union of the block group geometries
    trail_union = trail_block_groups.unary_union

    # Create a custom legend
    min_pop = trail_block_groups['Population'].min()
    max_pop = trail_block_groups['Population'].max()
    bins = np.linspace(min_pop, max_pop, 6)
    bins = np.round(bins, -2)  # Round to nearest hundred for cleaner labels
    labels = [f'{int(bins[i]):,} - {int(bins[i+1]):,}' for i in range(len(bins)-1)]

    # Create a colormap and normalization
    norm = BoundaryNorm(bins, plt.get_cmap(cmap).N)

    # Create legend patches
    legend_handles = [
        Patch(
            facecolor=plt.get_cmap(cmap)(norm(bins[i])),
            edgecolor='white',
            label=labels[i]
        ) for i in range(len(labels))
    ]

    # Add the legend below the map
    ax.legend(
        handles=legend_handles,
        loc='lower center',
        bbox_to_anchor=(0.5, -0.15),
        ncol=len(labels) + 1,
        title='Population',
        frameon=False,
        fontsize='small',
        title_fontsize='medium'
    )

    # Add title and labels
    ax.set_title(f'30-minute {trail}', fontsize=14, fontweight='bold')
    ax.set_axis_off()

    # Save the plot
    output_path = os.path.join(output_folder, f'{trail}_population_map.png')
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)

    print(f'Map saved for trail: {trail}')

print('All maps have been saved in the forest_access_maps folder.')