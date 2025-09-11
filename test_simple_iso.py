#!/usr/bin/env python3
"""Test direct isochrone generation."""

from socialmapper import create_isochrone
from rich.console import Console

console = Console()

# Test with coordinates (bypasses geocoding)
console.print("\n[cyan]Testing isochrone generation with coordinates:[/cyan]")

try:
    # Portland, OR coordinates
    iso = create_isochrone(
        location=(45.5152, -122.6784),
        travel_time=15,
        travel_mode="drive"
    )
    
    console.print("[green]✅ Success![/green]")
    console.print(f"  Location: {iso['location'].iloc[0]}")
    console.print(f"  Travel time: {iso['travel_time'].iloc[0]} min")
    console.print(f"  Travel mode: {iso['travel_mode'].iloc[0]}")
    console.print(f"  Geometry type: {iso.geometry.iloc[0].geom_type}")
    
    # Get as dict
    iso_dict = create_isochrone(
        location=(40.7128, -74.0060),  # NYC
        travel_time=10,
        travel_mode="walk",
        return_type="dict"
    )
    
    console.print("\n[cyan]Dict format:[/cyan]")
    console.print(f"  Type: {iso_dict['type']}")
    console.print(f"  Area: {iso_dict['properties']['area_sq_km']:.2f} sq km")
    
except Exception as e:
    console.print(f"[red]Error: {e}[/red]")