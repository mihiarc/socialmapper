#!/usr/bin/env python3
"""
Rich Demo for SocialMapper

This script demonstrates the new Rich-enhanced user interface
showing beautiful progress bars, tables, status indicators, and formatted output.
"""

import time
import random
from typing import List, Dict, Any

# Import Rich components
from socialmapper.ui.rich_console import (
    print_banner, print_success, print_error, print_warning, print_info,
    status_spinner, print_poi_summary_table, print_performance_summary,
    print_file_summary, print_census_variables_table, print_step,
    print_divider, console
)
from socialmapper.ui.rich_progress import (
    get_rich_tracker, ProcessingStage, track_stage
)
from socialmapper import __version__

def demo_banner():
    """Demonstrate the beautiful SocialMapper banner."""
    print_banner(
        "Rich Integration Demo",
        "Showcasing beautiful terminal output for community mapping",
        __version__
    )

def demo_messages():
    """Demonstrate different types of message panels."""
    print_step(1, 6, "Message Panels Demo", "💬")
    
    print_info("This is an informational message about the demo", "Demo Info")
    time.sleep(1)
    
    print_success("Rich integration was successful!")
    time.sleep(1)
    
    print_warning("This is what warnings look like with Rich")
    time.sleep(1)
    
    # Simulate an error (without actually failing)
    print_error("This is how errors are displayed (demo only)")
    time.sleep(1)

def demo_census_variables():
    """Demonstrate the census variables table."""
    print_step(2, 6, "Census Variables Table", "📊")
    
    # Sample census variables (subset for demo)
    sample_variables = {
        "total_population": "B01003_001E",
        "median_household_income": "B19013_001E", 
        "median_home_value": "B25077_001E",
        "median_age": "B01002_001E",
        "white_population": "B02001_002E",
        "housing_units": "B25001_001E"
    }
    
    print_census_variables_table(sample_variables)
    time.sleep(2)

def demo_poi_table():
    """Demonstrate POI summary table."""
    print_step(3, 6, "POI Summary Table", "📍")
    
    # Sample POI data
    sample_pois = [
        {
            "name": "Fuquay-Varina Library",
            "type": "library", 
            "lat": 35.5847,
            "lon": -78.7997,
            "tags": {"amenity": "library", "operator": "Wake County", "website": "wakegov.com"}
        },
        {
            "name": "Centennial Park",
            "type": "park",
            "lat": 35.5825,
            "lon": -78.8012,
            "tags": {"leisure": "park", "name": "Centennial Park", "access": "public"}
        },
        {
            "name": "Fuquay-Varina High School",
            "type": "school",
            "lat": 35.5863,
            "lon": -78.7889,
            "tags": {"amenity": "school", "grades": "9-12", "operator": "Wake County Schools"}
        },
        {
            "name": "Harris Teeter",
            "type": "supermarket",
            "lat": 35.5798,
            "lon": -78.8023,
            "tags": {"shop": "supermarket", "brand": "Harris Teeter", "parking": "yes"}
        }
    ]
    
    print_poi_summary_table(sample_pois)
    time.sleep(2)

def demo_progress_tracking():
    """Demonstrate Rich progress tracking."""
    print_step(4, 6, "Progress Tracking Demo", "⚡")
    
    # Get the Rich tracker
    tracker = get_rich_tracker()
    
    # Demo POI processing stage
    with track_stage(ProcessingStage.POI_PROCESSING, total_items=25) as stage_tracker:
        for i in range(25):
            time.sleep(0.1)  # Simulate work
            substage = "poi_query" if i < 10 else "poi_validation" if i < 20 else "clustering"
            stage_tracker.update_progress(advance=1, substage=substage)
    
    time.sleep(0.5)
    
    # Demo isochrone generation
    with track_stage(ProcessingStage.ISOCHRONE_GENERATION, total_items=15) as stage_tracker:
        for i in range(15):
            time.sleep(0.15)  # Simulate work
            substage = "network_download" if i < 5 else "isochrone_calculation"
            stage_tracker.update_progress(advance=1, substage=substage)
    
    time.sleep(0.5)
    
    # Demo census integration
    with track_stage(ProcessingStage.CENSUS_INTEGRATION, total_items=50) as stage_tracker:
        for i in range(50):
            time.sleep(0.05)  # Simulate work
            substage = "block_group_intersection" if i < 20 else "distance_calculation" if i < 35 else "census_data_fetch"
            stage_tracker.update_progress(advance=1, substage=substage)

def demo_status_spinners():
    """Demonstrate status spinners."""
    print_step(5, 6, "Status Spinners Demo", "⏳")
    
    with status_spinner("🌐 Downloading road networks..."):
        time.sleep(3)
    
    with status_spinner("🔍 Querying OpenStreetMap API...", spinner="earth"):
        time.sleep(2)
    
    with status_spinner("📊 Fetching census data...", spinner="clock"):
        time.sleep(2)

def demo_performance_summary():
    """Demonstrate performance summary table."""
    print_step(6, 6, "Performance Summary", "📈")
    
    # Simulate performance metrics
    metrics = {
        "processing_time": 45.7,
        "poi_count": 25,
        "isochrone_count": 25,
        "block_groups_count": 187,
        "memory_usage_mb": 342.8,
        "throughput_per_second": 12.3,
        "api_requests_count": 89,
        "cache_hits_count": 156
    }
    
    print_performance_summary(metrics)
    time.sleep(2)
    
    # Demo file summary
    sample_files = [
        "output/census_data.csv",
        "output/poi_data.json", 
        "output/maps/library_15min_population_map.png",
        "output/maps/interactive_map.html",
        "output/isochrones.geojson"
    ]
    
    print_file_summary("output", sample_files)

def demo_completion():
    """Show completion summary."""
    print_divider("Demo Complete")
    
    # Get tracker for final summary
    tracker = get_rich_tracker()
    tracker.print_summary()
    
    print_success(
        "Rich integration demo completed successfully!\n"
        "SocialMapper now features beautiful terminal output, progress tracking, and enhanced UX.",
        "Demo Complete"
    )
    
    console.print("\n[bold cyan]🎯 Key Rich Features Demonstrated:[/bold cyan]")
    console.print("  ✨ Beautiful banners and branding")
    console.print("  📊 Formatted data tables")
    console.print("  ⚡ Real-time progress bars with metrics")
    console.print("  ⏳ Status spinners for long operations") 
    console.print("  🎨 Color-coded panels for different message types")
    console.print("  📈 Performance monitoring and summaries")
    console.print("  🎭 Enhanced error handling with Rich tracebacks")
    
    console.print(f"\n[dim]Rich library integration adds professional polish to SocialMapper v{__version__}[/dim]")

def main():
    """Run the complete Rich demo."""
    console.print("[bold green]🚀 Starting SocialMapper Rich Integration Demo[/bold green]\n")
    
    try:
        demo_banner()
        time.sleep(1)
        
        demo_messages()
        time.sleep(1)
        
        demo_census_variables()
        time.sleep(1)
        
        demo_poi_table()
        time.sleep(1)
        
        demo_progress_tracking()
        time.sleep(1)
        
        demo_status_spinners()
        time.sleep(1)
        
        demo_performance_summary()
        time.sleep(1)
        
        demo_completion()
        
    except KeyboardInterrupt:
        print_warning("Demo interrupted by user")
        console.print("[dim]Demo stopped early[/dim]")
    except Exception as e:
        print_error(f"Demo encountered an error: {str(e)}")
        # Rich will automatically show beautiful traceback
        raise

if __name__ == "__main__":
    main() 