"""
Census Variable Service for SocialMapper.

Handles census variable mapping, validation, and conversion between
human-readable names and census codes.
"""

from typing import Dict, List, Optional, Union
from enum import Enum

from ..domain.entities import CensusVariable
from ..domain.interfaces import ConfigurationProvider


class VariableFormat(Enum):
    """Enumeration of census variable formats."""
    CODE = "code"  # Census code (e.g., "B01003_001E")
    NAME = "name"  # Human-readable name (e.g., "total_population")


class CensusVariableService:
    """Service for managing census variables and their mappings."""
    
    # Standard census variable mappings
    # Can be a single code string or a list of codes for calculated variables
    VARIABLE_MAPPING: Dict[str, Union[str, List[str]]] = {
        "population": "B01003_001E",
        "total_population": "B01003_001E",
        "median_income": "B19013_001E",
        "median_household_income": "B19013_001E",
        "median_age": "B01002_001E",
        "households": "B11001_001E",
        "housing_units": "B25001_001E",
        "median_home_value": "B25077_001E",
        "white_population": "B02001_002E",
        "black_population": "B02001_003E",
        "hispanic_population": "B03003_003E",
        "education_bachelors_plus": "B15003_022E",
        "percent_poverty": "B17001_002E",
        # Calculated variable: sum of owner and renter occupied households with no vehicle
        "percent_without_vehicle": ["B25044_003E", "B25044_010E"],
        "households_no_vehicle": ["B25044_003E", "B25044_010E"],
    }
    
    # Variable-specific color schemes for visualization
    VARIABLE_COLORMAPS = {
        "B01003_001E": "viridis",  # Population - blues/greens
        "B19013_001E": "plasma",   # Income - yellows/purples
        "B25077_001E": "inferno",  # Home value - oranges/reds
        "B01002_001E": "cividis",  # Age - yellows/blues
        "B02001_002E": "Blues",    # White population
        "B02001_003E": "Purples",  # Black population
        "B03003_003E": "Oranges",  # Hispanic population
        "B15003_022E": "Greens",   # Education (Bachelor's or higher)
        "B17001_002E": "Reds",     # Poverty
        "B25044_003E": "YlOrRd",   # No vehicle available (owner occupied)
        "B25044_010E": "YlOrRd",   # No vehicle available (renter occupied)
    }
    
    def __init__(self, config: ConfigurationProvider):
        self._config = config
        
        # Create reverse mapping (only for simple variables, not calculated ones)
        self._code_to_name = {}
        for name, code in self.VARIABLE_MAPPING.items():
            if isinstance(code, str):
                self._code_to_name[code] = name
    
    def is_calculated_variable(self, variable: str) -> bool:
        """
        Check if a variable is calculated (composed of multiple census codes).
        
        Args:
            variable: Variable name
            
        Returns:
            True if it's a calculated variable
        """
        mapping = self.VARIABLE_MAPPING.get(variable.lower())
        return isinstance(mapping, list)
    
    def get_component_variables(self, variable: str) -> List[str]:
        """
        Get the component variables for a calculated variable.
        
        Args:
            variable: Variable name
            
        Returns:
            List of census codes that make up this variable
        """
        mapping = self.VARIABLE_MAPPING.get(variable.lower())
        if isinstance(mapping, list):
            return mapping
        elif isinstance(mapping, str):
            return [mapping]
        else:
            # If not found, assume it's a direct census code
            return [variable]
    
    def normalize_variable(self, variable: str) -> Union[str, List[str]]:
        """
        Normalize a census variable to its code form.
        
        Args:
            variable: Census variable code or human-readable name
            
        Returns:
            Census variable code(s) - string for simple variables, list for calculated ones
        """
        # If it's already a code with format like 'BXXXXX_XXXE', return as is
        if self._is_census_code(variable):
            return variable
        
        # Check if it's a known human-readable name
        code = self.VARIABLE_MAPPING.get(variable.lower())
        if code:
            return code
        
        # If not recognized, return as is (could be a custom variable)
        return variable
    
    def code_to_name(self, census_code: str) -> str:
        """
        Convert a census variable code to its human-readable name.
        
        Args:
            census_code: Census variable code (e.g., "B01003_001E")
            
        Returns:
            Human-readable name or the original code if not found
        """
        return self._code_to_name.get(census_code, census_code)
    
    def name_to_code(self, name: str) -> str:
        """
        Convert a human-readable name to its census variable code.
        
        Args:
            name: Human-readable name (e.g., "total_population")
            
        Returns:
            Census variable code or the original name if not found
        """
        return self.VARIABLE_MAPPING.get(name.lower(), name)
    
    def get_readable_variable(self, variable: str) -> str:
        """
        Get a human-readable representation of a census variable (with code).
        
        Args:
            variable: Census variable code or name
            
        Returns:
            Human-readable string like "Total Population (B01003_001E)"
        """
        # Check if it's a known human-readable name
        if variable.lower() in self.VARIABLE_MAPPING:
            # Format name for display (convert snake_case to Title Case)
            readable_name = variable.replace("_", " ").title()
            mapping = self.VARIABLE_MAPPING[variable.lower()]
            if isinstance(mapping, list):
                # For calculated variables, show the components
                codes = "+".join(mapping)
                return f"{readable_name} ({codes})"
            else:
                return f"{readable_name} ({mapping})"
        
        # If it's already a code, try to find its name
        if self._is_census_code(variable):
            name = self.code_to_name(variable)
            if name != variable:
                # Format name for display (convert snake_case to Title Case)
                readable_name = name.replace("_", " ").title()
                return f"{readable_name} ({variable})"
        
        # If no human-readable name found, return as is
        return variable
    
    def get_readable_variables(self, variables: List[str]) -> List[str]:
        """
        Get human-readable representations for a list of census variables.
        
        Args:
            variables: List of census variable codes
            
        Returns:
            List of human-readable strings with codes
        """
        return [self.get_readable_variable(var) for var in variables]
    
    def validate_variable(self, variable: str) -> bool:
        """
        Validate a census variable code format.
        
        Args:
            variable: Census variable code to validate
            
        Returns:
            True if valid format, False otherwise
        """
        # Census variable pattern: Letter followed by digits, underscore, digits, and letter
        # Example: B01003_001E
        if self._is_census_code(variable):
            return True
        
        # Check if it's a known human-readable name
        return variable.lower() in self.VARIABLE_MAPPING
    
    def get_colormap(self, variable: str) -> str:
        """
        Get the recommended colormap for a census variable.
        
        Args:
            variable: Census variable code
            
        Returns:
            Colormap name (defaults to 'viridis' if not found)
        """
        code = self.normalize_variable(variable)
        return self.VARIABLE_COLORMAPS.get(code, "viridis")
    
    def create_variable_entity(self, code: str, name: Optional[str] = None) -> CensusVariable:
        """
        Create a CensusVariable entity.
        
        Args:
            code: Census variable code
            name: Optional human-readable name
            
        Returns:
            CensusVariable entity
        """
        if not name:
            name = self.code_to_name(code)
        
        return CensusVariable(
            code=code,
            name=name,
            description=f"Census variable {code}"
        )
    
    def get_all_variables(self) -> List[CensusVariable]:
        """
        Get all available census variables as entities.
        
        Returns:
            List of CensusVariable entities
        """
        return [
            self.create_variable_entity(code, name)
            for name, code in self.VARIABLE_MAPPING.items()
        ]
    
    def _is_census_code(self, variable: str) -> bool:
        """Check if a string matches census code format."""
        import re
        pattern = r"^[A-Z]\d{5}_\d{3}[A-Z]$"
        return bool(re.match(pattern, variable)) 