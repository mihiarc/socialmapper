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
    """
    Custom progress column displaying processing speed.

    Shows items per second or seconds per item depending
    on the processing rate.
    """

    def render(self, task: "Task") -> Text:
        """
        Render the progress speed indicator.

        Parameters
        ----------
        task : Task
            Rich progress task object containing speed data.

        Returns
        -------
        Text
            Formatted text showing processing speed.
        """
        if task.speed is None:
            return Text("", style="progress.percentage")

        if task.speed >= 1:
            return Text(f"{task.speed:.1f} items/sec", style="progress.percentage")
        else:
            return Text(f"{1 / task.speed:.1f} sec/item", style="progress.percentage")


class RichProgressWrapper:
    """
    tqdm-compatible wrapper for Rich progress bars.

    Provides a drop-in replacement for tqdm progress bars using
    Rich's more advanced display capabilities.
    """

    def __init__(self, iterable=None, desc="", total=None, unit="it", **kwargs):
        """
        Initialize Rich progress bar with tqdm-compatible interface.

        Parameters
        ----------
        iterable : iterable, optional
            Items to iterate over with progress tracking.
        desc : str, optional
            Progress bar description text. Default is "".
        total : int, optional
            Total number of items. Default is None (auto-detected).
        unit : str, optional
            Unit name for items. Default is "it".
        **kwargs
            Additional arguments for compatibility.
        """
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
            total_msg = f" ({self.total} items)" if self.total else ""
            console.print(f"🔄 {desc}{total_msg}")
            self.progress_instance = None
            self.task_id = None

    def __iter__(self):
        """
        Iterate with automatic progress updates.

        Yields
        ------
        Any
            Items from the iterable with progress tracking.
        """
        if self.iterable:
            for item in self.iterable:
                yield item
                self.update(1)

    def __enter__(self):
        """
        Enter progress bar context.

        Returns
        -------
        RichProgressWrapper
            Self for context manager protocol.
        """
        return self

    def __exit__(self, *args):
        """
        Exit context and cleanup progress display.

        Parameters
        ----------
        *args
            Exception information (unused).
        """
        self.close()

    def update(self, n=1):
        """
        Advance progress bar by specified amount.

        Parameters
        ----------
        n : int, optional
            Number of items to advance. Default is 1.
        """
        if self.progress_instance and self.task_id is not None:
            with suppress(Exception):
                # If progress update fails, just track position
                self.progress_instance.update(self.task_id, advance=n)
        self.position += n

        # If no progress display, show individual updates for detailed tracking
        if self.progress_instance is None and self.total:
            percentage = (self.position / self.total) * 100
            console.print(f"  Progress: {self.position}/{self.total} ({percentage:.1f}%)")

    def set_description(self, desc):
        """
        Update the progress bar description text.

        Parameters
        ----------
        desc : str
            New description text to display.
        """
        if self.progress_instance and self.task_id is not None:
            self.progress_instance.update(self.task_id, description=desc)

    def close(self):
        """
        Stop and remove the progress bar display.

        Performs cleanup of Rich progress instance and
        resets internal state.
        """
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
        """
        Write message to console above progress bar.

        Parameters
        ----------
        message : str
            Text to display in the console.
        """
        console.print(message)


def rich_tqdm(*args, **kwargs):
    """
    Create tqdm-compatible progress bar using Rich.

    Drop-in replacement for tqdm that uses Rich's advanced
    terminal rendering capabilities.

    Parameters
    ----------
    *args
        Positional arguments passed to RichProgressWrapper.
    **kwargs
        Keyword arguments passed to RichProgressWrapper.

    Returns
    -------
    RichProgressWrapper
        Progress bar instance with tqdm-compatible API.

    Examples
    --------
    >>> for item in rich_tqdm(range(100), desc="Processing"):
    ...     process(item)

    >>> with rich_tqdm(total=50) as pbar:
    ...     for i in range(50):
    ...         pbar.update(1)
    """
    return RichProgressWrapper(*args, **kwargs)


@contextmanager
def progress_bar(
    description: str, total: int | None = None, transient: bool = False, disable: bool = False
):
    """
    Context manager for Rich progress bar display.

    Creates a sophisticated progress bar with time estimates,
    speed metrics, and automatic cleanup.

    Parameters
    ----------
    description : str
        Text description for the progress bar.
    total : int, optional
        Total number of items. None for indeterminate progress.
        Default is None.
    transient : bool, optional
        If True, removes progress bar after completion.
        Default is False.
    disable : bool, optional
        If True, disables progress bar entirely.
        Default is False.

    Yields
    ------
    Progress or DummyProgress
        Rich Progress instance or dummy object if disabled.

    Examples
    --------
    >>> with progress_bar("Loading data", total=100) as progress:
    ...     task_id = progress.task_id
    ...     for i in range(100):
    ...         progress.update(task_id, advance=1)

    >>> with progress_bar("Processing", transient=True) as p:
    ...     # Progress bar disappears when done
    ...     process_data()
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
