#!/usr/bin/env python3
"""
Custom benchmark script for comparing county-based and state-based block group selection.

This script allows you to run benchmarks with POIs from your own JSON or CSV files.
"""
import os
import sys
import json
import csv
import argparse
from pathlib import Path
from benchmark_block_groups import (
    run_benchmarks,
    save_results,
    create_summary,
    plot_results
)
from community_mapper import parse_custom_coordinates

def load_custom_poi_data(file_path):
    """Load POI data from a JSON or CSV file."""
    print(f"Loading POI data from {file_path}")
    try:
        poi_data = parse_custom_coordinates(file_path)
        print(f"Successfully loaded {len(poi_data['pois'])} POIs from {file_path}")
        return poi_data
    except Exception as e:
        print(f"Error loading POI data: {e}")
        sys.exit(1)

def create_test_case(poi_data, name, travel_time=15):
    """Create a test case dictionary from POI data."""
    return {
        "name": name,
        "poi_data": poi_data,
        "travel_time": travel_time
    }

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run custom benchmark for county-based vs state-based block group selection"
    )
    parser.add_argument(
        "poi_file",
        type=str,
        help="Path to JSON or CSV file with POI coordinates"
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Name for the test case (defaults to the filename)"
    )
    parser.add_argument(
        "--travel-time",
        type=int,
        default=15,
        help="Travel time in minutes (default: 15)"
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Number of times to repeat the test (default: 1)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="custom_benchmark_results",
        help="Base output filename (without extension)"
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the custom benchmark script."""
    args = parse_arguments()
    
    print("=" * 80)
    print("Custom Block Group Selection Method Benchmark")
    print("=" * 80)
    
    # Load POI data
    poi_data = load_custom_poi_data(args.poi_file)
    
    # Create a name for the test case if not provided
    if args.name is None:
        file_name = Path(args.poi_file).stem
        args.name = f"Custom Test: {file_name}"
    
    # Create a test case
    test_case = create_test_case(poi_data, args.name, args.travel_time)
    
    print(f"Running benchmark for '{args.name}'")
    print(f"Travel time: {args.travel_time} minutes")
    print(f"Will repeat {args.repeat} time(s)")
    
    # Run the benchmark
    results = run_benchmarks([test_case], repeat=args.repeat)
    
    # Save the raw results
    save_results(results, f"{args.output}.json")
    
    # Create and display summary
    summary, pivot = create_summary(results)
    print("\nSummary:")
    print(summary)
    
    print("\nMethod comparison (mean execution time in seconds):")
    print(pivot)
    
    # Plot the results
    plot_results(results, f"{args.output}.png")

if __name__ == "__main__":
    main() 