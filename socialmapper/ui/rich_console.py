#!/usr/bin/env python3
"""
Rich Console Module for SocialMapper.

This module provides a centralized Rich console for consistent beautiful
output throughout the SocialMapper application.
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from rich import box
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.pretty import pprint
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    Task,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.status import Status
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.traceback import install as install_rich_traceback

# Install Rich tracebacks globally for the package
install_rich_traceback(show_locals=True)


class RichProgressColumn(ProgressColumn):
    """Custom progress column showing items per second."""

    def render(self, task: "Task") -> Text:
        """Render the progress column."""
        if task.speed is None:
            return Text("", style="progress.percentage")

        if task.speed >= 1:
            return Text(f"{task.speed:.1f} items/sec", style="progress.percentage")
        else:
            return Text(f"{1/task.speed:.1f} sec/item", style="progress.percentage")


# Compatibility class for existing tqdm usage
class RichProgressWrapper:
    """Wrapper to make Rich Progress compatible with existing tqdm usage."""

    def __init__(self, iterable=None, desc="", total=None, unit="it", **kwargs):
        self.iterable = iterable
        self.desc = desc
        self.total = total or (len(iterable) if iterable else None)
        self.unit = unit
        self.position = 0
        self.task_id = None
        self.progress_instance = None

        # Create progress instance
        self.progress_instance = Progress(
            SpinnerColumn(),
            TextColumn(f"[progress.description]{desc}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            TextColumn("•"),
            RichProgressColumn(),
            console=console,
            refresh_per_second=10,
        )

        # Use try-except to handle Rich live display conflicts
        try:
            self.progress_instance.start()
            self.task_id = self.progress_instance.add_task(desc, total=self.total)
        except Exception:
            # If we can't start the progress display (e.g., another is active),
            # fallback to simple print statements
            console.print(f"🔄 {desc}")
            self.progress_instance = None
            self.task_id = None

    def __iter__(self):
        if self.iterable:
            for item in self.iterable:
                yield item
                self.update(1)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def update(self, n=1):
        if self.progress_instance and self.task_id is not None:
            try:
                self.progress_instance.update(self.task_id, advance=n)
            except Exception:
                # If progress update fails, just track position
                pass
        self.position += n

        # If no progress display, show periodic updates
        if (
            self.progress_instance is None
            and self.total
            and self.position % max(1, self.total // 10) == 0
        ):
            percentage = (self.position / self.total) * 100
            console.print(f"  Progress: {self.position}/{self.total} ({percentage:.1f}%)")

    def set_description(self, desc):
        if self.progress_instance and self.task_id is not None:
            self.progress_instance.update(self.task_id, description=desc)

    def close(self):
        if self.progress_instance:
            try:
                self.progress_instance.stop()
            except Exception:
                # Ignore errors during cleanup
                pass
            finally:
                self.progress_instance = None
                self.task_id = None

    def write(self, message):
        console.print(message)


def rich_tqdm(*args, **kwargs):
    """Drop-in replacement for tqdm using Rich."""
    return RichProgressWrapper(*args, **kwargs)


def clear_console_state():
    """Clear any active Rich console state to prevent conflicts."""
    try:
        # Clear any active live displays
        if hasattr(console, "_live") and console._live is not None:
            console.clear_live()
    except Exception:
        # Ignore errors during cleanup
        pass


@contextmanager
def progress_bar(
    description: str, total: Optional[int] = None, transient: bool = False, disable: bool = False
):
    """
    Context manager for Rich progress bars.

    Args:
        description: Progress description
        total: Total number of items (None for indeterminate)
        transient: Whether to clear progress bar when done
        disable: Whether to disable progress bar

    Yields:
        Progress instance
    """
    if disable:
        # Return a dummy progress instance
        class DummyProgress:
            def add_task(self, *args, **kwargs):
                return 0

            def update(self, *args, **kwargs):
                pass

            def advance(self, *args, **kwargs):
                pass

        yield DummyProgress()
        return

    # Create custom progress with performance metrics
    custom_progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        TextColumn("•"),
        RichProgressColumn(),
        console=console,
        transient=transient,
        refresh_per_second=10,
    )

    with custom_progress:
        task_id = custom_progress.add_task(description, total=total)
        custom_progress.task_id = task_id  # Store for convenience
        yield custom_progress


# Global console instance for SocialMapper
console = Console()

# Rich logging handler
rich_handler = RichHandler(
    console=console, show_time=True, show_path=False, markup=True, rich_tracebacks=True
)


def setup_rich_logging(level: str = "INFO", show_time: bool = True, show_path: bool = False):
    """
    Set up Rich-enhanced logging for SocialMapper.

    Args:
        level: Logging level (default: "INFO")
        show_time: Whether to show timestamps
        show_path: Whether to show file paths
    """
    # Convert string level to int
    if isinstance(level, str):
        level = getattr(logging, level.upper())

    # Configure root logger with Rich handler
    logging.basicConfig(level=level, format="%(message)s", datefmt="[%X]", handlers=[rich_handler])

    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a Rich-enabled logger.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def print_statistics(stats: dict, title: str = "Statistics", **kwargs) -> None:
    """Print statistics in a formatted table."""
    table = Table(title=title, show_header=True, **kwargs)
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="cyan")

    for key, value in stats.items():
        # Format the key
        formatted_key = str(key).replace("_", " ").title()

        # Format the value
        if isinstance(value, float):
            if 0 < value < 1:
                formatted_value = f"{value:.1%}"
            else:
                formatted_value = f"{value:.1f}"
        elif isinstance(value, int):
            formatted_value = f"{value:,}"
        else:
            formatted_value = str(value)

        table.add_row(formatted_key, formatted_value)

    console.print(table)


def print_panel(
    content: str,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    style: str = "cyan",
    **kwargs,
) -> None:
    """Print content in a styled panel."""
    panel = Panel(content, title=title, subtitle=subtitle, border_style=style, **kwargs)
    console.print(panel)


def print_table(
    data: List[Dict[str, Any]], title: Optional[str] = None, show_header: bool = True, **kwargs
) -> None:
    """Print data as a formatted table."""
    if not data:
        print_warning("No data to display in table")
        return

    table = Table(title=title, show_header=show_header, **kwargs)

    # Add columns from first row
    for key in data[0].keys():
        table.add_column(str(key).replace("_", " ").title())

    # Add rows
    for row in data:
        table.add_row(*[str(value) for value in row.values()])

    console.print(table)


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
        border_style="cyan",
    )
    console.print(panel)


def create_streamlit_banner(
    title: str, subtitle: Optional[str] = None, version: Optional[str] = None
) -> str:
    """
    Create a markdown banner for Streamlit apps.

    Args:
        title: Main title text
        subtitle: Optional subtitle
        version: Optional version string

    Returns:
        Markdown formatted banner string
    """
    if subtitle and version:
        return f"""
# 🏘️ {title}
### {subtitle}
*Version {version}*

---
"""
    elif subtitle:
        return f"""
# 🏘️ {title}
### {subtitle}

---
"""
    elif version:
        return f"""
# 🏘️ {title}
*Version {version}*

---
"""
    else:
        return f"""
# 🏘️ {title}

---
"""


def print_success(message: str, title: str = "Success"):
    """Print a success message in a green panel."""
    panel = Panel(
        f"[bold green]✅ {message}[/bold green]",
        title=f"🎉 {title}",
        box=box.ROUNDED,
        border_style="green",
    )
    console.print(panel)


def print_error(message: str, title: str = "Error"):
    """Print an error message in a red panel."""
    panel = Panel(
        f"[bold red]❌ {message}[/bold red]",
        title=f"💥 {title}",
        box=box.ROUNDED,
        border_style="red",
    )
    console.print(panel)


def print_warning(message: str, title: str = "Warning"):
    """Print a warning message in an orange panel."""
    panel = Panel(
        f"[bold yellow]⚠️ {message}[/bold yellow]",
        title=f"🚨 {title}",
        box=box.ROUNDED,
        border_style="yellow",
    )
    console.print(panel)


def print_info(message: str, title: Optional[str] = None):
    """Print an info message in a blue panel."""
    if title:
        panel = Panel(
            f"[bold blue]ℹ️ {message}[/bold blue]",
            title=f"📢 {title}",
            box=box.ROUNDED,
            border_style="blue",
        )
        console.print(panel)
    else:
        console.print(f"[blue]ℹ️ {message}[/blue]")


@contextmanager
def status_spinner(message: str, spinner: str = "dots"):
    """Context manager for showing a status spinner."""
    with Status(message, spinner=spinner, console=console) as status:
        yield status


@contextmanager
def status(message: str, spinner: str = "dots"):
    """Context manager for showing a status spinner (alias for status_spinner)."""
    with Status(message, spinner=spinner, console=console) as status_obj:
        yield status_obj


def create_data_table(
    title: str,
    columns: List[Dict[str, Any]],
    rows: List[List[str]],
    show_header: bool = True,
    box_style: box.Box = box.ROUNDED,
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
            col["name"],
            style=col.get("style", "default"),
            justify=col.get("justify", "left"),
            no_wrap=col.get("no_wrap", False),
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


def print_performance_summary(metrics: Dict[str, Any]):
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
    print_info(
        f"Generating {travel_time}-minute travel areas for {count:,} POIs", "Isochrone Generation"
    )


def log_census_integration_start(count: int):
    """Log the start of census data integration."""
    print_info(f"Integrating census data for {count:,} block groups", "Census Integration")


def log_export_start(formats: List[str]):
    """Log the start of data export."""
    formats_str = ", ".join(formats)
    print_info(f"Exporting results in formats: {formats_str}", "Data Export")


def create_rich_panel(content: str, title: str = "", style: str = "cyan") -> str:
    """
    Create a rich-styled panel for Streamlit (returns markdown).

    Args:
        content: Panel content
        title: Panel title
        style: Panel style/color

    Returns:
        Markdown formatted panel
    """
    emoji_map = {"cyan": "💎", "green": "✅", "red": "❌", "yellow": "⚠️", "blue": "ℹ️"}

    emoji = emoji_map.get(style, "📋")

    if title:
        return f"""
> {emoji} **{title}**
> 
> {content}
"""
    else:
        return f"""
> {emoji} {content}
"""


def create_performance_table(data: Dict[str, Any]) -> str:
    """
    Create a performance comparison table for Streamlit (returns markdown).

    Args:
        data: Performance data dictionary

    Returns:
        Markdown formatted table
    """
    if not data:
        return "No performance data available."

    # Create markdown table
    table_lines = ["| Metric | Value |", "|--------|-------|"]

    for key, value in data.items():
        formatted_key = key.replace("_", " ").title()
        if isinstance(value, (int, float)):
            if "time" in key.lower():
                formatted_value = f"{value:.2f}s"
            elif "count" in key.lower():
                formatted_value = f"{value:,}"
            else:
                formatted_value = str(value)
        else:
            formatted_value = str(value)

        table_lines.append(f"| {formatted_key} | {formatted_value} |")

    return "\n".join(table_lines)


# Export the main console for direct use
__all__ = [
    "console",
    "setup_rich_logging",
    "print_banner",
    "create_streamlit_banner",
    "print_success",
    "print_error",
    "print_warning",
    "print_info",
    "status_spinner",
    "create_data_table",
    "create_rich_panel",
    "create_performance_table",
    "print_census_variables_table",
    "print_poi_summary_table",
    "print_performance_summary",
    "print_file_summary",
    "print_json",
    "print_step",
    "print_divider",
    "log_poi_processing_start",
    "log_isochrone_generation_start",
    "log_census_integration_start",
    "log_export_start",
]
