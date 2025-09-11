"""Simplified result objects for SocialMapper.

Clean, Pythonic result containers that replace the complex Result pattern.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd


@dataclass
class AnalysisResult:
    """Clean result container for SocialMapper analysis.
    
    Provides direct access to analysis data without complex unwrapping.
    """
    
    # Core metrics
    poi_count: int
    census_units_analyzed: int
    isochrone_area_km2: float = 0.0
    
    # Data
    pois: List[Dict[str, Any]] = field(default_factory=list)
    demographics: Dict[str, float] = field(default_factory=dict)
    isochrones: Optional[Any] = None  # GeoDataFrame
    census_data: Optional[pd.DataFrame] = None
    
    # File outputs
    files_created: List[Path] = field(default_factory=list)
    output_directory: Optional[Path] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        """Check if analysis completed successfully."""
        return self.poi_count > 0
    
    @property
    def has_demographics(self) -> bool:
        """Check if demographic data is available."""
        return bool(self.demographics)
    
    @property
    def has_maps(self) -> bool:
        """Check if map files were created."""
        return any("map" in str(f).lower() for f in self.files_created)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'poi_count': self.poi_count,
            'census_units_analyzed': self.census_units_analyzed,
            'isochrone_area_km2': self.isochrone_area_km2,
            'demographics': self.demographics,
            'files_created': [str(f) for f in self.files_created],
            'output_directory': str(self.output_directory) if self.output_directory else None,
            'metadata': self.metadata,
            'warnings': self.warnings,
            'success': self.success,
            'has_demographics': self.has_demographics,
            'has_maps': self.has_maps,
        }
    
    def save_summary(self, path: Union[str, Path]) -> None:
        """Save analysis summary to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def print_summary(self) -> None:
        """Print a human-readable summary of results."""
        print("🗺️  SocialMapper Analysis Results")
        print("=" * 40)
        print(f"📍 POIs Found: {self.poi_count}")
        print(f"🏘️  Census Units: {self.census_units_analyzed}")
        print(f"📐 Isochrone Area: {self.isochrone_area_km2:.2f} km²")
        
        if self.has_demographics:
            print("\n📊 Demographics:")
            for var, value in self.demographics.items():
                if value is not None:
                    if isinstance(value, float) and value > 1000:
                        print(f"   {var}: {value:,.0f}")
                    else:
                        print(f"   {var}: {value}")
        
        if self.files_created:
            print(f"\n📁 Files Created: {len(self.files_created)}")
            for file in self.files_created[:3]:  # Show first 3
                print(f"   • {file.name}")
            if len(self.files_created) > 3:
                print(f"   ... and {len(self.files_created) - 3} more")
        
        if self.warnings:
            print(f"\n⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"   • {warning}")


@dataclass 
class POIResult:
    """Result container for POI discovery analysis."""
    
    # Core metrics
    total_poi_count: int
    category_counts: Dict[str, int] = field(default_factory=dict)
    unique_categories: int = 0
    
    # Data
    pois: List[Dict[str, Any]] = field(default_factory=list)
    isochrone_area_km2: float = 0.0
    
    # File outputs
    files_created: List[Path] = field(default_factory=list)
    output_directory: Optional[Path] = None
    
    # Metadata
    location: Optional[str] = None
    travel_time: int = 15
    travel_mode: str = "drive"
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate derived fields after initialization."""
        if not self.unique_categories and self.category_counts:
            self.unique_categories = len(self.category_counts)
    
    @property
    def success(self) -> bool:
        """Check if POI discovery completed successfully."""
        return self.total_poi_count > 0
    
    @property
    def has_maps(self) -> bool:
        """Check if map files were created."""
        return any("map" in str(f).lower() for f in self.files_created)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'total_poi_count': self.total_poi_count,
            'category_counts': self.category_counts,
            'unique_categories': self.unique_categories,
            'isochrone_area_km2': self.isochrone_area_km2,
            'files_created': [str(f) for f in self.files_created],
            'output_directory': str(self.output_directory) if self.output_directory else None,
            'location': self.location,
            'travel_time': self.travel_time,
            'travel_mode': self.travel_mode,
            'metadata': self.metadata,
            'warnings': self.warnings,
            'success': self.success,
            'has_maps': self.has_maps,
        }
    
    def save_summary(self, path: Union[str, Path]) -> None:
        """Save POI discovery summary to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def print_summary(self) -> None:
        """Print a human-readable summary of POI discovery results."""
        print("🗺️  SocialMapper POI Discovery Results")
        print("=" * 45)
        print(f"📍 Location: {self.location}")
        print(f"⏱️  Travel Time: {self.travel_time} minutes ({self.travel_mode})")
        print(f"🏢 Total POIs: {self.total_poi_count}")
        print(f"📐 Area Covered: {self.isochrone_area_km2:.2f} km²")
        
        if self.category_counts:
            print(f"\n📊 POIs by Category:")
            # Sort categories by count (descending)
            sorted_categories = sorted(
                self.category_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            for category, count in sorted_categories:
                print(f"   • {category}: {count}")
        
        if self.files_created:
            print(f"\n📁 Files Created: {len(self.files_created)}")
            for file in self.files_created[:3]:  # Show first 3
                print(f"   • {file.name}")
            if len(self.files_created) > 3:
                print(f"   ... and {len(self.files_created) - 3} more")
        
        if self.warnings:
            print(f"\n⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"   • {warning}")


def create_analysis_result_from_pipeline_data(
    pipeline_data: Dict[str, Any],
    config: Dict[str, Any]
) -> AnalysisResult:
    """Create AnalysisResult from pipeline output data.
    
    Converts the complex pipeline output into a clean result object.
    """
    # Extract POI data
    pois = pipeline_data.get("pois", [])
    
    # Extract demographics from census data
    demographics = {}
    census_data = pipeline_data.get("census_data")
    if census_data is not None and hasattr(census_data, 'columns'):
        for var in config.get("census_variables", []):
            if var in census_data.columns:
                valid_values = census_data[var].dropna()
                if len(valid_values) > 0:
                    # Sum for population-like variables, mean for income-like variables
                    if "population" in var.lower() or "count" in var.lower():
                        demographics[var] = valid_values.sum()
                    else:
                        demographics[var] = valid_values.mean()
    
    # Calculate isochrone area
    isochrone_area = 0.0
    isochrones = pipeline_data.get("isochrones")
    if isochrones is not None and hasattr(isochrones, 'geometry'):
        try:
            # Convert to equal area projection and calculate area in km²
            iso_equal_area = isochrones.to_crs("EPSG:5070")
            isochrone_area = iso_equal_area.geometry.area.sum() / 1_000_000
        except Exception:
            pass  # Silently handle projection errors
    
    # Extract file paths
    files_created = []
    output_dir = None
    
    # Look for various output files in pipeline data
    if "csv_data" in pipeline_data:
        csv_info = pipeline_data["csv_data"]
        if isinstance(csv_info, dict) and "csv_data" in csv_info:
            files_created.append(Path(csv_info["csv_data"]))
        elif isinstance(csv_info, (str, Path)):
            files_created.append(Path(csv_info))
    
    if "maps" in pipeline_data:
        maps_info = pipeline_data["maps"]
        if isinstance(maps_info, dict):
            if "output_paths" in maps_info:
                for map_path in maps_info["output_paths"].values():
                    files_created.append(Path(map_path))
            if "output_directory" in maps_info:
                output_dir = Path(maps_info["output_directory"])
    
    if "isochrone_file" in pipeline_data:
        files_created.append(Path(pipeline_data["isochrone_file"]))
    
    return AnalysisResult(
        poi_count=len(pois),
        census_units_analyzed=len(census_data) if census_data is not None else 0,
        isochrone_area_km2=isochrone_area,
        pois=pois,
        demographics=demographics,
        isochrones=isochrones,
        census_data=census_data,
        files_created=files_created,
        output_directory=output_dir,
        metadata={
            'travel_time': config.get('travel_time'),
            'location': f"{config.get('city', '')}, {config.get('state', '')}".strip(', '),
            'poi_types': f"{config.get('poi_type', '')}:{config.get('poi_name', '')}",
            'census_variables': config.get('census_variables', []),
        }
    )