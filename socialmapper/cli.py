#!/usr/bin/env python3
"""Command-line interface for SocialMapper."""

# Load environment variables from .env file as early as possible
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available - continue without it
    pass

import argparse
import os
import sys
import time

from rich import box
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .core import run_socialmapper
from .progress import get_progress_tracker
from .states import StateFormat, normalize_state
from .ui.rich_console import (
    console,
    get_logger,
    setup_rich_logging,
)
from .util import CENSUS_VARIABLE_MAPPING

# Setup Rich logging for the entire application
setup_rich_logging(level="INFO", show_time=True, show_path=False)
logger = get_logger(__name__)


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
    input_group = parser.add_mutually_exclusive_group(
        required=False
    )  # Made not required for testing
    input_group.add_argument(
        "--custom-coords", help="Path to custom coordinates file (CSV or JSON)"
    )
    input_group.add_argument("--poi", action="store_true", help="Use direct POI parameters")

    # POI parameters (used when --poi is specified)
    poi_group = parser.add_argument_group("POI Parameters (used with --poi)")
    poi_group.add_argument("--geocode-area", help="Area to search within (city/town name)")
    poi_group.add_argument(
        "--city", help="City to search within (defaults to geocode-area if not specified)"
    )
    poi_group.add_argument("--poi-type", help="Type of POI (e.g., 'amenity', 'leisure')")
    poi_group.add_argument("--poi-name", help="Name of POI (e.g., 'library', 'park')")
    poi_group.add_argument("--state", help="State name or abbreviation")

    # Address Lookup Options
    parser.add_argument(
        "--addresses", action="store_true", help="Enable address-based analysis using geocoding"
    )
    parser.add_argument("--address-file", type=str, help="CSV file containing addresses to geocode")
    parser.add_argument(
        "--address-column",
        type=str,
        default="address",
        help="Column name containing addresses (default: 'address')",
    )
    parser.add_argument(
        "--geocoding-provider",
        choices=["nominatim", "census", "auto"],
        default="auto",
        help="Geocoding provider preference",
    )
    parser.add_argument(
        "--geocoding-quality",
        choices=["exact", "interpolated", "centroid", "approximate"],
        default="centroid",
        help="Minimum geocoding quality threshold",
    )

    # General parameters
    parser.add_argument("--travel-time", type=int, default=15, help="Travel time in minutes")
    parser.add_argument(
        "--geographic-level",
        choices=["block-group", "zcta"],
        default="block-group",
        help="Geographic unit for analysis: 'block-group' (default) or 'zcta' (ZIP Code Tabulation Areas)",
    )
    parser.add_argument(
        "--census-variables",
        nargs="+",
        default=["total_population"],
        help="Census variables to retrieve (e.g. total_population median_household_income)",
    )
    parser.add_argument(
        "--api-key", help="Census API key (optional if set as environment variable)"
    )
    parser.add_argument(
        "--list-variables", action="store_true", help="List available census variables and exit"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print what would be done without actually doing it"
    )

    # Output type controls - only CSV enabled by default
    parser.add_argument(
        "--export-csv",
        action="store_true",
        default=True,
        help="Export census data to CSV format (default: enabled)",
    )
    parser.add_argument(
        "--no-export-csv",
        action="store_false",
        dest="export_csv",
        help="Disable exporting census data to CSV format",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Custom output directory for all generated files (default: 'output')",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"SocialMapper {__version__}",
        help="Show version and exit",
    )

    args = parser.parse_args()

    # If not testing migration and not listing variables, require input method
    if not args.test_migration and not args.list_variables and not args.dry_run:
        if not args.custom_coords and not args.poi and not args.addresses:
            parser.error(
                "one of the arguments --custom-coords --poi --addresses is required (unless using --test-migration, --list-variables, or --dry-run)"
            )

        # Validate address arguments if --addresses is specified
        if args.addresses and not args.address_file:
            parser.error("When using --addresses, you must specify --address-file")

    # Validate POI arguments if --poi is specified for querying OSM
    if args.poi:
        if not all([args.geocode_area, args.poi_type, args.poi_name]):
            parser.error(
                "When using --poi, you must specify --geocode-area, --poi-type, and --poi-name"
            )

    return args



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
        console.print(
            "\n[bold]Usage example:[/bold] --census-variables total_population median_household_income"
        )
        sys.exit(0)


    # Create the output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Print beautiful banner using Rich
    tracker = get_progress_tracker()

    # Print banner info using Rich console
    console.print("\n[bold cyan]🌍 SocialMapper[/bold cyan]")
    console.print("[dim]End-to-end tool for mapping community resources[/dim]")
    console.print(
        "[dim]Analyzing community connections through demographics and points of interest[/dim]\n"
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

        console.print(table)
        console.print(
            "\n[bold red]Note:[/bold red] This is a dry run - no operations will be performed."
        )
        sys.exit(0)

    # Execute the full process
    console.print("\n[bold green]🚀 Starting SocialMapper Analysis[/bold green]")
    start_time = time.time()

    try:
        # Execute the full pipeline
        if args.poi:
            # Normalize state to abbreviation
            state_abbr = (
                normalize_state(args.state, to_format=StateFormat.ABBREVIATION)
                if args.state
                else None
            )

            # Use direct POI parameters
            run_socialmapper(
                geocode_area=args.geocode_area,
                state=state_abbr,
                city=args.city or args.geocode_area,  # Default to geocode_area if city not provided
                poi_type=args.poi_type,
                poi_name=args.poi_name,
                travel_time=args.travel_time,
                geographic_level=args.geographic_level,
                census_variables=args.census_variables,
                api_key=args.api_key,
                output_dir=args.output_dir,
                export_csv=args.export_csv,
            )
        elif args.addresses:
            # Handle address-based analysis
            import pandas as pd

            from .geocoding import (
                AddressProvider,
                AddressQuality,
                GeocodingConfig,
                addresses_to_poi_format,
            )

            console.print(
                f"[bold cyan]📍 Processing addresses from {args.address_file}[/bold cyan]"
            )

            # Load addresses from CSV
            df = pd.read_csv(args.address_file)
            if args.address_column not in df.columns:
                raise ValueError(f"Column '{args.address_column}' not found in {args.address_file}")

            addresses = df[args.address_column].tolist()

            # Configure geocoding
            config = GeocodingConfig(
                primary_provider=(
                    AddressProvider.NOMINATIM
                    if args.geocoding_provider == "nominatim"
                    else (
                        AddressProvider.CENSUS
                        if args.geocoding_provider == "census"
                        else AddressProvider.NOMINATIM
                    )
                ),  # auto defaults to Nominatim
                min_quality_threshold=AddressQuality(args.geocoding_quality),
            )

            # Geocode addresses to POI format
            console.print(f"[bold yellow]🔍 Geocoding {len(addresses)} addresses...[/bold yellow]")
            poi_data = addresses_to_poi_format(addresses, config)

            # Create a temporary file for the geocoded coordinates

            temp_file = os.path.join(args.output_dir, "geocoded_addresses.csv")
            os.makedirs(args.output_dir, exist_ok=True)

            # Convert to CSV format for SocialMapper
            poi_csv_data = []
            for poi in poi_data:
                poi_csv_data.append(
                    {
                        "name": poi["name"],
                        "lat": poi["lat"],
                        "lon": poi["lon"],
                        "type": poi.get("type", "address"),
                    }
                )

            import pandas as pd

            df = pd.DataFrame(poi_csv_data)
            df.to_csv(temp_file, index=False)

            console.print(f"[bold green]✅ Saved geocoded addresses to {temp_file}[/bold green]")

            # Run SocialMapper with the geocoded coordinates
            run_socialmapper(
                custom_coords=temp_file,
                travel_time=args.travel_time,
                geographic_level=args.geographic_level,
                census_variables=args.census_variables,
                api_key=args.api_key,
                output_dir=args.output_dir,
                export_csv=args.export_csv,
            )
        else:
            # Use custom coordinates file
            run_socialmapper(
                custom_coords=args.custom_coords,
                travel_time=args.travel_time,
                geographic_level=args.geographic_level,
                census_variables=args.census_variables,
                api_key=args.api_key,
                output_dir=args.output_dir,
                export_csv=args.export_csv,
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
            border_style="green",
        )
        console.print(success_panel)

    except Exception as e:
        # Rich will automatically handle the traceback beautifully
        error_panel = Panel(
            f"[bold red]❌ SocialMapper encountered an error:[/bold red]\n[red]{str(e)}[/red]",
            title="💥 Error",
            box=box.ROUNDED,
            border_style="red",
        )
        console.print(error_panel)
        sys.exit(1)


if __name__ == "__main__":
    main()
