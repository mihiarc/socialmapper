#!/usr/bin/env python3
"""
Clean Walmart data by removing auxiliary services (pharmacy, deli, etc.) 
that are part of the main store.
"""

import pandas as pd
from pathlib import Path
from rich.console import Console

console = Console()

def clean_walmart_data():
    """Remove duplicate Walmart entries for auxiliary services."""
    
    # Load the data
    input_file = Path(__file__).parent.parent / "data" / "input" / "walmart_all.csv"
    output_file = Path(__file__).parent.parent / "data" / "input" / "walmart_cleaned.csv"
    
    console.print("[bold blue]Cleaning Walmart Data[/bold blue]")
    console.print("=" * 60)
    
    df = pd.read_csv(input_file)
    console.print(f"[cyan]Original dataset: {len(df)} entries[/cyan]")
    
    # Identify auxiliary service types to remove
    auxiliary_types = [
        'pharmacy', 'deli', 'garden center', 'vision center', 
        'auto care center', 'bakery', 'photo center', 'tire center'
    ]
    
    # Create a mask for auxiliary services
    is_auxiliary = df['name'].str.lower().str.contains('|'.join(auxiliary_types), na=False)
    
    # Show what we're removing
    auxiliary_df = df[is_auxiliary]
    console.print(f"\n[yellow]Found {len(auxiliary_df)} auxiliary service entries:[/yellow]")
    
    # Count by type
    for aux_type in auxiliary_types:
        count = df['name'].str.lower().str.contains(aux_type, na=False).sum()
        if count > 0:
            console.print(f"  • {aux_type.title()}: {count}")
    
    # Remove auxiliary services
    cleaned_df = df[~is_auxiliary].copy()
    
    # Remove exact coordinate duplicates (in case any remain)
    cleaned_df['lat_round'] = cleaned_df['latitude'].round(6)
    cleaned_df['lon_round'] = cleaned_df['longitude'].round(6)
    
    before_dedup = len(cleaned_df)
    cleaned_df = cleaned_df.drop_duplicates(subset=['lat_round', 'lon_round'], keep='first')
    after_dedup = len(cleaned_df)
    
    if before_dedup > after_dedup:
        console.print(f"\n[yellow]Removed {before_dedup - after_dedup} duplicate locations[/yellow]")
    
    # Drop temporary columns
    cleaned_df = cleaned_df.drop(columns=['lat_round', 'lon_round'])
    
    # Save cleaned data
    cleaned_df.to_csv(output_file, index=False)
    
    console.print(f"\n[green]✓ Cleaned dataset: {len(cleaned_df)} unique Walmart stores[/green]")
    console.print(f"[green]✓ Saved to: {output_file}[/green]")
    
    # Show summary by subtype
    console.print("\n[cyan]Store types in cleaned dataset:[/cyan]")
    for subtype, count in cleaned_df['subtype'].value_counts().items():
        console.print(f"  • {subtype}: {count}")
    
    return cleaned_df

if __name__ == "__main__":
    clean_walmart_data()