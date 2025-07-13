#!/usr/bin/env python3
"""
Consolidated data preparation script for Kansas grocery analysis.
Fetches and prepares Walmart and small grocer locations for SocialMapper analysis.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import requests
from rich.console import Console
from rich.table import Table
from rich.progress import track, Progress, SpinnerColumn, TextColumn

console = Console()

# Kansas strict bounding box (no buffer)
# Source: OpenStreetMap, US Census, Anthony Louis D'Agostino PhD (see https://wiki.openstreetmap.org/wiki/Kansas and https://anthonylouisdagostino.com/bounding-boxes-for-all-us-states/)
KANSAS_BOUNDS = {
    'min_lat': 36.993016,
    'max_lat': 40.003162,
    'min_lon': -102.051744,
    'max_lon': -94.588413
}


def query_overpass(query: str, max_retries: int = 3) -> Dict[str, Any]:
    """Execute an Overpass API query with retry logic."""
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                overpass_url, 
                params={'data': query}, 
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 10 * (attempt + 1)
                console.print(f"[yellow]Request failed, retrying in {wait_time} seconds...[/yellow]")
                time.sleep(wait_time)
            else:
                console.print(f"[red]Error querying Overpass API: {e}[/red]")
                return {"elements": []}


def fetch_walmart_stores() -> pd.DataFrame:
    """Fetch all Walmart stores in Kansas region from OpenStreetMap."""
    console.print("[bold blue]Fetching Walmart stores from OpenStreetMap...[/bold blue]")
    
    query = f"""
    [out:json][timeout:180];
    (
      // Primary: Walmart's Wikidata identifier
      nwr["brand:wikidata"="Q483551"]({KANSAS_BOUNDS['min_lat']},{KANSAS_BOUNDS['min_lon']},{KANSAS_BOUNDS['max_lat']},{KANSAS_BOUNDS['max_lon']});
      
      // Secondary: Name-based search
      nwr["shop"]["name"~"Walmart",i]({KANSAS_BOUNDS['min_lat']},{KANSAS_BOUNDS['min_lon']},{KANSAS_BOUNDS['max_lat']},{KANSAS_BOUNDS['max_lon']});
      
      // Include Sam's Club (owned by Walmart)
      nwr["brand:wikidata"="Q1972120"]({KANSAS_BOUNDS['min_lat']},{KANSAS_BOUNDS['min_lon']},{KANSAS_BOUNDS['max_lat']},{KANSAS_BOUNDS['max_lon']});
    );
    out center;
    """
    
    result = query_overpass(query)
    
    if not result.get('elements'):
        console.print("[red]No Walmart stores found[/red]")
        return pd.DataFrame()
    
    stores = []
    for element in result['elements']:
        if 'tags' not in element:
            continue
            
        tags = element['tags']
        
        # Extract coordinates
        if element['type'] == 'node':
            lat, lon = element['lat'], element['lon']
        else:
            center = element.get('center', {})
            lat = center.get('lat', 0)
            lon = center.get('lon', 0)
        
        # Skip invalid coordinates
        if lat == 0 or lon == 0:
            continue
        
        # Determine store type
        name = tags.get('name', '')
        if 'supercenter' in name.lower():
            store_type = 'supercenter'
        elif 'neighborhood market' in name.lower():
            store_type = 'neighborhood_market'
        elif 'sam\'s club' in name.lower():
            store_type = 'sams_club'
        else:
            store_type = 'walmart'
        
        stores.append({
            'name': name,
            'latitude': lat,
            'longitude': lon,
            'type': 'walmart',
            'subtype': store_type,
            'address': f"{tags.get('addr:street', '')}, {tags.get('addr:city', '')}, {tags.get('addr:state', 'KS')} {tags.get('addr:postcode', '')}".strip(),
            'city': tags.get('addr:city', ''),
            'state': tags.get('addr:state', ''),
            'brand': tags.get('brand', 'Walmart')
        })
    
    df = pd.DataFrame(stores)
    
    # Keep only Kansas stores and nearby border stores
    if 'state' in df.columns:
        df = df[(df['state'] == 'KS') | (df['state'].isna()) | (df['state'] == '')]
    
    console.print(f"[green]Found {len(df)} Walmart stores[/green]")
    return df


def fetch_small_grocers() -> pd.DataFrame:
    """Fetch small grocery stores and food retailers from OpenStreetMap."""
    console.print("[bold blue]Fetching small grocery stores from OpenStreetMap...[/bold blue]")
    
    query = f"""
    [out:json][timeout:180];
    (
      // Traditional grocery and convenience stores
      nwr["shop"="supermarket"]["name"!~"Walmart|Sam's Club",i]({KANSAS_BOUNDS['min_lat']},{KANSAS_BOUNDS['min_lon']},{KANSAS_BOUNDS['max_lat']},{KANSAS_BOUNDS['max_lon']});
      nwr["shop"="grocery"]({KANSAS_BOUNDS['min_lat']},{KANSAS_BOUNDS['min_lon']},{KANSAS_BOUNDS['max_lat']},{KANSAS_BOUNDS['max_lon']});
    );
    out center;
    """
    
    result = query_overpass(query)
    
    if not result.get('elements'):
        console.print("[red]No small grocery stores found[/red]")
        return pd.DataFrame()
    
    stores = []
    for element in result['elements']:
        if 'tags' not in element:
            continue
            
        tags = element['tags']
        
        # Extract coordinates
        if element['type'] == 'node':
            lat, lon = element['lat'], element['lon']
        else:
            center = element.get('center', {})
            lat = center.get('lat', 0)
            lon = center.get('lon', 0)
        
        # Skip invalid coordinates
        if lat == 0 or lon == 0:
            continue
        
        # Skip Walmart-owned stores
        name = tags.get('name', '')
        if any(x in name.lower() for x in ['walmart', 'sam\'s club']):
            continue
        
        # Determine store type
        shop_type = tags.get('shop', 'unknown')
        if 'dollar' in name.lower():
            subtype = 'dollar_store'
        elif shop_type == 'convenience':
            subtype = 'convenience_store'
        elif shop_type in ['butcher', 'greengrocer', 'farm']:
            subtype = 'specialty_food'
        else:
            subtype = shop_type
        
        stores.append({
            'name': name or f"Unnamed {shop_type}",
            'latitude': lat,
            'longitude': lon,
            'type': 'small_grocer',
            'subtype': subtype,
            'address': f"{tags.get('addr:street', '')}, {tags.get('addr:city', '')}, KS {tags.get('addr:postcode', '')}".strip(),
            'city': tags.get('addr:city', ''),
            'state': 'KS',
            'shop_type': shop_type
        })
    
    df = pd.DataFrame(stores)
    console.print(f"[green]Found {len(df)} small grocery stores[/green]")
    return df


def prepare_socialmapper_format(df: pd.DataFrame, poi_type: str) -> pd.DataFrame:
    """Convert store data to SocialMapper custom POI format."""
    poi_df = pd.DataFrame({
        'name': df['name'],
        'latitude': df['latitude'],
        'longitude': df['longitude'],
        'type': poi_type,
        'address': df['address']
    })
    
    # Add metadata columns
    if 'city' in df.columns:
        poi_df['city'] = df['city']
    if 'subtype' in df.columns:
        poi_df['subtype'] = df['subtype']
    
    # Validate coordinates
    poi_df = poi_df[(poi_df['latitude'].between(36, 41)) & 
                    (poi_df['longitude'].between(-103, -94))]
    
    # Remove duplicates at exact same location
    # Round coordinates to 6 decimal places (about 0.1 meter precision)
    poi_df['lat_round'] = poi_df['latitude'].round(6)
    poi_df['lon_round'] = poi_df['longitude'].round(6)
    
    # Keep only the first store at each unique location
    before_dedup = len(poi_df)
    poi_df = poi_df.drop_duplicates(subset=['lat_round', 'lon_round'], keep='first')
    after_dedup = len(poi_df)
    
    if before_dedup > after_dedup:
        console.print(f"[yellow]Removed {before_dedup - after_dedup} duplicate locations (stores at exact same coordinates)[/yellow]")
    
    # Drop the temporary rounding columns
    poi_df = poi_df.drop(columns=['lat_round', 'lon_round'])
    
    return poi_df


def remove_cross_dataset_duplicates(walmart_poi: pd.DataFrame, grocer_poi: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Remove stores that appear in both datasets at the same location."""
    if walmart_poi.empty or grocer_poi.empty:
        return walmart_poi, grocer_poi
    
    # Round coordinates for comparison
    walmart_poi['lat_round'] = walmart_poi['latitude'].round(6)
    walmart_poi['lon_round'] = walmart_poi['longitude'].round(6)
    grocer_poi['lat_round'] = grocer_poi['latitude'].round(6)
    grocer_poi['lon_round'] = grocer_poi['longitude'].round(6)
    
    # Find locations that appear in both datasets
    walmart_coords = set(zip(walmart_poi['lat_round'], walmart_poi['lon_round']))
    grocer_coords = set(zip(grocer_poi['lat_round'], grocer_poi['lon_round']))
    duplicate_coords = walmart_coords.intersection(grocer_coords)
    
    if duplicate_coords:
        console.print(f"[yellow]Found {len(duplicate_coords)} locations appearing in both Walmart and grocer datasets[/yellow]")
        
        # Remove duplicates from grocer dataset (keep Walmart as it's likely the primary store)
        grocer_poi = grocer_poi[~grocer_poi[['lat_round', 'lon_round']].apply(tuple, axis=1).isin(duplicate_coords)]
        console.print(f"[yellow]Removed duplicates from grocer dataset (keeping Walmart locations)[/yellow]")
    
    # Drop temporary columns
    walmart_poi = walmart_poi.drop(columns=['lat_round', 'lon_round'])
    grocer_poi = grocer_poi.drop(columns=['lat_round', 'lon_round'])
    
    return walmart_poi, grocer_poi


def save_data(walmart_df: pd.DataFrame, small_grocer_df: pd.DataFrame, output_dir: Path) -> None:
    """Save prepared data in SocialMapper-ready format (only all Walmarts and all small grocers)."""
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Prepare data with deduplication
    walmart_poi = pd.DataFrame()
    grocer_poi = pd.DataFrame()
    
    if not walmart_df.empty:
        walmart_poi = prepare_socialmapper_format(walmart_df, 'walmart')
    
    if not small_grocer_df.empty:
        grocer_poi = prepare_socialmapper_format(small_grocer_df, 'small_grocer')
    
    # Remove cross-dataset duplicates
    if not walmart_poi.empty and not grocer_poi.empty:
        walmart_poi, grocer_poi = remove_cross_dataset_duplicates(walmart_poi, grocer_poi)
    
    # Save Walmart data
    if not walmart_poi.empty:
        walmart_poi.to_csv(output_dir / 'walmart_all.csv', index=False)
        console.print(f"[green]✓ Saved {len(walmart_poi)} Walmart stores[/green]")
    
    # Save small grocer data
    if not grocer_poi.empty:
        grocer_poi.to_csv(output_dir / 'small_grocers_all.csv', index=False)
        console.print(f"[green]✓ Saved {len(grocer_poi)} small grocery stores[/green]")


def generate_summary(walmart_df: pd.DataFrame, small_grocer_df: pd.DataFrame) -> None:
    """Generate and display summary statistics."""
    table = Table(title="Kansas Grocery Store Summary")
    table.add_column("Category", style="cyan")
    table.add_column("Count", style="green")
    table.add_column("Details", style="yellow")
    
    # Walmart summary
    if not walmart_df.empty:
        walmart_total = len(walmart_df)
        walmart_cities = walmart_df['city'].nunique()
        walmart_types = walmart_df.groupby('subtype').size()
        
        table.add_row("Walmart Stores", str(walmart_total), f"{walmart_cities} cities")
        for subtype, count in walmart_types.items():
            table.add_row(f"  - {subtype}", str(count), "")
    
    # Small grocer summary
    if not small_grocer_df.empty:
        grocer_total = len(small_grocer_df)
        grocer_cities = small_grocer_df['city'].nunique()
        grocer_types = small_grocer_df.groupby('subtype').size()
        
        table.add_row("Small Grocers", str(grocer_total), f"{grocer_cities} cities")
        for subtype, count in grocer_types.head(5).items():
            table.add_row(f"  - {subtype}", str(count), "")
    
    console.print(table)


def main():
    """Main function to prepare all data for Kansas grocery analysis."""
    console.print("[bold]Kansas Grocery Analysis - Data Preparation[/bold]")
    console.print("=" * 60)
    
    # Set up output directory - use absolute path
    output_dir = Path(__file__).parent.parent / "data" / "input"
    output_dir = output_dir.resolve()  # Convert to absolute path
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Fetch data from OpenStreetMap
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        task1 = progress.add_task("[yellow]Fetching Walmart stores...", total=None)
        walmart_df = fetch_walmart_stores()
        progress.update(task1, completed=True)
        
        task2 = progress.add_task("[yellow]Fetching small grocery stores...", total=None)
        small_grocer_df = fetch_small_grocers()
        progress.update(task2, completed=True)
    
    # Generate summary
    console.print("\n")
    generate_summary(walmart_df, small_grocer_df)
    
    # Save data
    console.print("\n[cyan]Saving data files...[/cyan]")
    save_data(walmart_df, small_grocer_df, output_dir)
    
    console.print("\n[bold green]Data preparation complete![/bold green]")
    console.print("\nNext step: Run analyze_access.py to perform the food access analysis")


if __name__ == "__main__":
    main()