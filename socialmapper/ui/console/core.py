#!/usr/bin/env python3
"""
Core console functionality for SocialMapper.

This module provides the central Rich console instance and basic formatting functions.
"""

from contextlib import contextmanager
from typing import Any, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.pretty import pprint
from rich.status import Status
from rich.syntax import Syntax
from rich.traceback import install as install_rich_traceback

# Install Rich tracebacks globally for the package
install_rich_traceback(show_locals=True)

# Global console instance for SocialMapper
console = Console()


def clear_console_state():
    """Clear any active Rich console state to prevent conflicts."""
    try:
        # Clear any active live displays
        if hasattr(console, "_live") and console._live is not None:
            console.clear_live()
    except Exception:
        # Ignore errors during cleanup
        pass


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


def print_statistics(stats: dict, title: str = "Statistics", **kwargs) -> None:
    """Print statistics in a formatted table."""
    from .tables import create_statistics_table

    table = create_statistics_table(stats, title, **kwargs)
    console.print(table)