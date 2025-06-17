#!/usr/bin/env python3
"""Progress bar and tracking functionality for SocialMapper.

This module provides Rich-based progress bars and progress tracking utilities.
"""

from contextlib import contextmanager, suppress

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
from rich.text import Text

from .core import console


class RichProgressColumn(ProgressColumn):
    """Custom progress column showing items per second."""

    def render(self, task: "Task") -> Text:
        """Render the progress column."""
        if task.speed is None:
            return Text("", style="progress.percentage")

        if task.speed >= 1:
            return Text(f"{task.speed:.1f} items/sec", style="progress.percentage")
        else:
            return Text(f"{1 / task.speed:.1f} sec/item", style="progress.percentage")


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
        """Iterate over items while updating progress."""
        if self.iterable:
            for item in self.iterable:
                yield item
                self.update(1)

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, *args):
        """Exit context manager and close progress bar."""
        self.close()

    def update(self, n=1):
        if self.progress_instance and self.task_id is not None:
            with suppress(Exception):
                # If progress update fails, just track position
                self.progress_instance.update(self.task_id, advance=n)
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


@contextmanager
def progress_bar(
    description: str, total: int | None = None, transient: bool = False, disable: bool = False
):
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
