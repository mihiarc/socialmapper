#!/usr/bin/env python3
"""
Performance Testing Pipeline Validation Script

Validates k6 load testing, Lighthouse CI, and performance monitoring
configurations in the CI/CD pipeline.
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
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

console = Console()

@dataclass
class PerformanceTest:
    name: str
    test_type: str  # 'k6', 'lighthouse', 'artillery', 'jmeter'
    config_files: List[str]
    test_files: List[str]
    thresholds_defined: bool
    reporting_configured: bool
    ci_integration: bool

class PerformanceValidator:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.performance_dir = repo_root / "performance"
        self.workflows_dir = repo_root / ".github" / "workflows"
        
    def validate_performance_pipeline(self) -> Dict[str, Any]:
        """Run comprehensive performance pipeline validation"""
        console.print(Panel(
            "⚡ Performance Testing Pipeline Validation\n"
            f"Repository: {self.repo_root}\n"
            f"Performance Directory: {self.performance_dir}",
            title="Performance Validator",
            expand=False
        ))
        
        results = {
            "summary": {
                "k6_tests": 0,
                "lighthouse_configs": 0,
                "performance_budgets": 0,
                "monitoring_dashboards": 0,
                "ci_integration": False,
                "thresholds_configured": False
            },
            "k6_validation": {},
            "lighthouse_validation": {},
            "monitoring_validation": {},
            "ci_integration": {},
            "performance_budgets": {},
            "recommendations": [],
            "critical_issues": []
        }
        
        with Progress() as progress:
            task = progress.add_task("[green]Validating performance tools...", total=6)
            
            # Validate k6 configuration
            progress.update(task, advance=1, description="[blue]Validating k6 tests...")
            results["k6_validation"] = self._validate_k6_setup()
            results["summary"]["k6_tests"] = results["k6_validation"].get("test_count", 0)
            
            # Validate Lighthouse CI configuration
            progress.update(task, advance=1, description="[blue]Validating Lighthouse CI...")
            results["lighthouse_validation"] = self._validate_lighthouse_setup()
            results["summary"]["lighthouse_configs"] = len(results["lighthouse_validation"].get("config_files", []))
            
            # Validate performance monitoring
            progress.update(task, advance=1, description="[blue]Validating monitoring...")
            results["monitoring_validation"] = self._validate_monitoring_setup()
            results["summary"]["monitoring_dashboards"] = len(results["monitoring_validation"].get("dashboards", []))
            
            # Validate CI integration
            progress.update(task, advance=1, description="[blue]Validating CI integration...")
            results["ci_integration"] = self._validate_ci_integration()
            results["summary"]["ci_integration"] = results["ci_integration"].get("properly_integrated", False)
            
            # Validate performance budgets
            progress.update(task, advance=1, description="[blue]Validating performance budgets...")
            results["performance_budgets"] = self._validate_performance_budgets()
            results["summary"]["performance_budgets"] = len(results["performance_budgets"].get("budget_files", []))
            
            # Validate thresholds and alerting
            progress.update(task, advance=1, description="[blue]Validating thresholds...")
            results["thresholds"] = self._validate_thresholds()
            results["summary"]["thresholds_configured"] = results["thresholds"].get("configured", False)
        
        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results)
        results["critical_issues"] = self._identify_critical_issues(results)
        
        return results
    
    def _validate_k6_setup(self) -> Dict[str, Any]:
        """Validate k6 load testing configuration"""
        k6_dir = self.performance_dir / "k6"
        
        validation = {
            "k6_directory_exists": k6_dir.exists(),
            "test_files": [],
            "config_files": [],
            "test_count": 0,
            "test_types": [],
            "thresholds_defined": False,
            "helper_functions": False,
            "environment_configs": [],
            "issues": [],
            "recommendations": []
        }
        
        if not k6_dir.exists():
            validation["issues"].append("k6 directory not found")
            validation["recommendations"].append("Create performance/k6 directory structure")
            return validation
        
        # Check for test files
        tests_dir = k6_dir / "tests"
        if tests_dir.exists():
            test_files = list(tests_dir.glob("*.js"))
            validation["test_files"] = [f.name for f in test_files]
            validation["test_count"] = len(test_files)
            
            # Analyze test content
            for test_file in test_files:
                try:
                    with open(test_file, 'r') as f:
                        content = f.read()
                        
                        # Check for different test types
                        if "stages" in content:
                            validation["test_types"].append("load")
                        if "spike" in content.lower():
                            validation["test_types"].append("spike")
                        if "stress" in content.lower():
                            validation["test_types"].append("stress")
                        if "soak" in content.lower():
                            validation["test_types"].append("soak")
                        
                        # Check for thresholds
                        if "thresholds" in content:
                            validation["thresholds_defined"] = True
                        
                        # Check for helper functions
                        if "utils/helpers" in content or "import" in content:
                            validation["helper_functions"] = True
                            
                except Exception as e:
                    validation["issues"].append(f"Error reading {test_file.name}: {str(e)}")
        
        # Check for configuration files
        config_dir = k6_dir / "config"
        if config_dir.exists():
            config_files = list(config_dir.glob("*.js")) + list(config_dir.glob("*.json"))
            validation["config_files"] = [f.name for f in config_files]
        
        # Check for utils/helpers
        utils_dir = k6_dir / "utils"
        if utils_dir.exists():
            validation["helper_functions"] = True
        
        # Check for environment-specific configurations
        if "TEST_ENV" in str(k6_dir):
            validation["environment_configs"].append("environment variable support")
        
        # Generate recommendations
        if validation["test_count"] == 0:
            validation["recommendations"].append("Add k6 test files for load, stress, and spike testing")
        
        if not validation["thresholds_defined"]:
            validation["recommendations"].append("Define performance thresholds in k6 tests")
        
        if validation["test_count"] < 3:
            validation["recommendations"].append("Add tests for different load patterns (load, stress, spike)")
        
        return validation
    
    def _validate_lighthouse_setup(self) -> Dict[str, Any]:
        """Validate Lighthouse CI configuration"""
        lighthouse_dir = self.performance_dir / "lighthouse"
        
        validation = {
            "lighthouse_directory_exists": lighthouse_dir.exists(),
            "config_files": [],
            "budget_files": [],
            "ci_integration": False,
            "mobile_config": False,
            "desktop_config": False,
            "performance_budgets": False,
            "issues": [],
            "recommendations": []
        }
        
        if not lighthouse_dir.exists():
            validation["issues"].append("Lighthouse directory not found")
            validation["recommendations"].append("Create performance/lighthouse directory")
            return validation
        
        # Check for Lighthouse configuration files
        config_files = [
            "lighthouserc.json",
            "lighthouse.config.js",
            "mobile-config.json",
            "desktop-config.json"
        ]
        
        for config_file in config_files:
            config_path = lighthouse_dir / config_file
            if config_path.exists():
                validation["config_files"].append(config_file)
                
                if "mobile" in config_file:
                    validation["mobile_config"] = True
                if "desktop" in config_file or "lighthouserc" in config_file:
                    validation["desktop_config"] = True
                
                # Analyze configuration content
                try:
                    with open(config_path, 'r') as f:
                        content = f.read()
                        if "budgets" in content or "budget" in content:
                            validation["performance_budgets"] = True
                except Exception as e:
                    validation["issues"].append(f"Error reading {config_file}: {str(e)}")
        
        # Check for budget files
        budget_files = ["budget.json", "performance-budget.json"]
        for budget_file in budget_files:
            budget_path = lighthouse_dir / budget_file
            if budget_path.exists():
                validation["budget_files"].append(budget_file)
                validation["performance_budgets"] = True
        
        # Check CI integration (look for workflow integration)
        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                content = f.read()
                if "lighthouse" in content.lower() or "@lhci/cli" in content:
                    validation["ci_integration"] = True
                    break
        
        # Generate recommendations
        if not validation["config_files"]:
            validation["recommendations"].append("Add Lighthouse CI configuration files")
        
        if not validation["performance_budgets"]:
            validation["recommendations"].append("Define performance budgets for Lighthouse")
        
        if not validation["mobile_config"]:
            validation["recommendations"].append("Add mobile-specific Lighthouse configuration")
        
        if not validation["ci_integration"]:
            validation["recommendations"].append("Integrate Lighthouse CI into GitHub Actions workflow")
        
        return validation
    
    def _validate_monitoring_setup(self) -> Dict[str, Any]:
        """Validate performance monitoring configuration"""
        monitoring_dir = self.performance_dir / "monitoring"
        
        validation = {
            "monitoring_directory_exists": monitoring_dir.exists(),
            "dashboards": [],
            "prometheus_config": False,
            "grafana_config": False,
            "alertmanager_config": False,
            "docker_compose": False,
            "performance_rules": False,
            "issues": [],
            "recommendations": []
        }
        
        if not monitoring_dir.exists():
            validation["issues"].append("Performance monitoring directory not found")
            validation["recommendations"].append("Create performance monitoring infrastructure")
            return validation
        
        # Check for monitoring configuration files
        config_files = {
            "prometheus-config.yml": "prometheus_config",
            "prometheus.yml": "prometheus_config",
            "grafana": "grafana_config",
            "alertmanager.yml": "alertmanager_config",
            "docker-compose.monitoring.yml": "docker_compose",
            "performance_rules.yml": "performance_rules"
        }
        
        for config_file, config_type in config_files.items():
            config_path = monitoring_dir / config_file
            if config_path.exists() or (monitoring_dir / config_file).is_dir():
                validation[config_type] = True
        
        # Check for Grafana dashboards
        grafana_dir = monitoring_dir / "grafana"
        if grafana_dir.exists():
            dashboard_files = list(grafana_dir.rglob("*.json"))
            validation["dashboards"] = [f.name for f in dashboard_files]
        
        # Check performance dashboard specifically
        dashboard_file = self.performance_dir / "dashboards" / "socialmapper-performance-dashboard.json"
        if dashboard_file.exists():
            validation["dashboards"].append(dashboard_file.name)
        
        # Generate recommendations
        if not validation["prometheus_config"]:
            validation["recommendations"].append("Add Prometheus configuration for performance metrics")
        
        if not validation["grafana_config"]:
            validation["recommendations"].append("Configure Grafana for performance visualization")
        
        if not validation["dashboards"]:
            validation["recommendations"].append("Create performance monitoring dashboards")
        
        return validation
    
    def _validate_ci_integration(self) -> Dict[str, Any]:
        """Validate CI integration for performance testing"""
        validation = {
            "performance_workflow_exists": False,
            "workflow_triggers": [],
            "job_dependencies": [],
            "artifact_collection": False,
            "reporting_configured": False,
            "properly_integrated": False,
            "issues": [],
            "recommendations": []
        }
        
        # Check for performance testing workflow
        perf_workflow = self.workflows_dir / "performance-testing.yml"
        validation["performance_workflow_exists"] = perf_workflow.exists()
        
        if not perf_workflow.exists():
            validation["issues"].append("Performance testing workflow not found")
            validation["recommendations"].append("Create performance-testing.yml workflow")
            return validation
        
        # Analyze workflow content
        try:
            with open(perf_workflow, 'r') as f:
                workflow_data = yaml.safe_load(f)
            
            # Check triggers
            triggers = workflow_data.get('on', {})
            if 'workflow_run' in triggers:
                validation["workflow_triggers"].append("workflow_run")
            if 'workflow_dispatch' in triggers:
                validation["workflow_triggers"].append("manual_trigger")
            if 'schedule' in triggers:
                validation["workflow_triggers"].append("scheduled")
            
            # Check jobs and their dependencies
            jobs = workflow_data.get('jobs', {})
            for job_name, job_config in jobs.items():
                needs = job_config.get('needs', [])
                if needs:
                    validation["job_dependencies"].append(f"{job_name} depends on {needs}")
                
                # Check for artifact collection
                steps = job_config.get('steps', [])
                for step in steps:
                    if step.get('uses', '').startswith('actions/upload-artifact'):
                        validation["artifact_collection"] = True
                    if 'GITHUB_STEP_SUMMARY' in str(step.get('run', '')):
                        validation["reporting_configured"] = True
            
            # Determine if properly integrated
            validation["properly_integrated"] = (
                len(validation["workflow_triggers"]) > 0 and
                validation["artifact_collection"] and
                len(jobs) >= 2  # At least k6 and lighthouse jobs
            )
            
        except Exception as e:
            validation["issues"].append(f"Error analyzing performance workflow: {str(e)}")
        
        # Check integration with main CI/CD workflow
        ci_cd_workflow = self.workflows_dir / "ci-cd.yml"
        if ci_cd_workflow.exists():
            with open(ci_cd_workflow, 'r') as f:
                content = f.read()
                if "performance" not in content.lower():
                    validation["recommendations"].append("Integrate performance testing with main CI/CD pipeline")
        
        return validation
    
    def _validate_performance_budgets(self) -> Dict[str, Any]:
        """Validate performance budget configuration"""
        validation = {
            "budget_files": [],
            "k6_thresholds": False,
            "lighthouse_budgets": False,
            "budget_categories": [],
            "enforcement_configured": False,
            "issues": [],
            "recommendations": []
        }
        
        # Check for performance budget files
        budget_locations = [
            self.performance_dir / "config" / "performance-budgets.yaml",
            self.performance_dir / "lighthouse" / "budget.json",
            self.performance_dir / "budgets.json"
        ]
        
        for budget_file in budget_locations:
            if budget_file.exists():
                validation["budget_files"].append(str(budget_file.relative_to(self.repo_root)))
                
                # Analyze budget content
                try:
                    with open(budget_file, 'r') as f:
                        content = f.read()
                        
                        if "response_time" in content or "duration" in content:
                            validation["budget_categories"].append("response_time")
                        if "throughput" in content or "requests" in content:
                            validation["budget_categories"].append("throughput")
                        if "memory" in content or "cpu" in content:
                            validation["budget_categories"].append("resource_usage")
                        if "lighthouse" in content.lower():
                            validation["lighthouse_budgets"] = True
                            
                except Exception as e:
                    validation["issues"].append(f"Error reading budget file {budget_file.name}: {str(e)}")
        
        # Check k6 thresholds
        k6_tests_dir = self.performance_dir / "k6" / "tests"
        if k6_tests_dir.exists():
            for test_file in k6_tests_dir.glob("*.js"):
                with open(test_file, 'r') as f:
                    content = f.read()
                    if "thresholds" in content:
                        validation["k6_thresholds"] = True
                        break
        
        # Check enforcement in CI
        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                content = f.read()
                if "budget" in content.lower() or "threshold" in content.lower():
                    validation["enforcement_configured"] = True
                    break
        
        # Generate recommendations
        if not validation["budget_files"]:
            validation["recommendations"].append("Create performance budget configuration files")
        
        if not validation["k6_thresholds"]:
            validation["recommendations"].append("Add performance thresholds to k6 tests")
        
        if not validation["lighthouse_budgets"]:
            validation["recommendations"].append("Configure Lighthouse performance budgets")
        
        if not validation["enforcement_configured"]:
            validation["recommendations"].append("Configure budget enforcement in CI pipeline")
        
        return validation
    
    def _validate_thresholds(self) -> Dict[str, Any]:
        """Validate performance threshold configuration"""
        validation = {
            "configured": False,
            "k6_thresholds": [],
            "lighthouse_thresholds": [],
            "alerting_rules": [],
            "threshold_categories": [],
            "issues": [],
            "recommendations": []
        }
        
        # Check k6 thresholds
        k6_tests_dir = self.performance_dir / "k6" / "tests"
        if k6_tests_dir.exists():
            for test_file in k6_tests_dir.glob("*.js"):
                with open(test_file, 'r') as f:
                    content = f.read()
                    
                    # Extract threshold information
                    import re
                    threshold_matches = re.findall(r'thresholds:\s*{([^}]+)}', content, re.MULTILINE | re.DOTALL)
                    for match in threshold_matches:
                        validation["k6_thresholds"].append(f"{test_file.name}: {match.strip()}")
                        validation["configured"] = True
                        
                        # Categorize thresholds
                        if "http_req_duration" in match:
                            validation["threshold_categories"].append("response_time")
                        if "http_req_failed" in match:
                            validation["threshold_categories"].append("error_rate")
                        if "http_reqs" in match:
                            validation["threshold_categories"].append("throughput")
        
        # Check Lighthouse thresholds
        lighthouse_configs = [
            self.performance_dir / "lighthouse" / "lighthouserc.json",
            self.performance_dir / "lighthouse" / "mobile-config.json"
        ]
        
        for config_file in lighthouse_configs:
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                        if "assert" in content or "budgets" in content:
                            validation["lighthouse_thresholds"].append(config_file.name)
                            validation["configured"] = True
                except Exception as e:
                    validation["issues"].append(f"Error reading {config_file.name}: {str(e)}")
        
        # Check alerting rules
        alerting_files = [
            self.performance_dir / "monitoring" / "performance_rules.yml",
            self.performance_dir / "monitoring" / "alertmanager.yml"
        ]
        
        for alert_file in alerting_files:
            if alert_file.exists():
                validation["alerting_rules"].append(alert_file.name)
                validation["configured"] = True
        
        # Generate recommendations
        if not validation["k6_thresholds"]:
            validation["recommendations"].append("Add performance thresholds to k6 tests")
        
        if not validation["lighthouse_thresholds"]:
            validation["recommendations"].append("Configure Lighthouse CI assertions")
        
        if not validation["alerting_rules"]:
            validation["recommendations"].append("Set up performance alerting rules")
        
        return validation
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate overall recommendations based on validation results"""
        recommendations = []
        
        # Collect all recommendations from individual validations
        for validation_key in ["k6_validation", "lighthouse_validation", "monitoring_validation", 
                             "ci_integration", "performance_budgets", "thresholds"]:
            if validation_key in results and "recommendations" in results[validation_key]:
                recommendations.extend(results[validation_key]["recommendations"])
        
        # Add high-level recommendations
        if results["summary"]["k6_tests"] == 0:
            recommendations.insert(0, "🚨 CRITICAL: No k6 load tests found - implement load testing")
        
        if not results["summary"]["ci_integration"]:
            recommendations.insert(0, "🚨 CRITICAL: Performance testing not integrated with CI/CD")
        
        if results["summary"]["performance_budgets"] == 0:
            recommendations.append("📊 Define performance budgets and SLAs")
        
        if results["summary"]["monitoring_dashboards"] == 0:
            recommendations.append("📈 Set up performance monitoring dashboards")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    def _identify_critical_issues(self, results: Dict[str, Any]) -> List[str]:
        """Identify critical issues that need immediate attention"""
        critical_issues = []
        
        if results["summary"]["k6_tests"] == 0:
            critical_issues.append("No load tests configured - application performance unknown")
        
        if not results["summary"]["ci_integration"]:
            critical_issues.append("Performance testing not automated - manual testing required")
        
        if not results["summary"]["thresholds_configured"]:
            critical_issues.append("No performance thresholds defined - cannot detect regressions")
        
        if results["summary"]["performance_budgets"] == 0:
            critical_issues.append("No performance budgets - no SLA enforcement")
        
        # Check for specific issues from individual validations
        for validation in results.values():
            if isinstance(validation, dict) and "issues" in validation:
                critical_issues.extend([f"ISSUE: {issue}" for issue in validation["issues"]])
        
        return critical_issues
    
    def generate_performance_report(self, results: Dict[str, Any], output_file: Optional[Path] = None) -> str:
        """Generate comprehensive performance validation report"""
        
        # Create summary table
        table = Table(title="⚡ Performance Testing Analysis")
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold")
        table.add_column("Configuration", style="dim")
        table.add_column("CI Integration", justify="center")
        
        components = [
            ("k6 Load Testing", 
             "✅ Configured" if results["summary"]["k6_tests"] > 0 else "❌ Missing",
             f"{results['summary']['k6_tests']} tests",
             "✅" if results["k6_validation"].get("ci_integration", False) else "❌"),
            ("Lighthouse CI",
             "✅ Configured" if results["summary"]["lighthouse_configs"] > 0 else "❌ Missing",
             f"{results['summary']['lighthouse_configs']} configs",
             "✅" if results["lighthouse_validation"].get("ci_integration", False) else "❌"),
            ("Performance Monitoring",
             "✅ Configured" if results["summary"]["monitoring_dashboards"] > 0 else "❌ Missing",
             f"{results['summary']['monitoring_dashboards']} dashboards",
             "✅" if results["monitoring_validation"].get("prometheus_config", False) else "❌"),
            ("Performance Budgets",
             "✅ Configured" if results["summary"]["performance_budgets"] > 0 else "❌ Missing",
             f"{results['summary']['performance_budgets']} files",
             "✅" if results["performance_budgets"].get("enforcement_configured", False) else "❌")
        ]
        
        for component, status, config, ci_integration in components:
            table.add_row(component, status, config, ci_integration)
        
        console.print(table)
        
        # Calculate performance testing score
        score_factors = {
            "k6_tests": min(results["summary"]["k6_tests"] / 3.0, 1.0) * 30,  # Up to 3 tests = 30 points
            "lighthouse_configs": min(results["summary"]["lighthouse_configs"] / 2.0, 1.0) * 20,  # 2 configs = 20 points
            "monitoring": min(results["summary"]["monitoring_dashboards"] / 2.0, 1.0) * 20,  # 2 dashboards = 20 points
            "ci_integration": 15 if results["summary"]["ci_integration"] else 0,  # 15 points
            "budgets": min(results["summary"]["performance_budgets"] / 2.0, 1.0) * 10,  # 2 budget files = 10 points
            "thresholds": 5 if results["summary"]["thresholds_configured"] else 0  # 5 points
        }
        
        overall_score = sum(score_factors.values())
        
        # Determine status
        if overall_score >= 80:
            panel_style = "green"
            status_emoji = "🚀"
            status_text = "EXCELLENT"
        elif overall_score >= 60:
            panel_style = "yellow"
            status_emoji = "⚡"
            status_text = "GOOD"
        elif overall_score >= 40:
            panel_style = "orange"
            status_emoji = "⚠️"
            status_text = "NEEDS IMPROVEMENT"
        else:
            panel_style = "red"
            status_emoji = "🚨"
            status_text = "CRITICAL ISSUES"
        
        summary_text = f"""
Performance Testing Score: {overall_score:.1f}/100

Components Status:
• k6 Load Tests: {results['summary']['k6_tests']} configured
• Lighthouse Configs: {results['summary']['lighthouse_configs']} configured  
• Monitoring Dashboards: {results['summary']['monitoring_dashboards']} configured
• Performance Budgets: {results['summary']['performance_budgets']} configured
• CI Integration: {'✅' if results['summary']['ci_integration'] else '❌'}
• Thresholds: {'✅' if results['summary']['thresholds_configured'] else '❌'}
        """
        
        console.print(Panel(
            f"{status_emoji} {status_text}\n{summary_text}",
            title="⚡ Performance Assessment",
            style=panel_style,
            expand=False
        ))
        
        # Show critical issues if any
        if results["critical_issues"]:
            critical_panel = Panel(
                "\n".join([f"• {issue}" for issue in results["critical_issues"]]),
                title="🚨 Critical Issues",
                style="red",
                expand=False
            )
            console.print(critical_panel)
        
        # Generate detailed markdown report
        report_content = self._generate_detailed_performance_report(results, overall_score)
        
        if output_file:
            output_file.write_text(report_content)
            console.print(f"📄 Detailed performance report saved to: {output_file}")
        
        return report_content
    
    def _generate_detailed_performance_report(self, results: Dict[str, Any], overall_score: float) -> str:
        """Generate detailed markdown performance report"""
        
        report_lines = [
            "# ⚡ Performance Testing Pipeline Validation Report",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
            f"**Repository:** {self.repo_root.name}",
            f"**Overall Performance Score:** {overall_score:.1f}/100",
            "",
            "## Executive Summary",
            ""
        ]
        
        # Add status assessment
        if overall_score >= 80:
            status = "🚀 **EXCELLENT** - Comprehensive performance testing pipeline"
        elif overall_score >= 60:
            status = "⚡ **GOOD** - Solid performance testing foundation"
        elif overall_score >= 40:
            status = "⚠️ **NEEDS IMPROVEMENT** - Basic performance testing in place"
        else:
            status = "🚨 **CRITICAL ISSUES** - Performance testing requires immediate attention"
        
        report_lines.extend([
            status,
            "",
            f"- **k6 Load Tests:** {results['summary']['k6_tests']} configured",
            f"- **Lighthouse CI:** {results['summary']['lighthouse_configs']} configurations",
            f"- **Performance Monitoring:** {results['summary']['monitoring_dashboards']} dashboards",
            f"- **Performance Budgets:** {results['summary']['performance_budgets']} budget files",
            f"- **CI Integration:** {'✅ Enabled' if results['summary']['ci_integration'] else '❌ Missing'}",
            f"- **Thresholds Configured:** {'✅ Yes' if results['summary']['thresholds_configured'] else '❌ No'}",
            "",
            "## Detailed Analysis",
            ""
        ])
        
        # k6 Load Testing Analysis
        report_lines.extend([
            "### 🔥 k6 Load Testing",
            ""
        ])
        
        k6_validation = results["k6_validation"]
        if k6_validation.get("k6_directory_exists"):
            report_lines.extend([
                f"**Status:** {'✅ Configured' if k6_validation['test_count'] > 0 else '❌ No tests found'}",
                f"**Test Files:** {k6_validation['test_count']} ({', '.join(k6_validation['test_files'])[:100]}{'...' if len(', '.join(k6_validation['test_files'])) > 100 else ''})",
                f"**Test Types:** {', '.join(set(k6_validation['test_types'])) if k6_validation['test_types'] else 'None configured'}",
                f"**Thresholds Defined:** {'✅ Yes' if k6_validation['thresholds_defined'] else '❌ No'}",
                f"**Helper Functions:** {'✅ Available' if k6_validation['helper_functions'] else '❌ Missing'}",
                ""
            ])
        else:
            report_lines.extend([
                "**Status:** ❌ k6 directory not found",
                "**Impact:** No load testing capability",
                ""
            ])
        
        if k6_validation.get("recommendations"):
            report_lines.extend([
                "**k6 Recommendations:**",
                ""
            ])
            for rec in k6_validation["recommendations"]:
                report_lines.append(f"- 💡 {rec}")
            report_lines.append("")
        
        # Lighthouse CI Analysis
        report_lines.extend([
            "### 💡 Lighthouse CI",
            ""
        ])
        
        lighthouse_validation = results["lighthouse_validation"]
        if lighthouse_validation.get("lighthouse_directory_exists"):
            report_lines.extend([
                f"**Status:** {'✅ Configured' if lighthouse_validation['config_files'] else '❌ No configuration found'}",
                f"**Configuration Files:** {', '.join(lighthouse_validation['config_files']) if lighthouse_validation['config_files'] else 'None'}",
                f"**Mobile Configuration:** {'✅ Yes' if lighthouse_validation['mobile_config'] else '❌ No'}",
                f"**Desktop Configuration:** {'✅ Yes' if lighthouse_validation['desktop_config'] else '❌ No'}",
                f"**Performance Budgets:** {'✅ Configured' if lighthouse_validation['performance_budgets'] else '❌ Missing'}",
                f"**CI Integration:** {'✅ Enabled' if lighthouse_validation['ci_integration'] else '❌ Not integrated'}",
                ""
            ])
        else:
            report_lines.extend([
                "**Status:** ❌ Lighthouse directory not found",
                "**Impact:** No frontend performance monitoring",
                ""
            ])
        
        # Performance Monitoring Analysis
        report_lines.extend([
            "### 📊 Performance Monitoring",
            ""
        ])
        
        monitoring_validation = results["monitoring_validation"]
        if monitoring_validation.get("monitoring_directory_exists"):
            report_lines.extend([
                f"**Prometheus:** {'✅ Configured' if monitoring_validation['prometheus_config'] else '❌ Missing'}",
                f"**Grafana:** {'✅ Configured' if monitoring_validation['grafana_config'] else '❌ Missing'}",
                f"**Alertmanager:** {'✅ Configured' if monitoring_validation['alertmanager_config'] else '❌ Missing'}",
                f"**Dashboards:** {len(monitoring_validation['dashboards'])} ({', '.join(monitoring_validation['dashboards'][:3])}{'...' if len(monitoring_validation['dashboards']) > 3 else ''})",
                f"**Docker Compose:** {'✅ Available' if monitoring_validation['docker_compose'] else '❌ Missing'}",
                ""
            ])
        else:
            report_lines.extend([
                "**Status:** ❌ Monitoring directory not found",
                "**Impact:** No performance observability",
                ""
            ])
        
        # CI Integration Analysis
        report_lines.extend([
            "### 🔄 CI/CD Integration",
            ""
        ])
        
        ci_integration = results["ci_integration"]
        if ci_integration.get("performance_workflow_exists"):
            report_lines.extend([
                "**Workflow Status:** ✅ Performance testing workflow found",
                f"**Triggers:** {', '.join(ci_integration['workflow_triggers']) if ci_integration['workflow_triggers'] else 'None configured'}",
                f"**Job Dependencies:** {'✅ Configured' if ci_integration['job_dependencies'] else '❌ Missing'}",
                f"**Artifact Collection:** {'✅ Enabled' if ci_integration['artifact_collection'] else '❌ Missing'}",
                f"**Reporting:** {'✅ Configured' if ci_integration['reporting_configured'] else '❌ Missing'}",
                ""
            ])
        else:
            report_lines.extend([
                "**Workflow Status:** ❌ No performance testing workflow found",
                "**Impact:** Performance tests not automated",
                ""
            ])
        
        # Performance Budgets Analysis
        report_lines.extend([
            "### 💰 Performance Budgets",
            ""
        ])
        
        budgets = results["performance_budgets"]
        if budgets["budget_files"]:
            report_lines.extend([
                f"**Budget Files:** {len(budgets['budget_files'])} configured",
                f"**k6 Thresholds:** {'✅ Configured' if budgets['k6_thresholds'] else '❌ Missing'}",
                f"**Lighthouse Budgets:** {'✅ Configured' if budgets['lighthouse_budgets'] else '❌ Missing'}",
                f"**Categories:** {', '.join(set(budgets['budget_categories'])) if budgets['budget_categories'] else 'None'}",
                f"**CI Enforcement:** {'✅ Enabled' if budgets['enforcement_configured'] else '❌ Missing'}",
                ""
            ])
        else:
            report_lines.extend([
                "**Status:** ❌ No performance budgets configured",
                "**Impact:** No SLA enforcement or regression detection",
                ""
            ])
        
        # Critical Issues Section
        if results["critical_issues"]:
            report_lines.extend([
                "## 🚨 Critical Issues",
                "",
                "The following issues require immediate attention:",
                ""
            ])
            
            for issue in results["critical_issues"]:
                report_lines.append(f"- ❌ {issue}")
            
            report_lines.append("")
        
        # Recommendations Section
        if results["recommendations"]:
            report_lines.extend([
                "## 🚀 Recommendations",
                "",
                "### Priority Actions",
                ""
            ])
            
            # Prioritize recommendations
            critical_recs = [r for r in results["recommendations"] if "CRITICAL" in r]
            high_recs = [r for r in results["recommendations"] if r.startswith("🚨") and r not in critical_recs]
            normal_recs = [r for r in results["recommendations"] if r not in critical_recs + high_recs]
            
            for i, rec in enumerate(critical_recs + high_recs[:5], 1):
                report_lines.append(f"{i}. {rec}")
            
            if normal_recs:
                report_lines.extend([
                    "",
                    "### Additional Improvements",
                    ""
                ])
                for rec in normal_recs[:10]:
                    report_lines.append(f"- {rec}")
            
            report_lines.append("")
        
        # Implementation Roadmap
        report_lines.extend([
            "## 📋 Implementation Roadmap",
            "",
            "### Phase 1: Critical Infrastructure (Week 1-2)",
            "1. Set up k6 load testing framework",
            "2. Create basic performance workflow in GitHub Actions",
            "3. Configure performance budgets and thresholds",
            "",
            "### Phase 2: Comprehensive Testing (Week 3-4)",
            "1. Implement Lighthouse CI for frontend performance",
            "2. Add multiple load testing scenarios (load, stress, spike)",
            "3. Configure performance monitoring and dashboards",
            "",
            "### Phase 3: Advanced Features (Week 5-6)",
            "1. Set up automated performance regression detection",
            "2. Implement performance alerting and notifications",
            "3. Add performance trend analysis and reporting",
            "",
            "### Phase 4: Optimization (Ongoing)",
            "1. Regular performance baseline updates",
            "2. Continuous improvement of test scenarios",
            "3. Performance optimization based on insights",
            ""
        ])
        
        return "\n".join(report_lines)

def main():
    parser = argparse.ArgumentParser(description="Validate Performance Testing Pipeline Configuration")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(),
                       help="Repository root directory (default: current directory)")
    parser.add_argument("--output", type=Path,
                       help="Output file for detailed report")
    parser.add_argument("--json", action="store_true",
                       help="Output results in JSON format")
    parser.add_argument("--fail-threshold", type=float, default=40.0,
                       help="Fail if performance score below threshold (default: 40.0)")
    
    args = parser.parse_args()
    
    # Validate repository root
    if not (args.repo_root / ".github" / "workflows").exists():
        console.print("❌ Error: .github/workflows directory not found", style="red")
        sys.exit(1)
    
    # Run validation
    validator = PerformanceValidator(args.repo_root)
    results = validator.validate_performance_pipeline()
    
    if args.json:
        # Output JSON results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        else:
            print(json.dumps(results, indent=2, default=str))
    else:
        # Generate formatted report
        validator.generate_performance_report(results, args.output)
    
    # Calculate score and exit appropriately
    score_factors = {
        "k6_tests": min(results["summary"]["k6_tests"] / 3.0, 1.0) * 30,
        "lighthouse_configs": min(results["summary"]["lighthouse_configs"] / 2.0, 1.0) * 20,
        "monitoring": min(results["summary"]["monitoring_dashboards"] / 2.0, 1.0) * 20,
        "ci_integration": 15 if results["summary"]["ci_integration"] else 0,
        "budgets": min(results["summary"]["performance_budgets"] / 2.0, 1.0) * 10,
        "thresholds": 5 if results["summary"]["thresholds_configured"] else 0
    }
    
    overall_score = sum(score_factors.values())
    
    if overall_score < args.fail_threshold:
        console.print(f"\n⚡ Performance validation failed: {overall_score:.1f}% < {args.fail_threshold}%", style="red")
        sys.exit(1)
    else:
        console.print(f"\n✅ Performance validation passed: {overall_score:.1f}% >= {args.fail_threshold}%", style="green")
        sys.exit(0)

if __name__ == "__main__":
    main()