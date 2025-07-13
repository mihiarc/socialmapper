#!/usr/bin/env python3
"""
Identify which specific stores have the small isochrones.
"""

import pandas as pd
from pathlib import Path
from rich.console import Console

console = Console()

def identify_problem_stores():
    """Map the problem isochrone indices to actual stores."""
    
    data_dir = Path(__file__).parent.parent / "data"
    
    # Load the original Walmart data to map indices
    walmart_file = data_dir / "input" / "walmart_all.csv"
    walmart_df = pd.read_csv(walmart_file)
    
    # The problematic indices from our visualization
    problem_indices = [1, 2, 3, 26, 39]
    
    console.print("[bold]Stores with Small Isochrones:[/bold]\n")
    
    for idx in problem_indices:
        if idx < len(walmart_df):
            store = walmart_df.iloc[idx]
            console.print(f"[cyan]Index {idx}:[/cyan]")
            console.print(f"  Name: {store['name']}")
            console.print(f"  Type: {store['subtype']}")
            console.print(f"  City: {store['city']}")
            console.print(f"  Address: {store['address']}")
            console.print(f"  Coordinates: ({store['latitude']}, {store['longitude']})")
            console.print()
    
    # Also check the cleaned data
    console.print("\n[bold]Checking cleaned data file:[/bold]\n")
    
    cleaned_file = data_dir / "input" / "walmart_cleaned.csv"
    if cleaned_file.exists():
        cleaned_df = pd.read_csv(cleaned_file)
        
        # The poi_custom numbers in the isochrone file might map differently
        # Let's check by coordinates
        for idx in problem_indices:
            if idx < len(walmart_df):
                orig_store = walmart_df.iloc[idx]
                lat, lon = orig_store['latitude'], orig_store['longitude']
                
                # Find this store in cleaned data
                matches = cleaned_df[
                    (abs(cleaned_df['latitude'] - lat) < 0.0001) &
                    (abs(cleaned_df['longitude'] - lon) < 0.0001)
                ]
                
                if len(matches) == 0:
                    console.print(f"[yellow]Index {idx} ({orig_store['name']}) was removed during cleaning[/yellow]")
                    console.print(f"  Subtype: {orig_store['subtype']}")
                else:
                    console.print(f"[green]Index {idx} is still in cleaned data[/green]")

if __name__ == "__main__":
    identify_problem_stores()