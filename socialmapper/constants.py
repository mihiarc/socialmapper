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
VALID_EXPORT_FORMATS = ["png", "pdf", "svg", "geojson", "shapefile", "html"]
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
COORDINATE_PAIR_LENGTH = 2  # Expected length of (lat, lon) coordinate tuples

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
CRS_WGS84_EPSG = 4326  # WGS84 EPSG code as integer
CRS_CONUS_ALBERS = "EPSG:5070"  # NAD83 / Conus Albers - optimized for CONUS (~0.1% accuracy)
CRS_GLOBAL_EQUAL_AREA = "EPSG:6933"  # NSIDC EASE-Grid 2.0 - global equal-area (~1-2% accuracy)

# ==========================================
# Visualization Constants
# ==========================================
SCALE_BAR_ROUND_THRESHOLD = 0.1  # Threshold for rounding scale bar length
METERS_PER_KM = 1000  # Meters per kilometer

# Choropleth map defaults
DEFAULT_BASEMAP = "CartoDB.Voyager"  # Clean, light basemap for choropleths
DEFAULT_CHOROPLETH_CMAP = "YlGnBu"  # Blue-green gradient for sequential data
DEFAULT_DIVERGING_CMAP = "RdBu_r"  # Red-blue for diverging data
DEFAULT_CATEGORICAL_CMAP = "Set2"  # Richer saturation for categorical data
MAP_FIGURE_SIZE = (14, 12)  # Width, height in inches
MAP_DPI = 200  # Output resolution
MAP_FACECOLOR = "#fafafa"  # Subtle off-white figure background
CHOROPLETH_EDGE_COLOR = "#cccccc"  # Soft gray boundary lines
CHOROPLETH_EDGE_WIDTH = 0.4  # Line width for polygon edges
CHOROPLETH_ALPHA = 0.85  # Transparency for choropleth layer
BASEMAP_ALPHA = 0.5  # Transparency for basemap (so choropleth shows through)

# Title styling
TITLE_FONTSIZE = 18  # Larger title for impact
TITLE_COLOR = "#1a1a2e"  # Dark navy for titles

# Overlay styling
OVERLAY_BOUNDARY_COLOR = "#d63384"  # Modern magenta-pink for boundary overlays
OVERLAY_BOUNDARY_WIDTH = 3  # Line width for overlay boundaries
OVERLAY_BOUNDARY_STYLE = "--"  # Dashed line style
OVERLAY_POINT_COLOR = "#d63384"  # Magenta-pink for point markers
OVERLAY_POINT_SIZE = 150  # Marker size for overlay points
OVERLAY_POINT_EDGE_COLOR = "white"  # White edge around markers
OVERLAY_POINT_EDGE_WIDTH = 2  # Edge width for markers

# Point label styling
LABEL_BG_COLOR = "white"  # Background color for label halo
LABEL_BG_ALPHA = 0.8  # Transparency for label background
LABEL_EDGE_COLOR = "none"  # No border on label box
LABEL_FONTSIZE = 9  # Font size for point labels
LABEL_PAD = 0.3  # Padding inside label box

# Stats box styling
STATS_BOX_ALPHA = 0.95  # Background opacity
STATS_BOX_FONTSIZE = 11  # Font size for stats text
STATS_BOX_FONT_FAMILY = "sans-serif"  # Clean sans-serif font
STATS_BOX_BORDER_COLOR = "#d0d0d0"  # Lighter border

# North arrow / scale bar styling
MAP_ACCENT_COLOR = "#333333"  # Dark gray for decorations (arrows, scale bar)
NORTH_ARROW_FONTSIZE = 12  # Slightly smaller north arrow label
NORTH_ARROW_LINE_WIDTH = 1.5  # Thinner arrow line
SCALE_BAR_LINE_WIDTH = 2  # Thinner scale bar line

# Web Mercator CRS for basemap compatibility
CRS_WEB_MERCATOR = "EPSG:3857"
CRS_WEB_MERCATOR_EPSG = 3857

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

# ==========================================
# HTTP Status Codes
# ==========================================
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_RATE_LIMITED = 429
HTTP_SERVER_ERROR = 500

# ==========================================
# Network Validation Thresholds
# ==========================================
MIN_NETWORK_NODES = 100  # Minimum nodes for a valid network graph
MIN_TRAVEL_TIME_FOR_NETWORK_VALIDATION = 15  # Minutes - validate networks for longer trips
MIN_ISOCHRONE_AREA_KM2 = 100  # Minimum expected isochrone area in km²

# ==========================================
# Tutorial Configuration
# ==========================================
TUTORIAL_MAX_TRAVEL_TIME = 60  # Maximum travel time for tutorial examples

# ==========================================
# String/Format Validation
# ==========================================
US_STATE_ABBREV_LENGTH = 2  # Length of US state abbreviations (e.g., "CA", "NY")
MIN_INDEX_TUPLE_ELEMENTS = 2  # Minimum elements in OSMnx multi-index tuples

# ==========================================
# Processing Thresholds
# ==========================================
MIN_CLUSTERING_POI_COUNT = 5  # Minimum POIs to enable clustering
MIN_CONCURRENT_POI_COUNT = 3  # Minimum POIs to enable concurrent processing
MIN_POLYGON_POINTS = 3  # Minimum points to create a polygon

# ==========================================
# Geographic Boundaries
# ==========================================
US_CANADA_BORDER_LAT = 49.0  # 49th parallel - US-Canada border

# ==========================================
# Speed Limits (km/h)
# ==========================================
MAX_WALKING_SPEED_KPH = 7.0  # Maximum realistic walking speed
NORMAL_WALKING_SPEED_KPH = 5.0  # Normal walking speed
MAX_CYCLING_SPEED_KPH = 30.0  # Maximum realistic cycling speed
NORMAL_CYCLING_SPEED_KPH = 15.0  # Normal cycling speed

# ==========================================
# Cluster Analysis
# ==========================================
RURAL_CLUSTER_SPAN_KM = 50  # Cluster span threshold for rural areas
SUBURBAN_CLUSTER_SPAN_KM = 20  # Cluster span threshold for suburban areas

# ==========================================
# Efficiency Ratings
# ==========================================
EFFICIENCY_EXCELLENT_THRESHOLD = 50  # Time savings % for "Excellent" rating
EFFICIENCY_GOOD_THRESHOLD = 25  # Time savings % for "Good" rating
