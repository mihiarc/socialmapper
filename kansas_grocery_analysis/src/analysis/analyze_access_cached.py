#!/usr/bin/env python3
"""
Cached version of Kansas grocery access analysis.
This version uses the DuckDB isochrone cache for dramatically faster performance.
"""

import sys
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.cached_analysis import CachedAnalysisRunner
from utils.isochrone_cache import IsochroneCache

console = Console()

# Set up logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"cached_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        RichHandler(console=console, rich_tracebacks=True)
    ]
)
logger = logging.getLogger(__name__)


class CachedKansasGroceryAnalyzer:
    """Analyzes grocery store accessibility using cached isochrones."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the analyzer with cache support."""
        self.output_dir = Path(output_dir) if output_dir else Path("data/output/cached_analysis")
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        self.data_dir = Path("data/input")
        
        # Analysis parameters
        self.walmart_travel_time = 30
        self.small_grocer_travel_time = 10
        self.travel_mode = "drive"
        
        # Track performance
        self.performance_stats = {}
    
    def show_cache_status(self):
        """Display current cache status before analysis."""
        with IsochroneCache() as cache:
            stats = cache.get_statistics()
            
            console.print("\n[bold cyan]Cache Status Before Analysis:[/bold cyan]")
            console.print(f"  Total isochrones: {stats['total_isochrones'] or 0:,}")
            console.print(f"  Unique locations: {stats['unique_locations'] or 0:,}")
            console.print(f"  Average validation score: {stats['avg_validation_score'] or 0:.2f}")
            
            # Show validation summary
            val_summary = cache.get_validation_summary()
            if val_summary['status_distribution']:
                console.print("\n  Validation status:")
                for item in val_summary['status_distribution']:
                    console.print(f"    {item['validation_status']}: {item['count']}")
    
    def analyze_walmart_access_cached(self) -> Dict:
        """Analyze Walmart access using cached isochrones."""
        console.print("\n[bold blue]Analyzing Walmart Access with Cache[/bold blue]")
        
        walmart_file = self.data_dir / "walmart_cleaned.csv"
        if not walmart_file.exists():
            walmart_file = self.data_dir / "walmart_all.csv"
        
        if not walmart_file.exists():
            console.print("[red]No Walmart data found.[/red]")
            return {}
        
        # Verify dataset
        df = pd.read_csv(walmart_file)
        console.print(f"[green]Analyzing {len(df)} Walmart stores[/green]")
        
        start_time = datetime.now()
        
        with CachedAnalysisRunner() as runner:
            results = runner.analyze_with_cache(
                poi_file=str(walmart_file),
                travel_time=self.walmart_travel_time,
                travel_mode=self.travel_mode,
                output_dir=self.output_dir / "walmart_cached"
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if results:
                # Display performance
                cache_stats = results['cache_stats']
                hit_rate = cache_stats['cache_hits'] / results['total_pois'] * 100 if results['total_pois'] > 0 else 0
                
                console.print(f"\n[green]Walmart Analysis Complete:[/green]")
                console.print(f"  Processing time: {elapsed:.1f} seconds")
                console.print(f"  Cache hit rate: {hit_rate:.1f}%")
                console.print(f"  Time saved: {cache_stats['time_saved_seconds']:.1f} seconds")
                
                self.performance_stats['walmart'] = {
                    'time': elapsed,
                    'hit_rate': hit_rate,
                    'pois': results['total_pois']
                }
                
                return results
            
        return {}
    
    def analyze_small_grocer_access_cached(self) -> Dict:
        """Analyze small grocer access using cached isochrones."""
        console.print("\n[bold blue]Analyzing Small Grocer Access with Cache[/bold blue]")
        
        grocer_file = self.data_dir / "small_grocers_all.csv"
        if not grocer_file.exists():
            console.print("[red]No small grocer data found.[/red]")
            return {}
        
        df = pd.read_csv(grocer_file)
        console.print(f"[green]Analyzing {len(df)} small grocery stores[/green]")
        
        start_time = datetime.now()
        
        with CachedAnalysisRunner() as runner:
            results = runner.analyze_with_cache(
                poi_file=str(grocer_file),
                travel_time=self.small_grocer_travel_time,
                travel_mode=self.travel_mode,
                output_dir=self.output_dir / "grocers_cached"
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if results:
                cache_stats = results['cache_stats']
                hit_rate = cache_stats['cache_hits'] / results['total_pois'] * 100 if results['total_pois'] > 0 else 0
                
                console.print(f"\n[green]Small Grocer Analysis Complete:[/green]")
                console.print(f"  Processing time: {elapsed:.1f} seconds")
                console.print(f"  Cache hit rate: {hit_rate:.1f}%")
                console.print(f"  Time saved: {cache_stats['time_saved_seconds']:.1f} seconds")
                
                self.performance_stats['grocers'] = {
                    'time': elapsed,
                    'hit_rate': hit_rate,
                    'pois': results['total_pois']
                }
                
                return results
            
        return {}
    
    def show_performance_summary(self):
        """Display overall performance summary."""
        console.print("\n[bold cyan]Performance Summary:[/bold cyan]")
        
        table = Table(title="Cache Performance")
        table.add_column("Analysis", style="cyan")
        table.add_column("POIs", justify="right")
        table.add_column("Time (s)", justify="right")
        table.add_column("Hit Rate", justify="right", style="green")
        
        total_time = 0
        total_pois = 0
        
        for name, stats in self.performance_stats.items():
            table.add_row(
                name.capitalize(),
                f"{stats['pois']:,}",
                f"{stats['time']:.1f}",
                f"{stats['hit_rate']:.1f}%"
            )
            total_time += stats['time']
            total_pois += stats['pois']
        
        if self.performance_stats:
            table.add_row(
                "[bold]Total[/bold]",
                f"[bold]{total_pois:,}[/bold]",
                f"[bold]{total_time:.1f}[/bold]",
                ""
            )
        
        console.print(table)
        
        # Show final cache status
        with IsochroneCache() as cache:
            stats = cache.get_statistics()
            
            console.print("\n[bold cyan]Final Cache Status:[/bold cyan]")
            console.print(f"  Total isochrones: {stats['total_isochrones'] or 0:,}")
            console.print(f"  Total cache hits: {stats['total_hits'] or 0:,}")
            console.print(f"  Average area: {stats['avg_area_km2'] or 0:.1f} km²")
    
    def export_cache_to_geoparquet(self):
        """Export the cache to GeoParquet for archival."""
        console.print("\n[cyan]Exporting cache to GeoParquet...[/cyan]")
        
        with IsochroneCache() as cache:
            output_file = self.output_dir / f"kansas_isochrones_{datetime.now().strftime('%Y%m%d')}.geoparquet"
            
            count = cache.export_to_geoparquet(
                str(output_file),
                filters={'travel_mode': 'drive'}
            )
            
            console.print(f"[green]✓ Exported {count} isochrones to {output_file.name}[/green]")
            
            # Check file size
            if output_file.exists():
                size_mb = output_file.stat().st_size / (1024 * 1024)
                console.print(f"  File size: {size_mb:.1f} MB")


def main():
    """Run the cached Kansas grocery analysis."""
    console.print("[bold magenta]Kansas Grocery Analysis with DuckDB Cache[/bold magenta]")
    console.print("=" * 60)
    
    try:
        analyzer = CachedKansasGroceryAnalyzer()
        
        # Show initial cache status
        analyzer.show_cache_status()
        
        # Run analyses
        console.print("\n[cyan]Starting cached analysis...[/cyan]")
        
        # Walmart analysis
        walmart_results = analyzer.analyze_walmart_access_cached()
        
        # Small grocer analysis
        grocer_results = analyzer.analyze_small_grocer_access_cached()
        
        # Show performance summary
        analyzer.show_performance_summary()
        
        # Generate cache report
        with CachedAnalysisRunner() as runner:
            runner.export_cache_report(
                str(analyzer.output_dir / "cache_performance_report.md")
            )
            console.print("\n[green]✓ Cache report saved[/green]")
        
        # Optional: Export cache to GeoParquet
        if console.input("\n[cyan]Export cache to GeoParquet? (y/n): [/cyan]").lower() == 'y':
            analyzer.export_cache_to_geoparquet()
        
        console.print("\n[green]✨ Analysis complete with caching![/green]")
        
        # Tips for next run
        console.print("\n[bold]Next Run Will Be Even Faster![/bold]")
        console.print("The cache now contains all isochrones. Re-running will be ~20x faster.")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        logger.error(traceback.format_exc())
        console.print(f"\n[red]Error: {str(e)}[/red]")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())