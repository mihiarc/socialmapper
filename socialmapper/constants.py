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

# ==========================================
# HTTP Timeout Constants (seconds)
# ==========================================
DEFAULT_HTTP_TIMEOUT = 30  # Default for most API calls
GEOCODING_TIMEOUT = 10  # For geocoding requests (quick responses expected)
OSM_TIMEOUT = 180  # For OSMnx/Overpass requests (large data, slow)
CENSUS_API_TIMEOUT = 30  # For Census API requests
SECURITY_TIMEOUT = 5  # For key manager operations

# ==========================================
# CONUS Bounds (Contiguous United States)
# Used for selecting appropriate equal-area projection
# ==========================================
CONUS_MIN_LAT = 24.0  # Southern tip of Florida Keys
CONUS_MAX_LAT = 50.0  # Northern border with Canada
CONUS_MIN_LON = -125.0  # West coast of Washington state
CONUS_MAX_LON = -66.0  # Eastern tip of Maine

# ==========================================
# Coordinate Reference Systems (CRS)
# ==========================================
CRS_WGS84 = "EPSG:4326"  # Standard lat/lon coordinates
CRS_CONUS_ALBERS = "EPSG:5070"  # NAD83 / Conus Albers - optimized for CONUS (~0.1% accuracy)
CRS_GLOBAL_EQUAL_AREA = "EPSG:6933"  # NSIDC EASE-Grid 2.0 - global equal-area (~1-2% accuracy)

# ==========================================
# API Base URLs
# ==========================================
NOMINATIM_API_URL = "https://nominatim.openstreetmap.org/search"
CENSUS_GEOCODER_BASE_URL = "https://geocoding.geo.census.gov/geocoder"
CENSUS_GEOCODER_LOCATIONS_URL = f"{CENSUS_GEOCODER_BASE_URL}/locations/onelineaddress"
CENSUS_GEOCODER_GEOGRAPHIES_URL = f"{CENSUS_GEOCODER_BASE_URL}/geographies/coordinates"
CENSUS_API_BASE_URL = "https://api.census.gov/data"
CENSUS_KEY_SIGNUP_URL = "https://api.census.gov/data/key_signup.html"

# ==========================================
# Rate Limiting
# ==========================================
DEFAULT_RATE_LIMIT_RPS = 1.0  # Default requests per second
NOMINATIM_RATE_LIMIT_RPS = 1.0  # Nominatim policy: max 1 request/second
CENSUS_RATE_LIMIT_RPS = 10.0  # Census API is more generous

# ==========================================
# User Agent String
# ==========================================
USER_AGENT = "SocialMapper/2.0 (https://github.com/socialmapper)"

# ==========================================
# Retry Configuration
# ==========================================
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BACKOFF = 0.5  # seconds
DEFAULT_RETRY_BACKOFF_EXPONENTIAL = 2.0  # base delay for exponential backoff
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]
NETWORK_MAX_RETRIES = 2  # Max retries for network downloads (isochrone)

# ==========================================
# Batch Processing
# ==========================================
CENSUS_BATCH_SIZE = 10  # Number of tracts to process per batch
CENSUS_BATCH_DELAY = 0.1  # Delay between batches in seconds

# ==========================================
# Overpass API Configuration
# ==========================================
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]
OVERPASS_PRIMARY_ENDPOINT = OVERPASS_ENDPOINTS[0]
OVERPASS_TIMEOUT = 30  # Timeout for individual Overpass requests (not OSMnx)
