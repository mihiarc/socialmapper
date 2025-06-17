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
# ADDITIONAL CONSTANTS FOR MAGIC VALUE FIXES
# =============================================================================

# Data Processing Constants
CATEGORICAL_CONVERSION_THRESHOLD = 0.5  # Unique ratio threshold for converting to categorical
DEFAULT_BATCH_SIZE = 1000  # Default batch size for processing
PROGRESS_UPDATE_INTERVAL = 1000  # How often to update progress bars
SMALL_DATASET_THRESHOLD = 50  # Threshold for small datasets
MEDIUM_DATASET_THRESHOLD = 500  # Threshold for medium datasets
LARGE_DATASET_THRESHOLD = 5000  # Threshold for large datasets

# Travel and Distance Constants
DEFAULT_TRAVEL_TIME_MINUTES = 30  # Default travel time for isochrones
DEFAULT_SEARCH_RADIUS_KM = 50  # Default search radius in kilometers
SHORT_DISTANCE_THRESHOLD_M = 500  # Short distance threshold in meters

# Area Constants
SMALL_AREA_THRESHOLD_KM2 = 100  # Small area threshold in square kilometers
MEDIUM_AREA_THRESHOLD_KM2 = 1000  # Medium area threshold in square kilometers
SMALL_POLYGON_AREA_THRESHOLD_KM2 = 0.01  # Small polygon area threshold

# Rate Limiting Constants
RATE_LIMIT_ADAPTATION_INTERVAL_S = 60  # Rate limit adaptation interval in seconds
MIN_REQUESTS_BEFORE_RATE_INCREASE = 10  # Minimum requests before increasing rate
ERROR_RATE_THRESHOLD = 0.1  # 10% error rate threshold

# Cache Constants
CACHE_EXPIRY_DAYS = 30  # Cache expiry in days
RECENT_CACHE_THRESHOLD_DAYS = 7  # Recent cache threshold in days
CACHE_SIZE_LIMIT_MB = 100  # Cache size limit in MB
CACHE_REDUCTION_TARGET_RATIO = 0.8  # Target ratio when reducing cache

# Geocoding Constants
WESTERN_US_LONGITUDE_THRESHOLD = -100  # Longitude threshold for western US states

# Visualization Constants
SCALE_TEXT_KM_THRESHOLD = 10  # Threshold for scale text formatting in km
LEGEND_Y_POSITION = 0.2  # Legend position y-coordinate
LEGEND_ITEM_LIMIT = 100  # Maximum number of legend items
SUBPLOT_COUNT = 4  # Number of subplots in grid layouts

# POI Constants
SMALL_POI_COUNT = 10  # Small POI count threshold
LARGE_POI_COUNT = 100  # Large POI count threshold

# ZCTA Constants
SMALL_ZCTA_COUNT = 10  # Small ZCTA count threshold
MEDIUM_ZCTA_COUNT = 50  # Medium ZCTA count threshold
LARGE_ZCTA_BATCH_SIZE = 2000  # Batch size for large ZCTA queries
SMALL_ZCTA_BATCH_SIZE = 500  # Batch size for small ZCTA queries

# Network Processing Constants
NETWORK_BUFFER_SCALE = 0.9  # Network buffer scale factor
DISSOLVE_BUFFER_FACTOR = 0.99  # Dissolve buffer factor
SIMPLIFICATION_TOLERANCE = 0.01  # Tolerance for geometry simplification
AREA_SCALING_FACTOR = 0.5  # Area scaling factor for network processing

# Request Processing Constants
LARGE_REQUEST_BATCH_SIZE = 10000  # Large request batch size
CENSUS_REQUEST_BATCH_SIZE = 1000  # Census API request batch size
SMALL_BATCH_SIZE = 100  # Small batch size for API requests
TRANSFORM_BATCH_SIZE = 200  # Batch size for transform operations

# HTTP Status Codes (additional)
HTTP_OK = 200
HTTP_NOT_FOUND = 404
HTTP_TOO_MANY_REQUESTS = 429  # Already defined above, but keeping for clarity
HTTP_SERVER_ERROR = 500

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
