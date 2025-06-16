"""SocialMapper constants and configuration values.

This module defines constants used throughout the SocialMapper project to avoid
magic numbers and ensure consistency.

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

# Geographic coordinate limits (WGS84)
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

# File system limits
MAX_FILENAME_LENGTH = 255
MIN_ASCII_PRINTABLE = 32

# Address validation
MIN_ADDRESS_LENGTH = 3
MAX_VARIABLE_NAME_LENGTH = 50

# Data validation
MIN_CLUSTER_POINTS = 2
MIN_GEOJSON_COORDINATES = 2

# HTTP status codes
HTTP_TOO_MANY_REQUESTS = 429
HTTP_SERVER_ERROR_START = 500
HTTP_SERVER_ERROR_END = 600

# System resource thresholds (in GB)
LOW_MEMORY_THRESHOLD = 4.0
HIGH_MEMORY_THRESHOLD = 16.0
ENTERPRISE_MEMORY_THRESHOLD = 32.0

# CPU core thresholds
MIN_CPU_CORES = 2
RECOMMENDED_CPU_CORES = 4
HIGH_PERFORMANCE_CPU_CORES = 8
ENTERPRISE_CPU_CORES = 16

# Memory thresholds (in GB)
MINIMUM_MEMORY_GB = 2.0
LOW_MEMORY_WARNING_GB = 4.0
RECOMMENDED_MEMORY_GB = 8.0
MEDIUM_MEMORY_THRESHOLD = 8.0

# Disk space thresholds (in GB)
MINIMUM_DISK_SPACE_GB = 1.0
RECOMMENDED_DISK_SPACE_GB = 5.0
LARGE_DATASET_DISK_SPACE_GB = 10.0

# Configuration validation limits
MAX_MEMORY_LIMIT_WARNING = 64
MIN_STREAMING_BATCH_SIZE = 10
MAX_CONCURRENT_DOWNLOADS_WARNING = 100
MIN_CACHE_SIZE_WARNING = 0.1
MIN_DISTANCE_CHUNK_SIZE = 100
MAX_DISTANCE_CHUNK_SIZE = 100000

# UI display limits
MAX_POI_NAME_DISPLAY_LENGTH = 30
MAX_POI_DISPLAY_COUNT = 10
POI_COUNT_TRUNCATION_THRESHOLD = 10

# Scale and measurement constants
SCALE_METER_TO_KM_THRESHOLD = 1
SCALE_KM_DISPLAY_THRESHOLD = 10

# Classification limits
MIN_CLASSIFICATION_CLASSES = 2
MAX_CLASSIFICATION_CLASSES = 12


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


def is_large_dataset(size_mb: float | None = None, record_count: int | None = None) -> bool:
    """Determine if dataset should be considered 'large' for processing."""
    if size_mb is not None:
        return size_mb > LARGE_DATASET_MB
    if record_count is not None:
        return record_count > LARGE_DATASET_RECORDS
    return False
