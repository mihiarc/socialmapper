"""SocialMapper Tutorial Pages

This module contains the 5 core tutorial pages that mirror the documentation examples.
Each page provides an interactive version of the corresponding tutorial from the [online documentation](https://mihiarc.github.io/socialmapper/tutorials/).
"""

from .address_geocoding import render_address_geocoding_page
from .custom_pois import render_custom_pois_page
from .getting_started import render_getting_started_page
from .travel_modes import render_travel_modes_page
from .zcta_analysis import render_zcta_analysis_page

# Tutorial pages that mirror documentation examples
__all__ = [
    "render_address_geocoding_page",
    "render_custom_pois_page", 
    "render_getting_started_page",
    "render_travel_modes_page",
    "render_zcta_analysis_page",
]
