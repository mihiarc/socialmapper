#!/usr/bin/env python3
"""
SocialMapper Neighbors API Usage Examples

This script demonstrates the different ways to access neighbor functionality
directly without using the full SocialMapper workflow.
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import socialmapper
import socialmapper.neighbors as neighbors
from socialmapper.neighbors import (
    get_neighboring_states,
    get_neighboring_counties,
    get_geography_from_point
)

# Import Rich components
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.progress import track
from rich import box
import time

console = Console()

def demo_package_level_access():
    """Demonstrate accessing neighbors at the package level."""
    
    console.print(Panel.fit(
        "[bold blue]1. Package-Level Access[/bold blue]\n[dim]Using socialmapper's main API interface[/dim]",
        border_style="blue"
    ))
    
    # Show available functions
    neighbor_functions = [attr for attr in dir(socialmapper) if 'neighbor' in attr.lower() or attr.startswith('get_')]
    
    functions_table = Table(title="📋 Available Functions at Package Level", box=box.ROUNDED)
    functions_table.add_column("Function", style="cyan", no_wrap=True)
    functions_table.add_column("Full Name", style="white")
    
    for func in neighbor_functions:
        functions_table.add_row("✓", f"socialmapper.{func}")
    
    console.print(functions_table)
    
    # Example usage
    with console.status("[bold green]Fetching neighbor data..."):
        nc_neighbors = socialmapper.get_neighboring_states('37')
        wake_neighbors = socialmapper.get_neighboring_counties('37183')
    
    usage_table = Table(title="📍 Example Usage Results", box=box.ROUNDED)
    usage_table.add_column("Query", style="yellow")
    usage_table.add_column("Result", style="green")
    usage_table.add_column("Count", style="magenta", justify="right")
    
    usage_table.add_row(
        "NC neighboring states",
        str(nc_neighbors),
        str(len(nc_neighbors))
    )
    usage_table.add_row(
        "Wake County neighbors",
        f"Found neighboring counties",
        str(len(wake_neighbors))
    )
    
    console.print(usage_table)

def demo_dedicated_module_access():
    """Demonstrate using the dedicated neighbors module."""
    
    console.print(Panel.fit(
        "[bold green]2. Dedicated Neighbors Module[/bold green]\n[dim]Direct access to specialized neighbor functions[/dim]",
        border_style="green"
    ))
    
    # State neighbors table
    state_table = Table(title="🏛️ State Neighbors (with abbreviations)", box=box.ROUNDED)
    state_table.add_column("State", style="cyan")
    state_table.add_column("Neighbors", style="white")
    state_table.add_column("Count", style="magenta", justify="right")
    
    states_to_test = [('NC', 'North Carolina'), ('CA', 'California')]
    
    for abbr, name in track(states_to_test, description="[green]Getting state neighbors..."):
        time.sleep(0.2)  # Small delay for demo effect
        neighbors_list = neighbors.get_neighboring_states_by_abbr(abbr)
        state_table.add_row(
            f"{abbr} ({name})",
            ", ".join(neighbors_list),
            str(len(neighbors_list))
        )
    
    console.print(state_table)
    
    # County neighbors table
    county_table = Table(title="🏘️ County Neighbors", box=box.ROUNDED)
    county_table.add_column("County", style="cyan")
    county_table.add_column("State", style="yellow")
    county_table.add_column("Neighbor Count", style="magenta", justify="right")
    
    counties_to_test = [
        ('37', '183', 'Wake County, NC'),
        ('06', '037', 'Los Angeles County, CA')
    ]
    
    for state_fips, county_fips, name in track(counties_to_test, description="[green]Getting county neighbors..."):
        time.sleep(0.2)
        county_neighbors = neighbors.get_neighboring_counties(state_fips, county_fips)
        county_table.add_row(name, state_fips, str(len(county_neighbors)))
    
    console.print(county_table)
    
    # Point geocoding
    geocoding_table = Table(title="📍 Point Geocoding", box=box.ROUNDED)
    geocoding_table.add_column("Location", style="cyan")
    geocoding_table.add_column("Coordinates", style="yellow")
    geocoding_table.add_column("State FIPS", style="green")
    geocoding_table.add_column("County FIPS", style="blue")
    
    locations = [
        (35.7796, -78.6382, "Raleigh, NC"),
        (34.0522, -118.2437, "Los Angeles, CA")
    ]
    
    for lat, lon, name in track(locations, description="[green]Geocoding points..."):
        time.sleep(0.2)
        geo_info = neighbors.get_geography_from_point(lat, lon)
        geocoding_table.add_row(
            name,
            f"{lat:.4f}, {lon:.4f}",
            geo_info['state_fips'],
            geo_info['county_fips']
        )
    
    console.print(geocoding_table)
    
    # Database statistics
    with console.status("[bold blue]Gathering database statistics..."):
        stats = neighbors.get_statistics()
    
    stats_panel = Panel(
        f"""[bold cyan]Database Statistics:[/bold cyan]
        
• [yellow]State relationships:[/yellow] [bold green]{stats['state_relationships']:,}[/bold green]
• [yellow]County relationships:[/yellow] [bold green]{stats['county_relationships']:,}[/bold green]
• [yellow]Cross-state county relationships:[/yellow] [bold green]{stats['cross_state_county_relationships']:,}[/bold green]
• [yellow]States with data:[/yellow] [bold green]{stats['states_with_county_data']}[/bold green]""",
        title="📊 Neighbor Database Stats",
        border_style="cyan"
    )
    console.print(stats_panel)

def demo_census_module_access():
    """Demonstrate accessing through the census module."""
    
    console.print(Panel.fit(
        "[bold magenta]3. Census Module Access[/bold magenta]\n[dim]Original API location for backward compatibility[/dim]",
        border_style="magenta"
    ))
    
    census_table = Table(title="🔧 Original Census API Access", box=box.ROUNDED)
    census_table.add_column("Function", style="cyan")
    census_table.add_column("Input", style="yellow")
    census_table.add_column("Result", style="green")
    census_table.add_column("Count", style="magenta", justify="right")
    
    with console.status("[bold magenta]Using census module functions..."):
        # Texas neighbors
        tx_neighbors = get_neighboring_states('48')
        
        # Harris County neighbors (census module uses full county FIPS)
        harris_neighbors = get_neighboring_counties('48201')
    
    census_table.add_row(
        "get_neighboring_states",
        "Texas (FIPS: 48)",
        str(tx_neighbors),
        str(len(tx_neighbors))
    )
    census_table.add_row(
        "get_neighboring_counties",
        "Harris County, TX (48201)",
        f"Neighboring counties found",
        str(len(harris_neighbors))
    )
    
    console.print(census_table)

def demo_poi_batch_processing():
    """Demonstrate POI batch processing capabilities."""
    
    console.print(Panel.fit(
        "[bold red]4. POI Batch Processing[/bold red]\n[dim]Processing multiple points of interest efficiently[/dim]",
        border_style="red"
    ))
    
    # Sample POIs
    pois = [
        {'lat': 35.7796, 'lon': -78.6382, 'name': 'Raleigh, NC'},
        {'lat': 35.2271, 'lon': -80.8431, 'name': 'Charlotte, NC'},
        {'lat': 34.0522, 'lon': -118.2437, 'name': 'Los Angeles, CA'},
        {'lat': 37.7749, 'lon': -122.4194, 'name': 'San Francisco, CA'},
        {'lat': 29.7604, 'lon': -95.3698, 'name': 'Houston, TX'},
        {'lat': 32.7767, 'lon': -96.7970, 'name': 'Dallas, TX'},
    ]
    
    # POI table
    poi_table = Table(title=f"✅ Processing {len(pois)} POIs", box=box.ROUNDED)
    poi_table.add_column("POI", style="cyan")
    poi_table.add_column("Coordinates", style="yellow")
    poi_table.add_column("Status", style="green")
    
    for poi in pois:
        poi_table.add_row(
            poi['name'],
            f"{poi['lat']:.4f}, {poi['lon']:.4f}",
            "✓ Ready"
        )
    
    console.print(poi_table)
    
    # Process counties
    with console.status("[bold red]Processing counties from POIs..."):
        counties_only = neighbors.get_counties_from_pois(pois, include_neighbors=False)
        counties_with_neighbors = neighbors.get_counties_from_pois(pois, include_neighbors=True)
    
    # Results table
    results_table = Table(title="📍 County Processing Results", box=box.ROUNDED)
    results_table.add_column("Processing Type", style="cyan")
    results_table.add_column("Counties Found", style="magenta", justify="right")
    results_table.add_column("Details", style="white")
    
    results_table.add_row(
        "POI locations only",
        str(len(counties_only)),
        "Direct county matches"
    )
    results_table.add_row(
        "Including neighbors",
        str(len(counties_with_neighbors)),
        f"Expansion factor: {len(counties_with_neighbors) / len(counties_only):.1f}x"
    )
    
    console.print(results_table)
    
    # County details table
    county_details = Table(title="🌐 County Details (POI locations)", box=box.ROUNDED)
    county_details.add_column("State", style="cyan")
    county_details.add_column("County FIPS", style="yellow")
    county_details.add_column("State-County", style="green")
    
    for state_fips, county_fips in counties_only:
        state_abbr = neighbors.get_state_abbr(state_fips)
        county_details.add_row(state_abbr, county_fips, f"{state_abbr}-{county_fips}")
    
    console.print(county_details)

def demo_convenience_functions():
    """Demonstrate convenience functions."""
    
    console.print(Panel.fit(
        "[bold yellow]5. Convenience Functions[/bold yellow]\n[dim]State code conversions and reference data[/dim]",
        border_style="yellow"
    ))
    
    # FIPS to abbreviation
    fips_table = Table(title="🔄 FIPS to Abbreviation", box=box.ROUNDED)
    fips_table.add_column("FIPS Code", style="cyan")
    fips_table.add_column("State Abbreviation", style="green")
    fips_table.add_column("Status", style="yellow")
    
    test_fips = ['37', '06', '48', '12', '36']
    for fips in track(test_fips, description="[yellow]Converting FIPS codes..."):
        time.sleep(0.1)
        abbr = neighbors.get_state_abbr(fips)
        fips_table.add_row(fips, abbr, "✓ Converted")
    
    console.print(fips_table)
    
    # Abbreviation to FIPS
    abbr_table = Table(title="🔄 Abbreviation to FIPS", box=box.ROUNDED)
    abbr_table.add_column("State Abbreviation", style="green")
    abbr_table.add_column("FIPS Code", style="cyan")
    abbr_table.add_column("Status", style="yellow")
    
    test_abbrs = ['NC', 'CA', 'TX', 'FL', 'NY']
    for abbr in track(test_abbrs, description="[yellow]Converting abbreviations..."):
        time.sleep(0.1)
        fips = neighbors.get_state_fips(abbr)
        abbr_table.add_row(abbr, fips, "✓ Converted")
    
    console.print(abbr_table)
    
    # Reference data
    reference_panel = Panel(
        f"""[bold yellow]Reference Data Available:[/bold yellow]
        
• [cyan]STATE_FIPS_CODES:[/cyan] [bold green]{len(neighbors.STATE_FIPS_CODES)}[/bold green] states
• [cyan]FIPS_TO_STATE:[/cyan] [bold green]{len(neighbors.FIPS_TO_STATE)}[/bold green] mappings

[dim]These dictionaries provide fast lookups for state code conversions.[/dim]""",
        title="📚 Reference Dictionaries",
        border_style="yellow"
    )
    console.print(reference_panel)

def main():
    """Run all demonstrations."""
    
    # Header
    header = Panel(
        "[bold blue]🗺️  SocialMapper Neighbors API Usage Examples[/bold blue]\n\n"
        "[dim]This script demonstrates multiple ways to access neighbor functionality\n"
        "independently of the main SocialMapper workflow.[/dim]",
        title="🚀 Neighbor API Demo",
        subtitle="Ready to explore geographic relationships",
        border_style="blue"
    )
    console.print(header)
    
    try:
        # Demo 1: Package-level access
        demo_package_level_access()
        console.print()
        
        # Demo 2: Dedicated module
        demo_dedicated_module_access()
        console.print()
        
        # Demo 3: Census module (original)
        demo_census_module_access()
        console.print()
        
        # Demo 4: POI batch processing
        demo_poi_batch_processing()
        console.print()
        
        # Demo 5: Convenience functions
        demo_convenience_functions()
        console.print()
        
        # Success summary
        success_panel = Panel(
            "[bold green]🎉 All demonstrations completed successfully![/bold green]\n\n"
            "[bold white]Summary of access methods:[/bold white]\n"
            "[cyan]1. Package level:[/cyan]     [white]import socialmapper[/white]\n"
            "[cyan]2. Dedicated module:[/cyan]  [white]import socialmapper.neighbors[/white]\n"
            "[cyan]3. Census module:[/cyan]     [white]from socialmapper.census import ...[/white]\n"
            "[cyan]4. Neighbors module:[/cyan]  [white]from socialmapper.neighbors import ...[/white]\n"
            "[cyan]5. All methods provide the same functionality with different APIs[/cyan]",
            title="✨ Demo Complete",
            border_style="green"
        )
        console.print(success_panel)
        
        return True
        
    except Exception as e:
        error_panel = Panel(
            f"[bold red]❌ Demo failed:[/bold red] [white]{e}[/white]\n\n"
            "[dim]Check the error details above for debugging information.[/dim]",
            title="🚨 Error",
            border_style="red"
        )
        console.print(error_panel)
        
        import traceback
        console.print("\n[bold red]Traceback:[/bold red]")
        console.print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 