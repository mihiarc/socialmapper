#!/usr/bin/env python3
"""
Montana Timber Mill 2-Hour Workforce Analysis

This script specifically analyzes the maximum 2-hour (120 minute) commute radius
to understand the full regional workforce potential, including major population
centers like Missoula, Butte, and Helena.
"""

from rich.console import Console
from rich.table import Table
from rich import print as rprint
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from socialmapper import SocialMapperBuilder, SocialMapperClient

console = Console()


def main():
    """Analyze 2-hour workforce catchment area for Montana timber mill."""
    
    console.print("\n[bold blue]🏭 Montana Timber Mill - 2 Hour Regional Analysis[/bold blue]\n")
    console.print("This analysis explores the maximum workforce catchment area,")
    console.print("including major Montana cities within a 2-hour drive.\n")
    
    # Key cities within ~2 hours
    console.print("[yellow]Major cities within 2-hour drive:[/yellow]")
    
    cities_table = Table(show_header=True, header_style="bold cyan")
    cities_table.add_column("City", style="white")
    cities_table.add_column("Distance", justify="right", style="green")
    cities_table.add_column("Population", justify="right", style="yellow")
    cities_table.add_column("Key Assets", style="magenta")
    
    cities_table.add_row("Missoula", "~80 miles", "~75,000", "University of Montana")
    cities_table.add_row("Butte", "~60 miles", "~35,000", "Montana Tech (engineering)")
    cities_table.add_row("Helena", "~90 miles", "~33,000", "State capital")
    cities_table.add_row("Anaconda", "~30 miles", "~9,000", "Industrial heritage")
    cities_table.add_row("Deer Lodge", "~25 miles", "~3,000", "Regional hub")
    
    console.print(cities_table)
    console.print()
    
    # Run the 2-hour analysis
    with SocialMapperClient() as client:
        console.print("[yellow]Running 2-hour commute analysis...[/yellow]\n")
        
        config = (
            SocialMapperBuilder()
            .with_custom_pois("montana_mill_location.csv")
            .with_travel_time(120)  # Maximum 2-hour analysis
            .with_travel_mode("drive")
            .with_census_variables(
                "total_population",
                "median_income",
                "median_age",
                "education_bachelors_plus",
                "households",
                "housing_units"
            )
            .enable_isochrone_export()
            .enable_map_generation()
            .with_output_directory("output/timber_mill_2hour_analysis")
            .build()
        )
        
        result = client.run_analysis(config)
        
        if result.is_ok():
            analysis = result.unwrap()
            demographics = analysis.demographics
            
            console.print("[green]✅ Analysis complete![/green]\n")
            
            # Create results table
            results_table = Table(title="2-Hour Workforce Catchment Area", show_header=True)
            results_table.add_column("Metric", style="cyan")
            results_table.add_column("Value", justify="right", style="yellow")
            
            results_table.add_row(
                "Total Population", 
                f"{demographics.get('total_population', 0):,.0f}"
            )
            results_table.add_row(
                "Total Households",
                f"{demographics.get('households', 0):,.0f}"
            )
            results_table.add_row(
                "Bachelor's Degree+",
                f"{demographics.get('education_bachelors_plus', 0):,.0f}"
            )
            results_table.add_row(
                "Median Income",
                f"${demographics.get('median_income', 0):,.0f}"
            )
            results_table.add_row(
                "Median Age",
                f"{demographics.get('median_age', 0):.1f} years"
            )
            results_table.add_row(
                "Coverage Area",
                f"{analysis.isochrone_area:,.0f} km²"
            )
            
            console.print(results_table)
            
            # Calculate workforce estimates
            console.print("\n[bold]Workforce Estimates:[/bold]")
            
            total_pop = demographics.get('total_population', 0)
            workforce_participation = 0.63  # US average ~63%
            potential_workforce = int(total_pop * workforce_participation)
            
            console.print(f"• Potential workforce (63% participation): [green]{potential_workforce:,}[/green]")
            console.print(f"• College-educated workers: [blue]{demographics.get('education_bachelors_plus', 0):,}[/blue]")
            
            # Realistic recruitment estimates
            console.print("\n[bold]Realistic Recruitment Zones:[/bold]")
            console.print("• [green]Daily commuters[/green] (0-60 min): Primary workforce")
            console.print("• [yellow]Weekly commuters[/yellow] (60-90 min): Skilled positions, 4-day weeks")
            console.print("• [red]Relocation candidates[/red] (90-120 min): Management, specialists")
            
            console.print(f"\n[dim]Output files saved to: {analysis.files_generated}[/dim]")
            
        else:
            error = result.unwrap_err()
            console.print(f"[red]❌ Error: {error.message}[/red]")
    
    console.print("\n[bold]Key Insights for 2-Hour Analysis:[/bold]")
    console.print("1. Captures entire regional workforce including major cities")
    console.print("2. Identifies skilled worker availability from university towns")
    console.print("3. Helps plan recruitment strategies for different position types")
    console.print("4. Informs housing and transportation infrastructure needs")
    console.print("5. Provides data for economic impact assessments")


if __name__ == "__main__":
    main()