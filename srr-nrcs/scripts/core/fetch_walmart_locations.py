import requests
import json
import pandas as pd
import time
import os
from pathlib import Path
from scripts.core.config import Config
import overpy

def load_bbox(config: Config) -> dict:
    """
    Load the study area bounding box.
    
    Args:
        config: Configuration object for path management
    """
    bbox_path = Path(config.get_path('data.input.county_data')) / 'study_area_bbox.json'
    with open(bbox_path, 'r') as f:
        return json.load(f)

def get_walmart_stores(config: Config) -> pd.DataFrame:
    """
    Fetch Walmart store locations from OpenStreetMap within the study area bounding box.
    
    Args:
        config: Configuration object for path management
    
    Returns:
        pd.DataFrame containing Walmart store information
    """
    # Load bounding box
    bbox = load_bbox(config)
    
    api = overpy.Overpass()
    max_retries = 3
    retry_count = 0
    success = False
    
    while retry_count < max_retries and not success:
        try:
            # Create query using bounding box
            query = f"""
                [out:json][timeout:90];
                // Define the bounding box
                (
                    // Find all Walmart stores
                    node["shop"]["brand"="Walmart"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
                    way["shop"]["brand"="Walmart"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
                    node["shop"]["name"~"Walmart",i]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
                    way["shop"]["name"~"Walmart",i]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
                );
                out body;
                >;
                out center;
            """
            
            print(f"Attempting to fetch Walmart stores (Attempt {retry_count + 1}/{max_retries})")
            result = api.query(query)
            
            all_stores = []
            
            # Process nodes (point locations)
            for node in result.nodes:
                store_info = {
                    'id': node.id,
                    'type': 'node',
                    'lat': float(node.lat),
                    'lon': float(node.lon),
                    'name': node.tags.get('name', None),
                    'brand': node.tags.get('brand', None),
                    'street': node.tags.get('addr:street', None),
                    'housenumber': node.tags.get('addr:housenumber', None),
                    'city': node.tags.get('addr:city', None),
                    'state': node.tags.get('addr:state', None),
                    'postcode': node.tags.get('addr:postcode', None),
                    'phone': node.tags.get('phone', None),
                    'website': node.tags.get('website', None),
                    'opening_hours': node.tags.get('opening_hours', None)
                }
                all_stores.append(store_info)
            
            # Process ways (areas/buildings)
            for way in result.ways:
                # Get the center coordinates if available
                if way.nodes:
                    center_lat = sum(float(node.lat) for node in way.nodes) / len(way.nodes)
                    center_lon = sum(float(node.lon) for node in way.nodes) / len(way.nodes)
                    
                    store_info = {
                        'id': way.id,
                        'type': 'way',
                        'lat': center_lat,
                        'lon': center_lon,
                        'name': way.tags.get('name', None),
                        'brand': way.tags.get('brand', None),
                        'street': way.tags.get('addr:street', None),
                        'housenumber': way.tags.get('addr:housenumber', None),
                        'city': way.tags.get('addr:city', None),
                        'state': way.tags.get('addr:state', None),
                        'postcode': way.tags.get('addr:postcode', None),
                        'phone': way.tags.get('phone', None),
                        'website': way.tags.get('website', None),
                        'opening_hours': way.tags.get('opening_hours', None)
                    }
                    all_stores.append(store_info)
            
            print("Successfully fetched Walmart stores")
            success = True
            
        except Exception as e:
            print(f"Error fetching data (Attempt {retry_count + 1}/{max_retries}): {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                wait_time = 20 * (retry_count + 1)  # Increasing wait time with each retry
                print(f"Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
    
    # Convert to DataFrame
    df = pd.DataFrame(all_stores)
    
    if not df.empty:
        # Create full address
        df['address'] = df.apply(lambda x: f"{x['housenumber']} {x['street']}" if pd.notna(x['housenumber']) and pd.notna(x['street']) else x['street'], axis=1)
        
        # Clean up the data
        df = df[df['name'].notna()]  # Remove entries without names
        
        # Reorder columns for better readability
        columns_order = ['name', 'brand', 'state', 'city', 'address', 'postcode', 
                        'lat', 'lon', 'phone', 'website', 'opening_hours', 'type', 'id']
        df = df[columns_order]
    
    return df

def main():
    # Initialize configuration
    config = Config()
    
    # Ensure required files exist
    bbox_path = Path(config.get_path('data.input.county_data')) / 'study_area_bbox.json'
    if not bbox_path.exists():
        print(f"Error: {bbox_path} not found! Run fetch_county_boundaries.py first.")
        exit(1)
    
    # Fetch Walmart stores in the study area
    stores_df = get_walmart_stores(config)
    
    # Get output directory from config
    output_dir = Path(config.get_path('data.output.analysis'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results to CSV
    output_file = output_dir / 'walmart_stores_bbox.csv'
    stores_df.to_csv(output_file, index=False)
    
    # Cache the raw API response
    cache_dir = Path(config.get_path('cache.api_responses'))
    cache_file = cache_dir / 'walmart_stores_raw.csv'
    stores_df.to_csv(cache_file, index=False)
    
    # Print summary statistics
    print("\nSummary of Walmart stores found:")
    if not stores_df.empty:
        print("\nStores per state:")
        print(stores_df.groupby('state')['name'].count())
        print(f"\nTotal stores found: {len(stores_df)}")
        print("\nSample of stores found:")
        print(stores_df[['name', 'state', 'city', 'lat', 'lon']].head())
        print(f"\nResults saved to {output_file}")
        print(f"Raw data cached to {cache_file}")
    else:
        print("No stores found.")

if __name__ == "__main__":
    main() 