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