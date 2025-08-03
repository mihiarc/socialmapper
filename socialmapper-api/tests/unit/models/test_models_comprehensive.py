#!/usr/bin/env python3
"""Comprehensive test for the core API data models implementation.
This test validates that task 4 requirements have been met:
- Create Pydantic models for analysis requests and responses
- Define job status and result models with proper validation
- Implement error response models with standardized format
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

import json
from datetime import datetime

# Import all the models we need to test
from api_server.models import (
    # Response models
    AnalysisResponse,
    AnalysisResult,
    BatchAnalysisItem,
    BatchAnalysisRequest,
    CensusVariable,
    CustomPOIAnalysisRequest,
    CustomPOILocation,
    # Error models
    DetailedValidationError,
    ErrorCode,
    ExportFormat,
    GeographicLevel,
    JobStatus,
    # Enums and base models
    JobStatusEnum,
    # Request models
    LocationAnalysisRequest,
    LocationSearchResult,
    POIType,
    ProcessingError,
    RateLimitError,
    ResourceNotFoundError,
    TravelMode,
    ValidationErrorDetail,
)
from pydantic import ValidationError


def test_analysis_request_models():
    """Test analysis request models with proper validation."""
    print("Testing analysis request models...")

    # Test LocationAnalysisRequest
    location_request = LocationAnalysisRequest(
        location="Portland, OR",
        poi_type="amenity",
        poi_name="library",
        travel_time=15,
        census_variables=["B01003_001E", "B25003_001E"],
        geographic_level=GeographicLevel.BLOCK_GROUP,
        travel_mode=TravelMode.WALK,
        include_isochrones=True,
        include_demographics=True
    )
    assert location_request.location == "Portland, OR"
    assert location_request.travel_time == 15
    assert len(location_request.census_variables) == 2
    print("✓ LocationAnalysisRequest created and validated")

    # Test CustomPOIAnalysisRequest
    custom_poi = CustomPOILocation(
        name="Central Library",
        latitude=45.5152,
        longitude=-122.6784,
        address="801 SW 10th Ave, Portland, OR",
        category="library"
    )

    custom_request = CustomPOIAnalysisRequest(
        location="Portland, OR",
        custom_pois=[custom_poi],
        travel_time=20,
        travel_mode=TravelMode.BIKE
    )
    assert len(custom_request.custom_pois) == 1
    assert custom_request.custom_pois[0].name == "Central Library"
    print("✓ CustomPOIAnalysisRequest created and validated")

    # Test BatchAnalysisRequest
    batch_item = BatchAnalysisItem(
        id="item-1",
        request=location_request
    )

    batch_request = BatchAnalysisRequest(
        items=[batch_item],
        priority=1
    )
    assert len(batch_request.items) == 1
    assert batch_request.priority == 1
    print("✓ BatchAnalysisRequest created and validated")

    # Test validation failures
    try:
        LocationAnalysisRequest(
            location="NY",  # Too short
            poi_type="amenity",
            poi_name="library"
        )
        assert False, "Should have failed validation"
    except ValidationError:
        print("✓ Location validation working correctly")

    try:
        CustomPOILocation(
            name="Test",
            latitude=91,  # Invalid latitude
            longitude=-122
        )
        assert False, "Should have failed validation"
    except ValidationError:
        print("✓ Coordinate validation working correctly")


def test_response_models():
    """Test response models with proper structure."""
    print("\nTesting response models...")

    # Test AnalysisResponse
    analysis_response = AnalysisResponse(
        job_id="job-123",
        status=JobStatusEnum.PENDING,
        created_at=datetime.now(),
        message="Job submitted successfully"
    )
    assert analysis_response.job_id == "job-123"
    assert analysis_response.status == JobStatusEnum.PENDING
    print("✓ AnalysisResponse created and validated")

    # Test JobStatus
    job_status = JobStatus(
        job_id="job-123",
        status=JobStatusEnum.RUNNING,
        progress=0.5,
        message="Processing analysis...",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    assert job_status.progress == 0.5
    assert job_status.status == JobStatusEnum.RUNNING
    print("✓ JobStatus created and validated")

    # Test AnalysisResult
    location_request = LocationAnalysisRequest(
        location="Portland, OR",
        poi_type="amenity",
        poi_name="library"
    )

    analysis_result = AnalysisResult(
        job_id="job-123",
        status=JobStatusEnum.COMPLETED,
        request=location_request,
        poi_count=15,
        demographics={"total_population": 50000},
        isochrones={"type": "FeatureCollection", "features": []},
        processing_time_seconds=45.2,
        created_at=datetime.now(),
        completed_at=datetime.now()
    )
    assert analysis_result.poi_count == 15
    assert "total_population" in analysis_result.demographics
    print("✓ AnalysisResult created and validated")


def test_metadata_models():
    """Test metadata models for census variables and POI types."""
    print("\nTesting metadata models...")

    # Test CensusVariable
    census_var = CensusVariable(
        code="B01003_001E",
        name="Total Population",
        concept="Total Population",
        group="Demographics",
        universe="Total population"
    )
    assert census_var.code == "B01003_001E"
    assert census_var.name == "Total Population"
    print("✓ CensusVariable created and validated")

    # Test POIType
    poi_type = POIType(
        type="amenity",
        name="library",
        description="Public library facility",
        category="Education & Culture",
        common_names=["library", "public library", "branch library"]
    )
    assert poi_type.type == "amenity"
    assert poi_type.name == "library"
    assert len(poi_type.common_names) == 3
    print("✓ POIType created and validated")

    # Test LocationSearchResult
    location_result = LocationSearchResult(
        display_name="Portland, Oregon, United States",
        city="Portland",
        state="Oregon",
        country="United States",
        latitude=45.5152,
        longitude=-122.6784,
        importance=0.8,
        place_type="city"
    )
    assert location_result.city == "Portland"
    assert location_result.latitude == 45.5152
    print("✓ LocationSearchResult created and validated")


def test_error_models():
    """Test comprehensive error response models."""
    print("\nTesting error models...")

    # Test ValidationErrorDetail
    validation_detail = ValidationErrorDetail(
        field="location",
        message="Location must be at least 3 characters long",
        invalid_value="NY",
        constraint="min_length"
    )
    assert validation_detail.field == "location"
    assert validation_detail.invalid_value == "NY"
    print("✓ ValidationErrorDetail created and validated")

    # Test DetailedValidationError
    detailed_error = DetailedValidationError(
        error_code=ErrorCode.VALIDATION_ERROR,
        message="Request validation failed",
        field_errors=[validation_detail]
    )
    assert detailed_error.error_code == ErrorCode.VALIDATION_ERROR
    assert len(detailed_error.field_errors) == 1
    print("✓ DetailedValidationError created and validated")

    # Test ResourceNotFoundError
    not_found_error = ResourceNotFoundError(
        error_code=ErrorCode.RESOURCE_NOT_FOUND,
        message="Job not found",
        resource_type="job",
        resource_id="job-123"
    )
    assert not_found_error.resource_type == "job"
    assert not_found_error.resource_id == "job-123"
    print("✓ ResourceNotFoundError created and validated")

    # Test RateLimitError
    rate_limit_error = RateLimitError(
        error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
        message="Rate limit exceeded",
        limit=100,
        window_seconds=60,
        retry_after_seconds=30,
        remaining_requests=0
    )
    assert rate_limit_error.limit == 100
    assert rate_limit_error.retry_after_seconds == 30
    print("✓ RateLimitError created and validated")

    # Test ProcessingError
    processing_error = ProcessingError(
        error_code=ErrorCode.PROCESSING_ERROR,
        message="Analysis processing failed",
        stage="isochrone_generation",
        retry_after_seconds=60
    )
    assert processing_error.stage == "isochrone_generation"
    print("✓ ProcessingError created and validated")


def test_json_serialization():
    """Test JSON serialization and deserialization."""
    print("\nTesting JSON serialization...")

    # Test request serialization
    request = LocationAnalysisRequest(
        location="Portland, OR",
        poi_type="amenity",
        poi_name="library",
        travel_time=15
    )

    # Serialize to JSON
    json_str = request.model_dump_json()
    assert isinstance(json_str, str)

    # Deserialize from JSON
    json_dict = json.loads(json_str)
    restored_request = LocationAnalysisRequest(**json_dict)
    assert restored_request.location == request.location
    assert restored_request.travel_time == request.travel_time
    print("✓ Request JSON serialization working")

    # Test response serialization
    response = AnalysisResponse(
        job_id="job-123",
        status=JobStatusEnum.PENDING,
        created_at=datetime.now()
    )

    json_str = response.model_dump_json()
    json_dict = json.loads(json_str)
    assert json_dict["job_id"] == "job-123"
    assert json_dict["status"] == "pending"
    print("✓ Response JSON serialization working")

    # Test error serialization
    error = DetailedValidationError(
        error_code=ErrorCode.VALIDATION_ERROR,
        message="Validation failed",
        field_errors=[
            ValidationErrorDetail(
                field="location",
                message="Required field"
            )
        ]
    )

    json_str = error.model_dump_json()
    json_dict = json.loads(json_str)
    assert json_dict["error_code"] == "validation_error"
    assert len(json_dict["field_errors"]) == 1
    print("✓ Error JSON serialization working")


def test_enum_values():
    """Test that all enums have correct values."""
    print("\nTesting enum values...")

    # Test JobStatusEnum
    assert JobStatusEnum.PENDING == "pending"
    assert JobStatusEnum.RUNNING == "running"
    assert JobStatusEnum.COMPLETED == "completed"
    assert JobStatusEnum.FAILED == "failed"
    assert JobStatusEnum.CANCELLED == "cancelled"
    print("✓ JobStatusEnum values correct")

    # Test TravelMode
    assert TravelMode.WALK == "walk"
    assert TravelMode.BIKE == "bike"
    assert TravelMode.DRIVE == "drive"
    print("✓ TravelMode values correct")

    # Test GeographicLevel
    assert GeographicLevel.BLOCK_GROUP == "block_group"
    assert GeographicLevel.ZCTA == "zcta"
    print("✓ GeographicLevel values correct")

    # Test ExportFormat
    assert ExportFormat.CSV == "csv"
    assert ExportFormat.GEOJSON == "geojson"
    assert ExportFormat.PARQUET == "parquet"
    assert ExportFormat.GEOPARQUET == "geoparquet"
    print("✓ ExportFormat values correct")

    # Test ErrorCode
    assert ErrorCode.VALIDATION_ERROR == "validation_error"
    assert ErrorCode.RESOURCE_NOT_FOUND == "resource_not_found"
    assert ErrorCode.PROCESSING_ERROR == "processing_error"
    assert ErrorCode.RATE_LIMIT_EXCEEDED == "rate_limit_exceeded"
    print("✓ ErrorCode values correct")


def main():
    """Run all tests."""
    print("=" * 60)
    print("COMPREHENSIVE API DATA MODELS TEST")
    print("=" * 60)

    try:
        test_analysis_request_models()
        test_response_models()
        test_metadata_models()
        test_error_models()
        test_json_serialization()
        test_enum_values()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("✅ Task 4 requirements have been successfully implemented:")
        print("   • Pydantic models for analysis requests and responses ✓")
        print("   • Job status and result models with proper validation ✓")
        print("   • Error response models with standardized format ✓")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
