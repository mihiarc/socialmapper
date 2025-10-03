"""Simplified visualization configuration with sensible defaults.

Instead of complex config classes, we provide simple default values.
Users can override any parameter by passing kwargs to visualization functions.
"""

# Default map styling
DEFAULT_FIGSIZE = (12, 10)
DEFAULT_DPI = 300
DEFAULT_CMAP = "YlOrRd"  # Any matplotlib colormap name works
DEFAULT_CLASSIFICATION = "fisher_jenks"  # Any mapclassify scheme
DEFAULT_N_CLASSES = 5
DEFAULT_EDGE_COLOR = "white"
DEFAULT_EDGE_WIDTH = 0.5
DEFAULT_ALPHA = 1.0
DEFAULT_MISSING_COLOR = "#CCCCCC"

# Default legend styling
DEFAULT_LEGEND_LOC = "lower left"
DEFAULT_LEGEND_FONTSIZE = 10
DEFAULT_LEGEND_FMT = "{:.0f}"

# Backward compatibility - removed classes, keeping names for imports
# These will raise helpful errors if used
class ColorScheme:
    """DEPRECATED: Pass colormap names directly instead of using this enum."""
    def __init__(self):
        raise NotImplementedError(
            "ColorScheme enum has been removed. "
            "Pass colormap names directly (e.g., 'viridis', 'YlOrRd', 'Blues')"
        )

class ClassificationScheme:
    """DEPRECATED: Pass scheme names directly instead of using this enum."""
    def __init__(self):
        raise NotImplementedError(
            "ClassificationScheme enum has been removed. "
            "Pass scheme names directly (e.g., 'quantiles', 'fisher_jenks')"
        )

class MapConfig:
    """DEPRECATED: Pass parameters directly to ChoroplethMap instead."""
    def __init__(self):
        raise NotImplementedError(
            "MapConfig has been removed. "
            "Pass parameters directly to ChoroplethMap(...) or use **kwargs"
        )

class LegendConfig:
    """DEPRECATED: Pass legend parameters directly instead."""
    def __init__(self):
        raise NotImplementedError(
            "LegendConfig has been removed. "
            "Pass legend parameters directly via legend_kwds parameter"
        )
