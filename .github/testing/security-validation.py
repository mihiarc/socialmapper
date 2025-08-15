#!/usr/bin/env python3
"""
Security Pipeline Validation Script

Validates all security scanning configurations, SARIF outputs,
and security policy enforcement in the CI/CD pipeline.
"""

import json
import os
import sys
import yaml
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import tempfile
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
import time

console = Console()

@dataclass
class SecurityCheck:
    name: str
    description: str
    config_files: List[str]
    workflow_integration: str
    required_secrets: List[str]
    sarif_output: bool = True

class SecurityValidator:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.workflows_dir = repo_root / ".github" / "workflows"
        self.security_dir = repo_root / ".github" / "security"
        
        # Define security tools and their configurations
        self.security_checks = [
            SecurityCheck(
                name="CodeQL SAST",
                description="GitHub's semantic code analysis",
                config_files=[".github/codeql/codeql-config.yml"],
                workflow_integration="github/codeql-action",
                required_secrets=[],
                sarif_output=True
            ),
            SecurityCheck(
                name="Trivy Vulnerability Scanner",
                description="Container and filesystem vulnerability scanning",
                config_files=[".trivyignore", ".github/security/trivy-config.yaml"],
                workflow_integration="aquasecurity/trivy-action",
                required_secrets=[],
                sarif_output=True
            ),
            SecurityCheck(
                name="Semgrep SAST",
                description="Rule-based static analysis",
                config_files=[".semgrep.yml", ".github/security/semgrep-rules/"],
                workflow_integration="returntocorp/semgrep-action",
                required_secrets=[],
                sarif_output=True
            ),
            SecurityCheck(
                name="Bandit Python Security",
                description="Python security issue detection",
                config_files=[".bandit", "pyproject.toml"],
                workflow_integration="bandit[toml]",
                required_secrets=[],
                sarif_output=True
            ),
            SecurityCheck(
                name="Gitleaks Secret Scanning",
                description="Git repository secret detection",
                config_files=[".github/security/gitleaks.toml", ".gitleaks.toml"],
                workflow_integration="gitleaks/gitleaks-action",
                required_secrets=[],
                sarif_output=False
            ),
            SecurityCheck(
                name="TruffleHog Secret Scanning",
                description="Enhanced secret detection",
                config_files=[".trufflehog.yaml"],
                workflow_integration="trufflesecurity/trufflehog",
                required_secrets=[],
                sarif_output=False
            ),
            SecurityCheck(
                name="Snyk Vulnerability Scanning",
                description="Dependency vulnerability scanning",
                config_files=[".snyk", "snyk.json"],
                workflow_integration="snyk/actions",
                required_secrets=["SNYK_TOKEN"],
                sarif_output=True
            ),
            SecurityCheck(
                name="OWASP Dependency Check",
                description="Dependency vulnerability analysis",
                config_files=[".github/security/dependency-check-suppressions.xml"],
                workflow_integration="dependency-check/Dependency-Check_Action",
                required_secrets=["NVD_API_KEY"],
                sarif_output=True
            ),
            SecurityCheck(
                name="Hadolint Docker Linting",
                description="Dockerfile security best practices",
                config_files=[".hadolint.yaml", ".github/security/hadolint.yaml"],
                workflow_integration="hadolint/hadolint-action",
                required_secrets=[],
                sarif_output=True
            ),
            SecurityCheck(
                name="Container Structure Test",
                description="Container security validation",
                config_files=[".github/security/container-structure-*.yaml"],
                workflow_integration="container-structure-test",
                required_secrets=[],
                sarif_output=False
            ),
            SecurityCheck(
                name="Checkov IaC Security",
                description="Infrastructure as Code security scanning",
                config_files=[".checkov.yaml", ".github/security/checkov-config.yaml"],
                workflow_integration="bridgecrewio/checkov-action",
                required_secrets=[],
                sarif_output=True
            ),
            SecurityCheck(
                name="tfsec Terraform Security",
                description="Terraform security scanning",
                config_files=[".tfsec.yml", ".github/security/tfsec-config.yaml"],
                workflow_integration="aquasecurity/tfsec-action",
                required_secrets=[],
                sarif_output=True
            ),
            SecurityCheck(
                name="Kubesec K8s Security",
                description="Kubernetes security validation",
                config_files=[".github/security/kubesec-policy.yaml"],
                workflow_integration="kubesec",
                required_secrets=[],
                sarif_output=False
            ),
            SecurityCheck(
                name="ESLint Security Plugins",
                description="JavaScript/TypeScript security linting",
                config_files=[".eslintrc.security.json", ".github/security/eslint-security.json"],
                workflow_integration="eslint-plugin-security",
                required_secrets=[],
                sarif_output=False
            ),
            SecurityCheck(
                name="npm audit",
                description="Node.js dependency vulnerability scanning",
                config_files=[".github/security/audit-ci.json", ".npmrc"],
                workflow_integration="audit-ci",
                required_secrets=[],
                sarif_output=False
            )
        ]
    
    def validate_security_pipeline(self) -> Dict[str, Any]:
        """Run comprehensive security pipeline validation"""
        console.print(Panel(
            "🛡️ Security Pipeline Validation\n"
            f"Repository: {self.repo_root}\n"
            f"Security Tools: {len(self.security_checks)} configured",
            title="Security Validator",
            expand=False
        ))
        
        results = {
            "summary": {
                "total_checks": len(self.security_checks),
                "enabled_tools": 0,
                "properly_configured": 0,
                "sarif_enabled": 0,
                "missing_configs": 0,
                "workflow_integrations": 0
            },
            "detailed_results": {},
            "recommendations": [],
            "critical_issues": [],
            "compliance_status": {}
        }
        
        with Progress() as progress:
            task = progress.add_task("[green]Validating security tools...", total=len(self.security_checks))
            
            for security_check in self.security_checks:
                check_result = self._validate_security_tool(security_check)
                results["detailed_results"][security_check.name] = check_result
                
                if check_result["enabled"]:
                    results["summary"]["enabled_tools"] += 1
                if check_result["properly_configured"]:
                    results["summary"]["properly_configured"] += 1
                if check_result["sarif_enabled"]:
                    results["summary"]["sarif_enabled"] += 1
                if not check_result["config_found"]:
                    results["summary"]["missing_configs"] += 1
                if check_result["workflow_integrated"]:
                    results["summary"]["workflow_integrations"] += 1
                
                progress.update(task, advance=1)
        
        # Additional validations
        results["policy_enforcement"] = self._validate_security_policies()
        results["secret_management"] = self._validate_secret_management()
        results["compliance_checks"] = self._validate_compliance_requirements()
        
        return results
    
    def _validate_security_tool(self, security_check: SecurityCheck) -> Dict[str, Any]:
        """Validate individual security tool configuration"""
        result = {
            "enabled": False,
            "properly_configured": False,
            "config_found": False,
            "workflow_integrated": False,
            "sarif_enabled": security_check.sarif_output,
            "required_secrets_configured": False,
            "issues": [],
            "recommendations": [],
            "config_files_found": [],
            "config_files_missing": []
        }
        
        # Check configuration files
        for config_file in security_check.config_files:
            config_path = self.repo_root / config_file
            
            # Handle glob patterns for config files
            if "*" in config_file:
                import glob
                matching_files = glob.glob(str(self.repo_root / config_file))
                if matching_files:
                    result["config_files_found"].extend([Path(f).relative_to(self.repo_root) for f in matching_files])
                    result["config_found"] = True
                else:
                    result["config_files_missing"].append(config_file)
            else:
                if config_path.exists():
                    result["config_files_found"].append(config_file)
                    result["config_found"] = True
                else:
                    result["config_files_missing"].append(config_file)
        
        # Check workflow integration
        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                workflow_content = f.read()
                if security_check.workflow_integration in workflow_content:
                    result["workflow_integrated"] = True
                    result["enabled"] = True
                    break
        
        # Check required secrets
        if security_check.required_secrets:
            configured_secrets = []
            for workflow_file in workflow_files:
                with open(workflow_file, 'r') as f:
                    workflow_content = f.read()
                    for secret in security_check.required_secrets:
                        if f"secrets.{secret}" in workflow_content:
                            configured_secrets.append(secret)
            
            missing_secrets = set(security_check.required_secrets) - set(configured_secrets)
            if not missing_secrets:
                result["required_secrets_configured"] = True
            else:
                result["issues"].append(f"Missing required secrets: {list(missing_secrets)}")
        else:
            result["required_secrets_configured"] = True
        
        # Determine if properly configured
        result["properly_configured"] = (
            result["enabled"] and 
            result["required_secrets_configured"] and
            (result["config_found"] or not security_check.config_files)
        )
        
        # Generate recommendations
        if not result["enabled"]:
            result["recommendations"].append(f"Enable {security_check.name} in CI/CD workflow")
        
        if not result["config_found"] and security_check.config_files:
            result["recommendations"].append(f"Add configuration file(s): {security_check.config_files}")
        
        if not result["required_secrets_configured"]:
            result["recommendations"].append(f"Configure required secrets: {security_check.required_secrets}")
        
        return result
    
    def _validate_security_policies(self) -> Dict[str, Any]:
        """Validate security policy enforcement"""
        policies = {
            "branch_protection": self._check_branch_protection_config(),
            "required_reviews": self._check_required_reviews_config(),
            "status_checks": self._check_status_checks_config(),
            "vulnerability_alerts": self._check_vulnerability_alerts_config(),
            "dependency_updates": self._check_dependency_updates_config()
        }
        
        return {
            "policies": policies,
            "enforcement_score": sum(1 for p in policies.values() if p["enabled"]) / len(policies) * 100
        }
    
    def _check_branch_protection_config(self) -> Dict[str, Any]:
        """Check if branch protection rules are configured"""
        # Look for branch protection configuration in workflows
        protection_found = False
        config_files = []
        
        # Check for GitHub settings files
        github_settings = [
            ".github/settings.yml",
            ".github/branch-protection.yml",
            "docs-dev/BRANCH_PROTECTION_SETUP.md"
        ]
        
        for settings_file in github_settings:
            if (self.repo_root / settings_file).exists():
                protection_found = True
                config_files.append(settings_file)
        
        return {
            "enabled": protection_found,
            "config_files": config_files,
            "recommendation": "Configure branch protection rules" if not protection_found else None
        }
    
    def _check_required_reviews_config(self) -> Dict[str, Any]:
        """Check if required reviews are configured in workflows"""
        review_requirements = []
        
        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                workflow_data = yaml.safe_load(f)
                
                # Check for environment protection rules
                jobs = workflow_data.get('jobs', {})
                for job_name, job_config in jobs.items():
                    if 'environment' in job_config:
                        review_requirements.append(f"Job '{job_name}' uses environment protection")
        
        return {
            "enabled": len(review_requirements) > 0,
            "requirements": review_requirements,
            "recommendation": "Add environment protection for deployment jobs" if not review_requirements else None
        }
    
    def _check_status_checks_config(self) -> Dict[str, Any]:
        """Check if status checks are properly configured"""
        status_checks = []
        
        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                workflow_data = yaml.safe_load(f)
                
                # Look for jobs that should be status checks
                jobs = workflow_data.get('jobs', {})
                for job_name in ['test-frontend', 'test-api', 'security-scan', 'build-images']:
                    if job_name in jobs:
                        status_checks.append(job_name)
        
        return {
            "enabled": len(status_checks) > 0,
            "checks": status_checks,
            "recommendation": "Configure required status checks in branch protection" if len(status_checks) < 3 else None
        }
    
    def _check_vulnerability_alerts_config(self) -> Dict[str, Any]:
        """Check if vulnerability alerts are configured"""
        # Look for dependabot configuration
        dependabot_config = self.repo_root / ".github" / "dependabot.yml"
        
        vulnerability_tools = []
        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
        
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                content = f.read()
                if "snyk" in content.lower() or "audit" in content.lower():
                    vulnerability_tools.append(workflow_file.name)
        
        return {
            "enabled": dependabot_config.exists() or len(vulnerability_tools) > 0,
            "dependabot_configured": dependabot_config.exists(),
            "vulnerability_scanning": vulnerability_tools,
            "recommendation": "Configure Dependabot for automated vulnerability alerts" if not dependabot_config.exists() else None
        }
    
    def _check_dependency_updates_config(self) -> Dict[str, Any]:
        """Check if dependency updates are automated"""
        dependabot_config = self.repo_root / ".github" / "dependabot.yml"
        renovate_config = self.repo_root / ".renovaterc.json"
        
        return {
            "enabled": dependabot_config.exists() or renovate_config.exists(),
            "dependabot": dependabot_config.exists(),
            "renovate": renovate_config.exists(),
            "recommendation": "Configure automated dependency updates" if not (dependabot_config.exists() or renovate_config.exists()) else None
        }
    
    def _validate_secret_management(self) -> Dict[str, Any]:
        """Validate secret management practices"""
        secret_issues = []
        secret_best_practices = []
        
        # Check for hardcoded secrets in workflows
        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
        
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                content = f.read()
                
                # Look for potential hardcoded secrets (very basic check)
                import re
                potential_secrets = re.findall(r'(password|token|key|secret):\s*[\'"]?([^\s\'"]{20,})[\'"]?', content, re.IGNORECASE)
                for match in potential_secrets:
                    if not match[1].startswith('${{'):  # Not a GitHub secret reference
                        secret_issues.append(f"Potential hardcoded secret in {workflow_file.name}: {match[0]}")
                
                # Check for proper secret usage
                secret_references = re.findall(r'\$\{\{\s*secrets\.([A-Z_]+)\s*\}\}', content)
                if secret_references:
                    secret_best_practices.append(f"{workflow_file.name}: Uses GitHub secrets properly")
        
        return {
            "issues": secret_issues,
            "best_practices": secret_best_practices,
            "score": 100 if not secret_issues else max(0, 100 - len(secret_issues) * 20)
        }
    
    def _validate_compliance_requirements(self) -> Dict[str, Any]:
        """Validate compliance with security standards"""
        compliance_frameworks = {
            "OWASP_Top_10": {
                "tools": ["semgrep", "bandit", "eslint-security", "snyk"],
                "coverage": 0
            },
            "SAST_Coverage": {
                "tools": ["codeql", "semgrep", "bandit", "eslint"],
                "coverage": 0
            },
            "DAST_Coverage": {
                "tools": ["zap", "nuclei", "nikto"],  # These would need to be added
                "coverage": 0
            },
            "Container_Security": {
                "tools": ["trivy", "hadolint", "container-structure-test"],
                "coverage": 0
            },
            "IaC_Security": {
                "tools": ["checkov", "tfsec", "kubesec"],
                "coverage": 0
            }
        }
        
        # Calculate coverage for each framework
        for framework, requirements in compliance_frameworks.items():
            enabled_tools = 0
            total_tools = len(requirements["tools"])
            
            workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
            for workflow_file in workflow_files:
                with open(workflow_file, 'r') as f:
                    content = f.read().lower()
                    for tool in requirements["tools"]:
                        if tool in content:
                            enabled_tools += 1
                            break
            
            requirements["coverage"] = (enabled_tools / total_tools) * 100 if total_tools > 0 else 0
        
        overall_compliance = sum(fw["coverage"] for fw in compliance_frameworks.values()) / len(compliance_frameworks)
        
        return {
            "frameworks": compliance_frameworks,
            "overall_score": overall_compliance,
            "recommendations": [
                f"Improve {fw} coverage (currently {compliance_frameworks[fw]['coverage']:.1f}%)"
                for fw in compliance_frameworks
                if compliance_frameworks[fw]["coverage"] < 80
            ]
        }
    
    def generate_security_report(self, results: Dict[str, Any], output_file: Optional[Path] = None) -> str:
        """Generate comprehensive security validation report"""
        
        # Create summary table
        table = Table(title="🛡️ Security Pipeline Analysis")
        table.add_column("Security Tool", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold")
        table.add_column("Configuration", style="dim")
        table.add_column("SARIF Output", justify="center")
        
        for tool_name, tool_result in results["detailed_results"].items():
            status = "✅ Enabled" if tool_result["enabled"] else "❌ Disabled"
            config_status = "✅ Found" if tool_result["config_found"] else "⚠️ Missing"
            sarif_status = "✅" if tool_result["sarif_enabled"] and tool_result["enabled"] else "❌"
            
            table.add_row(tool_name, status, config_status, sarif_status)
        
        console.print(table)
        
        # Security score calculation
        enabled_tools = results["summary"]["enabled_tools"]
        total_tools = results["summary"]["total_checks"]
        security_score = (enabled_tools / total_tools) * 100
        
        # Policy enforcement score
        policy_score = results["policy_enforcement"]["enforcement_score"]
        
        # Compliance score
        compliance_score = results["compliance_checks"]["overall_score"]
        
        # Overall security score
        overall_score = (security_score * 0.4 + policy_score * 0.3 + compliance_score * 0.3)
        
        summary_text = f"""
Security Tools Enabled: {enabled_tools}/{total_tools} ({security_score:.1f}%)
Policy Enforcement: {policy_score:.1f}%
Compliance Coverage: {compliance_score:.1f}%

🔒 Overall Security Score: {overall_score:.1f}%
        """
        
        # Determine overall security status
        if overall_score >= 80:
            panel_style = "green"
            status_emoji = "🛡️"
            status_text = "SECURE"
        elif overall_score >= 60:
            panel_style = "yellow"
            status_emoji = "⚠️"
            status_text = "NEEDS IMPROVEMENT"
        else:
            panel_style = "red"
            status_emoji = "🚨"
            status_text = "CRITICAL ISSUES"
        
        console.print(Panel(
            f"{status_emoji} {status_text}\n{summary_text}",
            title="🔒 Security Assessment",
            style=panel_style,
            expand=False
        ))
        
        # Generate detailed markdown report
        report_content = self._generate_detailed_security_report(results, overall_score)
        
        if output_file:
            output_file.write_text(report_content)
            console.print(f"📄 Detailed security report saved to: {output_file}")
        
        return report_content
    
    def _generate_detailed_security_report(self, results: Dict[str, Any], overall_score: float) -> str:
        """Generate detailed markdown security report"""
        
        report_lines = [
            "# 🛡️ Security Pipeline Validation Report",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
            f"**Repository:** {self.repo_root.name}",
            f"**Overall Security Score:** {overall_score:.1f}%",
            "",
            "## Executive Summary",
            ""
        ]
        
        # Add executive summary
        enabled_tools = results["summary"]["enabled_tools"]
        total_tools = results["summary"]["total_checks"]
        
        if overall_score >= 80:
            status = "✅ **SECURE** - Your security pipeline is well-configured"
        elif overall_score >= 60:
            status = "⚠️ **NEEDS IMPROVEMENT** - Several security gaps identified"
        else:
            status = "🚨 **CRITICAL ISSUES** - Immediate security attention required"
        
        report_lines.extend([
            status,
            "",
            f"- **Security Tools:** {enabled_tools}/{total_tools} enabled ({(enabled_tools/total_tools)*100:.1f}%)",
            f"- **SARIF Integration:** {results['summary']['sarif_enabled']}/{total_tools} tools",
            f"- **Policy Enforcement:** {results['policy_enforcement']['enforcement_score']:.1f}%",
            f"- **Compliance Coverage:** {results['compliance_checks']['overall_score']:.1f}%",
            "",
            "## Security Tools Analysis",
            ""
        ])
        
        # Detailed tool analysis
        for tool_name, tool_result in results["detailed_results"].items():
            status_emoji = "✅" if tool_result["enabled"] else "❌"
            
            report_lines.extend([
                f"### {status_emoji} {tool_name}",
                "",
                f"**Status:** {'Enabled' if tool_result['enabled'] else 'Disabled'}",
                f"**Configuration:** {'Found' if tool_result['config_found'] else 'Missing'}",
                f"**SARIF Output:** {'Enabled' if tool_result['sarif_enabled'] else 'Not Available'}",
                ""
            ])
            
            if tool_result["config_files_found"]:
                report_lines.extend([
                    "**Configuration Files Found:**",
                    ""
                ])
                for config_file in tool_result["config_files_found"]:
                    report_lines.append(f"- ✅ `{config_file}`")
                report_lines.append("")
            
            if tool_result["config_files_missing"]:
                report_lines.extend([
                    "**Missing Configuration Files:**",
                    ""
                ])
                for config_file in tool_result["config_files_missing"]:
                    report_lines.append(f"- ❌ `{config_file}`")
                report_lines.append("")
            
            if tool_result["issues"]:
                report_lines.extend([
                    "**Issues:**",
                    ""
                ])
                for issue in tool_result["issues"]:
                    report_lines.append(f"- ⚠️ {issue}")
                report_lines.append("")
            
            if tool_result["recommendations"]:
                report_lines.extend([
                    "**Recommendations:**",
                    ""
                ])
                for rec in tool_result["recommendations"]:
                    report_lines.append(f"- 💡 {rec}")
                report_lines.append("")
            
            report_lines.append("---")
            report_lines.append("")
        
        # Policy enforcement section
        report_lines.extend([
            "## Security Policy Enforcement",
            "",
            f"**Overall Policy Score:** {results['policy_enforcement']['enforcement_score']:.1f}%",
            ""
        ])
        
        for policy_name, policy_result in results["policy_enforcement"]["policies"].items():
            status_emoji = "✅" if policy_result["enabled"] else "❌"
            report_lines.extend([
                f"### {status_emoji} {policy_name.replace('_', ' ').title()}",
                ""
            ])
            
            if policy_result.get("recommendation"):
                report_lines.extend([
                    f"**Recommendation:** {policy_result['recommendation']}",
                    ""
                ])
        
        # Compliance section
        report_lines.extend([
            "## Compliance Framework Coverage",
            "",
            f"**Overall Compliance Score:** {results['compliance_checks']['overall_score']:.1f}%",
            ""
        ])
        
        for framework, details in results["compliance_checks"]["frameworks"].items():
            coverage_emoji = "✅" if details["coverage"] >= 80 else "⚠️" if details["coverage"] >= 50 else "❌"
            report_lines.extend([
                f"### {coverage_emoji} {framework.replace('_', ' ')}",
                f"**Coverage:** {details['coverage']:.1f}%",
                f"**Required Tools:** {', '.join(details['tools'])}",
                ""
            ])
        
        # Recommendations section
        all_recommendations = []
        
        # Collect recommendations from all tools
        for tool_result in results["detailed_results"].values():
            all_recommendations.extend(tool_result.get("recommendations", []))
        
        # Add compliance recommendations
        all_recommendations.extend(results["compliance_checks"].get("recommendations", []))
        
        if all_recommendations:
            report_lines.extend([
                "## 🚀 Priority Recommendations",
                ""
            ])
            
            for i, rec in enumerate(all_recommendations[:10], 1):  # Top 10 recommendations
                report_lines.append(f"{i}. {rec}")
            
            report_lines.append("")
        
        # Action items
        report_lines.extend([
            "## ✅ Next Steps",
            "",
            "1. **Immediate Actions:**",
            "   - Enable critical security tools that are currently disabled",
            "   - Configure missing SARIF uploads for security reporting",
            "   - Add required secret configurations",
            "",
            "2. **Short-term Improvements:**",
            "   - Implement missing security policies",
            "   - Add comprehensive security configuration files",
            "   - Enhance compliance framework coverage",
            "",
            "3. **Long-term Security Strategy:**",
            "   - Regular security pipeline reviews",
            "   - Automated security policy enforcement",
            "   - Continuous compliance monitoring",
            ""
        ])
        
        return "\n".join(report_lines)

def main():
    parser = argparse.ArgumentParser(description="Validate Security Pipeline Configuration")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(),
                       help="Repository root directory (default: current directory)")
    parser.add_argument("--output", type=Path,
                       help="Output file for detailed report")
    parser.add_argument("--json", action="store_true",
                       help="Output results in JSON format")
    parser.add_argument("--fail-threshold", type=float, default=60.0,
                       help="Fail if security score below threshold (default: 60.0)")
    
    args = parser.parse_args()
    
    # Validate repository root
    if not (args.repo_root / ".github" / "workflows").exists():
        console.print("❌ Error: .github/workflows directory not found", style="red")
        sys.exit(1)
    
    # Run validation
    validator = SecurityValidator(args.repo_root)
    results = validator.validate_security_pipeline()
    
    if args.json:
        # Output JSON results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
        else:
            print(json.dumps(results, indent=2))
    else:
        # Generate formatted report
        validator.generate_security_report(results, args.output)
    
    # Calculate overall score and exit appropriately
    enabled_tools = results["summary"]["enabled_tools"]
    total_tools = results["summary"]["total_checks"]
    security_score = (enabled_tools / total_tools) * 100
    policy_score = results["policy_enforcement"]["enforcement_score"]
    compliance_score = results["compliance_checks"]["overall_score"]
    overall_score = (security_score * 0.4 + policy_score * 0.3 + compliance_score * 0.3)
    
    if overall_score < args.fail_threshold:
        console.print(f"\n🚨 Security validation failed: {overall_score:.1f}% < {args.fail_threshold}%", style="red")
        sys.exit(1)
    else:
        console.print(f"\n✅ Security validation passed: {overall_score:.1f}% >= {args.fail_threshold}%", style="green")
        sys.exit(0)

if __name__ == "__main__":
    main()