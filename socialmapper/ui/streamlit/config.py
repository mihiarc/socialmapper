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
# Based on OpenStreetMap tagging standards: https://wiki.openstreetmap.org/wiki/Map_features
POI_TYPES = {
    "amenity": [
        "library",           # amenity=library - public libraries
        "school",            # amenity=school - primary/secondary schools (ages ~6-18)
        "hospital",          # amenity=hospital - facilities with inpatient care
        "community_centre",  # amenity=community_centre - public community facilities
        "pharmacy",          # amenity=pharmacy - shops dispensing medications
        "clinic",            # amenity=clinic - medical facilities without inpatient care
        "doctors",           # amenity=doctors - doctor's offices
        "university",        # amenity=university - higher education institutions
        "kindergarten",      # amenity=kindergarten - pre-school education
        "bank",              # amenity=bank - financial institutions
        "post_office",       # amenity=post_office - postal services
        "police",            # amenity=police - police stations
        "fire_station",      # amenity=fire_station - fire departments
        "parking"            # amenity=parking - parking facilities (for park_and_ride)
    ],
    "shop": [
        "supermarket",       # shop=supermarket - large grocery stores with full service
        "convenience",       # shop=convenience - small stores, limited hours/selection
        "mall",              # shop=mall - indoor shopping centers
        "grocery",           # shop=grocery - traditional/specialized grocery stores
        "department_store",  # shop=department_store - large stores with many departments
        "bakery",            # shop=bakery - shops selling bread and cakes
        "butcher"            # shop=butcher - shops selling meat
    ],
    "leisure": [
        "park",              # leisure=park - municipal parks (NOT amenity=park which is deprecated)
        "playground",        # leisure=playground - children's play areas
        "sports_centre",     # leisure=sports_centre - indoor sports facilities
        "swimming_pool",     # leisure=swimming_pool - swimming facilities
        "fitness_centre",    # leisure=fitness_centre - gyms and fitness facilities
        "stadium",           # leisure=stadium - large sports venues
        "garden"             # leisure=garden - botanical/ornamental gardens
    ],
    "public_transport": [
        "station",           # public_transport=station - train/metro stations
        "stop_position",     # public_transport=stop_position - bus/tram stops
        "platform"           # public_transport=platform - boarding platforms
    ],
    "railway": [
        "station",           # railway=station - train stations
        "halt",              # railway=halt - small train stops
        "tram_stop"          # railway=tram_stop - tram/light rail stops
    ]
    # Note: 'healthcare' and 'education' are not primary OSM keys
    # Healthcare facilities use amenity=hospital/clinic/doctors/pharmacy
    # Education facilities use amenity=school/university/kindergarten
    # Transit stations can be tagged as public_transport=station or railway=station
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
        "poi_types": [
            ("amenity", "library"),
            ("amenity", "hospital"),
            ("amenity", "school"),
            ("leisure", "park")  # Corrected from amenity to leisure
        ],
        "census_vars": ["B01003_001E", "B19013_001E", "B17001_002E"],
        "travel_time": 15
    },
    "Healthcare Access": {
        "description": "Evaluate access to healthcare facilities",
        "poi_types": [
            ("amenity", "hospital"),
            ("amenity", "clinic"),
            ("amenity", "doctors"),
            ("amenity", "pharmacy")
        ],
        "census_vars": ["B01003_001E", "B19013_001E", "B17001_002E"],
        "travel_time": 15
    },
    "Site Selection": {
        "description": "Evaluate potential locations for new facilities",
        "poi_types": [
            ("shop", "supermarket"),
            ("amenity", "pharmacy"),
            ("amenity", "bank")
        ],
        "census_vars": ["B01003_001E", "B19013_001E", "B25077_001E"],
        "travel_time": 10
    },
    "Transportation Planning": {
        "description": "Assess multi-modal accessibility to transit",
        "poi_types": [
            ("public_transport", "station"),
            ("railway", "station"),
            ("amenity", "parking")  # For park-and-ride facilities
        ],
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
