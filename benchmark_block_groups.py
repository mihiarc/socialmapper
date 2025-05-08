#!/usr/bin/env python3
"""
Benchmark script to compare state-based and county-based block group selection methods.

This script runs both methods on the same data and measures execution time,
ensuring cache is cleared before each run for fair comparison.
"""
import os
import time
import json
import argparse
import shutil
import traceback
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import matplotlib.pyplot as plt

# Import SocialMapper components
from src.blockgroups import (
    isochrone_to_block_groups,
    isochrone_to_block_groups_by_county
)
from src.states import (
    normalize_state,
    StateFormat,
    get_neighboring_states
)
from src.isochrone import create_isochrones_from_poi_list

# Test cases to benchmark
TEST_CASES = [
    {
        "name": "Single POI - Small State",
        "poi_data": {
            "pois": [
                {
                    "id": "test1",
                    "name": "Test POI in RI",
                    "lat": 41.8240,
                    "lon": -71.4128,
                    "state": "RI",
                    "tags": {"amenity": "library"}
                }
            ]
        },
        "travel_time": 15
    },
    {
        "name": "Single POI - Large State",
        "poi_data": {
            "pois": [
                {
                    "id": "test2",
                    "name": "Test POI in TX",
                    "lat": 29.7604,
                    "lon": -95.3698,
                    "state": "TX",
                    "tags": {"amenity": "library"}
                }
            ]
        },
        "travel_time": 15
    },
    {
        "name": "Multiple POIs - Same State",
        "poi_data": {
            "pois": [
                {
                    "id": "test3a",
                    "name": "Test POI 1 in CA",
                    "lat": 37.7749,
                    "lon": -122.4194,
                    "state": "CA",
                    "tags": {"amenity": "library"}
                },
                {
                    "id": "test3b",
                    "name": "Test POI 2 in CA",
                    "lat": 34.0522,
                    "lon": -118.2437,
                    "state": "CA",
                    "tags": {"amenity": "library"}
                }
            ]
        },
        "travel_time": 15
    },
    {
        "name": "Multiple POIs - Different States",
        "poi_data": {
            "pois": [
                {
                    "id": "test4a",
                    "name": "Test POI in NY",
                    "lat": 40.7128,
                    "lon": -74.0060,
                    "state": "NY",
                    "tags": {"amenity": "library"}
                },
                {
                    "id": "test4b",
                    "name": "Test POI in NJ",
                    "lat": 40.7357,
                    "lon": -74.1724,
                    "state": "NJ",
                    "tags": {"amenity": "library"}
                }
            ]
        },
        "travel_time": 15
    }
]

def clear_cache():
    """Clear the cache directory to ensure fresh runs."""
    cache_dir = Path("cache")
    if cache_dir.exists():
        print(f"Clearing cache directory: {cache_dir}")
        shutil.rmtree(cache_dir)
    cache_dir.mkdir(exist_ok=True)
    print("Cache directory cleared and recreated")

def setup_temp_dirs():
    """Create temporary directories for benchmark output."""
    dirs = {
        "isochrones": "benchmark_output/isochrones",
        "block_groups": "benchmark_output/block_groups",
    }
    
    for path in dirs.values():
        Path(path).mkdir(parents=True, exist_ok=True)
    
    return dirs

def generate_isochrone(poi_data, travel_time, output_dir):
    """Generate isochrone for the given POI data."""
    isochrone_path = create_isochrones_from_poi_list(
        poi_data=poi_data,
        travel_time_limit=travel_time,
        output_dir=output_dir,
        save_individual_files=True,
        combine_results=True
    )
    return isochrone_path

def get_states_from_poi_data(poi_data):
    """Extract state abbreviations from POI data."""
    states = set()
    for poi in poi_data["pois"]:
        state = poi.get("state")
        if state:
            state_abbr = normalize_state(state, to_format=StateFormat.ABBREVIATION)
            if state_abbr:
                states.add(state_abbr)
    return list(states)

def expand_states_with_neighbors(states):
    """Add neighboring states to the list of states."""
    expanded = states.copy()
    for state in states:
        neighbors = get_neighboring_states(state)
        for neighbor in neighbors:
            if neighbor not in expanded:
                expanded.append(neighbor)
    return expanded

def benchmark_state_method(isochrone_path, poi_data, output_path):
    """Benchmark the state-based method."""
    # Get states from POI data
    states = get_states_from_poi_data(poi_data)
    
    # Add neighboring states
    expanded_states = expand_states_with_neighbors(states)
    
    # Clear cache before the test
    clear_cache()
    
    # Time the state-based method
    start_time = time.time()
    
    # Run the state-based method
    result = isochrone_to_block_groups(
        isochrone_path=isochrone_path,
        state_fips=expanded_states,
        output_path=output_path,
        api_key=None  # Use environment variable if set
    )
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Count the number of block groups
    block_group_count = len(result)
    
    return {
        "method": "state",
        "execution_time": execution_time,
        "block_group_count": block_group_count,
        "states_used": expanded_states
    }

def benchmark_county_method(isochrone_path, poi_data, output_path):
    """Benchmark the county-based method."""
    # Clear cache before the test
    clear_cache()
    
    # Time the county-based method
    start_time = time.time()
    
    # Run the county-based method
    try:
        result = isochrone_to_block_groups_by_county(
            isochrone_path=isochrone_path,
            poi_data=poi_data,
            output_path=output_path,
            api_key=None  # Use environment variable if set
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Count the number of block groups
        block_group_count = len(result)
        
        return {
            "method": "county",
            "execution_time": execution_time,
            "block_group_count": block_group_count,
            "success": True
        }
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Get the full traceback for debugging
        tb = traceback.format_exc()
        print(f"Error in county method: {e}")
        print(f"Traceback:\n{tb}")
        
        return {
            "method": "county",
            "execution_time": execution_time,
            "error": str(e),
            "traceback": tb,
            "success": False
        }

def run_benchmarks(test_cases=None, repeat=1):
    """Run benchmarks for all test cases."""
    if test_cases is None:
        test_cases = TEST_CASES
    
    output_dirs = setup_temp_dirs()
    results = []
    
    for i, test_case in enumerate(test_cases):
        case_name = test_case["name"]
        poi_data = test_case["poi_data"]
        travel_time = test_case["travel_time"]
        
        print(f"\n=== Testing case {i+1}/{len(test_cases)}: {case_name} ===")
        
        # Generate isochrones for this test case
        print(f"Generating isochrones for travel time {travel_time} minutes...")
        isochrone_path = generate_isochrone(poi_data, travel_time, output_dirs["isochrones"])
        
        case_results = []
        
        # Run multiple times if requested
        for r in range(repeat):
            print(f"\nRepetition {r+1}/{repeat}")
            
            # Benchmark state-based method
            print("\nRunning state-based method...")
            state_output_path = os.path.join(output_dirs["block_groups"], f"case{i+1}_state_rep{r+1}.geojson")
            state_result = benchmark_state_method(isochrone_path, poi_data, state_output_path)
            state_result["case"] = case_name
            state_result["repetition"] = r + 1
            case_results.append(state_result)
            print(f"State method completed in {state_result['execution_time']:.2f} seconds")
            print(f"Found {state_result['block_group_count']} block groups")
            
            # Benchmark county-based method
            print("\nRunning county-based method...")
            county_output_path = os.path.join(output_dirs["block_groups"], f"case{i+1}_county_rep{r+1}.geojson")
            county_result = benchmark_county_method(isochrone_path, poi_data, county_output_path)
            county_result["case"] = case_name
            county_result["repetition"] = r + 1
            case_results.append(county_result)
            
            if county_result["success"]:
                print(f"County method completed in {county_result['execution_time']:.2f} seconds")
                print(f"Found {county_result['block_group_count']} block groups")
                
                # Calculate improvement
                if state_result["execution_time"] > 0:
                    improvement = (state_result["execution_time"] - county_result["execution_time"]) / state_result["execution_time"] * 100
                    print(f"Performance improvement: {improvement:.2f}%")
            else:
                print(f"County method failed with error: {county_result.get('error', 'Unknown error')}")
        
        results.extend(case_results)
    
    return results

def save_results(results, output_file="benchmark_results.json"):
    """Save benchmark results to a file."""
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_file}")

def create_summary(results):
    """Create a summary of the benchmark results."""
    df = pd.DataFrame(results)
    
    # Filter out failed tests
    successful_df = df[df.get("success", True)]
    
    # Group by case and method, and calculate mean execution time
    summary = successful_df.groupby(["case", "method"])["execution_time"].agg(
        ["mean", "min", "max", "std"]
    ).reset_index()
    
    # Pivot to compare methods
    pivot = summary.pivot(index="case", columns="method", values="mean")
    
    # Calculate improvement
    if "state" in pivot.columns and "county" in pivot.columns:
        pivot["improvement"] = (pivot["state"] - pivot["county"]) / pivot["state"] * 100
    
    return summary, pivot

def plot_results(results, output_file="benchmark_results.png"):
    """Create a bar chart of execution times."""
    df = pd.DataFrame(results)
    
    # Filter out failed tests
    successful_df = df[df.get("success", True)]
    
    # Group by case and method, and calculate mean execution time
    summary = successful_df.groupby(["case", "method"])["execution_time"].mean().reset_index()
    
    # Pivot to compare methods
    pivot = summary.pivot(index="case", columns="method", values="execution_time")
    
    # Create plot
    plt.figure(figsize=(12, 8))
    
    # Create a grouped bar chart
    pivot.plot(kind="bar", ax=plt.gca())
    
    plt.title("Block Group Selection Method Performance Comparison")
    plt.xlabel("Test Case")
    plt.ylabel("Execution Time (seconds)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    
    # Add legend
    plt.legend(["State-based Method", "County-based Method"])
    
    # Save the plot
    plt.savefig(output_file)
    print(f"Plot saved to {output_file}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Benchmark state-based vs county-based block group selection methods"
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Number of times to repeat each test (default: 1)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark_results",
        help="Base output filename (without extension)"
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the benchmark script."""
    args = parse_arguments()
    
    print("=" * 80)
    print("Block Group Selection Method Benchmark")
    print("=" * 80)
    print(f"Will run each test {args.repeat} time(s)")
    
    try:
        # Run the benchmarks
        results = run_benchmarks(repeat=args.repeat)
        
        # Save the raw results
        save_results(results, f"{args.output}.json")
        
        # Create and display summary
        summary, pivot = create_summary(results)
        print("\nSummary by test case and method:")
        print(summary)
        
        print("\nMethod comparison (mean execution time in seconds):")
        print(pivot)
        
        # Plot the results
        plot_results(results, f"{args.output}.png")
    except Exception as e:
        print(f"Error running benchmarks: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 