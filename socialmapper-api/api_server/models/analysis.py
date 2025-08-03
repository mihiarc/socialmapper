"""Analysis request and response models for the SocialMapper API.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, validator

from .base import (
    BaseResponse,
    ExportFormat,
    GeographicLevel,
    JobStatusEnum,
    TravelMode,
)


class BaseAnalysisRequest(BaseModel):
    """Base class for all analysis requests."""
    travel_time: int = Field(15, ge=1, le=120, description="Travel time in minutes")
    census_variables: list[str] = Field(
        default=["B01003_001E"],
        description="List of Census variable codes"
    )
    geographic_level: GeographicLevel = Field(
        GeographicLevel.BLOCK_GROUP,
        description="Geographic analysis level"
    )
    travel_mode: TravelMode = Field(
        TravelMode.WALK,
        description="Mode of transportation"
    )
    include_isochrones: bool = Field(True, description="Include isochrone polygons in results")
    include_demographics: bool = Field(True, description="Include demographic analysis")

    @validator('census_variables')
    def validate_census_variables(cls, v):
        """Validate census variables list."""
        if not v:
            raise ValueError("At least one census variable must be specified")
        # Basic validation for census variable format
        for var in v:
            if not var or not var.strip():
                raise ValueError("Census variable cannot be empty")
            # Check basic census variable format (letter + numbers + underscore + numbers + letter)
            var_clean = var.strip()
            if len(var_clean) < 5:
                raise ValueError(f"Census variable '{var_clean}' appears to be too short")
        return [var.strip() for var in v]


class LocationAnalysisRequest(BaseAnalysisRequest):
    """Request model for location-based POI analysis."""
    location: str = Field(..., description="Location to analyze (city, state format)")
    poi_type: str = Field(..., description="OpenStreetMap POI type (e.g., 'amenity')")
    poi_name: str = Field(..., description="OpenStreetMap POI name (e.g., 'library')")

    @validator('location')
    def validate_location(cls, v):
        """Validate location format."""
        if not v or len(v.strip()) < 3:
            raise ValueError("Location must be at least 3 characters long")
        return v.strip()

    @validator('poi_type')
    def validate_poi_type(cls, v):
        """Validate POI type."""
        if not v or len(v.strip()) < 2:
            raise ValueError("POI type must be at least 2 characters long")
        return v.strip()

    @validator('poi_name')
    def validate_poi_name(cls, v):
        """Validate POI name."""
        if not v or len(v.strip()) < 2:
            raise ValueError("POI name must be at least 2 characters long")
        return v.strip()


class CustomPOILocation(BaseModel):
    """Model for custom POI location."""
    name: str = Field(..., description="POI name")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    address: str | None = Field(None, description="Optional address")
    category: str | None = Field(None, description="Optional POI category")

    @validator('name')
    def validate_name(cls, v):
        """Validate POI name."""
        if not v or len(v.strip()) < 1:
            raise ValueError("POI name cannot be empty")
        return v.strip()


class CustomPOIAnalysisRequest(BaseAnalysisRequest):
    """Request model for custom POI analysis."""
    location: str = Field(..., description="Analysis area location (city, state format)")
    custom_pois: list[CustomPOILocation] = Field(
        ...,
        min_items=1,
        description="List of custom POI locations"
    )

    @validator('location')
    def validate_location(cls, v):
        """Validate location format."""
        if not v or len(v.strip()) < 3:
            raise ValueError("Location must be at least 3 characters long")
        return v.strip()

    @validator('custom_pois')
    def validate_custom_pois(cls, v):
        """Validate custom POIs list."""
        if not v:
            raise ValueError("At least one custom POI must be provided")
        if len(v) > 100:  # Reasonable limit
            raise ValueError("Too many custom POIs (maximum 100 allowed)")
        return v


class BatchAnalysisItem(BaseModel):
    """Single item in a batch analysis request."""
    id: str = Field(..., description="Unique identifier for this analysis item")
    request: LocationAnalysisRequest | CustomPOIAnalysisRequest = Field(
        ...,
        description="Analysis request"
    )

    @validator('id')
    def validate_id(cls, v):
        """Validate item ID."""
        if not v or len(v.strip()) < 1:
            raise ValueError("Item ID cannot be empty")
        return v.strip()


class BatchAnalysisRequest(BaseModel):
    """Request model for batch analysis processing."""
    items: list[BatchAnalysisItem] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="List of analysis items to process"
    )
    priority: int = Field(1, ge=1, le=5, description="Processing priority (1=highest, 5=lowest)")

    @validator('items')
    def validate_items(cls, v):
        """Validate batch items."""
        if not v:
            raise ValueError("At least one analysis item must be provided")

        # Check for duplicate IDs
        ids = [item.id for item in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate item IDs found in batch request")

        return v


# Maintain backward compatibility
AnalysisRequest = LocationAnalysisRequest


class AnalysisResponse(BaseResponse):
    """Response model for analysis submission."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatusEnum = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    estimated_completion: datetime | None = Field(
        None,
        description="Estimated completion time"
    )
    message: str | None = Field(None, description="Status message")

    @validator('job_id')
    def validate_job_id(cls, v):
        """Validate job ID format."""
        if not v or len(v.strip()) < 1:
            raise ValueError("Job ID cannot be empty")
        return v.strip()


class BatchAnalysisResponse(BaseResponse):
    """Response model for batch analysis submission."""
    batch_id: str = Field(..., description="Unique batch identifier")
    job_ids: list[str] = Field(..., description="List of individual job identifiers")
    status: JobStatusEnum = Field(..., description="Overall batch status")
    created_at: datetime = Field(..., description="Batch creation timestamp")
    estimated_completion: datetime | None = Field(
        None,
        description="Estimated completion time for entire batch"
    )
    total_items: int = Field(..., description="Total number of items in batch")

    @validator('batch_id')
    def validate_batch_id(cls, v):
        """Validate batch ID format."""
        if not v or len(v.strip()) < 1:
            raise ValueError("Batch ID cannot be empty")
        return v.strip()

    @validator('job_ids')
    def validate_job_ids(cls, v):
        """Validate job IDs list."""
        if not v:
            raise ValueError("At least one job ID must be provided")
        for job_id in v:
            if not job_id or len(job_id.strip()) < 1:
                raise ValueError("Job ID cannot be empty")
        return v


class JobStatus(BaseResponse):
    """Job status response model."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatusEnum = Field(..., description="Current job status")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Job progress (0.0 to 1.0)")
    message: str | None = Field(None, description="Current status message")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: datetime | None = Field(None, description="Job start timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    estimated_completion: datetime | None = Field(
        None,
        description="Estimated completion time"
    )
    error: str | None = Field(None, description="Error message if job failed")


class ExportRequest(BaseModel):
    """Request model for exporting analysis results."""
    job_id: str = Field(..., description="Job identifier to export")
    format: ExportFormat = Field(..., description="Export format")
    include_isochrones: bool = Field(True, description="Include isochrone data in export")
    include_demographics: bool = Field(True, description="Include demographic data in export")

    @validator('job_id')
    def validate_job_id(cls, v):
        """Validate job ID format."""
        if not v or len(v.strip()) < 1:
            raise ValueError("Job ID cannot be empty")
        return v.strip()


class ExportResponse(BaseResponse):
    """Response model for export requests."""
    export_id: str = Field(..., description="Unique export identifier")
    job_id: str = Field(..., description="Source job identifier")
    format: ExportFormat = Field(..., description="Export format")
    status: JobStatusEnum = Field(..., description="Export status")
    download_url: str | None = Field(None, description="Download URL when ready")
    expires_at: datetime | None = Field(None, description="Download URL expiration")
    file_size_bytes: int | None = Field(None, description="File size in bytes")


class BatchJobStatus(BaseResponse):
    """Status response for batch analysis."""
    batch_id: str = Field(..., description="Batch identifier")
    status: JobStatusEnum = Field(..., description="Overall batch status")
    total_items: int = Field(..., description="Total number of items")
    completed_items: int = Field(0, description="Number of completed items")
    failed_items: int = Field(0, description="Number of failed items")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Overall progress")
    job_statuses: list[JobStatus] = Field(..., description="Individual job statuses")
    created_at: datetime = Field(..., description="Batch creation timestamp")
    estimated_completion: datetime | None = Field(None, description="Estimated completion")


class AnalysisResult(BaseResponse):
    """Complete analysis result model."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatusEnum = Field(..., description="Job status")
    request: LocationAnalysisRequest | CustomPOIAnalysisRequest = Field(
        ...,
        description="Original analysis request"
    )

    # Results data
    poi_count: int | None = Field(None, ge=0, description="Number of POIs found")
    demographics: dict[str, Any] | None = Field(
        None,
        description="Demographic analysis results"
    )
    isochrones: dict[str, Any] | None = Field(
        None,
        description="Isochrone polygon data (GeoJSON format)"
    )

    # Analysis metadata
    analysis_area_km2: float | None = Field(
        None,
        ge=0,
        description="Total analysis area in square kilometers"
    )
    population_covered: int | None = Field(
        None,
        ge=0,
        description="Total population in analysis area"
    )

    # Processing metadata
    processing_time_seconds: float | None = Field(
        None,
        ge=0,
        description="Total processing time in seconds"
    )
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: datetime | None = Field(None, description="Job start timestamp")
    completed_at: datetime | None = Field(None, description="Job completion timestamp")

    # Export information
    export_urls: dict[ExportFormat, str] | None = Field(
        None,
        description="URLs for downloading results in different formats"
    )

    # Error information
    error: str | None = Field(None, description="Error message if job failed")
    error_details: dict[str, Any] | None = Field(
        None,
        description="Detailed error information"
    )

    @validator('job_id')
    def validate_job_id(cls, v):
        """Validate job ID format."""
        if not v or len(v.strip()) < 1:
            raise ValueError("Job ID cannot be empty")
        return v.strip()


class CensusVariable(BaseModel):
    """Model for census variable metadata."""
    code: str = Field(..., description="Census variable code (e.g., 'B01003_001E')")
    name: str = Field(..., description="Human-readable variable name")
    concept: str = Field(..., description="Census concept/table name")
    group: str | None = Field(None, description="Variable group/category")
    universe: str | None = Field(None, description="Universe description")

    @validator('code')
    def validate_code(cls, v):
        """Validate census variable code format."""
        if not v or len(v.strip()) < 5:
            raise ValueError("Census variable code must be at least 5 characters")
        return v.strip().upper()

    @validator('name')
    def validate_name(cls, v):
        """Validate variable name."""
        if not v or len(v.strip()) < 1:
            raise ValueError("Variable name cannot be empty")
        return v.strip()


class CensusVariablesResponse(BaseResponse):
    """Response model for census variables endpoint."""
    variables: list[CensusVariable] = Field(..., description="Available census variables")
    total_count: int = Field(..., description="Total number of variables")
    categories: list[str] = Field(..., description="Available variable categories")


class POIType(BaseModel):
    """Model for POI type information."""
    type: str = Field(..., description="OpenStreetMap POI type (e.g., 'amenity')")
    name: str = Field(..., description="POI name (e.g., 'library')")
    description: str | None = Field(None, description="Description of this POI type")
    category: str | None = Field(None, description="POI category")
    common_names: list[str] | None = Field(None, description="Common alternative names")

    @validator('type')
    def validate_type(cls, v):
        """Validate POI type."""
        if not v or len(v.strip()) < 1:
            raise ValueError("POI type cannot be empty")
        return v.strip().lower()

    @validator('name')
    def validate_name(cls, v):
        """Validate POI name."""
        if not v or len(v.strip()) < 1:
            raise ValueError("POI name cannot be empty")
        return v.strip().lower()


class POITypesResponse(BaseResponse):
    """Response model for POI types endpoint."""
    poi_types: list[POIType] = Field(..., description="Available POI types")
    total_count: int = Field(..., description="Total number of POI types")
    categories: list[str] = Field(..., description="Available POI categories")


class LocationSearchResult(BaseModel):
    """Model for location search result."""
    display_name: str = Field(..., description="Full display name of location")
    city: str | None = Field(None, description="City name")
    state: str | None = Field(None, description="State name")
    country: str = Field(..., description="Country name")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    importance: float | None = Field(None, description="Search result importance score")
    place_type: str | None = Field(None, description="Type of place (city, town, etc.)")

    @validator('display_name')
    def validate_display_name(cls, v):
        """Validate display name."""
        if not v or len(v.strip()) < 1:
            raise ValueError("Display name cannot be empty")
        return v.strip()

    @validator('country')
    def validate_country(cls, v):
        """Validate country."""
        if not v or len(v.strip()) < 1:
            raise ValueError("Country cannot be empty")
        return v.strip()


class LocationSearchResponse(BaseResponse):
    """Response model for location search endpoint."""
    query: str = Field(..., description="Original search query")
    results: list[LocationSearchResult] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results")


class ProcessingJob(BaseModel):
    """Internal job tracking model."""
    id: str = Field(..., description="Unique job identifier")
    request: LocationAnalysisRequest | CustomPOIAnalysisRequest | BatchAnalysisRequest = Field(
        ...,
        description="Analysis request"
    )
    status: JobStatusEnum = Field(JobStatusEnum.PENDING, description="Current status")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Progress percentage")
    message: str | None = Field(None, description="Current status message")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    # Results
    result: dict[str, Any] | None = None
    error: str | None = None
    error_details: dict[str, Any] | None = None

    # Processing metadata
    processing_time_seconds: float | None = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
