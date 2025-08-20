#!/usr/bin/env python3
"""
Generate isochrones for Libby, Montana with distance statistics.

This script creates drive-time isochrones for 30, 60, 90, and 120 minutes
from Libby, MT (48.389, -115.556340) and analyzes the distance statistics.
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

# Import socialmapper components
from socialmapper.isochrone import create_isochrone_from_poi, TravelMode
from socialmapper.console import setup_rich_logging, get_logger
from rich.console import Console
from rich.table import Table
from rich import box
from rich.progress import track

# Setup console and logging
console = Console()
logger = get_logger(__name__)
setup_rich_logging(level="INFO")

def generate_libby_isochrones():
    """Generate isochrones for multiple travel times from Libby, MT."""
    
    # Libby, Montana coordinates
    poi = {
        "id": "libby_mt_center",
        "lat": 48.389,
        "lon": -115.556340,
        "tags": {
            "name": "Libby, Montana",
            "place": "town",
            "population": "2,775",  # 2020 census
            "elevation_m": 636,  # ~2,087 feet
            "description": "Small town in northwest Montana near Kootenai National Forest"
        }
    }
    
    # Travel times in minutes (30, 60, 90, 120)
    travel_times = [30, 60, 90, 120]
    
    console.print("\n[bold cyan]🏔️ Generating Isochrones for Libby, Montana[/bold cyan]")
    console.print(f"[dim]Location: {poi['lat']:.3f}°N, {abs(poi['lon']):.3f}°W[/dim]")
    console.print(f"[dim]Population: {poi['tags']['population']} | Elevation: {poi['tags']['elevation_m']}m[/dim]")
    console.print(f"[dim]Travel times: {', '.join(str(t) for t in travel_times)} minutes[/dim]")
    console.print(f"[dim]Travel mode: Drive[/dim]\n")
    
    # Create output directory
    output_dir = Path("output/libby_mt_isochrones")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Store results
    results = []
    isochrone_gdfs = []
    
    # Generate isochrones for each travel time
    for travel_time in travel_times:
        console.print(f"[yellow]⏱️  Generating {travel_time}-minute isochrone...[/yellow]")
        
        try:
            # Generate isochrone with distance statistics
            isochrone_gdf = create_isochrone_from_poi(
                poi=poi,
                travel_time_limit=travel_time,
                output_dir=str(output_dir),
                save_file=False,  # We'll save manually with more details
                travel_mode=TravelMode.DRIVE,
                simplify_tolerance=0.001  # Simplify for visualization
            )
            
            if isochrone_gdf is not None and not isochrone_gdf.empty:
                # Extract statistics
                row = isochrone_gdf.iloc[0]
                
                # Calculate area
                iso_projected = isochrone_gdf.to_crs("EPSG:3857")
                area_km2 = iso_projected.geometry.area.iloc[0] / 1_000_000
                
                # Calculate perimeter
                perimeter_km = iso_projected.geometry.length.iloc[0] / 1000
                
                # Store result
                result = {
                    "travel_time_min": travel_time,
                    "travel_time_hours": travel_time / 60,
                    "min_distance_km": row.get('min_distance_km', 0),
                    "max_distance_km": row.get('max_distance_km', 0),
                    "avg_distance_km": row.get('avg_distance_km', 0),
                    "median_distance_km": row.get('median_distance_km', 0),
                    "std_dev_km": row.get('std_dev_distance_km', 0),
                    "reachable_nodes": int(row.get('reachable_nodes', 0)),
                    "analyzed_paths": int(row.get('analyzed_paths', 0)),
                    "area_km2": area_km2,
                    "perimeter_km": perimeter_km,
                    "avg_speed_kmh": row.get('avg_distance_km', 0) / (travel_time / 60) if travel_time > 0 else 0
                }
                
                results.append(result)
                isochrone_gdfs.append(isochrone_gdf)
                
                console.print(f"[green]✓ {travel_time}-minute isochrone generated successfully[/green]")
                
                # Save individual isochrone
                output_file = output_dir / f"libby_mt_{travel_time}min_isochrone.geojson"
                isochrone_gdf.to_file(output_file, driver="GeoJSON")
                console.print(f"[dim]  Saved to: {output_file}[/dim]")
                
        except Exception as e:
            console.print(f"[red]✗ Error generating {travel_time}-minute isochrone: {e}[/red]")
            logger.error(f"Failed to generate {travel_time}-minute isochrone", exc_info=True)
    
    # Display results table
    console.print("\n[bold cyan]📊 Isochrone Statistics for Libby, Montana[/bold cyan]\n")
    
    table = Table(box=box.ROUNDED)
    table.add_column("Time\n(min)", style="cyan", justify="center")
    table.add_column("Min Dist\n(km)", style="green", justify="right")
    table.add_column("Max Dist\n(km)", style="yellow", justify="right")
    table.add_column("Avg Dist\n(km)", style="magenta", justify="right")
    table.add_column("Median\n(km)", style="blue", justify="right")
    table.add_column("Std Dev\n(km)", style="dim", justify="right")
    table.add_column("Area\n(km²)", style="bright_white", justify="right")
    table.add_column("Nodes", style="white", justify="right")
    table.add_column("Avg Speed\n(km/h)", style="cyan", justify="right")
    
    for r in results:
        table.add_row(
            str(r["travel_time_min"]),
            f"{r['min_distance_km']:.1f}",
            f"{r['max_distance_km']:.1f}",
            f"{r['avg_distance_km']:.1f}",
            f"{r['median_distance_km']:.1f}",
            f"{r['std_dev_km']:.1f}",
            f"{r['area_km2']:.0f}",
            f"{r['reachable_nodes']:,}",
            f"{r['avg_speed_kmh']:.1f}"
        )
    
    console.print(table)
    
    # Geographic analysis
    console.print("\n[bold cyan]🗺️ Geographic Analysis[/bold cyan]")
    
    if len(results) > 0:
        # Estimate reach to major locations
        console.print("\n[yellow]Estimated Reach from Libby, MT:[/yellow]")
        
        landmarks = {
            30: ["Troy, MT", "Bull Lake", "Yaak River Valley"],
            60: ["Kalispell, MT", "Eureka, MT", "Bonners Ferry, ID"],
            90: ["Whitefish, MT", "Sandpoint, ID", "Cranbrook, BC (Canada)"],
            120: ["Coeur d'Alene, ID", "Missoula, MT", "Fernie, BC (Canada)"]
        }
        
        for time_min in travel_times:
            if time_min in landmarks and any(r['travel_time_min'] == time_min for r in results):
                result = next(r for r in results if r['travel_time_min'] == time_min)
                console.print(f"\n[cyan]{time_min} minutes ({result['max_distance_km']:.0f} km max):[/cyan]")
                for place in landmarks[time_min]:
                    console.print(f"  • {place}")
        
        # Distance analysis
        console.print("\n[yellow]Distance vs Time Analysis:[/yellow]")
        
        if len(results) >= 2:
            # Compare progressive increases
            for i in range(1, len(results)):
                prev = results[i-1]
                curr = results[i]
                
                time_increase = curr['travel_time_min'] - prev['travel_time_min']
                dist_increase = curr['max_distance_km'] - prev['max_distance_km']
                area_increase = curr['area_km2'] - prev['area_km2']
                
                console.print(f"\n{prev['travel_time_min']}→{curr['travel_time_min']} min (+{time_increase} min):")
                console.print(f"  • Distance: +{dist_increase:.1f} km (to {curr['max_distance_km']:.1f} km)")
                console.print(f"  • Area: +{area_increase:.0f} km² (to {curr['area_km2']:.0f} km²)")
                console.print(f"  • Speed: {dist_increase/(time_increase/60):.1f} km/h for this segment")
    
    # Save combined results
    if len(isochrone_gdfs) > 0:
        # Combine all isochrones
        combined_gdf = pd.concat(isochrone_gdfs, ignore_index=True)
        combined_file = output_dir / "libby_mt_all_isochrones.geojson"
        combined_gdf.to_file(combined_file, driver="GeoJSON")
        console.print(f"\n[dim]Combined isochrones saved to: {combined_file}[/dim]")
    
    # Save statistics to CSV
    if results:
        df = pd.DataFrame(results)
        stats_file = output_dir / "libby_mt_distance_statistics.csv"
        df.to_csv(stats_file, index=False)
        console.print(f"[dim]Statistics saved to: {stats_file}[/dim]")
        
        # Save summary JSON
        summary = {
            "location": {
                "name": "Libby, Montana",
                "coordinates": {"lat": poi["lat"], "lon": poi["lon"]},
                "metadata": poi["tags"]
            },
            "analysis_date": datetime.now().isoformat(),
            "travel_mode": "drive",
            "travel_times_minutes": travel_times,
            "statistics": results,
            "geographic_notes": {
                "terrain": "Mountainous region with Kootenai National Forest",
                "major_highways": ["US Route 2", "Montana Highway 37"],
                "border_proximity": "~65 km to Canadian border",
                "nearest_cities": {
                    "Kalispell, MT": "~90 km southeast",
                    "Spokane, WA": "~200 km southwest",
                    "Missoula, MT": "~190 km southeast"
                }
            }
        }
        
        summary_file = output_dir / "libby_mt_analysis_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        console.print(f"[dim]Analysis summary saved to: {summary_file}[/dim]")
    
    console.print("\n[bold green]✅ Analysis Complete![/bold green]")
    console.print(f"[dim]All files saved to: {output_dir}/[/dim]")
    
    # Terrain impact analysis
    console.print("\n[bold cyan]🏔️ Terrain Impact Analysis[/bold cyan]")
    if len(results) >= 2:
        # Calculate efficiency metric (actual distance vs theoretical straight-line)
        for r in results:
            # Theoretical max distance at highway speed (100 km/h)
            theoretical_max = (r['travel_time_min'] / 60) * 100
            efficiency = (r['max_distance_km'] / theoretical_max) * 100 if theoretical_max > 0 else 0
            
            console.print(f"\n{r['travel_time_min']} minutes:")
            console.print(f"  • Actual max distance: {r['max_distance_km']:.1f} km")
            console.print(f"  • Theoretical max (100 km/h): {theoretical_max:.1f} km")
            console.print(f"  • Network efficiency: {efficiency:.1f}%")
            
            if efficiency < 70:
                console.print(f"  • [yellow]Impact: Significant terrain/road limitations[/yellow]")
            elif efficiency < 85:
                console.print(f"  • [blue]Impact: Moderate terrain effects[/blue]")
            else:
                console.print(f"  • [green]Impact: Good highway access[/green]")
    
    return results, isochrone_gdfs


if __name__ == "__main__":
    console.print("=" * 70)
    console.print("[bold cyan]LIBBY, MONTANA ISOCHRONE ANALYSIS[/bold cyan]")
    console.print("=" * 70)
    
    try:
        results, isochrones = generate_libby_isochrones()
        
        console.print("\n[bold cyan]📍 Key Findings:[/bold cyan]")
        console.print("• Libby's location in mountainous northwest Montana affects travel distances")
        console.print("• Limited highway infrastructure constrains long-distance travel efficiency")
        console.print("• Canadian border proximity expands potential reach to the north")
        console.print("• Kootenai National Forest creates natural barriers to the east")
        
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")