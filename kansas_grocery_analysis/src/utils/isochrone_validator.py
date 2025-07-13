#!/usr/bin/env python3
"""
Isochrone validation system for quality control.

This module provides comprehensive validation checks to ensure only
high-quality, accurate isochrones are added to the cache.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

import numpy as np
from shapely.geometry import shape, Point, Polygon, MultiPolygon
from shapely.validation import explain_validity
from shapely.ops import unary_union

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation result status."""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    

@dataclass
class ValidationResult:
    """Result of isochrone validation."""
    status: ValidationStatus
    score: float  # 0.0 to 1.0
    checks_passed: List[str]
    checks_failed: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
    
    @property
    def is_valid(self) -> bool:
        """Check if isochrone passed validation."""
        return self.status == ValidationStatus.VALID
    
    @property
    def needs_review(self) -> bool:
        """Check if isochrone needs manual review."""
        return self.status == ValidationStatus.WARNING


class IsochroneValidator:
    """Comprehensive isochrone validation system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize validator with configuration.
        
        Args:
            config: Validation configuration parameters
        """
        self.config = config or self._default_config()
        
    def _default_config(self) -> Dict[str, Any]:
        """Default validation configuration."""
        return {
            # Geometry checks
            'min_area_km2': 1.0,  # Minimum isochrone area
            'max_area_km2': 5000.0,  # Maximum isochrone area
            'max_hole_ratio': 0.2,  # Max ratio of holes to total area
            'min_vertices': 10,  # Minimum polygon vertices
            'max_vertices': 10000,  # Maximum polygon vertices
            
            # Shape checks
            'min_compactness': 0.3,  # Minimum compactness ratio
            'max_elongation': 10.0,  # Maximum elongation ratio
            'max_complexity': 5.0,  # Maximum perimeter/sqrt(area) ratio
            
            # Travel mode expectations (area in km²)
            'expected_area_ranges': {
                'walk': {
                    15: (2, 20),    # 15-min walk: 2-20 km²
                    30: (8, 50),    # 30-min walk: 8-50 km²
                    45: (18, 80),   # 45-min walk: 18-80 km²
                    60: (30, 120),  # 60-min walk: 30-120 km²
                },
                'bike': {
                    15: (20, 100),   # 15-min bike: 20-100 km²
                    30: (80, 400),   # 30-min bike: 80-400 km²
                    45: (180, 900),  # 45-min bike: 180-900 km²
                    60: (320, 1600), # 60-min bike: 320-1600 km²
                },
                'drive': {
                    15: (100, 500),   # 15-min drive: 100-500 km²
                    30: (400, 2000),  # 30-min drive: 400-2000 km²
                    45: (900, 4500),  # 45-min drive: 900-4500 km²
                    60: (1600, 8000), # 60-min drive: 1600-8000 km²
                }
            },
            
            # Network quality checks
            'min_network_nodes': 50,  # Minimum nodes in road network
            'min_network_edges': 25,  # Minimum edges in road network
            
            # Scoring weights
            'weights': {
                'geometry': 0.3,
                'area': 0.2,
                'shape': 0.2,
                'network': 0.15,
                'consistency': 0.15
            }
        }
    
    def validate_isochrone(
        self,
        geometry: Any,
        travel_time: int,
        travel_mode: str,
        origin: Tuple[float, float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate an isochrone comprehensively.
        
        Args:
            geometry: Shapely geometry object
            travel_time: Travel time in minutes
            travel_mode: Mode of travel (walk, bike, drive)
            origin: Origin point (lat, lon)
            metadata: Additional metadata (network stats, generation time, etc.)
            
        Returns:
            ValidationResult with detailed findings
        """
        checks_passed = []
        checks_failed = []
        warnings = []
        scores = {}
        
        # 1. Basic geometry validation
        geom_score = self._validate_geometry(
            geometry, checks_passed, checks_failed, warnings
        )
        scores['geometry'] = geom_score
        
        # 2. Area validation
        area_score = self._validate_area(
            geometry, travel_time, travel_mode, 
            checks_passed, checks_failed, warnings
        )
        scores['area'] = area_score
        
        # 3. Shape quality validation
        shape_score = self._validate_shape(
            geometry, origin, checks_passed, checks_failed, warnings
        )
        scores['shape'] = shape_score
        
        # 4. Network quality validation (if metadata provided)
        if metadata:
            network_score = self._validate_network_quality(
                metadata, checks_passed, checks_failed, warnings
            )
            scores['network'] = network_score
        else:
            scores['network'] = 1.0  # No network data to validate
        
        # 5. Consistency checks
        consistency_score = self._validate_consistency(
            geometry, origin, travel_time, travel_mode,
            checks_passed, checks_failed, warnings
        )
        scores['consistency'] = consistency_score
        
        # Calculate weighted score
        weights = self.config['weights']
        total_score = sum(
            scores[key] * weights.get(key, 0.1) 
            for key in scores
        )
        
        # Determine status
        if checks_failed:
            status = ValidationStatus.INVALID
        elif warnings:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.VALID
        
        # Build result metadata
        result_metadata = {
            'scores': scores,
            'timestamp': datetime.now().isoformat(),
            'validator_version': '1.0.0',
            'config_summary': {
                'min_area_km2': self.config['min_area_km2'],
                'max_area_km2': self.config['max_area_km2'],
                'min_network_nodes': self.config['min_network_nodes']
            }
        }
        
        if metadata:
            result_metadata['input_metadata'] = metadata
        
        return ValidationResult(
            status=status,
            score=total_score,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            warnings=warnings,
            metadata=result_metadata
        )
    
    def _validate_geometry(
        self,
        geometry: Any,
        passed: List[str],
        failed: List[str],
        warnings: List[str]
    ) -> float:
        """Validate geometry structure and validity."""
        score = 1.0
        
        # Check if geometry is valid
        if not geometry.is_valid:
            failed.append(f"Invalid geometry: {explain_validity(geometry)}")
            return 0.0
        else:
            passed.append("Valid geometry structure")
        
        # Check geometry type
        if not isinstance(geometry, (Polygon, MultiPolygon)):
            failed.append(f"Invalid geometry type: {type(geometry).__name__}")
            return 0.0
        else:
            passed.append(f"Correct geometry type: {type(geometry).__name__}")
        
        # Check for empty geometry
        if geometry.is_empty:
            failed.append("Empty geometry")
            return 0.0
        
        # Check vertex count
        if isinstance(geometry, Polygon):
            num_vertices = len(geometry.exterior.coords)
        else:
            num_vertices = sum(len(p.exterior.coords) for p in geometry.geoms)
        
        min_vertices = self.config['min_vertices']
        max_vertices = self.config['max_vertices']
        
        if num_vertices < min_vertices:
            failed.append(f"Too few vertices: {num_vertices} < {min_vertices}")
            score *= 0.5
        elif num_vertices > max_vertices:
            warnings.append(f"Many vertices: {num_vertices} > {max_vertices}")
            score *= 0.9
        else:
            passed.append(f"Vertex count OK: {num_vertices}")
        
        # Check for holes (interior rings)
        if isinstance(geometry, Polygon):
            num_holes = len(geometry.interiors)
        else:
            num_holes = sum(len(p.interiors) for p in geometry.geoms)
        
        if num_holes > 0:
            hole_area = sum(Polygon(interior).area for p in 
                          (geometry.geoms if isinstance(geometry, MultiPolygon) else [geometry])
                          for interior in p.interiors)
            hole_ratio = hole_area / geometry.area
            
            if hole_ratio > self.config['max_hole_ratio']:
                warnings.append(f"Large holes detected: {hole_ratio:.1%} of area")
                score *= 0.8
            else:
                passed.append(f"Hole ratio acceptable: {hole_ratio:.1%}")
        
        return score
    
    def _validate_area(
        self,
        geometry: Any,
        travel_time: int,
        travel_mode: str,
        passed: List[str],
        failed: List[str],
        warnings: List[str]
    ) -> float:
        """Validate isochrone area against expectations."""
        # Calculate area in km²
        # Rough approximation for lat/lon coordinates
        area_km2 = geometry.area * 111.32 * 111.32
        
        # Check absolute bounds
        min_area = self.config['min_area_km2']
        max_area = self.config['max_area_km2']
        
        if area_km2 < min_area:
            failed.append(f"Area too small: {area_km2:.1f} km² < {min_area} km²")
            return 0.0
        elif area_km2 > max_area:
            failed.append(f"Area too large: {area_km2:.1f} km² > {max_area} km²")
            return 0.0
        
        # Check against expected ranges for travel mode/time
        expected_ranges = self.config['expected_area_ranges']
        
        if travel_mode in expected_ranges and travel_time in expected_ranges[travel_mode]:
            min_expected, max_expected = expected_ranges[travel_mode][travel_time]
            
            if area_km2 < min_expected:
                warnings.append(
                    f"Area smaller than expected for {travel_time}min {travel_mode}: "
                    f"{area_km2:.1f} km² < {min_expected} km²"
                )
                # Score based on how far off
                score = max(0.5, area_km2 / min_expected)
            elif area_km2 > max_expected:
                warnings.append(
                    f"Area larger than expected for {travel_time}min {travel_mode}: "
                    f"{area_km2:.1f} km² > {max_expected} km²"
                )
                # Score based on how far off
                score = max(0.5, max_expected / area_km2)
            else:
                passed.append(
                    f"Area within expected range: {area_km2:.1f} km² "
                    f"({min_expected}-{max_expected} km²)"
                )
                score = 1.0
        else:
            # No specific expectation, just use general bounds
            passed.append(f"Area within bounds: {area_km2:.1f} km²")
            score = 1.0
        
        return score
    
    def _validate_shape(
        self,
        geometry: Any,
        origin: Tuple[float, float],
        passed: List[str],
        failed: List[str],
        warnings: List[str]
    ) -> float:
        """Validate isochrone shape quality."""
        score = 1.0
        
        # Calculate shape metrics
        area = geometry.area
        perimeter = geometry.length
        
        # Compactness (isoperimetric quotient)
        # 1.0 for a circle, lower for irregular shapes
        compactness = (4 * np.pi * area) / (perimeter * perimeter)
        
        min_compactness = self.config['min_compactness']
        if compactness < min_compactness:
            warnings.append(
                f"Low compactness: {compactness:.2f} < {min_compactness}"
            )
            score *= (compactness / min_compactness)
        else:
            passed.append(f"Good compactness: {compactness:.2f}")
        
        # Check if origin is contained
        origin_point = Point(origin[1], origin[0])  # lon, lat
        if not geometry.contains(origin_point):
            # Check distance to nearest edge
            distance = geometry.distance(origin_point)
            if distance > 0.001:  # ~100m
                warnings.append(
                    f"Origin not contained in isochrone "
                    f"(distance: {distance * 111.32:.1f} km)"
                )
                score *= 0.8
            else:
                passed.append("Origin near isochrone boundary")
        else:
            passed.append("Origin contained in isochrone")
        
        # Complexity check (perimeter to area ratio)
        complexity = perimeter / np.sqrt(area)
        max_complexity = self.config['max_complexity']
        
        if complexity > max_complexity:
            warnings.append(
                f"High complexity: {complexity:.2f} > {max_complexity}"
            )
            score *= 0.9
        else:
            passed.append(f"Acceptable complexity: {complexity:.2f}")
        
        return score
    
    def _validate_network_quality(
        self,
        metadata: Dict[str, Any],
        passed: List[str],
        failed: List[str],
        warnings: List[str]
    ) -> float:
        """Validate network data quality."""
        score = 1.0
        
        # Check network size
        nodes = metadata.get('network_nodes', 0)
        edges = metadata.get('network_edges', 0)
        
        min_nodes = self.config['min_network_nodes']
        min_edges = self.config['min_network_edges']
        
        if nodes < min_nodes:
            warnings.append(
                f"Small network: {nodes} nodes < {min_nodes}"
            )
            score *= 0.8
        else:
            passed.append(f"Adequate network size: {nodes} nodes")
        
        if edges < min_edges:
            warnings.append(
                f"Few edges: {edges} edges < {min_edges}"
            )
            score *= 0.8
        else:
            passed.append(f"Adequate edge count: {edges} edges")
        
        # Check generation time if available
        gen_time = metadata.get('generation_time_seconds', 0)
        if gen_time > 30:
            warnings.append(
                f"Slow generation: {gen_time:.1f} seconds"
            )
            # Don't penalize score for slow generation
        
        # Check data age if available
        if 'osm_data_timestamp' in metadata:
            data_age_days = (
                datetime.now() - 
                datetime.fromisoformat(metadata['osm_data_timestamp'])
            ).days
            
            if data_age_days > 365:
                warnings.append(
                    f"Old OSM data: {data_age_days} days old"
                )
                score *= 0.9
        
        return score
    
    def _validate_consistency(
        self,
        geometry: Any,
        origin: Tuple[float, float],
        travel_time: int,
        travel_mode: str,
        passed: List[str],
        failed: List[str],
        warnings: List[str]
    ) -> float:
        """Validate logical consistency of the isochrone."""
        score = 1.0
        
        # Check maximum distance from origin
        origin_point = Point(origin[1], origin[0])
        
        # Get furthest point on boundary
        if isinstance(geometry, Polygon):
            boundary_points = list(geometry.exterior.coords)
        else:
            boundary_points = []
            for poly in geometry.geoms:
                boundary_points.extend(list(poly.exterior.coords))
        
        max_distance = max(
            origin_point.distance(Point(p)) 
            for p in boundary_points
        )
        
        # Convert to km
        max_distance_km = max_distance * 111.32
        
        # Expected maximum distances (rough estimates)
        expected_max_distances = {
            'walk': travel_time * 0.083,    # 5 km/h
            'bike': travel_time * 0.25,      # 15 km/h
            'drive': travel_time * 1.0       # 60 km/h
        }
        
        if travel_mode in expected_max_distances:
            expected_max = expected_max_distances[travel_mode]
            
            if max_distance_km > expected_max * 1.5:
                warnings.append(
                    f"Unusually far reach: {max_distance_km:.1f} km "
                    f"(expected < {expected_max * 1.5:.1f} km)"
                )
                score *= 0.8
            else:
                passed.append(
                    f"Reasonable reach: {max_distance_km:.1f} km"
                )
        
        return score
    
    def validate_batch(
        self,
        isochrones: List[Dict[str, Any]]
    ) -> List[ValidationResult]:
        """Validate a batch of isochrones.
        
        Args:
            isochrones: List of isochrone dictionaries with geometry and metadata
            
        Returns:
            List of ValidationResult objects
        """
        results = []
        
        for iso in isochrones:
            result = self.validate_isochrone(
                geometry=iso['geometry'],
                travel_time=iso['travel_time'],
                travel_mode=iso['travel_mode'],
                origin=(iso['lat'], iso['lon']),
                metadata=iso.get('metadata')
            )
            results.append(result)
        
        return results
    
    def get_validation_report(
        self,
        results: List[ValidationResult]
    ) -> Dict[str, Any]:
        """Generate summary report from validation results.
        
        Args:
            results: List of validation results
            
        Returns:
            Summary statistics and findings
        """
        total = len(results)
        valid = sum(1 for r in results if r.status == ValidationStatus.VALID)
        invalid = sum(1 for r in results if r.status == ValidationStatus.INVALID)
        warnings = sum(1 for r in results if r.status == ValidationStatus.WARNING)
        
        # Aggregate common issues
        all_failed_checks = []
        all_warnings = []
        
        for result in results:
            all_failed_checks.extend(result.checks_failed)
            all_warnings.extend(result.warnings)
        
        # Count frequencies
        from collections import Counter
        failed_counts = Counter(all_failed_checks)
        warning_counts = Counter(all_warnings)
        
        return {
            'summary': {
                'total': total,
                'valid': valid,
                'invalid': invalid,
                'warnings': warnings,
                'pass_rate': valid / total if total > 0 else 0,
                'average_score': sum(r.score for r in results) / total if total > 0 else 0
            },
            'common_failures': dict(failed_counts.most_common(10)),
            'common_warnings': dict(warning_counts.most_common(10)),
            'score_distribution': {
                '0.0-0.5': sum(1 for r in results if r.score <= 0.5),
                '0.5-0.7': sum(1 for r in results if 0.5 < r.score <= 0.7),
                '0.7-0.9': sum(1 for r in results if 0.7 < r.score <= 0.9),
                '0.9-1.0': sum(1 for r in results if r.score > 0.9)
            }
        }


# Example usage
if __name__ == "__main__":
    from shapely.geometry import Point
    
    # Create test validator
    validator = IsochroneValidator()
    
    # Create a test isochrone (circle)
    center = Point(-101.0, 39.0)
    test_isochrone = center.buffer(0.3)  # ~30km radius
    
    # Validate
    result = validator.validate_isochrone(
        geometry=test_isochrone,
        travel_time=30,
        travel_mode='drive',
        origin=(39.0, -101.0),
        metadata={
            'network_nodes': 1000,
            'network_edges': 500,
            'generation_time_seconds': 5.2
        }
    )
    
    print(f"Validation status: {result.status.value}")
    print(f"Score: {result.score:.2f}")
    print(f"Passed checks: {len(result.checks_passed)}")
    print(f"Failed checks: {len(result.checks_failed)}")
    print(f"Warnings: {len(result.warnings)}")