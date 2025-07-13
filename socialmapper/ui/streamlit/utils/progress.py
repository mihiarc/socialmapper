"""Enhanced progress indicators for Streamlit."""

import streamlit as st
import time
from typing import Optional, List, Callable, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Enhanced progress tracking with detailed status updates."""
    
    def __init__(self, total_steps: int, title: str = "Processing"):
        """Initialize progress tracker.
        
        Args:
            total_steps: Total number of steps
            title: Title for the progress section
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.title = title
        self.progress_bar = None
        self.status_text = None
        self.time_text = None
        self.start_time = None
        self.container = None
        
    def __enter__(self):
        """Enter context manager."""
        self.container = st.container()
        with self.container:
            st.markdown(f"### {self.title}")
            col1, col2 = st.columns([4, 1])
            with col1:
                self.progress_bar = st.progress(0)
                self.status_text = st.empty()
            with col2:
                self.time_text = st.empty()
        
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if exc_type is None:
            self.complete()
        else:
            self.error(f"Error: {exc_val}")
    
    def update(self, step: int, message: str) -> None:
        """Update progress with step number and message.
        
        Args:
            step: Current step number (1-based)
            message: Status message
        """
        self.current_step = step
        progress = min(step / self.total_steps, 1.0)
        
        if self.progress_bar:
            self.progress_bar.progress(progress)
        
        if self.status_text:
            self.status_text.text(f"Step {step}/{self.total_steps}: {message}")
        
        # Update time estimate
        if self.time_text and self.start_time:
            elapsed = time.time() - self.start_time
            if progress > 0:
                estimated_total = elapsed / progress
                remaining = estimated_total - elapsed
                self.time_text.text(f"⏱️ {self._format_time(remaining)} left")
    
    def complete(self) -> None:
        """Mark progress as complete."""
        if self.progress_bar:
            self.progress_bar.progress(1.0)
        if self.status_text:
            self.status_text.text("✅ Complete!")
        if self.time_text and self.start_time:
            total_time = time.time() - self.start_time
            self.time_text.text(f"⏱️ {self._format_time(total_time)}")
    
    def error(self, message: str) -> None:
        """Mark progress as error."""
        if self.status_text:
            self.status_text.error(f"❌ {message}")
        if self.progress_bar:
            self.progress_bar.empty()
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format time duration."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"


@contextmanager
def progress_context(steps: List[str], title: str = "Processing"):
    """Context manager for progress tracking with predefined steps.
    
    Args:
        steps: List of step descriptions
        title: Title for the progress section
        
    Yields:
        Function to advance to next step
    """
    tracker = ProgressTracker(len(steps), title)
    current_step = [0]  # Use list to allow modification in nested function
    
    def next_step():
        """Advance to the next step."""
        if current_step[0] < len(steps):
            current_step[0] += 1
            tracker.update(current_step[0], steps[current_step[0] - 1])
    
    with tracker:
        yield next_step


def multi_progress(tasks: List[dict[str, Any]], title: str = "Processing Tasks") -> None:
    """Display progress for multiple parallel tasks.
    
    Args:
        tasks: List of task dictionaries with 'name' and 'progress' keys
        title: Title for the progress section
    """
    container = st.container()
    with container:
        st.markdown(f"### {title}")
        
        progress_bars = {}
        status_texts = {}
        
        # Create progress bars for each task
        for task in tasks:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(task['name'])
                progress_bars[task['name']] = st.progress(0)
            with col2:
                status_texts[task['name']] = st.empty()
        
        # Update progress bars
        for task in tasks:
            progress = task.get('progress', 0)
            status = task.get('status', 'Pending')
            
            progress_bars[task['name']].progress(progress)
            status_texts[task['name']].text(status)


@st.fragment(run_every=0.1)
def animated_progress(
    progress_value: float,
    text: str = "Processing...",
    bar_color: Optional[str] = None
) -> None:
    """Animated progress bar that updates smoothly.
    
    Args:
        progress_value: Progress value (0.0 to 1.0)
        text: Text to display
        bar_color: Optional color for the progress bar
    """
    # Custom CSS for colored progress bar if specified
    if bar_color:
        st.markdown(
            f"""
            <style>
            .stProgress > div > div > div > div {{
                background-color: {bar_color};
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    
    progress_bar = st.progress(0)
    status_text = st.text(text)
    
    # Animate to target value
    current = 0
    step = 0.02
    while current < progress_value:
        current = min(current + step, progress_value)
        progress_bar.progress(current)
        time.sleep(0.01)
    
    # Update status when complete
    if progress_value >= 1.0:
        status_text.text("✅ Complete!")


def progress_with_eta(
    current: int,
    total: int,
    start_time: float,
    prefix: str = "Progress"
) -> tuple[float, str]:
    """Calculate progress with ETA.
    
    Args:
        current: Current item number
        total: Total items
        start_time: Start time (from time.time())
        prefix: Prefix for the progress text
        
    Returns:
        Tuple of (progress_fraction, status_text)
    """
    progress = current / total if total > 0 else 0
    elapsed = time.time() - start_time
    
    if current > 0:
        rate = current / elapsed
        remaining = (total - current) / rate if rate > 0 else 0
        eta_text = f" - ETA: {ProgressTracker._format_time(remaining)}"
    else:
        eta_text = ""
    
    status = f"{prefix}: {current}/{total} ({progress*100:.1f}%){eta_text}"
    
    return progress, status


# Convenience function for simple progress
def show_progress(message: str = "Processing...", duration: float = 2.0) -> None:
    """Show a simple progress animation.
    
    Args:
        message: Message to display
        duration: Duration in seconds
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    steps = 50
    for i in range(steps + 1):
        progress = i / steps
        progress_bar.progress(progress)
        status_text.text(f"{message} ({progress*100:.0f}%)")
        time.sleep(duration / steps)
    
    status_text.text("✅ Complete!")
    time.sleep(0.5)
    progress_bar.empty()
    status_text.empty()