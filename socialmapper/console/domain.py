#!/usr/bin/env python3
"""Domain-specific display functions for SocialMapper.

This module provides specialized display functions for census data, POIs,
and other SocialMapper-specific data types.
"""

import os
from typing import Any

from rich import box
from rich.table import Table

from .core import console, print_info, print_warning


def print_census_variables_table(variables: dict[str, str]):
    """Print available census variables in a formatted table."""
    table = Table(title="📊 Available Census Variables", box=box.ROUNDED)
    table.add_column("Variable Name", style="cyan", no_wrap=True)
    table.add_column("Census Code", style="green")

    for code, name in sorted(variables.items()):
        table.add_row(name, code)

    console.print(table)


def print_poi_summary_table(pois: list[dict[str, Any]]):
    """Print a summary table of POIs."""
    if not pois:
        print_warning("No POIs found")
        return

    table = Table(title=f"📍 Found {len(pois)} Points of Interest", box=box.ROUNDED)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="yellow")
    table.add_column("Coordinates", style="green")
    table.add_column("Tags", style="dim")

    for poi in pois[:10]:  # Show first 10 POIs
        tags_str = ", ".join([f"{k}={v}" for k, v in poi.get("tags", {}).items()][:3])
        if len(poi.get("tags", {})) > 3:
            tags_str += "..."

        table.add_row(
            poi.get("name", "Unknown"),
            poi.get("type", "Unknown"),
            f"{poi.get('lat', 0):.4f}, {poi.get('lon', 0):.4f}",
            tags_str or "None",
        )

    if len(pois) > 10:
        table.add_section()
        table.add_row(f"[dim]... and {len(pois) - 10} more POIs[/dim]", "", "", "")

    console.print(table)


def print_performance_summary(metrics: dict[str, Any]):
    """Print a performance summary table."""
    table = Table(title="⚡ Performance Summary", box=box.ROUNDED)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green", justify="right")
    table.add_column("Unit", style="dim")

    for metric, value in metrics.items():
        if metric.endswith("_time"):
            table.add_row(metric.replace("_", " ").title(), f"{value:.2f}", "seconds")
        elif metric.endswith("_count"):
            table.add_row(metric.replace("_", " ").title(), f"{value:,}", "items")
        elif metric.endswith("_mb"):
            table.add_row(metric.replace("_", " ").title(), f"{value:.1f}", "MB")
        elif metric.endswith("_per_second"):
            table.add_row(metric.replace("_", " ").title(), f"{value:.1f}", "items/sec")
        else:
            table.add_row(metric.replace("_", " ").title(), str(value), "")

    console.print(table)


def print_file_summary(output_dir: str, files: list[str]):
    """Print a summary of generated files."""
    if not files:
        print_warning("No files were generated")
        return

    table = Table(title=f"📁 Generated Files in {output_dir}", box=box.ROUNDED)
    table.add_column("File Type", style="cyan", no_wrap=True)
    table.add_column("Filename", style="green")
    table.add_column("Status", style="yellow")

    for file_path in files:
        filename = os.path.basename(file_path)
        if filename.endswith(".csv"):
            file_type = "📋 Data (CSV)"
        elif filename.endswith(".json"):
            file_type = "📄 Data (JSON)"
        elif filename.endswith(".png"):
            file_type = "🖼️ Map (PNG)"
        elif filename.endswith(".html"):
            file_type = "🌐 Interactive Map"
        else:
            file_type = "📄 File"

        exists = os.path.exists(file_path)
        status = "✅ Created" if exists else "❌ Failed"

        table.add_row(file_type, filename, status)

    console.print(table)


# Convenience functions for common use cases
def log_poi_processing_start(count: int):
    """Log the start of POI processing."""
    print_info(f"Starting to process {count:,} points of interest", "POI Processing")


def log_isochrone_generation_start(count: int, travel_time: int):
    """Log the start of isochrone generation."""
    print_info(
        f"Generating {travel_time}-minute travel areas for {count:,} POIs", "Isochrone Generation"
    )


def log_census_integration_start(count: int):
    """Log the start of census data integration."""
    print_info(f"Integrating census data for {count:,} block groups", "Census Integration")


def log_export_start(formats: list[str]):
    """Log the start of data export."""
    formats_str = ", ".join(formats)
    print_info(f"Exporting results in formats: {formats_str}", "Data Export")
