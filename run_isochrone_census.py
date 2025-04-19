#!/usr/bin/env python3
"""
Script to run the isochrone-to-census-blocks analysis.
"""
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Import environment setup utilities
from setup_env import activate_venv, create_directories

def run_analysis(isochrone_file, state_fips, output_file=None):
    """Run the isochrone-to-census-blocks analysis."""
    # These imports are done inside the function to ensure we're using the virtual env
    from poi_query.blockgroups import isochrone_to_block_groups
    
    # Load environment variables (for Census API key)
    load_dotenv()
    
    # Run the analysis
    result = isochrone_to_block_groups(
        isochrone_path=isochrone_file,
        state_fips=state_fips,
        output_path=output_file
    )
    
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run isochrone-to-census-blocks analysis")
    parser.add_argument("isochrone", help="Path to isochrone GeoJSON file")
    parser.add_argument("--states", required=True, nargs="+", help="State FIPS codes")
    parser.add_argument("--output", help="Output GeoJSON file path")
    
    args = parser.parse_args()
    
    # Ensure we have required directories
    create_directories()
    
    # Ensure we're running in the virtual environment
    activate_venv()
    
    # Run analysis (this code runs in the virtual environment)
    result = run_analysis(
        isochrone_file=args.isochrone,
        state_fips=args.states,
        output_file=args.output
    )
    
    print(f"Found {len(result)} intersecting block groups")
    if args.output:
        print(f"Results saved to {args.output}")
    else:
        # Display a sample of the results
        print("\nSample of results:")
        print(result.head(3)) 