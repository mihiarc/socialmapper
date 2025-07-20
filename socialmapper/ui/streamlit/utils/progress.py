"""Enhanced progress indicators for Streamlit."""

import streamlit as st
import time
from typing import Optional, List, Callable, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Enhanced progress tracking with detailed status updates and persistence."""
    
    def __init__(self, total_steps: int, title: str = "Processing", persist_key: str = None):
        """Initialize progress tracker.
        
        Args:
            total_steps: Total number of steps
            title: Title for the progress section
            persist_key: Optional key for persisting progress across page reloads
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.title = title
        self.persist_key = persist_key
        self.progress_bar = None
        self.status_text = None
        self.time_text = None
        self.start_time = None
        self.container = None
        self.step_history = []
        self.estimated_completion = None
        
        # Load persisted state if available
        if persist_key and f"progress_{persist_key}" in st.session_state:
            saved_state = st.session_state[f"progress_{persist_key}"]
            self.current_step = saved_state.get('current_step', 0)
            self.step_history = saved_state.get('step_history', [])
            self.start_time = saved_state.get('start_time')
            if self.start_time:
                # Restore start time from timestamp
                import datetime
                self.start_time = datetime.datetime.fromisoformat(self.start_time).timestamp()
        
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
        
        # Record step in history
        step_info = {
            'step': step,
            'message': message,
            'timestamp': time.time(),
            'progress': progress
        }
        self.step_history.append(step_info)
        
        # Persist state if key provided
        if self.persist_key:
            import datetime
            st.session_state[f"progress_{self.persist_key}"] = {
                'current_step': self.current_step,
                'step_history': self.step_history,
                'start_time': datetime.datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None
            }
        
        if self.progress_bar:
            self.progress_bar.progress(progress)
        
        if self.status_text:
            self.status_text.text(f"Step {step}/{self.total_steps}: {message}")
        
        # Update time estimate with improved accuracy
        if self.time_text and self.start_time:
            elapsed = time.time() - self.start_time
            if progress > 0:
                estimated_total = elapsed / progress
                remaining = max(0, estimated_total - elapsed)
                self.estimated_completion = time.time() + remaining
                self.time_text.text(f"⏱️ {self._format_time(remaining)} left")
            else:
                self.time_text.text("⏱️ Calculating...")
    
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


class PersistentProgressTracker:
    """Progress tracker that persists across page reloads and provides detailed step history."""
    
    def __init__(self, task_id: str, total_steps: int, title: str = "Processing"):
        """Initialize persistent progress tracker.
        
        Args:
            task_id: Unique identifier for this task
            total_steps: Total number of steps
            title: Title for the progress section
        """
        self.task_id = task_id
        self.total_steps = total_steps
        self.title = title
        self.state_key = f"persistent_progress_{task_id}"
        
        # Initialize or load state
        if self.state_key not in st.session_state:
            st.session_state[self.state_key] = {
                'current_step': 0,
                'steps_completed': [],
                'start_time': None,
                'status': 'not_started',
                'error_message': None,
                'completion_time': None
            }
    
    def start(self) -> None:
        """Start the progress tracking."""
        state = st.session_state[self.state_key]
        state['start_time'] = time.time()
        state['status'] = 'in_progress'
        state['steps_completed'] = []
        state['error_message'] = None
        state['completion_time'] = None
    
    def update_step(self, step: int, message: str, details: dict = None) -> None:
        """Update progress with detailed step information.
        
        Args:
            step: Current step number (1-based)
            message: Status message
            details: Optional additional details about the step
        """
        state = st.session_state[self.state_key]
        state['current_step'] = step
        
        step_info = {
            'step': step,
            'message': message,
            'timestamp': time.time(),
            'details': details or {}
        }
        
        # Update or add step
        existing_step = next((s for s in state['steps_completed'] if s['step'] == step), None)
        if existing_step:
            existing_step.update(step_info)
        else:
            state['steps_completed'].append(step_info)
    
    def complete(self) -> None:
        """Mark progress as complete."""
        state = st.session_state[self.state_key]
        state['status'] = 'completed'
        state['completion_time'] = time.time()
        state['current_step'] = self.total_steps
    
    def error(self, message: str) -> None:
        """Mark progress as error."""
        state = st.session_state[self.state_key]
        state['status'] = 'error'
        state['error_message'] = message
    
    def get_state(self) -> dict:
        """Get current progress state."""
        return st.session_state[self.state_key].copy()
    
    def render(self) -> None:
        """Render the progress UI."""
        state = st.session_state[self.state_key]
        
        st.markdown(f"### {self.title}")
        
        # Progress bar
        progress = min(state['current_step'] / self.total_steps, 1.0)
        st.progress(progress)
        
        # Status and timing
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if state['status'] == 'completed':
                st.success("✅ Complete!")
            elif state['status'] == 'error':
                st.error(f"❌ Error: {state['error_message']}")
            elif state['status'] == 'in_progress':
                current_step = next((s for s in state['steps_completed'] if s['step'] == state['current_step']), None)
                if current_step:
                    st.text(f"Step {state['current_step']}/{self.total_steps}: {current_step['message']}")
                else:
                    st.text(f"Step {state['current_step']}/{self.total_steps}")
            else:
                st.text("Ready to start")
        
        with col2:
            if state['start_time']:
                if state['completion_time']:
                    total_time = state['completion_time'] - state['start_time']
                    st.text(f"⏱️ {ProgressTracker._format_time(total_time)}")
                elif state['status'] == 'in_progress' and progress > 0:
                    elapsed = time.time() - state['start_time']
                    estimated_total = elapsed / progress
                    remaining = max(0, estimated_total - elapsed)
                    st.text(f"⏱️ {ProgressTracker._format_time(remaining)} left")
        
        # Step history (expandable)
        if state['steps_completed']:
            with st.expander("📋 Step Details", expanded=False):
                for step_info in state['steps_completed']:
                    step_time = time.strftime('%H:%M:%S', time.localtime(step_info['timestamp']))
                    st.text(f"[{step_time}] Step {step_info['step']}: {step_info['message']}")
                    if step_info.get('details'):
                        st.json(step_info['details'])
    
    def clear(self) -> None:
        """Clear progress state."""
        if self.state_key in st.session_state:
            del st.session_state[self.state_key]


@st.fragment(run_every=1)
def live_progress_display(task_id: str) -> None:
    """Display live progress that auto-refreshes.
    
    Args:
        task_id: Task ID to display progress for
    """
    state_key = f"persistent_progress_{task_id}"
    if state_key in st.session_state:
        state = st.session_state[state_key]
        
        # Only show if in progress
        if state['status'] == 'in_progress':
            progress = min(state['current_step'] / state.get('total_steps', 1), 1.0)
            st.progress(progress)
            
            current_step = next((s for s in state['steps_completed'] if s['step'] == state['current_step']), None)
            if current_step:
                st.text(current_step['message'])
            
            # Show ETA if available
            if state['start_time'] and progress > 0:
                elapsed = time.time() - state['start_time']
                estimated_total = elapsed / progress
                remaining = max(0, estimated_total - elapsed)
                st.caption(f"Estimated time remaining: {ProgressTracker._format_time(remaining)}")


def create_step_by_step_progress(steps: List[str], task_id: str = None) -> PersistentProgressTracker:
    """Create a step-by-step progress tracker with predefined steps.
    
    Args:
        steps: List of step descriptions
        task_id: Optional task ID for persistence
        
    Returns:
        PersistentProgressTracker instance
    """
    if not task_id:
        import uuid
        task_id = str(uuid.uuid4())[:8]
    
    tracker = PersistentProgressTracker(task_id, len(steps), "Step-by-Step Progress")
    
    # Pre-populate step descriptions
    state = tracker.get_state()
    for i, step_desc in enumerate(steps, 1):
        tracker.update_step(i, step_desc, {'predefined': True, 'completed': False})
    
    return tracker


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


# Utility functions for progress management
def clear_all_progress_state():
    """Clear all progress state from session."""
    keys_to_remove = [key for key in st.session_state.keys() if key.startswith('progress_') or key.startswith('persistent_progress_')]
    for key in keys_to_remove:
        del st.session_state[key]


def get_active_progress_tasks() -> List[str]:
    """Get list of active progress task IDs."""
    active_tasks = []
    for key in st.session_state.keys():
        if key.startswith('persistent_progress_'):
            task_id = key.replace('persistent_progress_', '')
            state = st.session_state[key]
            if state['status'] == 'in_progress':
                active_tasks.append(task_id)
    return active_tasks