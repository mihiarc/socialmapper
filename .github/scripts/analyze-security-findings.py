#!/usr/bin/env python3
"""
Analyze security findings from various scanning tools and generate a summary.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


class SecurityFindingsAnalyzer:
    """Analyze and aggregate security findings from multiple tools."""
    
    def __init__(self, artifacts_dir: str, output_file: str):
        self.artifacts_dir = Path(artifacts_dir)
        self.output_file = Path(output_file)
        self.findings = defaultdict(list)
        self.summary = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0,
            'total': 0
        }
        self.tools_summary = {}
    
    def normalize_severity(self, severity: str) -> str:
        """Normalize severity levels across different tools."""
        severity = severity.upper()
        severity_map = {
            'CRITICAL': 'critical',
            'HIGH': 'high',
            'MEDIUM': 'medium',
            'MODERATE': 'medium',
            'LOW': 'low',
            'INFO': 'info',
            'INFORMATIONAL': 'info',
            'WARNING': 'medium',
            'ERROR': 'high'
        }
        return severity_map.get(severity, 'info')
    
    def parse_sarif_file(self, file_path: Path) -> List[Dict]:
        """Parse SARIF format security findings."""
        findings = []
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for run in data.get('runs', []):
                tool_name = run.get('tool', {}).get('driver', {}).get('name', 'Unknown')
                
                for result in run.get('results', []):
                    severity = 'medium'  # Default severity
                    
                    # Try to get severity from different locations
                    if 'properties' in result:
                        if 'issue_severity' in result['properties']:
                            severity = result['properties']['issue_severity']
                        elif 'severity' in result['properties']:
                            severity = result['properties']['severity']
                    
                    # Get rule information
                    rule_id = result.get('ruleId', 'unknown')
                    message = result.get('message', {}).get('text', 'No description')
                    
                    # Get location information
                    locations = result.get('locations', [])
                    for location in locations:
                        physical_location = location.get('physicalLocation', {})
                        artifact_location = physical_location.get('artifactLocation', {})
                        file_path = artifact_location.get('uri', 'unknown')
                        
                        finding = {
                            'tool': tool_name,
                            'severity': self.normalize_severity(severity),
                            'rule_id': rule_id,
                            'message': message,
                            'file': file_path,
                            'type': 'sarif'
                        }
                        findings.append(finding)
            
        except Exception as e:
            print(f"Error parsing SARIF file {file_path}: {e}")
        
        return findings
    
    def parse_json_report(self, file_path: Path) -> List[Dict]:
        """Parse generic JSON security reports."""
        findings = []
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Handle Bandit reports
            if 'results' in data and 'metrics' in data:
                for result in data['results']:
                    finding = {
                        'tool': 'Bandit',
                        'severity': self.normalize_severity(result.get('issue_severity', 'medium')),
                        'confidence': result.get('issue_confidence', 'medium'),
                        'message': result.get('issue_text', ''),
                        'file': result.get('filename', ''),
                        'line': result.get('line_number', 0),
                        'type': 'bandit'
                    }
                    findings.append(finding)
            
            # Handle npm audit reports
            elif 'advisories' in data:
                for advisory_id, advisory in data['advisories'].items():
                    finding = {
                        'tool': 'npm-audit',
                        'severity': self.normalize_severity(advisory.get('severity', 'medium')),
                        'title': advisory.get('title', ''),
                        'module': advisory.get('module_name', ''),
                        'vulnerable_versions': advisory.get('vulnerable_versions', ''),
                        'recommendation': advisory.get('recommendation', ''),
                        'type': 'dependency'
                    }
                    findings.append(finding)
            
            # Handle Safety reports
            elif isinstance(data, list) and len(data) > 0 and 'package' in data[0]:
                for vuln in data:
                    finding = {
                        'tool': 'Safety',
                        'severity': self.normalize_severity('high'),
                        'package': vuln.get('package', ''),
                        'installed_version': vuln.get('installed_version', ''),
                        'affected_versions': vuln.get('affected_versions', ''),
                        'description': vuln.get('description', ''),
                        'type': 'dependency'
                    }
                    findings.append(finding)
            
            # Handle ESLint security reports
            elif isinstance(data, list) and len(data) > 0 and 'filePath' in data[0]:
                for file_report in data:
                    for message in file_report.get('messages', []):
                        finding = {
                            'tool': 'ESLint-Security',
                            'severity': self.normalize_severity(message.get('severity', '1')),
                            'rule': message.get('ruleId', ''),
                            'message': message.get('message', ''),
                            'file': file_report.get('filePath', ''),
                            'line': message.get('line', 0),
                            'column': message.get('column', 0),
                            'type': 'eslint'
                        }
                        findings.append(finding)
            
        except Exception as e:
            print(f"Error parsing JSON file {file_path}: {e}")
        
        return findings
    
    def collect_all_findings(self):
        """Collect findings from all artifact files."""
        # Process SARIF files
        for sarif_file in self.artifacts_dir.rglob('*.sarif'):
            print(f"Processing SARIF: {sarif_file}")
            findings = self.parse_sarif_file(sarif_file)
            for finding in findings:
                self.findings[finding['tool']].append(finding)
        
        # Process JSON reports
        json_patterns = [
            '*-report.json',
            '*-results.json',
            '*.json'
        ]
        
        processed_files = set()
        for pattern in json_patterns:
            for json_file in self.artifacts_dir.rglob(pattern):
                if json_file not in processed_files and not json_file.name.endswith('.sarif'):
                    print(f"Processing JSON: {json_file}")
                    findings = self.parse_json_report(json_file)
                    for finding in findings:
                        self.findings[finding['tool']].append(finding)
                    processed_files.add(json_file)
    
    def calculate_summary(self):
        """Calculate summary statistics."""
        for tool, tool_findings in self.findings.items():
            tool_summary = {
                'total': len(tool_findings),
                'by_severity': defaultdict(int)
            }
            
            for finding in tool_findings:
                severity = finding.get('severity', 'info')
                tool_summary['by_severity'][severity] += 1
                self.summary[severity] += 1
                self.summary['total'] += 1
            
            self.tools_summary[tool] = tool_summary
    
    def deduplicate_findings(self):
        """Remove duplicate findings across tools."""
        seen_findings = set()
        deduplicated = defaultdict(list)
        
        for tool, tool_findings in self.findings.items():
            for finding in tool_findings:
                # Create a unique key for the finding
                finding_key = (
                    finding.get('file', ''),
                    finding.get('line', 0),
                    finding.get('rule_id', finding.get('rule', '')),
                    finding.get('message', '')[:100]  # First 100 chars of message
                )
                
                if finding_key not in seen_findings:
                    seen_findings.add(finding_key)
                    deduplicated[tool].append(finding)
        
        self.findings = deduplicated
    
    def generate_output(self):
        """Generate the output summary."""
        output = {
            'summary': self.summary,
            'tools_summary': self.tools_summary,
            'total_tools_run': len(self.findings),
            'gate_passed': self.evaluate_gate(),
            'high_priority_findings': self.get_high_priority_findings(),
            'findings_by_tool': {
                tool: len(findings) for tool, findings in self.findings.items()
            }
        }
        
        return output
    
    def evaluate_gate(self) -> bool:
        """Evaluate if security gate should pass."""
        # Gate fails if there are any critical issues
        if self.summary['critical'] > 0:
            return False
        
        # Gate fails if there are more than 5 high issues
        if self.summary['high'] > 5:
            return False
        
        # Gate fails if there are more than 20 medium issues
        if self.summary['medium'] > 20:
            return False
        
        return True
    
    def get_high_priority_findings(self) -> List[Dict]:
        """Get the highest priority findings for review."""
        high_priority = []
        
        for tool, tool_findings in self.findings.items():
            for finding in tool_findings:
                if finding.get('severity') in ['critical', 'high']:
                    high_priority.append({
                        'tool': tool,
                        'severity': finding.get('severity'),
                        'description': finding.get('message', finding.get('title', '')),
                        'location': finding.get('file', 'unknown')
                    })
        
        # Sort by severity (critical first, then high)
        high_priority.sort(key=lambda x: (x['severity'] != 'critical', x['severity']))
        
        # Return top 10
        return high_priority[:10]
    
    def analyze(self):
        """Run the complete analysis."""
        print("Collecting security findings...")
        self.collect_all_findings()
        
        print("Deduplicating findings...")
        self.deduplicate_findings()
        
        print("Calculating summary...")
        self.calculate_summary()
        
        print("Generating output...")
        output = self.generate_output()
        
        # Save output
        with open(self.output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"Analysis complete. Results saved to {self.output_file}")
        
        # Print summary
        print("\n" + "="*50)
        print("SECURITY FINDINGS SUMMARY")
        print("="*50)
        print(f"Total findings: {output['summary']['total']}")
        print(f"Critical: {output['summary']['critical']}")
        print(f"High: {output['summary']['high']}")
        print(f"Medium: {output['summary']['medium']}")
        print(f"Low: {output['summary']['low']}")
        print(f"Info: {output['summary']['info']}")
        print(f"\nGate Status: {'PASSED' if output['gate_passed'] else 'FAILED'}")
        
        if not output['gate_passed']:
            print("\nHigh Priority Findings:")
            for finding in output['high_priority_findings']:
                print(f"  - [{finding['severity'].upper()}] {finding['tool']}: {finding['description'][:80]}...")
        
        return output['gate_passed']


def main():
    parser = argparse.ArgumentParser(description='Analyze security findings from scanning tools')
    parser.add_argument('--artifacts-dir', required=True, help='Directory containing security scan artifacts')
    parser.add_argument('--output-file', required=True, help='Output JSON file for summary')
    
    args = parser.parse_args()
    
    analyzer = SecurityFindingsAnalyzer(args.artifacts_dir, args.output_file)
    gate_passed = analyzer.analyze()
    
    # Exit with non-zero if gate failed
    if not gate_passed:
        exit(1)


if __name__ == '__main__':
    main()