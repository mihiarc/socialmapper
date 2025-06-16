"""Constants module for SocialMapper.

This module centralizes all magic numbers and constant values used throughout
the SocialMapper codebase, making the code more maintainable and self-documenting.

Categories:
- Geographic & Coordinate Constants
- Time & Performance Limits  
- Data Processing Thresholds
- File & Network Configuration
- Census & Geographic Identifiers
"""

# =============================================================================
# GEOGRAPHIC & COORDINATE CONSTANTS
# =============================================================================

# Coordinate bounds (degrees)
MIN_LATITUDE = -90.0
MAX_LATITUDE = 90.0
MIN_LONGITUDE = -180.0
MAX_LONGITUDE = 180.0

# Common coordinate reference systems
WGS84_EPSG = 4326  # Standard GPS coordinates
WEB_MERCATOR_EPSG = 3857  # Web mapping standard

# Geographic calculations
DEGREES_PER_KM_AT_EQUATOR = 1.0 / 111.0  # Approximate conversion
KM_PER_DEGREE_AT_EQUATOR = 111.0  # Approximate conversion


# =============================================================================
# TIME & PERFORMANCE LIMITS
# =============================================================================

# Travel time constraints (minutes)
MIN_TRAVEL_TIME = 1
MAX_TRAVEL_TIME = 120

# Timeout values (seconds)
DEFAULT_API_TIMEOUT = 30
LONG_API_TIMEOUT = 60
SHORT_API_TIMEOUT = 10

# CPU and memory thresholds (percentages)
HIGH_CPU_USAGE_THRESHOLD = 90
HIGH_MEMORY_USAGE_THRESHOLD = 85
MEMORY_WARNING_THRESHOLD = 75


# =============================================================================
# DATA PROCESSING THRESHOLDS
# =============================================================================

# Data size thresholds (MB)
SMALL_DATASET_MB = 10.0
MEDIUM_DATASET_MB = 100.0
LARGE_DATASET_MB = 500.0

# Record count thresholds
SMALL_DATASET_RECORDS = 1000
MEDIUM_DATASET_RECORDS = 10000
LARGE_DATASET_RECORDS = 100000

# Clustering and spatial analysis
DEFAULT_CLUSTER_RADIUS_KM = 15.0
MIN_CLUSTER_SIZE = 2
DEFAULT_SPATIAL_BUFFER_KM = 5.0

# Distance thresholds (meters)
CITY_SCALE_DISTANCE_M = 50000      # ~50km - city scale
METRO_SCALE_DISTANCE_M = 100000    # ~100km - metro area scale
REGIONAL_SCALE_DISTANCE_M = 200000 # ~200km - regional scale
STATE_SCALE_DISTANCE_M = 400000    # ~400km - state scale


# =============================================================================
# FILE & NETWORK CONFIGURATION
# =============================================================================

# File processing
MAX_BATCH_SIZE = 1000
DEFAULT_CHUNK_SIZE = 5000
LARGE_FILE_CHUNK_SIZE = 10000

# Network and caching
DEFAULT_CACHE_TTL_HOURS = 24
MAX_RETRIES = 3
DEFAULT_RATE_LIMIT_PER_SECOND = 1

# HTTP Status Codes (for API responses)
HTTP_OK = 200
HTTP_TOO_MANY_REQUESTS = 429
HTTP_INTERNAL_SERVER_ERROR = 500

# File size limits (bytes)
MAX_UPLOAD_SIZE_MB = 100
WARNING_FILE_SIZE_MB = 50


# =============================================================================
# CENSUS & GEOGRAPHIC IDENTIFIERS
# =============================================================================

# FIPS code lengths
STATE_FIPS_LENGTH = 2
COUNTY_FIPS_LENGTH = 3
TRACT_LENGTH = 6
BLOCK_GROUP_LENGTH = 1
FULL_TRACT_GEOID_LENGTH = 11  # state + county + tract
FULL_BLOCK_GROUP_GEOID_LENGTH = 12  # state + county + tract + block group

# Census data constraints
MAX_VARIABLES_PER_REQUEST = 50
MAX_GEOGRAPHIES_PER_REQUEST = 500


# =============================================================================
# UI & VISUALIZATION CONSTANTS
# =============================================================================

# Progress and display
DEFAULT_PROGRESS_UPDATE_INTERVAL = 0.1  # seconds
MIN_RECORDS_FOR_PROGRESS = 100

# Map visualization
DEFAULT_MAP_DPI = 300
DEFAULT_FIGURE_WIDTH = 12
DEFAULT_FIGURE_HEIGHT = 8

# Color and styling
DEFAULT_ALPHA = 0.7
HIGHLIGHT_ALPHA = 0.9


# =============================================================================
# VALIDATION & PARSING CONSTANTS
# =============================================================================

# String parsing
COORDINATE_PAIR_PARTS = 2  # lat,lon format
MIN_ADDRESS_LENGTH = 5
MAX_ADDRESS_LENGTH = 200

# Numeric validation tolerances
COORDINATE_PRECISION_TOLERANCE = 1e-6
PERCENTAGE_TOLERANCE = 0.01

# Default buffer sizes for various operations
DEFAULT_GEOMETRY_BUFFER_M = 1000  # 1km default buffer
INTERSECTION_BUFFER_M = 100       # Small buffer for intersection checks


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def validate_travel_time(minutes: int) -> bool:
    """Validate travel time is within acceptable bounds."""
    return MIN_TRAVEL_TIME <= minutes <= MAX_TRAVEL_TIME


def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude and longitude are within valid ranges."""
    return (MIN_LATITUDE <= lat <= MAX_LATITUDE and
            MIN_LONGITUDE <= lon <= MAX_LONGITUDE)


def get_scale_category(distance_m: float) -> str:
    """Categorize geographic scale based on distance."""
    if distance_m <= CITY_SCALE_DISTANCE_M:
        return "city"
    elif distance_m <= METRO_SCALE_DISTANCE_M:
        return "metro"
    elif distance_m <= REGIONAL_SCALE_DISTANCE_M:
        return "regional"
    else:
        return "state"


def is_large_dataset(size_mb: float = None, record_count: int = None) -> bool:
    """Determine if dataset should be considered 'large' for processing."""
    if size_mb is not None:
        return size_mb > LARGE_DATASET_MB
    if record_count is not None:
        return record_count > LARGE_DATASET_RECORDS
    return False
