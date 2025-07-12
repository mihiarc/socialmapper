#!/usr/bin/env python3
"""
Optimized Montana Timber Mill Analysis

This version includes performance optimizations for analyzing large areas,
especially important for 2-hour drive times in rural Montana.
"""

import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
import time

sys.path.insert(0, str(Path(__file__).parent))

from socialmapper import SocialMapperBuilder, SocialMapperClient

console = Console()


def run_optimized_analysis():
    """Run optimized timber mill analysis with performance considerations."""
    
    console.print(Panel.fit(
        "[bold blue]🏭 Montana Timber Mill Analysis - Optimized Version[/bold blue]\n\n" +
        "This version includes optimizations for faster processing:\n" +
        "• Selective map generation\n" +
        "• Strategic travel time selection\n" +
        "• Cached network data\n" +
        "• Focused census variables",
        border_style="blue"
    ))
    
    # Strategy: Run different analyses for different purposes
    analyses = [
        {
            "name": "Core Workforce",
            "travel_times": [15, 30],
            "generate_maps": True,
            "purpose": "Daily commuters"
        },
        {
            "name": "Extended Workforce", 
            "travel_times": [45, 60],
            "generate_maps": True,
            "purpose": "Skilled positions"
        },
        {
            "name": "Regional Assessment",
            "travel_times": [120],
            "generate_maps": False,  # Skip maps for 2-hour to save time
            "purpose": "Total workforce potential"
        }
    ]
    
    # Focused census variables for faster processing
    essential_variables = [
        "total_population",
        "median_income",
        "households"
    ]
    
    output_dir = Path(f"output/timber_mill_optimized_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    all_results = {}
    
    with SocialMapperClient() as client:
        for analysis in analyses:
            console.print(f"\n[yellow]Running {analysis['name']} Analysis...[/yellow]")
            console.print(f"Purpose: {analysis['purpose']}")
            
            for travel_time in analysis['travel_times']:
                start_time = time.time()
                console.print(f"\n⏱️  Analyzing {travel_time}-minute radius...")
                
                # Build optimized configuration
                builder = (
                    SocialMapperBuilder()
                    .with_custom_pois("montana_mill_location.csv")
                    .with_travel_time(travel_time)
                    .with_travel_mode("drive")
                    .with_census_variables(*essential_variables)
                    .with_output_directory(output_dir / f"{travel_time}min")
                )
                
                # Conditionally enable exports based on travel time
                if travel_time <= 60:
                    builder.with_exports(
                        csv=True,
                        isochrones=True,
                        maps=analysis['generate_maps']
                    )
                else:
                    # For 2-hour analysis, skip maps and isochrone export
                    builder.with_exports(
                        csv=True,
                        isochrones=False,
                        maps=False
                    )
                
                config = builder.build()
                result = client.run_analysis(config)
                
                if result.is_ok():
                    analysis_result = result.unwrap()
                    all_results[travel_time] = analysis_result
                    
                    elapsed = time.time() - start_time
                    console.print(f"[green]✅ Completed in {elapsed:.1f} seconds[/green]")
                    
                    # Quick summary
                    demographics = analysis_result.demographics
                    console.print(f"   Population: {demographics.get('total_population', 0):,.0f}")
                    console.print(f"   Area: {analysis_result.isochrone_area:.1f} km²")
                else:
                    console.print(f"[red]❌ Error: {result.unwrap_err().message}[/red]")
    
    # Generate optimized summary report
    generate_optimized_report(all_results, output_dir)
    
    # Performance tips
    console.print("\n[bold cyan]💡 Performance Optimization Tips:[/bold cyan]")
    console.print("1. For 2-hour analysis, consider running without maps")
    console.print("2. Use cached network data when re-running analyses")
    console.print("3. Limit census variables to essentials for faster processing")
    console.print("4. Consider analyzing different radii in separate runs")
    console.print("5. The 2-hour isochrone in rural areas can be 10,000+ km²")


def generate_optimized_report(results, output_dir):
    """Generate a streamlined report focusing on key insights."""
    
    console.print("\n[bold blue]📊 Generating Optimized Report[/bold blue]\n")
    
    # Summary table
    table = Table(title="Workforce Analysis Summary")
    table.add_column("Radius", style="cyan")
    table.add_column("Population", justify="right", style="green")
    table.add_column("Households", justify="right", style="yellow")
    table.add_column("Median Income", justify="right", style="magenta")
    table.add_column("Area (km²)", justify="right", style="blue")
    
    for minutes, analysis in sorted(results.items()):
        demographics = analysis.demographics
        table.add_row(
            f"{minutes} min",
            f"{demographics.get('total_population', 0):,.0f}",
            f"{demographics.get('households', 0):,.0f}",
            f"${demographics.get('median_income', 0):,.0f}",
            f"{analysis.isochrone_area:,.0f}"
        )
    
    console.print(table)
    
    # Write streamlined report
    report_path = output_dir / "optimized_analysis_report.md"
    with open(report_path, "w") as f:
        f.write("# Montana Timber Mill - Optimized Analysis Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Quick Summary\n\n")
        
        if 30 in results and 120 in results:
            pop_30 = results[30].demographics.get('total_population', 0)
            pop_120 = results[120].demographics.get('total_population', 0)
            
            f.write(f"- **30-minute workforce**: {pop_30:,.0f} people\n")
            f.write(f"- **2-hour regional workforce**: {pop_120:,.0f} people\n")
            f.write(f"- **Workforce expansion factor**: {pop_120/pop_30:.1f}x\n\n")
        
        f.write("## Recruitment Strategy\n\n")
        f.write("### Immediate Workforce (0-30 minutes)\n")
        if 30 in results:
            pop = results[30].demographics.get('total_population', 0)
            f.write(f"- Population: {pop:,.0f}\n")
            f.write("- Strategy: Core daily workforce\n")
            f.write("- Focus: Local hiring, community engagement\n\n")
        
        f.write("### Extended Workforce (30-60 minutes)\n")
        if 60 in results:
            pop_60 = results[60].demographics.get('total_population', 0)
            pop_30 = results.get(30, {}).demographics.get('total_population', 0) if 30 in results else 0
            additional = pop_60 - pop_30
            f.write(f"- Additional population: {additional:,.0f}\n")
            f.write("- Strategy: Skilled positions, shift work\n")
            f.write("- Consider: Carpool programs, flexible schedules\n\n")
        
        f.write("### Regional Workforce (60-120 minutes)\n")
        if 120 in results:
            pop_120 = results[120].demographics.get('total_population', 0)
            pop_60 = results.get(60, {}).demographics.get('total_population', 0) if 60 in results else 0
            additional = pop_120 - pop_60
            f.write(f"- Additional population: {additional:,.0f}\n")
            f.write("- Strategy: Management, specialists\n")
            f.write("- Consider: Relocation packages, remote work options\n")
    
    console.print(f"\n[green]✅ Optimized report saved to: {report_path}[/green]")


def run_quick_2hour_check():
    """Quick check just for 2-hour population without heavy processing."""
    
    console.print("\n[yellow]Quick 2-Hour Population Check[/yellow]")
    console.print("(CSV data only, no maps or isochrones)\n")
    
    with SocialMapperClient() as client:
        config = (
            SocialMapperBuilder()
            .with_custom_pois("montana_mill_location.csv")
            .with_travel_time(120)
            .with_travel_mode("drive")
            .with_census_variables("total_population", "households")
            .with_exports(csv=True, isochrones=False, maps=False)
            .build()
        )
        
        start_time = time.time()
        result = client.run_analysis(config)
        elapsed = time.time() - start_time
        
        if result.is_ok():
            analysis = result.unwrap()
            demographics = analysis.demographics
            
            console.print(f"[green]✅ Quick analysis completed in {elapsed:.1f} seconds[/green]")
            console.print(f"\n2-Hour Drive Radius:")
            console.print(f"- Total Population: {demographics.get('total_population', 0):,.0f}")
            console.print(f"- Households: {demographics.get('households', 0):,.0f}")
            console.print(f"- Coverage Area: {analysis.isochrone_area:,.0f} km²")


if __name__ == "__main__":
    # Ask user what type of analysis to run
    console.print("\n[bold]Select Analysis Type:[/bold]")
    console.print("1. Full optimized analysis (recommended)")
    console.print("2. Quick 2-hour population check only")
    console.print("3. Exit")
    
    choice = console.input("\nEnter choice (1-3): ")
    
    if choice == "1":
        run_optimized_analysis()
    elif choice == "2":
        run_quick_2hour_check()
    else:
        console.print("Exiting...")
        sys.exit(0)