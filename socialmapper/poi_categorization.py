#!/usr/bin/env python3
"""POI categorization module for classifying OpenStreetMap Points of Interest.

This module provides functionality to categorize POIs based on their OSM tags
into predefined categories like food_and_drink, shopping, education, etc.
"""

from typing import Any

# Comprehensive POI category mapping
# Maps category names to lists of OSM tag values
POI_CATEGORY_MAPPING = {
    "food_and_drink": [
        # Amenity tags
        "restaurant",
        "cafe",
        "bar",
        "fast_food",
        "pub",
        "food_court",
        "ice_cream",
        "biergarten",
        "nightclub",
        "wine_bar",
        "brewery",
        "distillery",
        "winery",
        "beer_garden",
        "coffee_shop",
        # Shop tags
        "bakery",
        "pastry",
        "confectionery",
        "deli",
        "beverages",
        "alcohol",
        "wine",
        "coffee",
        "tea",
        "butcher",
        "seafood",
        "cheese",
        "chocolate",
        "dairy",
        "frozen_food",
        "organic",
        # Cuisine/food related
        "bbq",
        "pizza",
        "burger",
        "sandwich",
        "juice_bar",
        "food_truck",
    ],
    "shopping": [
        # General shopping
        "shop",
        "mall",
        "supermarket",
        "convenience",
        "department_store",
        "marketplace",
        "general",
        "variety_store",
        "wholesale",
        # Specific shop types
        "clothes",
        "fashion",
        "shoes",
        "jewelry",
        "boutique",
        "fabric",
        "leather",
        "tailor",
        "fashion_accessories",
        "bag",
        "watches",
        # Electronics and appliances
        "electronics",
        "computer",
        "mobile_phone",
        "appliance",
        "hifi",
        "camera",
        "photo",
        "video",
        "video_games",
        # Home and garden
        "furniture",
        "interior_decoration",
        "household",
        "houseware",
        "doityourself",
        "hardware",
        "trade",
        "garden_centre",
        "florist",
        # Other retail
        "books",
        "stationery",
        "gift",
        "toys",
        "sports",
        "outdoor",
        "bicycle",
        "car",
        "car_parts",
        "motorcycle",
        "tyres",
        "newsagent",
        "kiosk",
        "tobacco",
        "e-cigarette",
        "lottery",
        "ticket",
        "music",
        "musical_instrument",
        "art",
        "craft",
        "frame",
        "trophy",
        "collector",
        "games",
        "model",
        "anime",
        "beauty",
        "cosmetics",
        "perfumery",
        "hairdresser",
        "massage",
        "tattoo",
        "piercing",
        "erotic",
        "hearing_aids",
        "optician",
        "medical_supply",
        "nutrition_supplements",
        "herbalist",
    ],
    "education": [
        # Educational institutions
        "school",
        "university",
        "college",
        "library",
        "kindergarten",
        "preschool",
        "childcare",
        "language_school",
        "driving_school",
        "music_school",
        "dance_school",
        "research_institute",
        "training",
        "education_centre",
        "academy",
        "seminary",
        # Related amenities
        "community_centre",
        "conference_centre",
        "events_venue",
        "exhibition_centre",
        "arts_centre",
    ],
    "healthcare": [
        # Medical facilities
        "hospital",
        "clinic",
        "pharmacy",
        "dentist",
        "doctors",
        "veterinary",
        "nursing_home",
        "social_facility",
        "healthcare",
        "health_centre",
        "medical_centre",
        "blood_bank",
        "laboratory",
        # Specialized healthcare
        "optometry",
        "physiotherapy",
        "psychotherapist",
        "audiologist",
        "speech_therapist",
        "occupational_therapist",
        "alternative",
        "acupuncture",
        "chiropractor",
        "homeopath",
        "midwife",
        "counselling",
        "hospice",
        "ambulance_station",
    ],
    "transportation": [
        # Public transport
        "bus_station",
        "subway_station",
        "train_station",
        "tram_stop",
        "ferry_terminal",
        "taxi",
        "airport",
        "helipad",
        # Private transport
        "parking",
        "parking_garage",
        "parking_space",
        "bicycle_parking",
        "motorcycle_parking",
        "car_sharing",
        "car_rental",
        "boat_rental",
        "bicycle_rental",
        "bicycle_repair_station",
        # Fuel and charging
        "fuel",
        "charging_station",
        "gas",
        "diesel",
        "lpg",
        "cng",
        "electric_vehicle_charging",
    ],
    "recreation": [
        # Parks and outdoor
        "park",
        "playground",
        "sports_centre",
        "stadium",
        "pitch",
        "golf_course",
        "miniature_golf",
        "swimming_pool",
        "water_park",
        "beach",
        "marina",
        "slipway",
        "fishing",
        "picnic_site",
        "viewpoint",
        "garden",
        "nature_reserve",
        "wilderness_hut",
        # Indoor recreation
        "cinema",
        "theatre",
        "casino",
        "gambling",
        "amusement_arcade",
        "adult_gaming_centre",
        "escape_game",
        "bowling_alley",
        "billiards",
        "darts",
        "paintball",
        "laser_tag",
        # Fitness and sports
        "fitness_centre",
        "gym",
        "yoga",
        "dance",
        "martial_arts",
        "climbing",
        "horse_riding",
        "ice_rink",
        "tennis",
        "squash",
        "badminton",
        "basketball",
        "volleyball",
        "table_tennis",
        # Cultural
        "museum",
        "gallery",
        "exhibition",
        "zoo",
        "aquarium",
        "theme_park",
        "attraction",
        "tourism",
    ],
    "services": [
        # Financial
        "bank",
        "atm",
        "bureau_de_change",
        "money_transfer",
        "payment_terminal",
        "financial",
        "insurance",
        "accountant",
        # Government
        "post_office",
        "government",
        "townhall",
        "courthouse",
        "police",
        "fire_station",
        "embassy",
        "tax_office",
        "customs",
        "immigration",
        "prison",
        "register_office",
        # Professional services
        "lawyer",
        "notary",
        "estate_agent",
        "employment_agency",
        "advertising_agency",
        "architect",
        "surveyor",
        "engineer",
        "it",
        "company",
        "office",
        "coworking_space",
        # Personal services
        "laundry",
        "dry_cleaning",
        "car_wash",
        "car_repair",
        "beauty_salon",
        "nail_salon",
        "spa",
        "sauna",
        "solarium",
        "shoe_repair",
        "tailor",
        "photo_booth",
        "copyshop",
        "printing",
        "funeral_directors",
        "crematorium",
        "cemetery",
    ],
    "accommodation": [
        # Lodging
        "hotel",
        "motel",
        "hostel",
        "guest_house",
        "bed_and_breakfast",
        "apartment",
        "chalet",
        "alpine_hut",
        "camp_site",
        "caravan_site",
        "resort",
        "spa_resort",
        "love_hotel",
        "shelter",
    ],
    "religious": [
        # Places of worship
        "place_of_worship",
        "church",
        "mosque",
        "temple",
        "synagogue",
        "chapel",
        "cathedral",
        "basilica",
        "minster",
        "monastery",
        "convent",
        "shrine",
        "wayside_shrine",
        "wayside_cross",
        "holy_well",
        "prayer_room",
        "religious_administrative_centre",
    ],
    "utilities": [
        # Basic utilities
        "toilets",
        "shower",
        "drinking_water",
        "water_point",
        "waste_basket",
        "waste_disposal",
        "recycling",
        "telephone",
        "emergency_phone",
        "clock",
        "post_box",
        "parcel_locker",
        "vending_machine",
        "atm",
        "photo_booth",
        "booth",
        "compressed_air",
        "water_fountain",
    ],
}

# Mapping of OSM keys to check for categorization
# This helps optimize the categorization process
OSM_KEY_PRIORITY = [
    "amenity",
    "shop",
    "leisure",
    "tourism",
    "office",
    "healthcare",
    "education",
    "place_of_worship",
    "public_transport",
    "highway",
    "railway",
    "aeroway",
    "natural",
    "landuse",
    "building",
]


def categorize_poi(poi_tags: dict[str, Any]) -> str:
    """Categorize a POI based on its OSM tags.

    Args:
        poi_tags: Dictionary of OSM tags for the POI

    Returns:
        Category string (e.g., "food_and_drink", "shopping") or "other" if no match

    Example:
        >>> categorize_poi({"amenity": "restaurant"})
        'food_and_drink'
        >>> categorize_poi({"shop": "supermarket"})
        'shopping'
        >>> categorize_poi({"unknown": "value"})
        'other'
    """
    if not poi_tags or not isinstance(poi_tags, dict):
        return "other"

    # Check each OSM key in priority order
    for osm_key in OSM_KEY_PRIORITY:
        if osm_key in poi_tags:
            tag_value = poi_tags[osm_key]

            # Convert to string and lowercase for comparison
            tag_value_str = str(tag_value).lower()

            # Check each category's values
            for category, values in POI_CATEGORY_MAPPING.items():
                if tag_value_str in [v.lower() for v in values]:
                    return category

    # Special case: check for specific tag combinations
    # For example, building=church should be categorized as religious
    if poi_tags.get("building") == "church":
        return "religious"

    # Check name field for hints (fallback)
    name = poi_tags.get("name", "").lower()
    if name:
        for category, values in POI_CATEGORY_MAPPING.items():
            for value in values:
                if value.lower() in name:
                    return category

    return "other"


def organize_pois_by_category(pois: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Organize a list of POIs by their categories.

    Args:
        pois: List of POI dictionaries, each containing a 'tags' field

    Returns:
        Dictionary mapping category names to lists of POIs in that category

    Example:
        >>> pois = [
        ...     {"id": 1, "tags": {"amenity": "restaurant"}},
        ...     {"id": 2, "tags": {"shop": "supermarket"}},
        ...     {"id": 3, "tags": {"amenity": "hospital"}},
        ... ]
        >>> result = organize_pois_by_category(pois)
        >>> list(result.keys())
        ['food_and_drink', 'shopping', 'healthcare']
    """
    categorized_pois: dict[str, list[dict[str, Any]]] = {}

    for poi in pois:
        # Extract tags from POI
        tags = poi.get("tags", {})

        # Categorize the POI
        category = categorize_poi(tags)

        # Add to appropriate category list
        if category not in categorized_pois:
            categorized_pois[category] = []

        categorized_pois[category].append(poi)

    return categorized_pois


def get_poi_category_info() -> dict[str, Any]:
    """Get information about available POI categories.

    Returns:
        Dictionary containing category mapping and statistics
    """
    info = {
        "categories": list(POI_CATEGORY_MAPPING.keys()),
        "total_categories": len(POI_CATEGORY_MAPPING),
        "category_details": {},
    }

    for category, values in POI_CATEGORY_MAPPING.items():
        info["category_details"][category] = {
            "value_count": len(values),
            "sample_values": values[:5],  # First 5 as examples
        }

    return info


def is_valid_category(category: str) -> bool:
    """Check if a category name is valid.

    Args:
        category: Category name to validate

    Returns:
        True if the category exists in POI_CATEGORY_MAPPING, False otherwise
    """
    return category in POI_CATEGORY_MAPPING


def get_category_values(category: str) -> list[str] | None:
    """Get all OSM tag values for a specific category.

    Args:
        category: Category name

    Returns:
        List of OSM tag values for the category, or None if category is invalid
    """
    if not is_valid_category(category):
        return None

    return POI_CATEGORY_MAPPING[category].copy()


def add_category_value(category: str, value: str) -> bool:
    """Add a new value to an existing category (for extensibility).

    Args:
        category: Category name
        value: OSM tag value to add

    Returns:
        True if successfully added, False if category doesn't exist
    """
    if not is_valid_category(category):
        return False

    if value not in POI_CATEGORY_MAPPING[category]:
        POI_CATEGORY_MAPPING[category].append(value)

    return True


def create_custom_category(category_name: str, values: list[str]) -> bool:
    """Create a new custom category (for extensibility).

    Args:
        category_name: Name for the new category
        values: List of OSM tag values for the category

    Returns:
        True if successfully created, False if category already exists
    """
    if category_name in POI_CATEGORY_MAPPING:
        return False

    POI_CATEGORY_MAPPING[category_name] = values.copy()
    return True
