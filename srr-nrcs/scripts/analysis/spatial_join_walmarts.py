import geopandas as gpd
import pandas as pd
from pathlib import Path

def load_walmart_points(csv_file: str) -> gpd.GeoDataFrame:
    """Load Walmart locations and convert to GeoDataFrame."""
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Create GeoDataFrame from lat/lon
    gdf = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df.lon, df.lat),
        crs="EPSG:4326"  # WGS84 coordinate system
    )
    return gdf

def spatial_join_walmarts_to_counties():
    """Perform spatial join between Walmart locations and county boundaries."""
    # Check if input files exist
    walmart_file = 'walmart_stores_by_state.csv'
    counties_file = 'county_boundaries.geojson'
    
    if not Path(walmart_file).exists():
        raise FileNotFoundError(f"Walmart stores file not found: {walmart_file}")
    if not Path(counties_file).exists():
        raise FileNotFoundError(f"County boundaries file not found: {counties_file}")
    
    # Load the data
    print("Loading data...")
    counties = gpd.read_file(counties_file)
    walmarts = load_walmart_points(walmart_file)
    
    print(f"Found {len(walmarts)} Walmart locations")
    print(f"Found {len(counties)} counties")
    
    # Perform spatial join
    print("Performing spatial join...")
    joined = gpd.sjoin(walmarts, counties, how="inner", predicate="within")
    
    # Clean up the columns
    # Keep original Walmart data plus county information
    keep_cols = [
        'name', 'brand', 'state', 'city', 'address', 'postcode',
        'lat', 'lon', 'phone', 'website', 'opening_hours', 'type', 'id',
        'GEOID', 'NAME', 'STUSPS', 'COUNTYFP'
    ]
    joined = joined[keep_cols]
    
    # Rename columns for clarity
    joined = joined.rename(columns={
        'NAME': 'county_name',
        'STUSPS': 'state_code',
        'GEOID': 'county_fips',
        'COUNTYFP': 'county_fips_local'
    })
    
    # Save results
    output_file = 'walmart_stores_by_county.csv'
    joined.to_csv(output_file, index=False)
    print(f"\nResults saved to {output_file}")
    
    # Print summary statistics
    print("\nWalmart stores by state and county:")
    summary = joined.groupby(['state_code', 'county_name'])['name'].count()
    print(summary)
    print(f"\nTotal stores in study area: {len(joined)}")

if __name__ == "__main__":
    spatial_join_walmarts_to_counties() 