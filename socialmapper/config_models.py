from pydantic import BaseModel, ConfigDict, Field, field_validator


class RunConfig(BaseModel):
    """DEPRECATED: Use SocialMapperBuilder from socialmapper.api instead.

    This configuration model is maintained for backward compatibility only
    and will be removed in version 0.6.0.

    Example migration:
        # Old way (deprecated):
        config = RunConfig(
            custom_coords_path="locations.csv",
            travel_time=20,
            census_variables=["total_population"]
        )
        run_socialmapper(config)

        # New way (recommended):
        from socialmapper.api import SocialMapperBuilder, SocialMapperClient

        config = (SocialMapperBuilder()
            .with_custom_pois("locations.csv")
            .with_travel_time(20)
            .with_census_variables("total_population")
            .build()
        )

        with SocialMapperClient() as client:
            result = client.run_analysis(config)
    """

    # Use Pydantic V2 ConfigDict instead of class Config
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Mutually-exclusive input methods
    custom_coords_path: str | None = Field(
        None, description="Path to a CSV/JSON file with custom coordinates"
    )

    # Core parameters
    travel_time: int = Field(15, ge=1, le=120, description="Travel time in minutes for isochrones")
    census_variables: list[str] = Field(
        default_factory=lambda: ["total_population"],
        description="List of census variables (either friendly names or raw codes)",
    )
    api_key: str | None = Field(None, description="Census API key")

    # Output control parameters
    export_csv: bool = Field(True, description="Export census data to CSV format")
    export_maps: bool = Field(False, description="Generate map visualizations")

    @field_validator("custom_coords_path")
    @classmethod
    def at_least_one_input(cls, v):
        """Validate that custom_coords_path is provided."""
        if not v:
            raise ValueError("custom_coords_path must be provided")
        return v
