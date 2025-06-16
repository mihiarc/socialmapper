"""Examples of using the TIGER geometry client."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt

from ...visualization import ChoroplethMap, ColorScheme, MapConfig
from .client import TigerGeometryClient
from .models import GeographyLevel, GeometryQuery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_fetch_counties():
    """Example: Fetch county geometries for California."""
    client = TigerGeometryClient()

    # Fetch all counties in California
    result = client.fetch_counties(state_fips="06")

    print(f"Fetched {result.geometry_count} counties")
    print(f"Bounds: {result.bounds}")
    print(f"Sample counties: {result.geodataframe['NAME'].head().tolist()}")

    return result


def example_fetch_bay_area_counties():
    """Example: Fetch specific Bay Area counties."""
    client = TigerGeometryClient()

    # Fetch specific counties by name
    bay_area_counties = [
        "Alameda County",
        "Contra Costa County",
        "Marin County",
        "Napa County",
        "San Francisco County",
        "San Mateo County",
        "Santa Clara County",
        "Solano County",
        "Sonoma County",
    ]

    result = client.fetch_counties(
        state_fips="06",
        county_names=bay_area_counties,
        simplify_tolerance=0.001,  # More aggressive simplification
    )

    print(f"Fetched {result.geometry_count} Bay Area counties")

    return result


def example_fetch_block_groups():
    """Example: Fetch block groups for Alameda County, CA."""
    client = TigerGeometryClient()

    # Fetch block groups for Alameda County (FIPS: 001)
    result = client.fetch_block_groups(
        state_fips="06",
        county_fips="001",
        simplify_tolerance=0.0001,
    )

    print(f"Fetched {result.geometry_count} block groups")
    print(f"Sample GEOIDs: {result.geodataframe['GEOID'].head().tolist()}")

    return result


def example_fetch_zctas():
    """Example: Fetch ZCTAs starting with 945 (East Bay area)."""
    client = TigerGeometryClient()

    # Fetch ZCTAs with prefix 945
    result = client.fetch_zctas(
        zcta_prefix="945",
        simplify_tolerance=0.0001,
    )

    print(f"Fetched {result.geometry_count} ZCTAs")
    print(f"ZCTAs: {sorted(result.geodataframe['GEOID'].tolist())}")

    return result


def example_visualize_counties_with_data():
    """Example: Visualize counties with mock demographic data."""
    # Fetch counties
    client = TigerGeometryClient()
    result = client.fetch_counties(state_fips="06")

    # Add mock demographic data (e.g., population density)
    import numpy as np

    np.random.seed(42)
    result.geodataframe["pop_density"] = np.random.uniform(50, 5000, len(result.geodataframe))

    # Create choropleth map
    map_config = MapConfig(
        title="California Counties - Population Density",
        color_scheme=ColorScheme.VIRIDIS,
        figsize=(12, 10),
        show_legend=True,
        show_north_arrow=True,
        show_scale_bar=True,
    )

    choropleth = ChoroplethMap(
        gdf=result.geodataframe,
        value_column="pop_density",
        config=map_config,
    )

    # Create the map
    fig = choropleth.create_map()

    # Save the map
    output_path = Path("california_counties_density.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Map saved to {output_path}")

    return fig


def example_multi_geography_visualization():
    """Example: Visualize multiple geography levels together."""
    client = TigerGeometryClient()

    # Fetch Bay Area counties
    counties_result = client.fetch_counties(
        state_fips="06",
        county_names=["Alameda County", "San Francisco County", "Contra Costa County"],
    )

    # Fetch ZCTAs in the same area
    zctas_result = client.fetch_zctas(zcta_prefix="946")  # East Bay ZCTAs

    # Create a figure with both layers
    fig, ax = plt.subplots(figsize=(12, 10))

    # Plot counties as base layer
    counties_result.geodataframe.plot(
        ax=ax,
        color="lightgray",
        edgecolor="black",
        linewidth=2,
        alpha=0.5,
    )

    # Plot ZCTAs on top
    zctas_result.geodataframe.plot(
        ax=ax,
        color="skyblue",
        edgecolor="darkblue",
        linewidth=0.5,
        alpha=0.7,
    )

    # Add labels for counties
    for idx, row in counties_result.geodataframe.iterrows():
        centroid = row.geometry.centroid
        ax.annotate(
            row["NAME"],
            xy=(centroid.x, centroid.y),
            xytext=(3, 3),
            textcoords="offset points",
            fontsize=10,
            fontweight="bold",
        )

    ax.set_title("Bay Area Counties and ZCTAs", fontsize=16, fontweight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def example_advanced_query():
    """Example: Advanced query with custom parameters."""
    client = TigerGeometryClient(
        cache_dir=".tiger_cache",  # Enable caching
        rate_limit_delay=0.2,  # Be nice to the API
    )

    # Create a custom query for congressional districts
    query = GeometryQuery(
        geography_level=GeographyLevel.CONGRESSIONAL_DISTRICT,
        state_fips="06",  # California
        simplify_tolerance=0.001,
        include_attributes=True,
    )

    result = client.fetch_geometries(query)

    print(f"Fetched {result.geometry_count} congressional districts")
    print(f"Columns: {result.geodataframe.columns.tolist()}")

    return result


def example_integration_with_census_data():
    """Example: Integrate TIGER geometries with census demographic data."""
    from ...census.infrastructure.census_api_client import CensusAPIClientImpl
    from ...census.services.census_data_service import CensusDataService

    # Initialize clients
    tiger_client = TigerGeometryClient()
    census_client = CensusAPIClientImpl(api_key="YOUR_CENSUS_API_KEY")
    census_service = CensusDataService(census_client)

    # Fetch block group geometries
    geometry_result = tiger_client.fetch_block_groups(
        state_fips="06",
        county_fips="001",  # Alameda County
    )

    # Fetch demographic data for the same block groups
    # Note: This is a simplified example - actual implementation would need proper API key
    variables = ["B01001_001E"]  # Total population

    # Merge geometries with demographic data
    # (In practice, you'd fetch the census data and merge on GEOID)

    print(f"Ready to merge {geometry_result.geometry_count} geometries with census data")

    return geometry_result


if __name__ == "__main__":
    # Run examples
    print("=== Fetching California Counties ===")
    example_fetch_counties()

    print("\n=== Fetching Bay Area Counties ===")
    example_fetch_bay_area_counties()

    print("\n=== Fetching Block Groups ===")
    example_fetch_block_groups()

    print("\n=== Fetching ZCTAs ===")
    example_fetch_zctas()

    print("\n=== Creating County Visualization ===")
    example_visualize_counties_with_data()

    print("\n=== Advanced Query Example ===")
    example_advanced_query()
