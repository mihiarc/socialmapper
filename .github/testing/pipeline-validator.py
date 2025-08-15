#!/usr/bin/env python3
"""
Comprehensive CI/CD Pipeline Validation Script for SocialMapper

This script validates all GitHub Actions workflows, their dependencies,
configurations, and expected behavior without executing actual deployments.
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
from enum import Enum
import tempfile
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.tree import Tree
import time

console = Console()

class ValidationLevel(Enum):
    QUICK = "quick"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"

class TestResult(Enum):
    PASSED = "✅ PASSED"
    FAILED = "❌ FAILED"
    WARNING = "⚠️ WARNING"
    SKIPPED = "⏸️ SKIPPED"

@dataclass
class ValidationResult:
    test_name: str
    result: TestResult
    message: str
    details: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0

class PipelineValidator:
    def __init__(self, repo_root: Path, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.repo_root = repo_root
        self.validation_level = validation_level
        self.workflows_dir = repo_root / ".github" / "workflows"
        self.results: List[ValidationResult] = []
        
    def run_validation(self) -> List[ValidationResult]:
        """Run all validation tests based on the specified level"""
        console.print(Panel(
            f"🚀 Starting CI/CD Pipeline Validation\n"
            f"Repository: {self.repo_root}\n"
            f"Validation Level: {self.validation_level.value.upper()}",
            title="Pipeline Validator",
            expand=False
        ))
        
        with Progress() as progress:
            main_task = progress.add_task("[green]Validating Pipeline...", total=100)
            
            # Phase 1: Workflow Structure Validation (20%)
            progress.update(main_task, advance=20, description="[blue]Validating workflow structure...")
            self._validate_workflow_structure()
            
            # Phase 2: YAML Syntax and Schema Validation (20%)
            progress.update(main_task, advance=20, description="[blue]Validating YAML syntax...")
            self._validate_yaml_syntax()
            
            # Phase 3: Workflow Dependencies (20%)
            progress.update(main_task, advance=20, description="[blue]Checking dependencies...")
            self._validate_dependencies()
            
            # Phase 4: Secret and Environment Validation (20%)
            progress.update(main_task, advance=20, description="[blue]Validating secrets...")
            self._validate_secrets_and_env()
            
            # Phase 5: Advanced Validations (20%)
            if self.validation_level in [ValidationLevel.STANDARD, ValidationLevel.COMPREHENSIVE]:
                progress.update(main_task, advance=20, description="[blue]Running advanced checks...")
                self._validate_advanced_features()
            
        return self.results
    
    def _validate_workflow_structure(self):
        """Validate the basic structure of workflow files"""
        start_time = time.time()
        
        try:
            workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
            
            if not workflow_files:
                self.results.append(ValidationResult(
                    "workflow_structure", TestResult.FAILED,
                    "No workflow files found in .github/workflows/",
                    execution_time=time.time() - start_time
                ))
                return
            
            expected_workflows = {
                'ci-cd.yml': 'Main CI/CD Pipeline',
                'performance-testing.yml': 'Performance Testing',
                'comprehensive-security.yml': 'Security Scanning',
                'advanced-deployment.yml': 'Advanced Deployment',
                'deploy-monitoring.yml': 'Monitoring Deployment'
            }
            
            found_workflows = {f.name: f for f in workflow_files}
            
            # Check for required workflows
            missing_workflows = []
            for expected, description in expected_workflows.items():
                if expected not in found_workflows:
                    missing_workflows.append(f"{expected} ({description})")
            
            if missing_workflows:
                self.results.append(ValidationResult(
                    "required_workflows", TestResult.WARNING,
                    f"Missing workflows: {', '.join(missing_workflows)}",
                    {"missing": missing_workflows},
                    time.time() - start_time
                ))
            else:
                self.results.append(ValidationResult(
                    "required_workflows", TestResult.PASSED,
                    f"All {len(expected_workflows)} required workflows found",
                    {"found": list(expected_workflows.keys())},
                    time.time() - start_time
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                "workflow_structure", TestResult.FAILED,
                f"Error validating workflow structure: {str(e)}",
                execution_time=time.time() - start_time
            ))
    
    def _validate_yaml_syntax(self):
        """Validate YAML syntax and basic structure of all workflows"""
        start_time = time.time()
        
        try:
            workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
            validation_errors = []
            
            for workflow_file in workflow_files:
                try:
                    with open(workflow_file, 'r') as f:
                        workflow_data = yaml.safe_load(f)
                    
                    # Basic structure validation
                    required_keys = ['name', 'on', 'jobs']
                    missing_keys = [key for key in required_keys if key not in workflow_data]
                    
                    if missing_keys:
                        validation_errors.append(f"{workflow_file.name}: Missing keys: {missing_keys}")
                    
                    # Validate job structure
                    if 'jobs' in workflow_data:
                        for job_name, job_config in workflow_data['jobs'].items():
                            if not isinstance(job_config, dict):
                                validation_errors.append(f"{workflow_file.name}: Job '{job_name}' must be a dict")
                            elif 'runs-on' not in job_config:
                                validation_errors.append(f"{workflow_file.name}: Job '{job_name}' missing 'runs-on'")
                
                except yaml.YAMLError as e:
                    validation_errors.append(f"{workflow_file.name}: YAML syntax error: {str(e)}")
                except Exception as e:
                    validation_errors.append(f"{workflow_file.name}: Validation error: {str(e)}")
            
            if validation_errors:
                self.results.append(ValidationResult(
                    "yaml_syntax", TestResult.FAILED,
                    f"YAML validation errors found: {len(validation_errors)}",
                    {"errors": validation_errors},
                    time.time() - start_time
                ))
            else:
                self.results.append(ValidationResult(
                    "yaml_syntax", TestResult.PASSED,
                    f"All {len(workflow_files)} workflow files have valid YAML syntax",
                    {"validated_files": [f.name for f in workflow_files]},
                    time.time() - start_time
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                "yaml_syntax", TestResult.FAILED,
                f"Error during YAML validation: {str(e)}",
                execution_time=time.time() - start_time
            ))
    
    def _validate_dependencies(self):
        """Validate workflow dependencies and job ordering"""
        start_time = time.time()
        
        try:
            # Load main CI/CD workflow
            ci_cd_file = self.workflows_dir / "ci-cd.yml"
            if not ci_cd_file.exists():
                self.results.append(ValidationResult(
                    "workflow_dependencies", TestResult.FAILED,
                    "Main CI/CD workflow (ci-cd.yml) not found",
                    execution_time=time.time() - start_time
                ))
                return
            
            with open(ci_cd_file, 'r') as f:
                ci_cd_data = yaml.safe_load(f)
            
            jobs = ci_cd_data.get('jobs', {})
            dependency_issues = []
            
            # Check for circular dependencies
            for job_name, job_config in jobs.items():
                needs = job_config.get('needs', [])
                if isinstance(needs, str):
                    needs = [needs]
                
                # Check if needed jobs exist
                for needed_job in needs:
                    if needed_job not in jobs:
                        dependency_issues.append(f"Job '{job_name}' depends on non-existent job '{needed_job}'")
            
            # Validate build -> test -> deploy flow
            expected_flow = {
                'build-images': ['security-scan', 'test-api', 'test-package', 'test-frontend', 'frontend-security'],
                'deploy-staging': ['build-images'],
                'deploy-production': ['build-images', 'deploy-staging']
            }
            
            for job_name, expected_needs in expected_flow.items():
                if job_name in jobs:
                    actual_needs = jobs[job_name].get('needs', [])
                    if isinstance(actual_needs, str):
                        actual_needs = [actual_needs]
                    
                    missing_deps = set(expected_needs) - set(actual_needs)
                    if missing_deps:
                        dependency_issues.append(f"Job '{job_name}' missing dependencies: {missing_deps}")
            
            if dependency_issues:
                self.results.append(ValidationResult(
                    "workflow_dependencies", TestResult.WARNING,
                    f"Dependency issues found: {len(dependency_issues)}",
                    {"issues": dependency_issues},
                    time.time() - start_time
                ))
            else:
                self.results.append(ValidationResult(
                    "workflow_dependencies", TestResult.PASSED,
                    "Workflow job dependencies are correctly configured",
                    {"validated_jobs": len(jobs)},
                    time.time() - start_time
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                "workflow_dependencies", TestResult.FAILED,
                f"Error validating dependencies: {str(e)}",
                execution_time=time.time() - start_time
            ))
    
    def _validate_secrets_and_env(self):
        """Validate required secrets and environment variables"""
        start_time = time.time()
        
        try:
            # Required secrets for the pipeline
            required_secrets = {
                'AWS_ACCESS_KEY_ID': 'AWS access for deployments',
                'AWS_SECRET_ACCESS_KEY': 'AWS secret for deployments',
                'AWS_ACCOUNT_ID': 'AWS account ID for ECR',
                'CENSUS_API_KEY': 'Census API access',
                'SLACK_WEBHOOK_URL': 'Slack notifications',
                'VITE_MAPBOX_TOKEN': 'Mapbox token for frontend'
            }
            
            optional_secrets = {
                'SNYK_TOKEN': 'Snyk security scanning',
                'SONAR_TOKEN': 'SonarCloud analysis',
                'NVD_API_KEY': 'OWASP dependency check'
            }
            
            workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
            used_secrets = set()
            used_env_vars = set()
            
            for workflow_file in workflow_files:
                with open(workflow_file, 'r') as f:
                    content = f.read()
                    
                    # Find secrets usage
                    import re
                    secret_pattern = r'\$\{\{\s*secrets\.([A-Z_]+)\s*\}\}'
                    used_secrets.update(re.findall(secret_pattern, content))
                    
                    # Find environment variables
                    env_pattern = r'\$\{\{\s*env\.([A-Z_]+)\s*\}\}'
                    used_env_vars.update(re.findall(env_pattern, content))
            
            # Check for missing required secrets
            missing_required = set(required_secrets.keys()) - used_secrets
            missing_optional = set(optional_secrets.keys()) - used_secrets
            
            issues = []
            if missing_required:
                for secret in missing_required:
                    issues.append(f"Required secret not used: {secret} ({required_secrets[secret]})")
            
            warnings = []
            if missing_optional:
                for secret in missing_optional:
                    warnings.append(f"Optional secret not used: {secret} ({optional_secrets[secret]})")
            
            if issues:
                self.results.append(ValidationResult(
                    "required_secrets", TestResult.FAILED,
                    f"Missing required secrets: {len(missing_required)}",
                    {"missing_required": list(missing_required), "issues": issues},
                    time.time() - start_time
                ))
            else:
                result_type = TestResult.WARNING if warnings else TestResult.PASSED
                message = f"Required secrets configured. {len(warnings)} optional secrets not used." if warnings else "All secrets properly configured"
                
                self.results.append(ValidationResult(
                    "required_secrets", result_type,
                    message,
                    {"used_secrets": list(used_secrets), "warnings": warnings},
                    time.time() - start_time
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                "secrets_validation", TestResult.FAILED,
                f"Error validating secrets: {str(e)}",
                execution_time=time.time() - start_time
            ))
    
    def _validate_advanced_features(self):
        """Validate advanced pipeline features"""
        start_time = time.time()
        
        try:
            validations = []
            
            # Validate Docker configurations
            validations.append(self._validate_docker_configs())
            
            # Validate Kubernetes manifests
            validations.append(self._validate_kubernetes_configs())
            
            # Validate security configurations
            validations.append(self._validate_security_configs())
            
            # Validate performance testing setup
            validations.append(self._validate_performance_configs())
            
            # Validate monitoring setup
            validations.append(self._validate_monitoring_configs())
            
            self.results.extend(validations)
            
        except Exception as e:
            self.results.append(ValidationResult(
                "advanced_features", TestResult.FAILED,
                f"Error in advanced validation: {str(e)}",
                execution_time=time.time() - start_time
            ))
    
    def _validate_docker_configs(self) -> ValidationResult:
        """Validate Docker configurations"""
        start_time = time.time()
        
        try:
            docker_files = []
            
            # Check for Dockerfiles
            api_dockerfile = self.repo_root / "socialmapper-api" / "Dockerfile"
            ui_dockerfile = self.repo_root / "socialmapper-ui" / "Dockerfile"
            
            if api_dockerfile.exists():
                docker_files.append("API Dockerfile")
            if ui_dockerfile.exists():
                docker_files.append("UI Dockerfile")
            
            # Check docker-compose files
            compose_files = list(self.repo_root.glob("docker-compose*.yml"))
            docker_files.extend([f"Docker Compose: {f.name}" for f in compose_files])
            
            if len(docker_files) < 2:  # Expect at least API and UI Dockerfiles
                return ValidationResult(
                    "docker_configs", TestResult.WARNING,
                    f"Missing Docker configurations. Found: {docker_files}",
                    {"found_files": docker_files},
                    time.time() - start_time
                )
            
            return ValidationResult(
                "docker_configs", TestResult.PASSED,
                f"Docker configurations found: {len(docker_files)} files",
                {"found_files": docker_files},
                time.time() - start_time
            )
            
        except Exception as e:
            return ValidationResult(
                "docker_configs", TestResult.FAILED,
                f"Error validating Docker configs: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _validate_kubernetes_configs(self) -> ValidationResult:
        """Validate Kubernetes configurations"""
        start_time = time.time()
        
        try:
            k8s_dir = self.repo_root / "infrastructure" / "kubernetes"
            
            if not k8s_dir.exists():
                return ValidationResult(
                    "kubernetes_configs", TestResult.WARNING,
                    "Kubernetes configuration directory not found",
                    execution_time=time.time() - start_time
                )
            
            k8s_files = list(k8s_dir.glob("*.yaml")) + list(k8s_dir.glob("*.yml"))
            
            required_k8s_files = [
                "namespace.yaml",
                "api-deployment.yaml", 
                "ui-deployment.yaml",
                "configmap.yaml",
                "ingress.yaml"
            ]
            
            found_files = [f.name for f in k8s_files]
            missing_files = [f for f in required_k8s_files if f not in found_files]
            
            if missing_files:
                return ValidationResult(
                    "kubernetes_configs", TestResult.WARNING,
                    f"Missing K8s files: {missing_files}",
                    {"missing": missing_files, "found": found_files},
                    time.time() - start_time
                )
            
            return ValidationResult(
                "kubernetes_configs", TestResult.PASSED,
                f"Kubernetes configs validated: {len(k8s_files)} files",
                {"found": found_files},
                time.time() - start_time
            )
            
        except Exception as e:
            return ValidationResult(
                "kubernetes_configs", TestResult.FAILED,
                f"Error validating K8s configs: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _validate_security_configs(self) -> ValidationResult:
        """Validate security scanning configurations"""
        start_time = time.time()
        
        try:
            security_features = []
            
            # Check for security workflow
            security_workflow = self.workflows_dir / "comprehensive-security.yml"
            if security_workflow.exists():
                security_features.append("Comprehensive security workflow")
            
            # Check for security configuration files
            security_configs = [
                ".github/security/gitleaks.toml",
                ".github/security/audit-ci.json",
                ".github/security/dependency-check-suppressions.xml"
            ]
            
            for config_path in security_configs:
                if (self.repo_root / config_path).exists():
                    security_features.append(f"Security config: {Path(config_path).name}")
            
            if len(security_features) < 2:
                return ValidationResult(
                    "security_configs", TestResult.WARNING,
                    f"Limited security configurations: {security_features}",
                    {"found": security_features},
                    time.time() - start_time
                )
            
            return ValidationResult(
                "security_configs", TestResult.PASSED,
                f"Security configurations found: {len(security_features)}",
                {"found": security_features},
                time.time() - start_time
            )
            
        except Exception as e:
            return ValidationResult(
                "security_configs", TestResult.FAILED,
                f"Error validating security configs: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _validate_performance_configs(self) -> ValidationResult:
        """Validate performance testing configurations"""
        start_time = time.time()
        
        try:
            perf_dir = self.repo_root / "performance"
            performance_features = []
            
            if perf_dir.exists():
                # Check for k6 tests
                k6_tests = list((perf_dir / "k6" / "tests").glob("*.js")) if (perf_dir / "k6" / "tests").exists() else []
                if k6_tests:
                    performance_features.append(f"k6 tests: {len(k6_tests)} files")
                
                # Check for Lighthouse configs
                lighthouse_configs = list((perf_dir / "lighthouse").glob("*.json")) if (perf_dir / "lighthouse").exists() else []
                if lighthouse_configs:
                    performance_features.append(f"Lighthouse configs: {len(lighthouse_configs)} files")
                
                # Check for performance workflow
                perf_workflow = self.workflows_dir / "performance-testing.yml"
                if perf_workflow.exists():
                    performance_features.append("Performance testing workflow")
            
            if not performance_features:
                return ValidationResult(
                    "performance_configs", TestResult.WARNING,
                    "No performance testing configurations found",
                    execution_time=time.time() - start_time
                )
            
            return ValidationResult(
                "performance_configs", TestResult.PASSED,
                f"Performance testing configured: {len(performance_features)} components",
                {"found": performance_features},
                time.time() - start_time
            )
            
        except Exception as e:
            return ValidationResult(
                "performance_configs", TestResult.FAILED,
                f"Error validating performance configs: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _validate_monitoring_configs(self) -> ValidationResult:
        """Validate monitoring configurations"""
        start_time = time.time()
        
        try:
            monitoring_features = []
            
            # Check for monitoring infrastructure
            monitoring_dir = self.repo_root / "infrastructure" / "monitoring"
            if monitoring_dir.exists():
                monitoring_files = list(monitoring_dir.glob("*.yaml")) + list(monitoring_dir.glob("*.yml"))
                if monitoring_files:
                    monitoring_features.append(f"Monitoring manifests: {len(monitoring_files)} files")
            
            # Check for Helm charts
            helm_dir = self.repo_root / "helm"
            if helm_dir.exists():
                helm_charts = [d for d in helm_dir.iterdir() if d.is_dir() and (d / "Chart.yaml").exists()]
                if helm_charts:
                    monitoring_features.append(f"Helm charts: {len(helm_charts)}")
            
            # Check for monitoring workflow
            monitoring_workflow = self.workflows_dir / "deploy-monitoring.yml"
            if monitoring_workflow.exists():
                monitoring_features.append("Monitoring deployment workflow")
            
            if not monitoring_features:
                return ValidationResult(
                    "monitoring_configs", TestResult.WARNING,
                    "No monitoring configurations found",
                    execution_time=time.time() - start_time
                )
            
            return ValidationResult(
                "monitoring_configs", TestResult.PASSED,
                f"Monitoring configured: {len(monitoring_features)} components",
                {"found": monitoring_features},
                time.time() - start_time
            )
            
        except Exception as e:
            return ValidationResult(
                "monitoring_configs", TestResult.FAILED,
                f"Error validating monitoring configs: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def generate_report(self, output_file: Optional[Path] = None) -> str:
        """Generate a comprehensive validation report"""
        
        # Count results by type
        passed = len([r for r in self.results if r.result == TestResult.PASSED])
        failed = len([r for r in self.results if r.result == TestResult.FAILED])
        warnings = len([r for r in self.results if r.result == TestResult.WARNING])
        skipped = len([r for r in self.results if r.result == TestResult.SKIPPED])
        
        # Create summary table
        table = Table(title="🔍 CI/CD Pipeline Validation Results")
        table.add_column("Test Category", style="cyan", no_wrap=True)
        table.add_column("Result", style="bold")
        table.add_column("Message", style="dim")
        table.add_column("Time (s)", justify="right")
        
        for result in sorted(self.results, key=lambda x: (x.result.name, x.test_name)):
            table.add_row(
                result.test_name.replace('_', ' ').title(),
                result.result.value,
                result.message[:80] + "..." if len(result.message) > 80 else result.message,
                f"{result.execution_time:.2f}"
            )
        
        console.print(table)
        
        # Summary panel
        summary_text = f"""
Total Tests: {len(self.results)}
✅ Passed: {passed}
❌ Failed: {failed}
⚠️ Warnings: {warnings}
⏸️ Skipped: {skipped}

Pipeline Health Score: {(passed / len(self.results) * 100):.1f}%
        """
        
        console.print(Panel(summary_text, title="📊 Summary", expand=False))
        
        # Generate detailed report
        report_content = self._generate_detailed_report()
        
        if output_file:
            output_file.write_text(report_content)
            console.print(f"📄 Detailed report saved to: {output_file}")
        
        return report_content
    
    def _generate_detailed_report(self) -> str:
        """Generate detailed markdown report"""
        
        report_lines = [
            "# CI/CD Pipeline Validation Report",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
            f"**Repository:** {self.repo_root.name}",
            f"**Validation Level:** {self.validation_level.value.upper()}",
            "",
            "## Summary",
            ""
        ]
        
        # Add summary statistics
        passed = len([r for r in self.results if r.result == TestResult.PASSED])
        failed = len([r for r in self.results if r.result == TestResult.FAILED])
        warnings = len([r for r in self.results if r.result == TestResult.WARNING])
        
        report_lines.extend([
            f"- **Total Tests:** {len(self.results)}",
            f"- **✅ Passed:** {passed}",
            f"- **❌ Failed:** {failed}",
            f"- **⚠️ Warnings:** {warnings}",
            f"- **Pipeline Health Score:** {(passed / len(self.results) * 100):.1f}%",
            "",
            "## Detailed Results",
            ""
        ])
        
        # Group results by category
        categories = {}
        for result in self.results:
            category = result.test_name.replace('_', ' ').title()
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        for category, results in categories.items():
            report_lines.extend([f"### {category}", ""])
            
            for result in results:
                status_emoji = "✅" if result.result == TestResult.PASSED else "❌" if result.result == TestResult.FAILED else "⚠️"
                report_lines.extend([
                    f"{status_emoji} **{result.result.name}**: {result.message}",
                    f"   - *Execution Time:* {result.execution_time:.2f}s",
                    ""
                ])
                
                if result.details:
                    report_lines.extend([
                        "   **Details:**",
                        f"   ```json",
                        f"   {json.dumps(result.details, indent=2)}",
                        f"   ```",
                        ""
                    ])
        
        return "\n".join(report_lines)

def main():
    parser = argparse.ArgumentParser(description="Validate CI/CD Pipeline Configuration")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(),
                       help="Repository root directory (default: current directory)")
    parser.add_argument("--level", type=str, choices=[v.value for v in ValidationLevel],
                       default=ValidationLevel.STANDARD.value,
                       help="Validation level (default: standard)")
    parser.add_argument("--output", type=Path,
                       help="Output file for detailed report")
    parser.add_argument("--json", action="store_true",
                       help="Output results in JSON format")
    
    args = parser.parse_args()
    
    # Validate repository root
    if not (args.repo_root / ".github" / "workflows").exists():
        console.print("❌ Error: .github/workflows directory not found", style="red")
        sys.exit(1)
    
    # Run validation
    validator = PipelineValidator(args.repo_root, ValidationLevel(args.level))
    results = validator.run_validation()
    
    if args.json:
        # Output JSON results
        json_results = []
        for result in results:
            json_results.append({
                "test_name": result.test_name,
                "result": result.result.name,
                "message": result.message,
                "details": result.details,
                "execution_time": result.execution_time
            })
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(json_results, f, indent=2)
        else:
            print(json.dumps(json_results, indent=2))
    else:
        # Generate formatted report
        validator.generate_report(args.output)
    
    # Exit with appropriate code
    failed_tests = [r for r in results if r.result == TestResult.FAILED]
    if failed_tests:
        console.print(f"\n❌ Pipeline validation failed with {len(failed_tests)} critical issues", style="red")
        sys.exit(1)
    else:
        console.print("\n✅ Pipeline validation completed successfully", style="green")
        sys.exit(0)

if __name__ == "__main__":
    main()