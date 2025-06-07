#!/usr/bin/env python3
"""
Rich Console Module for SocialMapper.

This module provides a centralized Rich console for consistent beautiful
output throughout the SocialMapper application.
"""

import logging
from typing import Optional, Any, Dict, List, Union
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.status import Status
from rich.progress import Progress
from rich import box
from rich.pretty import pprint
from rich.syntax import Syntax
from rich.traceback import install as install_rich_traceback
from contextlib import contextmanager

# Install Rich tracebacks globally for the package
install_rich_traceback(show_locals=True)

# Global console instance for SocialMapper
console = Console()

# Rich logging handler
rich_handler = RichHandler(
    console=console,
    show_time=True,
    show_path=False,
    markup=True,
    rich_tracebacks=True
)

def setup_rich_logging(level: int = logging.INFO):
    """
    Set up Rich-enhanced logging for SocialMapper.
    
    Args:
        level: Logging level (default: INFO)
    """
    # Configure root logger with Rich handler
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[rich_handler]
    )
    
    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)


def print_banner(title: str, subtitle: Optional[str] = None, version: Optional[str] = None):
    """
    Print a beautiful banner for SocialMapper.
    
    Args:
        title: Main title text
        subtitle: Optional subtitle
        version: Optional version string
    """
    if subtitle:
        banner_text = f"[bold cyan]{title}[/bold cyan]\n[dim]{subtitle}[/dim]"
    else:
        banner_text = f"[bold cyan]{title}[/bold cyan]"
    
    panel = Panel(
        banner_text,
        title="🏘️ SocialMapper",
        subtitle=f"v{version}" if version else None,
        box=box.DOUBLE,
        padding=(1, 2),
        border_style="cyan"
    )
    console.print(panel)


def print_success(message: str, title: str = "Success"):
    """Print a success message in a green panel."""
    panel = Panel(
        f"[bold green]✅ {message}[/bold green]",
        title=f"🎉 {title}",
        box=box.ROUNDED,
        border_style="green"
    )
    console.print(panel)


def print_error(message: str, title: str = "Error"):
    """Print an error message in a red panel."""
    panel = Panel(
        f"[bold red]❌ {message}[/bold red]",
        title=f"💥 {title}",
        box=box.ROUNDED,
        border_style="red"
    )
    console.print(panel)


def print_warning(message: str, title: str = "Warning"):
    """Print a warning message in an orange panel."""
    panel = Panel(
        f"[bold yellow]⚠️ {message}[/bold yellow]",
        title=f"🚨 {title}",
        box=box.ROUNDED,
        border_style="yellow"
    )
    console.print(panel)


def print_info(message: str, title: Optional[str] = None):
    """Print an info message in a blue panel."""
    if title:
        panel = Panel(
            f"[bold blue]ℹ️ {message}[/bold blue]",
            title=f"📢 {title}",
            box=box.ROUNDED,
            border_style="blue"
        )
        console.print(panel)
    else:
        console.print(f"[blue]ℹ️ {message}[/blue]")


@contextmanager
def status_spinner(message: str, spinner: str = "dots"):
    """Context manager for showing a status spinner."""
    with Status(message, spinner=spinner, console=console) as status:
        yield status


def create_data_table(
    title: str,
    columns: List[Dict[str, Any]],
    rows: List[List[str]],
    show_header: bool = True,
    box_style: box.Box = box.ROUNDED
) -> Table:
    """
    Create a formatted data table.
    
    Args:
        title: Table title
        columns: List of column definitions with keys: 'name', 'style', 'justify'
        rows: List of row data
        show_header: Whether to show the header
        box_style: Box style for the table
        
    Returns:
        Configured Rich Table
    """
    table = Table(title=title, show_header=show_header, box=box_style)
    
    # Add columns
    for col in columns:
        table.add_column(
            col['name'],
            style=col.get('style', 'default'),
            justify=col.get('justify', 'left'),
            no_wrap=col.get('no_wrap', False)
        )
    
    # Add rows
    for row in rows:
        table.add_row(*row)
    
    return table


def print_census_variables_table(variables: Dict[str, str]):
    """Print available census variables in a formatted table."""
    table = Table(title="📊 Available Census Variables", box=box.ROUNDED)
    table.add_column("Variable Name", style="cyan", no_wrap=True)
    table.add_column("Census Code", style="green")
    
    for code, name in sorted(variables.items()):
        table.add_row(name, code)
    
    console.print(table)


def print_poi_summary_table(pois: List[Dict[str, Any]]):
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
        tags_str = ", ".join([f"{k}={v}" for k, v in poi.get('tags', {}).items()][:3])
        if len(poi.get('tags', {})) > 3:
            tags_str += "..."
        
        table.add_row(
            poi.get('name', 'Unknown'),
            poi.get('type', 'Unknown'),
            f"{poi.get('lat', 0):.4f}, {poi.get('lon', 0):.4f}",
            tags_str or "None"
        )
    
    if len(pois) > 10:
        table.add_section()
        table.add_row(f"[dim]... and {len(pois) - 10} more POIs[/dim]", "", "", "")
    
    console.print(table)


def print_performance_summary(metrics: Dict[str, Any]):
    """Print a performance summary table."""
    table = Table(title="⚡ Performance Summary", box=box.ROUNDED)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green", justify="right")
    table.add_column("Unit", style="dim")
    
    for metric, value in metrics.items():
        if metric.endswith('_time'):
            table.add_row(metric.replace('_', ' ').title(), f"{value:.2f}", "seconds")
        elif metric.endswith('_count'):
            table.add_row(metric.replace('_', ' ').title(), f"{value:,}", "items")
        elif metric.endswith('_mb'):
            table.add_row(metric.replace('_', ' ').title(), f"{value:.1f}", "MB")
        elif metric.endswith('_per_second'):
            table.add_row(metric.replace('_', ' ').title(), f"{value:.1f}", "items/sec")
        else:
            table.add_row(metric.replace('_', ' ').title(), str(value), "")
    
    console.print(table)


def print_file_summary(output_dir: str, files: List[str]):
    """Print a summary of generated files."""
    if not files:
        print_warning("No files were generated")
        return
    
    table = Table(title=f"📁 Generated Files in {output_dir}", box=box.ROUNDED)
    table.add_column("File Type", style="cyan", no_wrap=True)
    table.add_column("Filename", style="green")
    table.add_column("Status", style="yellow")
    
    for file_path in files:
        import os
        filename = os.path.basename(file_path)
        if filename.endswith('.csv'):
            file_type = "📋 Data (CSV)"
        elif filename.endswith('.json'):
            file_type = "📄 Data (JSON)"
        elif filename.endswith('.png'):
            file_type = "🖼️ Map (PNG)"
        elif filename.endswith('.html'):
            file_type = "🌐 Interactive Map"
        else:
            file_type = "📄 File"
        
        exists = os.path.exists(file_path)
        status = "✅ Created" if exists else "❌ Failed"
        
        table.add_row(file_type, filename, status)
    
    console.print(table)


def print_json(data: Any, title: Optional[str] = None):
    """Pretty print JSON data with syntax highlighting."""
    if title:
        console.print(f"\n[bold cyan]{title}[/bold cyan]")
    
    try:
        import json
        json_str = json.dumps(data, indent=2, default=str)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
        console.print(syntax)
    except Exception:
        # Fallback to pretty print
        pprint(data)


def print_step(step_number: int, total_steps: int, description: str, emoji: str = "🔄"):
    """Print a numbered step in the process."""
    progress_text = f"[bold cyan]Step {step_number}/{total_steps}:[/bold cyan]"
    console.print(f"\n{progress_text} {emoji} {description}")


def print_divider(title: Optional[str] = None):
    """Print a visual divider."""
    if title:
        console.print(f"\n[bold blue]{'─' * 20} {title} {'─' * 20}[/bold blue]")
    else:
        console.print(f"\n[dim]{'─' * 60}[/dim]")


# Convenience functions for common use cases
def log_poi_processing_start(count: int):
    """Log the start of POI processing."""
    print_info(f"Starting to process {count:,} points of interest", "POI Processing")

def log_isochrone_generation_start(count: int, travel_time: int):
    """Log the start of isochrone generation."""
    print_info(f"Generating {travel_time}-minute travel areas for {count:,} POIs", "Isochrone Generation")

def log_census_integration_start(count: int):
    """Log the start of census data integration."""
    print_info(f"Integrating census data for {count:,} block groups", "Census Integration")

def log_export_start(formats: List[str]):
    """Log the start of data export."""
    formats_str = ", ".join(formats)
    print_info(f"Exporting results in formats: {formats_str}", "Data Export")

# Export the main console for direct use
__all__ = [
    'console',
    'setup_rich_logging',
    'print_banner',
    'print_success',
    'print_error', 
    'print_warning',
    'print_info',
    'status_spinner',
    'create_data_table',
    'print_census_variables_table',
    'print_poi_summary_table',
    'print_performance_summary',
    'print_file_summary',
    'print_json',
    'print_step',
    'print_divider',
    'log_poi_processing_start',
    'log_isochrone_generation_start',
    'log_census_integration_start',
    'log_export_start'
] 