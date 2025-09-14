"""Configuration objects for SocialMapper API functions."""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union, Dict, Any


@dataclass
class IsochroneConfig:
    """Configuration for isochrone generation."""

    location: Union[str, Tuple[float, float]]
    travel_time: int = 15
    travel_mode: str = "drive"

    def __post_init__(self):
        if not 1 <= self.travel_time <= 120:
            raise ValueError(
                f"Travel time must be between 1 and 120 minutes, "
                f"got {self.travel_time}"
            )

        if self.travel_mode not in ["drive", "walk", "bike"]:
            raise ValueError(
                f"Travel mode must be 'drive', 'walk', or 'bike', "
                f"got {self.travel_mode}"
            )


@dataclass
class CensusConfig:
    """Configuration for census data retrieval."""

    location: Union[Dict, List[str], Tuple[float, float]]
    variables: List[str]
    year: int = 2023


@dataclass
class PoiConfig:
    """Configuration for POI search."""

    location: Union[str, Tuple[float, float]]
    categories: Optional[List[str]] = None
    travel_time: Optional[int] = None
    limit: int = 100
    validate_coords: bool = True


@dataclass
class MapConfig:
    """Configuration for map creation."""

    data: Union[List[Dict], Any]  # pandas/geopandas types
    column: str
    title: Optional[str] = None
    save_path: Optional[str] = None
    export_format: str = "png"


@dataclass
class MultipleAnalysisConfig:
    """Configuration for multiple location analysis."""

    locations: List[Union[str, Tuple[float, float]]]
    travel_time: int = 15
    travel_mode: str = "drive"
    variables: List[str] = None
    compare: bool = True

    def __post_init__(self):
        if self.variables is None:
            self.variables = ["population"]


@dataclass
class ReportConfig:
    """Configuration for report generation."""

    analysis_data: Dict[str, Any]
    format: str = "html"
    template: str = "default"
    include_maps: bool = True

    def __post_init__(self):
        if self.format not in ["html", "pdf"]:
            raise ValueError("Format must be 'html' or 'pdf'")