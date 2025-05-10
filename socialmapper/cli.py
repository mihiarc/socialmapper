#!/usr/bin/env python3
"""Command-line interface for SocialMapper."""

import argparse
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional

from . import __version__
from .core import run_socialmapper, setup_directories
from .util import CENSUS_VARIABLE_MAPPING, normalize_census_variable
from .states import normalize_state, StateFormat

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
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
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--custom-coords", help="Path to custom coordinates file (CSV or JSON)")
    input_group.add_argument("--poi", action="store_true", help="Use direct POI parameters")
    
    # POI parameters (used when --poi is specified)
    poi_group = parser.add_argument_group("POI Parameters (used with --poi)")
    poi_group.add_argument("--geocode-area", help="Area to search within (city/town name)")
    poi_group.add_argument("--city", help="City to search within (defaults to geocode-area if not specified)")
    poi_group.add_argument("--poi-type", help="Type of POI (e.g., 'amenity', 'leisure')")
    poi_group.add_argument("--poi-name", help="Name of POI (e.g., 'library', 'park')")
    poi_group.add_argument("--state", help="State name or abbreviation")
    
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
    parser.add_argument(
        "--export", 
        action="store_true", 
        default=True, 
        help="Export census data to CSV format (default: enabled)"
    )
    parser.add_argument(
        "--no-export", 
        action="store_false", 
        dest="export", 
        help="Disable exporting census data to CSV format"
    )
    parser.add_argument(
        "--version", 
        action="version", 
        version=f"SocialMapper {__version__}",
        help="Show version and exit"
    )
    
    args = parser.parse_args()
    
    # Validate POI arguments if --poi is specified
    if args.poi:
        if not all([args.geocode_area, args.poi_type, args.poi_name]):
            parser.error("When using --poi, you must specify --geocode-area, --poi-type, and --poi-name")
    
    return args

def main():
    """Main entry point for the application."""
    args = parse_arguments()
    
    # If user just wants to list available variables
    if args.list_variables:
        print("\nAvailable Census Variables:")
        print("=" * 50)
        for code, name in sorted(CENSUS_VARIABLE_MAPPING.items()):
            print(f"{name:<25} {code}")
        print("\nUsage example: --census-variables total_population median_household_income")
        sys.exit(0)
        
    # Setup output directories
    output_dirs = setup_directories()
    
    # Print banner
    print("=" * 80)
    print(f"SocialMapper v{__version__}: End-to-end tool for mapping community resources")
    print("=" * 80)
    
    # If dry-run, just print what would be done and exit
    if args.dry_run:
        print("\n=== DRY RUN - SHOWING PLANNED STEPS ===")
        if args.poi:
            print(f"POI Query: {args.geocode_area} - {args.poi_type} - {args.poi_name}")
        else:
            print(f"Custom coordinates: {args.custom_coords}")
        print(f"Travel time limit: {args.travel_time} minutes")
        print(f"Census variables: {', '.join(args.census_variables)}")
        print(f"Output directories: {output_dirs}")
        print("No operations will be performed.")
        sys.exit(0)
    
    # Execute the full process
    print("\n=== Starting SocialMapper ===")
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
                export=args.export
            )
        else:
            # Use custom coordinates
            run_socialmapper(
                travel_time=args.travel_time,
                census_variables=args.census_variables,
                api_key=args.api_key,
                custom_coords_path=args.custom_coords,
                export=args.export
            )
        
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"\n=== SocialMapper Completed in {elapsed:.1f} seconds ===")
        
    except Exception as e:
        print(f"\n=== Error: {str(e)} ===")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 