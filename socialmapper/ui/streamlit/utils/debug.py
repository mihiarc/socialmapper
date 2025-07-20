"""Debug utilities for Streamlit application development."""

import logging
from typing import Any, Dict, List
from datetime import datetime

import streamlit as st

logger = logging.getLogger(__name__)


def render_debug_panel():
    """Render a debug panel with session state information."""
    if not st.session_state.user_preferences.get('show_debug', False):
        return
    
    with st.expander("🔧 Debug Panel", expanded=False):
        debug_tabs = st.tabs(["Session State", "Performance", "Logs", "Actions"])
        
        with debug_tabs[0]:
            render_session_state_debug()
        
        with debug_tabs[1]:
            render_performance_debug()
        
        with debug_tabs[2]:
            render_logs_debug()
        
        with debug_tabs[3]:
            render_debug_actions()


def render_session_state_debug():
    """Render session state debugging information."""
    st.subheader("Session State Variables")
    
    # Get session info
    try:
        from .session_state import get_debug_info
        session_info = get_debug_info()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Session ID", session_info.get('session_id', 'N/A'))
            st.metric("Current Page", session_info.get('current_page', 'N/A'))
            st.metric("Navigation Mode", session_info.get('navigation_mode', 'N/A'))
        
        with col2:
            duration = session_info.get('duration')
            if duration:
                st.metric("Session Duration", f"{duration.total_seconds():.0f}s")
            st.metric("Cache Hits", session_info.get('cache_stats', {}).get('hits', 0))
            st.metric("Error Count", session_info.get('error_count', 0))
        
        # Page visit statistics
        page_visits = session_info.get('page_visits', {})
        if page_visits:
            st.subheader("Page Visit Count")
            for page, count in page_visits.items():
                st.write(f"**{page}:** {count}")
    
    except Exception as e:
        st.error(f"Error getting session info: {e}")
    
    # Raw session state (filtered)
    st.subheader("Key Session State Variables")
    
    important_keys = [
        'current_page', 'analysis_complete', 'navigation_mode',
        'analysis_results', 'travel_analysis_results', 'error_state'
    ]
    
    for key in important_keys:
        if key in st.session_state:
            value = st.session_state[key]
            if value is not None:
                # Truncate large values
                if isinstance(value, (dict, list)) and len(str(value)) > 200:
                    display_value = f"{type(value).__name__} with {len(value)} items"
                else:
                    display_value = str(value)[:200]
                st.code(f"{key}: {display_value}")


def render_performance_debug():
    """Render performance debugging information."""
    st.subheader("Performance Metrics")
    
    # Cache statistics
    cache_stats = st.session_state.get('cache_stats', {})
    if cache_stats:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cache Hits", cache_stats.get('hits', 0))
        with col2:
            st.metric("Cache Misses", cache_stats.get('misses', 0))
        with col3:
            total = cache_stats.get('hits', 0) + cache_stats.get('misses', 0)
            hit_rate = (cache_stats.get('hits', 0) / total * 100) if total > 0 else 0
            st.metric("Hit Rate", f"{hit_rate:.1f}%")
    
    # Performance metrics
    perf_metrics = st.session_state.get('performance_metrics', {})
    if perf_metrics:
        st.subheader("Analysis Performance")
        for metric, value in perf_metrics.items():
            if isinstance(value, (int, float)):
                st.metric(metric.replace('_', ' ').title(), f"{value:.2f}")
    
    # Memory usage (if available)
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        st.subheader("Memory Usage")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("RSS Memory", f"{memory_info.rss / 1024 / 1024:.1f} MB")
        with col2:
            st.metric("VMS Memory", f"{memory_info.vms / 1024 / 1024:.1f} MB")
    
    except ImportError:
        st.info("Install psutil for memory usage information")
    except Exception as e:
        st.warning(f"Could not get memory info: {e}")


def render_logs_debug():
    """Render debug logs."""
    st.subheader("Debug Logs")
    
    debug_logs = st.session_state.get('debug_logs', [])
    
    if not debug_logs:
        st.info("No debug logs available")
        return
    
    # Show recent logs
    recent_logs = debug_logs[-20:]  # Last 20 logs
    
    for log_entry in reversed(recent_logs):
        timestamp = log_entry.get('timestamp', datetime.now())
        level = log_entry.get('level', 'info')
        message = log_entry.get('message', '')
        
        # Color code by level
        if level == 'error':
            st.error(f"[{timestamp.strftime('%H:%M:%S')}] {message}")
        elif level == 'warning':
            st.warning(f"[{timestamp.strftime('%H:%M:%S')}] {message}")
        else:
            st.info(f"[{timestamp.strftime('%H:%M:%S')}] {message}")


def render_debug_actions():
    """Render debug actions."""
    st.subheader("Debug Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Reset Session State"):
            try:
                from .session_state import reset_application_state
                reset_application_state(preserve_preferences=True)
                st.success("Session state reset successfully")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to reset session state: {e}")
        
        if st.button("🧹 Clear Cache"):
            try:
                st.cache_data.clear()
                st.success("Cache cleared successfully")
            except Exception as e:
                st.error(f"Failed to clear cache: {e}")
    
    with col2:
        if st.button("📊 Validate Session State"):
            try:
                from .session_state import SessionStateManager
                issues = SessionStateManager.validate_session_state()
                if issues:
                    st.warning(f"Found {len(issues)} issues:")
                    for issue in issues:
                        st.write(f"- {issue}")
                else:
                    st.success("Session state is valid")
            except Exception as e:
                st.error(f"Validation failed: {e}")
        
        if st.button("💾 Export Debug Info"):
            try:
                debug_info = get_full_debug_info()
                st.download_button(
                    label="Download Debug Info",
                    data=str(debug_info),
                    file_name=f"debug_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"Failed to export debug info: {e}")


def get_full_debug_info() -> Dict[str, Any]:
    """Get comprehensive debug information."""
    try:
        from .session_state import get_debug_info
        
        debug_info = {
            'timestamp': datetime.now().isoformat(),
            'session_info': get_debug_info(),
            'session_state_keys': list(st.session_state.keys()),
            'error_state': st.session_state.get('error_state'),
            'debug_logs': st.session_state.get('debug_logs', [])[-10:],  # Last 10 logs
            'user_preferences': st.session_state.get('user_preferences', {}),
            'streamlit_version': st.__version__
        }
        
        return debug_info
    
    except Exception as e:
        return {'error': str(e), 'timestamp': datetime.now().isoformat()}


def log_page_transition(from_page: str, to_page: str):
    """Log page transitions for debugging."""
    try:
        from .session_state import log_debug_message
        log_debug_message(f"Page transition: {from_page} -> {to_page}", 'info')
    except Exception as e:
        logger.error(f"Failed to log page transition: {e}")


def log_analysis_start(analysis_type: str, config: Dict[str, Any]):
    """Log analysis start for debugging."""
    try:
        from .session_state import log_debug_message
        log_debug_message(f"Analysis started: {analysis_type} with config: {config}", 'info')
    except Exception as e:
        logger.error(f"Failed to log analysis start: {e}")


def log_analysis_complete(analysis_type: str, success: bool, duration: float):
    """Log analysis completion for debugging."""
    try:
        from .session_state import log_debug_message
        status = "success" if success else "failed"
        log_debug_message(f"Analysis {status}: {analysis_type} in {duration:.2f}s", 'info')
    except Exception as e:
        logger.error(f"Failed to log analysis completion: {e}")


def enable_debug_mode():
    """Enable debug mode for the application."""
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {}
    
    st.session_state.user_preferences['show_debug'] = True
    st.session_state.debug_mode = True
    
    from .session_state import log_debug_message
    log_debug_message("Debug mode enabled", 'info')


def disable_debug_mode():
    """Disable debug mode for the application."""
    if 'user_preferences' in st.session_state:
        st.session_state.user_preferences['show_debug'] = False
    
    st.session_state.debug_mode = False
    
    from .session_state import log_debug_message
    log_debug_message("Debug mode disabled", 'info')