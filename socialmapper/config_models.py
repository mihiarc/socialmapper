from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional

class RunConfig(BaseModel):
    """Validated configuration for running the socialmapper pipeline."""

    # Use Pydantic V2 ConfigDict instead of class Config
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Mutually-exclusive input methods
    custom_coords_path: Optional[str] = Field(None, description="Path to a CSV/JSON file with custom coordinates")

    # Core parameters
    travel_time: int = Field(15, ge=1, le=120, description="Travel time in minutes for isochrones")
    census_variables: List[str] = Field(default_factory=lambda: ["total_population"], description="List of census variables (either friendly names or raw codes)")
    api_key: Optional[str] = Field(None, description="Census API key")

    # Output control parameters
    export_csv: bool = Field(True, description="Export census data to CSV format")
    export_maps: bool = Field(False, description="Generate map visualizations")

    @field_validator("custom_coords_path")
    @classmethod
    def at_least_one_input(cls, v):
        if not v:
            raise ValueError("custom_coords_path must be provided")
        return v 