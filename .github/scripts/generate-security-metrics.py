#!/usr/bin/env python3
"""
Generate security metrics from various security scan reports.
"""

import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict
import xml.etree.ElementTree as ET


class SecurityMetricsGenerator:
    """Generate comprehensive security metrics from scan results."""
    
    def __init__(self, input_dir: str):
        self.input_dir = Path(input_dir)
        self.metrics = {
            'total_issues': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0,
            'vulnerabilities': 0,
            'secrets': 0,
            'license_issues': 0,
            'compliance_violations': 0,
            'container_issues': 0,
            'infrastructure_issues': 0,
            'dependency_issues': 0,
            'code_quality_issues': 0,
            'categories': defaultdict(int),
            'tools': defaultdict(dict),
            'files_scanned': 0,
            'lines_scanned': 0
        }
    
    def process_all_reports(self):
        """Process all security reports in the input directory."""
        for report_dir in self.input_dir.iterdir():
            if report_dir.is_dir():
                self.process_report_directory(report_dir)
    
    def process_report_directory(self, report_dir: Path):
        """Process reports from a specific tool/category."""
        for report_file in report_dir.glob('**/*'):
            if report_file.is_file():
                self.process_report_file(report_file)
    
    def process_report_file(self, report_file: Path):
        """Process individual report file based on its type."""
        try:
            if report_file.suffix == '.json':
                self.process_json_report(report_file)
            elif report_file.suffix == '.sarif':
                self.process_sarif_report(report_file)
            elif report_file.suffix == '.xml':
                self.process_xml_report(report_file)
        except Exception as e:
            print(f"Error processing {report_file}: {e}", file=sys.stderr)
    
    def process_json_report(self, report_file: Path):
        """Process JSON format security reports."""
        with open(report_file, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON report formats
        if 'vulnerabilities' in data:
            self.process_vulnerability_report(data)
        elif 'results' in data:
            self.process_semgrep_report(data)
        elif 'issues' in data:
            self.process_generic_issues(data['issues'])
        elif 'findings' in data:
            self.process_findings_report(data)
    
    def process_sarif_report(self, report_file: Path):
        """Process SARIF format security reports."""
        with open(report_file, 'r') as f:
            sarif = json.load(f)
        
        for run in sarif.get('runs', []):
            for result in run.get('results', []):
                severity = self.map_sarif_severity(result.get('level', 'note'))
                self.add_issue(severity, 'sarif', result.get('ruleId', 'unknown'))
    
    def process_xml_report(self, report_file: Path):
        """Process XML format security reports."""
        tree = ET.parse(report_file)
        root = tree.getroot()
        
        # Handle different XML formats (OWASP, etc.)
        if 'dependency-check' in root.tag.lower():
            self.process_dependency_check_xml(root)
    
    def process_vulnerability_report(self, data: Dict):
        """Process vulnerability-specific reports."""
        for vuln in data.get('vulnerabilities', []):
            severity = vuln.get('severity', 'low').lower()
            self.add_issue(severity, 'vulnerability', vuln.get('id', 'unknown'))
            self.metrics['vulnerabilities'] += 1
    
    def process_semgrep_report(self, data: Dict):
        """Process Semgrep scan results."""
        for result in data.get('results', []):
            extra = result.get('extra', {})
            severity = extra.get('severity', 'INFO').lower()
            if severity == 'info':
                severity = 'low'
            elif severity == 'warning':
                severity = 'medium'
            elif severity == 'error':
                severity = 'high'
            
            self.add_issue(severity, 'code-quality', result.get('check_id', 'unknown'))
            
            # Check if it's a secret detection
            if 'secret' in result.get('check_id', '').lower():
                self.metrics['secrets'] += 1
    
    def process_findings_report(self, data: Dict):
        """Process generic findings reports."""
        for finding in data.get('findings', []):
            severity = finding.get('severity', 'low').lower()
            category = finding.get('category', 'general')
            self.add_issue(severity, category, finding.get('id', 'unknown'))
    
    def process_generic_issues(self, issues: List):
        """Process generic issue lists."""
        for issue in issues:
            if isinstance(issue, dict):
                severity = issue.get('severity', 'low').lower()
                category = issue.get('category', 'general')
                self.add_issue(severity, category, issue.get('id', 'unknown'))
    
    def process_dependency_check_xml(self, root):
        """Process OWASP Dependency Check XML reports."""
        for dependency in root.findall('.//dependency'):
            vulnerabilities = dependency.findall('.//vulnerability')
            for vuln in vulnerabilities:
                severity = vuln.findtext('severity', 'LOW').lower()
                self.add_issue(severity, 'dependency', vuln.findtext('name', 'unknown'))
                self.metrics['dependency_issues'] += 1
    
    def map_sarif_severity(self, level: str) -> str:
        """Map SARIF severity levels to our standard levels."""
        mapping = {
            'error': 'high',
            'warning': 'medium',
            'note': 'low',
            'none': 'low'
        }
        return mapping.get(level.lower(), 'low')
    
    def add_issue(self, severity: str, category: str, issue_id: str):
        """Add an issue to the metrics."""
        self.metrics['total_issues'] += 1
        self.metrics['categories'][category] += 1
        
        if severity == 'critical':
            self.metrics['critical_issues'] += 1
        elif severity == 'high':
            self.metrics['high_issues'] += 1
        elif severity == 'medium':
            self.metrics['medium_issues'] += 1
        else:
            self.metrics['low_issues'] += 1
        
        # Track by tool
        tool_name = category.split('-')[0] if '-' in category else category
        if tool_name not in self.metrics['tools']:
            self.metrics['tools'][tool_name] = defaultdict(int)
        self.metrics['tools'][tool_name][severity] += 1
    
    def calculate_security_score(self) -> int:
        """Calculate overall security score (0-100)."""
        if self.metrics['total_issues'] == 0:
            return 100
        
        # Weighted scoring
        weights = {
            'critical': 40,
            'high': 30,
            'medium': 20,
            'low': 10
        }
        
        total_weight = sum([
            self.metrics['critical_issues'] * weights['critical'],
            self.metrics['high_issues'] * weights['high'],
            self.metrics['medium_issues'] * weights['medium'],
            self.metrics['low_issues'] * weights['low']
        ])
        
        # Score decreases with issues, minimum score of 0
        max_weight = self.metrics['total_issues'] * weights['critical']
        score = max(0, 100 - (total_weight / max_weight * 100))
        
        return int(score)
    
    def generate_report(self) -> Dict:
        """Generate the final metrics report."""
        self.metrics['security_score'] = self.calculate_security_score()
        self.metrics['summary'] = {
            'total_categories': len(self.metrics['categories']),
            'total_tools_run': len(self.metrics['tools']),
            'highest_severity': self.get_highest_severity()
        }
        return self.metrics
    
    def get_highest_severity(self) -> str:
        """Get the highest severity level found."""
        if self.metrics['critical_issues'] > 0:
            return 'critical'
        elif self.metrics['high_issues'] > 0:
            return 'high'
        elif self.metrics['medium_issues'] > 0:
            return 'medium'
        elif self.metrics['low_issues'] > 0:
            return 'low'
        return 'none'


def main():
    parser = argparse.ArgumentParser(description='Generate security metrics from scan reports')
    parser.add_argument('--input-dir', required=True, help='Directory containing security reports')
    parser.add_argument('--output-file', required=True, help='Output file for metrics JSON')
    
    args = parser.parse_args()
    
    generator = SecurityMetricsGenerator(args.input_dir)
    generator.process_all_reports()
    metrics = generator.generate_report()
    
    with open(args.output_file, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    
    print(f"Security metrics generated: {args.output_file}")
    print(f"Security Score: {metrics['security_score']}/100")
    print(f"Total Issues: {metrics['total_issues']}")
    print(f"Critical: {metrics['critical_issues']}, High: {metrics['high_issues']}, "
          f"Medium: {metrics['medium_issues']}, Low: {metrics['low_issues']}")


if __name__ == '__main__':
    main()