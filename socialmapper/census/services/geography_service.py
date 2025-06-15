"""
Geography Service for SocialMapper.

Handles state, county, and geographic unit operations including
FIPS code conversions, format detection, and geographic lookups.
"""

from enum import Enum
from typing import Dict, List, Optional, Union

from ..domain.entities import BlockGroupInfo, CountyInfo, StateInfo
from ..domain.interfaces import ConfigurationProvider, GeocodeProvider


class StateFormat(Enum):
    """Enumeration of different state formats."""
    NAME = "name"         # Full state name (e.g., "California")
    ABBREVIATION = "abbr" # Two-letter abbreviation (e.g., "CA")
    FIPS = "fips"        # FIPS code (e.g., "06")


class GeographyService:
    """Service for managing geographic information and conversions."""
    
    # State name to abbreviation mapping
    STATE_NAMES_TO_ABBR = {
        "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
        "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
        "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
        "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
        "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
        "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
        "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
        "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
        "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
        "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
        "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
        "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
        "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC",
    }
    
    # State abbreviation to FIPS code mapping
    STATE_ABBR_TO_FIPS = {
        "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08",
        "CT": "09", "DE": "10", "FL": "12", "GA": "13", "HI": "15", "ID": "16",
        "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21", "LA": "22",
        "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28",
        "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
        "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39", "OK": "40",
        "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46", "TN": "47",
        "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53", "WV": "54",
        "WI": "55", "WY": "56", "DC": "11",
    }
    
    def __init__(self, config: ConfigurationProvider, geocoder: Optional[GeocodeProvider] = None):
        self._config = config
        self._geocoder = geocoder
        
        # Generate inverse mappings
        self._abbr_to_name = {abbr: name for name, abbr in self.STATE_NAMES_TO_ABBR.items()}
        self._fips_to_abbr = {fips: abbr for abbr, fips in self.STATE_ABBR_TO_FIPS.items()}
        self._fips_to_name = {fips: self._abbr_to_name[abbr] for fips, abbr in self._fips_to_abbr.items()}
    
    def is_fips_code(self, code: Union[str, int]) -> bool:
        """
        Check if a string or number is a valid state FIPS code.
        
        Args:
            code: Potential FIPS code to check
            
        Returns:
            True if it is a valid state FIPS code, False otherwise
        """
        if isinstance(code, int):
            code = str(code).zfill(2)
        elif isinstance(code, str):
            code = code.zfill(2)
        else:
            return False
        
        return code in self._fips_to_abbr
    
    def detect_state_format(self, state: str) -> Optional[StateFormat]:
        """
        Detect the format of a state identifier.
        
        Args:
            state: State identifier (name, abbreviation, or FIPS code)
            
        Returns:
            StateFormat enum or None if format can't be determined
        """
        if not state:
            return None
        
        if isinstance(state, str):
            # Check if it's a 2-letter abbreviation
            if len(state) == 2 and state.upper() in self.STATE_ABBR_TO_FIPS:
                return StateFormat.ABBREVIATION
            
            # Check if it's a FIPS code
            if ((len(state) == 1 or len(state) == 2) and state.isdigit() 
                and state.zfill(2) in self._fips_to_abbr):
                return StateFormat.FIPS
            
            # Check if it's a state name
            if (state.title() in self.STATE_NAMES_TO_ABBR or 
                state.upper() in self.STATE_NAMES_TO_ABBR):
                return StateFormat.NAME
        
        # Handle numeric (possibly a FIPS code)
        if isinstance(state, (int, float)):
            state_str = str(int(state)).zfill(2)
            if state_str in self._fips_to_abbr:
                return StateFormat.FIPS
        
        return None
    
    def normalize_state(self, state: Union[str, int], 
                       to_format: StateFormat = StateFormat.ABBREVIATION) -> Optional[str]:
        """
        Convert a state identifier to the requested format.
        
        Args:
            state: State identifier (name, abbreviation, or FIPS code)
            to_format: Desired output format
            
        Returns:
            Normalized state identifier in the requested format or None if invalid
        """
        if state is None:
            return None
        
        # Detect input format
        state_format = self.detect_state_format(state)
        if state_format is None:
            return None
        
        state_str = str(state)
        
        # If already in desired format, just standardize and return
        if state_format == to_format:
            if state_format == StateFormat.ABBREVIATION:
                return state_str.upper()
            elif state_format == StateFormat.FIPS:
                return state_str.zfill(2)
            elif state_format == StateFormat.NAME:
                # Handle case variations
                for name in self.STATE_NAMES_TO_ABBR:
                    if name.lower() == state_str.lower():
                        return name
                return state_str
        
        # Convert from source format to abbreviation (intermediate step)
        abbr = None
        if state_format == StateFormat.NAME:
            for name, code in self.STATE_NAMES_TO_ABBR.items():
                if name.lower() == state_str.lower():
                    abbr = code
                    break
        elif state_format == StateFormat.FIPS:
            abbr = self._fips_to_abbr.get(state_str.zfill(2))
        else:  # ABBREVIATION
            abbr = state_str.upper()
        
        if not abbr:
            return None
        
        # Convert from abbreviation to target format
        if to_format == StateFormat.ABBREVIATION:
            return abbr
        elif to_format == StateFormat.FIPS:
            return self.STATE_ABBR_TO_FIPS.get(abbr)
        elif to_format == StateFormat.NAME:
            return self._abbr_to_name.get(abbr)
    
    def create_state_info(self, state: Union[str, int]) -> Optional[StateInfo]:
        """
        Create a StateInfo entity from any state identifier.
        
        Args:
            state: State identifier in any format
            
        Returns:
            StateInfo entity or None if invalid
        """
        fips = self.normalize_state(state, StateFormat.FIPS)
        abbr = self.normalize_state(state, StateFormat.ABBREVIATION)
        name = self.normalize_state(state, StateFormat.NAME)
        
        if not all([fips, abbr, name]):
            return None
        
        return StateInfo(fips=fips, abbreviation=abbr, name=name)
    
    def create_county_info(self, state_fips: str, county_fips: str, 
                          name: Optional[str] = None) -> CountyInfo:
        """
        Create a CountyInfo entity.
        
        Args:
            state_fips: State FIPS code
            county_fips: County FIPS code
            name: Optional county name
            
        Returns:
            CountyInfo entity
        """
        return CountyInfo(
            state_fips=state_fips.zfill(2),
            county_fips=county_fips.zfill(3),
            name=name
        )
    
    def create_block_group_info(self, state_fips: str, county_fips: str, 
                               tract: str, block_group: str) -> BlockGroupInfo:
        """
        Create a BlockGroupInfo entity.
        
        Args:
            state_fips: State FIPS code
            county_fips: County FIPS code  
            tract: Tract code
            block_group: Block group code
            
        Returns:
            BlockGroupInfo entity
        """
        return BlockGroupInfo(
            state_fips=state_fips.zfill(2),
            county_fips=county_fips.zfill(3),
            tract=tract.zfill(6),
            block_group=block_group
        )
    
    def get_all_states(self, format: StateFormat = StateFormat.ABBREVIATION) -> List[str]:
        """
        Get a list of all US states in the requested format.
        
        Args:
            format: Format for the returned state list
            
        Returns:
            List of all state identifiers in the requested format
        """
        if format == StateFormat.ABBREVIATION:
            return sorted(self.STATE_ABBR_TO_FIPS.keys())
        elif format == StateFormat.FIPS:
            return sorted(self._fips_to_abbr.keys())
        elif format == StateFormat.NAME:
            return sorted(self.STATE_NAMES_TO_ABBR.keys())
    
    def normalize_state_list(self, states: List[Union[str, int]], 
                           to_format: StateFormat = StateFormat.ABBREVIATION) -> List[str]:
        """
        Normalize a list of state identifiers to a consistent format.
        
        Args:
            states: List of state identifiers (can be mixed formats)
            to_format: Desired output format
            
        Returns:
            List of normalized state identifiers (invalid entries removed)
        """
        normalized = []
        for state in states:
            norm_state = self.normalize_state(state, to_format=to_format)
            if norm_state and norm_state not in normalized:
                normalized.append(norm_state)
        return normalized
    
    def is_valid_state(self, state: Union[str, int]) -> bool:
        """
        Check if a string is a valid state identifier in any format.
        
        Args:
            state: State identifier to validate
            
        Returns:
            True if valid state identifier, False otherwise
        """
        return self.detect_state_format(state) is not None
    
    def get_geography_from_point(self, lat: float, lon: float) -> Optional[Dict[str, Optional[str]]]:
        """
        Get geographic identifiers for a point using the geocoder.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with geographic identifiers or None
        """
        if not self._geocoder:
            return None
        
        try:
            result = self._geocoder.geocode_point(lat, lon)
            if result and result.state_fips:
                return {
                    "state_fips": result.state_fips,
                    "county_fips": result.county_fips,
                    "tract_geoid": result.tract_geoid,
                    "block_group_geoid": result.block_group_geoid,
                    "zcta_geoid": result.zcta_geoid,
                }
        except Exception:
            pass
        
        return None 