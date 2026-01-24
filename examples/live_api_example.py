#!/usr/bin/env python3
"""
SocialMapper Live API Example

This example demonstrates real API calls using the Census API key.
Unlike demo mode, this works with ANY US location and returns live data.

Prerequisites:
    export CENSUS_API_KEY=your_key_here

Usage:
    python examples/live_api_example.py
"""

import os
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Set the Census API key (or use environment variable)
# Get your free key at: https://api.census.gov/data/key_signup.html
if not os.environ.get("CENSUS_API_KEY"):
    os.environ["CENSUS_API_KEY"] = "b607120490031baad1c96ea61d30c8ba8b2bc246"

from socialmapper import (
    create_isochrone,
    get_poi,
    get_census_blocks,
    get_census_data,
    create_map,
)

console = Console()


def timed(func):
    """Decorator to time function execution."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        return result, elapsed
    return wrapper


@timed
def run_create_isochrone(location, travel_time, travel_mode):
    return create_isochrone(location, travel_time=travel_time, travel_mode=travel_mode)


@timed
def run_get_poi(location, categories, limit):
    return get_poi(location, categories=categories, limit=limit)


@timed
def run_get_census_blocks(polygon):
    return get_census_blocks(polygon=polygon)


@timed
def run_get_census_data(geoids, variables):
    return get_census_data(location=geoids, variables=variables)


def main():
    console.print()
    console.print(Panel(
        "[bold cyan]SocialMapper Live API Example[/bold cyan]\n\n"
        "Using real API calls - not demo mode!\n"
        "This works with ANY US location.",
        border_style="cyan"
    ))

    # Configuration
    location = (35.7796, -78.6382)  # Raleigh, NC (coordinates for precision)
    location_name = "Raleigh, NC"
    travel_time = 10  # minutes
    travel_mode = "drive"

    console.print(f"\n[bold]Analysis Configuration:[/bold]")
    console.print(f"  Location: {location_name} {location}")
    console.print(f"  Travel time: {travel_time} minutes")
    console.print(f"  Travel mode: {travel_mode}")

    # =========================================================================
    # 1. Create Isochrone
    # =========================================================================
    console.print("\n[bold yellow]1. Creating isochrone...[/bold yellow]")

    isochrone, iso_time = run_create_isochrone(location, travel_time, travel_mode)

    console.print(f"   [green]Done![/green] ({iso_time:.2f}s)")
    console.print(f"   Area: {isochrone['properties']['area_sq_km']:.2f} km²")

    # =========================================================================
    # 2. Find Points of Interest
    # =========================================================================
    console.print("\n[bold yellow]2. Finding points of interest...[/bold yellow]")

    # Valid categories: education, healthcare, food_and_drink, shopping,
    # recreation, transportation, services, accommodation, religious, utilities
    categories = ["education", "healthcare"]
    pois, poi_time = run_get_poi(location, categories, limit=20)

    console.print(f"   [green]Done![/green] ({poi_time:.2f}s)")
    console.print(f"   Found {len(pois)} POIs")

    if pois:
        # Group by category
        by_category = {}
        for poi in pois:
            cat = poi.get("category", "other")
            by_category[cat] = by_category.get(cat, 0) + 1

        for cat, count in sorted(by_category.items()):
            console.print(f"   - {cat}: {count}")

        # Show closest 3
        console.print("\n   [bold]Closest POIs:[/bold]")
        for poi in pois[:3]:
            name = poi.get("name", "Unknown")[:40]
            dist = poi.get("distance_km", 0)
            cat = poi.get("category", "")
            console.print(f"   - {name} ({cat}) - {dist:.2f} km")

    # =========================================================================
    # 3. Get Census Block Groups
    # =========================================================================
    console.print("\n[bold yellow]3. Getting census block groups...[/bold yellow]")

    blocks, blocks_time = run_get_census_blocks(isochrone)

    console.print(f"   [green]Done![/green] ({blocks_time:.2f}s)")
    console.print(f"   Found {len(blocks)} census block groups")

    # =========================================================================
    # 4. Get Census Data
    # =========================================================================
    console.print("\n[bold yellow]4. Fetching census demographics...[/bold yellow]")

    # Limit to first 30 blocks for faster API response
    sample_blocks = blocks[:30] if len(blocks) > 30 else blocks
    geoids = [block["geoid"] for block in sample_blocks]

    variables = ["population", "median_income", "median_age"]
    census_result, census_time = run_get_census_data(geoids, variables)

    console.print(f"   [green]Done![/green] ({census_time:.2f}s)")
    console.print(f"   Retrieved data for {len(census_result.data)} block groups")

    # Calculate totals
    total_pop = sum(
        d.get("population", 0) for d in census_result.data.values()
    )

    incomes = [
        d.get("median_income", 0)
        for d in census_result.data.values()
        if d.get("median_income", 0) > 0
    ]
    avg_income = sum(incomes) / len(incomes) if incomes else 0

    ages = [
        d.get("median_age", 0)
        for d in census_result.data.values()
        if d.get("median_age", 0) > 0
    ]
    avg_age = sum(ages) / len(ages) if ages else 0

    # =========================================================================
    # 5. Create Map (optional - save to file)
    # =========================================================================
    console.print("\n[bold yellow]5. Creating visualization...[/bold yellow]")

    # Add population data to blocks for visualization
    for block in sample_blocks:
        geoid = block["geoid"]
        block["population"] = census_result.data.get(geoid, {}).get("population", 0)

    try:
        map_result = create_map(
            data=sample_blocks,
            column="population",
            title=f"Population within {travel_time}-min {travel_mode} of {location_name}",
            save_path="raleigh_population_map.png"
        )
        console.print(f"   [green]Done![/green]")
        console.print(f"   Saved to: {map_result.file_path}")
    except Exception as e:
        console.print(f"   [yellow]Skipped:[/yellow] {e}")

    # =========================================================================
    # Results Summary
    # =========================================================================
    console.print()

    table = Table(title=f"Analysis Results: {location_name}", show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Location", f"{location_name} {location}")
    table.add_row("Travel Time", f"{travel_time} minutes ({travel_mode})")
    table.add_row("Coverage Area", f"{isochrone['properties']['area_sq_km']:.2f} km²")
    table.add_row("POIs Found", str(len(pois)))
    table.add_row("Census Blocks", str(len(blocks)))
    table.add_row("Total Population", f"{int(total_pop):,}")
    table.add_row("Avg Median Income", f"${avg_income:,.0f}")
    table.add_row("Avg Median Age", f"{avg_age:.1f} years")

    console.print(table)

    # Timing summary
    total_time = iso_time + poi_time + blocks_time + census_time
    console.print(f"\n[dim]Total API time: {total_time:.2f}s[/dim]")
    console.print(f"[dim]  - Isochrone: {iso_time:.2f}s[/dim]")
    console.print(f"[dim]  - POI search: {poi_time:.2f}s[/dim]")
    console.print(f"[dim]  - Census blocks: {blocks_time:.2f}s[/dim]")
    console.print(f"[dim]  - Census data: {census_time:.2f}s[/dim]")

    # =========================================================================
    # Example: Try a Different Location
    # =========================================================================
    console.print("\n" + "=" * 60)
    console.print("[bold]Try your own location![/bold]")
    console.print("=" * 60)
    console.print("""
Edit this script and change the location:

    # Use coordinates (more precise)
    location = (47.6062, -122.3321)  # Seattle, WA

    # Or use city name (requires geocoding)
    location = "Austin, TX"

    # Change travel parameters
    travel_time = 15  # minutes
    travel_mode = "walk"  # or "bike", "drive"
""")

    console.print("\n[green]Live API example complete![/green]\n")


if __name__ == "__main__":
    main()
