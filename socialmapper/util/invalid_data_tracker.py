#!/usr/bin/env python3
"""
Invalid Data Tracker for SocialMapper.

This module provides utilities to track and manage invalid data points
encountered during processing, such as single-point clusters, malformed
coordinates, or other data quality issues.
"""

import os
import json
import csv
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class InvalidDataTracker:
    """
    Tracks invalid data points encountered during SocialMapper processing.
    
    This class collects information about data quality issues and provides
    methods to save detailed reports for user review and debugging.
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the invalid data tracker.
        
        Args:
            output_dir: Directory where invalid data reports will be saved
        """
        self.output_dir = Path(output_dir)
        self.invalid_points = []
        self.invalid_clusters = []
        self.processing_errors = []
        self.session_start = datetime.now()
        
        logger.info(f"Initialized InvalidDataTracker with output_dir={output_dir}")
    
    def add_invalid_point(self, point_data: Dict[str, Any], reason: str, stage: str = "unknown"):
        """
        Add an invalid point to the tracking list.
        
        Args:
            point_data: Dictionary containing point information (lat, lon, id, etc.)
            reason: Reason why the point is invalid
            stage: Processing stage where the issue was detected
        """
        invalid_entry = {
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            'reason': reason,
            'data': point_data,
            'coordinates': {
                'lat': point_data.get('lat', point_data.get('latitude')),
                'lon': point_data.get('lon', point_data.get('longitude'))
            }
        }
        
        self.invalid_points.append(invalid_entry)
        logger.warning(f"Invalid point detected at {stage}: {reason} - {point_data}")
    
    def add_invalid_cluster(self, cluster_data: Dict[str, Any], reason: str, stage: str = "clustering"):
        """
        Add an invalid cluster to the tracking list.
        
        Args:
            cluster_data: Dictionary containing cluster information
            reason: Reason why the cluster is invalid
            stage: Processing stage where the issue was detected
        """
        invalid_entry = {
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            'reason': reason,
            'data': cluster_data
        }
        
        self.invalid_clusters.append(invalid_entry)
        logger.warning(f"Invalid cluster detected at {stage}: {reason} - {cluster_data}")
    
    def add_processing_error(self, error_data: Dict[str, Any], error_message: str, stage: str = "unknown"):
        """
        Add a processing error to the tracking list.
        
        Args:
            error_data: Dictionary containing data that caused the error
            error_message: Error message or exception details
            stage: Processing stage where the error occurred
        """
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            'error': error_message,
            'data': error_data
        }
        
        self.processing_errors.append(error_entry)
        logger.error(f"Processing error at {stage}: {error_message} - {error_data}")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all tracked invalid data.
        
        Returns:
            Dictionary containing summary statistics
        """
        return {
            'session_start': self.session_start.isoformat(),
            'total_invalid_points': len(self.invalid_points),
            'total_invalid_clusters': len(self.invalid_clusters),
            'total_processing_errors': len(self.processing_errors),
            'stages_with_issues': list(set(
                [item['stage'] for item in self.invalid_points] +
                [item['stage'] for item in self.invalid_clusters] +
                [item['stage'] for item in self.processing_errors]
            ))
        }
    
    def save_invalid_data_report(self, filename_prefix: str = "invalid_data") -> List[str]:
        """
        Save comprehensive invalid data report to files.
        
        Args:
            filename_prefix: Prefix for output filenames
            
        Returns:
            List of created file paths
        """
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        created_files = []
        
        # Save summary report
        summary_file = self.output_dir / f"{filename_prefix}_summary_{timestamp}.json"
        summary_data = {
            'summary': self.get_summary(),
            'invalid_points': self.invalid_points,
            'invalid_clusters': self.invalid_clusters,
            'processing_errors': self.processing_errors
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
        created_files.append(str(summary_file))
        
        # Save invalid points as CSV for easy review
        if self.invalid_points:
            points_csv = self.output_dir / f"{filename_prefix}_points_{timestamp}.csv"
            with open(points_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'stage', 'reason', 'lat', 'lon', 'point_id', 'original_data'])
                
                for point in self.invalid_points:
                    coords = point['coordinates']
                    point_id = point['data'].get('id', point['data'].get('poi_id', 'unknown'))
                    writer.writerow([
                        point['timestamp'],
                        point['stage'],
                        point['reason'],
                        coords.get('lat'),
                        coords.get('lon'),
                        point_id,
                        json.dumps(point['data'])
                    ])
            created_files.append(str(points_csv))
        
        # Save processing errors as text log
        if self.processing_errors:
            errors_log = self.output_dir / f"{filename_prefix}_errors_{timestamp}.log"
            with open(errors_log, 'w') as f:
                f.write(f"SocialMapper Processing Errors Report\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"Session Start: {self.session_start.isoformat()}\n")
                f.write("=" * 60 + "\n\n")
                
                for error in self.processing_errors:
                    f.write(f"Timestamp: {error['timestamp']}\n")
                    f.write(f"Stage: {error['stage']}\n")
                    f.write(f"Error: {error['error']}\n")
                    f.write(f"Data: {json.dumps(error['data'], indent=2)}\n")
                    f.write("-" * 40 + "\n\n")
            created_files.append(str(errors_log))
        
        logger.info(f"Invalid data report saved to {len(created_files)} files: {created_files}")
        return created_files
    
    def print_summary(self):
        """Print a summary of tracked invalid data to console."""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("📊 INVALID DATA SUMMARY")
        print("=" * 60)
        print(f"Session started: {summary['session_start']}")
        print(f"Invalid points: {summary['total_invalid_points']}")
        print(f"Invalid clusters: {summary['total_invalid_clusters']}")
        print(f"Processing errors: {summary['total_processing_errors']}")
        
        if summary['stages_with_issues']:
            print(f"Stages with issues: {', '.join(summary['stages_with_issues'])}")
        
        if summary['total_invalid_points'] > 0:
            print(f"\n⚠️  {summary['total_invalid_points']} invalid points detected and excluded from processing")
            print("   These points have been logged for your review.")
        
        if summary['total_processing_errors'] > 0:
            print(f"\n❌ {summary['total_processing_errors']} processing errors occurred")
            print("   Check the error log for detailed information.")
        
        print("=" * 60)


# Global tracker instance
_global_tracker: Optional[InvalidDataTracker] = None


def get_global_tracker() -> InvalidDataTracker:
    """Get the global invalid data tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = InvalidDataTracker()
    return _global_tracker


def reset_global_tracker(output_dir: str = "output"):
    """Reset the global tracker with a new output directory."""
    global _global_tracker
    _global_tracker = InvalidDataTracker(output_dir)


def track_invalid_point(point_data: Dict[str, Any], reason: str, stage: str = "unknown"):
    """Convenience function to track an invalid point using the global tracker."""
    tracker = get_global_tracker()
    tracker.add_invalid_point(point_data, reason, stage)


def track_invalid_cluster(cluster_data: Dict[str, Any], reason: str, stage: str = "clustering"):
    """Convenience function to track an invalid cluster using the global tracker."""
    tracker = get_global_tracker()
    tracker.add_invalid_cluster(cluster_data, reason, stage)


def track_processing_error(error_data: Dict[str, Any], error_message: str, stage: str = "unknown"):
    """Convenience function to track a processing error using the global tracker."""
    tracker = get_global_tracker()
    tracker.add_processing_error(error_data, error_message, stage) 