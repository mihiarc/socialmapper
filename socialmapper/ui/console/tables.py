#!/usr/bin/env python3
"""Table creation and formatting utilities for SocialMapper.

This module provides functions for creating various types of Rich tables.
"""

from typing import Any

from rich import box
from rich.table import Table

from .core import console


def create_data_table(
    title: str,
    columns: list[dict[str, Any]],
    rows: list[list[str]],
    show_header: bool = True,
    box_style: box.Box = box.ROUNDED,
) -> Table:
    """Create a formatted data table.

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


def print_table(
    data: list[dict[str, Any]], title: str | None = None, show_header: bool = True, **kwargs
) -> None:
    """Print data as a formatted table."""
    if not data:
        from .core import print_warning

        print_warning("No data to display in table")
        return

    table = Table(title=title, show_header=show_header, **kwargs)

    # Add columns from first row
    for key in data[0]:
        table.add_column(str(key).replace("_", " ").title())

    # Add rows
    for row in data:
        table.add_row(*[str(value) for value in row.values()])

    console.print(table)


def create_statistics_table(stats: dict, title: str = "Statistics", **kwargs) -> Table:
    """Create a statistics table."""
    table = Table(title=title, show_header=True, **kwargs)
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="cyan")

    for key, value in stats.items():
        # Format the key
        formatted_key = str(key).replace("_", " ").title()

        # Format the value
        if isinstance(value, float):
            formatted_value = f"{value:.1%}" if 0 < value < 1 else f"{value:.1f}"
        elif isinstance(value, int):
            formatted_value = f"{value:,}"
        else:
            formatted_value = str(value)

        table.add_row(formatted_key, formatted_value)

    return table


def create_performance_table(data: dict[str, Any]) -> str:
    """Create a performance comparison table (returns markdown for compatibility).

    Note: This function was originally designed for Streamlit integration,
    but Streamlit has been removed from SocialMapper. The function is kept
    for backward compatibility and returns markdown format.

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
        if isinstance(value, int | float):
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


def create_rich_panel(content: str, title: str = "", style: str = "cyan") -> str:
    """Create a rich-styled panel (returns markdown for compatibility).

    Note: This function was originally designed for Streamlit integration,
    but Streamlit has been removed from SocialMapper. The function is kept
    for backward compatibility and returns markdown format.

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
