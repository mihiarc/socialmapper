"""Constants for SocialMapper API."""

# Travel time constraints
MIN_TRAVEL_TIME = 1
MAX_TRAVEL_TIME = 120

# Valid modes of transportation
VALID_TRAVEL_MODES = ["drive", "walk", "bike"]

# Default values
DEFAULT_TRAVEL_TIME = 15
DEFAULT_TRAVEL_MODE = "drive"
DEFAULT_SEARCH_RADIUS_KM = 5.0
DEFAULT_POI_LIMIT = 100
DEFAULT_EXPORT_FORMAT = "png"
DEFAULT_CENSUS_YEAR = 2023

# Export formats
VALID_EXPORT_FORMATS = ["png", "pdf", "svg", "geojson", "shapefile"]
IMAGE_EXPORT_FORMATS = ["png", "pdf", "svg"]

# Coordinate boundaries
MIN_LATITUDE = -90
MAX_LATITUDE = 90
MIN_LONGITUDE = -180
MAX_LONGITUDE = 180

# Report formats
VALID_REPORT_FORMATS = ["html", "pdf"]

# Input validation constraints
MAX_VARIABLE_NAME_LENGTH = 100
MIN_ADDRESS_LENGTH = 3
MIN_ASCII_PRINTABLE = 32

# System resource thresholds
HIGH_CPU_USAGE_THRESHOLD = 80  # CPU usage percentage
HIGH_MEMORY_USAGE_THRESHOLD = 80  # Memory usage percentage

# Map scale distance thresholds (in meters)
CITY_SCALE_DISTANCE_M = 10000  # 10 km - neighborhood/small city
METRO_SCALE_DISTANCE_M = 50000  # 50 km - city/metro area
REGIONAL_SCALE_DISTANCE_M = 200000  # 200 km - large metro/small region
STATE_SCALE_DISTANCE_M = 500000  # 500 km - region/small state

# Clustering parameters
MIN_CLUSTER_POINTS = 2  # Minimum points required for clustering

# GeoJSON validation
MIN_GEOJSON_COORDINATES = 2  # Minimum coordinates for valid GeoJSON

# Dataset size thresholds (in MB)
SMALL_DATASET_MB = 10  # Small datasets - use in-memory processing
LARGE_DATASET_MB = 100  # Large datasets - use streaming/chunked processing

# Data type optimization
CATEGORICAL_CONVERSION_THRESHOLD = 0.5  # Convert to categorical if unique ratio < 50%

# Census geography
FULL_BLOCK_GROUP_GEOID_LENGTH = 12  # 2 state + 3 county + 6 tract + 1 block group
