"""Centralized session state management for the Streamlit application."""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

import streamlit as st

logger = logging.getLogger(__name__)


class SessionStateManager:
    """Centralized session state management with validation and recovery."""
    
    # Define the schema for session state variables
    SESSION_STATE_SCHEMA = {
        # Core application state
        'analysis_results': {'type': (type(None), dict), 'default': None},
        'current_page': {'type': str, 'default': "Getting Started"},
        'analysis_complete': {'type': bool, 'default': False},
        'census_vars': {'type': list, 'default': []},
        
        # Navigation and UI state
        'navigation_mode': {'type': (type(None), str), 'default': None},
        'page_config_set': {'type': bool, 'default': False},
        'error_state': {'type': (type(None), dict), 'default': None},
        
        # Analysis configuration state
        'analysis_config': {'type': dict, 'default': {}},
        'custom_poi_data': {'type': (type(None), object), 'default': None},
        'travel_analysis_results': {'type': (type(None), dict), 'default': None},
        'travel_analysis_config': {'type': (type(None), dict), 'default': None},
        
        # Cache and performance state
        'cache_stats': {'type': dict, 'default': {'hits': 0, 'misses': 0}},
        'performance_metrics': {'type': dict, 'default': {}},
        
        # User preferences
        'user_preferences': {
            'type': dict, 
            'default': {
                'theme': 'auto',
                'show_debug': False,
                'auto_refresh': True,
                'export_format': 'csv',
                'max_pois': 10
            }
        },
        
        # Session metadata
        'session_id': {'type': (type(None), str), 'default': None},
        'session_start_time': {'type': (type(None), datetime), 'default': None},
        'last_activity': {'type': (type(None), datetime), 'default': None},
        'page_visit_count': {'type': dict, 'default': {}},
        
        # Debug and development state
        'debug_mode': {'type': bool, 'default': False},
        'debug_logs': {'type': list, 'default': []},
        'feature_flags': {'type': dict, 'default': {}},
    }
    
    @classmethod
    def initialize_all(cls) -> None:
        """Initialize all session state variables with proper defaults."""
        try:
            for key, config in cls.SESSION_STATE_SCHEMA.items():
                if key not in st.session_state:
                    default_value = config['default']
                    # Handle callable defaults (like datetime.now)
                    if callable(default_value):
                        default_value = default_value()
                    st.session_state[key] = default_value
                    logger.debug(f"Initialized session state: {key}")
            
            # Set session metadata if not already set
            if st.session_state.session_id is None:
                st.session_state.session_id = cls._generate_session_id()
                st.session_state.session_start_time = datetime.now()
                logger.info(f"New session started: {st.session_state.session_id}")
            
            # Update last activity
            st.session_state.last_activity = datetime.now()
            
        except Exception as e:
            logger.error(f"Error initializing session state: {e}")
            raise
    
    @classmethod
    def validate_session_state(cls) -> List[str]:
        """Validate session state variables and return list of issues."""
        issues = []
        
        try:
            for key, config in cls.SESSION_STATE_SCHEMA.items():
                if key in st.session_state:
                    value = st.session_state[key]
                    expected_types = config['type']
                    
                    # Handle tuple of types
                    if isinstance(expected_types, tuple):
                        if not isinstance(value, expected_types):
                            issues.append(f"{key}: expected {expected_types}, got {type(value)}")
                    else:
                        if not isinstance(value, expected_types):
                            issues.append(f"{key}: expected {expected_types}, got {type(value)}")
                else:
                    issues.append(f"{key}: missing from session state")
        
        except Exception as e:
            issues.append(f"Validation error: {e}")
            logger.error(f"Session state validation error: {e}")
        
        return issues
    
    @classmethod
    def recover_session_state(cls) -> bool:
        """Attempt to recover corrupted session state variables."""
        try:
            issues = cls.validate_session_state()
            
            if not issues:
                return True
            
            logger.warning(f"Session state issues detected: {issues}")
            
            # Reset problematic variables to defaults
            for issue in issues:
                if ':' in issue:
                    key = issue.split(':')[0]
                    if key in cls.SESSION_STATE_SCHEMA:
                        default_value = cls.SESSION_STATE_SCHEMA[key]['default']
                        if callable(default_value):
                            default_value = default_value()
                        st.session_state[key] = default_value
                        logger.info(f"Reset session state variable: {key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Session state recovery failed: {e}")
            return False
    
    @classmethod
    def cleanup_session_state(cls) -> None:
        """Clean up session state for page transitions."""
        try:
            # Clear temporary analysis data
            temporary_keys = [
                'temp_analysis_data',
                'temp_upload_data',
                'temp_error_state',
                'temp_progress_state'
            ]
            
            for key in temporary_keys:
                if key in st.session_state:
                    del st.session_state[key]
                    logger.debug(f"Cleaned up temporary state: {key}")
            
            # Update page visit count
            current_page = st.session_state.get('current_page', 'Unknown')
            if current_page not in st.session_state.page_visit_count:
                st.session_state.page_visit_count[current_page] = 0
            st.session_state.page_visit_count[current_page] += 1
            
        except Exception as e:
            logger.error(f"Session state cleanup error: {e}")
    
    @classmethod
    def get_session_info(cls) -> Dict[str, Any]:
        """Get session information for debugging."""
        try:
            session_duration = None
            if st.session_state.session_start_time:
                session_duration = datetime.now() - st.session_state.session_start_time
            
            return {
                'session_id': st.session_state.get('session_id'),
                'start_time': st.session_state.get('session_start_time'),
                'duration': session_duration,
                'last_activity': st.session_state.get('last_activity'),
                'current_page': st.session_state.get('current_page'),
                'page_visits': st.session_state.get('page_visit_count', {}),
                'cache_stats': st.session_state.get('cache_stats', {}),
                'error_count': len(st.session_state.get('debug_logs', [])),
                'navigation_mode': st.session_state.get('navigation_mode')
            }
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return {'error': str(e)}
    
    @classmethod
    def reset_session_state(cls, preserve_preferences: bool = True) -> None:
        """Reset session state while optionally preserving user preferences."""
        try:
            # Preserve user preferences if requested
            preserved_data = {}
            if preserve_preferences:
                preserved_data['user_preferences'] = st.session_state.get('user_preferences', {})
            
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Reinitialize
            cls.initialize_all()
            
            # Restore preserved data
            for key, value in preserved_data.items():
                st.session_state[key] = value
            
            logger.info("Session state reset successfully")
            
        except Exception as e:
            logger.error(f"Session state reset failed: {e}")
            raise
    
    @classmethod
    def add_debug_log(cls, message: str, level: str = 'info') -> None:
        """Add a debug log entry to session state."""
        try:
            if 'debug_logs' not in st.session_state:
                st.session_state.debug_logs = []
            
            log_entry = {
                'timestamp': datetime.now(),
                'level': level,
                'message': message
            }
            
            st.session_state.debug_logs.append(log_entry)
            
            # Keep only last 100 log entries
            if len(st.session_state.debug_logs) > 100:
                st.session_state.debug_logs = st.session_state.debug_logs[-100:]
                
        except Exception as e:
            logger.error(f"Error adding debug log: {e}")
    
    @classmethod
    def _generate_session_id(cls) -> str:
        """Generate a unique session ID."""
        import uuid
        return str(uuid.uuid4())[:8]


# Convenience functions for common operations
def initialize_session_state():
    """Initialize session state - main entry point."""
    SessionStateManager.initialize_all()


def validate_and_recover_session_state() -> bool:
    """Validate session state and recover if needed."""
    issues = SessionStateManager.validate_session_state()
    if issues:
        return SessionStateManager.recover_session_state()
    return True


def cleanup_for_page_transition():
    """Clean up session state for page transitions."""
    SessionStateManager.cleanup_session_state()


def get_debug_info() -> Dict[str, Any]:
    """Get debug information about the current session."""
    return SessionStateManager.get_session_info()


def reset_application_state(preserve_preferences: bool = True):
    """Reset the entire application state."""
    SessionStateManager.reset_session_state(preserve_preferences)


def log_debug_message(message: str, level: str = 'info'):
    """Add a debug message to the session logs."""
    SessionStateManager.add_debug_log(message, level)