#!/usr/bin/env python3
"""
Calculate security score from metrics file.
"""

import json
import sys
import argparse


def calculate_score(metrics_file: str) -> int:
    """Calculate security score from metrics."""
    try:
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        return metrics.get('security_score', 0)
    except Exception as e:
        print(f"Error calculating score: {e}", file=sys.stderr)
        return 0


def main():
    parser = argparse.ArgumentParser(description='Calculate security score')
    parser.add_argument('--metrics-file', required=True, help='Security metrics JSON file')
    
    args = parser.parse_args()
    score = calculate_score(args.metrics_file)
    print(score)
    
    # Exit with non-zero if score is below threshold
    if score < 50:
        sys.exit(1)


if __name__ == '__main__':
    main()