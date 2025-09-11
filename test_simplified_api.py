#!/usr/bin/env python3
"""Test the simplified SocialMapper API."""

from socialmapper import create_isochrone, SocialMapper
from rich.console import Console
from rich.table import Table

console = Console()

def test_simplified_api():
    """Test the new simplified API."""
    
    console.print("\n[bold cyan]Testing Simplified SocialMapper API[/bold cyan]\n")
    
    # Test 1: Create isochrone from city name
    console.print("[yellow]Test 1:[/yellow] Creating isochrone from city name...")
    try:
        iso = create_isochrone("Portland, OR", travel_time=15, travel_mode="drive")
        console.print(f"✅ Created isochrone for Portland, OR")
        console.print(f"   - Geometry type: {iso.geometry.iloc[0].geom_type}")
        console.print(f"   - Travel time: {iso['travel_time'].iloc[0]} minutes")
        console.print(f"   - Travel mode: {iso['travel_mode'].iloc[0]}")
    except Exception as e:
        console.print(f"❌ Failed: {e}")
    
    # Test 2: Create isochrone from coordinates
    console.print("\n[yellow]Test 2:[/yellow] Creating isochrone from coordinates...")
    try:
        iso = create_isochrone((45.5152, -122.6784), travel_time=10, travel_mode="walk")
        console.print(f"✅ Created isochrone for coordinates (45.5152, -122.6784)")
        console.print(f"   - Location: {iso['location'].iloc[0]}")
        console.print(f"   - Travel time: {iso['travel_time'].iloc[0]} minutes")
        console.print(f"   - Travel mode: {iso['travel_mode'].iloc[0]}")
    except Exception as e:
        console.print(f"❌ Failed: {e}")
    
    # Test 3: Get isochrone as dict for JSON serialization
    console.print("\n[yellow]Test 3:[/yellow] Getting isochrone as dict...")
    try:
        iso_dict = create_isochrone("Boston, MA", travel_time=20, return_type="dict")
        console.print(f"✅ Created isochrone dict for Boston, MA")
        console.print(f"   - Type: {iso_dict['type']}")
        console.print(f"   - Geometry type: {iso_dict['geometry']['type']}")
        console.print(f"   - Area: {iso_dict['properties']['area_sq_km']:.2f} sq km")
    except Exception as e:
        console.print(f"❌ Failed: {e}")
    
    # Test 4: Test simplified client
    console.print("\n[yellow]Test 4:[/yellow] Testing simplified SocialMapper client...")
    try:
        mapper = SocialMapper(api_key="test_key")
        console.print(f"✅ Created client: {mapper}")
    except Exception as e:
        console.print(f"❌ Failed: {e}")
    
    # Summary
    console.print("\n[bold green]API Simplification Summary:[/bold green]")
    
    table = Table(title="Removed Components", show_header=True)
    table.add_column("Component", style="cyan")
    table.add_column("Reason", style="yellow")
    
    table.add_row("9 convenience functions", "Redundant wrappers around core functionality")
    table.add_row("analyze_location()", "Overengineered orchestration")
    table.add_row("Pipeline orchestrator", "Unnecessary abstraction")
    table.add_row("Complex configs", "Should be simple function parameters")
    
    console.print(table)
    
    console.print("\n[bold green]New Simple API:[/bold green]")
    console.print("• create_isochrone() - Direct isochrone generation")
    console.print("• SocialMapper() - Minimal client for API key management")
    console.print("• Individual census/poi functions for composition")

if __name__ == "__main__":
    test_simplified_api()