"""Configuration classes for visualization module."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ColorScheme(str, Enum):
    """Available color schemes for choropleth maps."""

    # Sequential schemes (for continuous data)
    YLORBR = "YlOrBr"
    YLORD = "YlOrRd"
    ORANGES = "Oranges"
    REDS = "Reds"
    BLUES = "Blues"
    GREENS = "Greens"
    GREYS = "Greys"
    PURPLES = "Purples"
    VIRIDIS = "viridis"
    PLASMA = "plasma"
    INFERNO = "inferno"
    MAGMA = "magma"
    CIVIDIS = "cividis"

    # Diverging schemes (for data with meaningful midpoint)
    RDBU = "RdBu"
    RDYLBU = "RdYlBu"
    RDYLGN = "RdYlGn"
    SPECTRAL = "Spectral"
    BRBG = "BrBG"
    PIYG = "PiYG"
    PRGN = "PRGn"
    PUOR = "PuOr"
    RDGY = "RdGy"

    # Qualitative schemes (for categorical data)
    SET1 = "Set1"
    SET2 = "Set2"
    SET3 = "Set3"
    PASTEL1 = "Pastel1"
    PASTEL2 = "Pastel2"
    DARK2 = "Dark2"
    ACCENT = "Accent"
    PAIRED = "Paired"
    TAB10 = "tab10"
    TAB20 = "tab20"


class ClassificationScheme(str, Enum):
    """Classification methods for data binning."""

    QUANTILES = "quantiles"
    EQUAL_INTERVAL = "equal_interval"
    FISHER_JENKS = "fisher_jenks"
    JENKS_CASPALL = "jenks_caspall"
    HEAD_TAIL_BREAKS = "head_tail_breaks"
    MAXIMUM_BREAKS = "maximum_breaks"
    NATURAL_BREAKS = "natural_breaks"
    STD_MEAN = "std_mean"
    PERCENTILES = "percentiles"
    BOX_PLOT = "box_plot"
    FISHER_JENKS_SAMPLED = "fisher_jenks_sampled"
    MAX_P_CLASSIFIER = "max_p_classifier"
    DEFINED_INTERVAL = "defined_interval"


class LegendConfig(BaseModel):
    """Configuration for map legend."""

    title: str | None = None
    loc: str = "lower left"
    bbox_to_anchor: tuple[float, float] | None = None
    ncol: int = 1
    fontsize: int = 10
    title_fontsize: int = 12
    frameon: bool = True
    fancybox: bool = True
    shadow: bool = True
    borderpad: float = 0.4
    columnspacing: float = 2.0
    fmt: str = "{:.0f}"
    labels: list[str] | None = None

    @classmethod
    @field_validator("loc")
    def validate_loc(cls, v):
        """Validate legend location is a valid matplotlib location."""
        valid_locs = [
            "best",
            "upper right",
            "upper left",
            "lower left",
            "lower right",
            "right",
            "center left",
            "center right",
            "lower center",
            "upper center",
            "center",
        ]
        if v not in valid_locs:
            raise ValueError(f"loc must be one of {valid_locs}")
        return v


class MapConfig(BaseModel):
    """Configuration for chloropleth maps."""

    # Figure settings
    figsize: tuple[float, float] = (12, 10)
    dpi: int = 300
    facecolor: str = "white"
    edgecolor: str = "none"

    # Map appearance
    color_scheme: ColorScheme = ColorScheme.YLORBR
    classification_scheme: ClassificationScheme = ClassificationScheme.FISHER_JENKS
    n_classes: int = 5
    missing_color: str = "#CCCCCC"
    edge_color: str = "white"
    edge_width: float = 0.5
    alpha: float = 1.0

    # Map elements
    title: str | None = None
    title_fontsize: int = 16
    title_fontweight: str = "bold"
    title_pad: float = 20

    # Legend configuration
    legend: bool = True
    legend_config: LegendConfig = Field(default_factory=LegendConfig)

    # Additional elements
    north_arrow: bool = True
    north_arrow_location: str = "upper right"
    north_arrow_scale: float = 0.5

    scale_bar: bool = True
    scale_bar_location: str = "lower right"
    scale_bar_length_fraction: float = 0.25
    scale_bar_box_alpha: float = 0.8
    scale_bar_font_size: int = 10

    # Attribution
    attribution: str | None = "Data: US Census Bureau, OpenStreetMap | Analysis: SocialMapper"
    attribution_fontsize: int = 9
    attribution_color: str = "gray"

    # Export settings
    bbox_inches: str = "tight"
    pad_inches: float = 0.1

    # Basemap settings
    add_basemap: bool = True
    basemap_source: str = "OpenStreetMap.Mapnik"
    basemap_alpha: float = 0.6
    basemap_attribution: str | None = None
    basemap_zoom: str | int | None = "auto"  # Can be "auto", integer zoom level, or None

    # Advanced settings
    simplify_tolerance: float | None = 0.01
    aspect: str = "auto"

    @classmethod
    @field_validator("n_classes")
    def validate_n_classes(cls, v):
        """Validate number of classes is within reasonable bounds."""
        if v < 2 or v > 12:
            raise ValueError("n_classes must be between 2 and 12")
        return v
