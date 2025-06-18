"""Configuration settings for the Streamlit application."""



# Page configuration
PAGE_CONFIG = {
    "page_title": "SocialMapper Dashboard",
    "page_icon": "🗺️",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Available pages in the application
PAGES = [
    "Getting Started",
    "Custom POIs",
    "Travel Modes",
    "ZCTA Analysis",
    "Address Geocoding",
    "Batch Analysis",
    "Settings"
]

# Census variables with human-readable names
CENSUS_VARIABLES = {
    "B01003_001E": "Total Population",
    "B19013_001E": "Median Household Income",
    "B25077_001E": "Median Home Value",
    "B15003_022E": "Bachelor's Degree Holders",
    "B08301_021E": "Public Transit Users",
    "B17001_002E": "Population in Poverty"
}

# Default census variables for quick analysis
DEFAULT_CENSUS_VARS = ["B01003_001E", "B19013_001E", "B25077_001E"]

# POI type options
POI_TYPES = {
    "amenity": ["library", "school", "hospital", "community_centre", "park"],
    "shop": ["supermarket", "convenience", "mall"],
    "leisure": ["park", "playground", "sports_centre"],
    "healthcare": ["hospital", "clinic", "pharmacy"],
    "education": ["school", "university", "kindergarten"]
}

# Travel mode configurations
TRAVEL_MODES = {
    "walk": {"name": "Walking", "icon": "🚶", "color": "#ff7f00"},
    "bike": {"name": "Biking", "icon": "🚴", "color": "#4daf4a"},
    "drive": {"name": "Driving", "icon": "🚗", "color": "#377eb8"}
}

# Map visualization defaults
MAP_DEFAULTS = {
    "zoom_start": 13,
    "center_us": (39.8283, -98.5795),  # Geographic center of US
    "isochrone_style": {
        'fillColor': '#3388ff',
        'color': '#3388ff',
        'weight': 2,
        'fillOpacity': 0.3
    }
}

# File upload configurations
FILE_UPLOAD_CONFIG = {
    "csv": {
        "type": ["csv"],
        "help": "Upload a CSV file with columns: name, lat, lon",
        "max_size_mb": 10
    }
}

# Analysis templates for batch processing
ANALYSIS_TEMPLATES = {
    "Equity Assessment": {
        "description": "Analyze equitable access to essential services",
        "poi_types": ["library", "hospital", "school", "park"],
        "census_vars": ["B01003_001E", "B19013_001E", "B17001_002E"],
        "travel_time": 15
    },
    "Site Selection": {
        "description": "Evaluate potential locations for new facilities",
        "poi_types": ["supermarket", "pharmacy", "bank"],
        "census_vars": ["B01003_001E", "B19013_001E", "B25077_001E"],
        "travel_time": 10
    },
    "Transportation Planning": {
        "description": "Assess multi-modal accessibility",
        "poi_types": ["transit_station", "park_and_ride"],
        "census_vars": ["B08301_021E", "B08301_001E"],
        "travel_time": 20
    }
}

# Export formats
EXPORT_FORMATS = {
    "csv": "Comma-separated values",
    "parquet": "Apache Parquet (efficient storage)",
    "geojson": "Geographic JSON",
    "excel": "Microsoft Excel"
}

# Performance settings
PERFORMANCE_CONFIG = {
    "max_concurrent_requests": 5,
    "cache_ttl_minutes": 60,
    "default_timeout_seconds": 30
}
