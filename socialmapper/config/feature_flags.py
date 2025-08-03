"""Feature flag system for gradual rollout of frontend-backend separation."""

import os
from enum import Enum
from typing import Dict, Any


class UIMode(str, Enum):
    """UI deployment modes."""
    MONOLITHIC = "monolithic"  # Original embedded UI
    SEPARATED = "separated"    # New API-based UI
    HYBRID = "hybrid"         # Both modes available


class FeatureFlags:
    """Feature flag configuration for SocialMapper."""
    
    def __init__(self):
        """Initialize feature flags from environment variables."""
        # UI Architecture Mode
        self.ui_mode = UIMode(os.getenv("SOCIALMAPPER_UI_MODE", UIMode.MONOLITHIC.value))
        
        # API Server Configuration (for separated mode)
        self.enable_api_server = self._get_bool_env("SOCIALMAPPER_ENABLE_API_SERVER", False)
        self.api_server_host = os.getenv("SOCIALMAPPER_API_SERVER_HOST", "localhost")
        self.api_server_port = int(os.getenv("SOCIALMAPPER_API_SERVER_PORT", "8000"))
        
        # Frontend Configuration (for separated mode)
        self.enable_separated_ui = self._get_bool_env("SOCIALMAPPER_ENABLE_SEPARATED_UI", False)
        self.separated_ui_host = os.getenv("SOCIALMAPPER_SEPARATED_UI_HOST", "localhost")
        self.separated_ui_port = int(os.getenv("SOCIALMAPPER_SEPARATED_UI_PORT", "8501"))
        
        # Migration and Compatibility
        self.show_migration_notice = self._get_bool_env("SOCIALMAPPER_SHOW_MIGRATION_NOTICE", True)
        self.allow_legacy_imports = self._get_bool_env("SOCIALMAPPER_ALLOW_LEGACY_IMPORTS", True)
        self.deprecation_warnings = self._get_bool_env("SOCIALMAPPER_DEPRECATION_WARNINGS", True)
        
        # Development and Testing
        self.debug_mode = self._get_bool_env("SOCIALMAPPER_DEBUG_MODE", False)
        self.mock_api_responses = self._get_bool_env("SOCIALMAPPER_MOCK_API_RESPONSES", False)
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean value from environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")


# Global feature flags instance
_feature_flags: FeatureFlags = None


def get_feature_flags() -> FeatureFlags:
    """Get the global feature flags instance."""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlags()
    return _feature_flags


def is_ui_mode(mode: UIMode) -> bool:
    """Check if the current UI mode matches the specified mode."""
    flags = get_feature_flags()
    return flags.ui_mode == mode or flags.ui_mode == UIMode.HYBRID


def is_separated_mode() -> bool:
    """Check if separated UI mode is enabled."""
    return is_ui_mode(UIMode.SEPARATED)


def is_monolithic_mode() -> bool:
    """Check if monolithic UI mode is enabled."""
    return is_ui_mode(UIMode.MONOLITHIC)


def is_hybrid_mode() -> bool:
    """Check if hybrid mode is enabled (both UIs available)."""
    flags = get_feature_flags()
    return flags.ui_mode == UIMode.HYBRID


def should_show_migration_notice() -> bool:
    """Check if migration notice should be shown."""
    flags = get_feature_flags()
    return flags.show_migration_notice and (is_separated_mode() or is_hybrid_mode())


def get_api_base_url() -> str:
    """Get the API base URL for separated mode."""
    flags = get_feature_flags()
    return f"http://{flags.api_server_host}:{flags.api_server_port}"


def get_ui_base_url() -> str:
    """Get the UI base URL for separated mode."""
    flags = get_feature_flags()
    return f"http://{flags.separated_ui_host}:{flags.separated_ui_port}"


def get_runtime_config() -> Dict[str, Any]:
    """Get runtime configuration based on feature flags."""
    flags = get_feature_flags()
    
    config = {
        "ui_mode": flags.ui_mode.value,
        "api_enabled": flags.enable_api_server,
        "separated_ui_enabled": flags.enable_separated_ui,
        "debug_mode": flags.debug_mode,
    }
    
    if is_separated_mode() or is_hybrid_mode():
        config.update({
            "api_base_url": get_api_base_url(),
            "ui_base_url": get_ui_base_url(),
        })
    
    return config