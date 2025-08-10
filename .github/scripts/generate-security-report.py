#!/usr/bin/env python3
"""
Generate consolidated security report from various security scan outputs.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import argparse
import html


class SecurityReportGenerator:
    """Generate HTML security report from scan results."""
    
    def __init__(self, input_dir: str, output_file: str):
        self.input_dir = Path(input_dir)
        self.output_file = Path(output_file)
        self.report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_issues': 0,
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'info': 0
            },
            'scans': {}
        }
    
    def parse_bandit_report(self, file_path: Path) -> Dict[str, Any]:
        """Parse Bandit security scan results."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            issues = []
            for result in data.get('results', []):
                issues.append({
                    'severity': result['issue_severity'],
                    'confidence': result['issue_confidence'],
                    'description': result['issue_text'],
                    'file': result['filename'],
                    'line': result['line_number'],
                    'code': result['code']
                })
            
            return {
                'tool': 'Bandit',
                'issues': issues,
                'metrics': data.get('metrics', {})
            }
        except Exception as e:
            print(f"Error parsing Bandit report: {e}")
            return {'tool': 'Bandit', 'issues': [], 'error': str(e)}
    
    def parse_npm_audit(self, file_path: Path) -> Dict[str, Any]:
        """Parse npm audit results."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            issues = []
            for advisory_id, advisory in data.get('advisories', {}).items():
                issues.append({
                    'severity': advisory['severity'],
                    'title': advisory['title'],
                    'module': advisory['module_name'],
                    'vulnerable_versions': advisory['vulnerable_versions'],
                    'patched_versions': advisory['patched_versions'],
                    'overview': advisory['overview'],
                    'recommendation': advisory['recommendation']
                })
            
            return {
                'tool': 'npm audit',
                'issues': issues,
                'metadata': data.get('metadata', {})
            }
        except Exception as e:
            print(f"Error parsing npm audit report: {e}")
            return {'tool': 'npm audit', 'issues': [], 'error': str(e)}
    
    def parse_safety_report(self, file_path: Path) -> Dict[str, Any]:
        """Parse Safety Python dependency check results."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            issues = []
            for vuln in data:
                issues.append({
                    'severity': 'HIGH',  # Safety doesn't provide severity
                    'package': vuln['package'],
                    'installed_version': vuln['installed_version'],
                    'affected_versions': vuln['affected_versions'],
                    'description': vuln['description'],
                    'vulnerability_id': vuln.get('vulnerability_id', 'N/A')
                })
            
            return {
                'tool': 'Safety',
                'issues': issues
            }
        except Exception as e:
            print(f"Error parsing Safety report: {e}")
            return {'tool': 'Safety', 'issues': [], 'error': str(e)}
    
    def collect_reports(self):
        """Collect all security reports from input directory."""
        report_patterns = {
            '**/bandit-report.json': self.parse_bandit_report,
            '**/npm-audit-report.json': self.parse_npm_audit,
            '**/safety-report.json': self.parse_safety_report,
        }
        
        for pattern, parser in report_patterns.items():
            for file_path in self.input_dir.rglob(pattern.split('/')[-1]):
                print(f"Processing {file_path}")
                result = parser(file_path)
                if result and result.get('issues'):
                    scan_name = f"{result['tool']}_{file_path.parent.name}"
                    self.report_data['scans'][scan_name] = result
                    
                    # Update summary
                    for issue in result['issues']:
                        self.report_data['summary']['total_issues'] += 1
                        severity = issue.get('severity', 'info').lower()
                        if severity in self.report_data['summary']:
                            self.report_data['summary'][severity] += 1
    
    def generate_html(self) -> str:
        """Generate HTML report."""
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SocialMapper Security Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-card h3 {{
            margin: 0;
            font-size: 2em;
        }}
        .summary-card p {{
            margin: 5px 0 0 0;
            color: #666;
            text-transform: uppercase;
            font-size: 0.9em;
        }}
        .critical {{ color: #d32f2f; }}
        .high {{ color: #f57c00; }}
        .medium {{ color: #fbc02d; }}
        .low {{ color: #388e3c; }}
        .info {{ color: #1976d2; }}
        .scan-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .scan-header {{
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .issue {{
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid;
            background: #fafafa;
            border-radius: 4px;
        }}
        .issue.critical {{ border-color: #d32f2f; }}
        .issue.high {{ border-color: #f57c00; }}
        .issue.medium {{ border-color: #fbc02d; }}
        .issue.low {{ border-color: #388e3c; }}
        .issue.info {{ border-color: #1976d2; }}
        .issue-title {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .issue-meta {{
            color: #666;
            font-size: 0.9em;
        }}
        code {{
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background: #263238;
            color: #aed581;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>SocialMapper Security Report</h1>
        <p>Generated: {timestamp}</p>
    </div>
    
    <summary>
    <div class="summary">
        <div class="summary-card">
            <h3>{total_issues}</h3>
            <p>Total Issues</p>
        </div>
        <div class="summary-card">
            <h3 class="critical">{critical}</h3>
            <p>Critical</p>
        </div>
        <div class="summary-card">
            <h3 class="high">{high}</h3>
            <p>High</p>
        </div>
        <div class="summary-card">
            <h3 class="medium">{medium}</h3>
            <p>Medium</p>
        </div>
        <div class="summary-card">
            <h3 class="low">{low}</h3>
            <p>Low</p>
        </div>
        <div class="summary-card">
            <h3 class="info">{info}</h3>
            <p>Info</p>
        </div>
    </div>
    </summary>
    
    {scan_results}
    
    <div class="footer">
        <p>SocialMapper Security Report - CI/CD Pipeline</p>
    </div>
</body>
</html>'''
        
        # Generate scan results HTML
        scan_results_html = ''
        for scan_name, scan_data in self.report_data['scans'].items():
            scan_results_html += f'''
            <div class="scan-section">
                <div class="scan-header">
                    <h2>{html.escape(scan_data['tool'])}</h2>
                    <p>{len(scan_data['issues'])} issues found</p>
                </div>
                {self._generate_issues_html(scan_data['issues'])}
            </div>
            '''
        
        return html_template.format(
            timestamp=self.report_data['timestamp'],
            total_issues=self.report_data['summary']['total_issues'],
            critical=self.report_data['summary']['critical'],
            high=self.report_data['summary']['high'],
            medium=self.report_data['summary']['medium'],
            low=self.report_data['summary']['low'],
            info=self.report_data['summary']['info'],
            scan_results=scan_results_html
        )
    
    def _generate_issues_html(self, issues: List[Dict]) -> str:
        """Generate HTML for individual issues."""
        if not issues:
            return '<p>No issues found</p>'
        
        html = ''
        for issue in issues[:10]:  # Limit to first 10 issues per scan
            severity = issue.get('severity', 'info').lower()
            title = issue.get('title') or issue.get('description', 'Security Issue')
            
            html += f'''
            <div class="issue {severity}">
                <div class="issue-title">{html.escape(title)}</div>
                <div class="issue-meta">
            '''
            
            if 'file' in issue:
                html += f'File: <code>{html.escape(issue["file"])}</code> '
            if 'line' in issue:
                html += f'Line: {issue["line"]} '
            if 'module' in issue:
                html += f'Module: <code>{html.escape(issue["module"])}</code> '
            if 'package' in issue:
                html += f'Package: <code>{html.escape(issue["package"])}</code> '
            
            html += '</div>'
            
            if 'code' in issue and issue['code']:
                html += f'<pre>{html.escape(issue["code"])}</pre>'
            
            if 'recommendation' in issue:
                html += f'<p><strong>Recommendation:</strong> {html.escape(issue["recommendation"])}</p>'
            
            html += '</div>'
        
        if len(issues) > 10:
            html += f'<p><em>... and {len(issues) - 10} more issues</em></p>'
        
        return html
    
    def generate(self):
        """Generate the security report."""
        print(f"Collecting reports from {self.input_dir}")
        self.collect_reports()
        
        print(f"Generating HTML report")
        html_content = self.generate_html()
        
        self.output_file.write_text(html_content)
        print(f"Report saved to {self.output_file}")
        
        # Also save JSON data
        json_file = self.output_file.with_suffix('.json')
        with open(json_file, 'w') as f:
            json.dump(self.report_data, f, indent=2)
        print(f"JSON data saved to {json_file}")


def main():
    parser = argparse.ArgumentParser(description='Generate security report from scan results')
    parser.add_argument('--input-dir', required=True, help='Directory containing scan results')
    parser.add_argument('--output-file', required=True, help='Output HTML file path')
    
    args = parser.parse_args()
    
    generator = SecurityReportGenerator(args.input_dir, args.output_file)
    generator.generate()


if __name__ == '__main__':
    main()