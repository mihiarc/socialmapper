#!/usr/bin/env python3
"""
Montana Timber Mill Site Analysis

This script analyzes the potential workforce accessibility and demographics
for a proposed timber mill location in Montana. It evaluates the site based on:
- Workforce accessibility at different commute distances
- Demographic characteristics of the surrounding population
- Economic indicators relevant to workforce availability
"""

import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich import print as rprint

# Add parent directory to path if needed
sys.path.insert(0, str(Path(__file__).parent))

from socialmapper import SocialMapperBuilder, SocialMapperClient
from socialmapper.api.result_types import Ok, Err

# Initialize Rich console for formatted output
console = Console()


def run_mill_analysis():
    """Run comprehensive analysis for the Montana timber mill location."""
    
    # Analysis parameters
    mill_csv = "montana_mill_location.csv"
    travel_times = [15, 30, 45, 60, 120]  # Minutes - including 2-hour maximum for rural Montana
    travel_mode = "drive"  # Most workers will drive in rural Montana
    
    # Census variables relevant to workforce analysis
    census_variables = [
        "total_population",      # Total potential workforce
        "median_income",         # Economic profile
        "median_age",           # Age distribution
        "education_bachelors_plus",  # Skilled workforce availability
        "households",           # Residential density
        "percent_poverty",      # Economic challenges
        "percent_without_vehicle"  # Transportation access
    ]
    
    # Results storage
    analysis_results = {}
    
    console.print("\n[bold blue]🏭 Montana Timber Mill Workforce Analysis[/bold blue]\n")
    console.print(f"📍 Analyzing location from: {mill_csv}")
    console.print(f"🚗 Travel mode: {travel_mode}")
    console.print(f"⏱️  Travel times: {', '.join(map(str, travel_times))} minutes\n")
    
    # Create output directory for this analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/timber_mill_analysis_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with SocialMapperClient() as client:
            # Run analysis for each travel time
            for travel_time in travel_times:
                console.print(f"\n[yellow]Analyzing {travel_time}-minute commute radius...[/yellow]")
                
                # Build configuration
                # Disable maps for 2-hour analysis to avoid performance issues
                create_maps = travel_time < 120
                if not create_maps:
                    console.print("   [dim]Note: Skipping map generation for 2-hour analysis (use visualize_montana_results.py instead)[/dim]")
                
                config = (
                    SocialMapperBuilder()
                    .with_custom_pois(mill_csv)
                    .with_travel_time(travel_time)
                    .with_travel_mode(travel_mode)
                    .with_census_variables(*census_variables)
                    .with_output_directory(output_dir / f"{travel_time}min")
                    .with_exports(csv=True, isochrones=True, maps=create_maps)
                    .build()
                )
                
                # Run analysis
                result = client.run_analysis(config)
                
                if result.is_err():
                    error = result.unwrap_err()
                    console.print(f"[red]❌ Error: {error.message}[/red]")
                    continue
                
                analysis = result.unwrap()
                analysis_results[travel_time] = analysis
                
                console.print(f"[green]✅ Completed {travel_time}-minute analysis[/green]")
                console.print(f"   - Census units analyzed: {analysis.census_units_analyzed}")
                console.print(f"   - Isochrone area: {analysis.isochrone_area:.2f} km²")
                
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e!s}[/red]")
        return 1
    
    # Generate summary report
    if analysis_results:
        generate_summary_report(analysis_results, output_dir)
    
    return 0


def generate_summary_report(results, output_dir):
    """Generate a comprehensive summary report of the analysis."""
    
    console.print("\n[bold blue]📊 Generating Summary Report[/bold blue]\n")
    
    # Create summary table
    table = Table(title="Workforce Accessibility Summary")
    table.add_column("Commute Time", style="cyan", no_wrap=True)
    table.add_column("Population", justify="right", style="green")
    table.add_column("Households", justify="right", style="green")
    table.add_column("Median Income", justify="right", style="yellow")
    table.add_column("Median Age", justify="right", style="magenta")
    table.add_column("Area (km²)", justify="right", style="blue")
    
    # Add data rows
    for travel_time, analysis in sorted(results.items()):
        demographics = analysis.demographics
        
        # Format values
        population = f"{demographics.get('total_population', 0):,.0f}"
        households = f"{demographics.get('households', 0):,.0f}"
        median_income = f"${demographics.get('median_income', 0):,.0f}"
        median_age = f"{demographics.get('median_age', 0):.1f}"
        area = f"{analysis.isochrone_area:.1f}"
        
        table.add_row(
            f"{travel_time} minutes",
            population,
            households,
            median_income,
            median_age,
            area
        )
    
    console.print(table)
    
    # Write detailed report to file
    report_path = output_dir / "workforce_analysis_report.md"
    with open(report_path, "w") as f:
        f.write("# Montana Timber Mill Workforce Analysis Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write("This report analyzes the workforce accessibility and demographics ")
        f.write("for a proposed timber mill location in Montana.\n\n")
        
        f.write("## Location Details\n\n")
        f.write("- **Coordinates**: 47.167012, -113.466881\n")
        f.write("- **Nearest Town**: Philipsburg, Montana\n\n")
        
        f.write("## Workforce Accessibility Analysis\n\n")
        
        for travel_time, analysis in sorted(results.items()):
            demographics = analysis.demographics
            
            f.write(f"### {travel_time}-Minute Commute Radius\n\n")
            f.write(f"**Coverage Area**: {analysis.isochrone_area:.1f} km²\n\n")
            
            f.write("**Population Demographics**:\n")
            f.write(f"- Total Population: {demographics.get('total_population', 0):,.0f}\n")
            f.write(f"- Households: {demographics.get('households', 0):,.0f}\n")
            f.write(f"- Median Age: {demographics.get('median_age', 0):.1f} years\n\n")
            
            f.write("**Economic Indicators**:\n")
            f.write(f"- Median Household Income: ${demographics.get('median_income', 0):,.0f}\n")
            f.write(f"- Poverty Rate: {demographics.get('percent_poverty', 0):.1f}%\n\n")
            
            f.write("**Workforce Characteristics**:\n")
            f.write(f"- Bachelor's Degree or Higher: {demographics.get('education_bachelors_plus', 0):,.0f}\n")
            f.write(f"- Households Without Vehicle: {demographics.get('percent_without_vehicle', 0):.1f}%\n\n")
        
        f.write("## Key Findings\n\n")
        
        # Calculate workforce insights
        if 30 in results:
            pop_30min = results[30].demographics.get('total_population', 0)
            f.write(f"- Within a 30-minute commute: **{pop_30min:,.0f}** potential workers\n")
            
            if 15 in results and 45 in results and 60 in results and 120 in results:
                pop_15min = results[15].demographics.get('total_population', 0)
                pop_45min = results[45].demographics.get('total_population', 0)
                pop_60min = results[60].demographics.get('total_population', 0)
                pop_120min = results[120].demographics.get('total_population', 0)
                
                f.write(f"- Expanding from 15 to 30 minutes adds **{pop_30min - pop_15min:,.0f}** people\n")
                f.write(f"- Expanding from 30 to 45 minutes adds **{pop_45min - pop_30min:,.0f}** people\n")
                f.write(f"- Expanding from 45 to 60 minutes adds **{pop_60min - pop_45min:,.0f}** people\n")
                f.write(f"- Expanding from 60 to 120 minutes adds **{pop_120min - pop_60min:,.0f}** people\n")
                f.write(f"\n- Total within 2-hour drive: **{pop_120min:,.0f}** potential workers\n")
        
        f.write("\n## Recommendations\n\n")
        f.write("1. **Workforce Availability**: Assess if the population within reasonable ")
        f.write("commute distance is sufficient for mill operations\n")
        f.write("2. **Extended Commute Radius**: The 2-hour radius captures major population ")
        f.write("centers like Missoula and Butte, though daily commutes this long are uncommon\n")
        f.write("3. **Transportation**: Consider the percentage of households without vehicles ")
        f.write("when planning employee transportation programs\n")
        f.write("4. **Economic Impact**: The median income levels suggest the economic profile ")
        f.write("of the potential workforce\n")
        f.write("5. **Skills Assessment**: Review education levels to ensure availability of ")
        f.write("skilled workers for technical positions\n")
        f.write("6. **Relocation Incentives**: For workers beyond 60 minutes, consider ")
        f.write("relocation assistance or weekly lodging options\n")
    
    console.print(f"\n[green]✅ Report saved to: {report_path}[/green]")
    
    # Print key insights
    panel = Panel.fit(
        "[bold]Key Insights:[/bold]\n\n" +
        f"📍 Location provides access to workforce within typical rural commute distances\n" +
        f"📊 Demographic data saved for detailed analysis\n" +
        f"🗺️ Maps generated showing accessibility zones\n" +
        f"📄 Full report available at: {report_path}",
        title="Analysis Complete",
        border_style="green"
    )
    console.print(panel)


if __name__ == "__main__":
    exit_code = run_mill_analysis()
    sys.exit(exit_code)