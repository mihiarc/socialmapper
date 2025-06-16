"""Rich console and logging utilities for SocialMapper.

This module provides a centralized Rich-based console and logging system
to replace standard logging and tqdm throughout the codebase.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from rich.align import Align
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
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
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.traceback import install as install_rich_traceback

# Custom theme for SocialMapper
SOCIALMAPPER_THEME = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "highlight": "bold blue",
        "muted": "dim",
        "progress": "green",
        "poi": "blue",
        "census": "purple",
        "isochrone": "orange",
        "geocoding": "cyan",
        "network": "green",
    }
)

# Global console instance
console = Console(
    theme=SOCIALMAPPER_THEME,
    width=None,  # Auto-detect terminal width
    force_terminal=None,  # Auto-detect if in terminal
    force_interactive=None,  # Auto-detect if interactive
)

# Progress instance for complex operations
progress = Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    MofNCompleteColumn(),
    TextColumn("•"),
    TimeElapsedColumn(),
    TextColumn("•"),
    TimeRemainingColumn(),
    console=console,
    refresh_per_second=10,
)


class RichProgressColumn(ProgressColumn):
    """Custom progress column showing items per second."""

    def render(self, task: "Task") -> Text:
        """Render the progress column."""
        if task.speed is None:
            return Text("", style="progress")

        if task.speed >= 1:
            return Text(f"{task.speed:.1f} items/sec", style="progress")
        else:
            return Text(f"{1 / task.speed:.1f} sec/item", style="progress")


def setup_rich_logging(
    level: str = "INFO",
    show_time: bool = True,
    show_path: bool = False,
    rich_tracebacks: bool = True,
) -> None:
    """Set up Rich-based logging for the entire application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        show_time: Whether to show timestamps
        show_path: Whether to show file paths in logs
        rich_tracebacks: Whether to use Rich for tracebacks
    """
    # Install rich traceback handler
    if rich_tracebacks:
        install_rich_traceback(
            console=console,
            show_locals=level == "DEBUG",
            max_frames=20,
            width=None,
            word_wrap=True,
            extra_lines=2,
        )

    # Configure the root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        handlers=[
            RichHandler(
                console=console,
                show_time=show_time,
                show_path=show_path,
                rich_tracebacks=rich_tracebacks,
                tracebacks_width=None,
                tracebacks_extra_lines=2,
                tracebacks_show_locals=level == "DEBUG",
            )
        ],
    )

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a Rich-enabled logger.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


@contextmanager
def status(message: str, spinner: str = "dots"):
    """Context manager for showing a spinner status.

    Args:
        message: Status message to show
        spinner: Spinner style

    Yields:
        Console instance for additional output
    """
    with console.status(f"[info]{message}[/info]", spinner=spinner):
        yield console


@contextmanager
def progress_bar(
    description: str, total: int | None = None, transient: bool = False, disable: bool = False
) -> Iterator[Progress]:
    """Context manager for Rich progress bars.

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


def print_info(message: str, **kwargs) -> None:
    """Print an info message."""
    console.print(f"[info]ℹ️  {message}[/info]", **kwargs)


def print_success(message: str, **kwargs) -> None:
    """Print a success message."""
    console.print(f"[success]✅ {message}[/success]", **kwargs)


def print_warning(message: str, **kwargs) -> None:
    """Print a warning message."""
    console.print(f"[warning]⚠️  {message}[/warning]", **kwargs)


def print_error(message: str, **kwargs) -> None:
    """Print an error message."""
    console.print(f"[error]❌ {message}[/error]", **kwargs)


def print_panel(
    content: str,
    title: str | None = None,
    subtitle: str | None = None,
    style: str = "info",
    **kwargs,
) -> None:
    """Print content in a styled panel."""
    panel = Panel(content, title=title, subtitle=subtitle, border_style=style, **kwargs)
    console.print(panel)


def print_table(
    data: list[dict[str, Any]], title: str | None = None, show_header: bool = True, **kwargs
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


def print_statistics(stats: dict[str, Any], title: str = "Statistics", **kwargs) -> None:
    """Print statistics in a formatted table."""
    table = Table(title=title, show_header=True, **kwargs)
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="highlight")

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


def print_poi_summary(pois: list[dict[str, Any]], **kwargs) -> None:
    """Print a summary of POI data."""
    if not pois:
        print_warning("No POIs to display")
        return

    table = Table(title=f"📍 POI Summary ({len(pois)} locations)", show_header=True, **kwargs)
    table.add_column("Name", style="poi")
    table.add_column("Coordinates", style="muted")
    table.add_column("Type", style="highlight")

    for poi in pois[:10]:  # Show first 10
        name = poi.get("name", "Unknown")
        lat = poi.get("latitude", 0)
        lon = poi.get("longitude", 0)
        poi_type = poi.get("type", "unknown")

        table.add_row(
            name[:30] + "..." if len(name) > 30 else name, f"{lat:.4f}, {lon:.4f}", poi_type
        )

    if len(pois) > 10:
        table.add_row("...", "...", f"... and {len(pois) - 10} more")

    console.print(table)


def create_section_header(title: str, emoji: str = "🔧") -> None:
    """Create a styled section header."""
    header_text = Text(f"{emoji} {title}", style="bold highlight")
    console.print()
    console.print(Align.center(header_text))
    console.print("─" * len(f"{emoji} {title}"), style="muted")


# Compatibility functions for legacy progress tracking
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
            console=console,
            refresh_per_second=10,
        )

        self.progress_instance.start()
        self.task_id = self.progress_instance.add_task(desc, total=self.total)

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
            self.progress_instance.update(self.task_id, advance=n)
            self.position += n

    def set_description(self, desc):
        if self.progress_instance and self.task_id is not None:
            self.progress_instance.update(self.task_id, description=desc)

    def close(self):
        if self.progress_instance:
            self.progress_instance.stop()

    def write(self, message):
        console.print(message)


def rich_tqdm(*args, **kwargs):
    """Drop-in replacement for tqdm using Rich."""
    return RichProgressWrapper(*args, **kwargs)


# Export main interface
__all__ = [
    "RichProgressWrapper",
    "console",
    "create_section_header",
    "get_logger",
    "print_error",
    "print_info",
    "print_panel",
    "print_poi_summary",
    "print_statistics",
    "print_success",
    "print_table",
    "print_warning",
    "progress",
    "progress_bar",
    "rich_tqdm",
    "setup_rich_logging",
    "status",
]
