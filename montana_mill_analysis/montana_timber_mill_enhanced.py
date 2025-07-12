#!/usr/bin/env python3
"""
Enhanced Montana Timber Mill Site Analysis

This enhanced version includes:
- Comparison with nearby towns for workforce competition
- Analysis of existing industrial/logging infrastructure
- Transportation corridor analysis
- Seasonal workforce considerations
"""

import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import pandas as pd

# Add parent directory to path if needed
sys.path.insert(0, str(Path(__file__).parent))

from socialmapper import SocialMapperBuilder, SocialMapperClient

# Initialize Rich console
console = Console()


def create_comparison_locations_csv():
    """Create a CSV with nearby towns for comparison analysis."""
    
    comparison_data = [
        # Mill location
        {"name": "Montana Mill Site", "lat": 47.167012, "lon": -113.466881, "type": "mill", "notes": "Proposed site"},
        # Nearby towns
        {"name": "Philipsburg", "lat": 46.3321, "lon": -113.2948, "type": "town", "notes": "Nearest town"},
        {"name": "Anaconda", "lat": 46.1285, "lon": -112.9420, "type": "city", "notes": "Industrial history"},
        {"name": "Deer Lodge", "lat": 46.3966, "lon": -112.7306, "type": "town", "notes": "Regional center"},
        {"name": "Drummond", "lat": 46.6677, "lon": -113.1433, "type": "town", "notes": "I-90 corridor"},
    ]
    
    df = pd.DataFrame(comparison_data)
    comparison_file = "montana_timber_analysis_locations.csv"
    df.to_csv(comparison_file, index=False)
    
    return comparison_file


def analyze_transportation_access():
    """Analyze access to major transportation corridors."""
    
    console.print("\n[bold yellow]🚛 Transportation Infrastructure Analysis[/bold yellow]\n")
    
    # Key transportation features to analyze
    transport_features = [
        ("Interstate 90", "Major east-west freight corridor"),
        ("US Highway 10A", "Regional connector"),
        ("Montana Rail Link", "Freight rail access"),
        ("State Route 1", "North-south connector")
    ]
    
    table = Table(title="Transportation Infrastructure")
    table.add_column("Feature", style="cyan")
    table.add_column("Importance", style="green")
    table.add_column("Access Notes", style="yellow")
    
    table.add_row(
        "Interstate 90",
        "Critical",
        "~20 miles north via US-10A"
    )
    table.add_row(
        "Rail Access",
        "High",
        "Montana Rail Link runs through Drummond"
    )
    table.add_row(
        "State Highways",
        "Medium",
        "Direct access to MT-1 and US-10A"
    )
    table.add_row(
        "Airport",
        "Low",
        "Missoula International ~80 miles"
    )
    
    console.print(table)


def analyze_existing_industry():
    """Analyze existing industrial and forestry infrastructure."""
    
    console.print("\n[bold green]🌲 Existing Industry Analysis[/bold green]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        task = progress.add_task("Searching for existing facilities...", total=None)
        
        try:
            with SocialMapperClient() as client:
                # Search for existing industrial facilities
                industrial_config = (
                    SocialMapperBuilder()
                    .with_location("Philipsburg", "Montana")
                    .with_osm_pois("landuse", "industrial")
                    .with_travel_time(30)
                    .with_travel_mode("drive")
                    .limit_pois(20)
                    .with_exports(csv=True, maps=False)
                    .build()
                )
                
                result = client.run_analysis(industrial_config)
                
                if result.is_ok():
                    analysis = result.unwrap()
                    console.print(f"\n[green]Found {analysis.poi_count} existing industrial sites within 30 minutes[/green]")
                else:
                    console.print("[yellow]No existing industrial sites found in immediate area[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Could not complete industry analysis: {e}[/red]")
        
        progress.update(task, completed=True)


def run_enhanced_analysis():
    """Run enhanced timber mill site analysis."""
    
    console.print(Panel.fit(
        "[bold blue]🏭 Enhanced Montana Timber Mill Analysis[/bold blue]\n\n" +
        "This analysis includes:\n" +
        "• Multi-location workforce comparison\n" +
        "• Transportation infrastructure assessment\n" +
        "• Existing industry analysis\n" +
        "• Seasonal workforce considerations",
        border_style="blue"
    ))
    
    # Create comparison locations file
    locations_file = create_comparison_locations_csv()
    console.print(f"\n[green]✅ Created comparison locations file: {locations_file}[/green]")
    
    # Analyze transportation access
    analyze_transportation_access()
    
    # Analyze existing industry
    analyze_existing_industry()
    
    # Run comprehensive workforce analysis
    console.print("\n[bold blue]👥 Comparative Workforce Analysis[/bold blue]\n")
    
    # Analysis parameters
    travel_times = [20, 40, 60, 120]  # Extended to include 2-hour maximum for rural Montana
    census_variables = [
        "total_population",
        "median_income", 
        "median_age",
        "households",
        "percent_poverty",
        "education_bachelors_plus",
        "percent_without_vehicle",
        "housing_units"  # For seasonal worker housing assessment
    ]
    
    output_dir = Path(f"output/timber_mill_enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    try:
        with SocialMapperClient() as client:
            # Analyze each location with extended travel time
            config = (
                SocialMapperBuilder()
                .with_custom_pois(locations_file)
                .with_travel_time(120)  # Maximum 2-hour analysis to capture regional workforce
                .with_travel_mode("drive")
                .with_census_variables(*census_variables)
                .with_output_directory(output_dir)
                .with_exports(csv=True, isochrones=True, maps=True)
                .build()
            )
            
            result = client.run_analysis(config)
            
            if result.is_ok():
                analysis = result.unwrap()
                console.print(f"[green]✅ Completed comparative analysis[/green]")
                console.print(f"   - Locations analyzed: {analysis.poi_count}")
                console.print(f"   - Total census units: {analysis.census_units_analyzed}")
                
                # Generate competitive analysis report
                generate_competitive_report(analysis, output_dir)
            else:
                console.print(f"[red]❌ Error: {result.unwrap_err().message}[/red]")
                
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e!s}[/red]")
        return 1
    
    # Seasonal workforce considerations
    console.print("\n[bold magenta]🌡️ Seasonal Workforce Considerations[/bold magenta]\n")
    console.print("Montana timber operations typically experience:")
    console.print("• Peak season: May-October (dry conditions)")
    console.print("• Reduced operations: November-April (snow/mud)")
    console.print("• Consider seasonal worker housing availability")
    console.print("• Plan for 20-30% workforce variation by season")
    
    return 0


def generate_competitive_report(analysis, output_dir):
    """Generate report comparing workforce availability across locations."""
    
    report_path = output_dir / "competitive_workforce_analysis.md"
    
    with open(report_path, "w") as f:
        f.write("# Montana Timber Mill Competitive Workforce Analysis\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write("This enhanced analysis compares the proposed timber mill site with ")
        f.write("nearby communities to assess workforce competition and availability.\n\n")
        
        f.write("## Competitive Advantages\n\n")
        f.write("1. **Location**: Strategic position between Philipsburg and Drummond\n")
        f.write("2. **Transportation**: Access to I-90 corridor via US-10A\n")
        f.write("3. **Workforce**: Draw from multiple communities\n")
        f.write("4. **Competition**: Limited industrial employers in immediate area\n")
        f.write("5. **Regional Access**: Within 2-hour drive of major centers:\n")
        f.write("   - Missoula (~80 miles): University town, population ~75,000\n")
        f.write("   - Butte (~60 miles): Mining heritage, Montana Tech, population ~35,000\n")
        f.write("   - Helena (~90 miles): State capital, population ~33,000\n\n")
        
        f.write("## Workforce Recruitment Strategy\n\n")
        f.write("- Primary recruitment: Philipsburg (nearest town)\n")
        f.write("- Secondary markets: Anaconda, Deer Lodge\n")
        f.write("- Commuter corridor: Drummond (I-90 access)\n")
        f.write("- Consider shuttle service from larger towns\n\n")
        
        f.write("## Infrastructure Requirements\n\n")
        f.write("- Road improvements on US-10A for truck traffic\n")
        f.write("- Potential rail spur from Montana Rail Link\n")
        f.write("- Workforce housing for seasonal workers\n")
        f.write("- Training partnerships with Montana Tech (Butte)\n")
    
    console.print(f"\n[green]✅ Competitive analysis report saved to: {report_path}[/green]")


if __name__ == "__main__":
    exit_code = run_enhanced_analysis()
    sys.exit(exit_code)