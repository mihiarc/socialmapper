#!/usr/bin/env python3
"""Command-line interface for SocialMapper."""

import argparse
import logging
import sys
import time
import traceback
import os

from . import __version__
from .core import run_socialmapper, setup_directory
from .util import CENSUS_VARIABLE_MAPPING, normalize_census_variable
from .states import normalize_state, StateFormat
from .ui.rich_progress import get_rich_tracker, console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.traceback import install as install_rich_traceback

# Install Rich traceback handling
install_rich_traceback(show_locals=True)

# Configure basic logging with Rich integration
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise, Rich will handle user feedback
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description=f"SocialMapper v{__version__}: Tool for mapping community resources and demographics"
    )
    
    # Input source group
    input_group = parser.add_mutually_exclusive_group(required=False)  # Made not required for testing
    input_group.add_argument("--custom-coords", help="Path to custom coordinates file (CSV or JSON)")
    input_group.add_argument("--poi", action="store_true", help="Use direct POI parameters")
    
    # POI parameters (used when --poi is specified)
    poi_group = parser.add_argument_group("POI Parameters (used with --poi)")
    poi_group.add_argument("--geocode-area", help="Area to search within (city/town name)")
    poi_group.add_argument("--city", help="City to search within (defaults to geocode-area if not specified)")
    poi_group.add_argument("--poi-type", help="Type of POI (e.g., 'amenity', 'leisure')")
    poi_group.add_argument("--poi-name", help="Name of POI (e.g., 'library', 'park')")
    poi_group.add_argument("--state", help="State name or abbreviation")
    
    # Address Lookup Options
    parser.add_argument("--addresses", action="store_true",
                        help="Enable address-based analysis using geocoding")
    parser.add_argument("--address-file", type=str,
                        help="CSV file containing addresses to geocode")
    parser.add_argument("--address-column", type=str, default="address",
                        help="Column name containing addresses (default: 'address')")
    parser.add_argument("--geocoding-provider", choices=["nominatim", "census", "auto"], 
                        default="auto", help="Geocoding provider preference")
    parser.add_argument("--geocoding-quality", choices=["exact", "interpolated", "centroid", "approximate"],
                        default="centroid", help="Minimum geocoding quality threshold")
    
    # General parameters
    parser.add_argument("--travel-time", type=int, default=15, help="Travel time in minutes")
    parser.add_argument(
        "--census-variables", 
        nargs="+", 
        default=["total_population"], 
        help="Census variables to retrieve (e.g. total_population median_household_income)"
    )
    parser.add_argument("--api-key", help="Census API key (optional if set as environment variable)")
    parser.add_argument("--list-variables", action="store_true", help="List available census variables and exit")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without actually doing it")
    parser.add_argument("--test-migration", action="store_true", help="Test Plotly migration and backend compatibility")
    
    # Output type controls - only CSV enabled by default
    parser.add_argument(
        "--export-csv", 
        action="store_true", 
        default=True, 
        help="Export census data to CSV format (default: enabled)"
    )
    parser.add_argument(
        "--no-export-csv", 
        action="store_false", 
        dest="export_csv", 
        help="Disable exporting census data to CSV format"
    )
    parser.add_argument(
        "--export-maps", 
        action="store_true", 
        default=False, 
        help="Generate map visualizations (default: disabled)"
    )
    parser.add_argument(
        "--map-backend",
        choices=["plotly", "folium", "both"],
        default="plotly",
        help="Map visualization backend (default: plotly)"
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Custom output directory for all generated files (default: 'output')"
    )
    parser.add_argument(
        "--version", 
        action="version", 
        version=f"SocialMapper {__version__}",
        help="Show version and exit"
    )
    
    args = parser.parse_args()
    
    # If not testing migration and not listing variables, require input method
    if not args.test_migration and not args.list_variables and not args.dry_run:
        if not args.custom_coords and not args.poi:
            parser.error("one of the arguments --custom-coords --poi is required (unless using --test-migration, --list-variables, or --dry-run)")
    
    # Validate POI arguments if --poi is specified for querying OSM
    if args.poi:
        if not all([args.geocode_area, args.poi_type, args.poi_name]):
            parser.error("When using --poi, you must specify --geocode-area, --poi-type, and --poi-name")
    
    return args

def _test_plotly_migration():
    """Test Plotly migration and backend compatibility."""
    console.print("\n[bold cyan]🧪 Testing Plotly Migration[/bold cyan]")
    console.print("=" * 60)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Import tests
    console.print("\n[bold]📦 Testing imports...[/bold]")
    total_tests += 1
    
    try:
        import plotly.graph_objects as go
        from socialmapper.visualization.plotly_map import create_plotly_map
        console.print("✅ Plotly modules imported successfully")
        tests_passed += 1
    except Exception as e:
        console.print(f"❌ Import failed: {e}")
    
    # Test 2: Map creation with sample data
    console.print("\n[bold]🗺️ Testing map creation...[/bold]")
    total_tests += 1
    
    try:
        import geopandas as gpd
        import pandas as pd
        from shapely.geometry import Point
        import numpy as np
        
        # Create minimal sample data
        np.random.seed(42)
        sample_data = {
            'GEOID': ['370630001', '370630002', '370630003'],
            'total_population': [1200, 1800, 950],
            'geometry': [Point(-78.8, 35.55), Point(-78.79, 35.56), Point(-78.81, 35.54)]
        }
        
        census_gdf = gpd.GeoDataFrame(sample_data, crs="EPSG:4326")
        
        fig = create_plotly_map(
            census_data=census_gdf,
            variable="total_population",
            title="Test Map",
            height=400
        )
        
        # Verify modern API usage
        if fig.data[0].type == 'scattermap':
            console.print("✅ Map created successfully with modern Scattermap API")
            tests_passed += 1
        else:
            console.print(f"⚠️ Unexpected trace type: {fig.data[0].type}")
            
    except Exception as e:
        console.print(f"❌ Map creation failed: {e}")
    
    # Test 3: CLI integration
    console.print("\n[bold]🔧 Testing CLI integration...[/bold]")
    total_tests += 1
    
    try:
        import inspect
        sig = inspect.signature(run_socialmapper)
        if 'map_backend' in sig.parameters:
            console.print("✅ map_backend parameter available in CLI")
            tests_passed += 1
        else:
            console.print("❌ map_backend parameter missing from CLI")
    except Exception as e:
        console.print(f"❌ CLI integration test failed: {e}")
    
    # Test 4: Backend comparison
    console.print("\n[bold]⚖️ Backend comparison...[/bold]")
    
    # Create comparison table
    comparison_table = Table(title="🗺️ Map Backend Comparison", box=box.ROUNDED)
    comparison_table.add_column("Feature", style="cyan")
    comparison_table.add_column("Plotly", style="green")
    comparison_table.add_column("Folium", style="yellow")
    
    comparison_data = [
        ("Performance", "⭐⭐⭐⭐⭐", "⭐⭐⭐"),
        ("Interactivity", "⭐⭐⭐⭐⭐", "⭐⭐⭐"),
        ("Mobile Support", "⭐⭐⭐⭐⭐", "⭐⭐⭐"),
        ("Learning Curve", "⭐⭐⭐", "⭐⭐⭐⭐⭐"),
        ("API Status", "Modern", "Stable")
    ]
    
    for feature, plotly_rating, folium_rating in comparison_data:
        comparison_table.add_row(feature, plotly_rating, folium_rating)
    
    console.print(comparison_table)
    
    # Summary
    console.print("\n" + "=" * 60)
    
    if tests_passed == total_tests:
        success_panel = Panel(
            f"[bold green]🎉 All {tests_passed}/{total_tests} tests passed![/bold green]\n"
            "[green]Plotly migration is successful and ready to use.[/green]\n\n"
            "[bold]Recommended usage:[/bold]\n"
            "[cyan]socialmapper --poi --geocode-area 'Fuquay-Varina' --poi-type amenity --poi-name library --export-maps --map-backend plotly[/cyan]",
            title="✅ Migration Test Results",
            box=box.ROUNDED,
            border_style="green"
        )
    else:
        failed_tests = total_tests - tests_passed
        warning_panel = Panel(
            f"[bold yellow]⚠️ {tests_passed}/{total_tests} tests passed, {failed_tests} failed[/bold yellow]\n"
            "[yellow]Some migration components may need attention.[/yellow]\n\n"
            "[bold]Fallback usage:[/bold]\n"
            "[cyan]socialmapper --poi --geocode-area 'Fuquay-Varina' --poi-type amenity --poi-name library --export-maps --map-backend folium[/cyan]",
            title="⚠️ Migration Test Results",
            box=box.ROUNDED,
            border_style="yellow"
        )
    
    console.print(success_panel if tests_passed == total_tests else warning_panel)

def main():
    """Main entry point for the application."""
    args = parse_arguments()
    
    # If user just wants to list available variables
    if args.list_variables:
        table = Table(title="📊 Available Census Variables", box=box.ROUNDED)
        table.add_column("Variable Name", style="cyan", no_wrap=True)
        table.add_column("Census Code", style="green")
        
        for code, name in sorted(CENSUS_VARIABLE_MAPPING.items()):
            table.add_row(name, code)
        
        console.print(table)
        console.print("\n[bold]Usage example:[/bold] --census-variables total_population median_household_income")
        sys.exit(0)
    
    # If user wants to test the Plotly migration
    if args.test_migration:
        _test_plotly_migration()
        sys.exit(0)
        
    # Create the output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Print beautiful banner using Rich
    tracker = get_rich_tracker()
    tracker.print_banner(
        "End-to-end tool for mapping community resources",
        "Analyzing community connections through demographics and points of interest"
    )
    
    # If dry-run, just print what would be done and exit
    if args.dry_run:
        # Create dry run information table
        table = Table(title="🔍 Dry Run - Planned Operations", box=box.ROUNDED)
        table.add_column("Parameter", style="cyan", no_wrap=True)
        table.add_column("Value", style="yellow")
        
        if args.poi:
            table.add_row("Mode", "POI Query")
            table.add_row("Area", args.geocode_area)
            table.add_row("POI Type", args.poi_type)
            table.add_row("POI Name", args.poi_name)
            if args.state:
                table.add_row("State", args.state)
        elif args.addresses:
            table.add_row("Mode", "Address Geocoding")
            table.add_row("Address File", args.address_file)
            table.add_row("Address Column", args.address_column)
            table.add_row("Geocoding Provider", args.geocoding_provider)
            table.add_row("Quality Threshold", args.geocoding_quality)
        else:
            table.add_row("Mode", "Custom Coordinates")
            table.add_row("Coordinates File", args.custom_coords)
        
        table.add_row("Travel Time", f"{args.travel_time} minutes")
        table.add_row("Census Variables", ", ".join(args.census_variables))
        table.add_row("Output Directory", args.output_dir)
        table.add_section()
        table.add_row("Export CSV", "✅ Yes" if args.export_csv else "❌ No")
        table.add_row("Export Maps", "✅ Yes" if args.export_maps else "❌ No")
        if args.export_maps:
            table.add_row("Map Backend", args.map_backend)
        
        console.print(table)
        console.print("\n[bold red]Note:[/bold red] This is a dry run - no operations will be performed.")
        sys.exit(0)
    
    # Execute the full process
    console.print("\n[bold green]🚀 Starting SocialMapper Analysis[/bold green]")
    start_time = time.time()
    
    try:
        # Execute the full pipeline
        if args.poi:
            # Normalize state to abbreviation
            state_abbr = normalize_state(args.state, to_format=StateFormat.ABBREVIATION) if args.state else None
            
            # Use direct POI parameters
            run_socialmapper(
                geocode_area=args.geocode_area,
                state=state_abbr,
                city=args.city or args.geocode_area,  # Default to geocode_area if city not provided
                poi_type=args.poi_type,
                poi_name=args.poi_name,
                travel_time=args.travel_time,
                census_variables=args.census_variables,
                api_key=args.api_key,
                output_dir=args.output_dir,
                export_csv=args.export_csv,
                export_maps=args.export_maps,
                map_backend=args.map_backend
            )
        elif args.addresses:
            # Handle address-based analysis
            from .geocoding import addresses_to_poi_format, GeocodingConfig, AddressProvider, AddressQuality
            import pandas as pd
            
            console.print(f"[bold cyan]📍 Processing addresses from {args.address_file}[/bold cyan]")
            
            # Load addresses from CSV
            df = pd.read_csv(args.address_file)
            if args.address_column not in df.columns:
                raise ValueError(f"Column '{args.address_column}' not found in {args.address_file}")
            
            addresses = df[args.address_column].tolist()
            
            # Configure geocoding
            config = GeocodingConfig(
                primary_provider=AddressProvider.NOMINATIM if args.geocoding_provider == "nominatim" else 
                               AddressProvider.CENSUS if args.geocoding_provider == "census" else
                               AddressProvider.NOMINATIM,  # auto defaults to Nominatim
                min_quality_threshold=AddressQuality(args.geocoding_quality)
            )
            
            # Geocode addresses to POI format
            console.print(f"[bold yellow]🔍 Geocoding {len(addresses)} addresses...[/bold yellow]")
            poi_data = addresses_to_poi_format(addresses, config)
            
            # Create a temporary file for the geocoded coordinates
            import tempfile
            import os
            
            temp_file = os.path.join(args.output_dir, "geocoded_addresses.csv")
            
            # Convert POIs to CSV format
            if poi_data['pois']:
                geocoded_df = pd.DataFrame([
                    {
                        'name': poi['name'],
                        'latitude': poi['lat'],
                        'longitude': poi['lon'],
                        'type': poi['type'],
                        'provider': poi['tags'].get('geocoding:provider'),
                        'quality': poi['tags'].get('geocoding:quality'),
                        'confidence': poi['tags'].get('geocoding:confidence')
                    }
                    for poi in poi_data['pois']
                ])
                geocoded_df.to_csv(temp_file, index=False)
                
                console.print(f"[green]✅ Successfully geocoded {len(poi_data['pois'])} addresses[/green]")
                console.print(f"[dim]Geocoded coordinates saved to: {temp_file}[/dim]")
                
                # Run SocialMapper with geocoded addresses
                run_socialmapper(
                    travel_time=args.travel_time,
                    census_variables=args.census_variables,
                    api_key=args.api_key,
                    custom_coords_path=temp_file,
                    output_dir=args.output_dir,
                    export_csv=args.export_csv,
                    export_maps=args.export_maps,
                    map_backend=args.map_backend,
                    name_field='name',
                    type_field='type'
                )
            else:
                raise ValueError("No addresses could be successfully geocoded")
                
        else:
            # Use custom coordinates
            run_socialmapper(
                travel_time=args.travel_time,
                census_variables=args.census_variables,
                api_key=args.api_key,
                custom_coords_path=args.custom_coords,
                output_dir=args.output_dir,
                export_csv=args.export_csv,
                export_maps=args.export_maps,
                map_backend=args.map_backend
            )
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Show final summary
        tracker.print_summary()
        
        # Success message
        success_panel = Panel(
            f"[bold green]✅ SocialMapper completed successfully in {elapsed:.1f} seconds[/bold green]\n"
            f"[dim]Results available in: {args.output_dir}/[/dim]",
            title="🎉 Analysis Complete",
            box=box.ROUNDED,
            border_style="green"
        )
        console.print(success_panel)
        
    except Exception as e:
        # Rich will automatically handle the traceback beautifully
        error_panel = Panel(
            f"[bold red]❌ SocialMapper encountered an error:[/bold red]\n[red]{str(e)}[/red]",
            title="💥 Error",
            box=box.ROUNDED,
            border_style="red"
        )
        console.print(error_panel)
        sys.exit(1)

if __name__ == "__main__":
    main() 