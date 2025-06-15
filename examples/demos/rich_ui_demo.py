#!/usr/bin/env python3
"""
Simplified Rich Demo for SocialMapper

This script demonstrates the Rich-enhanced user interface without
the parts that might be causing hangs.
"""

import time
from socialmapper.ui.rich_console import (
    print_banner, print_success, print_error, print_warning, print_info,
    print_poi_summary_table, print_performance_summary,
    print_census_variables_table, print_step, console
)
from socialmapper import __version__

def main():
    """Run simplified Rich demo."""
    console.print("[bold green]🚀 Starting SocialMapper Rich Integration Demo (Simplified)[/bold green]\n")
    
    # Demo 1: Banner
    print_banner(
        "Rich Integration Demo", 
        "Showcasing beautiful terminal output for community mapping",
        __version__
    )
    time.sleep(0.5)
    
    # Demo 2: Messages
    print_step(1, 4, "Message Panels Demo", "💬")
    print_info("This is an informational message about the demo", "Demo Info")
    print_success("Rich integration was successful!")
    print_warning("This is what warnings look like with Rich")
    print_error("This is how errors are displayed (demo only)")
    time.sleep(0.5)
    
    # Demo 3: Census Variables
    print_step(2, 4, "Census Variables Table", "📊")
    census_vars = {
        "B01003_001E": "Total Population",
        "B19013_001E": "Median Household Income", 
        "B25077_001E": "Median Home Value",
    }
    print_census_variables_table(census_vars)
    time.sleep(0.5)
    
    # Demo 4: POI Table
    print_step(3, 4, "POI Summary Table", "📍")
    pois = [
        {"name": "Central Library", "type": "library", "lat": 44.5646, "lon": -123.2620, "distance": 0.5},
        {"name": "OSU Valley Library", "type": "library", "lat": 44.5651, "lon": -123.2785, "distance": 1.2},
        {"name": "Corvallis Library", "type": "library", "lat": 44.5707, "lon": -123.2690, "distance": 0.8},
    ]
    print_poi_summary_table(pois)
    time.sleep(0.5)
    
    # Demo 5: Performance Summary
    print_step(4, 4, "Performance Summary", "📈")
    metrics = {
        "processing_time": 12.5,
        "poi_count": 3,
        "isochrone_count": 3,
        "cache_hits": 42,
        "api_calls": 8,
        "memory_peak_mb": 156.3
    }
    print_performance_summary(metrics)
    
    console.print("\n[bold green]✅ Demo Complete![/bold green]")
    console.print("[dim]Rich library adds professional polish to SocialMapper[/dim]\n")

if __name__ == "__main__":
    main()