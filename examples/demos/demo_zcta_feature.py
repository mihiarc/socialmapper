#!/usr/bin/env python3
"""
ZCTA Feature Demo for SocialMapper

This demo showcases the new ZIP Code Tabulation Area (ZCTA) functionality
by comparing analysis results between block groups and ZCTAs using the same POIs.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import geopandas as gpd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Import SocialMapper
try:
    from socialmapper.core import run_socialmapper
    from socialmapper.cli import main as cli_main
except ImportError:
    print("❌ SocialMapper not found. Please install it first:")
    print("   pip install -e .")
    exit(1)

console = Console()

def create_demo_data():
    """Create sample data files for the demo."""
    demo_dir = Path("demo_zcta_data")
    demo_dir.mkdir(exist_ok=True)
    
    # Sample libraries in Seattle area
    sample_libraries = [
        {
            "name": "Seattle Central Library",
            "lat": 47.6062,
            "lon": -122.3321,
            "type": "library",
            "address": "1000 4th Ave, Seattle, WA"
        },
        {
            "name": "University Branch Library",
            "lat": 47.6613,
            "lon": -122.3138,
            "type": "library", 
            "address": "5009 Roosevelt Way NE, Seattle, WA"
        },
        {
            "name": "Ballard Branch Library",
            "lat": 47.6684,
            "lon": -122.3829,
            "type": "library",
            "address": "5614 22nd Ave NW, Seattle, WA"
        },
        {
            "name": "Capitol Hill Branch Library",
            "lat": 47.6205,
            "lon": -122.3207,
            "type": "library",
            "address": "425 Harvard Ave E, Seattle, WA"
        },
        {
            "name": "West Seattle Branch Library",
            "lat": 47.5643,
            "lon": -122.3856,
            "type": "library",
            "address": "2306 42nd Ave SW, Seattle, WA"
        }
    ]
    
    # Save as JSON
    json_file = demo_dir / "seattle_libraries.json"
    with open(json_file, 'w') as f:
        json.dump(sample_libraries, f, indent=2)
    
    # Save as CSV
    csv_file = demo_dir / "seattle_libraries.csv" 
    df = pd.DataFrame(sample_libraries)
    df.to_csv(csv_file, index=False)
    
    # Create address file for geocoding demo
    addresses = [
        "1000 4th Ave, Seattle, WA",
        "5009 Roosevelt Way NE, Seattle, WA", 
        "5614 22nd Ave NW, Seattle, WA",
        "425 Harvard Ave E, Seattle, WA",
        "2306 42nd Ave SW, Seattle, WA"
    ]
    
    address_file = demo_dir / "sample_addresses.csv"
    pd.DataFrame({"address": addresses}).to_csv(address_file, index=False)
    
    console.print(f"✅ Created demo data in {demo_dir}/")
    return demo_dir, json_file, csv_file, address_file

def run_comparison_analysis(coord_file: Path, output_base: str) -> Dict[str, Any]:
    """Run the same analysis with both block groups and ZCTAs."""
    results = {}
    
    # Common parameters
    common_params = {
        "custom_coords_path": str(coord_file),
        "travel_time": 15,
        "census_variables": ["total_population", "median_household_income", "median_age"],
        "export_csv": True,
        "output_dir": f"demo_output_{output_base}"
    }
    
    console.print("\n" + "="*60)
    console.print("🏠 RUNNING BLOCK GROUP ANALYSIS", style="bold blue")
    console.print("="*60)
    
    start_time = time.time()
    
    # Run with block groups (default)
    bg_results = run_socialmapper(
        **common_params,
        geographic_level="block-group"
    )
    
    bg_time = time.time() - start_time
    results['block_groups'] = {
        'results': bg_results,
        'processing_time': bg_time,
        'unit_count': len(bg_results.get('geographic_units', [])),
        'output_dir': common_params['output_dir']
    }
    
    console.print(f"✅ Block group analysis completed in {bg_time:.1f} seconds")
    
    # Clear Rich console state to prevent conflicts
    from socialmapper.ui.rich_console import clear_console_state
    clear_console_state()
    
    console.print("\n" + "="*60) 
    console.print("📮 RUNNING ZCTA ANALYSIS", style="bold green")
    console.print("="*60)
    
    start_time = time.time()
    
    # Update output directory for ZCTA run
    zcta_params = common_params.copy()
    zcta_params["output_dir"] = f"demo_output_{output_base}_zcta"
    
    # Run with ZCTAs
    zcta_results = run_socialmapper(
        **zcta_params,
        geographic_level="zcta"
    )
    
    zcta_time = time.time() - start_time
    results['zctas'] = {
        'results': zcta_results,
        'processing_time': zcta_time,
        'unit_count': len(zcta_results.get('geographic_units', [])),
        'output_dir': f"demo_output_{output_base}_zcta"
    }
    
    console.print(f"✅ ZCTA analysis completed in {zcta_time:.1f} seconds")
    
    return results

def display_comparison_results(results: Dict[str, Any]):
    """Display a comparison table of the results."""
    
    # Create comparison table
    table = Table(title="📊 Block Groups vs ZCTAs Comparison", box=box.ROUNDED)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Block Groups", style="blue")
    table.add_column("ZCTAs", style="green")
    table.add_column("Difference", style="yellow")
    
    bg_data = results['block_groups']
    zcta_data = results['zctas']
    
    # Processing time comparison
    table.add_row(
        "Processing Time",
        f"{bg_data['processing_time']:.1f}s",
        f"{zcta_data['processing_time']:.1f}s", 
        f"{zcta_data['processing_time'] - bg_data['processing_time']:+.1f}s"
    )
    
    # Geographic unit count
    table.add_row(
        "Geographic Units",
        str(bg_data['unit_count']),
        str(zcta_data['unit_count']),
        f"{zcta_data['unit_count'] - bg_data['unit_count']:+d}"
    )
    
    # File outputs
    bg_files = len(bg_data['results'].get('maps', []))
    zcta_files = len(zcta_data['results'].get('maps', []))
    table.add_row(
        "Output Files",
        str(bg_files),
        str(zcta_files),
        f"{zcta_files - bg_files:+d}"
    )
    
    # POI count (should be same)
    bg_pois = len(bg_data['results']['poi_data']['pois'])
    zcta_pois = len(zcta_data['results']['poi_data']['pois'])
    table.add_row(
        "POIs Analyzed",
        str(bg_pois),
        str(zcta_pois),
        "Same" if bg_pois == zcta_pois else f"{zcta_pois - bg_pois:+d}"
    )
    
    console.print("\n")
    console.print(table)
    
    # Output directories info
    console.print(f"\n📁 Block Group results: {bg_data['output_dir']}/")
    console.print(f"📁 ZCTA results: {zcta_data['output_dir']}/")

def analyze_census_data_differences(results: Dict[str, Any]):
    """Analyze differences in census data between block groups and ZCTAs."""
    
    bg_census = results['block_groups']['results'].get('census_data')
    zcta_census = results['zctas']['results'].get('census_data')
    
    if bg_census is None or zcta_census is None:
        console.print("⚠️ Census data not available for comparison")
        return
    
    console.print("\n" + "="*60)
    console.print("📈 CENSUS DATA ANALYSIS", style="bold magenta")
    console.print("="*60)
    
    # Create census comparison table
    table = Table(title="Census Variable Summary", box=box.ROUNDED)
    table.add_column("Variable", style="cyan")
    table.add_column("Block Groups", style="blue", justify="right")
    table.add_column("ZCTAs", style="green", justify="right")
    table.add_column("Difference", style="yellow", justify="right")
    
    # Analyze total population
    census_vars = ['total_population', 'median_household_income', 'median_age']
    
    for var in census_vars:
        if var in bg_census.columns and var in zcta_census.columns:
            bg_total = bg_census[var].sum() if var == 'total_population' else bg_census[var].mean()
            zcta_total = zcta_census[var].sum() if var == 'total_population' else zcta_census[var].mean()
            
            if var == 'total_population':
                table.add_row(
                    var.replace('_', ' ').title(),
                    f"{bg_total:,.0f}",
                    f"{zcta_total:,.0f}",
                    f"{zcta_total - bg_total:+,.0f}"
                )
            elif 'income' in var:
                table.add_row(
                    var.replace('_', ' ').title(), 
                    f"${bg_total:,.0f}",
                    f"${zcta_total:,.0f}",
                    f"${zcta_total - bg_total:+,.0f}"
                )
            else:
                table.add_row(
                    var.replace('_', ' ').title(),
                    f"{bg_total:.1f}",
                    f"{zcta_total:.1f}",
                    f"{zcta_total - bg_total:+.1f}"
                )
    
    console.print(table)

def demo_cli_usage():
    """Demonstrate CLI usage for the ZCTA feature."""
    console.print("\n" + "="*60)
    console.print("💻 CLI USAGE EXAMPLES", style="bold cyan")
    console.print("="*60)
    
    examples = [
        {
            "title": "🏠 Block Groups (Default)",
            "command": "python -m socialmapper.cli --custom-coords demo_zcta_data/seattle_libraries.csv --travel-time 15"
        },
        {
            "title": "📮 ZIP Code Tabulation Areas", 
            "command": "python -m socialmapper.cli --custom-coords demo_zcta_data/seattle_libraries.csv --travel-time 15 --geographic-level zcta"
        },
        {
            "title": "🗺️ POI Search with ZCTAs",
            "command": "python -m socialmapper.cli --poi --geocode-area 'Seattle' --state 'WA' --poi-type 'amenity' --poi-name 'library' --geographic-level zcta"
        },
        {
            "title": "📍 Address Geocoding with ZCTAs",
            "command": "python -m socialmapper.cli --addresses --address-file demo_zcta_data/sample_addresses.csv --geographic-level zcta"
        }
    ]
    
    for example in examples:
        panel = Panel(
            example["command"],
            title=example["title"],
            border_style="blue"
        )
        console.print(panel)
        console.print()

def main():
    """Run the complete ZCTA feature demo."""
    
    console.print(Panel.fit(
        "🎯 SocialMapper ZCTA Feature Demo\n\n"
        "This demo compares Census Block Groups vs ZIP Code Tabulation Areas (ZCTAs)\n"
        "using the same set of Seattle library locations.",
        title="Welcome to the ZCTA Demo",
        border_style="bold green"
    ))
    
    try:
        # Step 1: Create demo data
        console.print("\n📋 Step 1: Creating demo data...")
        demo_dir, json_file, csv_file, address_file = create_demo_data()
        
        # Step 2: Run comparison analysis
        console.print("\n🔍 Step 2: Running comparison analysis...")
        results = run_comparison_analysis(csv_file, "libraries")
        
        # Step 3: Display results comparison
        console.print("\n📊 Step 3: Analyzing results...")
        display_comparison_results(results)
        
        # Step 4: Analyze census data differences
        analyze_census_data_differences(results)
        
        # Step 5: Show CLI examples
        demo_cli_usage()
        
        # Summary
        console.print("\n" + "="*60)
        console.print("🎉 DEMO COMPLETE!", style="bold green")
        console.print("="*60)
        
        console.print("\n✅ Key Takeaways:")
        console.print("   • ZCTAs provide ZIP code-level analysis (larger geographic units)")
        console.print("   • Block groups provide fine-grained neighborhood analysis") 
        console.print("   • Same census variables available for both levels")
        console.print("   • Processing times may vary based on data density")
        console.print("   • Choose geographic level based on your analysis needs")
        
        console.print(f"\n📁 Demo files created in: {demo_dir}")
        console.print("📁 Analysis results in: demo_output_libraries/ and demo_output_libraries_zcta/")
        
        console.print("\n🔧 Next Steps:")
        console.print("   • Explore the generated CSV files and maps")
        console.print("   • Try the CLI commands shown above")
        console.print("   • Experiment with different travel times and census variables")
        
    except Exception as e:
        console.print(f"\n❌ Demo failed: {e}", style="bold red")
        console.print("\nPlease ensure:")
        console.print("   • SocialMapper is properly installed")
        console.print("   • Census API key is configured (if needed)")
        console.print("   • Internet connection is available")
        raise

if __name__ == "__main__":
    main() 